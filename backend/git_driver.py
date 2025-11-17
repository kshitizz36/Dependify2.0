from git import Repo
import uuid
import requests
import os
import supabase
from config import Config

# Initialize Supabase client
supabase_client = supabase.create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

def create_fork(repo_owner, repo_name):
    """
    Create a TEMPORARY STAGING fork of the repository for PR creation purposes.
    
    This fork is created solely to propose changes via pull request.
    Users can safely delete the fork after the PR is merged/closed.
    
    If the user already owns the repo, returns the original repo info (no fork needed).
    If fork already exists, returns the existing fork information.

    Args:
        repo_owner: Original repository owner
        repo_name: Repository name

    Returns:
        Dictionary with repository information (original or fork) and a flag indicating if it's the user's own repo
    """
    if not Config.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not configured")

    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Get authenticated user's username
    try:
        user_response = requests.get("https://api.github.com/user", headers=headers, timeout=30)
        if user_response.status_code == 200:
            username = user_response.json()["login"]
            
            # Check if user owns the repository
            if username.lower() == repo_owner.lower():
                print(f"User owns the repository - no fork needed")
                # Get original repo info
                repo_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
                repo_response = requests.get(repo_url, headers=headers, timeout=30)
                if repo_response.status_code == 200:
                    repo_data = repo_response.json()
                    repo_data['is_own_repo'] = True  # Flag to indicate it's user's own repo
                    return repo_data
            
            # Check if fork already exists
            fork_check_url = f"https://api.github.com/repos/{username}/{repo_name}"
            fork_response = requests.get(fork_check_url, headers=headers, timeout=30)
            
            if fork_response.status_code == 200:
                fork_data = fork_response.json()
                if fork_data.get("fork"):
                    print(f"Fork already exists: {fork_data['clone_url']}")
                    fork_data['is_own_repo'] = False
                    return fork_data
    except requests.RequestException as e:
        print(f"Error checking user/fork: {e}")
    
    # Create new fork
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/forks"

    try:
        response = requests.post(url, headers=headers, timeout=30)
        if response.status_code == 202:  # GitHub returns 202 for fork creation
            print("New fork created successfully")
            fork_data = response.json()
            fork_data['is_own_repo'] = False
            return fork_data
        elif response.status_code == 200:  # Fork already exists
            print("Fork already exists (200 response)")
            fork_data = response.json()
            fork_data['is_own_repo'] = False
            return fork_data
        else:
            print(f"Failed to create fork: {response.status_code} - {response.text}")
            return None
    except requests.RequestException as e:
        print(f"Error creating fork: {e}")
        return None

def load_repository(repo_path="./staging"):
    """
    Load a Git repository from the specified path.

    Args:
        repo_path: Path to the repository directory

    Returns:
        Tuple of (repo, origin, origin_url)
    """
    try:
        repo = Repo(repo_path)
        origin = repo.remotes.origin

        data = {
            "status": "LOADING",
            "message": "Loading repository..."
        }
        supabase_client.table("repo-updates").insert(data).execute()

        origin_url = origin.url
        return repo, origin, origin_url
    except Exception as e:
        print(f"Error loading repository: {e}")
        raise

def create_and_push_branch(repo, origin, files_to_stage):
    """
    Create a new branch, stage files, commit, and push to remote.

    Args:
        repo: Git repository object
        origin: Remote origin
        files_to_stage: List of file paths to stage

    Returns:
        Tuple of (branch_name, username)
    """
    if not Config.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not configured")

    # Create unique branch name
    new_branch_name = f"dependify-{uuid.uuid4().hex[:8]}"
    new_branch = repo.create_head(new_branch_name)
    new_branch.checkout()

    print(f"Created and switched to branch: {new_branch_name}")

    # Stage files
    repo.index.add(files_to_stage)
    print(f"Staged {len(files_to_stage)} files")

    # Create commit
    commit_message = """🤖 Automated code modernization by Dependify

This commit contains automated refactoring to update outdated syntax
and improve code quality using AI-powered analysis.

Generated with Dependify 2.0
"""
    repo.index.commit(commit_message)

    # Update Supabase
    data = {
        "status": "LOADING",
        "message": "Pushing changes to GitHub..."
    }
    supabase_client.table("repo-updates").insert(data).execute()

    # Get authenticated user's username
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    try:
        user_response = requests.get("https://api.github.com/user", headers=headers, timeout=30)
        if user_response.status_code == 200:
            username = user_response.json()["login"]
        else:
            raise Exception(f"Could not get authenticated user: {user_response.text}")
    except requests.RequestException as e:
        raise Exception(f"GitHub API error: {e}")

    # Push to remote
    try:
        origin.push(new_branch)
        print(f"Pushed branch {new_branch_name} to remote")
    except Exception as e:
        print(f"Error pushing to remote: {e}")
        raise

    return new_branch_name, username

