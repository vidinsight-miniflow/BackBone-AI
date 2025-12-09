"""
Tools for code quality validation.
"""

import ast
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

from app.core.logger import get_logger
from app.schemas.validator_schema import ValidationIssue, ValidationSeverityLevel

logger = get_logger(__name__)


class PythonSyntaxChecker:
    """
    Tool for checking Python syntax using AST parsing.
    """

    def __init__(self):
        self.name = "python_syntax_checker"

    def check(self, file_path: str, code: str) -> List[ValidationIssue]:
        """
        Check Python syntax.

        Args:
            file_path: Path to the file being checked
            code: Python code to check

        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []

        try:
            # Try to parse the code
            ast.parse(code)
            logger.debug(f"Syntax check passed: {file_path}")

        except SyntaxError as e:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverityLevel.ERROR,
                    category="syntax",
                    message=f"Syntax error: {e.msg}",
                    file_path=file_path,
                    line_number=e.lineno,
                    column=e.offset,
                    code="E999",
                    suggestion="Fix the syntax error according to Python grammar",
                )
            )

        except Exception as e:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverityLevel.ERROR,
                    category="syntax",
                    message=f"Failed to parse: {str(e)}",
                    file_path=file_path,
                    code="E999",
                )
            )

        return issues


class TypeChecker:
    """
    Tool for type checking using mypy.
    """

    def __init__(self):
        self.name = "mypy_type_checker"

    def check(self, file_path: str, code: str) -> List[ValidationIssue]:
        """
        Check types using mypy.

        Args:
            file_path: Path to the file being checked
            code: Python code to check

        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []

        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name

            # Run mypy
            result = subprocess.run(
                [
                    "mypy",
                    "--no-error-summary",
                    "--show-column-numbers",
                    "--no-color-output",
                    tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse mypy output
            if result.returncode != 0:
                for line in result.stdout.splitlines():
                    # Parse mypy output format: file.py:10:5: error: message
                    match = re.match(
                        r"(.+):(\d+):(\d+): (error|warning|note): (.+)", line
                    )
                    if match:
                        _, line_num, col, severity, message = match.groups()
                        issues.append(
                            ValidationIssue(
                                severity=(
                                    ValidationSeverityLevel.ERROR
                                    if severity == "error"
                                    else ValidationSeverityLevel.WARNING
                                    if severity == "warning"
                                    else ValidationSeverityLevel.INFO
                                ),
                                category="types",
                                message=message.strip(),
                                file_path=file_path,
                                line_number=int(line_num),
                                column=int(col),
                                code="mypy",
                            )
                        )

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

        except FileNotFoundError:
            logger.warning("mypy not found, skipping type checking")
        except subprocess.TimeoutExpired:
            logger.warning(f"mypy timed out for {file_path}")
        except Exception as e:
            logger.error(f"Type checking failed: {e}")

        return issues


class CodeLinter:
    """
    Tool for linting code using ruff.
    """

    def __init__(self):
        self.name = "ruff_linter"

    def check(self, file_path: str, code: str) -> List[ValidationIssue]:
        """
        Lint code using ruff.

        Args:
            file_path: Path to the file being checked
            code: Python code to check

        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []

        try:
            # Write code to temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as tmp_file:
                tmp_file.write(code)
                tmp_path = tmp_file.name

            # Run ruff
            result = subprocess.run(
                [
                    "ruff",
                    "check",
                    "--output-format=json",
                    tmp_path,
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Parse ruff JSON output
            if result.stdout:
                import json

                ruff_results = json.loads(result.stdout)
                for item in ruff_results:
                    severity = (
                        ValidationSeverityLevel.ERROR
                        if item.get("severity") == "error"
                        else ValidationSeverityLevel.WARNING
                    )

                    issues.append(
                        ValidationIssue(
                            severity=severity,
                            category="style",
                            message=item.get("message", "Style issue"),
                            file_path=file_path,
                            line_number=item.get("location", {}).get("row"),
                            column=item.get("location", {}).get("column"),
                            code=item.get("code"),
                            suggestion=item.get("fix", {}).get("message"),
                        )
                    )

            # Clean up
            Path(tmp_path).unlink(missing_ok=True)

        except FileNotFoundError:
            logger.warning("ruff not found, skipping linting")
        except subprocess.TimeoutExpired:
            logger.warning(f"ruff timed out for {file_path}")
        except Exception as e:
            logger.error(f"Linting failed: {e}")

        return issues


class SecurityScanner:
    """
    Tool for basic security scanning.
    """

    def __init__(self):
        self.name = "security_scanner"

        # Common security patterns to check
        self.patterns = [
            (
                r"eval\s*\(",
                "Use of eval() is dangerous",
                "Avoid eval(), use ast.literal_eval() or json.loads() instead",
            ),
            (
                r"exec\s*\(",
                "Use of exec() is dangerous",
                "Avoid exec(), refactor to use safer alternatives",
            ),
            (
                r"__import__\s*\(",
                "Dynamic imports can be dangerous",
                "Use static imports when possible",
            ),
            (
                r"pickle\.loads?\s*\(",
                "Pickle can execute arbitrary code",
                "Use json or safer serialization formats",
            ),
            (
                r"shell\s*=\s*True",
                "Shell injection vulnerability",
                "Set shell=False in subprocess calls",
            ),
            (
                r"password\s*=\s*['\"].*['\"]",
                "Hardcoded password detected",
                "Use environment variables or secrets management",
            ),
            (
                r"api[_-]?key\s*=\s*['\"].*['\"]",
                "Hardcoded API key detected",
                "Use environment variables or secrets management",
            ),
        ]

    def check(self, file_path: str, code: str) -> List[ValidationIssue]:
        """
        Scan for security issues.

        Args:
            file_path: Path to the file being checked
            code: Python code to check

        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []

        lines = code.splitlines()
        for line_num, line in enumerate(lines, start=1):
            for pattern, message, suggestion in self.patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverityLevel.WARNING,
                            category="security",
                            message=message,
                            file_path=file_path,
                            line_number=line_num,
                            code="SEC",
                            suggestion=suggestion,
                        )
                    )

        return issues


