"""
Pydantic schemas for validation results.
These schemas define the output format of validation tools.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""

    ERROR = "error"  # Critical issues that prevent code generation
    WARNING = "warning"  # Non-critical issues that should be addressed
    INFO = "info"  # Informational messages


class ValidationIssue(BaseModel):
    """A single validation issue."""

    severity: ValidationSeverity = Field(..., description="Issue severity")
    message: str = Field(..., description="Issue description")
    location: str | None = Field(None, description="Location of the issue (e.g., table name, column name)")
    code: str | None = Field(None, description="Error code for programmatic handling")

    def __str__(self) -> str:
        """String representation of the issue."""
        location_str = f" [{self.location}]" if self.location else ""
        return f"[{self.severity.value.upper()}]{location_str} {self.message}"


class ValidationReport(BaseModel):
    """Validation report containing all issues found."""

    valid: bool = Field(..., description="Overall validation status")
    issues: list[ValidationIssue] = Field(default_factory=list, description="List of validation issues")
    summary: str = Field(..., description="Summary of validation results")

    @property
    def error_count(self) -> int:
        """Count of error-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        """Count of warning-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        """Count of info-level issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.INFO)

    def get_errors(self) -> list[ValidationIssue]:
        """Get all error-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]

    def get_warnings(self) -> list[ValidationIssue]:
        """Get all warning-level issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]

    def to_string(self) -> str:
        """Convert report to formatted string."""
        lines = [f"Validation Report: {self.summary}", ""]

        if self.error_count > 0:
            lines.append(f"Errors: {self.error_count}")
            for issue in self.get_errors():
                lines.append(f"  - {issue}")
            lines.append("")

        if self.warning_count > 0:
            lines.append(f"Warnings: {self.warning_count}")
            for issue in self.get_warnings():
                lines.append(f"  - {issue}")
            lines.append("")

        if self.valid:
            lines.append("✅ Schema is valid!")
        else:
            lines.append("❌ Schema validation failed!")

        return "\n".join(lines)


class DependencyNode(BaseModel):
    """A node in the dependency graph."""

    table_name: str = Field(..., description="Table name")
    depends_on: list[str] = Field(default_factory=list, description="Tables this table depends on")


class DependencyAnalysis(BaseModel):
    """Result of dependency analysis."""

    valid: bool = Field(..., description="Whether the dependency graph is valid (no cycles)")
    build_order: list[str] = Field(default_factory=list, description="Order in which tables should be created")
    dependency_graph: dict[str, list[str]] = Field(
        default_factory=dict, description="Dependency graph (table -> dependencies)"
    )
    cycles: list[list[str]] = Field(
        default_factory=list, description="Circular dependencies found"
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="Issues found during analysis"
    )

    def to_string(self) -> str:
        """Convert analysis to formatted string."""
        lines = ["Dependency Analysis", ""]

        if self.valid:
            lines.append("✅ No circular dependencies found")
            lines.append("")
            lines.append("Build Order:")
            for i, table in enumerate(self.build_order, 1):
                deps = self.dependency_graph.get(table, [])
                deps_str = f" (depends on: {', '.join(deps)})" if deps else " (no dependencies)"
                lines.append(f"  {i}. {table}{deps_str}")
        else:
            lines.append("❌ Circular dependencies detected!")
            lines.append("")
            lines.append("Cycles found:")
            for i, cycle in enumerate(self.cycles, 1):
                lines.append(f"  {i}. {' -> '.join(cycle)} -> {cycle[0]}")

        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")

        return "\n".join(lines)


class ForeignKeyValidation(BaseModel):
    """Result of foreign key validation."""

    valid: bool = Field(..., description="Whether all foreign keys are valid")
    foreign_keys: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Foreign keys by table (table -> list of FK targets)"
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list, description="Issues found with foreign keys"
    )

    def to_string(self) -> str:
        """Convert validation to formatted string."""
        lines = ["Foreign Key Validation", ""]

        if self.valid:
            lines.append("✅ All foreign keys are valid")
            lines.append("")
            lines.append("Foreign Keys:")
            for table, fks in self.foreign_keys.items():
                if fks:
                    lines.append(f"  {table}:")
                    for fk in fks:
                        lines.append(f"    - {fk}")
        else:
            lines.append("❌ Invalid foreign keys found!")

        if self.issues:
            lines.append("")
            lines.append("Issues:")
            for issue in self.issues:
                lines.append(f"  - {issue}")

        return "\n".join(lines)
