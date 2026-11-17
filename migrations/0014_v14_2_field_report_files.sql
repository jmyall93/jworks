-- JWorks 14.2: persistent, company-scoped report attachments (up to 1MB/file)
CREATE TABLE IF NOT EXISTS field_report_files (id TEXT PRIMARY KEY,report_id TEXT NOT NULL REFERENCES field_reports(id) ON DELETE CASCADE,owner_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,data TEXT NOT NULL,created_at TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_field_report_files_report ON field_report_files(report_id);
