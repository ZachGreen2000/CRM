CREATE EXTENSION IF NOT EXISTS vector;

-- One embedding per email (for retrieval)
CREATE TABLE email_embeddings (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  email_id    UUID REFERENCES emails(id) ON DELETE CASCADE,
  embedding   vector(768)  -- 1536 for OpenAI, 768 for others
);

-- Rolling AI summary per contact (regenerated periodically)
CREATE TABLE contact_summaries (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id    UUID REFERENCES contacts(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  embedding     vector(768),
  updated_at    TIMESTAMPTZ DEFAULT now()
);

-- Rolling AI summary per client
CREATE TABLE client_summaries (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id     UUID REFERENCES clients(id) ON DELETE CASCADE UNIQUE,
  summary_text  TEXT,
  embedding     vector(768),
  updated_at    TIMESTAMPTZ DEFAULT now()
);