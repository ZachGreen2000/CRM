import asyncio
import os
import sqlite3
import uuid
from datetime import datetime
from imap_tools import MailBox, AND
import aiosqlite
import httpx
from src.Memory.vector_store import get_vector_store
from src.Memory.thread_summarizer import get_thread_summarizer

MODEL = "qwen3:8b"
# ── DB connection ────────────────────────────────────────────────────────────

async def get_db():
    # Connect to local SQLite database
    # Use absolute path from project root to avoid working directory issues
    # __file__ is at: src/Orchestrator/Agents/email_agent.py
    # Go up 3 levels to project root, then back down to src/Database
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    db_path = os.path.join(project_root, "src", "Database", "crm.db")
    return await aiosqlite.connect(db_path)

# ── Embedding via Ollama (or swap for OpenAI) ────────────────────────────────

async def generate_embedding(text: str) -> list[float]:
    print(f"[EMAIL_AGENT] Generating embedding for text (length: {len(text)})")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "nomic-embed-text",
                    "input": text[:8000]
                }
            )
            result = response.json()
            embedding = result.get("embedding")
            if embedding is None and isinstance(result.get("data"), list) and result["data"]:
                embedding = result["data"][0].get("embedding")

            if embedding is None:
                raise ValueError(f"Embedding response missing expected field: {result}")

            print(f"[EMAIL_AGENT] Embedding generated successfully, vector length: {len(embedding)}")
            return embedding
    except Exception as e:
        print(f"[EMAIL_AGENT] Error generating embedding: {e}")
        raise

# ── Contact resolution ───────────────────────────────────────────────────────

async def resolve_contact(db, email_address: str) -> dict | None:
    cursor = await db.execute(
        "SELECT id, client_id FROM contacts WHERE email = ?",
        (email_address.lower(),)
    )
    row = await cursor.fetchone()
    return {"id": row[0], "client_id": row[1]} if row else None

# ── Deduplication ────────────────────────────────────────────────────────────

async def email_exists(db, message_id: str) -> bool:
    cursor = await db.execute(
        "SELECT id FROM emails WHERE thread_id = ? LIMIT 1",
        (message_id,)
    )
    row = await cursor.fetchone()
    return row is not None

# ── Store email + embedding ──────────────────────────────────────────────────

