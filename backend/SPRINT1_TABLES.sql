-- ============================================================
-- SPRINT 1: New tables for user repo linking & debt scoring
-- Run this in your Supabase SQL Editor
-- ============================================================

-- Table: user-repos
-- Stores repos that users have linked to their Dependify dashboard
CREATE TABLE IF NOT EXISTS "user-repos" (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  username TEXT NOT NULL,
  repo_url TEXT NOT NULL,
  repo_name TEXT NOT NULL,
  repo_owner TEXT NOT NULL,
  language TEXT,
  linked_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Prevent duplicate links
  UNIQUE(user_id, repo_url)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_user_repos_user_id ON "user-repos"(user_id);
CREATE INDEX IF NOT EXISTS idx_user_repos_linked_at ON "user-repos"(linked_at DESC);

-- Row Level Security
ALTER TABLE "user-repos" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on user-repos"
  ON "user-repos" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read own repos"
  ON "user-repos" FOR SELECT
  TO authenticated
  USING (true);


-- ============================================================
-- Table: repo-debt-summaries
-- Stores aggregate debt scores per repo (for historical tracking)
-- Populated after each scan/update run
-- ============================================================

CREATE TABLE IF NOT EXISTS "repo-debt-summaries" (
  id BIGSERIAL PRIMARY KEY,
  repository_url TEXT NOT NULL,
  run_id TEXT,

  -- Overall metrics
  overall_debt_score INTEGER DEFAULT 0,  -- 0-100
  score_grade TEXT DEFAULT 'A',          -- A, B, C, D, F

  -- Severity counts
  critical_count INTEGER DEFAULT 0,
  high_count INTEGER DEFAULT 0,
  medium_count INTEGER DEFAULT 0,
  low_count INTEGER DEFAULT 0,

  -- Improvements
  files_analyzed INTEGER DEFAULT 0,
  files_updated INTEGER DEFAULT 0,
  improvement_percentage FLOAT DEFAULT 0,
  estimated_hours_saved FLOAT DEFAULT 0,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_debt_summaries_repo ON "repo-debt-summaries"(repository_url);
CREATE INDEX IF NOT EXISTS idx_debt_summaries_created_at ON "repo-debt-summaries"(created_at DESC);

-- Row Level Security
ALTER TABLE "repo-debt-summaries" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on repo-debt-summaries"
  ON "repo-debt-summaries" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);

CREATE POLICY "Allow authenticated read on repo-debt-summaries"
  ON "repo-debt-summaries" FOR SELECT
  TO authenticated
  USING (true);
