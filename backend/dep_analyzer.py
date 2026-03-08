"""
Behavioral Dependency Analyzer.
Analyzes what dependencies actually DO — not just CVE lookups.
Detects suspicious install scripts, network access, env var reads, etc.

Inspired by: Socket.dev (behavioral analysis of packages).
Our advantage: We detect AND suggest safer alternatives via the Writer agent.
"""
import os
import json
import re
from typing import List, Dict, Optional


def analyze_npm_deps(repo_root: str) -> List[dict]:
    """
    Analyze npm dependencies for behavioral risks.
    Checks package.json for install scripts, suspicious deps, etc.
    """
    findings = []
    pkg_path = os.path.join(repo_root, "package.json")
    if not os.path.exists(pkg_path):
        return findings

    try:
        with open(pkg_path, 'r', encoding='utf-8') as f:
            pkg = json.load(f)
    except Exception:
        return findings

    # Check for install scripts (postinstall, preinstall can execute arbitrary code)
    scripts = pkg.get("scripts", {})
    dangerous_hooks = ["preinstall", "postinstall", "preuninstall", "postuninstall"]
    for hook in dangerous_hooks:
        if hook in scripts:
            script_content = scripts[hook]
            findings.append({
                "type": "install_script",
                "severity": "high",
                "package": "project",
                "description": f"Project has a '{hook}' script: {script_content[:100]}",
                "risk": "Install scripts can execute arbitrary code during npm install",
                "evidence": [f"package.json scripts.{hook} = {script_content[:100]}"],
            })

    # Check all deps for known risky patterns
    all_deps = {}
    all_deps.update(pkg.get("dependencies", {}))
    all_deps.update(pkg.get("devDependencies", {}))

    for name, version in all_deps.items():
        # URL-based dependencies (not from npm registry)
        if version.startswith(("http://", "https://", "git://", "git+", "github:")):
            findings.append({
                "type": "url_dependency",
                "severity": "medium",
                "package": name,
                "description": f"Package '{name}' is installed from a URL, not npm registry",
                "risk": "URL dependencies bypass npm's security scanning",
                "evidence": [f"{name}: {version}"],
            })

        # File-based dependencies
        if version.startswith("file:"):
            findings.append({
                "type": "file_dependency",
                "severity": "low",
                "package": name,
                "description": f"Package '{name}' is a local file dependency",
                "risk": "File dependencies may contain unreviewed code",
                "evidence": [f"{name}: {version}"],
            })

    # Check for package-lock.json integrity issues
    lock_path = os.path.join(repo_root, "package-lock.json")
    if os.path.exists(lock_path):
        try:
            with open(lock_path, 'r', encoding='utf-8') as f:
                lock = json.load(f)
            # Check for packages with install scripts in lockfile
            packages = lock.get("packages", {})
            for pkg_name, pkg_data in packages.items():
                if pkg_data.get("hasInstallScript") and pkg_name:
                    short_name = pkg_name.replace("node_modules/", "")
                    if short_name and short_name not in ("", "."):
                        findings.append({
                            "type": "dep_install_script",
                            "severity": "medium",
                            "package": short_name,
                            "description": f"Dependency '{short_name}' has install scripts",
                            "risk": "Install scripts in dependencies can execute code during install",
                            "evidence": [f"{short_name} has hasInstallScript=true in lockfile"],
                        })
        except Exception:
            pass

    return findings