class CodeMetricsAnalyzer:
    """
    Tool for analyzing code metrics.
    """

    def __init__(self):
        self.name = "code_metrics_analyzer"

    def analyze(self, file_path: str, code: str) -> Dict[str, Any]:
        """
        Analyze code metrics.

        Args:
            file_path: Path to the file
            code: Python code to analyze

        Returns:
            Dictionary of metrics
        """
        metrics: Dict[str, Any] = {
            "lines_of_code": 0,
            "blank_lines": 0,
            "comment_lines": 0,
            "classes": 0,
            "functions": 0,
            "complexity": 0,
        }

        try:
            lines = code.splitlines()
            metrics["lines_of_code"] = len(lines)

            # Count blank and comment lines
            for line in lines:
                stripped = line.strip()
                if not stripped:
                    metrics["blank_lines"] += 1
                elif stripped.startswith("#"):
                    metrics["comment_lines"] += 1

            # Parse AST for structure metrics
            tree = ast.parse(code)

            # Count classes and functions
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    metrics["classes"] += 1
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    metrics["functions"] += 1

            # Simple complexity metric (based on control flow statements)
            complexity = 1  # Base complexity
            for node in ast.walk(tree):
                if isinstance(
                    node,
                    (
                        ast.If,
                        ast.For,
                        ast.While,
                        ast.ExceptHandler,
                        ast.With,
                        ast.Assert,
                    ),
                ):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1

            metrics["complexity"] = complexity

        except Exception as e:
            logger.warning(f"Failed to analyze metrics for {file_path}: {e}")

        return metrics


class ImportAnalyzer:
    """
    Tool for analyzing imports and dependencies.
    """

    def __init__(self):
        self.name = "import_analyzer"

    def check(self, file_path: str, code: str) -> List[ValidationIssue]:
        """
        Check imports for issues.

        Args:
            file_path: Path to the file
            code: Python code to check

        Returns:
            List of validation issues
        """
        issues: List[ValidationIssue] = []

        try:
            tree = ast.parse(code)

            # Track imports
            imports = set()
            import_locations = {}

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        if name in imports:
                            issues.append(
                                ValidationIssue(
                                    severity=ValidationSeverityLevel.INFO,
                                    category="imports",
                                    message=f"Duplicate import: {name}",
                                    file_path=file_path,
                                    line_number=node.lineno,
                                    code="I001",
                                    suggestion="Remove duplicate import",
                                )
                            )
                        imports.add(name)
                        import_locations[name] = node.lineno

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            full_name = f"{node.module}.{alias.name}"
                            imports.add(full_name)

        except Exception as e:
            logger.warning(f"Import analysis failed for {file_path}: {e}")

        return issues
