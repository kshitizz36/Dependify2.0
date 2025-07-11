import modal
import checker
from dotenv import load_dotenv
import os
import supabase

# Create an image with all necessary dependencies
image = modal.Image.debian_slim(python_version="3.10") \
    .apt_install("git", "python3", "bash") \
    .pip_install("python-dotenv", "groq", "fastapi", "uvicorn", "modal", "instructor", "pydantic", "websockets", "supabase") \
    .add_local_python_source("checker") \
    .add_local_python_source("modal_write")

app = modal.App(name="groq-write", image=image)

# Use consistent hardcoded values for Modal deployment
GROQ_API_KEY_HARDCODED = "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"
SUPABASE_URL_HARDCODED = "https://vpfwosqtxotjkpcgsnas.supabase.co"
SUPABASE_KEY_HARDCODED = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwZndvc3F0eG90amtwY2dzbmFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjA0MTQ5MCwiZXhwIjoyMDU3NjE3NDkwfQ.eqFTQpKUDKBx4UTnukRjXTpYulANvFQ_t4b56tg4IGg"

@app.function(
    secrets=[
        modal.Secret.from_name("GROQ_API_KEY"), 
        modal.Secret.from_name("SUPABASE_URL"), 
        modal.Secret.from_name("SUPABASE_KEY"),
    ],
    timeout=300,  # 5 minutes timeout
    retries=2
)
def process_file(job):
    from groq import Groq
    from pydantic import BaseModel, ValidationError
    from os import getenv
    import instructor
    import json
    import supabase

    # Try to get from Modal secrets first, then fallback to hardcoded
    GROQ_API_KEY = getenv("GROQ_API_KEY") or GROQ_API_KEY_HARDCODED
    SUPABASE_URL = getenv("SUPABASE_URL") or SUPABASE_URL_HARDCODED
    SUPABASE_KEY = getenv("SUPABASE_KEY") or SUPABASE_KEY_HARDCODED

    print(f"Using GROQ API Key: {GROQ_API_KEY[:20]}...")

    class JobReport(BaseModel):
        refactored_code: str
        refactored_code_comments: str

    try:
        # Initialize clients
        client = Groq(api_key=GROQ_API_KEY)
        client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)
        supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

        file_path = job["path"]
        code_content = job["code_content"]

        print(f"Processing file: {file_path}")

        user_prompt = (
            "Analyze the following code and determine if the syntax is out of date. "
            "If it is out of date, specify what changes need to be made in the following JSON format:\n\n"
            "{\n"
            '  "refactored_code": "A rewrite of the file that is more up to date, using the native language (i.e. if the file is a NextJS file, rewrite the NextJS file using Javascript/Typescript with the updated API changes)". The file should be a complete file, not just a partial updated code segment,\n'
            '  "refactored_code_comments": "Comments and explanations for your code changes. Be as descriptive, informative, technical as possible."\n'
            "}\n\n"
            f"{code_content}"
        )

        print("Making API call to GROQ...")
        job_report = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes code and returns a JSON object with the refactored code and the comments that come with it. Your goal is to identify outdated syntax in code and suggest changes to update it to the latest syntax."},
                {"role": "user", "content": user_prompt}
            ],
            response_model=JobReport,
            max_retries=3,
            timeout=60
        )

        print("API call successful, updating database...")

        data = {
            "status": "WRITING",
            "message": "Updating " + file_path.split("/")[-1] + "...",
            "code": job_report.refactored_code
        }

        try:
            supabase_client.table("repo-updates").insert(data).execute()
            print("Database update successful")
        except Exception as db_error:
            print(f"Database update failed: {db_error}")

        return {
            "file_path": file_path,
            **job_report.model_dump()
        }

    except Exception as e:
        print(f"Error processing {job.get('path', 'unknown')}: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        # Log the specific error for debugging
        if "401" in str(e) or "Invalid API Key" in str(e):
            print("API Key validation failed!")
            print(f"Current API key starts with: {GROQ_API_KEY[:20] if GROQ_API_KEY else 'None'}")
        
        return {
            "file_path": job.get("path", "unknown"),
            "error": str(e),
            "refactored_code": "",
            "refactored_code_comments": f"Error processing file: {str(e)}"
        }
