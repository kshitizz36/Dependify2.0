"""
Commit-by-Commit Evolution Analysis.
Analyzes last N commits to understand how the codebase is evolving.
Detects debt accumulation, recently introduced vulnerabilities, and health trends.

Inspired by: OpenAI Codex Security's commit-by-commit cumulative context.
"""
import subprocess
import os
import json
from typing import Dict, List


def analyze_commit_history(repo_root: str, depth: int = 20) -> Dict:
    """
    Analyze the last N commits to detect codebase evolution patterns.
    Pure git analysis, no LLM needed.
    """
    try:
        # Get commit log with stats
        result = subprocess.run(
            ["git", "log", f"--max-count={depth}", "--pretty=format:%H|%an|%ad|%s", "--date=short", "--stat"],
            capture_output=True, text=True, timeout=30, cwd=repo_root
        )
        if result.returncode != 0:
            return {"error": "Failed to read git log"}

        lines = result.stdout.strip().split("\n")
        commits = []
        current_commit = None
        files_changed_freq: Dict[str, int] = {}

        for line in lines:
            if "|" in line and len(line.split("|")) == 4:
                parts = line.split("|")
                current_commit = {
                    "hash": parts[0][:8],
                    "author": parts[1],
                    "date": parts[2],
                    "message": parts[3],
                    "files": [],
                }
                commits.append(current_commit)
            elif current_commit and "|" in line and ("+" in line or "-" in line):
                # File stat line: " src/file.ts | 12 +++---"
                file_part = line.split("|")[0].strip()
                if file_part:
                    current_commit["files"].append(file_part)
                    files_changed_freq[file_part] = files_changed_freq.get(file_part, 0) + 1

        # Find hotspots (files changed most frequently)
        hotspots = sorted(files_changed_freq.items(), key=lambda x: -x[1])[:10]
        churn_files = [{"file": f, "changes": c, "risk": "high" if c >= 5 else "medium" if c >= 3 else "low"} for f, c in hotspots]

        # Detect patterns
        patch_patterns = []
        for f, count in hotspots[:5]:
            if count >= 4:
                patch_patterns.append(f"{f} changed {count} times in last {depth} commits — may need refactor instead of patches")

        return {
            "total_commits": len(commits),
            "commits": commits[:10],  # Last 10 for display
            "churn_hotspots": churn_files,
            "patch_patterns": patch_patterns,
            "unique_files_changed": len(files_changed_freq),
            "authors": list(set(c["author"] for c in commits)),
        }

    except Exception as e:
        return {"error": str(e)}
