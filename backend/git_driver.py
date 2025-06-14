from git import Repo
import uuid
import requests
from os import getenv
from dotenv import load_dotenv
import os
import supabase

load_dotenv()

supabase = supabase.create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

def create_fork(repo_owner, repo_name):
    """Create a fork of the repository under the authenticated user's account"""
    GITHUB_TOKEN = getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/forks"
    response = requests.post(url, headers=headers)
    if response.status_code == 202:  # GitHub returns 202 for fork creation
        return response.json()
    return None

def load_repository(repo_path="./staging"):
    repo = Repo(repo_path)
    origin = repo.remotes.origin
    data = {
        "status": "LOADING",
        "message": "Loading repository..."
    }
    supabase.table("repo-updates").insert(data).execute()
    origin_url = origin.url
    return repo, origin, origin_url

def create_and_push_branch(repo, origin, files_to_stage):
    new_branch_name = uuid.uuid4().hex
    new_branch = repo.create_head(new_branch_name)
    new_branch.checkout()

    print("Created and switched to branch:", new_branch_name)

    repo.index.add(files_to_stage)
    print("Staged files:", files_to_stage)

    repo.index.commit("Automated commit message.")

    data = {
        "status": "LOADING",
        "message": "Creating branches..."
    }
    supabase.table("repo-updates").insert(data).execute()

    # Get the authenticated user's username
    GITHUB_TOKEN = getenv("GITHUB_TOKEN")
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    user_response = requests.get("https://api.github.com/user", headers=headers)
    if user_response.status_code == 200:
        username = user_response.json()["login"]
    else:
        raise Exception("Could not get authenticated user information")

    origin.push(new_branch)
    print("Pushed branch to remote.")

    return new_branch_name, username

def create_pull_request(new_branch_name, repo_owner, repo_name, base_branch, head_owner):
    """
    Create a pull request from fork to original repository
    @param new_branch_name: Name of the branch with changes
    @param repo_owner: Original repository owner
    @param repo_name: Repository name
    @param base_branch: Target branch in original repository
    @param head_owner: Owner of the fork (usually the authenticated user)
    """
    GITHUB_TOKEN = getenv("GITHUB_TOKEN")
    if not GITHUB_TOKEN:
        raise Exception("GITHUB_TOKEN environment variable not set.")

    pr_title = f"Automated PR for branch {new_branch_name}"
    pr_body = "This pull request was automatically created."
    
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # The head should be in format "username:branch_name"
    head = f"{head_owner}:{new_branch_name}"
    
    data = {
        "title": pr_title,
        "head": head,  # Format: username:branch_name
        "base": base_branch,
        "body": pr_body
    }
    
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    response = requests.post(url, json=data, headers=headers)

    if response.status_code == 201:
        pr_url = response.json().get("html_url")
        print("Pull request created:", pr_url)
        return pr_url
    else:
        print("Failed to create pull request:", response.json())
        return None

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
        
        # 2. Clone the forked repository
        staging_dir = "./staging"
        if os.path.exists(staging_dir):
            import shutil
            shutil.rmtree(staging_dir)
        
        os.makedirs(staging_dir)
        
        # Clone the fork instead of original repository
        repo = Repo.clone_from(fork_url, staging_dir)
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