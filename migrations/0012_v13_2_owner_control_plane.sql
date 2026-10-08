-- JWorks V13.2 owner control plane
CREATE TABLE IF NOT EXISTS platform_settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL DEFAULT '',
  updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS platform_audit (
  id TEXT PRIMARY KEY,
  actor_user_id TEXT,
  action TEXT NOT NULL,
  target_type TEXT,
  target_id TEXT,
  detail TEXT,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_platform_audit_created ON platform_audit(created_at);
INSERT OR IGNORE INTO platform_settings(key,value,updated_at) VALUES
 ('maintenance_mode','false',CURRENT_TIMESTAMP),('default_plan','professional',CURRENT_TIMESTAMP),
 ('default_seat_limit','5',CURRENT_TIMESTAMP),('trial_days','14',CURRENT_TIMESTAMP),
 ('support_email','',CURRENT_TIMESTAMP),('ai_enabled','true',CURRENT_TIMESTAMP),
 ('reports_enabled','true',CURRENT_TIMESTAMP),('new_gantt_enabled','true',CURRENT_TIMESTAMP);
