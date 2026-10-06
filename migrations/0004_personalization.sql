PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS user_preferences(
 user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 config_json TEXT NOT NULL DEFAULT '{}',
 updated_at TEXT NOT NULL
);
