import os
import argparse
from groq import Groq
from pydantic import BaseModel, ValidationError
import json
import instructor
import supabase

# Initialize clients lazily to avoid issues with Modal secrets
_client = None
_supabase_client = None

def get_client():
    """Get or create Groq client with API key."""
    global _client
    if _client is None:
        # Read from environment variable (Modal secrets inject these)
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            # Fallback to Config for local development
            try:
                from config import Config
                api_key = Config.GROQ_API_KEY
            except ImportError:
                raise ValueError("GROQ_API_KEY not found in environment or config")
        
        _client = instructor.from_groq(
            Groq(api_key=api_key),
            mode=instructor.Mode.JSON
        )
    return _client

def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            # Fallback to Config for local development
            try:
                from config import Config
                url = url or Config.SUPABASE_URL
                key = key or Config.SUPABASE_KEY
            except ImportError:
                raise ValueError("SUPABASE credentials not found in environment or config")
        
        _supabase_client = supabase.create_client(url, key)
    return _supabase_client


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
    with open(file_path, 'r', encoding="utf-8", errors="ignore") as f:
        file_content = f.read()


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
        client = get_client()
        chat_completion = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that analyzes code and returns a JSON object with the path, and raw code content. Your goal is to identify outdated syntax in code and keep track of it."},
                {"role": "user", "content": user_prompt}
            ],
            response_model=CodeChange,
        )

        print(chat_completion)

        filename = file_path.split("/")[-1]
        data = {
            "status": "READING",
            "message": f"📖 Reading {filename}",
            "code": chat_completion.code_content
        }

        try:
            supabase_client = get_supabase_client()
            supabase_client.table("repo-updates").insert(data).execute()
        except Exception as db_error:
            # If filename column doesn't exist, try without it
            print(f"Database error (may need to add 'filename' column): {db_error}")
            data_fallback = {
                "status": "READING",
                "message": f"📖 Reading {filename}",
                "code": chat_completion.code_content
            }
            supabase_client.table("repo-updates").insert(data_fallback).execute()
        
        return chat_completion
    except (ValidationError, json.JSONDecodeError) as parse_error:
        print(f"Error parsing LLM response for {file_path}: {parse_error}")
        return None
    except Exception as e:
        # Handle any other exceptions, e.g. network errors, model issues, etc.
        print(f"Error analyzing {file_path}: {e}")
        return None
    
def fetch_updates(directory):
    """
    Fetches the latest updates for a given file from the repository.
    """
    analysis_results = []
    all_files = get_all_files_recursively(directory)
    for filepath in all_files:
        
        if (
            os.path.basename(filepath).startswith(".") or
            filepath.endswith((".css", ".json", ".md", ".svg", ".ico", ".mjs", ".gitignore", ".env"))
            or ".git/" in filepath
        ):
            continue
        # Query LLM for this file

        response = analyze_file_with_llm(filepath)
        if response is None or response.add == False:
            continue  # Skip if there was an error
        print(filepath)
        response.path = filepath
        analysis_results.append(response)

    return analysis_results
    


def main():
    # print(fetch_updates("website-test")[0])
    print(fetch_updates("website-test"))

    # parser = argparse.ArgumentParser(description="Analyze code files for outdated syntax.")
    # parser.add_argument("directory", type=str, help="Directory to analyze")

    # args = parser.parse_args()
    # directory_to_analyze = args.directory

    # # Store results in a list of CodeChange instances
    # analysis_results = []

    # all_files = get_all_files_recursively(directory_to_analyze)
    # for filepath in all_files:
        
    #     if (
    #         os.path.basename(filepath).startswith(".") or
    #         filepath.endswith((".css", ".json", ".md", ".svg", ".ico", ".mjs", ".gitignore", ".env"))
    #         or ".git/" in filepath
    #     ):
    #         continue
    #     # Query LLM for this file

    #     response = analyze_file_with_llm(filepath)
    #     if response is None:
    #         continue  # Skip if there was an error
    #     response.path = filepath
    #     analysis_results.append(response)

    

    # # Print out any files that are deemed out of date and their suggested changes
    # if not analysis_results:
    #     print("No files were found to be out of date.")
    # else:
    #     print("=UPDATED=")
    #     print(analysis_results)

        # for result in analysis_results:
        #     print(f"File PATH: {result.path}")
        #     print(f"File CONTENT: {result.code_content}")
        #     print(f"Reason: {result.reason}")
        #     print("-" * 40)

if __name__ == "__main__":
    main()
