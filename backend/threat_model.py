"""
Cross-File Threat Modeling.
Generates a project-level threat model: trust boundaries, data flows, exposure points.
Uses Claude Sonnet for reasoning + filesystem analysis for structure.

Inspired by: OpenAI Codex Security's threat modeling.
Our advantage: We generate AND auto-fix the issues found.
"""
import os
import re
import json
from typing import List, Dict
from anthropic import Anthropic
from config import Config
from checker import get_all_files_recursively, CODE_EXTENSIONS, SKIP_DIRS, MAX_FILE_LINES

client = Anthropic(api_key=Config.ANTHROPIC_API_KEY)
THREAT_MODEL = "claude-sonnet-4-20250514"


def collect_entry_points(repo_root: str) -> List[Dict]:
    """
    Find all entry points where external data enters the system.
    Pure filesystem/regex analysis, no LLM.
    """
    entry_points = []

    # Patterns that indicate entry points by language
    patterns = {
        "http_handler": [
            re.compile(r'@app\.(get|post|put|delete|patch)\s*\('),  # FastAPI/Flask
            re.compile(r'router\.(get|post|put|delete|patch)\s*\('),  # Express
            re.compile(r'@(Get|Post|Put|Delete|Patch)Mapping'),  # Spring
            re.compile(r'def\s+(get|post|put|delete|patch)\s*\(.*request'),  # Django
        ],
        "cli_input": [
            re.compile(r'input\s*\('),  # Python input()
            re.compile(r'process\.argv'),  # Node.js CLI args
            re.compile(r'sys\.argv'),  # Python CLI args
            re.compile(r'argparse\.ArgumentParser'),  # Python argparse
        ],
        "env_vars": [
            re.compile(r'os\.getenv\s*\('),  # Python
            re.compile(r'process\.env\.'),  # Node.js
            re.compile(r'os\.Getenv\s*\('),  # Go
        ],
        "file_read": [
            re.compile(r'open\s*\(.*["\']r'),  # Python file read
            re.compile(r'fs\.readFile'),  # Node.js
            re.compile(r'readFileSync'),  # Node.js sync
        ],
    }

    for fp in get_all_files_recursively(repo_root):
        rel_path = os.path.relpath(fp, repo_root)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        for entry_type, regexes in patterns.items():
            for regex in regexes:
                matches = regex.findall(content)
                if matches:
                    entry_points.append({
                        "file": rel_path,
                        "type": entry_type,
                        "count": len(matches),
                    })
                    break  # One match per type per file is enough

    return entry_points


def collect_sensitive_sinks(repo_root: str) -> List[Dict]:
    """
    Find all sensitive sinks where data leaves the system or touches dangerous operations.
    """
    sinks = []

    patterns = {
        "database_query": [
            re.compile(r'\.execute\s*\('),  # SQL execute
            re.compile(r'\.query\s*\('),  # Generic query
            re.compile(r'\.find\s*\('),  # MongoDB
            re.compile(r'\.select\s*\('),  # Supabase/ORM
            re.compile(r'\.insert\s*\('),  # Insert
        ],
        "subprocess": [
            re.compile(r'subprocess\.\w+\s*\('),  # Python subprocess
            re.compile(r'exec\s*\('),  # exec
            re.compile(r'child_process'),  # Node.js
            re.compile(r'os\.system\s*\('),  # Python os.system
        ],
        "network_request": [
            re.compile(r'fetch\s*\('),  # JS fetch
            re.compile(r'requests\.\w+\s*\('),  # Python requests
            re.compile(r'httpx\.\w+'),  # Python httpx
            re.compile(r'axios\.\w+\s*\('),  # Axios
        ],
        "file_write": [
            re.compile(r'open\s*\(.*["\']w'),  # Python file write
            re.compile(r'fs\.writeFile'),  # Node.js
            re.compile(r'writeFileSync'),  # Node.js sync
        ],
    }

    for fp in get_all_files_recursively(repo_root):
        rel_path = os.path.relpath(fp, repo_root)
        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        for sink_type, regexes in patterns.items():
            for regex in regexes:
                matches = regex.findall(content)
                if matches:
                    sinks.append({
                        "file": rel_path,
                        "type": sink_type,
                        "count": len(matches),
                    })
                    break

    return sinks


def generate_threat_model(repo_root: str) -> Dict:
    """
    Generate a full threat model for the project.
    Step 1: Filesystem analysis (entry points + sinks)
    Step 2: One Sonnet call to reason about data flows and missing protections
    """
    entry_points = collect_entry_points(repo_root)
    sinks = collect_sensitive_sinks(repo_root)

    # If very few entry points/sinks, skip LLM call
    if len(entry_points) == 0 and len(sinks) == 0:
        return {
            "entry_points": [],
            "sinks": [],
            "data_flows": [],
            "missing_protections": [],
            "risk_summary": "No entry points or sensitive sinks detected.",
        }

    # Build context for Sonnet
    context = {
        "entry_points": entry_points[:20],
        "sinks": sinks[:20],
    }

    prompt = (
        "You are a security architect. Given these entry points and sensitive sinks "
        "found in a codebase, generate a threat model.\n\n"
        f"ENTRY POINTS (where external data enters):\n{json.dumps(context['entry_points'], indent=2)}\n\n"
        f"SENSITIVE SINKS (where data is used dangerously):\n{json.dumps(context['sinks'], indent=2)}\n\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  "data_flows": [{"from": "file:type", "to": "file:type", "risk": "high|medium|low", "description": "..."}],\n'
        '  "missing_protections": [{"location": "file", "issue": "...", "recommendation": "..."}],\n'
        '  "risk_summary": "1-2 sentence overall risk assessment"\n'
        "}"
    )

    try:
        response = client.messages.create(
            model=THREAT_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        text = response.content[0].text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        result["entry_points"] = entry_points
        result["sinks"] = sinks
        return result

    except Exception as e:
        print(f"Threat model generation failed: {e}")
        return {
            "entry_points": entry_points,
            "sinks": sinks,
            "data_flows": [],
            "missing_protections": [],
            "risk_summary": f"Analysis incomplete: {str(e)[:100]}",
        }
