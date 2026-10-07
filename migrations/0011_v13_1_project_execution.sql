-- JWorks 13.1 project execution fields used by the cloud UI.
ALTER TABLE tasks ADD COLUMN phase_id TEXT REFERENCES phases(id) ON DELETE SET NULL;
ALTER TABLE tasks ADD COLUMN assignee TEXT NOT NULL DEFAULT '';
ALTER TABLE tasks ADD COLUMN estimated_hours REAL NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN actual_hours REAL NOT NULL DEFAULT 0;
ALTER TABLE tasks ADD COLUMN tags TEXT NOT NULL DEFAULT '';
CREATE INDEX IF NOT EXISTS idx_tasks_phase ON tasks(owner_id,phase_id);
