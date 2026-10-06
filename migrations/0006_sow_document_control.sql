PRAGMA foreign_keys=ON;
ALTER TABLE scopes_of_work ADD COLUMN document_project_code TEXT NOT NULL DEFAULT '';
ALTER TABLE scopes_of_work ADD COLUMN revision_label TEXT NOT NULL DEFAULT '0';
ALTER TABLE scopes_of_work ADD COLUMN revision_date TEXT NOT NULL DEFAULT '';
ALTER TABLE scopes_of_work ADD COLUMN revision_history_json TEXT NOT NULL DEFAULT '[]';
