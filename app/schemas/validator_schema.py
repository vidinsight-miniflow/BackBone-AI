"""
Schemas for code validation output.
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ValidationSeverityLevel(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    SUCCESS = "success"


class ValidationIssue(BaseModel):
    """A single validation issue."""

    severity: ValidationSeverityLevel
    category: str = Field(..., description="Category: syntax, types, style, security, etc.")
    message: str = Field(..., description="Human-readable message")
    file_path: Optional[str] = Field(None, description="File where issue was found")
    line_number: Optional[int] = Field(None, description="Line number of issue")
    column: Optional[int] = Field(None, description="Column number of issue")
    code: Optional[str] = Field(None, description="Error code (e.g., E501, F401)")
    suggestion: Optional[str] = Field(None, description="How to fix the issue")


class FileValidationResult(BaseModel):
    """Validation results for a single file."""

    file_path: str
    passed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Code metrics: lines, complexity, etc.",
    )


class CodeQualityMetrics(BaseModel):
    """Overall code quality metrics."""

    total_lines: int = 0
    total_files: int = 0
    files_with_issues: int = 0
    total_errors: int = 0
    total_warnings: int = 0
    total_info: int = 0
    complexity_score: Optional[float] = None
    maintainability_score: Optional[float] = None
    test_coverage: Optional[float] = None


class ValidatorAgentOutput(BaseModel):
    """Output from the Validator Agent."""

    status: str = Field(..., description="passed, failed, or passed_with_warnings")
    summary: str = Field(..., description="Human-readable summary")
    overall_passed: bool
    file_results: List[FileValidationResult] = Field(default_factory=list)
    metrics: CodeQualityMetrics
    errors: List[ValidationIssue] = Field(default_factory=list)
    warnings: List[ValidationIssue] = Field(default_factory=list)
    suggestions: List[ValidationIssue] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return self.metrics.total_errors > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return self.metrics.total_warnings > 0


class ValidationToolResult(BaseModel):
    """Result from a validation tool."""

    tool_name: str
    passed: bool
    issues: List[ValidationIssue] = Field(default_factory=list)
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
