-- ============================================================
-- Dependify 2.0 - Database Migration
-- Add filename and old_code columns to repo-updates table
-- ============================================================
-- Run this SQL in your Supabase SQL Editor
-- https://kuxwmlxghamrslgbxiof.supabase.co
-- ============================================================

-- Add filename column to store the name of the file being processed
ALTER TABLE "repo-updates" 
ADD COLUMN IF NOT EXISTS filename TEXT;

-- Add old_code column to store the original code before refactoring
ALTER TABLE "repo-updates" 
ADD COLUMN IF NOT EXISTS old_code TEXT;

-- Create an index on status for faster filtering (if not exists)
CREATE INDEX IF NOT EXISTS idx_repo_updates_status 
ON "repo-updates"(status);

-- Create an index on filename for faster queries
CREATE INDEX IF NOT EXISTS idx_repo_updates_filename 
ON "repo-updates"(filename);

-- Create a composite index for efficient file matching
CREATE INDEX IF NOT EXISTS idx_repo_updates_filename_status 
ON "repo-updates"(filename, status);

-- Create index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_repo_updates_created_at 
ON "repo-updates"(created_at DESC);

-- ============================================================
-- Verification Query
-- ============================================================
-- Run this to verify all columns exist:
SELECT 
  column_name, 
  data_type, 
  is_nullable,
  column_default
FROM information_schema.columns 
WHERE table_name = 'repo-updates'
ORDER BY ordinal_position;

-- ============================================================
-- Sample Query to Test
-- ============================================================
-- After migration, test with:
-- SELECT id, status, filename, message, created_at 
-- FROM "repo-updates" 
-- ORDER BY created_at DESC 
-- LIMIT 10;
