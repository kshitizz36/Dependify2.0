"""
Learning Loop - PR merge tracking and scan preference learning.
Tracks what users merge/reject to tune future scans.

Inspired by: OpenAI Codex Security (84% noise reduction on repeated scans).
Our advantage: We learn from actual PR merge decisions, not our own output.
"""
import json
from typing import Optional, Dict, List
from config import Config
import supabase
import httpx

supabase_client = supabase.create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


async def check_pr_status(pr_url: str, github_token: str) -> Optional[Dict]:
    """
    Check the status of a Dependify PR on GitHub.
    Returns merge status, which files were included, etc.
    """
    if not pr_url or not github_token:
        return None

    # Extract owner/repo/number from PR URL
    # https://github.com/owner/repo/pull/123
    try:
        parts = pr_url.rstrip("/").split("/")
        pr_number = parts[-1]
        repo_name = parts[-3]
        owner = parts[-4]
    except (IndexError, ValueError):
        return None

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}",
                headers=headers,
                timeout=10.0,
            )
            if resp.status_code != 200:
                return None

            pr = resp.json()
            return {
                "state": pr.get("state"),  # open, closed
                "merged": pr.get("merged", False),
                "merged_at": pr.get("merged_at"),
                "closed_at": pr.get("closed_at"),
                "changed_files": pr.get("changed_files", 0),
                "additions": pr.get("additions", 0),
                "deletions": pr.get("deletions", 0),
            }
    except Exception as e:
        print(f"Error checking PR status: {e}")
        return None


def save_scan_feedback(
    run_id: str,
    repo_url: str,
    file_path: str,
    change_category: str,
    user_action: str,  # merged, rejected, modified, ignored
    pr_url: Optional[str] = None,
):
    """Save feedback for a single file change."""
    try:
        supabase_client.table("scan-feedback").insert({
            "run_id": run_id,
            "repo_url": repo_url,
            "file_path": file_path,
            "change_category": change_category,
            "user_action": user_action,
            "pr_url": pr_url or "",
        }).execute()
    except Exception as e:
        print(f"Error saving scan feedback: {e}")


def get_repo_preferences(repo_url: str) -> Dict:
    """
    Get learned preferences for a repo based on past PR merge/reject history.
    Returns guidance for the Reader agent.
    """
    try:
        # Get all feedback for this repo
        result = supabase_client.table("scan-feedback") \
            .select("change_category,user_action") \
            .eq("repo_url", repo_url) \
            .execute()

        if not result.data:
            return {"has_history": False, "scan_count": 0}

        # Tally by category
        category_stats: Dict[str, Dict[str, int]] = {}
        for row in result.data:
            cat = row.get("change_category", "unknown")
            action = row.get("user_action", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"merged": 0, "rejected": 0, "total": 0}
            category_stats[cat]["total"] += 1
            if action == "merged":
                category_stats[cat]["merged"] += 1
            elif action in ("rejected", "ignored"):
                category_stats[cat]["rejected"] += 1

        # Compute preferences
        preferred_categories = []
        rejected_categories = []
        for cat, stats in category_stats.items():
            if stats["total"] >= 2:
                merge_rate = stats["merged"] / stats["total"]
                if merge_rate >= 0.7:
                    preferred_categories.append(cat)
                elif merge_rate <= 0.3:
                    rejected_categories.append(cat)

        return {
            "has_history": True,
            "scan_count": len(result.data),
            "preferred_categories": preferred_categories,
            "rejected_categories": rejected_categories,
            "category_stats": category_stats,
        }
    except Exception as e:
        print(f"Error getting repo preferences: {e}")
        return {"has_history": False, "scan_count": 0}


def build_learning_context(repo_url: str) -> str:
    """
    Build a context string for the Reader agent based on past scan history.
    This is injected into the Reader prompt to reduce noise.
    """
    prefs = get_repo_preferences(repo_url)

    if not prefs.get("has_history") or prefs.get("scan_count", 0) < 3:
        return ""

    context_parts = []
    context_parts.append(
        f"LEARNING CONTEXT: This repo has been scanned {prefs['scan_count']} times before."
    )

    if prefs.get("preferred_categories"):
        context_parts.append(
            f"The team consistently merges these types of changes: {', '.join(prefs['preferred_categories'])}. "
            "Prioritize these categories."
        )

    if prefs.get("rejected_categories"):
        context_parts.append(
            f"The team consistently rejects these types of changes: {', '.join(prefs['rejected_categories'])}. "
            "Deprioritize or skip these unless severity is HIGH or above."
        )

    return "\n".join(context_parts)
