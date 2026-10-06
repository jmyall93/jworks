-- JWorks V12 commercial platform
ALTER TABLE companies ADD COLUMN accent_color TEXT DEFAULT '#5ee6e6';
ALTER TABLE companies ADD COLUMN branding_mode TEXT DEFAULT 'powered_by_jworks';
ALTER TABLE companies ADD COLUMN feature_flags TEXT DEFAULT '{}';
CREATE TABLE IF NOT EXISTS support_tickets (id TEXT PRIMARY KEY, ticket_number TEXT NOT NULL UNIQUE, company_id TEXT NOT NULL, user_id TEXT NOT NULL, subject TEXT NOT NULL, category TEXT, priority TEXT, description TEXT NOT NULL, diagnostics TEXT, status TEXT DEFAULT 'open', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_support_company ON support_tickets(company_id,created_at);
CREATE TABLE IF NOT EXISTS knowledge_articles (id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT, summary TEXT, body TEXT, status TEXT DEFAULT 'published', created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
