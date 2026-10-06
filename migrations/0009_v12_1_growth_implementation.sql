CREATE TABLE IF NOT EXISTS implementations (id TEXT PRIMARY KEY, company_id TEXT, company_name TEXT NOT NULL, source_platform TEXT DEFAULT 'excel', status TEXT DEFAULT 'discovery', progress INTEGER DEFAULT 0, owner_notes TEXT DEFAULT '', config_json TEXT DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS implementation_steps (id TEXT PRIMARY KEY, implementation_id TEXT NOT NULL, step_key TEXT NOT NULL, title TEXT NOT NULL, status TEXT DEFAULT 'pending', notes TEXT DEFAULT '', sort_order INTEGER DEFAULT 0, updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS migration_profiles (id TEXT PRIMARY KEY, implementation_id TEXT, source_platform TEXT NOT NULL, name TEXT NOT NULL, mapping_json TEXT DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_impl_company ON implementations(company_id);
CREATE INDEX IF NOT EXISTS idx_impl_steps ON implementation_steps(implementation_id,sort_order);
