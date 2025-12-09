"""
Tests for the Validator Agent.
"""

import pytest

from app.agents.validator_agent import ValidatorAgent
from app.schemas.validator_schema import ValidationSeverityLevel


@pytest.fixture
def valid_code():
    """Valid Python code sample."""
    return """
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
"""


@pytest.fixture
def code_with_syntax_error():
    """Code with syntax error."""
    return """
def broken_function():
    return "missing quote
"""


@pytest.fixture
def code_with_security_issues():
    """Code with security issues."""
    return """
import subprocess

def dangerous_function(user_input):
    # Security issue: shell=True
    subprocess.run(user_input, shell=True)

    # Security issue: eval
    result = eval(user_input)

    # Security issue: hardcoded password
    password = "supersecret123"

    return result
"""


@pytest.fixture
def code_with_style_issues():
    """Code with style issues."""
    return """
import sys
import os
import re
import json  # Unused import

def badly_formatted_function(  x,y,z  ):
    if x==1:
        if y==2:
            if z==3:
                return True
    return False

class   MyClass:
    pass
"""


@pytest.fixture
def complex_code():
    """Code with high complexity."""
    return """
def complex_function(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    if e:
                        for i in range(10):
                            if i % 2:
                                while i > 0:
                                    if i == 5:
                                        return True
                                    i -= 1
    return False
"""


class TestValidatorAgent:
    """Test Validator Agent."""

    @pytest.mark.asyncio
    async def test_validator_initialization(self):
        """Test validator can be initialized."""
        validator = ValidatorAgent(
            enable_type_checking=True,
            enable_linting=True,
            enable_security_scan=True,
        )

        assert validator is not None
        assert validator.syntax_checker is not None
        assert validator.type_checker is not None
        assert validator.linter is not None
        assert validator.security_scanner is not None

    @pytest.mark.asyncio
    async def test_validate_valid_code(self, valid_code):
        """Test validation of valid code."""
        validator = ValidatorAgent(
            enable_type_checking=False,  # Disable mypy for simpler test
            enable_linting=False,  # Disable ruff for simpler test
            enable_security_scan=False,
        )

        result = await validator.execute({
            "generated_files": {
                "models/user.py": valid_code
            }
        })

        assert result["overall_passed"] is True
        assert result["status"] in ["passed", "passed_with_warnings"]
        assert result["metrics"]["total_files"] == 1

    @pytest.mark.asyncio
    async def test_validate_syntax_error(self, code_with_syntax_error):
        """Test validation catches syntax errors."""
        validator = ValidatorAgent()

        result = await validator.execute({
            "generated_files": {
                "models/broken.py": code_with_syntax_error
            }
        })

        assert result["overall_passed"] is False
        assert result["status"] == "failed"
        assert len(result["errors"]) > 0

        # Check that error is a syntax error
        syntax_errors = [
            e for e in result["errors"]
            if e["category"] == "syntax"
        ]
        assert len(syntax_errors) > 0

    @pytest.mark.asyncio
    async def test_validate_security_issues(self, code_with_security_issues):
        """Test validation catches security issues."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=True,
        )

        result = await validator.execute({
            "generated_files": {
                "models/dangerous.py": code_with_security_issues
            }
        })

        # Should pass syntax but have warnings
        assert len(result["warnings"]) > 0

        # Check for specific security warnings
        security_warnings = [
            w for w in result["warnings"]
            if w["category"] == "security"
        ]
        assert len(security_warnings) >= 2  # shell=True and eval

    @pytest.mark.asyncio
    async def test_strict_mode_treats_warnings_as_errors(self, code_with_security_issues):
        """Test strict mode treats warnings as errors."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=True,
            strict_mode=True,
        )

        result = await validator.execute({
            "generated_files": {
                "models/dangerous.py": code_with_security_issues
            }
        })

        # In strict mode, warnings should cause failure
        assert result["overall_passed"] is False
        assert result["status"] == "failed"

    @pytest.mark.asyncio
    async def test_validate_multiple_files(self, valid_code, code_with_syntax_error):
        """Test validation of multiple files."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
        )

        result = await validator.execute({
            "generated_files": {
                "models/user.py": valid_code,
                "models/broken.py": code_with_syntax_error,
            }
        })

        assert result["metrics"]["total_files"] == 2
        assert result["metrics"]["files_with_issues"] >= 1
        assert result["overall_passed"] is False

    @pytest.mark.asyncio
    async def test_code_metrics_calculation(self, valid_code):
        """Test code metrics are calculated."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=False,
        )

        result = await validator.execute({
            "generated_files": {
                "models/user.py": valid_code
            }
        })

        # Check metrics exist
        assert "metrics" in result
        metrics = result["metrics"]
        assert metrics["total_lines"] > 0
        assert metrics["total_files"] == 1
        assert "maintainability_score" in metrics

        # Check file-level metrics
        file_results = result["file_results"]
        assert len(file_results) == 1
        file_metrics = file_results[0]["metrics"]
        assert file_metrics["lines_of_code"] > 0
        assert file_metrics["classes"] > 0  # Should find Base and User classes

    @pytest.mark.asyncio
    async def test_high_complexity_warning(self, complex_code):
        """Test high complexity triggers warning."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=False,
        )

        result = await validator.execute({
            "generated_files": {
                "models/complex.py": complex_code
            }
        })

        # Should have complexity warning
        complexity_warnings = [
            w for w in result["warnings"]
            if w["category"] == "complexity"
        ]
        assert len(complexity_warnings) > 0

    @pytest.mark.asyncio
    async def test_import_analysis(self):
        """Test import analysis detects issues."""
        code_with_duplicate_imports = """
