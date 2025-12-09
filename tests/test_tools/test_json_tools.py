"""
Tests for JSON validation tools.
"""

import pytest

from app.schemas.validation_schema import ValidationReport, ValidationSeverity
from app.tools.json_tools import JSONValidatorTool, SchemaParserTool
from tests.fixtures.sample_schemas import (
    INVALID_JSON_SYNTAX,
    get_invalid_fk_json,
    get_invalid_no_pk_json,
    get_valid_simple_json,
    get_valid_with_relationships_json,
)


class TestJSONValidatorTool:
    """Tests for JSONValidatorTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = JSONValidatorTool()

    def test_valid_simple_schema(self):
        """Test validation of a valid simple schema."""
        json_content = get_valid_simple_json()
        result = self.tool._run(json_content)

        assert isinstance(result, dict)
        assert result["valid"] is True
        assert "issues" in result

        # Should have at least one info message
        issues = result["issues"]
        info_issues = [i for i in issues if i["severity"] == ValidationSeverity.INFO.value]
        assert len(info_issues) > 0

    def test_valid_schema_with_relationships(self):
        """Test validation of a schema with relationships."""
        json_content = get_valid_with_relationships_json()
        result = self.tool._run(json_content)

        assert result["valid"] is True
        assert "issues" in result

    def test_invalid_json_syntax(self):
        """Test validation fails for invalid JSON syntax."""
        result = self.tool._run(INVALID_JSON_SYNTAX)

        assert result["valid"] is False
        assert len(result["issues"]) > 0

        # Should have a syntax error
        error_codes = [i["code"] for i in result["issues"]]
        assert "JSON_SYNTAX_ERROR" in error_codes

    def test_invalid_no_primary_key(self):
        """Test validation fails when table has no primary key."""
        json_content = get_invalid_no_pk_json()
        result = self.tool._run(json_content)

        assert result["valid"] is False
        assert len(result["issues"]) > 0

        # Should have a schema validation error
        error_codes = [i["code"] for i in result["issues"]]
        assert "SCHEMA_VALIDATION_ERROR" in error_codes

    def test_warning_for_string_without_length(self):
        """Test that warning is issued for String columns without length."""
        schema_without_length = {
            "project_name": "Test",
            "db_type": "postgresql",
            "schema": [
                {
                    "table_name": "users",
                    "class_name": "User",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "name",
                            "type": "String",
                            # Missing length
                            "nullable": True,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        import json

        result = self.tool._run(json.dumps(schema_without_length))

        # Should be valid but with warnings
        assert result["valid"] is True
        warning_issues = [
            i for i in result["issues"] if i["severity"] == ValidationSeverity.WARNING.value
        ]
        assert len(warning_issues) > 0

        # Should have STRING_NO_LENGTH warning
        warning_codes = [i["code"] for i in warning_issues]
        assert "STRING_NO_LENGTH" in warning_codes

    def test_info_for_composite_primary_key(self):
        """Test that info message is provided for composite primary keys."""
        schema_composite_pk = {
            "project_name": "Test",
            "db_type": "postgresql",
            "schema": [
                {
                    "table_name": "user_roles",
                    "class_name": "UserRole",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "user_id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "role_id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        import json

        result = self.tool._run(json.dumps(schema_composite_pk))

        assert result["valid"] is True

        info_issues = [
            i for i in result["issues"] if i["severity"] == ValidationSeverity.INFO.value
        ]
        info_codes = [i["code"] for i in info_issues]
        assert "COMPOSITE_PRIMARY_KEY" in info_codes


class TestSchemaParserTool:
    """Tests for SchemaParserTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = SchemaParserTool()

    def test_parse_valid_schema(self):
        """Test parsing a valid schema."""
        json_content = get_valid_simple_json()
        result = self.tool._run(json_content)

        assert isinstance(result, dict)
        assert "project_name" in result
        assert result["project_name"] == "TestProject"
        assert "schema" in result
        assert len(result["schema"]) == 1

    def test_parse_invalid_json_raises_error(self):
        """Test that parsing invalid JSON raises an error."""
        with pytest.raises(ValueError, match="Failed to parse schema"):
            self.tool._run(INVALID_JSON_SYNTAX)

    def test_parse_schema_preserves_structure(self):
        """Test that parsing preserves schema structure."""
        json_content = get_valid_with_relationships_json()
        result = self.tool._run(json_content)

        assert result["project_name"] == "BlogProject"
        assert len(result["schema"]) == 2

        # Check first table
        users_table = result["schema"][0]
        assert users_table["table_name"] == "users"
        assert users_table["class_name"] == "User"

        # Check relationships
        assert len(users_table["relationships"]) == 1
        assert users_table["relationships"][0]["target_table"] == "posts"
