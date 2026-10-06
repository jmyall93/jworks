CREATE TABLE IF NOT EXISTS demo_records (
  id TEXT PRIMARY KEY,
  company_id TEXT NOT NULL,
  owner_id TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  demo_set TEXT NOT NULL DEFAULT 'northstar-v1',
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_demo_company ON demo_records(company_id,demo_set);
