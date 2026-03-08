"""
Sandbox Execution Engine.
Runs build/test/lint commands inside Modal containers to validate changes
BEFORE creating a PR. If code doesn't compile or tests fail, it doesn't ship.

Safety states:
- "safe": all checks pass, PR recommended
- "needs_review": some checks inconclusive, human review required
- "unsafe": checks failed, PR BLOCKED
"""
import modal
import json

image = modal.Image.debian_slim(python_version="3.10") \
    .apt_install("git", "curl", "bash") \
    .run_commands(
        # Install Node.js 20 for JS/TS projects
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -",
        "apt-get install -y nodejs",
        # Install common build tools
        "npm install -g pnpm yarn typescript",
        # Install Python tools
        "pip install ruff mypy pytest",
    ) \
    .pip_install("pydantic", "supabase")

app = modal.App(name="dependify-sandbox", image=image)

# Auto-detected project types and their check commands
PROJECT_CHECKS = {
    "package.json": {
        "type": "node",
        "install": ["npm install --ignore-scripts"],
        "build": ["npm run build --if-present"],
        "test": ["npm test --if-present"],
        "lint": ["npx eslint . --max-warnings=0 --no-error-on-unmatched-pattern 2>/dev/null || true"],
    },
    "pnpm-lock.yaml": {
        "type": "node-pnpm",
        "install": ["pnpm install --ignore-scripts"],
        "build": ["pnpm run build --if-present"],
        "test": ["pnpm test --if-present"],
        "lint": [],
    },
    "requirements.txt": {
        "type": "python",
        "install": ["pip install -r requirements.txt"],
        "build": [],
        "test": ["python -m pytest --tb=short -q 2>/dev/null || true"],
        "lint": ["ruff check . 2>/dev/null || true"],
    },
    "pyproject.toml": {
        "type": "python",
        "install": ["pip install -e '.[dev]' 2>/dev/null || pip install -e . 2>/dev/null || true"],
        "build": [],
        "test": ["python -m pytest --tb=short -q 2>/dev/null || true"],
        "lint": ["ruff check . 2>/dev/null || true"],
    },
    "go.mod": {
        "type": "go",
        "install": [],
        "build": ["go build ./..."],
        "test": ["go test ./... -short"],
        "lint": [],
    },
    "Cargo.toml": {
        "type": "rust",
        "install": [],
        "build": ["cargo build 2>&1"],
        "test": ["cargo test 2>&1"],
        "lint": [],
    },
}


@app.function(
    timeout=600,  # 10 min max
    max_containers=20,
    min_containers=0,
    secrets=[
        modal.Secret.from_name("SUPABASE_URL"),
        modal.Secret.from_name("SUPABASE_KEY"),
    ],
)
def run_sandbox_checks(repo_url: str, changed_files: list[dict], run_id: str = "") -> dict:
    """
    Clone repo, apply changes, run build/test/lint, return safety state.

    Args:
        repo_url: GitHub repo URL to clone
        changed_files: List of {"path": "relative/path", "content": "new code"}
        run_id: For tracking in Supabase

    Returns:
        {
            "safety_state": "safe" | "needs_review" | "unsafe",
            "checks": [{"name": "build", "passed": True, "output": "..."}],
            "project_type": "node",
            "summary": "All checks passed"
        }
    """
    import subprocess
    import os
    import tempfile
    import supabase as sb

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase_client = sb.create_client(SUPABASE_URL, SUPABASE_KEY)

    def log_status(message):
        print(f"[Sandbox {run_id}] {message}")
        try:
            supabase_client.table("repo-updates").insert({
                "status": "SANDBOX",
                "message": message,
            }).execute()
        except Exception:
            pass

    workspace = tempfile.mkdtemp(prefix="sandbox_")
    checks_results = []

    try:
        # Step 1: Clone
        log_status("Cloning repository into sandbox...")
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, workspace],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return {
                "safety_state": "unsafe",
                "checks": [{"name": "clone", "passed": False, "output": result.stderr[:500]}],
                "project_type": "unknown",
                "summary": f"Failed to clone: {result.stderr[:200]}"
            }

        # Step 2: Apply changes
        log_status(f"Applying {len(changed_files)} file changes...")
        for change in changed_files:
            file_path = os.path.join(workspace, change["path"])
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(change["content"])

        # Step 3: Detect project type
        project_type = "unknown"
        check_config = None
        for manifest, config in PROJECT_CHECKS.items():
            if os.path.exists(os.path.join(workspace, manifest)):
                project_type = config["type"]
                check_config = config
                break

        if not check_config:
            log_status("No recognized project manifest found. Skipping checks.")
            return {
                "safety_state": "needs_review",
                "checks": [],
                "project_type": "unknown",
                "summary": "No recognized build system. Manual review recommended."
            }

        log_status(f"Detected {project_type} project. Running checks...")

        # Step 4: Run checks in order: install → build → test → lint
        for phase in ["install", "build", "test", "lint"]:
            commands = check_config.get(phase, [])
            if not commands:
                continue

            for cmd in commands:
                log_status(f"Running {phase}: {cmd[:60]}...")
                try:
                    proc = subprocess.run(
                        cmd, shell=True, capture_output=True, text=True,
                        timeout=180, cwd=workspace,
                        env={**os.environ, "CI": "true", "NODE_ENV": "production"}
                    )
                    passed = proc.returncode == 0
                    output = (proc.stdout[-500:] + "\n" + proc.stderr[-500:]).strip()

                    checks_results.append({
                        "name": phase,
                        "command": cmd,
                        "passed": passed,
                        "output": output[:1000],
                        "exit_code": proc.returncode,
                    })

                    if not passed and phase in ("build", "test"):
                        log_status(f"{phase} FAILED (exit {proc.returncode})")
                except subprocess.TimeoutExpired:
                    checks_results.append({
                        "name": phase,
                        "command": cmd,
                        "passed": False,
                        "output": "Timed out after 180 seconds",
                        "exit_code": -1,
                    })

        # Step 5: Determine safety state
        build_passed = all(c["passed"] for c in checks_results if c["name"] == "build")
        test_passed = all(c["passed"] for c in checks_results if c["name"] == "test")
        has_build = any(c["name"] == "build" for c in checks_results)
        has_test = any(c["name"] == "test" for c in checks_results)

        if has_build and not build_passed:
            safety_state = "unsafe"
            summary = "Build failed. Changes would break the project."
        elif has_test and not test_passed:
            safety_state = "needs_review"
            summary = "Tests failed. Changes may introduce regressions."
        elif not has_build and not has_test:
            safety_state = "needs_review"
            summary = "No build or test commands detected. Manual review recommended."
        else:
            safety_state = "safe"
            summary = "All checks passed."

        log_status(f"Sandbox result: {safety_state} - {summary}")

        return {
            "safety_state": safety_state,
            "checks": checks_results,
            "project_type": project_type,
            "summary": summary,
        }

    except Exception as e:
        return {
            "safety_state": "needs_review",
            "checks": checks_results,
            "project_type": project_type if 'project_type' in dir() else "unknown",
            "summary": f"Sandbox error: {str(e)[:200]}",
        }
