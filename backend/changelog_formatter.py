"""
AI-Explained Changelog Formatter.
Formats refactored code comments into detailed, file-by-file changelogs
with clear explanations of AI reasoning for each change.
"""

from typing import List, Dict
from dataclasses import dataclass
import json


@dataclass
class FileChange:
    """Represents a single file change with AI explanation."""
    file_path: str
    old_code: str
    new_code: str
    explanation: str
    confidence_score: int
    language: str
    lines_added: int
    lines_removed: int
    key_changes: List[str]


class ChangelogFormatter:
    """Format AI code changes into human-readable changelogs."""
    
    @staticmethod
    def parse_explanation(raw_comments: str) -> Dict[str, List[str]]:
        """
        Parse AI explanation into structured sections.
        
        Args:
            raw_comments: Raw explanation from LLM
            
        Returns:
            Dictionary with categorized changes
        """
        sections = {
            'modernization': [],
            'deprecations': [],
            'best_practices': [],
            'api_updates': [],
            'other': []
        }
        
        # Keywords for categorization
        modernization_keywords = ['modern', 'updated', 'new syntax', 'es6', 'async/await', 'latest']
        deprecation_keywords = ['deprecated', 'outdated', 'legacy', 'old', 'replaced']
        best_practice_keywords = ['best practice', 'improve', 'clean', 'readable', 'maintainable']
        api_keywords = ['api', 'library', 'framework', 'version', 'import']
        
        # Split into sentences
        sentences = raw_comments.replace('\n', ' ').split('. ')
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            sentence_lower = sentence.lower()
            
            # Categorize based on keywords
            if any(keyword in sentence_lower for keyword in modernization_keywords):
                sections['modernization'].append(sentence)
            elif any(keyword in sentence_lower for keyword in deprecation_keywords):
                sections['deprecations'].append(sentence)
            elif any(keyword in sentence_lower for keyword in best_practice_keywords):
                sections['best_practices'].append(sentence)
            elif any(keyword in sentence_lower for keyword in api_keywords):
                sections['api_updates'].append(sentence)
            else:
                sections['other'].append(sentence)
        
        return sections
    
    @staticmethod
    def calculate_diff_stats(old_code: str, new_code: str) -> tuple:
        """
        Calculate exact git-style diff statistics matching GitHub's display.
        
        Args:
            old_code: Original code
            new_code: Refactored code
            
        Returns:
            Tuple of (lines_added, lines_removed)
        """
        if not old_code and not new_code:
            return 0, 0
        
        # Split into lines preserving empty lines like git does
        old_lines = old_code.split('\n') if old_code else []
        new_lines = new_code.split('\n') if new_code else []
        
        # Use difflib for accurate line-by-line comparison (same as git)
        import difflib
        matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
        
        added = 0
        removed = 0
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'replace':
                # Lines that changed count as both added and removed
                removed += (i2 - i1)
                added += (j2 - j1)
            elif tag == 'delete':
                removed += (i2 - i1)
            elif tag == 'insert':
                added += (j2 - j1)
            # 'equal' means no change, so we skip it
        
        return added, removed
    
    @staticmethod
    def extract_key_changes(old_code: str, new_code: str, explanation: str) -> List[str]:
        """
        Extract key changes from code comparison.
        
        Args:
            old_code: Original code
            new_code: Refactored code
            explanation: AI explanation
            
        Returns:
            List of key change descriptions
        """
        key_changes = []
        
        old_lines = set(old_code.split('\n'))
        new_lines = set(new_code.split('\n'))
        
        # Find significantly changed lines
        added_lines = new_lines - old_lines
        removed_lines = old_lines - new_lines
        
        # Look for specific patterns
        patterns = {
            'async/await': ('async', 'await'),
            'arrow functions': ('=>',),
            'const/let': ('const ', 'let '),
            'template literals': ('`',),
            'destructuring': ('{', '}'),
            'spread operator': ('...',),
            'type annotations': (': string', ': number', ': boolean'),
        }
        
        for pattern_name, keywords in patterns.items():
            if any(keyword in new_code for keyword in keywords) and \
               not any(keyword in old_code for keyword in keywords):
                key_changes.append(f"Added {pattern_name}")
        
        # Add from explanation
        sections = ChangelogFormatter.parse_explanation(explanation)
        if sections['modernization']:
            key_changes.extend(sections['modernization'][:2])  # Top 2
        if sections['deprecations']:
            key_changes.extend(sections['deprecations'][:1])   # Top 1
        
        return key_changes[:5]  # Limit to 5 key changes
    
    @staticmethod
    def calculate_diff_stats(old_code: str, new_code: str) -> tuple[int, int]:
        """
        Calculate lines added and removed.
        
        Args:
            old_code: Original code
            new_code: Refactored code
            
        Returns:
            Tuple of (lines_added, lines_removed)
        """
        # Defensive: handle None or non-string inputs
        if not isinstance(old_code, str):
            old_code = str(old_code) if old_code else ''
        if not isinstance(new_code, str):
            new_code = str(new_code) if new_code else ''
        
        try:
            old_lines = old_code.split('\n')
            new_lines = new_code.split('\n')
            
            old_set = set(line.strip() for line in old_lines if line.strip())
            new_set = set(line.strip() for line in new_lines if line.strip())
            
            lines_added = len(new_set - old_set)
            lines_removed = len(old_set - new_set)
            
            return lines_added, lines_removed
        except Exception as e:
            # Fallback to simple line count on error
            print(f"Warning: Error calculating diff stats: {e}")
            return 0, 0
    
    @staticmethod
    def format_file_change(
        file_path: str,
        old_code: str,
        new_code: str,
        explanation: str,
        confidence_score: int,
        language: str
    ) -> FileChange:
        """
        Format a single file change into structured changelog entry.
        
        Args:
            file_path: Path to the file
            old_code: Original code
            new_code: Refactored code
            explanation: AI explanation
            confidence_score: Confidence score (0-100)
            language: Programming language
            
        Returns:
            FileChange object
        """
        lines_added, lines_removed = ChangelogFormatter.calculate_diff_stats(old_code, new_code)
        key_changes = ChangelogFormatter.extract_key_changes(old_code, new_code, explanation)
        
        return FileChange(
            file_path=file_path,
            old_code=old_code,
            new_code=new_code,
            explanation=explanation,
            confidence_score=confidence_score,
            language=language,
            lines_added=lines_added,
            lines_removed=lines_removed,
            key_changes=key_changes
        )
    
    @staticmethod
    def generate_markdown_changelog(file_changes: List[FileChange]) -> str:
        """
        Generate a comprehensive markdown changelog.
        
        Args:
            file_changes: List of FileChange objects
            
        Returns:
            Markdown formatted changelog
        """
        # Calculate totals
        total_files = len(file_changes)
        total_added = sum(fc.lines_added for fc in file_changes)
        total_removed = sum(fc.lines_removed for fc in file_changes)
        avg_confidence = sum(fc.confidence_score for fc in file_changes) / total_files if total_files > 0 else 0
        
        # Group by language
        languages = {}
        for fc in file_changes:
            if fc.language not in languages:
                languages[fc.language] = []
            languages[fc.language].append(fc)
        
        # Build markdown
        md = []
        md.append("# 🤖 AI-Powered Code Modernization Report\n")
        md.append("## Summary\n")
        md.append(f"- **Files Updated**: {total_files}")
        md.append(f"- **Lines Added**: +{total_added}")
        md.append(f"- **Lines Removed**: -{total_removed}")
        md.append(f"- **Average Confidence**: {avg_confidence:.1f}/100")
        md.append(f"- **Languages**: {', '.join(languages.keys())}\n")
        
        md.append("---\n")
        md.append("## File-by-File Changes\n")
        
        for i, fc in enumerate(file_changes, 1):
            md.append(f"### {i}. `{fc.file_path}`\n")
            
            # Confidence badge
            if fc.confidence_score >= 80:
                badge = "🟢 HIGH CONFIDENCE"
            elif fc.confidence_score >= 60:
                badge = "🟡 MEDIUM CONFIDENCE"
            else:
                badge = "🔴 NEEDS REVIEW"
            
            md.append(f"**{badge}** - Score: {fc.confidence_score}/100\n")
            md.append(f"**Language**: {fc.language.upper()}\n")
            md.append(f"**Changes**: +{fc.lines_added} / -{fc.lines_removed} lines\n")
            
            # Key changes
            if fc.key_changes:
                md.append("\n**Key Modernizations**:")
                for change in fc.key_changes:
                    md.append(f"- {change}")
                md.append("")
            
            # AI Explanation
            md.append("**AI Reasoning**:")
            md.append(f"> {fc.explanation}\n")
            
            # Categorized changes
            sections = ChangelogFormatter.parse_explanation(fc.explanation)
            
            if sections['deprecations']:
                md.append("**Deprecated Syntax Removed**:")
                for item in sections['deprecations']:
                    md.append(f"- {item}")
                md.append("")
            
            if sections['api_updates']:
                md.append("**API Updates**:")
                for item in sections['api_updates']:
                    md.append(f"- {item}")
                md.append("")
            
            md.append("---\n")
        
        # Footer
        md.append("## How to Review\n")
        md.append("1. **High Confidence (🟢)**: Safe to merge after quick review")
        md.append("2. **Medium Confidence (🟡)**: Review changes carefully")
        md.append("3. **Needs Review (🔴)**: Requires thorough testing\n")
        
        md.append("---\n")
        md.append("*Generated by [Dependify 2.0](https://github.com/kshitizz36/Dependify2.0) - AI-Powered Code Modernization*")
        
        return '\n'.join(md)
    
    @staticmethod
    def generate_json_changelog(file_changes: List[FileChange]) -> str:
        """
        Generate a JSON changelog for programmatic use.
        
        Args:
            file_changes: List of FileChange objects
            
        Returns:
            JSON formatted changelog
        """
        changelog = {
            'summary': {
                'total_files': len(file_changes),
                'total_lines_added': sum(fc.lines_added for fc in file_changes),
                'total_lines_removed': sum(fc.lines_removed for fc in file_changes),
                'average_confidence': sum(fc.confidence_score for fc in file_changes) / len(file_changes) if file_changes else 0,
            },
            'files': [
                {
                    'path': fc.file_path,
                    'language': fc.language,
                    'confidence_score': fc.confidence_score,
                    'lines_added': fc.lines_added,
                    'lines_removed': fc.lines_removed,
                    'key_changes': fc.key_changes,
                    'explanation': fc.explanation,
                    'categorized_changes': ChangelogFormatter.parse_explanation(fc.explanation)
                }
                for fc in file_changes
            ]
        }
        
        return json.dumps(changelog, indent=2)
    
    @staticmethod
    def generate_pr_description(file_changes: List[FileChange]) -> str:
        """
        Generate a detailed, professional PR description similar to GitButler style.
        Shows what changed, why it changed, and the impact.
        
        Args:
            file_changes: List of FileChange objects
            
        Returns:
            Detailed PR description with file-by-file breakdown
        """
        total_files = len(file_changes)
        
        # Calculate accurate diff stats
        total_added = 0
        total_removed = 0
        for fc in file_changes:
            added, removed = ChangelogFormatter.calculate_diff_stats(fc.old_code, fc.new_code)
            total_added += added
            total_removed += removed
        
        pr_desc = []
        pr_desc.append("## 🤖 Automated Code Modernization\n")
        pr_desc.append("This pull request modernizes outdated code patterns and updates deprecated syntax to current best practices.\n")
        
        # Summary section
        pr_desc.append("### 📝 Summary\n")
        pr_desc.append(f"Updated **{total_files} file{'s' if total_files != 1 else ''}** with modern syntax and improved code quality.\n")
        
        # File-by-file breakdown
        pr_desc.append("### 📁 Changes by File\n")
        for i, fc in enumerate(file_changes, 1):
            added, removed = ChangelogFormatter.calculate_diff_stats(fc.old_code, fc.new_code)
            
            pr_desc.append(f"#### {i}. `{fc.file_path}`\n")
            
            # Show what changed
            if fc.key_changes and len(fc.key_changes) > 0:
                pr_desc.append("**What changed:**")
                for change in fc.key_changes[:5]:  # Top 5 changes per file
                    pr_desc.append(f"- {change}")
                pr_desc.append("")
            
            # Show why it changed (AI explanation)
            if fc.explanation and fc.explanation.strip():
                pr_desc.append("**Why:**")
                # Clean up the explanation
                explanation_lines = fc.explanation.strip().split('. ')
                for line in explanation_lines[:3]:  # First 3 sentences
                    if line.strip():
                        pr_desc.append(f"> {line.strip()}{'.' if not line.endswith('.') else ''}")
                pr_desc.append("")
            
            pr_desc.append("---\n")
        
        # Footer with context
        pr_desc.append("### ✅ Review Checklist\n")
        pr_desc.append("- [ ] Review the changes in each file")
        pr_desc.append("- [ ] Verify the modernized syntax is correct")
        pr_desc.append("- [ ] Run tests to ensure no breaking changes")
        pr_desc.append("- [ ] Check for any deprecated API usage\n")
        
        pr_desc.append("### 🤖 About This PR\n")
        pr_desc.append("This PR was automatically generated by [Dependify](https://github.com/kshitizz36/Dependify2.0), ")
        pr_desc.append("an AI-powered tool that modernizes code by detecting outdated patterns and applying current best practices.\n")
        pr_desc.append("All changes are transparent and can be reviewed in the **Files changed** tab above.\n")
        
        return '\n'.join(pr_desc)


