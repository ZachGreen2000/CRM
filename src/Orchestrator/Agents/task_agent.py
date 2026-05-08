# task_agent.py
# Handles all task board operations: create, update, move, delete, list, search, summarise.
# Mirrors email_agent patterns: aiosqlite, Ollama embeddings, plain-dict returns, run() dispatcher.

import os
import uuid
import httpx
import aiosqlite

MODEL = "qwen3:8b"

VALID_COLUMNS   = {"backlog", "todo", "inprogress", "done"}
VALID_PRIORITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}


# ── DB connection ─────────────────────────────────────────────────────────────

async def get_db():
    # __file__ is at: src/Orchestrator/Agents/task_agent.py
    # Go up 3 levels to project root, then into src/Database
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    db_path = os.path.join(project_root, "src", "Database", "crm.db")
    return await aiosqlite.connect(db_path)


# ── Embedding via Ollama ──────────────────────────────────────────────────────

async def generate_embedding(text: str) -> list[float] | None:
    print(f"[TASK_AGENT] Generating embedding for text (length: {len(text)})")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:11434/api/embeddings",
                json={"model": "nomic-embed-text", "input": text[:8000]},
            )
            result = response.json()
            embedding = result.get("embedding")
            if embedding is None and isinstance(result.get("data"), list) and result["data"]:
                embedding = result["data"][0].get("embedding")
            if embedding is None:
                raise ValueError(f"Embedding response missing expected field: {result}")
            print(f"[TASK_AGENT] Embedding generated, vector length: {len(embedding)}")
            return embedding
    except Exception as e:
        print(f"[TASK_AGENT] Error generating embedding: {e}")
        return None


# ── Schema bootstrap ──────────────────────────────────────────────────────────
# Creates the tasks table if it doesn't exist yet.
# Call once at startup or let each function call it lazily via _ensure_table().

async def _ensure_table(db):
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id          TEXT PRIMARY KEY,
            title       TEXT NOT NULL,
            description TEXT,
            priority    TEXT NOT NULL DEFAULT 'MEDIUM',
            column_name TEXT NOT NULL DEFAULT 'backlog',
            due_date    TEXT,
            embedding   BLOB,
            created_at  TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    await db.commit()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _row_to_dict(row, cursor) -> dict:
    """Convert an aiosqlite Row into a plain dict using cursor.description."""
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def _normalise_priority(value: str | None) -> str | None:
    if value is None:
        return None
    upper = value.upper()
    return upper if upper in VALID_PRIORITIES else None


def _normalise_column(value: str | None) -> str | None:
    if value is None:
        return None
    lower = value.lower().replace(" ", "").replace("_", "")
    # Accept friendly aliases
    aliases = {
        "inprogress": "inprogress",
        "in-progress": "inprogress",
        "todo": "todo",
        "to-do": "todo",
        "backlog": "backlog",
        "done": "done",
        "complete": "done",
        "completed": "done",
    }
    return aliases.get(lower)


# ── Action: create_task ───────────────────────────────────────────────────────

async def create_task(
    title:       str,
    description: str | None = None,
    priority:    str | None = None,
    column:      str | None = None,
    due_date:    str | None = None,
) -> dict:
    if not title or not title.strip():
        return {"success": False, "error": "Task title is required"}

    col  = _normalise_column(column)   or "backlog"
    pri  = _normalise_priority(priority) or "MEDIUM"

    task_id = str(uuid.uuid4())

    # Generate embedding for semantic search later
    embed_text = f"{title} {description or ''}".strip()
    embedding  = await generate_embedding(embed_text)

    db = await get_db()
    try:
        await _ensure_table(db)
        await db.execute(
            """
            INSERT INTO tasks (id, title, description, priority, column_name, due_date, embedding, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """,
            (task_id, title.strip(), description, pri, col, due_date,
             str(embedding) if embedding else None),
        )
        await db.commit()
        print(f"[TASK_AGENT] Created task id={task_id} title='{title}' col={col} pri={pri}")
        return {
            "success": True,
            "task_id": task_id,
            "title":   title.strip(),
            "description": description,
            "priority": pri,
            "column":  col,
            "due_date": due_date,
        }
    finally:
        await db.close()


