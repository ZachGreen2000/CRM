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

-- Individual emails
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

-- One embedding per email (for retrieval)
-- Note: SQLite doesn't have vector extension, storing as TEXT for now
CREATE TABLE email_embeddings (
  id          TEXT PRIMARY KEY,
  email_id    TEXT REFERENCES emails(id) ON DELETE CASCADE,
  embedding   TEXT  -- JSON string representation of embedding vector
);

-- Rolling AI summary per contact (regenerated periodically)
CREATE TABLE contact_summaries (
  id            TEXT PRIMARY KEY,
  contact_id    TEXT REFERENCES contacts(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  embedding     TEXT,  -- JSON string representation of embedding vector
  updated_at    TEXT DEFAULT (datetime('now'))
);

-- Rolling AI summary per client
CREATE TABLE client_summaries (
  id            TEXT PRIMARY KEY,
  client_id     TEXT REFERENCES clients(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  embedding     TEXT,  -- JSON string representation of embedding vector
  updated_at    TEXT DEFAULT (datetime('now'))
);