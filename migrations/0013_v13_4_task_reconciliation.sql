ALTER TABLE tasks ADD COLUMN external_import_id TEXT;
CREATE INDEX IF NOT EXISTS idx_tasks_external_import ON tasks(owner_id,external_import_id);