# ── Action: update_task ───────────────────────────────────────────────────────

async def update_task(
    task_id:     str,
    title:       str | None = None,
    description: str | None = None,
    priority:    str | None = None,
    column:      str | None = None,
    due_date:    str | None = None,
) -> dict:
    if not task_id:
        return {"success": False, "error": "task_id is required"}

    db = await get_db()
    try:
        await _ensure_table(db)

        # Confirm task exists
        cursor = await db.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return {"success": False, "error": f"No task found with id '{task_id}'"}

        # Build dynamic SET clause from provided fields only
        fields, values = [], []

        if title is not None:
            fields.append("title = ?");       values.append(title.strip())
        if description is not None:
            fields.append("description = ?"); values.append(description)
        if priority is not None:
            pri = _normalise_priority(priority)
            if not pri:
                return {"success": False, "error": f"Invalid priority '{priority}'. Use: CRITICAL, HIGH, MEDIUM, LOW"}
            fields.append("priority = ?");    values.append(pri)
        if column is not None:
            col = _normalise_column(column)
            if not col:
                return {"success": False, "error": f"Invalid column '{column}'. Use: backlog, todo, inprogress, done"}
            fields.append("column_name = ?"); values.append(col)
        if due_date is not None:
            fields.append("due_date = ?");    values.append(due_date)

        if not fields:
            return {"success": False, "error": "No fields provided to update"}

        # Regenerate embedding if searchable text changed
        if title is not None or description is not None:
            current = _row_to_dict(row, cursor)
            new_title = title or current["title"]
            new_desc  = description or current.get("description", "")
            embedding = await generate_embedding(f"{new_title} {new_desc}".strip())
            if embedding:
                fields.append("embedding = ?"); values.append(str(embedding))

        fields.append("updated_at = datetime('now')")
        values.append(task_id)

        await db.execute(
            f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?",
            values,
        )
        await db.commit()
        print(f"[TASK_AGENT] Updated task id={task_id} fields={[f.split(' =')[0] for f in fields]}")

        # Return updated record
        cursor = await db.execute("SELECT id, title, description, priority, column_name, due_date FROM tasks WHERE id = ?", (task_id,))
        updated = await cursor.fetchone()
        return {
            "success":     True,
            "task_id":     updated[0],
            "title":       updated[1],
            "description": updated[2],
            "priority":    updated[3],
            "column":      updated[4],
            "due_date":    updated[5],
        }
    finally:
        await db.close()


# ── Action: move_task ─────────────────────────────────────────────────────────