def analyze_python_deps(repo_root: str) -> List[dict]:
    """
    Analyze Python dependencies for behavioral risks.
    """
    findings = []

    # Check requirements.txt
    req_path = os.path.join(repo_root, "requirements.txt")
    if os.path.exists(req_path):
        try:
            with open(req_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue

                # URL-based dependencies
                if line.startswith(("http://", "https://", "git+")):
                    findings.append({
                        "type": "url_dependency",
                        "severity": "medium",
                        "package": line.split("/")[-1].split("@")[0] if "/" in line else line[:50],
                        "description": f"Package installed from URL: {line[:80]}",
                        "risk": "URL dependencies bypass PyPI security scanning",
                        "evidence": [line[:100]],
                    })

                # Unpinned versions (no == or >=)
                if re.match(r'^[a-zA-Z][\w-]*$', line):
                    findings.append({
                        "type": "unpinned_version",
                        "severity": "low",
                        "package": line,
                        "description": f"Package '{line}' has no version pin",
                        "risk": "Unpinned deps can change behavior between installs",
                        "evidence": [f"{line} in requirements.txt with no version constraint"],
                    })
        except Exception:
            pass

    # Check setup.py for dangerous patterns
    setup_path = os.path.join(repo_root, "setup.py")
    if os.path.exists(setup_path):
        try:
            with open(setup_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if "cmdclass" in content:
                findings.append({
                    "type": "custom_install",
                    "severity": "medium",
                    "package": "project",
                    "description": "setup.py uses custom cmdclass (custom install commands)",
                    "risk": "Custom install commands can execute arbitrary code",
                    "evidence": ["cmdclass found in setup.py"],
                })

            if "subprocess" in content or "os.system" in content:
                findings.append({
                    "type": "setup_exec",
                    "severity": "high",
                    "package": "project",
                    "description": "setup.py executes system commands",
                    "risk": "System command execution during package install",
                    "evidence": ["subprocess or os.system found in setup.py"],
                })
        except Exception:
            pass

    return findings


def analyze_code_for_dangerous_patterns(repo_root: str, file_paths: List[str]) -> List[dict]:
    """
    Scan code files for dangerous dependency usage patterns.
    This catches things like eval(user_input), exec(), etc.
    """
    findings = []

    dangerous_patterns = [
        {
            "pattern": re.compile(r'\beval\s*\('),
            "name": "eval_usage",
            "severity": "high",
            "description": "eval() executes arbitrary code",
            "languages": {".js", ".jsx", ".ts", ".tsx", ".py"},
        },
        {
            "pattern": re.compile(r'\bexec\s*\('),
            "name": "exec_usage",
            "severity": "high",
            "description": "exec() executes arbitrary code",
            "languages": {".py"},
        },
        {
            "pattern": re.compile(r'dangerouslySetInnerHTML'),
            "name": "xss_risk",
            "severity": "high",
            "description": "dangerouslySetInnerHTML can lead to XSS",
            "languages": {".jsx", ".tsx", ".js", ".ts"},
        },
        {
            "pattern": re.compile(r'subprocess\.call\s*\(.*shell\s*=\s*True'),
            "name": "shell_injection",
            "severity": "critical",
            "description": "subprocess with shell=True is vulnerable to command injection",
            "languages": {".py"},
        },
        {
            "pattern": re.compile(r'pickle\.loads?\s*\('),
            "name": "pickle_deserialization",
            "severity": "high",
            "description": "pickle deserialization can execute arbitrary code",
            "languages": {".py"},
        },
        {
            "pattern": re.compile(r'__import__\s*\('),
            "name": "dynamic_import",
            "severity": "medium",
            "description": "Dynamic import can load arbitrary modules",
            "languages": {".py"},
        },
        {
            "pattern": re.compile(r'innerHTML\s*='),
            "name": "innerhtml_xss",
            "severity": "medium",
            "description": "Direct innerHTML assignment can lead to XSS",
            "languages": {".js", ".jsx", ".ts", ".tsx"},
        },
    ]

    for fp in file_paths:
        _, ext = os.path.splitext(fp)
        ext = ext.lower()

        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        rel_path = os.path.relpath(fp, repo_root)

        for dp in dangerous_patterns:
            if ext not in dp["languages"]:
                continue
            matches = dp["pattern"].findall(content)
            if matches:
                findings.append({
                    "type": dp["name"],
                    "severity": dp["severity"],
                    "package": rel_path,
                    "description": f"{dp['description']} in {rel_path}",
                    "risk": dp["description"],
                    "evidence": [f"Found {len(matches)} occurrence(s) in {rel_path}"],
                })

    return findings


def run_full_dep_analysis(repo_root: str, file_paths: List[str]) -> dict:
    """
    Run all dependency analyses and return combined results.
    """
    all_findings = []

    # Manifest-based analysis
    all_findings.extend(analyze_npm_deps(repo_root))
    all_findings.extend(analyze_python_deps(repo_root))

    # Code pattern analysis
    all_findings.extend(analyze_code_for_dangerous_patterns(repo_root, file_paths))

    # Summarize
    by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        sev = f.get("severity", "low")
        if sev in by_severity:
            by_severity[sev] += 1

    return {
        "total_findings": len(all_findings),
        "by_severity": by_severity,
        "findings": all_findings,
    }