# Example usage
if __name__ == "__main__":
    # Test data
    test_changes = [
        FileChange(
            file_path="src/utils/api.js",
            old_code="function fetchData(url) {\n  return fetch(url).then(r => r.json());\n}",
            new_code="async function fetchData(url) {\n  const response = await fetch(url);\n  return response.json();\n}",
            explanation="Updated to use modern async/await syntax instead of promise chaining. This improves readability and makes error handling cleaner. The function now follows current JavaScript best practices.",
            confidence_score=95,
            language="javascript",
            lines_added=3,
            lines_removed=1,
            key_changes=["Added async/await", "Improved error handling patterns"]
        ),
        FileChange(
            file_path="src/components/Header.tsx",
            old_code="import React from 'react';\nclass Header extends React.Component {",
            new_code="import React, { FC } from 'react';\nconst Header: FC = () => {",
            explanation="Converted from class component to modern functional component with TypeScript. Functional components are the current React best practice and enable better use of hooks.",
            confidence_score=88,
            language="typescript",
            lines_added=2,
            lines_removed=2,
            key_changes=["Converted to functional component", "Added TypeScript types"]
        )
    ]
    
    # Generate changelog
    formatter = ChangelogFormatter()
    markdown = formatter.generate_markdown_changelog(test_changes)
    print(markdown)
    print("\n" + "="*80 + "\n")
    
    # Generate PR description
    pr_desc = formatter.generate_pr_description(test_changes)
    print(pr_desc)
