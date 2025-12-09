"""
Tests for relationship validation and dependency analysis tools.
"""

import json

import pytest

from app.schemas.validation_schema import ValidationSeverity
from app.tools.relationship_tools import DependencyAnalyzerTool, ForeignKeyCheckerTool
from tests.fixtures.sample_schemas import (
    CIRCULAR_DEPENDENCY_SCHEMA,
    INVALID_FK_REFERENCE,
    VALID_SCHEMA_WITH_RELATIONSHIPS,
    VALID_SIMPLE_SCHEMA,
)


class TestForeignKeyCheckerTool:
    """Tests for ForeignKeyCheckerTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = ForeignKeyCheckerTool()

    def test_valid_foreign_keys(self):
        """Test validation of valid foreign keys."""
        result = self.tool._run(VALID_SCHEMA_WITH_RELATIONSHIPS)

        assert result["valid"] is True
        assert "foreign_keys" in result

        # Should have foreign keys for posts table
        assert "posts" in result["foreign_keys"]
        fks = result["foreign_keys"]["posts"]
        assert len(fks) == 1
        assert "author_id -> users.id" in fks[0]

    def test_no_foreign_keys(self):
        """Test schema with no foreign keys."""
        result = self.tool._run(VALID_SIMPLE_SCHEMA)

        assert result["valid"] is True
        assert len(result["foreign_keys"]) == 0

    def test_invalid_foreign_key_reference(self):
        """Test detection of invalid foreign key references."""
        result = self.tool._run(INVALID_FK_REFERENCE)

        assert result["valid"] is False
        assert len(result["issues"]) > 0

        # Should have FK_TABLE_NOT_FOUND error
        error_codes = [i["code"] for i in result["issues"]]
        assert "FK_TABLE_NOT_FOUND" in error_codes

    def test_foreign_key_to_non_existent_column(self):
        """Test detection of foreign key to non-existent column."""
        schema = {
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
                        }
                    ],
                    "relationships": [],
                },
                {
                    "table_name": "posts",
                    "class_name": "Post",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "author_id",
                            "type": "ForeignKey",
                            "target": "users.non_existent_column",
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                },
            ],
        }

        result = self.tool._run(schema)

        assert result["valid"] is False
        error_codes = [i["code"] for i in result["issues"]]
        assert "FK_COLUMN_NOT_FOUND" in error_codes

    def test_foreign_key_to_non_pk_column_warning(self):
        """Test warning when foreign key references non-PK, non-unique column."""
        schema = {
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
                            "name": "age",
                            "type": "Integer",
                            "nullable": True,
                            # Not PK or unique
                        },
                    ],
                    "relationships": [],
                },
                {
                    "table_name": "posts",
                    "class_name": "Post",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "user_age",
                            "type": "ForeignKey",
                            "target": "users.age",
                            "nullable": True,
                        },
                    ],
                    "relationships": [],
                },
            ],
        }

        result = self.tool._run(schema)

        # Should be valid (warning, not error)
        assert result["valid"] is True

        # But should have warning
        warning_issues = [
            i for i in result["issues"] if i["severity"] == ValidationSeverity.WARNING.value
        ]
        assert len(warning_issues) > 0

        warning_codes = [i["code"] for i in warning_issues]
        assert "FK_NOT_PK_OR_UNIQUE" in warning_codes


class TestDependencyAnalyzerTool:
    """Tests for DependencyAnalyzerTool."""

    def setup_method(self):
        """Set up test fixtures."""
        self.tool = DependencyAnalyzerTool()

    def test_simple_dependency_order(self):
        """Test dependency analysis for simple schema."""
        result = self.tool._run(VALID_SCHEMA_WITH_RELATIONSHIPS)

        assert result["valid"] is True
        assert "build_order" in result
        assert len(result["build_order"]) == 2

        # users should come before posts
        build_order = result["build_order"]
        assert build_order.index("users") < build_order.index("posts")

        # Check dependency graph
        assert "users" in result["dependency_graph"]
        assert "posts" in result["dependency_graph"]
        assert "users" in result["dependency_graph"]["posts"]

    def test_no_dependencies(self):
        """Test schema with no dependencies."""
        result = self.tool._run(VALID_SIMPLE_SCHEMA)

        assert result["valid"] is True
        assert len(result["build_order"]) == 1
        assert result["build_order"][0] == "users"
        assert len(result["dependency_graph"]["users"]) == 0

    def test_circular_dependency_detection(self):
        """Test detection of circular dependencies."""
        result = self.tool._run(CIRCULAR_DEPENDENCY_SCHEMA)

        assert result["valid"] is False
        assert len(result["cycles"]) > 0

        # Should have circular dependency error
        error_codes = [i["code"] for i in result["issues"]]
        assert "CIRCULAR_DEPENDENCY" in error_codes

        # Build order should be empty for circular deps
        assert len(result["build_order"]) == 0

    def test_complex_dependency_order(self):
        """Test dependency analysis for complex schema."""
        schema = {
            "project_name": "Complex",
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
                        }
                    ],
                    "relationships": [],
                },
                {
                    "table_name": "posts",
                    "class_name": "Post",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "author_id",
                            "type": "ForeignKey",
                            "target": "users.id",
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                },
                {
                    "table_name": "comments",
                    "class_name": "Comment",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "post_id",
                            "type": "ForeignKey",
                            "target": "posts.id",
                            "nullable": False,
                        },
                        {
                            "name": "user_id",
                            "type": "ForeignKey",
                            "target": "users.id",
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                },
            ],
        }

        result = self.tool._run(schema)

        assert result["valid"] is True
        build_order = result["build_order"]

        # users should come first
        assert build_order[0] == "users"

        # posts should come before comments
        assert build_order.index("posts") < build_order.index("comments")

        # Check dependencies
        deps = result["dependency_graph"]
        assert "users" in deps["posts"]
        assert "posts" in deps["comments"]
        assert "users" in deps["comments"]

    def test_self_referential_table(self):
        """Test handling of self-referential foreign keys."""
        schema = {
            "project_name": "SelfRef",
            "db_type": "postgresql",
            "schema": [
                {
                    "table_name": "employees",
                    "class_name": "Employee",
                    "options": {"use_timestamps": False, "use_soft_delete": False},
                    "columns": [
                        {
                            "name": "id",
                            "type": "Integer",
                            "primary_key": True,
                            "nullable": False,
                        },
                        {
                            "name": "manager_id",
                            "type": "ForeignKey",
                            "target": "employees.id",
                            "nullable": True,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        result = self.tool._run(schema)

        # Self-references should not create cycles
        assert result["valid"] is True
        assert len(result["cycles"]) == 0
        assert "employees" in result["build_order"]

        # Self-references should not be in dependency graph
        assert len(result["dependency_graph"]["employees"]) == 0
