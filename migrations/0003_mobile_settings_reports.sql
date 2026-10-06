PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS custom_report_templates(
 id TEXT PRIMARY KEY,
 owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 title TEXT NOT NULL,
 config_json TEXT NOT NULL DEFAULT '{}',
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_custom_report_templates_owner ON custom_report_templates(owner_id,created_at);