import os
import sys
import os  # Duplicate

def test():
    pass
"""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=False,
        )

        result = await validator.execute({
            "generated_files": {
                "test.py": code_with_duplicate_imports
            }
        })

        # Should detect duplicate import
        import_issues = [
            i for i in result["suggestions"]
            if i["category"] == "imports"
        ]
        assert len(import_issues) > 0

    @pytest.mark.asyncio
    async def test_validation_skips_other_checks_on_syntax_error(self, code_with_syntax_error):
        """Test that other checks are skipped if syntax error exists."""
        validator = ValidatorAgent(
            enable_type_checking=True,
            enable_linting=True,
            enable_security_scan=True,
        )

        result = await validator.execute({
            "generated_files": {
                "broken.py": code_with_syntax_error
            }
        })

        # Should only have syntax errors, no other issues
        errors = result["errors"]
        assert all(e["category"] == "syntax" for e in errors)


class TestValidationTools:
    """Test individual validation tools."""

    def test_syntax_checker(self, valid_code, code_with_syntax_error):
        """Test syntax checker."""
        from app.tools.validation_tools import PythonSyntaxChecker

        checker = PythonSyntaxChecker()

        # Valid code
        issues = checker.check("test.py", valid_code)
        assert len(issues) == 0

        # Invalid code
        issues = checker.check("test.py", code_with_syntax_error)
        assert len(issues) > 0
        assert issues[0].severity == ValidationSeverityLevel.ERROR

    def test_security_scanner(self, code_with_security_issues):
        """Test security scanner."""
        from app.tools.validation_tools import SecurityScanner

        scanner = SecurityScanner()

        issues = scanner.check("test.py", code_with_security_issues)
        assert len(issues) >= 3  # shell=True, eval, hardcoded password

        # Check specific patterns
        categories = [i.message for i in issues]
        assert any("shell" in msg.lower() for msg in categories)
        assert any("eval" in msg.lower() for msg in categories)
        assert any("password" in msg.lower() for msg in categories)

    def test_metrics_analyzer(self, valid_code):
        """Test code metrics analyzer."""
        from app.tools.validation_tools import CodeMetricsAnalyzer

        analyzer = CodeMetricsAnalyzer()

        metrics = analyzer.analyze("test.py", valid_code)

        assert metrics["lines_of_code"] > 0
        assert metrics["classes"] == 2  # Base and User
        assert metrics["functions"] == 1  # __repr__
        assert metrics["complexity"] > 0

    def test_import_analyzer(self):
        """Test import analyzer."""
        from app.tools.validation_tools import ImportAnalyzer

        analyzer = ImportAnalyzer()

        code_with_issues = """
import os
import sys
import os  # Duplicate

from typing import List
from typing import Dict
"""

        issues = analyzer.check("test.py", code_with_issues)

        # Should detect duplicate import
        duplicate_issues = [i for i in issues if "Duplicate" in i.message]
        assert len(duplicate_issues) > 0


class TestValidationSummaries:
    """Test validation summary generation."""

    @pytest.mark.asyncio
    async def test_failed_summary_format(self, code_with_syntax_error):
        """Test failed validation summary format."""
        validator = ValidatorAgent()

        result = await validator.execute({
            "generated_files": {
                "broken.py": code_with_syntax_error
            }
        })

        summary = result["summary"]
        assert "failed" in summary.lower()
        assert "error" in summary.lower()

    @pytest.mark.asyncio
    async def test_passed_with_warnings_summary(self, code_with_security_issues):
        """Test passed with warnings summary."""
        validator = ValidatorAgent(
            enable_type_checking=False,
            enable_linting=False,
            enable_security_scan=True,
            strict_mode=False,
        )

        result = await validator.execute({
            "generated_files": {
                "dangerous.py": code_with_security_issues
            }
        })

        summary = result["summary"]
        assert "warning" in summary.lower()
