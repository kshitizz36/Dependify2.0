from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker # Assuming you might still use this directly or indirectly
from docker.errors import DockerException, ContainerError # Assuming these are relevant for your Modal setup or other parts
import os
import subprocess
import asyncio
# import websockets # No longer needed for client connection here
import json
import traceback # For detailed error logging

# Hardcoded credentials (development only - consider moving to environment variables for production)
SUPABASE_URL="https://vpfwosqtxotjkpcgsnas.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwZndvc3F0eG90amtwY2dzbmFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjA0MTQ5MCwiZXhwIjoyMDU3NjE3NDkwfQ.eqFTQpKUDKBx4UTnukRjXTpYulANvFQ_t4b56tg4IGg"
GROQ_API_KEY = "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"

# Import updated app objects from your modules
# Adjust these imports to match the names and locations of your modules.
from containers import app as container_app, run_script
from modal_write import app as write_app, process_file
from git_driver import load_repository, create_and_push_branch, create_pull_request
from socket_manager import ConnectionManager

app = FastAPI()
manager = ConnectionManager()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)

# Define request model
class UpdateRequest(BaseModel):
    repository: str
    repository_owner: str
    repository_name: str

@app.post('/update')
async def update(request: UpdateRequest):
    try:
        # Run container-based script execution (Modal app)
        # Assuming container_app.run() is a context manager for Modal
        with container_app.run():
            job_list = run_script.remote(request.repository)

        # Broadcast the initial job list to all connected WebSocket clients
        # Ensure job_list is JSON serializable
        await manager.broadcast(json.dumps({"type": "job_list_update", "data": job_list}))

        # Process files using another Modal app
        # Assuming write_app.run() is a context manager for Modal
        with write_app.run():
            refactored_jobs = []
            for job in job_list: # job_list should be a list of items process_file can handle
                print(f"Processing job: {job}") # Log which job is being processed
                output = process_file.remote(job)  # This can return None if process_file fails

                if output: # Check if output is not None
                    # Construct the full path for staging.
                    # Ensure output['file_path'] and the slicing [24:] are correct for your use case.
                    # This path logic might need adjustment based on what output['file_path'] truly represents.
                    # It's generally safer if output['file_path'] is a relative path within the repo.
                    relative_file_path_in_repo = output['file_path'] # Assuming this is the relative path from repo root
                    # If output['file_path'] contains an absolute path or a prefix that needs stripping:
                    # Example: if output['file_path'] is like '/tmp/some_prefix/actual/repo/path.py'
                    # and you know the prefix length, you'd strip it. The [24:] was an example.
                    # For now, let's assume output['file_path'] IS the relative path from the repo root.
                    
                    # The staging_dir will be created later. The path here should be relative to staging_dir.
                    # So, the 'path' key here should store the path where the file WILL BE in the staging directory.
                    staged_file_path = os.path.join(os.getcwd(), "staging", relative_file_path_in_repo.lstrip('/'))

                    refactored_jobs.append({
                        "path_in_staging": staged_file_path, # Store the full path in staging
                        "relative_path_in_repo": relative_file_path_in_repo, # Store original relative path for git
                        "new_content": output["refactored_code"],
                        "comments": output["refactored_code_comments"]
                    })
                else:
                    print(f"Warning: process_file.remote returned None for job: {job}. Skipping this job.")
                    # Optionally, notify client about this specific job failure via WebSocket
                    await manager.broadcast(json.dumps({"type": "job_processing_failure", "job": job}))
      
        # Create staging area if it doesn't exist
        staging_dir = os.path.join(os.getcwd(), "staging")
        if not os.path.exists(staging_dir):
            os.makedirs(staging_dir)
        else:
            # If it exists, you might want to clean it up from previous runs
            # For simplicity, this example doesn't, but consider `shutil.rmtree(staging_dir)` and then `os.makedirs(staging_dir)`
            pass


        # Clone repository into the staging directory
        # Ensure request.repository is a valid clone URL
        print(f"Cloning repository {request.repository} into {staging_dir}")
        clone_cmd = ["git", "clone", request.repository, staging_dir]
        git_clone_result = subprocess.run(clone_cmd, capture_output=True, text=True, check=False)

        if git_clone_result.returncode != 0:
            error_message = f"Git clone failed for {request.repository}. Stderr: {git_clone_result.stderr}"
            print(error_message) # Log to server
            raise Exception(error_message) # This will be caught by the generic handler

        print(f"Repository cloned successfully into {staging_dir}")

        # Load repository info once clone is complete
        # git_driver functions should handle paths relative to the cloned repo in staging_dir
        repo, origin, origin_url = load_repository(staging_dir)
        
        files_to_commit = []

        for job_data in refactored_jobs:
            # The file path should now be correctly pointing within the staging directory
            file_path_in_staging = job_data.get("path_in_staging")
            
            # Ensure the directory for the file exists within staging_dir
            os.makedirs(os.path.dirname(file_path_in_staging), exist_ok=True)

            print(f"Writing changes to file: {file_path_in_staging}")
            if os.path.exists(os.path.dirname(file_path_in_staging)): # Check if parent dir exists
                with open(file_path_in_staging, "w") as f:
                    f.write(job_data.get("new_content"))
                files_to_commit.append(job_data.get("relative_path_in_repo")) # Commit using relative path
            else:
                print(f"Error: Directory for file {file_path_in_staging} does not exist. Skipping this file.")

        if not files_to_commit:
            print("No files were successfully modified to commit.")
            # Decide how to handle this: maybe return a specific message
            return {
                "status": "noop",
                "message": "No files were refactored or written to the staging area.",
                "repository": request.repository,
                "output": refactored_jobs, # Still show what was attempted
            }

        print(f"Files changed and written to staging: {files_to_commit}")

        new_branch_name = create_and_push_branch(repo, origin, files_to_commit) # Pass relative paths
        print(f"Created and pushed new branch: {new_branch_name}")

        pr_url = create_pull_request(new_branch_name, request.repository_owner, request.repository_name, "main") # Assuming 'main' is the base
        print(f"Created pull request: {pr_url}")

        # Clean up staging directory (optional, but good practice)
        # import shutil
        # shutil.rmtree(staging_dir)
        # print(f"Cleaned up staging directory: {staging_dir}")

        return {
            "status": "success",
            "message": "Repository updated, new branch created, and pull request opened successfully.",
            "repository": request.repository,
            "new_branch": new_branch_name,
            "pull_request_url": pr_url,
            "output": refactored_jobs, # Contains info about what was refactored
        }
    except ContainerError as ce:
        err_output = ce.stderr.decode("utf-8") if ce.stderr else str(ce)
        print(f"ContainerError in /update endpoint: {err_output}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Container error: {err_output}")
    except DockerException as de:
        print(f"DockerException in /update endpoint: {str(de)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Docker error: {str(de)}")
    except Exception as e:
        # This is the generic exception handler. It will catch errors from git clone,
        # Modal calls if they raise unexpected exceptions, or any other part of the try block.
        print(f"An unexpected error occurred in /update endpoint: {str(e)}\nFULL TRACEBACK:\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"An unexpected server error occurred: {str(e)}. Check server logs for more details.")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    # If client_id is not provided via query param, you might want to generate one
    # For simplicity, we'll use it if provided, or None which ConnectionManager might handle
    actual_client_id = client_id if client_id else str(websocket.client.host) + ":" + str(websocket.client.port)
    
    await manager.connect(websocket, actual_client_id)
    print(f"Client {actual_client_id} connected to WebSocket.")
    try:
        while True:
            data = await websocket.receive_text() # Or receive_json if clients always send JSON
            # For now, just log received data. If clients send commands, process them here.
            print(f"Received data from {actual_client_id}: {data}")
            # Example: if client sends a ping or a specific request
            # await manager.send_personal_message(f"Echo: {data}", actual_client_id)
    except WebSocketDisconnect:
        print(f"Client {actual_client_id} disconnected.")
        manager.disconnect(actual_client_id)
    except Exception as e:
        print(f"Error in WebSocket connection for {actual_client_id}: {e}\n{traceback.format_exc()}")
        manager.disconnect(actual_client_id) # Ensure disconnect on other errors too


if __name__ == '__main__':
    import uvicorn
    # Use PORT environment variable if available (Render provides this, typically 10000)
    # Default to 10000 if not set, as per earlier logs.
    port = int(os.environ.get("PORT", 10000))
    # For cloud deployment, host should be "0.0.0.0"
    # reload=False is generally better for production/staging; True is for local dev
    print(f"Starting Uvicorn server on host 0.0.0.0 and port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)
