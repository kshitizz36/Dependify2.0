import os
from anthropic import Anthropic
from pydantic import BaseModel, ValidationError
from typing import List, Optional
import json
import supabase
from config import Config

# Model configuration
READER_MODEL = "claude-sonnet-4-20250514"

# Whitelist of code file extensions to scan
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx',
    '.java', '.go', '.rs', '.rb', '.php',
    '.c', '.cpp', '.cs', '.swift', '.kt',
    '.scala', '.vue', '.svelte', '.sh',
}

# Directories to always skip
SKIP_DIRS = {
    'node_modules', 'vendor', 'dist', 'build', '.next',
    '__pycache__', '.git', 'venv', '.venv', 'target',
    'coverage', '.cache', 'bower_components', '.tox',
    'eggs', '.eggs', '.mypy_cache', '.pytest_cache',
    '.gradle', '.idea', '.vscode', 'bin', 'obj',
}

# Max file lines to scan (skip very large files to save cost)
MAX_FILE_LINES = 500

# Initialize Anthropic client (Reader Agent - Sonnet)
client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)

# Initialize Supabase client
supabase_client = supabase.create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)


# --- Models ---

class Finding(BaseModel):
    """A single issue found in a file."""
    category: str       # security | maintainability | outdated_code | dependency
    severity: str       # critical | high | medium | low
    confidence: float   # 0.0 - 1.0
    description: str    # What the issue is
    evidence: List[str] # Chain of reasoning


class CodeChange(BaseModel):
    """Extended model: file analysis result from Reader agent."""
    path: str
    code_content: str
    reason: str
    add: bool
    # New fields for Sprint 1
    findings: List[Finding] = []
    risk_score: int = 0  # 0-100 per file, computed deterministically


# --- Deterministic Scoring (no LLM needed) ---

# Severity weights for score calculation
SEVERITY_WEIGHTS = {
    "critical": 25,
    "high": 15,
    "medium": 8,
    "low": 3,
}

# Category multipliers (security issues weigh more)
CATEGORY_MULTIPLIERS = {
    "security": 1.5,
    "dependency": 1.3,
    "outdated_code": 1.0,
    "maintainability": 0.8,
}


def compute_file_risk_score(findings: List[Finding]) -> int:
    """
    Compute a 0-100 risk score from findings. Pure math, no LLM.
    This same function can be used by a future CLI/OSS tool with static analysis findings.
    """
    if not findings:
        return 0

    raw_score = 0
    for f in findings:
        weight = SEVERITY_WEIGHTS.get(f.severity, 5)
        multiplier = CATEGORY_MULTIPLIERS.get(f.category, 1.0)
        raw_score += weight * multiplier * f.confidence

    # Cap at 100
    return min(int(raw_score), 100)


def compute_repo_score(all_findings: List[Finding], files_analyzed: int) -> dict:
    """
    Compute aggregate repo debt score from all findings across all files.
    Returns a dict matching the repo-debt-summaries table schema.
    """
    if not all_findings:
        return {
            "overall_debt_score": 0,
            "score_grade": "A",
            "critical_count": 0,
            "high_count": 0,
            "medium_count": 0,
            "low_count": 0,
        }

    # Count by severity
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.severity if isinstance(f, Finding) else f.get("severity", "low")
        if sev in counts:
            counts[sev] += 1

    # Weighted score: normalized by files analyzed
    raw = (
        counts["critical"] * 25 +
        counts["high"] * 15 +
        counts["medium"] * 8 +
        counts["low"] * 3
    )

    # Normalize: a repo with 50 files and 5 critical issues scores differently
    # than a repo with 5 files and 5 critical issues
    normalized = raw / max(files_analyzed, 1) * 10
    overall = min(int(normalized), 100)

    # Grade
    if overall <= 10:
        grade = "A"
    elif overall <= 25:
        grade = "B"
    elif overall <= 50:
        grade = "C"
    elif overall <= 75:
        grade = "D"
    else:
        grade = "F"

    return {
        "overall_debt_score": overall,
        "score_grade": grade,
        "critical_count": counts["critical"],
        "high_count": counts["high"],
        "medium_count": counts["medium"],
        "low_count": counts["low"],
    }


# --- File Collection ---

def get_all_files_recursively(root_directory):
    """
    Recursively collect code file paths, skipping non-code directories and files.
    Uses a whitelist approach (only scan known code extensions).
    """
    all_files = []
    for root, dirs, files in os.walk(root_directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

        for filename in files:
            _, ext = os.path.splitext(filename)
            if ext.lower() in CODE_EXTENSIONS:
                file_path = os.path.join(root, filename)
                all_files.append(file_path)
    return all_files


def collect_repo_metadata(root_directory):
    """
    Collect structural metadata about the repo for intelligence brief.
    No LLM needed — pure filesystem analysis.
    """
    metadata = {
        "file_count_by_ext": {},
        "total_files": 0,
        "total_lines": 0,
        "directories": [],
        "manifests": {},
        "test_files": [],
        "config_files": [],
        "has_dockerfile": False,
        "has_ci": False,
    }

    manifest_names = {
        "package.json", "requirements.txt", "Pipfile", "pyproject.toml",
        "go.mod", "Cargo.toml", "Gemfile", "pom.xml", "build.gradle",
        "composer.json", "pubspec.yaml",
    }

    config_names = {
        ".env", ".env.example", "docker-compose.yml", "Dockerfile",
        "tsconfig.json", "next.config.js", "next.config.ts",
        "vite.config.ts", "webpack.config.js", ".eslintrc.json",
    }

    ci_dirs = {".github", ".gitlab-ci.yml", ".circleci", "Jenkinsfile"}

    for root, dirs, files in os.walk(root_directory):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith('.')]

        rel_dir = os.path.relpath(root, root_directory)
        if rel_dir != ".":
            metadata["directories"].append(rel_dir)

        for filename in files:
            file_path = os.path.join(root, filename)
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            # Count by extension
            if ext in CODE_EXTENSIONS:
                metadata["file_count_by_ext"][ext] = metadata["file_count_by_ext"].get(ext, 0) + 1
                metadata["total_files"] += 1
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        metadata["total_lines"] += sum(1 for _ in f)
                except Exception:
                    pass

            # Detect test files
            lower = filename.lower()
            if "test" in lower or "spec" in lower or lower.startswith("test_"):
                metadata["test_files"].append(os.path.relpath(file_path, root_directory))

            # Manifests
            if filename in manifest_names:
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(8192)  # First 8KB
                    metadata["manifests"][filename] = content
                except Exception:
                    pass

            # Config files
            if filename in config_names:
                metadata["config_files"].append(filename)

            # Dockerfile
            if "dockerfile" in lower:
                metadata["has_dockerfile"] = True

        # CI detection
        for d in dirs:
            if d in ci_dirs:
                metadata["has_ci"] = True

    return metadata


