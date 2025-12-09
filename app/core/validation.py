"""
Input validation utilities for security.
"""

import json
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

from app.core.logger import get_logger

logger = get_logger(__name__)

# Size limits (in bytes)
MAX_JSON_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_REQUEST_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_STRING_LENGTH = 1000
MAX_ARRAY_LENGTH = 100

# Schema limits
MAX_TABLES = 50
MAX_COLUMNS_PER_TABLE = 100
MAX_RELATIONSHIPS_PER_TABLE = 50


class ValidationLimits(BaseModel):
    """Configuration for validation limits."""

    max_json_size: int = Field(
        default=MAX_JSON_SIZE, description="Maximum JSON size in bytes"
    )
    max_tables: int = Field(default=MAX_TABLES, description="Maximum number of tables")
    max_columns_per_table: int = Field(
        default=MAX_COLUMNS_PER_TABLE, description="Maximum columns per table"
    )
    max_relationships_per_table: int = Field(
        default=MAX_RELATIONSHIPS_PER_TABLE, description="Maximum relationships per table"
    )
    max_string_length: int = Field(
        default=MAX_STRING_LENGTH, description="Maximum string field length"
    )


def validate_json_size(json_data: str | bytes) -> None:
    """
    Validate JSON size is within limits.

    Args:
        json_data: JSON data as string or bytes

    Raises:
        HTTPException: If size exceeds limit
    """
    size = len(json_data.encode() if isinstance(json_data, str) else json_data)

    if size > MAX_JSON_SIZE:
        logger.warning(f"JSON size {size} exceeds limit {MAX_JSON_SIZE}")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"JSON size ({size} bytes) exceeds maximum allowed ({MAX_JSON_SIZE} bytes)",
        )


def validate_schema_limits(schema_data: Dict[str, Any], limits: Optional[ValidationLimits] = None) -> None:
    """
    Validate schema data against limits.

    Args:
        schema_data: Schema data to validate
        limits: Optional custom limits

    Raises:
        HTTPException: If limits are exceeded
    """
    if limits is None:
        limits = ValidationLimits()

    # Validate number of tables
    tables = schema_data.get("schema", [])
    if len(tables) > limits.max_tables:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Number of tables ({len(tables)}) exceeds maximum allowed ({limits.max_tables})",
        )

    # Validate each table
    for i, table in enumerate(tables):
        table_name = table.get("table_name", f"table_{i}")

        # Validate columns
        columns = table.get("columns", [])
        if len(columns) > limits.max_columns_per_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Table '{table_name}': Number of columns ({len(columns)}) exceeds maximum allowed ({limits.max_columns_per_table})",
            )

        # Validate relationships
        relationships = table.get("relationships", [])
        if len(relationships) > limits.max_relationships_per_table:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Table '{table_name}': Number of relationships ({len(relationships)}) exceeds maximum allowed ({limits.max_relationships_per_table})",
            )

        # Validate string lengths
        if len(table_name) > limits.max_string_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Table name '{table_name}' exceeds maximum length ({limits.max_string_length})",
            )


def sanitize_input(value: Any, max_length: int = MAX_STRING_LENGTH) -> Any:
    """
    Sanitize input value.

    Args:
        value: Value to sanitize
        max_length: Maximum string length

    Returns:
        Sanitized value
    """
    if isinstance(value, str):
        # Truncate if too long
        if len(value) > max_length:
            logger.warning(f"String truncated from {len(value)} to {max_length}")
            return value[:max_length]

        # Remove null bytes
        return value.replace("\x00", "")

    elif isinstance(value, dict):
        return {k: sanitize_input(v, max_length) for k, v in value.items()}

    elif isinstance(value, list):
        # Limit array length
        if len(value) > MAX_ARRAY_LENGTH:
            logger.warning(f"Array truncated from {len(value)} to {MAX_ARRAY_LENGTH}")
            value = value[:MAX_ARRAY_LENGTH]
        return [sanitize_input(v, max_length) for v in value]

    return value


def validate_json_structure(json_str: str) -> Dict[str, Any]:
    """
    Validate and parse JSON structure.

    Args:
        json_str: JSON string to validate

    Returns:
        Parsed JSON data

    Raises:
        HTTPException: If JSON is invalid
    """
    try:
        # Validate size first
        validate_json_size(json_str)

        # Parse JSON
        data = json.loads(json_str)

        # Sanitize input
        data = sanitize_input(data)

        return data

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON: {str(e)}",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"JSON validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"JSON validation error: {str(e)}",
        )


def validate_project_schema(schema_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate complete project schema.

    Args:
        schema_data: Project schema data

    Returns:
        Validated and sanitized schema data

    Raises:
        HTTPException: If validation fails
    """
    # Validate schema limits
    validate_schema_limits(schema_data)

    # Validate required fields
    if "project_name" not in schema_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: project_name",
        )

    if "schema" not in schema_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required field: schema",
        )

    # Validate project name
    project_name = schema_data["project_name"]
    if not isinstance(project_name, str) or not project_name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="project_name must be a non-empty string",
        )

    # Validate schema is a list
    if not isinstance(schema_data["schema"], list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="schema must be an array of table definitions",
        )

    return schema_data


class SecureRequestValidator:
    """Validator for securing API requests."""

    @staticmethod
    def validate_generation_request(schema: Dict[str, Any]) -> None:
        """
        Validate code generation request.

        Args:
            schema: Schema data to validate

        Raises:
            HTTPException: If validation fails
        """
        # Validate structure
        validated = validate_project_schema(schema)

        # Additional generation-specific validation
        # Check for suspicious patterns (SQL injection, XSS, etc.)
        schema_str = json.dumps(validated).lower()

        suspicious_patterns = [
            "drop table",
            "delete from",
            "<script>",
            "javascript:",
            "eval(",
            "exec(",
        ]

        for pattern in suspicious_patterns:
            if pattern in schema_str:
                logger.warning(f"Suspicious pattern detected: {pattern}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Suspicious pattern detected in schema: {pattern}",
                )
