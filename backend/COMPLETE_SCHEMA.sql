-- ============================================================
-- COMPLETE SCHEMA FOR repo-updates TABLE
-- After running the migration, your table should look like this
-- ============================================================

CREATE TABLE "repo-updates" (
  id BIGSERIAL PRIMARY KEY,
  status TEXT,                              -- READING, WRITING, LOADING
  message TEXT,                             -- Human-readable status message
  code TEXT,                                -- Current/new code content
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  
  -- NEW COLUMNS (add these via ADD_COLUMNS_TO_SUPABASE.sql)
  filename TEXT,                            -- e.g., "_app.js", "index.ts"
  old_code TEXT                             -- Original code before refactoring
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_repo_updates_status ON "repo-updates"(status);
CREATE INDEX IF NOT EXISTS idx_repo_updates_filename ON "repo-updates"(filename);
CREATE INDEX IF NOT EXISTS idx_repo_updates_filename_status ON "repo-updates"(filename, status);
CREATE INDEX IF NOT EXISTS idx_repo_updates_created_at ON "repo-updates"(created_at DESC);

-- Row Level Security
ALTER TABLE "repo-updates" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on repo-updates"
  ON "repo-updates" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read on repo-updates"
  ON "repo-updates" FOR SELECT
  TO authenticated
  USING (true);

-- Real-time subscription
ALTER PUBLICATION supabase_realtime ADD TABLE "repo-updates";

-- ============================================================
-- SAMPLE DATA STRUCTURE
-- ============================================================

-- READING phase:
-- {
--   "id": 1,
--   "status": "READING",
--   "message": "📖 Reading _app.js",
--   "code": "import '@/styles/globals.css'...",
--   "filename": "_app.js",
--   "old_code": null,
--   "created_at": "2025-11-15T22:34:09Z"
-- }

-- WRITING phase:
-- {
--   "id": 2,
--   "status": "WRITING",
--   "message": "✍️ Updating _app.js",
--   "code": "import '@/styles/globals.css'...",  (refactored)
--   "filename": "_app.js",
--   "old_code": "import '@/styles/globals.css'...",  (original)
--   "created_at": "2025-11-15T22:34:15Z"
-- }

-- LOADING phase:
-- {
--   "id": 3,
--   "status": "LOADING",
--   "message": "🏃‍♂️ Pushing changes to GitHub...",
--   "code": null,
--   "filename": null,
--   "old_code": null,
--   "created_at": "2025-11-15T22:34:20Z"
-- }

-- ============================================================
-- USEFUL QUERIES
-- ============================================================

-- Get all updates for a specific file
SELECT * FROM "repo-updates" 
WHERE filename = '_app.js' 
ORDER BY created_at ASC;

-- Get old vs new for a file
SELECT 
  (SELECT code FROM "repo-updates" WHERE filename = '_app.js' AND status = 'READING' LIMIT 1) as old_code,
  (SELECT code FROM "repo-updates" WHERE filename = '_app.js' AND status = 'WRITING' LIMIT 1) as new_code;

-- Get recent processing activity
SELECT filename, status, message, created_at 
FROM "repo-updates" 
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;

-- Count files by status
SELECT status, COUNT(*) as count 
FROM "repo-updates" 
GROUP BY status;

-- Clean up old data (optional, run periodically)
DELETE FROM "repo-updates" 
WHERE created_at < NOW() - INTERVAL '7 days';
