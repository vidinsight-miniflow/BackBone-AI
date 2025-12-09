"""
Pydantic schemas for agent output.
These schemas define the output format of different agents.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    """Overall validation status."""

    PASS = "PASS"
    FAIL = "FAIL"


class ValidationErrorDetail(BaseModel):
    """Detailed information about a validation error."""

    message: str = Field(..., description="Error message")
    location: str | None = Field(None, description="Location of the error")
    recommendation: str | None = Field(None, description="How to fix this error")


class ValidationWarningDetail(BaseModel):
    """Detailed information about a validation warning."""

    message: str = Field(..., description="Warning message")
    location: str | None = Field(None, description="Location of the warning")
    recommendation: str | None = Field(None, description="Suggested improvement")


class ValidationInfoDetail(BaseModel):
    """Detailed information about validation info."""

    message: str = Field(..., description="Information message")
    location: str | None = Field(None, description="Location reference")


class SchemaValidatorOutput(BaseModel):
    """Output schema for Schema Validator Agent."""

    validation_status: ValidationStatus = Field(
        ..., description="Overall validation status (PASS/FAIL)"
    )
    summary: str = Field(..., description="Brief summary of validation results")

    # Individual validation results
    schema_valid: bool = Field(..., description="JSON structure and syntax validation result")
    foreign_keys_valid: bool = Field(..., description="Foreign key validation result")
    dependencies_valid: bool = Field(..., description="Dependency analysis result")

    # Build order
    build_order: list[str] = Field(
        default_factory=list, description="Recommended table creation order"
    )

    # Issues
    errors: list[ValidationErrorDetail] = Field(
        default_factory=list, description="Critical errors that must be fixed"
    )
    warnings: list[ValidationWarningDetail] = Field(
        default_factory=list, description="Warnings that should be addressed"
    )
    info: list[ValidationInfoDetail] = Field(
        default_factory=list, description="Informational messages"
    )

    # Recommendations
    recommendations: list[str] = Field(
        default_factory=list, description="General recommendations for improvement"
    )

    # Raw tool outputs (for debugging/reference)
    tool_outputs: dict[str, Any] = Field(
        default_factory=dict, description="Raw outputs from validation tools"
    )

    @property
    def is_valid(self) -> bool:
        """Check if schema passed all validations."""
        return self.validation_status == ValidationStatus.PASS

    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0

    def get_all_issues(self) -> list[str]:
        """Get all issues as formatted strings."""
        issues = []

        for error in self.errors:
            location = f" [{error.location}]" if error.location else ""
            issues.append(f"❌ ERROR{location}: {error.message}")

        for warning in self.warnings:
            location = f" [{warning.location}]" if warning.location else ""
            issues.append(f"⚠️  WARNING{location}: {warning.message}")

        for info in self.info:
            location = f" [{info.location}]" if info.location else ""
            issues.append(f"ℹ️  INFO{location}: {info.message}")

        return issues

    def to_detailed_string(self) -> str:
        """Convert output to detailed formatted string."""
        lines = [
            "=" * 80,
            "SCHEMA VALIDATION REPORT",
            "=" * 80,
            "",
            f"Status: {'✅ PASS' if self.is_valid else '❌ FAIL'}",
            f"Summary: {self.summary}",
            "",
            "=" * 80,
            "VALIDATION RESULTS",
            "=" * 80,
            "",
            f"JSON Structure: {'✅ Valid' if self.schema_valid else '❌ Invalid'}",
            f"Foreign Keys: {'✅ Valid' if self.foreign_keys_valid else '❌ Invalid'}",
            f"Dependencies: {'✅ Valid' if self.dependencies_valid else '❌ Invalid'}",
            "",
        ]

        if self.build_order:
            lines.extend(
                [
                    "=" * 80,
                    "BUILD ORDER",
                    "=" * 80,
                    "",
                    "Tables should be created in this order:",
                ]
            )
            for i, table in enumerate(self.build_order, 1):
                lines.append(f"  {i}. {table}")
            lines.append("")

        if self.errors:
            lines.extend(
                [
                    "=" * 80,
                    f"ERRORS ({len(self.errors)})",
                    "=" * 80,
                    "",
                ]
            )
            for i, error in enumerate(self.errors, 1):
                location = f" [{error.location}]" if error.location else ""
                lines.append(f"{i}. {error.message}{location}")
                if error.recommendation:
                    lines.append(f"   → Recommendation: {error.recommendation}")
                lines.append("")

        if self.warnings:
            lines.extend(
                [
                    "=" * 80,
                    f"WARNINGS ({len(self.warnings)})",
                    "=" * 80,
                    "",
                ]
            )
            for i, warning in enumerate(self.warnings, 1):
                location = f" [{warning.location}]" if warning.location else ""
                lines.append(f"{i}. {warning.message}{location}")
                if warning.recommendation:
                    lines.append(f"   → Recommendation: {warning.recommendation}")
                lines.append("")

        if self.info:
            lines.extend(
                [
                    "=" * 80,
                    f"INFORMATION ({len(self.info)})",
                    "=" * 80,
                    "",
                ]
            )
            for i, info in enumerate(self.info, 1):
                location = f" [{info.location}]" if info.location else ""
                lines.append(f"{i}. {info.message}{location}")
            lines.append("")

        if self.recommendations:
            lines.extend(
                [
                    "=" * 80,
                    "RECOMMENDATIONS",
                    "=" * 80,
                    "",
                ]
            )
            for i, rec in enumerate(self.recommendations, 1):
                lines.append(f"{i}. {rec}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