# --- LLM Analysis ---

READER_SYSTEM_PROMPT = """You are Dependify's code analysis agent. You perform comprehensive code health analysis.

For each file, identify ALL issues across these categories:

1. **security**: SQL injection, XSS, hardcoded secrets/keys/passwords, insecure deserialization, command injection, path traversal, insecure crypto, missing input validation at boundaries
2. **outdated_code**: Deprecated APIs, old syntax patterns, removed/replaced library methods, legacy patterns that have modern equivalents
3. **maintainability**: God functions (>50 lines), no error handling, deeply nested logic, code duplication signals, magic numbers, missing type annotations in typed languages
4. **dependency**: Known vulnerable patterns (e.g. using eval(), exec(), dangerouslySetInnerHTML without sanitization), insecure dependency usage patterns

For each issue found, assign:
- **severity**: critical (exploitable security flaw, data exposure), high (significant risk or very outdated), medium (should fix), low (nice to fix)
- **confidence**: 0.0-1.0 how certain you are this is a real issue
- **evidence**: list of reasoning steps (e.g. "line 42 uses eval() with user input", "React.createClass deprecated in v15.5, project uses React 18")

Return ONLY valid JSON. If the file has no issues, set add=false."""


def analyze_file_with_llm(file_path):
    """
    Comprehensive file analysis: security, debt, outdated code, maintainability.
    Returns a CodeChange object with structured findings.
    """
    with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
        file_content = f.read()

    user_prompt = (
        f"Analyze this file for ALL code health issues (security, outdated patterns, maintainability, dependency risks).\n\n"
        f"File: {file_path}\n\n"
        f"```\n{file_content}\n```\n\n"
        "Return JSON:\n"
        "{\n"
        '  "path": "the file path",\n'
        '  "code_content": "the complete original file content",\n'
        '  "reason": "summary of all issues found",\n'
        '  "add": true/false (true if any issues found),\n'
        '  "findings": [\n'
        '    {\n'
        '      "category": "security|maintainability|outdated_code|dependency",\n'
        '      "severity": "critical|high|medium|low",\n'
        '      "confidence": 0.0-1.0,\n'
        '      "description": "what the issue is",\n'
        '      "evidence": ["reasoning step 1", "reasoning step 2"]\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    try:
        response = client.messages.create(
            model=READER_MODEL,
            max_tokens=4096,
            system=READER_SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        response_text = response.content[0].text.strip()
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()

        parsed = json.loads(response_text)

        # Parse findings
        raw_findings = parsed.get("findings", [])
        findings = []
        for rf in raw_findings:
            try:
                findings.append(Finding(**rf))
            except ValidationError:
                continue

        # Compute deterministic risk score
        risk_score = compute_file_risk_score(findings)

        change = CodeChange(
            path=parsed.get("path", file_path),
            code_content=parsed.get("code_content", file_content),
            reason=parsed.get("reason", ""),
            add=parsed.get("add", False),
            findings=findings,
            risk_score=risk_score,
        )

        # Write to Supabase for real-time UI
        filename = file_path.split("/")[-1]
        data = {
            "status": "READING",
            "message": f"Reading {filename} (score: {risk_score}, {len(findings)} issues)",
            "code": change.code_content
        }
        try:
            supabase_client.table("repo-updates").insert(data).execute()
        except Exception as db_error:
            print(f"Supabase error: {db_error}")

        return change

    except (ValidationError, json.JSONDecodeError) as parse_error:
        print(f"Error parsing LLM response for {file_path}: {parse_error}")
        return None
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return None


def fetch_updates(directory):
    """
    Scan all code files in the repo. Returns list of CodeChange objects
    with structured findings and risk scores.
    """
    analysis_results = []
    all_files = get_all_files_recursively(directory)
    print(f"Found {len(all_files)} code files to analyze")

    for filepath in all_files:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
            if line_count > MAX_FILE_LINES:
                print(f"Skipping {filepath} ({line_count} lines > {MAX_FILE_LINES} limit)")
                continue
        except Exception:
            continue

        response = analyze_file_with_llm(filepath)
        if response is None or response.add is False:
            continue
        response.path = filepath
        analysis_results.append(response)

    return analysis_results


if __name__ == "__main__":
    print(fetch_updates("website-test"))
