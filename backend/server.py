from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import docker
from docker.errors import DockerException, ContainerError
import os
import subprocess
import asyncio
import websockets
import json

# Hardcoded credentials (development only)
SUPABASE_URL="https://vpfwosqtxotjkpcgsnas.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwZndvc3F0eG90amtwY2dzbmFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjA0MTQ5MCwiZXhwIjoyMDU3NjE3NDkwfQ.eqFTQpKUDKBx4UTnukRjXTpYulANvFQ_t4b56tg4IGg"
GROQ_API_KEY = "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"

# If other modules rely on environment variables, update them accordingly.
# For example, in your containers module, you might replace:
#   client = instructor.from_groq(Groq(api_key=os.getenv("GROQ_API_KEY")), mode=instructor.Mode.JSON)
# with:
#   client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.JSON)

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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request model
class UpdateRequest(BaseModel):
    repository: str
    repository_owner: str
    repository_name: str

@app.post('/update')
async def update(request: UpdateRequest):
    try:
        # Run container-based script execution
        with container_app.run():
            job_list = run_script.remote(request.repository)

        async def update_ws():
            uri = "wss://localhost:5000/ws?client_id=1"
            print("updating ws")
            async with websockets.connect(uri) as websocket:
                # Now `websocket` is connected
                await websocket.send(json.dumps(job_list))
                response = await websocket.recv()
                print(response)

        # Run the websocket update in a background task
        asyncio.create_task(update_ws())
 
        with write_app.run():
            refactored_jobs = []
            for job in job_list:
                output = process_file.remote(job)  # spin up a container for every file and wait for result
                refactored_jobs.append({
                    "path": f"{os.getcwd()}/staging{output['file_path'][24:]}",
                    "new_content": output["refactored_code"],
                    "comments": output["refactored_code_comments"]
                })
      
        # Create staging area
        staging_dir = os.path.join(os.getcwd(), "staging")
        if not os.path.exists(staging_dir):
            os.makedirs(staging_dir)

        # Clone repository and wait for completion
        clone_cmd = ["git", "clone", request.repository, staging_dir]
        result = subprocess.call(clone_cmd)

        # Load repository info once clone is complete
        repo, origin, origin_url = load_repository(staging_dir)
        files_changed = []

        for job in refactored_jobs:
            file_path = job.get("path")
            print("filepath:", file_path)
            files_changed.append(file_path)
            if os.path.exists(file_path):
                with open(file_path, "w") as f:
                    f.write(job.get("new_content"))
            else:
                print(f"File {file_path} does not exist")

        new_branch_name = create_and_push_branch(repo, origin, files_changed)
        create_pull_request(new_branch_name, request.repository_owner, request.repository_name, "main")

        return {
            "status": "success",
            "message": "Repository updated and script executed successfully",
            "repository": request.repository,
            "output": refactored_jobs,
        }
    except ContainerError as ce:
        err_output = ce.stderr.decode("utf-8") if ce.stderr else str(ce)
        raise HTTPException(status_code=500, detail=f"Container error: {err_output}")
    except DockerException as de:
        raise HTTPException(status_code=500, detail=f"Docker error: {str(de)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    await manager.connect(websocket, client_id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(client_id)

# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run("server:app", host="127.0.0.1", port=5000, reload=True)
if __name__ == '__main__':
    import uvicorn
    # Change host from "127.0.0.1" to "0.0.0.0" for cloud deployment
    # Also use PORT environment variable if available (Render provides this)
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=False)

