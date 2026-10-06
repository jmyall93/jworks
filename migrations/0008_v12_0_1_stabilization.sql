-- JWorks V12.0.1 stabilization and commercial website
ALTER TABLE companies ADD COLUMN support_email TEXT DEFAULT '';
ALTER TABLE companies ADD COLUMN inactivity_minutes INTEGER DEFAULT 10;
ALTER TABLE companies ADD COLUMN document_branding TEXT DEFAULT 'powered_by_jworks';
CREATE TABLE IF NOT EXISTS user_preferences (user_id TEXT PRIMARY KEY, settings_json TEXT NOT NULL DEFAULT '{}', updated_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS public_inquiries (id TEXT PRIMARY KEY, inquiry_number TEXT NOT NULL UNIQUE, name TEXT, email TEXT NOT NULL, category TEXT, subject TEXT NOT NULL, message TEXT NOT NULL, status TEXT DEFAULT 'open', created_at TEXT NOT NULL);
