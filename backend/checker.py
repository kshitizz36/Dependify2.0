import os
import argparse
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError
import json
import instructor
import supabase

load_dotenv()

# Use environment variable first, fallback to hardcoded if not available
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
client = instructor.from_groq(Groq(api_key=GROQ_API_KEY), mode=instructor.Mode.JSON)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://vpfwosqtxotjkpcgsnas.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwZndvc3F0eG90amtwY2dzbmFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjA0MTQ5MCwiZXhwIjoyMDU3NjE3NDkwfQ.eqFTQpKUDKBx4UTnukRjXTpYulANvFQ_t4b56tg4IGg")
supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

class CodeChange(BaseModel):
    path: str
    code_content: str
    reason: str
    add: bool

def get_all_files_recursively(root_directory):
    """
    Recursively collect all file paths under the specified directory.
    """
    all_files = []
    for root, dirs, files in os.walk(root_directory):
        for filename in files:
            # Build the full path to the file
            file_path = os.path.join(root, filename)
            all_files.append(file_path)
    return all_files

def analyze_file_with_llm(file_path):
    """
    Reads file content and queries the LLM to determine if it's out of date
    and what changes might be necessary. Returns a CodeChange object if applicable.
    """
    try:
        with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
            file_content = f.read()
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None

    # Create a user prompt for the LLM
    user_prompt = (
        "Analyze the following code and determine if the syntax is out of date. "
        "If it is out of date, specify what changes need to be made in the following JSON format:\n\n"
        "{\n"
        '  "path": "relative/file/path",\n'
        '  "code_content": "The entire content of the file, before any changes are made. This should be a complete file, not just a partial updated code segment."\n'
        '  "reason": "A short explanation of why the code is out of date."\n'
        '  "add": "Whether the code should be updated and has changes."\n'
        "}\n\n"
        f"{file_content}"
    )

    try:
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes code and returns a JSON object with the path, and raw code content. Your goal is to identify outdated syntax in code and keep track of it."},
                {"role": "user", "content": user_prompt}
            ],
            response_model=CodeChange,
            max_retries=3,
            timeout=30
        )

        print(f"Successfully analyzed: {file_path}")
        print(chat_completion)

        data = {
            "status": "READING",
            "message": "Reading " + file_path.split("/")[-1] + "...",
            "code": chat_completion.code_content
        }

        try:
            supabase.table("repo-updates").insert(data).execute()
        except Exception as db_error:
            print(f"Database insert error: {db_error}")
        
        return chat_completion
    except Exception as api_error:
        print(f"API Error analyzing {file_path}: {api_error}")
        return None
    
def fetch_updates(directory):
    """
    Fetches the latest updates for a given file from the repository.
    """
    analysis_results = []
    all_files = get_all_files_recursively(directory)
    
    print(f"Found {len(all_files)} files to analyze")
    
    for filepath in all_files:
        
        if (
            os.path.basename(filepath).startswith(".") or
            filepath.endswith((".css", ".json", ".md", ".svg", ".ico", ".mjs", ".gitignore", ".env"))
            or ".git/" in filepath
        ):
            continue
        
        print(f"Analyzing: {filepath}")
        response = analyze_file_with_llm(filepath)
        if response is None or response.add == False:
            continue  # Skip if there was an error
        
        response.path = filepath
        analysis_results.append(response)

    return analysis_results

def main():
    print("Testing GROQ API Key...")
    print(f"Using API Key: {GROQ_API_KEY[:20]}...")
    
    # Test API connection first
    try:
        test_client = Groq(api_key=GROQ_API_KEY)
        test_response = test_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": "Hello, just testing the connection."}],
            max_tokens=10
        )
        print("API connection successful!")
    except Exception as e:
        print(f"API connection failed: {e}")
        return
    
    print(fetch_updates("website-test"))

if __name__ == "__main__":
    main()