async def move_task(task_id: str, column: str) -> dict:
    if not task_id:
        return {"success": False, "error": "task_id is required"}

    col = _normalise_column(column)
    if not col:
        return {"success": False, "error": f"Invalid column '{column}'. Use: backlog, todo, inprogress, done"}

    db = await get_db()
    try:
        await _ensure_table(db)
        cursor = await db.execute("SELECT id, title, column_name FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return {"success": False, "error": f"No task found with id '{task_id}'"}

        prev_col = row[2]
        await db.execute(
            "UPDATE tasks SET column_name = ?, updated_at = datetime('now') WHERE id = ?",
            (col, task_id),
        )
        await db.commit()
        print(f"[TASK_AGENT] Moved task id={task_id} '{row[1]}' from {prev_col} → {col}")
        return {
            "success":      True,
            "task_id":      task_id,
            "title":        row[1],
            "from_column":  prev_col,
            "to_column":    col,
        }
    finally:
        await db.close()


# ── Action: delete_task ───────────────────────────────────────────────────────

async def delete_task(task_id: str) -> dict:
    if not task_id:
        return {"success": False, "error": "task_id is required"}

    db = await get_db()
    try:
        await _ensure_table(db)
        cursor = await db.execute("SELECT id, title FROM tasks WHERE id = ?", (task_id,))
        row = await cursor.fetchone()
        if not row:
            return {"success": False, "error": f"No task found with id '{task_id}'"}

        await db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        await db.commit()
        print(f"[TASK_AGENT] Deleted task id={task_id} title='{row[1]}'")
        return {"success": True, "task_id": task_id, "title": row[1], "deleted": True}
    finally:
        await db.close()


# ── Action: list_tasks ────────────────────────────────────────────────────────

async def list_tasks(
    column:   str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
) -> dict:
    db = await get_db()
    try:
        await _ensure_table(db)

        clauses, values = [], []

        if column:
            col = _normalise_column(column)
            if not col:
                return {"status": "error", "error": f"Invalid column '{column}'"}
            clauses.append("column_name = ?"); values.append(col)

        if priority:
            pri = _normalise_priority(priority)
            if not pri:
                return {"status": "error", "error": f"Invalid priority '{priority}'"}
            clauses.append("priority = ?"); values.append(pri)

        if due_date:
            clauses.append("due_date = ?"); values.append(due_date)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = await db.execute(
            f"SELECT id, title, description, priority, column_name, due_date, created_at FROM tasks {where} ORDER BY created_at DESC",
            values,
        )
        rows = await cursor.fetchall()

        tasks = [
            {
                "task_id":     r[0],
                "title":       r[1],
                "description": r[2],
                "priority":    r[3],
                "column":      r[4],
                "due_date":    r[5],
                "created_at":  r[6],
            }
            for r in rows
        ]

        print(f"[TASK_AGENT] list_tasks returned {len(tasks)} tasks (filters: col={column} pri={priority} date={due_date})")
        return {"status": "ok", "tasks": tasks, "count": len(tasks)}
    finally:
        await db.close()


# ── Action: search_tasks ──────────────────────────────────────────────────────
# Uses cosine-like string comparison against stored embeddings as a lightweight
# fallback. For full vector search, swap the scoring block with your vector_store
# search_similar() call (same pattern as search_emails).

async def search_tasks(query: str, column: str | None = None, limit: int = 5) -> dict:
    if not query:
        return {"status": "error", "error": "query is required", "results": []}

    print(f"[TASK_AGENT] search_tasks query='{query}' col={column} limit={limit}")

    # Generate query embedding
    query_embedding = await generate_embedding(query)

    db = await get_db()
    try:
        await _ensure_table(db)

        clauses, values = [], []
        if column:
            col = _normalise_column(column)
            if col:
                clauses.append("column_name = ?"); values.append(col)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        cursor = await db.execute(
            f"SELECT id, title, description, priority, column_name, due_date, embedding FROM tasks {where}",
            values,
        )
        rows = await cursor.fetchall()

        if not rows:
            return {"status": "ok", "query": query, "results": [], "count": 0}

        # Score each task — vector cosine if embeddings exist, else title substring match
        scored = []
        query_lower = query.lower()

        for r in rows:
            task_id, title, desc, pri, col_name, due_date, stored_emb = r

            score = 0.0
            if query_embedding and stored_emb:
                try:
                    import ast, math
                    stored = ast.literal_eval(stored_emb)
                    # Cosine similarity
                    dot = sum(a * b for a, b in zip(query_embedding, stored))
                    mag_q = math.sqrt(sum(a * a for a in query_embedding))
                    mag_s = math.sqrt(sum(b * b for b in stored))
                    score = dot / (mag_q * mag_s) if mag_q and mag_s else 0.0
                except Exception:
                    # Fallback to keyword match if embedding parse fails
                    score = 1.0 if query_lower in (title or "").lower() else 0.0
            else:
                # No embeddings available — simple substring match
                haystack = f"{title or ''} {desc or ''}".lower()
                score = 1.0 if query_lower in haystack else 0.0

            if score > 0:
                scored.append((score, {
                    "task_id":     task_id,
                    "title":       title,
                    "description": desc,
                    "priority":    pri,
                    "column":      col_name,
                    "due_date":    due_date,
                    "score":       round(score, 4),
                }))

        scored.sort(key=lambda x: x[0], reverse=True)
        results = [item for _, item in scored[:limit]]

        print(f"[TASK_AGENT] search_tasks found {len(results)} results for '{query}'")
        return {"status": "ok", "query": query, "results": results, "count": len(results)}
    finally:
        await db.close()


# ── Action: summarise_tasks ───────────────────────────────────────────────────

async def summarise_tasks(column: str | None = None, project_id: str | None = None) -> dict:
    # Fetch tasks (optionally scoped to a column)
    listed = await list_tasks(column=column)
    if listed["status"] != "ok":
        return listed

    tasks = listed["tasks"]
    if not tasks:
        return {
            "status":  "ok",
            "summary": "The task board is empty — no tasks to summarise.",
            "counts":  {},
        }

    # Build counts by column and priority for context
    from collections import Counter
    col_counts  = Counter(t["column"]   for t in tasks)
    pri_counts  = Counter(t["priority"] for t in tasks)
    overdue_titles = [
        t["title"] for t in tasks
        if t.get("due_date") and t["column"] != "done"
    ]

    board_snapshot = "\n".join(
        f"- [{t['priority']}] ({t['column']}) {t['title']}"
        + (f" — due {t['due_date']}" if t.get("due_date") else "")
        for t in tasks
    )

    prompt = f"""You are a project assistant. Given the task board snapshot below, provide a concise summary covering:
1. Overall progress (tasks per column)
2. Critical or high-priority items needing immediate attention
3. Any tasks that have a due date and are not yet done (potential blockers)
4. Suggested next 2-3 actions

TASK BOARD:
{board_snapshot}

COUNTS BY COLUMN: {dict(col_counts)}
COUNTS BY PRIORITY: {dict(pri_counts)}

Respond in plain conversational English. Be concise."""

    print(f"[TASK_AGENT] Calling LLM for task summary ({len(tasks)} tasks)")
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                },
            )
            summary_text = response.json()["message"]["content"]
    except Exception as e:
        print(f"[TASK_AGENT] LLM call failed: {e}")
        summary_text = (
            f"Board has {len(tasks)} tasks: "
            + ", ".join(f"{v} in {k}" for k, v in col_counts.items())
            + f". Critical: {pri_counts.get('CRITICAL', 0)}, High: {pri_counts.get('HIGH', 0)}."
        )

    return {
        "status":  "ok",
        "summary": summary_text,
        "counts":  {
            "total":    len(tasks),
            "by_column":   dict(col_counts),
            "by_priority": dict(pri_counts),
        },
    }


