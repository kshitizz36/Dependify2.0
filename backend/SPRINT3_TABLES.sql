-- Sprint 3: Scan feedback table for learning loop
CREATE TABLE IF NOT EXISTS "scan-feedback" (
  id BIGSERIAL PRIMARY KEY,
  run_id TEXT NOT NULL,
  repo_url TEXT NOT NULL,
  file_path TEXT NOT NULL,
  change_category TEXT DEFAULT '',
  user_action TEXT DEFAULT '',
  pr_url TEXT DEFAULT '',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_scan_feedback_repo ON "scan-feedback"(repo_url);
CREATE INDEX IF NOT EXISTS idx_scan_feedback_run ON "scan-feedback"(run_id);

ALTER TABLE "scan-feedback" ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service role full access on scan-feedback"
  ON "scan-feedback" FOR ALL
  TO service_role
  USING (true) WITH CHECK (true);
