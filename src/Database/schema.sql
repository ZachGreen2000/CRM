-- SQLite schema for CRM database
-- Run this to initialize the database: sqlite3 src/Database/crm.db < src/Database/schema.sql

-- Top level: the business
CREATE TABLE clients (
  id          TEXT PRIMARY KEY,
  name        TEXT NOT NULL,
  domain      TEXT,
  created_at  TEXT DEFAULT (datetime('now'))
);

-- Person within a business
CREATE TABLE contacts (
  id          TEXT PRIMARY KEY,
  client_id   TEXT REFERENCES clients(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  email       TEXT NOT NULL UNIQUE,
  role        TEXT,
  created_at  TEXT DEFAULT (datetime('now'))
);

-- Individual emails (embeddings now stored in ChromaDB vector store)
CREATE TABLE emails (
  id            TEXT PRIMARY KEY,
  contact_id    TEXT REFERENCES contacts(id) ON DELETE CASCADE,
  client_id     TEXT REFERENCES clients(id) ON DELETE CASCADE,
  subject       TEXT,
  body          TEXT,
  direction     TEXT CHECK (direction IN ('inbound', 'outbound')),
  sent_at       TEXT,
  thread_id     TEXT,  -- for grouping email chains
  created_at    TEXT DEFAULT (datetime('now'))
);

-- Rolling AI summary per contact (embeddings now stored in ChromaDB)
-- Summary text cached here, vector embeddings in ChromaDB
CREATE TABLE contact_summaries (
  id            TEXT PRIMARY KEY,
  contact_id    TEXT REFERENCES contacts(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  updated_at    TEXT DEFAULT (datetime('now')),
  email_count   INTEGER DEFAULT 0,  -- track number of emails summarized
  last_email_id TEXT  -- track the last email processed for this summary
);

-- Thread summaries (incremental summaries for email threads)
-- Summary text cached here, vector embeddings in ChromaDB
CREATE TABLE thread_summaries (
  id            TEXT PRIMARY KEY,
  thread_id     TEXT UNIQUE,  -- matches emails.thread_id
  contact_id    TEXT REFERENCES contacts(id) ON DELETE CASCADE,
  summary_text  TEXT,
  updated_at    TEXT DEFAULT (datetime('now')),
  email_count   INTEGER DEFAULT 0
);

-- Rolling AI summary per client
CREATE TABLE client_summaries (
  id            TEXT PRIMARY KEY,
  client_id     TEXT REFERENCES clients(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  embedding     TEXT,  -- JSON string representation of embedding vector
  updated_at    TEXT DEFAULT (datetime('now'))
);