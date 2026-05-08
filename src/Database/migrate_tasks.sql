-- migrate_tasks.sql
-- Adds the tasks table and indexes to an existing crm.db without touching other tables.
-- Run with: sqlite3 src/Database/crm.db < src/Database/migrate_tasks.sql

-- Task board (columns: backlog | todo | inprogress | done)
CREATE TABLE IF NOT EXISTS tasks (
  id            TEXT PRIMARY KEY,
  title         TEXT NOT NULL,
  description   TEXT,
  priority      TEXT NOT NULL DEFAULT 'MEDIUM'
                  CHECK (priority IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW')),
  column_name   TEXT NOT NULL DEFAULT 'backlog'
                  CHECK (column_name IN ('backlog', 'todo', 'inprogress', 'done')),
  due_date      TEXT,
  embedding     TEXT,  -- JSON string representation of embedding vector (nomic-embed-text)
  created_at    TEXT DEFAULT (datetime('now')),
  updated_at    TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_tasks_column   ON tasks (column_name);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks (priority);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks (due_date);