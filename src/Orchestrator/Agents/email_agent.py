import asyncio
import os
import sqlite3
import uuid
from imap_tools import MailBox, AND
import aiosqlite
import httpx

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
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:11434/api/embeddings",
            json={
                "model": "nomic-embed-text",
                "prompt": text[:8000]
            }
        )
        return response.json()["embedding"]

# ── Contact resolution ───────────────────────────────────────────────────────

async def resolve_contact(db, email_address: str) -> dict | None:
    cursor = await db.execute(
        "SELECT id, client_id FROM contacts WHERE email = ?",
        (email_address.lower(),)
    )
    row = await cursor.fetchone()
    return dict(row) if row else None

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
    contact_id = contact["id"]
    client_id  = contact["client_id"]

    your_email = os.environ["EMAIL_USER"].lower()
    from_addr  = (msg.from_ or "").lower()
    direction  = "outbound" if from_addr == your_email else "inbound"

    body = msg.text or msg.html or ""

    # Generate a UUID for the email
    email_id = str(uuid.uuid4())

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

    # Generate and store embedding
    text_to_embed = f"{msg.subject or ''} {body}".strip()
    embedding     = await generate_embedding(text_to_embed)

    # Generate UUID for embedding
    embedding_id = str(uuid.uuid4())
    await db.execute(
        "INSERT INTO email_embeddings (id, email_id, embedding) VALUES (?, ?, ?)",
        (embedding_id, email_id, str(embedding))
    )

    await db.commit()
    return email_id

# ── Action: fetch and ingest unseen emails ───────────────────────────────────

async def fetch_emails(limit: int, folder: str) -> dict:
    db = await get_db()
    ingested = []
    skipped  = []

    try:
        # Run blocking MailBox operations in a thread executor to avoid blocking the event loop
        def _fetch_from_imap():
            with MailBox("imap.gmail.com").login(
                os.getenv("EMAIL_USER"),
                os.getenv("EMAIL_PASS")
            ) as mailbox:
                mailbox.folder.set(folder)
                return list(mailbox.fetch(AND(seen=False), limit=limit))
        
        msgs = await asyncio.to_thread(_fetch_from_imap)

        for msg in msgs:
            # Deduplicate
            if msg.uid and await email_exists(db, str(msg.uid)):
                skipped.append({"uid": msg.uid, "reason": "already stored"})
                continue

            from_addr = msg.from_ or ""
            contact   = await resolve_contact(db, from_addr)

            if not contact:
                skipped.append({"uid": msg.uid, "from": from_addr, "reason": "not in CRM"})
                continue

            email_id = await store_email(db, msg, contact)
            ingested.append({
                "email_id":   email_id,
                "from":       from_addr,
                "subject":    msg.subject,
                "contact_id": contact["id"],
                "client_id":  contact["client_id"]
            })

    finally:
        await db.close()

    return {
        "status":   "ok",
        "ingested": ingested,
        "skipped":  skipped,
        "counts":   {"ingested": len(ingested), "skipped": len(skipped)}
    }

# ── Action: update contact summary from a specific email ────────────────────

async def update_contact_from_email(email_data: dict, contact_id: str) -> dict:
    db = await get_db()

    try:
        # Pull last 15 emails for this contact for context
        cursor = await db.execute(
            """
            SELECT subject, body, direction, sent_at
            FROM emails
            WHERE contact_id = ?
            ORDER BY sent_at DESC
            LIMIT 15
            """,
            (contact_id,)
        )
        rows = await cursor.fetchall()

        if not rows:
            return {"updated": False, "status": "no emails found for contact"}

        # Build context block for LLM
        email_context = "\n---\n".join([
            f"[{r[2].upper()}] {r[3]} — {r[0]}\n{r[1]}"
            for r in rows
        ])

        # Call Ollama LLM for summary (swap URL/model for OpenAI if preferred)
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3",
                    "messages": [
                        {
                            "role": "user",
                            "content": f"""You are a CRM assistant. Based on the email history below,
write a concise summary of the relationship with this contact.
Cover: key topics discussed, outstanding actions, overall sentiment,
and any important dates or commitments.

EMAIL HISTORY:
{email_context}

SUMMARY:"""
                        }
                    ],
                    "stream": False
                }
            )
            summary = response.json()["message"]["content"]

        # Check if summary exists and update or insert
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