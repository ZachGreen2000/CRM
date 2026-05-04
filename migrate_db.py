#!/usr/bin/env python3
"""
Database Migration Script
Updates existing CRM database to use new vector store architecture.
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Migrate existing database to new schema."""

    # Find database path
    project_root = Path(__file__).parent.parent
    db_path = project_root / "src" / "Database" / "crm.db"

    if not db_path.exists():
        print(f"Database not found at {db_path}")
        return

    print(f"Migrating database at {db_path}")

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # Check if old tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='email_embeddings'")
        if cursor.fetchone():
            print("Found old email_embeddings table - this will be replaced by ChromaDB")
            # Note: We don't drop the table yet, just warn the user

        # Add new columns to contact_summaries if they don't exist
        cursor.execute("PRAGMA table_info(contact_summaries)")
        columns = [row[1] for row in cursor.fetchall()]

        if 'email_count' not in columns:
            print("Adding email_count column to contact_summaries")
            cursor.execute("ALTER TABLE contact_summaries ADD COLUMN email_count INTEGER DEFAULT 0")

        if 'last_email_id' not in columns:
            print("Adding last_email_id column to contact_summaries")
            cursor.execute("ALTER TABLE contact_summaries ADD COLUMN last_email_id TEXT")

        # Create thread_summaries table if it doesn't exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='thread_summaries'")
        if not cursor.fetchone():
            print("Creating thread_summaries table")
            cursor.execute("""
                CREATE TABLE thread_summaries (
                    id            TEXT PRIMARY KEY,
                    thread_id     TEXT UNIQUE,
                    contact_id    TEXT REFERENCES contacts(id) ON DELETE CASCADE,
                    summary_text  TEXT,
                    updated_at    TEXT DEFAULT (datetime('now')),
                    email_count   INTEGER DEFAULT 0
                )
            """)

        conn.commit()
        print("Migration completed successfully!")
        print("\nNote: Email embeddings have been moved to ChromaDB vector store.")
        print("The old email_embeddings table can be dropped after verifying the migration.")

    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()

    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()