async def store_email(db, msg, contact: dict) -> str | None:
    print(f"[EMAIL_AGENT] Storing email: subject='{msg.subject}', from='{msg.from_}', contact_id={contact['id']}")
    contact_id = contact["id"]
    client_id  = contact["client_id"]

    your_email = os.getenv("EMAIL_USER", "").lower()
    from_addr  = (msg.from_ or "").lower()
    direction  = "outbound" if from_addr == your_email else "inbound"

    body = msg.text or msg.html or ""
    print(f"[EMAIL_AGENT] Email direction: {direction}, body length: {len(body)} chars")

    # Generate a UUID for the email
    email_id = str(uuid.uuid4())
    print(f"[EMAIL_AGENT] Generated email_id: {email_id}")

    # Store email in SQLite (without embedding)
    await db.execute(
        """
        INSERT INTO emails (id, contact_id, client_id, subject, body, direction, sent_at, thread_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            email_id,
            contact_id,
            client_id,
            msg.subject or "(no subject)",
            body,
            direction,
            msg.date,
            msg.uid  # use UID as thread_id
        )
    )

    # Generate and store embedding in vector store
    text_to_embed = f"{msg.subject or ''} {body}".strip()
    print(f"[EMAIL_AGENT] Generating embedding for text length: {len(text_to_embed)} chars")
    embedding = await generate_embedding(text_to_embed)

    if embedding:
        vector_store = get_vector_store()
        metadata = {
            "contact_id": contact_id,
            "client_id": client_id,
            "subject": msg.subject or "(no subject)",
            "direction": direction,
            "sent_at": str(msg.date),
            "thread_id": msg.uid,
            "sender": from_addr
        }

        success = await vector_store.store_email_embedding(
            email_id, text_to_embed, embedding, metadata
        )

        if success:
            print(f"[EMAIL_AGENT] Stored embedding in vector store")
        else:
            print(f"[EMAIL_AGENT] Failed to store embedding in vector store")

    # Generate/update thread summary
    thread_summarizer = get_thread_summarizer()
    thread_summary = await thread_summarizer.generate_incremental_summary(
        msg.uid, contact_id, text_to_embed,
        {
            "subject": msg.subject or "(no subject)",
            "direction": direction,
            "sender": from_addr,
            "email_id": email_id
        }
    )

    print(f"[EMAIL_AGENT] Generated thread summary: {thread_summary[:100]}...")

    await db.commit()
    print(f"[EMAIL_AGENT] Database transaction committed")
    return email_id

# ── Action: fetch and ingest unseen emails ───────────────────────────────────

async def fetch_emails(limit: int, folder: str) -> dict:
    print(f"[EMAIL_AGENT] Starting fetch_emails with limit={limit}, folder='{folder}'")

    # Validate required environment variables
    email_user = os.getenv("EMAIL_USER")
    email_pass = os.getenv("EMAIL_PASS")

    if not email_user:
        error_msg = "[EMAIL_AGENT] ERROR: EMAIL_USER environment variable is not set"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "ingested": [],
            "skipped": [],
            "counts": {"ingested": 0, "skipped": 0}
        }

    if not email_pass:
        error_msg = "[EMAIL_AGENT] ERROR: EMAIL_PASS environment variable is not set"
        print(error_msg)
        return {
            "status": "error",
            "error": error_msg,
            "ingested": [],
            "skipped": [],
            "counts": {"ingested": 0, "skipped": 0}
        }

    db = await get_db()
    ingested = []
    skipped  = []

    try:
        # Run blocking MailBox operations in a thread executor to avoid blocking the event loop
        def _fetch_from_imap():
            print(f"[EMAIL_AGENT] Connecting to IMAP server imap.gmail.com with user {email_user}")
            with MailBox("imap.gmail.com").login(
                email_user,
                email_pass
            ) as mailbox:
                print(f"[EMAIL_AGENT] Setting folder to '{folder}'")
                mailbox.folder.set(folder)
                print(f"[EMAIL_AGENT] Fetching up to {limit} unseen emails")
                return list(mailbox.fetch(AND(seen=False), limit=limit))

        msgs = await asyncio.to_thread(_fetch_from_imap)
        print(f"[EMAIL_AGENT] Retrieved {len(msgs)} messages from IMAP")

        for msg in msgs:
            print(f"[EMAIL_AGENT] Processing message UID={msg.uid}, subject='{msg.subject}', from='{msg.from_}'")

            # Deduplicate
            if msg.uid and await email_exists(db, str(msg.uid)):
                print(f"[EMAIL_AGENT] Skipping message UID={msg.uid} - already exists in database")
                skipped.append({"uid": msg.uid, "reason": "already stored"})
                continue

            from_addr = msg.from_ or ""
            contact   = await resolve_contact(db, from_addr)

            if not contact:
                print(f"[EMAIL_AGENT] Skipping message UID={msg.uid} - sender '{from_addr}' not found in CRM contacts")
                skipped.append({"uid": msg.uid, "from": from_addr, "reason": "not in CRM"})
                continue

            print(f"[EMAIL_AGENT] Storing email for contact_id={contact['id']}, client_id={contact['client_id']}")
            email_id = await store_email(db, msg, contact)
            ingested.append({
                "email_id":   email_id,
                "from":       from_addr,
                "subject":    msg.subject,
                "contact_id": contact["id"],
                "client_id":  contact["client_id"]
            })
            print(f"[EMAIL_AGENT] Successfully stored email with ID={email_id}")

    finally:
        await db.close()
        print(f"[EMAIL_AGENT] Database connection closed")

    result = {
        "status":   "ok",
        "ingested": ingested,
        "skipped":  skipped,
        "counts":   {"ingested": len(ingested), "skipped": len(skipped)}
    }
    print(f"[EMAIL_AGENT] fetch_emails completed. Ingested: {len(ingested)}, Skipped: {len(skipped)}")
    return result

# ── Action: search emails using vector similarity ────────────────────────

async def search_emails(query: str, contact_id: str = None, limit: int = 5) -> dict:
    """
    Search for emails using semantic similarity via vector embeddings.
    """
    print(f"[EMAIL_AGENT] Searching emails with query: '{query}', contact_id: {contact_id}, limit: {limit}")

    try:
        # Generate embedding for the search query
        query_embedding = await generate_embedding(query)

        if not query_embedding:
            return {
                "status": "error",
                "error": "Failed to generate embedding for search query",
                "results": []
            }

        # Search vector store
        vector_store = get_vector_store()
        results = await vector_store.search_similar_emails(
            query_embedding, contact_id=contact_id, limit=limit
        )

        # Enrich results with full email data from SQLite
        enriched_results = await _enrich_search_results(results)

        return {
            "status": "ok",
            "query": query,
            "results": enriched_results,
            "count": len(enriched_results)
        }

    except Exception as e:
        print(f"[EMAIL_AGENT] Error searching emails: {e}")
        return {
            "status": "error",
            "error": str(e),
            "results": []
        }


async def _enrich_search_results(vector_results: list) -> list:
    """Enrich vector search results with full email data from SQLite."""
    if not vector_results:
        return []

    db = await get_db()
    enriched = []

    try:
        for result in vector_results:
            email_id = result['id']

            # Get full email data
            cursor = await db.execute(
                """
                SELECT e.subject, e.body, e.direction, e.sent_at, e.thread_id,
                       c.name as contact_name, c.email as contact_email,
                       cl.name as client_name
                FROM emails e
                JOIN contacts c ON e.contact_id = c.id
                JOIN clients cl ON e.client_id = cl.id
                WHERE e.id = ?
                """,
                (email_id,)
            )

            email_data = await cursor.fetchone()

            if email_data:
                enriched.append({
                    "email_id": email_id,
                    "subject": email_data[0],
                    "body": email_data[1],
                    "direction": email_data[2],
                    "sent_at": email_data[3],
                    "thread_id": email_data[4],
                    "contact_name": email_data[5],
                    "contact_email": email_data[6],
                    "client_name": email_data[7],
                    "similarity_score": result.get('distance'),
                    "matched_content": result['content'][:200] + "..." if len(result['content']) > 200 else result['content']
                })

    finally:
        await db.close()

    return enriched

async def update_contact_from_email(email_data: dict, contact_id: str, model: str | None = None) -> dict:
    """
    Update contact summary based on email data.
    This now uses the thread summarizer for incremental updates.
    """
    print(f"[EMAIL_AGENT] Updating contact summary for contact_id: {contact_id}")

    db = await get_db()

    try:
        # Get thread context using vector store
        thread_summarizer = get_thread_summarizer(model)
        thread_context = await thread_summarizer.get_thread_context(
            email_data.get('thread_id', 'unknown')
        )

        # Generate comprehensive contact summary
        summary = await _generate_contact_summary(db, contact_id, thread_context, model=model)

        # Store summary in SQLite and vector store
        vector_store = get_vector_store()
        summary_embedding = await generate_embedding(summary)

        if summary_embedding:
            metadata = {
                "contact_id": contact_id,
                "updated_at": str(datetime.now()),
                "source": "email_update"
            }

            await vector_store.store_contact_summary_embedding(
                contact_id, summary, summary_embedding, metadata
            )

        # Update SQLite record
        cursor = await db.execute(
            "SELECT id FROM contact_summaries WHERE contact_id = ?",
            (contact_id,)
        )
        existing = await cursor.fetchone()

        if existing:
            await db.execute(
                "UPDATE contact_summaries SET summary_text = ?, updated_at = datetime('now') WHERE contact_id = ?",
                (summary, contact_id)
            )
        else:
            summary_id = str(uuid.uuid4())
            await db.execute(
                "INSERT INTO contact_summaries (id, contact_id, summary_text, updated_at) VALUES (?, ?, ?, datetime('now'))",
                (summary_id, contact_id, summary)
            )

        await db.commit()

        return {
            "updated":    True,
            "status":     "ok",
            "contact_id": contact_id,
            "summary":    summary
        }

    finally:
        await db.close()


async def _generate_contact_summary(db, contact_id: str, thread_context: dict, model: str | None = None) -> str:
    """Generate comprehensive contact summary using thread context."""
    model = model or MODEL

    # Get recent emails for context
    cursor = await db.execute(
        """
        SELECT subject, body, direction, sent_at
        FROM emails
        WHERE contact_id = ?
        ORDER BY sent_at DESC
        LIMIT 10
        """,
        (contact_id,)
    )
    rows = await cursor.fetchall()

    if not rows:
        return "No email history available for this contact."

    # Build context
    email_context = "\n---\n".join([
        f"[{r[2].upper()}] {r[3]} — {r[0]}\n{r[1][:500]}..."
        for r in rows
    ])

    thread_summary = thread_context.get('summary', 'No thread summary available.')

    # Call LLM for comprehensive summary
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "http://localhost:11434/api/chat",
            json={
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"""Based on the email history and thread summary below,
write a comprehensive summary of the relationship with this contact.

RECENT EMAIL HISTORY:
{email_context}

CURRENT THREAD SUMMARY:
{thread_summary}

Provide a summary covering:
- Overall relationship status
- Key topics discussed
- Outstanding actions or requests
- Communication patterns and frequency
- Any important dates, deadlines, or commitments

COMPREHENSIVE SUMMARY:"""
                    }
                ],
                "stream": False
            }
        )
        summary = response.json()["message"]["content"]

    return summary

# ── Action: add a new client ─────────────────────────────────────────────────

async def add_client(name: str, domain: str | None) -> dict:
    if not name:
        return {"success": False, "error": "Client name is required"}

    db = await get_db()

    try:
        # Check if client already exists
        cursor = await db.execute(
            "SELECT id, name FROM clients WHERE LOWER(name) = LOWER(?)",
            (name,)
        )
        existing = await cursor.fetchone()
        if existing:
            return {
                "success":   False,
                "error":     f"Client '{name}' already exists",
                "client_id": existing[0]
            }

        client_id = str(uuid.uuid4())
        await db.execute(
            "INSERT INTO clients (id, name, domain, created_at) VALUES (?, ?, ?, datetime('now'))",
            (client_id, name, domain or None)
        )
        await db.commit()

        return {
            "success":   True,
            "client_id": client_id,
            "name":      name,
            "domain":    domain
        }

    finally:
        await db.close()

# ── Action: add a new contact ────────────────────────────────────────────────

async def add_contact(
    name:       str,
    email:      str,
    client_id:  str | None,
    client_name: str | None,
    role:       str | None
) -> dict:
    if not name or not email:
        return {"success": False, "error": "Contact name and email are required"}

    db = await get_db()

    try:
        # Resolve client_id from name if not directly provided
        if not client_id and client_name:
            cursor = await db.execute(
                "SELECT id FROM clients WHERE LOWER(name) = LOWER(?)",
                (client_name,)
            )
            row = await cursor.fetchone()
            if not row:
                # Client doesn't exist, create it automatically
                client_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT INTO clients (id, name, domain, created_at) VALUES (?, ?, ?, datetime('now'))",
                    (client_id, client_name, None)
                )
                await db.commit()
            else:
                client_id = row[0]

        if not client_id:
            return {"success": False, "error": "A client name or client_id is required"}

        # Check if contact email already exists
        cursor = await db.execute(
            "SELECT id FROM contacts WHERE LOWER(email) = LOWER(?)",
            (email,)
        )
        existing = await cursor.fetchone()
        if existing:
            return {
                "success":    False,
                "error":      f"Contact with email '{email}' already exists",
                "contact_id": existing[0]
            }

        contact_id = str(uuid.uuid4())
        await db.execute(
            """
            INSERT INTO contacts (id, client_id, name, email, role, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
            """,
            (contact_id, client_id, name, email.lower(), role or None)
        )
        await db.commit()

        return {
            "success":    True,
            "contact_id": contact_id,
            "name":       name,
            "email":      email,
            "client_id":  client_id,
            "role":       role
        }

    finally:
        await db.close()

# ── Agent entry point (called by your tool registry / orchestrator) ───────────

async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "fetch_emails":
        return await fetch_emails(
            limit=params.get("limit", 10),
            folder=params.get("folder", "INBOX"),
        )

    if action == "update_contact_from_email":
        return await update_contact_from_email(
            email_data=params.get("email_data"),
            contact_id=params.get("contact_id"),
            model=params.get("model"),
        )

    if action == "_generate_contact_summary":
        return await _generate_contact_summary(
            db=await get_db(),
            contact_id=params.get("contact_id"),
            thread_context=params.get("thread_context", {}),
            model=params.get("model"),
        )

    if action == "search_emails":
        return await search_emails(
            query=params.get("query", ""),
            contact_id=params.get("contact_id"),
            limit=params.get("limit", 5),
        )

    if action == "add_client":
        return await add_client(
            name=params.get("name"),
            domain=params.get("domain"),
        )

    if action == "add_contact":
        return await add_contact(
            name=params.get("name"),
            email=params.get("email"),
            client_id=params.get("client_id"),
            client_name=params.get("client_name"),
            role=params.get("role"),
        )

    return {"error": f"Unknown action: {action}"}