-- ============================================================
-- SPRINT 1 V2: New tables for repo briefs and file-level scores
-- Run this in your Supabase SQL Editor
-- (repo-debt-summaries and user-repos already exist from V1)
-- ============================================================

-- Table: repo-briefs
-- Stores repo intelligence briefs (architecture, tech stack, onboarding)
CREATE TABLE IF NOT EXISTS "repo-briefs" (
  id BIGSERIAL PRIMARY KEY,
  repo_url TEXT NOT NULL,
  user_id TEXT NOT NULL,
  brief_json JSONB NOT NULL DEFAULT '{}',
  brief_markdown TEXT DEFAULT '',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_repo_briefs_repo ON "repo-briefs"(repo_url);
CREATE INDEX IF NOT EXISTS idx_repo_briefs_user ON "repo-briefs"(user_id);
CREATE INDEX IF NOT EXISTS idx_repo_briefs_created ON "repo-briefs"(created_at DESC);

ALTER TABLE "repo-briefs" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on repo-briefs"
  ON "repo-briefs" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read on repo-briefs"
  ON "repo-briefs" FOR SELECT
  TO authenticated
  USING (true);


-- Table: file-scores
-- Stores per-file risk scores for each scan run (heatmap data)
CREATE TABLE IF NOT EXISTS "file-scores" (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL,
  repo_url TEXT NOT NULL,
  file_path TEXT NOT NULL,
  risk_score INTEGER DEFAULT 0,
  findings_count INTEGER DEFAULT 0,
  severity_breakdown JSONB DEFAULT '{}',
  category_breakdown JSONB DEFAULT '{}',
  line_count INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_file_scores_run ON "file-scores"(run_id);
CREATE INDEX IF NOT EXISTS idx_file_scores_repo ON "file-scores"(repo_url);
CREATE INDEX IF NOT EXISTS idx_file_scores_created ON "file-scores"(created_at DESC);

ALTER TABLE "file-scores" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on file-scores"
  ON "file-scores" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read on file-scores"
  ON "file-scores" FOR SELECT
  TO authenticated
  USING (true);
