"""
Blast Radius Analysis - Import graph builder.
Analyzes which files depend on which, so we know the impact of changing a file.
Pure filesystem/regex analysis, no LLM needed.

Inspired by: Reclaim Security's PIPE engine + Aikido's reachability analysis.
"""
import os
import re
from typing import Dict, List, Set


# Import patterns by language
IMPORT_PATTERNS = {
    # JavaScript/TypeScript: import X from './path', require('./path')
    '.js': [
        re.compile(r'''(?:import\s+.*?\s+from\s+['"](.+?)['"])'''),
        re.compile(r'''(?:import\s*\(\s*['"](.+?)['"]\s*\))'''),
        re.compile(r'''(?:require\s*\(\s*['"](.+?)['"]\s*\))'''),
    ],
    '.jsx': None,  # same as .js
    '.ts': None,
    '.tsx': None,
    '.mjs': None,

    # Python: import X, from X import Y
    '.py': [
        re.compile(r'''(?:from\s+(\S+)\s+import)'''),
        re.compile(r'''(?:import\s+(\S+))'''),
    ],

    # Go: import "path"
    '.go': [
        re.compile(r'''(?:import\s+["'](.+?)["'])'''),
        re.compile(r'''(?:["'](.+?)["'])'''),  # inside import blocks
    ],

    # Java/Kotlin: import com.package.Class
    '.java': [
        re.compile(r'''(?:import\s+(?:static\s+)?(\S+))'''),
    ],
    '.kt': None,  # same as .java

    # Ruby: require 'path', require_relative 'path'
    '.rb': [
        re.compile(r'''(?:require(?:_relative)?\s+['"](.+?)['"])'''),
    ],

    # PHP: use Namespace\Class, require 'path'
    '.php': [
        re.compile(r'''(?:use\s+(\S+))'''),
        re.compile(r'''(?:require(?:_once)?\s+['"](.+?)['"])'''),
        re.compile(r'''(?:include(?:_once)?\s+['"](.+?)['"])'''),
    ],

    # Rust: use crate::module, mod module
    '.rs': [
        re.compile(r'''(?:use\s+(?:crate::)?(\S+))'''),
        re.compile(r'''(?:mod\s+(\w+))'''),
    ],

    # Vue/Svelte: same as JS
    '.vue': None,
    '.svelte': None,
}

# Alias groups (share same patterns)
_js_patterns = IMPORT_PATTERNS['.js']
for ext in ['.jsx', '.ts', '.tsx', '.mjs', '.vue', '.svelte']:
    IMPORT_PATTERNS[ext] = _js_patterns

_java_patterns = IMPORT_PATTERNS['.java']
IMPORT_PATTERNS['.kt'] = _java_patterns


def resolve_relative_import(importing_file: str, import_path: str, repo_root: str) -> str:
    """
    Resolve a relative import path to an absolute path within the repo.
    Returns the relative path from repo root, or the raw import if unresolvable.
    """
    if import_path.startswith('.'):
        # Relative import
        dir_of_file = os.path.dirname(importing_file)
        resolved = os.path.normpath(os.path.join(dir_of_file, import_path))

        # Try common extensions
        for ext in ['', '.ts', '.tsx', '.js', '.jsx', '.py', '/index.ts', '/index.tsx', '/index.js']:
            candidate = resolved + ext
            full_path = os.path.join(repo_root, candidate)
            if os.path.isfile(full_path):
                return candidate

        return resolved
    else:
        # Absolute/package import - return as-is (external dep or alias)
        return import_path


def build_import_graph(repo_root: str, file_paths: List[str]) -> Dict[str, dict]:
    """
    Build a bidirectional import graph for all files in the repo.

    Returns dict keyed by relative file path:
    {
        "src/utils/format.ts": {
            "imports": ["src/lib/helpers.ts", "lodash"],
            "imported_by": ["src/components/Card.tsx", "src/pages/index.tsx"],
            "import_count": 2,
            "imported_by_count": 2,
            "is_external_facing": True  # has exports used by other files
        }
    }
    """
    graph: Dict[str, dict] = {}

    # Initialize all files
    for fp in file_paths:
        rel = os.path.relpath(fp, repo_root)
        graph[rel] = {
            "imports": [],
            "imported_by": [],
            "import_count": 0,
            "imported_by_count": 0,
            "is_external_facing": False,
        }

    # Parse imports for each file
    for fp in file_paths:
        rel = os.path.relpath(fp, repo_root)
        _, ext = os.path.splitext(fp)
        ext = ext.lower()

        patterns = IMPORT_PATTERNS.get(ext)
        if not patterns:
            continue

        try:
            with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue

        imports: Set[str] = set()
        for pattern in patterns:
            matches = pattern.findall(content)
            for match in matches:
                resolved = resolve_relative_import(rel, match, repo_root)
                imports.add(resolved)

        graph[rel]["imports"] = list(imports)
        graph[rel]["import_count"] = len(imports)

    # Build reverse edges (imported_by)
    all_rel_paths = set(graph.keys())
    for file_path, data in graph.items():
        for imp in data["imports"]:
            # Check if this import resolves to a file in the repo
            # Try exact match and common variations
            candidates = [imp]
            if not os.path.splitext(imp)[1]:
                for ext in ['.ts', '.tsx', '.js', '.jsx', '.py']:
                    candidates.append(imp + ext)
                candidates.append(imp + '/index.ts')
                candidates.append(imp + '/index.tsx')
                candidates.append(imp + '/index.js')

            for candidate in candidates:
                if candidate in all_rel_paths:
                    graph[candidate]["imported_by"].append(file_path)
                    graph[candidate]["imported_by_count"] += 1
                    graph[candidate]["is_external_facing"] = True
                    break

    return graph


def get_blast_radius(graph: Dict[str, dict], file_path: str) -> dict:
    """
    Get the blast radius for a single file.
    Returns info about what depends on this file.
    """
    data = graph.get(file_path, {})
    imported_by = data.get("imported_by", [])
    return {
        "file": file_path,
        "direct_dependents": imported_by,
        "dependent_count": len(imported_by),
        "risk_level": "HIGH" if len(imported_by) >= 10 else "MEDIUM" if len(imported_by) >= 3 else "LOW",
        "is_external_facing": data.get("is_external_facing", False),
    }


def compute_blast_radius_for_changes(repo_root: str, changed_files: List[str], all_files: List[str]) -> dict:
    """
    Main entry point: compute blast radius for a set of changed files.

    Args:
        repo_root: Root directory of the repo
        changed_files: List of files that will be modified (relative paths)
        all_files: All code files in the repo (absolute paths)

    Returns:
        Dict with per-file blast radius and aggregate stats
    """
    graph = build_import_graph(repo_root, all_files)

    results = []
    total_affected = set()

    for fp in changed_files:
        # Normalize to relative path
        rel = os.path.relpath(fp, repo_root) if os.path.isabs(fp) else fp
        radius = get_blast_radius(graph, rel)
        results.append(radius)
        total_affected.update(radius["direct_dependents"])

    # Find high-risk changes (files with many dependents)
    high_risk = [r for r in results if r["risk_level"] == "HIGH"]

    return {
        "files_changed": len(changed_files),
        "total_affected_files": len(total_affected),
        "high_risk_changes": len(high_risk),
        "per_file": results,
        "all_affected_files": list(total_affected),
    }
