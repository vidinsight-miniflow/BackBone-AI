"""
JSON validation tools for LangChain agents.
These tools validate JSON schema structure and content.
"""

import json
from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field, ValidationError

from app.core.logger import get_logger
from app.schemas.input_schema import ProjectSchema
from app.schemas.validation_schema import (
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)

logger = get_logger(__name__)


class JSONValidatorInput(BaseModel):
    """Input schema for JSON validator tool."""

    json_content: str = Field(
        ..., description="JSON content as string to validate"
    )


class JSONValidatorTool(BaseTool):
    """
    Tool for validating JSON schema structure and content.

    This tool performs comprehensive validation including:
    - JSON syntax validation
    - Schema structure validation using Pydantic
    - Field type validation
    - Required field checks
    - Naming convention validation
    """

    name: str = "json_validator"
    description: str = """
    Validates JSON schema structure and content.
    Use this tool to check if the input JSON is valid and follows the expected schema.
    Returns a validation report with any errors or warnings found.

    Input: JSON content as a string
    Output: ValidationReport with status and issues
    """
    args_schema: type[BaseModel] = JSONValidatorInput

    def _run(self, json_content: str) -> dict[str, Any]:
        """
        Validate JSON content.

        Args:
            json_content: JSON string to validate

        Returns:
            dict: ValidationReport as dictionary
        """
        logger.info("Starting JSON validation")
        issues: list[ValidationIssue] = []

        try:
            # Step 1: Parse JSON syntax
            try:
                data = json.loads(json_content)
                logger.debug("JSON syntax is valid")
            except json.JSONDecodeError as e:
                logger.error(f"JSON syntax error: {e}")
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Invalid JSON syntax: {e.msg}",
                        location=f"line {e.lineno}, column {e.colno}",
                        code="JSON_SYNTAX_ERROR",
                    )
                )
                # Cannot continue if JSON is invalid
                return ValidationReport(
                    valid=False,
                    issues=issues,
                    summary="JSON syntax validation failed",
                ).model_dump()

            # Step 2: Validate against Pydantic schema
            try:
                project_schema = ProjectSchema.model_validate(data)
                logger.info(f"Schema validation successful for project: {project_schema.project_name}")

                # Add info about the project
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        message=f"Project '{project_schema.project_name}' with {len(project_schema.schema)} table(s)",
                        code="PROJECT_INFO",
                    )
                )

                # Check for potential issues (warnings)
                self._check_warnings(project_schema, issues)

            except ValidationError as e:
                logger.error(f"Schema validation error: {e}")
                # Convert Pydantic errors to ValidationIssues
                for error in e.errors():
                    location = " -> ".join(str(loc) for loc in error["loc"])
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            message=error["msg"],
                            location=location,
                            code="SCHEMA_VALIDATION_ERROR",
                        )
                    )

                return ValidationReport(
                    valid=False,
                    issues=issues,
                    summary="Schema validation failed",
                ).model_dump()

            # Step 3: Additional semantic checks
            self._check_semantic_issues(project_schema, issues)

            # Determine overall validity
            has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in issues)

            report = ValidationReport(
                valid=not has_errors,
                issues=issues,
                summary=f"Validation {'successful' if not has_errors else 'failed'} with {len(issues)} issue(s)",
            )

            logger.info(f"Validation complete: {report.summary}")
            return report.model_dump()

        except Exception as e:
            logger.error(f"Unexpected error during validation: {e}", exc_info=True)
            return ValidationReport(
                valid=False,
                issues=[
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        message=f"Unexpected validation error: {str(e)}",
                        code="UNEXPECTED_ERROR",
                    )
                ],
                summary="Validation failed due to unexpected error",
            ).model_dump()

    async def _arun(self, json_content: str) -> dict[str, Any]:
        """Async version of _run."""
        return self._run(json_content)

    def _check_warnings(self, schema: ProjectSchema, issues: list[ValidationIssue]) -> None:
        """Check for potential issues that don't prevent validation but should be noted."""

        # Check for tables without relationships
        for table in schema.schema:
            if not table.relationships:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message="Table has no relationships defined",
                        location=f"table: {table.table_name}",
                        code="NO_RELATIONSHIPS",
                    )
                )

            # Check for String columns without length
            for column in table.columns:
                if column.type.value == "String" and not column.length:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            message="String column should specify length",
                            location=f"table: {table.table_name}, column: {column.name}",
                            code="STRING_NO_LENGTH",
                        )
                    )

    def _check_semantic_issues(self, schema: ProjectSchema, issues: list[ValidationIssue]) -> None:
        """Check for semantic issues in the schema."""

        # Check for multiple primary keys (composite keys)
        for table in schema.schema:
            pk_columns = [col.name for col in table.columns if col.primary_key]
            if len(pk_columns) > 1:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.INFO,
                        message=f"Table has composite primary key: {', '.join(pk_columns)}",
                        location=f"table: {table.table_name}",
                        code="COMPOSITE_PRIMARY_KEY",
                    )
                )

        # Check for tables with many columns (potential normalization issue)
        for table in schema.schema:
            if len(table.columns) > 20:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        message=f"Table has many columns ({len(table.columns)}). Consider normalization.",
                        location=f"table: {table.table_name}",
                        code="TOO_MANY_COLUMNS",
                    )
                )


class SchemaParserInput(BaseModel):
    """Input schema for schema parser tool."""

    json_content: str = Field(..., description="Valid JSON content to parse")


class SchemaParserTool(BaseTool):
    """
    Tool for parsing validated JSON into ProjectSchema object.
    Use this after JSONValidatorTool confirms the JSON is valid.
    """

    name: str = "schema_parser"
    description: str = """
    Parses validated JSON content into a structured ProjectSchema object.
    Use this tool after JSONValidatorTool confirms the schema is valid.

    Input: Valid JSON content as string
    Output: Parsed ProjectSchema as dictionary
    """
    args_schema: type[BaseModel] = SchemaParserInput

    def _run(self, json_content: str) -> dict[str, Any]:
        """
        Parse JSON into ProjectSchema.

        Args:
            json_content: Valid JSON string

        Returns:
            dict: ProjectSchema as dictionary
        """
        try:
            data = json.loads(json_content)
            project_schema = ProjectSchema.model_validate(data)
            logger.info(f"Successfully parsed schema for project: {project_schema.project_name}")
            return project_schema.model_dump()
        except Exception as e:
            logger.error(f"Failed to parse schema: {e}")
            raise ValueError(f"Failed to parse schema: {str(e)}")

    async def _arun(self, json_content: str) -> dict[str, Any]:
        """Async version of _run."""
        return self._run(json_content)
