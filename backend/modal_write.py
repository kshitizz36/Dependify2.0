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
    .add_local_python_source("modal_write")  # Add self as local source

app = modal.App(name="groq-write", image=image)

load_dotenv()

SUPABASE_URL="https://vpfwosqtxotjkpcgsnas.supabase.co"
SUPABASE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InZwZndvc3F0eG90amtwY2dzbmFzIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0MjA0MTQ5MCwiZXhwIjoyMDU3NjE3NDkwfQ.eqFTQpKUDKBx4UTnukRjXTpYulANvFQ_t4b56tg4IGg"
supabase = supabase.create_client(SUPABASE_URL, SUPABASE_KEY)

@app.function(secrets=[modal.Secret.from_name("GROQ_API_KEY"), modal.Secret.from_name("SUPABASE_URL"), modal.Secret.from_name("SUPABASE_KEY")])
def process_file(job):
  from groq import Groq
  from pydantic import BaseModel, ValidationError
  from os import getenv
  import instructor
  import json

  GROQ_API_KEY = getenv("GROQ_API_KEY")

  class JobReport(BaseModel):
    refactored_code: str
    refactored_code_comments: str

  client = Groq(api_key="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")
  client = instructor.from_groq(client, mode=instructor.Mode.TOOLS)

  file_path = job["path"]
  code_content = job["code_content"]

  user_prompt = (
      "Analyze the following code and determine if the syntax is out of date. "
      "If it is out of date, specify what changes need to be made in the following JSON format:\n\n"
      "{\n"
      '  "refactored_code": "A rewrite of the file that is more up to date, using the native language (i.e. if the file is a NextJS file, rewrite the NextJS file using Javascript/Typescript with the updated API changes)". The file should be a complete file, not just a partial updated code segment,\n'
      '  "refactored_code_comments": "Comments and explanations for your code changes. Be as descriptive, informative, technical as possible."\n'
      "}\n\n"
      f"{code_content}"
  )

  try:
      print("Trying...")
      job_report = client.chat.completions.create(
          model="llama-3.1-8b-instant",
          messages=[{"role": "system", "content": "You are a helpful assistant that analyzes code and returns a JSON object with the refactored code and the comments that come with it. Your goal is to identify outdated syntax in code and suggest changes to update it to the latest syntax."}, {"role": "user", "content": user_prompt}],
          response_model=JobReport,
      )

      data = {
          "status": "WRITING",
          "message": "Updating " + file_path.split("/")[-1] + "...",
          "code": job_report.refactored_code
      }

      supabase.table("repo-updates").insert(data).execute()

      return {
          "file_path": file_path,
          **job_report.model_dump()
      }
  except (ValidationError, json.JSONDecodeError) as parse_error:
      print(f"Error parsing LLM response for {file_path}: {parse_error}")
      return None
  except Exception as e:
      # Handle any other exceptions, e.g. network errors, model issues, etc.
      print(f"Error analyzing {file_path}: {e}")
      return None