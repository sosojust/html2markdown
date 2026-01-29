-- 20260129_add_user_preferences.sql
-- Add preferences column to users table to store user configurations (e.g. Notion/Obsidian settings)

-- For PostgreSQL/MySQL
ALTER TABLE users ADD COLUMN preferences TEXT;

-- For SQLite (Split into separate statements if needed, but standard SQL supports ADD COLUMN)
-- ALTER TABLE users ADD COLUMN preferences TEXT;
