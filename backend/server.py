# server.py
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query, Request
from typing import Optional, Dict
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from docker.errors import DockerException, ContainerError
import os
import subprocess
import asyncio
import json
import shutil
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import configuration and authentication
from config import Config
from auth import AuthService, get_current_user, get_optional_user
from changelog_formatter import ChangelogFormatter, FileChange

# Import updated app objects from modules
from containers import app as container_app, run_script
from modal_write import app as write_app, process_file
from git_driver import load_repository, create_and_push_branch, create_pull_request, create_fork
from socket_manager import ConnectionManager

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

# Initialize WebSocket manager
manager = ConnectionManager()

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


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """Root endpoint returning API information."""
    return {
        "name": "Dependify API",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


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


@app.post('/update', tags=["Repository"])
@limiter.limit(f"{Config.RATE_LIMIT_PER_HOUR}/hour")
async def update(request: Request, payload: UpdateRequest,
                 current_user: Optional[Dict] = Depends(get_optional_user)):
    """
    Process a repository to modernize code and create a pull request.

    This endpoint:
    1. Analyzes repository files for outdated syntax
    2. Uses LLM to refactor code
    3. Creates a new branch with changes
    4. Submits a pull request

    Requires authentication for private repositories.
    """
    staging_dir = None

    try:
        print(f"Processing repository: {payload.repository}")

        # Create staging area
        staging_dir = os.path.join(os.getcwd(), "staging")

        # Clean up existing staging directory
        if os.path.exists(staging_dir):
            shutil.rmtree(staging_dir)
        os.makedirs(staging_dir)

        # Run container-based script execution to analyze files
        print("Step 1: Analyzing repository files...")
        try:
            with container_app.run():
                job_list = run_script.remote(payload.repository)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze repository: {str(e)}"
            )

        if not job_list or not isinstance(job_list, list):
            return {
                "status": "success",
                "message": "No outdated files found in repository",
                "repository": payload.repository,
                "files_analyzed": 0,
                "files_updated": 0
            }

        print(f"Found {len(job_list)} files to update")

        # Process files with LLM refactoring IN PARALLEL (async)
        print("Step 2: Refactoring files with AI (parallel processing)...")
        with write_app.run():
            # Use Modal's .map.aio() for async parallel processing
            print(f"Starting parallel processing of {len(job_list)} files...")
            
            refactored_jobs = []
            file_changes = []  # For changelog generation
            validation_results = []
            i = 0
            async for output in process_file.map.aio(job_list):
                i += 1
                if output and output.get("refactored_code"):
                    # make path safe - only attempt to map if output has file_path
                    file_path = output.get("file_path", "")
                    # preserve original behavior but guard slicing
                    new_path = (
                        f"{staging_dir}{file_path[24:]}" if file_path and len(file_path) > 24 else os.path.join(staging_dir, os.path.basename(file_path))
                    )
                    
                    # Collect changelog data
                    if output.get("changelog") and output.get("confidence_score") is not None:
                        file_change = FileChange(
                            file_path=file_path,
                            old_code=output.get("original_code", ""),
                            new_code=output.get("refactored_code", ""),
                            explanation=output.get("refactored_code_comments", ""),
                            confidence_score=output.get("confidence_score", 0),
                            language=output.get("validation", {}).get("language", "unknown"),
                            lines_added=output.get("changelog", {}).get("lines_added", 0),
                            lines_removed=output.get("changelog", {}).get("lines_removed", 0),
                            key_changes=output.get("changelog", {}).get("key_changes", [])
                        )
                        file_changes.append(file_change)
                    
                    # Collect validation results
                    if output.get("validation"):
                        validation_results.append({
                            "file": file_path,
                            "is_valid": output["validation"].get("is_valid", True),
                            "confidence": output.get("confidence_score", 0)
                        })
                    
                    refactored_jobs.append({
                        "path": new_path,
                        "new_content": output["refactored_code"],
                        "comments": output.get("refactored_code_comments", ""),
                        "confidence_score": output.get("confidence_score", 0),
                        "validation": output.get("validation", {}),
                        "changelog": output.get("changelog", {})
                    })
                    
                    # Enhanced logging with confidence emoji
                    conf_emoji = "🟢" if output.get("confidence_score", 0) >= 80 else "🟡" if output.get("confidence_score", 0) >= 60 else "🔴"
                    print(f"✅ Completed {i}/{len(job_list)}: {file_path} {conf_emoji}")
                else:
                    print(f"⚠️ Skipped {i}/{len(job_list)}: No output")

        # Validate refactored jobs
        if not refactored_jobs or not isinstance(refactored_jobs, list):
            raise HTTPException(
                status_code=400,
                detail="Failed to refactor any files. Please check if the repository contains valid code files."
            )
        
        # Filter out invalid entries
        refactored_jobs = [
            job for job in refactored_jobs 
            if job and isinstance(job, dict) and job.get("new_content")
        ]
        
        if not refactored_jobs:
            raise HTTPException(
                status_code=400,
                detail="No valid refactored files generated. Please check repository content."
            )

        # Create fork of the repository (or get original if user owns it)
        print("Step 3: Checking repository ownership and creating fork if needed...")
        fork_result = create_fork(payload.repository_owner, payload.repository_name)
        
        if not fork_result:
            raise HTTPException(
                status_code=400,
                detail="Failed to access repository. Make sure GITHUB_TOKEN is configured correctly."
            )
        
        is_own_repo = fork_result.get("is_own_repo", False)
        repo_url = fork_result.get("clone_url")
        repo_owner_username = fork_result.get("owner", {}).get("login")
        
        # Add GitHub token to URL for authentication
        if repo_url and repo_url.startswith("https://github.com/"):
            authenticated_url = repo_url.replace("https://github.com/", f"https://{Config.GITHUB_TOKEN}@github.com/")
        else:
            authenticated_url = repo_url
        
        if is_own_repo:
            print(f"User owns the repository - working directly on: {repo_url}")
        else:
            print(f"Fork created/found: {repo_url}")

        # Clone the repository (fork or original) with authentication
        print("Step 4: Cloning repository...")
        clone_cmd = ["git", "clone", authenticated_url, staging_dir]
        result = subprocess.run(clone_cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to clone repository: {result.stderr}"
            )

        # Load repository info
        print("Step 5: Loading repository information...")
        repo, origin, origin_url = load_repository(staging_dir)
        files_changed = []

        # Apply refactored code to files
        print("Step 6: Applying changes...")
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
        print("Step 7: Creating branch and pushing changes...")
        new_branch_name, username = create_and_push_branch(repo, origin, files_changed)

        # Create pull request (different logic for own repo vs fork)
        if is_own_repo:
            print("Step 8: Creating pull request in user's own repository...")
        else:
            print("Step 8: Creating pull request from fork to original repository...")
        
        # Generate comprehensive changelog for PR
        pr_description = None
        if file_changes:
            print(f"Generating AI-explained changelog for {len(file_changes)} files...")
            pr_description = ChangelogFormatter.generate_pr_description(file_changes)
            
            # Also generate full markdown changelog for reference
            full_changelog = ChangelogFormatter.generate_markdown_changelog(file_changes)
            print("Changelog generated successfully")
        
        pr_url = create_pull_request(
            new_branch_name,
            payload.repository_owner,  # Original repo owner
            payload.repository_name,   # Original repo name
            "main",                     # Base branch
            username,                   # User's username
            is_own_repo,               # Flag to indicate if it's user's own repo
            pr_description             # Enhanced changelog
        )

        # Build response with fork information
        # Calculate statistics
        total_confidence = sum(job.get("confidence_score", 0) for job in refactored_jobs) / len(refactored_jobs) if refactored_jobs else 0
        all_valid = all(job.get("validation", {}).get("is_valid", True) for job in refactored_jobs)
        high_confidence_count = sum(1 for job in refactored_jobs if job.get("confidence_score", 0) >= 80)
        
        response_data = {
            "status": "success",
            "message": "Repository updated and pull request created successfully",
            "repository": payload.repository,
            "files_analyzed": len(job_list),
            "files_updated": len(files_changed),
            "branch": new_branch_name,
            "pull_request_url": pr_url,
            "is_own_repo": is_own_repo,
            "quality_metrics": {
                "average_confidence_score": round(total_confidence, 1),
                "all_files_validated": all_valid,
                "high_confidence_files": high_confidence_count,
                "validation_results": validation_results[:10]  # First 10 for preview
            },
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


@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    client_id: Optional[str] = Query(None)
):
    """
    WebSocket endpoint for real-time updates during repository processing.

    Clients can connect to receive live progress updates.
    """
    await manager.connect(websocket, client_id or "default")
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        await manager.disconnect(client_id or "default")
        print(f"Client {client_id or 'default'} disconnected")
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        await manager.disconnect(client_id or "default")


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
