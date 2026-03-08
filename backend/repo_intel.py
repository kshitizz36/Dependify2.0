"""
Repo Intelligence & Enhanced Onboarding.
Generates architecture overviews, dependency graphs, complexity analysis,
API route maps, and verified onboarding briefs.

The "holy shit" feature: link a repo, understand it in 60 seconds.
"""
import os
import re
import json
from typing import Dict, List
from anthropic import Anthropic
from config import Config
from checker import collect_repo_metadata, get_all_files_recursively, CODE_EXTENSIONS, MAX_FILE_LINES

client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

BRIEF_MODEL = "claude-sonnet-4-20250514"


def detect_api_routes(repo_root: str) -> List[Dict]:
    """Detect all API routes/endpoints in the codebase."""
    routes = []
    patterns = [
        # FastAPI / Flask
        (re.compile(r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'), "python"),
        # Express.js
        (re.compile(r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)'), "javascript"),
        # Next.js API routes (file-based)
        (re.compile(r'export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH)'), "nextjs"),
        # Spring
        (re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*["\']([^"\']+)'), "java"),
        # Django
        (re.compile(r'path\s*\(\s*["\']([^"\']+)'), "django"),
    ]

    for fp in get_all_files_recursively(repo_root):
        rel_path = os.path.relpath(fp, repo_root)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        for pattern, framework in patterns:
            for match in pattern.finditer(content):
                groups = match.groups()
                if framework == "nextjs":
                    method = groups[0]
                    path = f"/api/{'/'.join(rel_path.replace('app/api/', '').replace('/route.ts', '').replace('/route.js', '').split('/'))}"
                    routes.append({"method": method, "path": path, "file": rel_path, "framework": framework})
                elif framework == "django":
                    routes.append({"method": "ANY", "path": groups[0], "file": rel_path, "framework": framework})
                else:
                    routes.append({"method": groups[0].upper(), "path": groups[1], "file": rel_path, "framework": framework})

    return routes


def analyze_complexity(repo_root: str) -> Dict:
    """Analyze code complexity metrics without LLM."""
    file_metrics = []

    for fp in get_all_files_recursively(repo_root):
        rel_path = os.path.relpath(fp, repo_root)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            continue

        line_count = len(lines)
        if line_count == 0:
            continue

        # Count complexity indicators
        import_count = sum(1 for l in lines if l.strip().startswith(('import ', 'from ', 'require(', '#include')))
        function_count = sum(1 for l in lines if re.match(r'\s*(def |function |const \w+ = |async function |export (?:default )?function )', l))
        class_count = sum(1 for l in lines if re.match(r'\s*class \w+', l))
        todo_count = sum(1 for l in lines if 'TODO' in l or 'FIXME' in l or 'HACK' in l)
        comment_lines = sum(1 for l in lines if l.strip().startswith(('#', '//', '/*', '*')))

        # Nesting depth (rough estimate via indentation)
        max_indent = 0
        for l in lines:
            stripped = l.lstrip()
            if stripped:
                indent = len(l) - len(stripped)
                max_indent = max(max_indent, indent)

        # Complexity score: weighted combination
        complexity = (
            (line_count / 100) * 2 +
            import_count * 0.5 +
            (max_indent / 4) * 1.5 +
            todo_count * 2
        )

        file_metrics.append({
            "file": rel_path,
            "lines": line_count,
            "functions": function_count,
            "classes": class_count,
            "imports": import_count,
            "todos": todo_count,
            "comment_ratio": round(comment_lines / max(line_count, 1) * 100, 1),
            "max_nesting": max_indent // 4,
            "complexity_score": round(complexity, 1),
        })

    # Sort by complexity
    file_metrics.sort(key=lambda x: -x["complexity_score"])

    # Summary
    total_lines = sum(f["lines"] for f in file_metrics)
    total_functions = sum(f["functions"] for f in file_metrics)
    total_todos = sum(f["todos"] for f in file_metrics)
    avg_comment_ratio = sum(f["comment_ratio"] for f in file_metrics) / max(len(file_metrics), 1)

    return {
        "total_files": len(file_metrics),
        "total_lines": total_lines,
        "total_functions": total_functions,
        "total_todos": total_todos,
        "avg_comment_ratio": round(avg_comment_ratio, 1),
        "most_complex": file_metrics[:10],
        "simplest": file_metrics[-5:] if len(file_metrics) > 5 else [],
    }


def detect_env_vars(repo_root: str) -> List[Dict]:
    """Detect environment variables used in the codebase."""
    env_vars = {}
    patterns = [
        re.compile(r'process\.env\.(\w+)'),
        re.compile(r'os\.getenv\s*\(\s*["\'](\w+)'),
        re.compile(r'os\.environ\s*\[\s*["\'](\w+)'),
        re.compile(r'os\.Getenv\s*\(\s*["\'](\w+)'),
    ]

    for fp in get_all_files_recursively(repo_root):
        rel_path = os.path.relpath(fp, repo_root)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        for pattern in patterns:
            for match in pattern.finditer(content):
                var_name = match.group(1)
                if var_name not in env_vars:
                    env_vars[var_name] = {"name": var_name, "used_in": []}
                if rel_path not in env_vars[var_name]["used_in"]:
                    env_vars[var_name]["used_in"].append(rel_path)

    # Check .env.example for defaults
    for env_file in [".env.example", ".env.sample", ".env.template"]:
        env_path = os.path.join(repo_root, env_file)
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        if '=' in line and not line.strip().startswith('#'):
                            key = line.split('=')[0].strip()
                            if key in env_vars:
                                env_vars[key]["has_example"] = True
            except Exception:
                pass

    return list(env_vars.values())


def generate_repo_brief(repo_path: str) -> dict:
    """Generate a complete repo intelligence brief."""
    metadata = collect_repo_metadata(repo_path)

    manifest_summaries = {}
    for name, content in metadata.get("manifests", {}).items():
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


def generate_full_onboarding(repo_path: str) -> dict:
    """
    Generate the complete enhanced onboarding package.
    This is the "holy shit" feature — everything a dev needs to understand a new codebase.
    """
    brief = generate_repo_brief(repo_path)
    api_routes = detect_api_routes(repo_path)
    complexity = analyze_complexity(repo_path)
    env_vars = detect_env_vars(repo_path)

    return {
        "brief": brief,
        "api_routes": api_routes[:30],
        "api_route_count": len(api_routes),
        "complexity": complexity,
        "env_vars": env_vars,
        "env_var_count": len(env_vars),
    }
