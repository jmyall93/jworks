PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS companies(
 id TEXT PRIMARY KEY,
 login_code TEXT UNIQUE NOT NULL,
 name TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'active',
 plan TEXT NOT NULL DEFAULT 'professional',
 seat_limit INTEGER NOT NULL DEFAULT 5,
 trial_ends_at TEXT,
 logo_data_url TEXT NOT NULL DEFAULT '',
 address TEXT NOT NULL DEFAULT '',
 report_footer TEXT NOT NULL DEFAULT 'Generated with JWorks',
 created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS company_memberships(
 company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 role TEXT NOT NULL DEFAULT 'user',
 status TEXT NOT NULL DEFAULT 'active',
 created_at TEXT NOT NULL,
 PRIMARY KEY(company_id,user_id)
);
CREATE INDEX IF NOT EXISTS idx_company_members_user ON company_memberships(user_id,status);
CREATE TABLE IF NOT EXISTS subscriptions(
 id TEXT PRIMARY KEY,
 company_id TEXT UNIQUE NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 status TEXT NOT NULL DEFAULT 'active',
 plan TEXT NOT NULL DEFAULT 'professional',
 seat_limit INTEGER NOT NULL DEFAULT 5,
 starts_at TEXT NOT NULL,
 renews_at TEXT,
 trial_ends_at TEXT,
 notes TEXT NOT NULL DEFAULT '',
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS password_reset_tokens(
 id TEXT PRIMARY KEY,
 company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
 token_hash TEXT NOT NULL,
 expires_at TEXT NOT NULL,
 used_at TEXT,
 created_at TEXT NOT NULL
);
-- Preserve existing installations as the owner's initial workspace.
INSERT OR IGNORE INTO companies(id,login_code,name,status,plan,seat_limit,report_footer,created_at)
VALUES('jworks-owner-company','JWORKS-OWNER','My JWorks Workspace','active','owner',999,'Generated with JWorks',datetime('now'));
INSERT OR IGNORE INTO company_memberships(company_id,user_id,role,status,created_at)
SELECT 'jworks-owner-company',id,CASE WHEN id=(SELECT id FROM users ORDER BY created_at ASC LIMIT 1) THEN 'platform_owner' ELSE 'admin' END,'active',datetime('now') FROM users;
INSERT OR IGNORE INTO subscriptions(id,company_id,status,plan,seat_limit,starts_at,created_at,updated_at)
VALUES('jworks-owner-subscription','jworks-owner-company','active','owner',999,datetime('now'),datetime('now'),datetime('now'));
