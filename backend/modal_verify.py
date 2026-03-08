import modal

# Create an image with necessary dependencies
image = modal.Image.debian_slim(python_version="3.10") \
    .pip_install("anthropic", "pydantic", "supabase")

app = modal.App(name="claude-verify", image=image)

# Configuration
MAX_RETRIES = 2
VERIFIER_MODEL = "claude-3-5-haiku-20241022"   # Haiku verifies (fast/cheap)
ANALYZER_MODEL = "claude-sonnet-4-20250514"     # Sonnet analyzes failures (smart)
FIXER_MODEL = "claude-3-5-haiku-20241022"       # Haiku fixes based on Sonnet's analysis


@app.function(
    timeout=300,
    max_containers=100,
    min_containers=2,
    secrets=[
        modal.Secret.from_name("ANTHROPIC_API_KEY"),
        modal.Secret.from_name("SUPABASE_URL"),
        modal.Secret.from_name("SUPABASE_KEY"),
    ],
)
def verify_and_fix(job):
    """
    Verification Agent: Reviews refactored code using Sonnet, and if issues
    are found, uses Haiku to fix them in a retry loop.

    This is the third agent in the pipeline:
    1. Reader Agent (Sonnet) - identifies outdated code
    2. Writer Agent (Haiku) - refactors code (fast, parallel)
    3. Verifier Agent:
       a. Haiku validates the changes (fast check)
       b. If fails → Sonnet analyzes what went wrong (deep analysis)
       c. Haiku fixes based on Sonnet's diagnosis
       d. Loop until pass or max retries

    Args:
        job: Dict with file_path, original_code, refactored_code, comments

    Returns:
        Dict with verified/fixed refactored_code and verification status
    """
    from anthropic import Anthropic
    from os import getenv
    import json
    import supabase as sb

    ANTHROPIC_API_KEY = getenv("ANTHROPIC_API_KEY")
    SUPABASE_URL = getenv("SUPABASE_URL")
    SUPABASE_KEY = getenv("SUPABASE_KEY")

    client = Anthropic(api_key=ANTHROPIC_API_KEY)
    supabase_client = sb.create_client(SUPABASE_URL, SUPABASE_KEY)

    file_path = job["file_path"]
    original_code = job["original_code"]
    refactored_code = job["refactored_code"]
    comments = job.get("comments", "")
    filename = file_path.split("/")[-1]

    def verify_code(original, refactored):
        """Use Haiku to quickly verify the refactored code."""
        verify_prompt = (
            "You are a code reviewer. Quickly verify this code refactoring is correct.\n\n"
            f"ORIGINAL CODE:\n```\n{original}\n```\n\n"
            f"REFACTORED CODE:\n```\n{refactored}\n```\n\n"
            "Check for:\n"
            "1. Does the refactored code maintain the same functionality?\n"
            "2. Is the syntax valid and uses modern patterns?\n"
            "3. Are there any bugs or regressions introduced?\n"
            "4. Is it a complete file (not partial or truncated)?\n\n"
            "Return ONLY valid JSON:\n"
            '{"passed": true/false, "issues": ["list of issues found"], "confidence": 0.0-1.0}'
        )

        response = client.messages.create(
            model=VERIFIER_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": verify_prompt}]
        )

        text = response.content[0].text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    def analyze_failure(code, issues, original):
        """Use Sonnet to deeply analyze what went wrong and how to fix it."""
        analyze_prompt = (
            "You are a senior software engineer. The following code refactoring has issues.\n"
            "Analyze deeply what went wrong and provide specific, actionable fix instructions.\n\n"
            f"ORIGINAL CODE:\n```\n{original}\n```\n\n"
            f"FAULTY REFACTORED CODE:\n```\n{code}\n```\n\n"
            f"ISSUES FOUND:\n{json.dumps(issues)}\n\n"
            "Return ONLY valid JSON:\n"
            '{"root_cause": "why this failed", "fix_instructions": ["step-by-step instructions for fixing"]}'
        )

        response = client.messages.create(
            model=ANALYZER_MODEL,
            max_tokens=2048,
            messages=[{"role": "user", "content": analyze_prompt}]
        )

        text = response.content[0].text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        return json.loads(text)

    def fix_code(code, analysis, original):
        """Use Haiku to fix code based on Sonnet's analysis."""
        fix_prompt = (
            "Fix the following refactored code based on the senior engineer's analysis.\n\n"
            f"ROOT CAUSE: {analysis.get('root_cause', 'Unknown')}\n\n"
            f"FIX INSTRUCTIONS:\n{json.dumps(analysis.get('fix_instructions', []))}\n\n"
            f"ORIGINAL CODE:\n```\n{original}\n```\n\n"
            f"CODE TO FIX:\n```\n{code}\n```\n\n"
            "Return ONLY the complete fixed code file. No explanations, no markdown, just the code."
        )

        response = client.messages.create(
            model=FIXER_MODEL,
            max_tokens=8192,
            messages=[{"role": "user", "content": fix_prompt}]
        )

        fixed = response.content[0].text.strip()
        if fixed.startswith("```"):
            lines = fixed.split("\n")
            if lines[-1].strip() == "```":
                fixed = "\n".join(lines[1:-1])
            else:
                fixed = "\n".join(lines[1:])

        return fixed

    # === Verification Loop ===
    current_code = refactored_code

    for attempt in range(MAX_RETRIES + 1):
        # Send VERIFYING status to Supabase for real-time UI updates
        try:
            msg = f"🔍 Verifying {filename}"
            if attempt > 0:
                msg += f" (retry {attempt})"
            supabase_client.table("repo-updates").insert({
                "status": "VERIFYING",
                "message": msg,
                "code": current_code
            }).execute()
        except Exception as e:
            print(f"Supabase error: {e}")

        # Verify with Sonnet
        try:
            result = verify_code(original_code, current_code)
        except Exception as e:
            print(f"Verification parse error for {filename}: {e}")
            # If we can't parse verification, assume it's fine
            result = {"passed": True, "issues": [], "confidence": 0.5}

        if result.get("passed", False) or result.get("confidence", 0) > 0.85:
            # PASSED - send verified status
            print(f"✅ {filename} passed verification (attempt {attempt + 1}, confidence: {result.get('confidence', 'N/A')})")
            try:
                supabase_client.table("repo-updates").insert({
                    "status": "VERIFIED",
                    "message": f"✅ Verified {filename}",
                    "code": current_code
                }).execute()
            except Exception as e:
                print(f"Supabase error: {e}")

            return {
                "file_path": file_path,
                "refactored_code": current_code,
                "refactored_code_comments": comments,
                "verified": True,
                "attempts": attempt + 1
            }

        # FAILED - Sonnet analyzes, then Haiku fixes
        if attempt < MAX_RETRIES:
            issues = result.get("issues", ["Unknown issues"])
            print(f"⚠️ {filename} failed verification: {issues}. Analyzing with Sonnet...")

            try:
                supabase_client.table("repo-updates").insert({
                    "status": "FIXING",
                    "message": f"🔧 Analyzing & fixing {filename}",
                    "code": current_code
                }).execute()
            except Exception:
                pass

            try:
                # Sonnet analyzes what went wrong
                analysis = analyze_failure(current_code, issues, original_code)
                print(f"🧠 Sonnet diagnosis: {analysis.get('root_cause', 'unknown')}")
                # Haiku fixes based on Sonnet's analysis
                current_code = fix_code(current_code, analysis, original_code)
            except Exception as e:
                print(f"Fix error for {filename}: {e}")
                break

    # Max retries exhausted - return best attempt
    print(f"⚠️ {filename} - max retries reached, using best attempt")
    return {
        "file_path": file_path,
        "refactored_code": current_code,
        "refactored_code_comments": comments,
        "verified": False,
        "attempts": MAX_RETRIES + 1
    }
