import modal
import checker
import os
import supabase
from validators import validate_and_score, SyntaxValidator
from changelog_formatter import ChangelogFormatter

# Create an image with all necessary dependencies
image = modal.Image.debian_slim(python_version="3.10") \
    .apt_install("git", "python3", "bash") \
    .pip_install("python-dotenv", "groq", "fastapi", "uvicorn", "modal", "instructor", "pydantic", "websockets", "supabase") \
    .add_local_python_source("checker") \
    .add_local_python_source("modal_write") \
    .add_local_python_source("config") \
    .add_local_python_source("auth") \
    .add_local_python_source("containers") \
    .add_local_python_source("server")

app = modal.App(name="groq-write", image=image)

@app.function(
    timeout=300,  # 5 minutes per file
    max_containers=100,  # Process up to 100 files in parallel
    min_containers=3,  # Keep 3 containers warm for faster response
    secrets=[
        modal.Secret.from_name("GROQ_API_KEY"),
        modal.Secret.from_name("SUPABASE_URL"),
        modal.Secret.from_name("SUPABASE_KEY"),
    ],
)
def process_file(job):
    """
    Process a single file: analyze and refactor outdated code using LLM.

    Args:
        job: Dictionary containing file path and code content

    Returns:
        Dictionary with refactored code and comments
    """
    from groq import Groq
    from pydantic import BaseModel, ValidationError
    from os import getenv
    import instructor
    import json
    import supabase

    # Get credentials from Modal secrets (environment variables)
    GROQ_API_KEY = getenv("GROQ_API_KEY")
    SUPABASE_URL = getenv("SUPABASE_URL")
    SUPABASE_KEY = getenv("SUPABASE_KEY")
    
    # Debug: Print to verify secrets are loaded
    print(f"Debug: GROQ_API_KEY present: {bool(GROQ_API_KEY)}")
    print(f"Debug: GROQ_API_KEY length: {len(GROQ_API_KEY) if GROQ_API_KEY else 0}")
    
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not found in environment variables")
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE credentials not found in environment variables")

    # Initialize Supabase client
    supabase_client = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

    class JobReport(BaseModel):
        refactored_code: str
        refactored_code_comments: str

    # Initialize Groq client with API key from environment
    client = Groq(api_key=GROQ_API_KEY)
    client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)

    # Validate input
    if not job or not isinstance(job, dict):
        print(f"Error: Invalid job input")
        return None
    
    file_path = job.get("path")
    code_content = job.get("code_content")
    
    if not file_path or not code_content:
        print(f"Error: Missing path or code_content in job")
        return None
    
    old_code = code_content  # Save original for comparison

    user_prompt = (
        "Analyze the following code and determine if the syntax is out of date. "
        "If it is out of date, specify what changes need to be made in the following JSON format:\n\n"
        "{\n"
        '  "refactored_code": "A rewrite of the file that is more up to date, using the native language (i.e. if the file is a NextJS file, rewrite the NextJS file using Javascript/Typescript with the updated API changes). The file should be a complete file, not just a partial updated code segment.",\n'
        '  "refactored_code_comments": "Comments and explanations for your code changes. Be as descriptive, informative, and technical as possible."\n'
        "}\n\n"
        f"File: {file_path}\n\n"
        f"Code:\n{code_content}"
    )

    try:
        print(f"Processing file: {file_path}")
        job_report = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful assistant that analyzes code and returns a JSON object with the refactored code and the comments that come with it. Your goal is to identify outdated syntax in code and suggest changes to update it to the latest syntax."
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            response_model=JobReport,
        )

        # Validate refactored code and calculate confidence score
        filename = file_path.split("/")[-1]
        language = SyntaxValidator.detect_language(file_path)
        
        validation_result, confidence_score = validate_and_score(
            file_path,
            old_code,
            job_report.refactored_code
        )
        
        # Generate enhanced changelog
        file_change = ChangelogFormatter.format_file_change(
            file_path=file_path,
            old_code=old_code,
            new_code=job_report.refactored_code,
            explanation=job_report.refactored_code_comments,
            confidence_score=confidence_score.score,
            language=language
        )
        
        # Log validation results
        validation_emoji = "✅" if validation_result.is_valid else "⚠️"
        
        print(f"{validation_emoji} {filename}: Processing complete")
        if not validation_result.is_valid:
            print(f"  Validation warning: {validation_result.error_message}")
        
        # Update Supabase with clean status message
        data = {
            "status": "WRITING",
            "message": f"✍️ Updating {filename}",
            "code": job_report.refactored_code
        }

        try:
            supabase_client.table("repo-updates").insert(data).execute()
        except Exception as db_error:
            # If columns don't exist, try without them
            print(f"Database error (may need to add columns): {db_error}")
            data_fallback = {
                "status": "WRITING",
                "message": f"✍️ Updating {filename}",
                "code": job_report.refactored_code
            }
            supabase_client.table("repo-updates").insert(data_fallback).execute()

        return {
            "file_path": file_path,
            "original_code": old_code,  # Include original for changelog
            "validation": {
                "is_valid": validation_result.is_valid,
                "language": validation_result.language,
                "error": validation_result.error_message
            },
            "confidence_score": confidence_score.score,
            "confidence_factors": confidence_score.factors,
            "changelog": {
                "lines_added": file_change.lines_added,
                "lines_removed": file_change.lines_removed,
                "key_changes": file_change.key_changes
            },
            **job_report.model_dump()
        }
    except (ValidationError, json.JSONDecodeError) as parse_error:
        print(f"Error parsing LLM response for {file_path}: {parse_error}")
        return None
    except Exception as e:
        # Handle any other exceptions, e.g. network errors, model issues, etc.
        print(f"Error analyzing {file_path}: {e}")
        return None