# ── Agent entry point (called by orchestrator) ────────────────────────────────

async def run(params: dict) -> dict:
    action = params.get("action")

    if action == "create_task":
        return await create_task(
            title=       params.get("title"),
            description= params.get("description"),
            priority=    params.get("priority"),
            column=      params.get("column"),
            due_date=    params.get("due_date"),
        )

    if action == "update_task":
        return await update_task(
            task_id=     params.get("task_id"),
            title=       params.get("title"),
            description= params.get("description"),
            priority=    params.get("priority"),
            column=      params.get("column"),
            due_date=    params.get("due_date"),
        )

    if action == "move_task":
        return await move_task(
            task_id= params.get("task_id"),
            column=  params.get("column"),
        )

    if action == "delete_task":
        return await delete_task(task_id=params.get("task_id"))

    if action == "list_tasks":
        return await list_tasks(
            column=   params.get("column"),
            priority= params.get("priority"),
            due_date= params.get("due_date"),
        )

    if action == "search_tasks":
        return await search_tasks(
            query=  params.get("query", ""),
            column= params.get("column"),
            limit=  params.get("limit", 5),
        )

    if action == "summarise_tasks":
        return await summarise_tasks(
            column=     params.get("column"),
            project_id= params.get("project_id"),
        )

    return {"status": "error", "error": f"Unknown action: {action}"}