def create_pull_request(new_branch_name, repo_owner, repo_name, base_branch, head_owner, is_own_repo=False, changelog_markdown=None):
    """
    Create a pull request from fork to original repository, or within the same repo if user owns it.

    Args:
        new_branch_name: Name of the branch with changes
        repo_owner: Original repository owner
        repo_name: Repository name
        base_branch: Target branch in original repository
        head_owner: Owner of the fork (usually the authenticated user)
        is_own_repo: Whether the user owns the repository (no fork needed)
        changelog_markdown: Optional detailed changelog markdown to include in PR

    Returns:
        Pull request URL or None if failed
    """
    if not Config.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not configured")

    pr_title = f"🤖 Automated code modernization by Dependify"
    
    # Use provided changelog or default PR body
    if changelog_markdown:
        pr_body = changelog_markdown
    elif is_own_repo:
        pr_body = f"""## Automated Code Modernization

This pull request was automatically generated by [Dependify](https://github.com/kshitizz36/Dependify2.0) to modernize outdated syntax and improve code quality.

### Changes Made
- Updated outdated syntax to modern standards
- Improved code readability and maintainability
- Applied best practices and conventions

### Review Guidelines
- Please review all changes carefully before merging
- Run your test suite to ensure compatibility
- Check for any breaking changes in updated APIs

### Branch
`{new_branch_name}`

---
Generated with ❤️ by [Dependify 2.0](https://github.com/kshitizz36/Dependify2.0)
"""
    else:
        pr_body = f"""## Automated Code Modernization

This pull request was automatically generated by [Dependify](https://github.com/kshitizz36/Dependify2.0) to modernize outdated syntax and improve code quality.

### Changes Made
- Updated outdated syntax to modern standards
- Improved code readability and maintainability
- Applied best practices and conventions

### Review Guidelines
- Please review all changes carefully before merging
- Run your test suite to ensure compatibility
- Check for any breaking changes in updated APIs

### About This PR
- This PR was created from a **temporary staging fork** (`{head_owner}/{repo_name}`)
- The fork was created solely to propose these changes
- You can safely delete the fork after reviewing/merging this PR
- All changes are transparent and can be reviewed in the "Files changed" tab

### Branch
`{new_branch_name}` (from fork: `{head_owner}/{repo_name}`)

---
Generated with ❤️ by [Dependify 2.0](https://github.com/kshitizz36/Dependify2.0)

*Note: This is an automated tool for code modernization. The temporary fork used to create this PR can be deleted after the PR is merged or closed.*
"""

    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    # If it's user's own repo, head is just the branch name
    # If it's a fork, head is "username:branch_name"
    if is_own_repo:
        head = new_branch_name
        print(f"Creating PR in user's own repository: {repo_owner}/{repo_name}")
    else:
        head = f"{head_owner}:{new_branch_name}"
        print(f"Creating PR from fork {head_owner}/{repo_name} to {repo_owner}/{repo_name}")

    data = {
        "title": pr_title,
        "head": head,
        "base": base_branch,
        "body": pr_body
    }
    
    # Debug: Log what we're sending
    print(f"DEBUG: PR body length: {len(pr_body) if pr_body else 0} characters")
    print(f"DEBUG: PR body preview: {pr_body[:200] if pr_body else 'None'}...")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"

    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)

        if response.status_code == 201:
            pr_url = response.json().get("html_url")
            print(f"✅ Pull request created: {pr_url}")
            return pr_url
        else:
            error_msg = response.json().get("message", "Unknown error") if response.text else "No response body"
            error_details = response.json() if response.text else {}
            print(f"❌ Failed to create pull request: {response.status_code} - {error_msg}")
            print(f"DEBUG: Full error response: {error_details}")
            print(f"DEBUG: Request URL: {url}")
            print(f"DEBUG: Request head: {data.get('head')}")
            print(f"DEBUG: Request base: {data.get('base')}")
            return None
    except requests.RequestException as e:
        print(f"❌ Error creating pull request: {e}")
        return None


def delete_fork(repo_owner, repo_name):
    """
    Delete a forked repository (OPTIONAL - for cleanup after PR is merged).
    
    This is useful for cleaning up temporary staging forks created by Dependify.
    Users can also manually delete forks from GitHub UI.
    
    Args:
        repo_owner: Fork owner (usually the authenticated user)
        repo_name: Repository name
        
    Returns:
        True if deleted successfully, False otherwise
    """
    if not Config.GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not configured")
    
    headers = {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
    
    try:
        response = requests.delete(url, headers=headers, timeout=30)
        
        if response.status_code == 204:  # GitHub returns 204 for successful deletion
            print(f"✅ Fork deleted: {repo_owner}/{repo_name}")
            return True
        else:
            print(f"Failed to delete fork: {response.status_code} - {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error deleting fork: {e}")
        return False


# Example usage:
def process_repository(repo_owner, repo_name, files_to_update):
    """
    Main function to process a repository and create a PR
    """
    try:
        # 1. Create a fork first
        fork_result = create_fork(repo_owner, repo_name)
        if not fork_result:
            raise Exception("Failed to create fork")
        
        fork_url = fork_result["clone_url"]  # Use the clone URL from the fork
        
        # Add GitHub token to URL for authentication
        if fork_url.startswith("https://github.com/"):
            # Insert token into URL: https://token@github.com/user/repo.git
            authenticated_url = fork_url.replace("https://github.com/", f"https://{Config.GITHUB_TOKEN}@github.com/")
        else:
            authenticated_url = fork_url
        
        # 2. Clone the forked repository
        staging_dir = "./staging"
        if os.path.exists(staging_dir):
            import shutil
            shutil.rmtree(staging_dir)
        
        os.makedirs(staging_dir)
        
        # Clone the fork with authenticated URL
        repo = Repo.clone_from(authenticated_url, staging_dir)
        origin = repo.remotes.origin
        
        # 3. Create and push branch with changes
        new_branch_name, username = create_and_push_branch(repo, origin, files_to_update)
        
        # 4. Create PR from fork to original repository
        pr_url = create_pull_request(
            new_branch_name,
            repo_owner,
            repo_name,
            "main",  # or whatever the base branch should be
            username
        )
        
        return pr_url
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return None