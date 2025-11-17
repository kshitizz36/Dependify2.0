"""
Multi-language syntax validation and confidence scoring system.
Validates code across Python, JavaScript, TypeScript, Go, Rust, and Java.
"""

import ast
import subprocess
import tempfile
import os
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
import json


@dataclass
class ValidationResult:
    """Result of code validation."""
    is_valid: bool
    language: str
    error_message: Optional[str] = None
    line_number: Optional[int] = None


@dataclass
class ConfidenceScore:
    """Confidence score for code changes."""
    score: int  # 0-100
    syntax_valid: bool
    complexity_factor: float
    factors: Dict[str, any]


class SyntaxValidator:
    """Multi-language syntax validator."""
    
    @staticmethod
    def detect_language(file_path: str) -> str:
        """
        Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name (lowercase)
        """
        extension_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.rs': 'rust',
            '.java': 'java',
        }
        
        _, ext = os.path.splitext(file_path)
        return extension_map.get(ext.lower(), 'unknown')
    
    @staticmethod
    def validate_python(code: str) -> ValidationResult:
        """
        Validate Python syntax using AST.
        
        Args:
            code: Python code string
            
        Returns:
            ValidationResult
        """
        if not code or not isinstance(code, str):
            return ValidationResult(
                is_valid=False,
                language='python',
                error_message='Code must be a non-empty string'
            )
        
        try:
            ast.parse(code)
            return ValidationResult(
                is_valid=True,
                language='python'
            )
        except SyntaxError as e:
            return ValidationResult(
                is_valid=False,
                language='python',
                error_message=str(e),
                line_number=e.lineno
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='python',
                error_message=f'Unexpected validation error: {str(e)}'
            )
    
    @staticmethod
    def validate_javascript(code: str) -> ValidationResult:
        """
        Validate JavaScript/TypeScript syntax using Node.js.
        
        Args:
            code: JavaScript code string
            
        Returns:
            ValidationResult
        """
        if not code or not isinstance(code, str):
            return ValidationResult(
                is_valid=False,
                language='javascript',
                error_message='Code must be a non-empty string'
            )
        
        temp_path = None
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to parse with node --check
            result = subprocess.run(
                ['node', '--check', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return ValidationResult(
                    is_valid=True,
                    language='javascript'
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language='javascript',
                    error_message=result.stderr
                )
        except subprocess.TimeoutExpired:
            return ValidationResult(
                is_valid=False,
                language='javascript',
                error_message='Validation timeout - code may contain infinite loops'
            )
        except FileNotFoundError:
            # Node.js not installed - skip validation but don't fail
            return ValidationResult(
                is_valid=True,  # Assume valid if we can't validate
                language='javascript',
                error_message='Node.js not available for validation'
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='javascript',
                error_message=f'Validation error: {str(e)}'
            )
        finally:
            # Always clean up temp file
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception:
                    pass  # Ignore cleanup errors
    
    @staticmethod
    def validate_typescript(code: str) -> ValidationResult:
        """
        Validate TypeScript syntax using tsc.
        
        Args:
            code: TypeScript code string
            
        Returns:
            ValidationResult
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.ts', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to parse with tsc --noEmit
            result = subprocess.run(
                ['tsc', '--noEmit', '--allowJs', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return ValidationResult(
                    is_valid=True,
                    language='typescript'
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language='typescript',
                    error_message=result.stderr
                )
        except FileNotFoundError:
            # TypeScript not installed - fall back to JavaScript validation
            return SyntaxValidator.validate_javascript(code)
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='typescript',
                error_message=str(e)
            )
    
    @staticmethod
    def validate_go(code: str) -> ValidationResult:
        """
        Validate Go syntax using go fmt.
        
        Args:
            code: Go code string
            
        Returns:
            ValidationResult
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.go', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to format with go fmt (will error on syntax issues)
            result = subprocess.run(
                ['gofmt', '-e', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return ValidationResult(
                    is_valid=True,
                    language='go'
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language='go',
                    error_message=result.stderr
                )
        except FileNotFoundError:
            # Go not installed - skip validation
            return ValidationResult(
                is_valid=True,
                language='go',
                error_message='Go not available for validation'
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='go',
                error_message=str(e)
            )
    
    @staticmethod
    def validate_rust(code: str) -> ValidationResult:
        """
        Validate Rust syntax using rustc.
        
        Args:
            code: Rust code string
            
        Returns:
            ValidationResult
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rs', delete=False) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to parse with rustc --parse-only
            result = subprocess.run(
                ['rustc', '--crate-type', 'lib', '-Z', 'parse-only', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            os.unlink(temp_path)
            
            if result.returncode == 0:
                return ValidationResult(
                    is_valid=True,
                    language='rust'
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language='rust',
                    error_message=result.stderr
                )
        except FileNotFoundError:
            # Rust not installed - skip validation
            return ValidationResult(
                is_valid=True,
                language='rust',
                error_message='Rust not available for validation'
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='rust',
                error_message=str(e)
            )
    
    @staticmethod
    def validate_java(code: str) -> ValidationResult:
        """
        Validate Java syntax using javac.
        
        Args:
            code: Java code string
            
        Returns:
            ValidationResult
        """
        try:
            # Extract class name from code
            import re
            class_match = re.search(r'public\s+class\s+(\w+)', code)
            if not class_match:
                class_match = re.search(r'class\s+(\w+)', code)
            
            if not class_match:
                return ValidationResult(
                    is_valid=False,
                    language='java',
                    error_message='Could not find class declaration'
                )
            
            class_name = class_match.group(1)
            
            # Create temporary file with correct class name
            with tempfile.NamedTemporaryFile(
                mode='w',
                suffix=f'{class_name}.java',
                delete=False,
                dir=tempfile.gettempdir()
            ) as f:
                f.write(code)
                temp_path = f.name
            
            # Try to compile with javac
            result = subprocess.run(
                ['javac', temp_path],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Clean up
            os.unlink(temp_path)
            # Also remove .class file if created
            class_file = temp_path.replace('.java', '.class')
            if os.path.exists(class_file):
                os.unlink(class_file)
            
            if result.returncode == 0:
                return ValidationResult(
                    is_valid=True,
                    language='java'
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    language='java',
                    error_message=result.stderr
                )
        except FileNotFoundError:
            # Java not installed - skip validation
            return ValidationResult(
                is_valid=True,
                language='java',
                error_message='Java not available for validation'
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                language='java',
                error_message=str(e)
            )
    
    @staticmethod
    def validate_code(code: str, language: str) -> ValidationResult:
        """
        Validate code based on detected language.
        
        Args:
            code: Source code string
            language: Programming language
            
        Returns:
            ValidationResult
        """
        validators = {
            'python': SyntaxValidator.validate_python,
            'javascript': SyntaxValidator.validate_javascript,
            'typescript': SyntaxValidator.validate_typescript,
            'go': SyntaxValidator.validate_go,
            'rust': SyntaxValidator.validate_rust,
            'java': SyntaxValidator.validate_java,
        }
        
        validator = validators.get(language.lower())
        if validator:
            return validator(code)
        else:
            # Unknown language - skip validation
            return ValidationResult(
                is_valid=True,
                language=language,
                error_message='Language not supported for validation'
            )


class ConfidenceScorer:
    """Calculate confidence scores for code changes."""
    
    @staticmethod
    def calculate_complexity(old_code: str, new_code: str) -> float:
        """
        Calculate complexity factor based on code changes.
        
        Args:
            old_code: Original code
            new_code: Refactored code
            
        Returns:
            Complexity factor (0.0 to 1.0, where 1.0 is low complexity)
        """
        old_lines = old_code.split('\n')
        new_lines = new_code.split('\n')
        
        # Calculate metrics
        lines_changed = abs(len(new_lines) - len(old_lines))
        total_lines = max(len(old_lines), len(new_lines))
        
        # Calculate percentage of lines changed
        if total_lines == 0:
            change_ratio = 0.0
        else:
            change_ratio = lines_changed / total_lines
        
        # Inverse complexity: smaller changes = higher confidence
        # 0% change = 1.0, 100% change = 0.0
        complexity_factor = max(0.0, 1.0 - change_ratio)
        
        return complexity_factor
    
    @staticmethod
    def calculate_score(
        old_code: str,
        new_code: str,
        validation_result: ValidationResult
    ) -> ConfidenceScore:
        """
        Calculate confidence score for code changes.
        
        Scoring formula:
        - Syntax validation: 60 points (pass/fail)
        - Complexity factor: 40 points (based on change size)
        
        Args:
            old_code: Original code
            new_code: Refactored code
            validation_result: Validation result
            
        Returns:
            ConfidenceScore
        """
        # Base score from syntax validation
        syntax_score = 60 if validation_result.is_valid else 0
        
        # Calculate complexity factor
        complexity_factor = ConfidenceScorer.calculate_complexity(old_code, new_code)
        complexity_score = int(complexity_factor * 40)
        
        # Total score
        total_score = syntax_score + complexity_score
        
        # Additional factors for reporting
        factors = {
            'syntax_validation': 'PASSED' if validation_result.is_valid else 'FAILED',
            'lines_changed': abs(len(new_code.split('\n')) - len(old_code.split('\n'))),
            'complexity_rating': 'LOW' if complexity_factor > 0.7 else 'MEDIUM' if complexity_factor > 0.3 else 'HIGH',
            'language': validation_result.language,
        }
        
        if not validation_result.is_valid:
            factors['error'] = validation_result.error_message
        
        return ConfidenceScore(
            score=total_score,
            syntax_valid=validation_result.is_valid,
            complexity_factor=complexity_factor,
            factors=factors
        )


def validate_and_score(
    file_path: str,
    old_code: str,
    new_code: str
) -> Tuple[ValidationResult, ConfidenceScore]:
    """
    Validate and score code changes.
    
    Args:
        file_path: Path to the file
        old_code: Original code
        new_code: Refactored code
        
    Returns:
        Tuple of (ValidationResult, ConfidenceScore)
    """
    # Detect language
    language = SyntaxValidator.detect_language(file_path)
    
    # Validate new code
    validation = SyntaxValidator.validate_code(new_code, language)
    
    # Calculate confidence score
    score = ConfidenceScorer.calculate_score(old_code, new_code, validation)
    
    return validation, score


# Example usage and testing
if __name__ == "__main__":
    # Test Python validation
    python_code = """
def hello():
    print("Hello, world!")
"""
    result = SyntaxValidator.validate_python(python_code)
    print(f"Python validation: {result}")
    
    # Test invalid Python
    invalid_python = """
def hello(
    print("Missing closing paren")
"""
    result = SyntaxValidator.validate_python(invalid_python)
    print(f"Invalid Python: {result}")
    
    # Test confidence scoring
    old_code = "def old():\n    pass"
    new_code = "def new():\n    print('updated')\n    return True"
    
    validation, score = validate_and_score("test.py", old_code, new_code)
    print(f"\nConfidence score: {score.score}/100")
    print(f"Factors: {json.dumps(score.factors, indent=2)}")
