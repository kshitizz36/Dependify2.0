# server.py
from fastapi import FastAPI, HTTPException, Depends, Request
from typing import Optional, Dict, List
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from docker.errors import DockerException, ContainerError
import os
import subprocess
import asyncio
import json
import shutil
import httpx
import supabase as supabase_lib
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration and authentication
from config import Config
from auth import AuthService, get_current_user, get_optional_user

# Import updated app objects from modules
from containers import app as container_app, run_script
from modal_write import app as write_app, process_file
from modal_verify import app as verify_app, verify_and_fix
from git_driver import load_repository, create_and_push_branch, create_pull_request, create_fork
from checker import compute_repo_score, Finding, get_all_files_recursively
from repo_intel import generate_repo_brief, generate_full_onboarding
from blast_radius import build_import_graph, get_blast_radius, compute_blast_radius_for_changes
from dep_analyzer import run_full_dep_analysis
from sandbox import app as sandbox_app, run_sandbox_checks
from scan_feedback import build_learning_context, save_scan_feedback, check_pr_status, get_repo_preferences
from threat_model import generate_threat_model
from commit_analyzer import analyze_commit_history
import uuid
import tempfile

# Initialize FastAPI app with metadata
app = FastAPI(
    title="Dependify API",
    description="AI-powered code modernization and technical debt reduction",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Initialize Supabase client for repo management
supabase_client = supabase_lib.create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Add CORS middleware with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Define request models
class UpdateRequest(BaseModel):
    repository: str = Field(..., description="GitHub repository URL")
    repository_owner: str = Field(..., description="Repository owner username")
    repository_name: str = Field(..., description="Repository name")

    @validator('repository')
    def validate_repository_url(cls, v):
        """Validate that repository URL is a valid GitHub URL."""
        if not v.startswith(('https://github.com/', 'git@github.com:')):
            raise ValueError('Repository must be a valid GitHub URL')
        return v


class GitHubOAuthRequest(BaseModel):
    code: str = Field(..., description="GitHub OAuth authorization code")


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict


class LinkReposRequest(BaseModel):
    repos: List[Dict] = Field(..., description="List of repos to link, each with repo_url, repo_name, repo_owner, language")


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """Health check endpoint to verify server is running."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "message": "Dependify API is running"
    }


# GitHub OAuth endpoints
@app.post("/auth/github", response_model=AuthResponse, tags=["Authentication"])
@limiter.limit("10/minute")
async def github_oauth(request: Request, oauth_request: GitHubOAuthRequest):
    """
    Exchange GitHub OAuth code for access token.

    This endpoint is called after user authorizes your app on GitHub.
    request must be a starlette.requests.Request instance for slowapi.
    """
    try:
        github_data = await AuthService.exchange_github_code(oauth_request.code)

        # Create JWT token for our API
        user_data = github_data["user"]
        access_token = AuthService.create_access_token(
            data={
                "user_id": user_data["id"],
                "username": user_data["login"],
                "github_token": github_data["github_token"]
            }
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_data
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


@app.get("/auth/me", tags=["Authentication"])
async def get_current_user_info(current_user: Dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    return {"user": current_user}


@app.get("/github/repos", tags=["Repository"])
@limiter.limit("30/minute")
async def get_github_repos(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Fetch the authenticated user's GitHub repositories.
    Used by the dashboard repo picker modal.
    """
    github_token = current_user.get("github_token")
    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token not found. Please re-authenticate.")

    try:
        repos = []
        page = 1
        async with httpx.AsyncClient() as client:
            while True:
                resp = await client.get(
                    f"https://api.github.com/user/repos?per_page=100&page={page}&sort=updated",
                    headers={
                        "Authorization": f"Bearer {github_token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    timeout=15.0,
                )
                if resp.status_code != 200:
                    raise HTTPException(status_code=resp.status_code, detail="Failed to fetch GitHub repos")

                batch = resp.json()
                if not batch:
                    break

                for r in batch:
                    repos.append({
                        "id": r["id"],
                        "name": r["name"],
                        "full_name": r["full_name"],
                        "owner": r["owner"]["login"],
                        "html_url": r["html_url"],
                        "clone_url": r["clone_url"],
                        "language": r.get("language"),
                        "updated_at": r["updated_at"],
                        "stargazers_count": r.get("stargazers_count", 0),
                        "private": r["private"],
                    })
                page += 1
                if len(batch) < 100:
                    break

        return {"repos": repos, "total": len(repos)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch repos: {str(e)}")


@app.post("/repos/link", tags=["Repository"])
@limiter.limit("20/minute")
async def link_repos(request: Request, payload: LinkReposRequest,
                     current_user: Dict = Depends(get_current_user)):
    """
    Link selected GitHub repos to the user's Dependify dashboard.
    Stores in Supabase user-repos table.
    """
    user_id = str(current_user.get("user_id", ""))
    username = current_user.get("username", "")

    linked = []
    for repo in payload.repos:
        row = {
            "user_id": user_id,
            "username": username,
            "repo_url": repo.get("repo_url", ""),
            "repo_name": repo.get("repo_name", ""),
            "repo_owner": repo.get("repo_owner", ""),
            "language": repo.get("language"),
        }
        try:
            supabase_client.table("user-repos").upsert(
                row, on_conflict="user_id,repo_url"
            ).execute()
            linked.append(row["repo_name"])
        except Exception as e:
            print(f"Error linking repo {row['repo_name']}: {e}")

    return {"status": "success", "linked": linked, "count": len(linked)}


@app.get("/repos", tags=["Repository"])
@limiter.limit("30/minute")
async def get_linked_repos(request: Request, current_user: Dict = Depends(get_current_user)):
    """
    Get the user's linked repos from Supabase.
    Includes last scan score if available.
    """
    user_id = str(current_user.get("user_id", ""))

    try:
        result = supabase_client.table("user-repos") \
            .select("*") \
            .eq("user_id", user_id) \
            .order("linked_at", desc=True) \
            .execute()

        repos = result.data or []

        # Fetch latest debt scores for each repo
        # Scan saves with HTML URL, linked repos store clone URL — try both
        for repo in repos:
            try:
                repo_url = repo["repo_url"]
                # Also try HTML URL (without .git)
                html_url = repo_url.replace(".git", "")
                score_result = supabase_client.table("repo-debt-summaries") \
                    .select("overall_debt_score,score_grade,created_at") \
                    .in_("repository_url", [repo_url, html_url]) \
                    .order("created_at", desc=True) \
                    .limit(1) \
                    .execute()
                if score_result.data:
                    repo["last_score"] = score_result.data[0]
                else:
                    repo["last_score"] = None
            except Exception:
                repo["last_score"] = None

        return {"repos": repos, "total": len(repos)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch linked repos: {str(e)}")


@app.delete("/repos/{repo_name}", tags=["Repository"])
@limiter.limit("20/minute")
async def unlink_repo(request: Request, repo_name: str,
                      current_user: Dict = Depends(get_current_user)):
    """
    Unlink a repo from the user's Dependify dashboard.
    """
    user_id = str(current_user.get("user_id", ""))

    try:
        supabase_client.table("user-repos") \
            .delete() \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .execute()
        return {"status": "success", "message": f"Unlinked {repo_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to unlink repo: {str(e)}")


@app.post('/update', tags=["Repository"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_HOUR}/hour")
async def update(request: Request, payload: UpdateRequest,
                 current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Process a repository to modernize code and create a pull request.

    This endpoint:
    1. Analyzes repository files for outdated syntax (Reader Agent - Sonnet)
    2. Uses LLM to refactor code (Writer Agent - Haiku)
    3. Verifies and fixes changes (Verifier Agent - Sonnet)
    4. Creates a new branch with changes
    5. Submits a pull request

    Requires authentication for private repositories.
    """
    staging_dir = None

    try:
        print(f"Processing repository: {payload.repository}")

        # Extract user's GitHub token for authenticated operations
        github_token = None
        if current_user:
            github_token = current_user.get("github_token")

        # Create staging area
        staging_dir = os.path.join(os.getcwd(), "staging")

        # Clean up existing staging directory
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        os.makedirs(staging_dir)

        # Run container-based script execution to analyze files
        print("Step 1: Analyzing files with Reader Agent (Sonnet)...")
        with container_app.run():
            job_list = run_script.remote(payload.repository)

        if not job_list:
            return {
                "status": "success",
                "message": "No issues found in repository",
                "repository": payload.repository,
                "score": {"overall_debt_score": 0, "score_grade": "A"},
                "files_analyzed": 0,
                "files_updated": 0
            }

        print(f"Found {len(job_list)} files to update")

        # Compute and save score from scan findings
        update_run_id = uuid.uuid4().hex[:12]
        all_scan_findings = []
        for job in job_list:
            for rf in job.get("findings", []):
                if isinstance(rf, dict):
                    try:
                        all_scan_findings.append(Finding(**rf))
                    except Exception:
                        continue

        scan_score = compute_repo_score(all_scan_findings, len(job_list))
        try:
            supabase_client.table("repo-debt-summaries").insert({
                "repository_url": payload.repository,
                "run_id": update_run_id,
                **scan_score,
                "files_analyzed": len(job_list),
                "files_updated": 0,  # Updated later after PR
            }).execute()
        except Exception as e:
            print(f"Error saving scan score: {e}")

        # Step 1.5: Compute blast radius for changed files
        # Clone repo temporarily to build import graph
        print("Step 1.5: Computing blast radius...")
        blast_data = {}
        try:
            blast_dir = tempfile.mkdtemp(prefix="blast_")
            subprocess.run(
                ["git", "clone", "--depth", "1", payload.repository, blast_dir],
                check=True, capture_output=True, text=True, timeout=60
            )
            all_repo_files = get_all_files_recursively(blast_dir)
            graph = build_import_graph(blast_dir, all_repo_files)

            # Inject blast radius into each job for the Writer agent
            for job in job_list:
                file_path = job.get("path", "")
                rel_path = file_path
                if "/repository/" in file_path:
                    rel_path = file_path.split("/repository/", 1)[1]
                radius = get_blast_radius(graph, rel_path)
                job["blast_radius"] = radius
                blast_data[rel_path] = radius
                if radius["dependent_count"] > 0:
                    print(f"  {rel_path}: {radius['dependent_count']} dependents ({radius['risk_level']})")

            shutil.rmtree(blast_dir, ignore_errors=True)
        except Exception as e:
            print(f"Blast radius computation failed (non-fatal): {e}")

        # Step 2: Refactor files with Writer Agent (Haiku - parallel)
        print("Step 2: Refactoring files with Writer Agent (Haiku)...")
        write_outputs = []
        with write_app.run():
            print(f"⚡ Processing {len(job_list)} files in parallel...")

            i = 0
            async for output in process_file.map.aio(job_list):
                i += 1
                if output and output.get("refactored_code"):
                    write_outputs.append(output)
                    print(f"✍️ Written {i}/{len(job_list)}: {output.get('file_path', 'unknown')}")
                else:
                    print(f"⚠️ Skipped {i}/{len(job_list)}: No output")

        if not write_outputs:
            raise HTTPException(
                status_code=400,
                detail="Failed to refactor any files. Please check if the repository contains valid code files."
            )

        # Step 3: Verify and fix with Verifier Agent (Sonnet - parallel)
        print("Step 3: Verifying changes with Verifier Agent (Sonnet)...")
        verify_jobs = []
        for output in write_outputs:
            original = next(
                (j for j in job_list if j.get("path") == output.get("file_path")),
                None
            )
            verify_jobs.append({
                "file_path": output["file_path"],
                "original_code": original.get("code_content", "") if original else "",
                "refactored_code": output["refactored_code"],
                "comments": output.get("refactored_code_comments", "")
            })

        refactored_jobs = []
        with verify_app.run():
            print(f"🔍 Verifying {len(verify_jobs)} files in parallel...")
            i = 0
            async for result in verify_and_fix.map.aio(verify_jobs):
                i += 1
                if result and result.get("refactored_code"):
                    file_path = result.get("file_path", "")
                    # Extract relative path from container's absolute path
                    # Container clones repo to .../repository/{relative_path}
                    if "/repository/" in file_path:
                        relative_path = file_path.split("/repository/", 1)[1]
                    else:
                        relative_path = os.path.basename(file_path)
                    new_path = os.path.join(staging_dir, relative_path)
                    # Find original code for this file
                    original_job = next(
                        (j for j in job_list if j.get("path") == file_path),
                        None
                    )
                    refactored_jobs.append({
                        "path": new_path,
                        "new_content": result["refactored_code"],
                        "old_content": original_job.get("code_content", "") if original_job else "",
                        "comments": result.get("refactored_code_comments", "")
                    })
                    status = "✅" if result.get("verified") else "⚠️"
                    print(f"{status} Verified {i}/{len(verify_jobs)}: {file_path} (attempts: {result.get('attempts', 1)})")
                else:
                    print(f"❌ Failed {i}/{len(verify_jobs)}")

        if not refactored_jobs:
            raise HTTPException(
                status_code=400,
                detail="Failed to verify any files. Please check if the repository contains valid code files."
            )

        # Step 3.5: Sandbox check — run build/test with changes applied
        print("Step 3.5: Running sandbox checks...")
        sandbox_result = None
        safety_state = "needs_review"  # Default if sandbox fails
        try:
            sandbox_changes = []
            for job in refactored_jobs:
                rel_path = job["path"]
                if staging_dir in rel_path:
                    rel_path = os.path.relpath(rel_path, staging_dir)
                sandbox_changes.append({"path": rel_path, "content": job["new_content"]})

            with sandbox_app.run():
                sandbox_result = run_sandbox_checks.remote(
                    payload.repository, sandbox_changes, update_run_id
                )

            safety_state = sandbox_result.get("safety_state", "needs_review")
            print(f"Sandbox result: {safety_state} - {sandbox_result.get('summary', '')}")

            # Block PR for unsafe runs
            if safety_state == "unsafe":
                return {
                    "status": "blocked",
                    "message": "PR blocked: sandbox checks failed. Changes would break the project.",
                    "repository": payload.repository,
                    "run_id": update_run_id,
                    "score": scan_score,
                    "safety_state": safety_state,
                    "sandbox": sandbox_result,
                    "files_analyzed": len(job_list),
                    "files_updated": 0,
                    "blast_radius": blast_data,
                }
        except Exception as e:
            print(f"Sandbox check failed (non-fatal): {e}")
            sandbox_result = {"safety_state": "needs_review", "summary": f"Sandbox error: {str(e)[:100]}"}

        # Create fork of the repository (or get original if user owns it)
        print("Step 4: Checking repository ownership and creating fork if needed...")
        fork_result = create_fork(payload.repository_owner, payload.repository_name, github_token=github_token)
        
        if not fork_result:
            raise HTTPException(
                status_code=400,
                detail="Failed to access repository. Make sure GITHUB_TOKEN is configured correctly."
            )
        
        is_own_repo = fork_result.get("is_own_repo", False)
        repo_url = fork_result.get("clone_url")
        repo_owner_username = fork_result.get("owner", {}).get("login")
        
        if is_own_repo:
            print(f"User owns the repository - working directly on: {repo_url}")
        else:
            print(f"Fork created/found: {repo_url}")

        # Clone the repository (fork or original)
        print("Step 5: Cloning repository...")
        clone_cmd = ["git", "clone", repo_url, staging_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {result.stderr}"
            )

        # Load repository info
        print("Step 6: Loading repository information...")
        repo, origin, origin_url = load_repository(staging_dir)
        files_changed = []

        # Apply refactored code to files
        print("Step 7: Applying changes...")
        for job in refactored_jobs:
            file_path = job.get("path")

            if os.path.exists(file_path):
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(job.get("new_content"))
                    files_changed.append(file_path)
                    print(f"Updated: {file_path}")
                except Exception as write_error:
                    print(f"Error writing file {file_path}: {write_error}")
            else:
                print(f"Warning: File {file_path} does not exist")

        if not files_changed:
            raise HTTPException(
                status_code=400,
                detail="No files were successfully updated"
            )

        # Create branch and push changes
        print("Step 8: Creating branch and pushing changes...")
        new_branch_name, username = create_and_push_branch(repo, origin, files_changed, github_token=github_token)

        # Create pull request (different logic for own repo vs fork)
        if is_own_repo:
            print("Step 9: Creating pull request in user's own repository...")
        else:
            print("Step 9: Creating pull request from fork to original repository...")
            
        pr_url = create_pull_request(
            new_branch_name,
            payload.repository_owner,  # Original repo owner
            payload.repository_name,   # Original repo name
            "main",                     # Base branch
            username,                   # User's username
            is_own_repo,               # Flag to indicate if it's user's own repo
            github_token=github_token  # User's authenticated token
        )

        # Build response with fork information
        response_data = {
            "status": "success",
            "message": "Repository updated and pull request created successfully",
            "repository": payload.repository,
            "run_id": update_run_id,
            "score": scan_score,
            "safety_state": safety_state,
            "sandbox": sandbox_result,
            "blast_radius": blast_data,
            "files_analyzed": len(job_list),
            "files_updated": len(files_changed),
            "branch": new_branch_name,
            "pull_request_url": pr_url,
            "is_own_repo": is_own_repo,
            "output": refactored_jobs[:5]  # Return first 5 for preview
        }
        
        # Add fork information if it was forked
        if not is_own_repo:
            response_data["fork_info"] = {
                "message": "A temporary staging fork was created to propose these changes",
                "fork_owner": username,
                "fork_name": payload.repository_name,
                "can_delete": True,
                "delete_note": "You can safely delete this fork after the PR is merged or closed"
            }
        
        return response_data

    except HTTPException:
        raise
    except ContainerError as ce:
        err_output = ce.stderr.decode("utf-8") if ce.stderr else str(ce)
        raise HTTPException(status_code=500, detail=f"Container execution error: {err_output}")
    except DockerException as de:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(de)}")
    except subprocess.CalledProcessError as pe:
        raise HTTPException(status_code=500, detail=f"Git operation failed: {str(pe)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
    finally:
        # Cleanup staging directory
        if staging_dir and os.path.exists(staging_dir):
            try:
                shutil.rmtree(staging_dir)
                print("Cleaned up staging directory")
            except Exception as cleanup_error:
                print(f"Warning: Could not clean up staging directory: {cleanup_error}")


# ============================================================
# Sprint 1: Scan, Score, Brief, History endpoints
# ============================================================

class ScanRequest(BaseModel):
    repository: str = Field(..., description="GitHub repository URL")
    repository_owner: str = Field(..., description="Repository owner username")
    repository_name: str = Field(..., description="Repository name")
    generate_brief: bool = Field(default=True, description="Also generate repo intelligence brief")

    @validator('repository')
    def validate_repository_url(cls, v):
        if not v.startswith(('https://github.com/', 'git@github.com:')):
            raise ValueError('Repository must be a valid GitHub URL')
        return v


@app.post('/scan', tags=["Scan"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_HOUR}/hour")
async def scan_repo(request: Request, payload: ScanRequest,
                    current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Score-only scan: analyze repo for security, debt, outdated code.
    Returns findings + score WITHOUT creating a PR.
    Optionally generates a repo intelligence brief.
    """
    scan_dir = None
    run_id = uuid.uuid4().hex[:12]

    try:
        print(f"[Scan {run_id}] Scanning repository: {payload.repository}")

        # Check learning history for this repo
        learning_context = build_learning_context(payload.repository)
        if learning_context:
            print(f"[Scan {run_id}] Learning context: {learning_context[:100]}...")

        # Step 1: Run Reader Agent via Modal
        print(f"[Scan {run_id}] Step 1: Analyzing files with Reader Agent...")
        with container_app.run():
            job_list = run_script.remote(payload.repository)

        # Collect all findings from the scan
        all_findings = []
        file_scores = []
        files_with_issues = 0

        for job in (job_list or []):
            raw_findings = job.get("findings", [])
            file_path = job.get("path", "")
            risk_score = job.get("risk_score", 0)

            # Parse findings
            findings = []
            severity_breakdown = {}
            category_breakdown = {}
            for rf in raw_findings:
                if isinstance(rf, dict):
                    sev = rf.get("severity", "low")
                    cat = rf.get("category", "maintainability")
                    severity_breakdown[sev] = severity_breakdown.get(sev, 0) + 1
                    category_breakdown[cat] = category_breakdown.get(cat, 0) + 1
                    findings.append(rf)
                    all_findings.append(rf)

            if findings:
                files_with_issues += 1

            # Extract relative path for storage
            rel_path = file_path
            if "/repository/" in file_path:
                rel_path = file_path.split("/repository/", 1)[1]

            file_scores.append({
                "run_id": run_id,
                "repo_url": payload.repository,
                "file_path": rel_path,
                "risk_score": risk_score,
                "findings_count": len(findings),
                "severity_breakdown": severity_breakdown,
                "category_breakdown": category_breakdown,
            })

        # Compute repo-level score (deterministic, no LLM)
        total_files = len(job_list) if job_list else 0
        # Convert raw finding dicts to Finding objects for scoring
        finding_objects = []
        for f in all_findings:
            try:
                finding_objects.append(Finding(**f))
            except Exception:
                continue

        score_data = compute_repo_score(finding_objects, total_files)

        # Write score to repo-debt-summaries table
        summary_row = {
            "repository_url": payload.repository,
            "run_id": run_id,
            "overall_debt_score": score_data["overall_debt_score"],
            "score_grade": score_data["score_grade"],
            "critical_count": score_data["critical_count"],
            "high_count": score_data["high_count"],
            "medium_count": score_data["medium_count"],
            "low_count": score_data["low_count"],
            "files_analyzed": total_files,
            "files_updated": files_with_issues,
        }
        try:
            supabase_client.table("repo-debt-summaries").insert(summary_row).execute()
            print(f"[Scan {run_id}] Score saved: {score_data['score_grade']} ({score_data['overall_debt_score']})")
        except Exception as e:
            print(f"[Scan {run_id}] Error saving score: {e}")

        # Write file-level scores for heatmap
        for fs in file_scores:
            try:
                supabase_client.table("file-scores").insert({
                    **fs,
                    "severity_breakdown": json.dumps(fs["severity_breakdown"]),
                    "category_breakdown": json.dumps(fs["category_breakdown"]),
                }).execute()
            except Exception as e:
                print(f"[Scan {run_id}] Error saving file score: {e}")

        # Step 2: Generate repo brief (optional)
        brief = None
        if payload.generate_brief:
            try:
                # Clone repo locally for brief generation
                import tempfile
                scan_dir = tempfile.mkdtemp(prefix="dependify_scan_")
                subprocess.run(
                    ["git", "clone", "--depth", "1", payload.repository, scan_dir],
                    check=True, capture_output=True, text=True
                )
                brief = generate_repo_brief(scan_dir)

                # Save brief to Supabase
                user_id = str(current_user.get("user_id", "")) if current_user else ""
                try:
                    supabase_client.table("repo-briefs").insert({
                        "repo_url": payload.repository,
                        "user_id": user_id,
                        "brief_json": json.dumps(brief),
                    }).execute()
                except Exception as e:
                    print(f"[Scan {run_id}] Error saving brief: {e}")

            except Exception as e:
                print(f"[Scan {run_id}] Brief generation failed: {e}")
                brief = {"error": str(e)}

        # Step 3: Blast radius + dependency analysis (uses the cloned repo if available)
        blast_radius_summary = {}
        dep_analysis = {}
        if scan_dir and os.path.exists(scan_dir):
            try:
                all_scan_files = get_all_files_recursively(scan_dir)
                changed_rel_paths = [fs["file_path"] for fs in file_scores if fs["findings_count"] > 0]
                blast_radius_summary = compute_blast_radius_for_changes(scan_dir, changed_rel_paths, all_scan_files)
            except Exception as e:
                print(f"[Scan {run_id}] Blast radius failed: {e}")

            try:
                all_scan_files_for_deps = get_all_files_recursively(scan_dir)
                dep_analysis = run_full_dep_analysis(scan_dir, all_scan_files_for_deps)
            except Exception as e:
                print(f"[Scan {run_id}] Dep analysis failed: {e}")

        return {
            "status": "success",
            "run_id": run_id,
            "repository": payload.repository,
            "score": score_data,
            "files_analyzed": total_files,
            "files_with_issues": files_with_issues,
            "total_findings": len(all_findings),
            "findings_by_severity": {
                "critical": score_data["critical_count"],
                "high": score_data["high_count"],
                "medium": score_data["medium_count"],
                "low": score_data["low_count"],
            },
            "file_scores": [
                {"file": fs["file_path"], "score": fs["risk_score"], "issues": fs["findings_count"]}
                for fs in file_scores if fs["findings_count"] > 0
            ],
            "all_findings": all_findings[:50],  # Detailed findings with evidence (capped at 50)
            "blast_radius": blast_radius_summary,
            "dep_analysis": dep_analysis,
            "brief": brief,
            "learning_context": learning_context if learning_context else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"[Scan {run_id}] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")
    finally:
        if scan_dir and os.path.exists(scan_dir):
            try:
                shutil.rmtree(scan_dir)
            except Exception:
                pass


@app.get("/repos/{repo_name}/brief", tags=["Intelligence"])
@limiter.limit("30/minute")
async def get_repo_brief(request: Request, repo_name: str,
                         current_user: Dict = Depends(get_current_user)):
    """Get the latest repo intelligence brief."""
    user_id = str(current_user.get("user_id", ""))

    try:
        # Find the repo URL from user-repos
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]

        # Fetch latest brief
        brief_result = supabase_client.table("repo-briefs") \
            .select("*") \
            .eq("repo_url", repo_url) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not brief_result.data:
            return {"brief": None, "message": "No brief available. Run a scan first."}

        row = brief_result.data[0]
        brief_json = row.get("brief_json", "{}")
        if isinstance(brief_json, str):
            brief_json = json.loads(brief_json)

        return {
            "brief": brief_json,
            "created_at": row.get("created_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch brief: {str(e)}")


@app.get("/repos/{repo_name}/history", tags=["Scan"])
@limiter.limit("30/minute")
async def get_score_history(request: Request, repo_name: str,
                            current_user: Dict = Depends(get_current_user)):
    """Get score history for a repo (for trend charts)."""
    user_id = str(current_user.get("user_id", ""))

    try:
        # Find the repo URL
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]

        # Fetch score history (last 20 scans)
        history_result = supabase_client.table("repo-debt-summaries") \
            .select("run_id,overall_debt_score,score_grade,critical_count,high_count,medium_count,low_count,files_analyzed,files_updated,created_at") \
            .eq("repository_url", repo_url) \
            .order("created_at", desc=True) \
            .limit(20) \
            .execute()

        return {
            "repo_name": repo_name,
            "history": history_result.data or [],
            "total_scans": len(history_result.data or []),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


@app.get("/repos/{repo_name}/heatmap", tags=["Scan"])
@limiter.limit("30/minute")
async def get_file_heatmap(request: Request, repo_name: str,
                           current_user: Dict = Depends(get_current_user)):
    """Get file-level risk scores for heatmap visualization."""
    user_id = str(current_user.get("user_id", ""))

    try:
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]

        # Get latest run's file scores
        latest_run = supabase_client.table("repo-debt-summaries") \
            .select("run_id") \
            .eq("repository_url", repo_url) \
            .order("created_at", desc=True) \
            .limit(1) \
            .execute()

        if not latest_run.data:
            return {"files": [], "message": "No scan data. Run a scan first."}

        run_id = latest_run.data[0]["run_id"]

        file_results = supabase_client.table("file-scores") \
            .select("file_path,risk_score,findings_count,severity_breakdown,category_breakdown") \
            .eq("run_id", run_id) \
            .order("risk_score", desc=True) \
            .execute()

        return {
            "run_id": run_id,
            "files": file_results.data or [],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch heatmap: {str(e)}")


# ============================================================
# Sprint 5: Smart PR Splitting
# ============================================================

class SplitUpdateRequest(BaseModel):
    repository: str = Field(..., description="GitHub repository URL")
    repository_owner: str = Field(..., description="Repository owner username")
    repository_name: str = Field(..., description="Repository name")
    categories: List[str] = Field(default=[], description="Which categories to include. Empty = all")

    @validator('repository')
    def validate_repository_url(cls, v):
        if not v.startswith(('https://github.com/', 'git@github.com:')):
            raise ValueError('Repository must be a valid GitHub URL')
        return v


@app.post('/update/preview', tags=["Update"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_HOUR}/hour")
async def preview_update(request: Request, payload: UpdateRequest,
                         current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Preview what an update would change WITHOUT creating a PR.
    Returns the scan findings grouped by category for split decision.
    """
    try:
        print(f"Preview: Scanning {payload.repository}...")
        with container_app.run():
            job_list = run_script.remote(payload.repository)

        if not job_list:
            return {"status": "success", "message": "No issues found", "categories": {}}

        # Group findings by category
        categories: Dict[str, list] = {}
        for job in job_list:
            for f in job.get("findings", []):
                if isinstance(f, dict):
                    cat = f.get("category", "other")
                    if cat not in categories:
                        categories[cat] = []
                    categories[cat].append({
                        "file": job.get("path", "").split("/repository/")[-1] if "/repository/" in job.get("path", "") else job.get("path", ""),
                        "severity": f.get("severity", "low"),
                        "description": f.get("description", ""),
                    })

        # Build split recommendation
        total = sum(len(v) for v in categories.values())
        recommendation = "single"
        if total > 10 and len(categories) > 1:
            recommendation = "split"

        return {
            "status": "success",
            "repository": payload.repository,
            "total_findings": total,
            "files_to_change": len(job_list),
            "categories": {
                cat: {"count": len(findings), "files": list(set(f["file"] for f in findings)), "findings": findings[:5]}
                for cat, findings in categories.items()
            },
            "recommendation": recommendation,
            "suggested_prs": [
                {"category": cat, "files": len(set(f["file"] for f in findings)), "findings": len(findings)}
                for cat, findings in sorted(categories.items(), key=lambda x: -len(x[1]))
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")


# ============================================================
# Sprint 4: Threat Modeling
# ============================================================

@app.get("/repos/{repo_name}/threat-model", tags=["Intelligence"])
@limiter.limit("10/minute")
async def get_threat_model(request: Request, repo_name: str,
                           current_user: Dict = Depends(get_current_user)):
    """Generate a cross-file threat model for a repo."""
    user_id = str(current_user.get("user_id", ""))

    try:
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]
        html_url = repo_url.replace(".git", "")

        # Clone repo for analysis
        import tempfile as tf
        threat_dir = tf.mkdtemp(prefix="threat_")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", html_url, threat_dir],
                check=True, capture_output=True, text=True, timeout=60
            )
            model = generate_threat_model(threat_dir)
            return {"repo_name": repo_name, "threat_model": model}
        finally:
            shutil.rmtree(threat_dir, ignore_errors=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Threat model failed: {str(e)}")


# ============================================================
# Sprint 3: Evidence, Learning Loop, Run Details
# ============================================================

@app.get("/runs/{run_id}", tags=["Runs"])
@limiter.limit("30/minute")
async def get_run_details(request: Request, run_id: str,
                          current_user: Dict = Depends(get_current_user)):
    """Get full evidence and details for a specific scan/update run."""
    try:
        # Get score summary
        score = supabase_client.table("repo-debt-summaries") \
            .select("*") \
            .eq("run_id", run_id) \
            .limit(1) \
            .execute()

        # Get file-level scores
        files = supabase_client.table("file-scores") \
            .select("*") \
            .eq("run_id", run_id) \
            .order("risk_score", desc=True) \
            .execute()

        if not score.data:
            raise HTTPException(status_code=404, detail="Run not found")

        return {
            "run_id": run_id,
            "score": score.data[0] if score.data else None,
            "files": files.data or [],
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch run: {str(e)}")


@app.get("/repos/{repo_name}/feedback", tags=["Learning"])
@limiter.limit("30/minute")
async def get_repo_feedback(request: Request, repo_name: str,
                            current_user: Dict = Depends(get_current_user)):
    """Get learning loop preferences for a repo."""
    user_id = str(current_user.get("user_id", ""))

    try:
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]
        html_url = repo_url.replace(".git", "")

        prefs = get_repo_preferences(html_url)
        return {"repo_name": repo_name, "preferences": prefs}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch feedback: {str(e)}")


@app.post("/runs/{run_id}/feedback", tags=["Learning"])
@limiter.limit("20/minute")
async def submit_run_feedback(request: Request, run_id: str,
                              current_user: Dict = Depends(get_current_user)):
    """
    Check PR status and record feedback for learning loop.
    Called after user merges/rejects a Dependify PR.
    """
    github_token = current_user.get("github_token")
    if not github_token:
        raise HTTPException(status_code=401, detail="GitHub token required")

    try:
        # Get the run's score data to find the PR
        score = supabase_client.table("repo-debt-summaries") \
            .select("repository_url") \
            .eq("run_id", run_id) \
            .limit(1) \
            .execute()

        if not score.data:
            raise HTTPException(status_code=404, detail="Run not found")

        repo_url = score.data[0]["repository_url"]

        # Get file scores for this run
        files = supabase_client.table("file-scores") \
            .select("file_path,category_breakdown") \
            .eq("run_id", run_id) \
            .execute()

        # For now, record all files as the same action
        # TODO: In future, check individual file status from PR diff
        body = await request.json()
        action = body.get("action", "unknown")  # merged, rejected, ignored

        for f in (files.data or []):
            categories = f.get("category_breakdown", {})
            if isinstance(categories, str):
                categories = json.loads(categories)
            primary_cat = max(categories, key=categories.get) if categories else "unknown"

            save_scan_feedback(
                run_id=run_id,
                repo_url=repo_url,
                file_path=f["file_path"],
                change_category=primary_cat,
                user_action=action,
            )

        return {"status": "success", "files_recorded": len(files.data or [])}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save feedback: {str(e)}")


# ============================================================
# Sprint 8: Enhanced Onboarding
# ============================================================

@app.get("/repos/{repo_name}/onboard", tags=["Intelligence"])
@limiter.limit("5/minute")
async def get_full_onboarding(request: Request, repo_name: str,
                              current_user: Dict = Depends(get_current_user)):
    """
    Generate the complete enhanced onboarding package for a repo.
    Includes: brief, API routes, complexity analysis, env vars, setup hints.
    """
    user_id = str(current_user.get("user_id", ""))

    try:
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]
        html_url = repo_url.replace(".git", "")

        onboard_dir = tempfile.mkdtemp(prefix="onboard_")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", html_url, onboard_dir],
                check=True, capture_output=True, text=True, timeout=60
            )
            result = generate_full_onboarding(onboard_dir)

            # Save brief to Supabase
            try:
                supabase_client.table("repo-briefs").insert({
                    "repo_url": html_url,
                    "user_id": user_id,
                    "brief_json": json.dumps(result["brief"]),
                }).execute()
            except Exception:
                pass

            return {"repo_name": repo_name, "onboarding": result}
        finally:
            shutil.rmtree(onboard_dir, ignore_errors=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Onboarding failed: {str(e)}")


# ============================================================
# Sprint 6: Fleet Health + Commit Evolution
# ============================================================

@app.get("/fleet/health", tags=["Fleet"])
@limiter.limit("10/minute")
async def get_fleet_health(request: Request, current_user: Dict = Depends(get_current_user)):
    """Get org-wide health summary across all linked repos."""
    user_id = str(current_user.get("user_id", ""))

    try:
        # Get all linked repos
        repos_result = supabase_client.table("user-repos") \
            .select("repo_name,repo_owner,repo_url,language") \
            .eq("user_id", user_id) \
            .execute()

        repos = repos_result.data or []
        fleet = []
        grade_counts = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        total_score = 0
        scanned_count = 0

        for repo in repos:
            repo_url = repo["repo_url"]
            html_url = repo_url.replace(".git", "")

            # Get latest score
            score_result = supabase_client.table("repo-debt-summaries") \
                .select("overall_debt_score,score_grade,created_at") \
                .in_("repository_url", [repo_url, html_url]) \
                .order("created_at", desc=True) \
                .limit(1) \
                .execute()

            score = score_result.data[0] if score_result.data else None
            fleet.append({
                "repo_name": repo["repo_name"],
                "repo_owner": repo["repo_owner"],
                "language": repo.get("language"),
                "score": score,
            })

            if score:
                grade = score.get("score_grade", "A")
                grade_counts[grade] = grade_counts.get(grade, 0) + 1
                total_score += score.get("overall_debt_score", 0)
                scanned_count += 1

        avg_score = total_score / max(scanned_count, 1)
        if avg_score <= 10: org_grade = "A"
        elif avg_score <= 25: org_grade = "B"
        elif avg_score <= 50: org_grade = "C"
        elif avg_score <= 75: org_grade = "D"
        else: org_grade = "F"

        return {
            "total_repos": len(repos),
            "scanned_repos": scanned_count,
            "org_grade": org_grade,
            "avg_debt_score": round(avg_score, 1),
            "grade_distribution": grade_counts,
            "repos": sorted(fleet, key=lambda r: (r["score"] or {}).get("overall_debt_score", -1), reverse=True),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fleet health failed: {str(e)}")


@app.get("/repos/{repo_name}/evolution", tags=["Intelligence"])
@limiter.limit("10/minute")
async def get_repo_evolution(request: Request, repo_name: str,
                             current_user: Dict = Depends(get_current_user)):
    """Analyze commit history to detect codebase evolution patterns."""
    user_id = str(current_user.get("user_id", ""))

    try:
        repo_result = supabase_client.table("user-repos") \
            .select("repo_url") \
            .eq("user_id", user_id) \
            .eq("repo_name", repo_name) \
            .limit(1) \
            .execute()

        if not repo_result.data:
            raise HTTPException(status_code=404, detail="Repository not found")

        repo_url = repo_result.data[0]["repo_url"]
        html_url = repo_url.replace(".git", "")

        # Clone with depth 50 for history
        evo_dir = tempfile.mkdtemp(prefix="evolution_")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "50", html_url, evo_dir],
                check=True, capture_output=True, text=True, timeout=60
            )
            evolution = analyze_commit_history(evo_dir, depth=30)
            return {"repo_name": repo_name, "evolution": evolution}
        finally:
            shutil.rmtree(evo_dir, ignore_errors=True)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evolution analysis failed: {str(e)}")


@app.on_event("startup")
async def startup_event():
    """
    Run validation checks on startup.
    """
    print("=" * 60)
    print("Starting Dependify API v2.0.0")
    print("=" * 60)

    # Validate configuration
    is_valid, missing_vars = Config.validate()
    if not is_valid:
        print(f"⚠️  WARNING: Missing environment variables: {', '.join(missing_vars)}")
        print("Some features may not work correctly.")
    else:
        print("✅ Configuration validated successfully")

    print(f"CORS allowed origins: {Config.get_allowed_origins()}")
    print(f"Rate limit: {Config.RATE_LIMIT_PER_HOUR} requests/hour")
    print("=" * 60)


if __name__ == '__main__':
    import uvicorn

    # Use PORT environment variable from Config
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=Config.PORT,
        reload=False,
        log_level="info"
    )
