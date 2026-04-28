-- Top level: the business
CREATE TABLE clients (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  domain      TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- Person within a business
CREATE TABLE contacts (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_id   UUID REFERENCES clients(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  email       TEXT NOT NULL UNIQUE,
  role        TEXT,
  created_at  TIMESTAMPTZ DEFAULT now()
);

-- Individual emails
CREATE TABLE emails (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  contact_id    UUID REFERENCES contacts(id) ON DELETE CASCADE,
  client_id     UUID REFERENCES clients(id) ON DELETE CASCADE,
  subject       TEXT,
  body          TEXT,
  direction     TEXT CHECK (direction IN ('inbound', 'outbound')),
  sent_at       TIMESTAMPTZ,
  thread_id     TEXT,  -- for grouping email chains
  created_at    TIMESTAMPTZ DEFAULT now()
);