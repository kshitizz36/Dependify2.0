"""
Repo Intelligence Brief Generator.
Generates architecture overviews, tech stack detection, and onboarding briefs.
Uses repo metadata (filesystem analysis) + one Sonnet call for the brief.
"""
import json
from anthropic import Anthropic
from config import Config
from checker import collect_repo_metadata

client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

BRIEF_MODEL = "claude-sonnet-4-20250514"


def generate_repo_brief(repo_path: str) -> dict:
    """
    Generate a complete repo intelligence brief.

    Returns:
        dict with keys: tech_stack, architecture, frameworks, entry_points,
        test_coverage, risky_hotspots, setup_hint, onboarding_summary, raw_metadata
    """
    # Step 1: Collect structural metadata (no LLM, pure filesystem)
    metadata = collect_repo_metadata(repo_path)

    # Step 2: Build a condensed summary for the LLM
    manifest_summaries = {}
    for name, content in metadata.get("manifests", {}).items():
        # Truncate manifests to avoid token waste
        manifest_summaries[name] = content[:3000]

    context = {
        "file_count_by_extension": metadata["file_count_by_ext"],
        "total_files": metadata["total_files"],
        "total_lines": metadata["total_lines"],
        "top_directories": metadata["directories"][:50],
        "test_files_count": len(metadata["test_files"]),
        "test_file_samples": metadata["test_files"][:10],
        "config_files": metadata["config_files"],
        "has_dockerfile": metadata["has_dockerfile"],
        "has_ci": metadata["has_ci"],
        "manifests": manifest_summaries,
    }

    # Step 3: One Sonnet call to generate the brief
    prompt = (
        "You are a senior software architect. Given this project metadata, generate a comprehensive "
        "developer onboarding brief.\n\n"
        f"PROJECT METADATA:\n```json\n{json.dumps(context, indent=2)}\n```\n\n"
        "Return ONLY valid JSON with this structure:\n"
        "{\n"
        '  "tech_stack": {"languages": ["Python", "TypeScript"], "versions": {"node": "18.x", "python": "3.10"}, "package_manager": "npm"},\n'
        '  "architecture": "monolith|microservices|serverless|monorepo|library",\n'
        '  "frameworks": ["Next.js 15", "FastAPI", "React 18"],\n'
        '  "entry_points": ["src/app/page.tsx", "backend/server.py"],\n'
        '  "test_coverage_estimate": "low|medium|high",\n'
        '  "risky_hotspots": ["path/to/complex/file.ts - reason"],\n'
        '  "setup_hint": "npm install && npm run dev",\n'
        '  "onboarding_summary": "A 3-5 sentence plain-English summary a new developer can read to understand the project."\n'
        "}"
    )

    try:
        response = client.messages.create(
            model=BRIEF_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        brief = json.loads(text)
        brief["raw_metadata"] = {
            "total_files": metadata["total_files"],
            "total_lines": metadata["total_lines"],
            "file_count_by_ext": metadata["file_count_by_ext"],
            "test_files_count": len(metadata["test_files"]),
            "has_dockerfile": metadata["has_dockerfile"],
            "has_ci": metadata["has_ci"],
        }
        return brief

    except Exception as e:
        print(f"Error generating repo brief: {e}")
        # Return a basic brief from metadata alone (no LLM fallback)
        return {
            "tech_stack": {"languages": list(metadata["file_count_by_ext"].keys())},
            "architecture": "unknown",
            "frameworks": [],
            "entry_points": [],
            "test_coverage_estimate": "low" if len(metadata["test_files"]) < 5 else "medium",
            "risky_hotspots": [],
            "setup_hint": "",
            "onboarding_summary": f"Project with {metadata['total_files']} code files across {len(metadata['file_count_by_ext'])} languages.",
            "raw_metadata": {
                "total_files": metadata["total_files"],
                "total_lines": metadata["total_lines"],
                "file_count_by_ext": metadata["file_count_by_ext"],
                "test_files_count": len(metadata["test_files"]),
                "has_dockerfile": metadata["has_dockerfile"],
                "has_ci": metadata["has_ci"],
            },
            "error": str(e),
        }
