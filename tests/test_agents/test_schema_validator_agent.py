"""
Tests for Schema Validator Agent.
"""

import json

import pytest

from app.agents.schema_validator_agent import SchemaValidatorAgent
from app.schemas.agent_output_schema import ValidationStatus
from tests.fixtures.sample_schemas import (
    CIRCULAR_DEPENDENCY_SCHEMA,
    INVALID_FK_REFERENCE,
    INVALID_JSON_SYNTAX,
    INVALID_NO_PRIMARY_KEY,
    VALID_SCHEMA_WITH_RELATIONSHIPS,
    VALID_SIMPLE_SCHEMA,
    get_circular_dependency_json,
    get_invalid_fk_json,
    get_invalid_no_pk_json,
    get_valid_simple_json,
    get_valid_with_relationships_json,
)


class TestSchemaValidatorAgent:
    """Tests for SchemaValidatorAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        # Initialize agent without LLM (direct tool use)
        self.agent = SchemaValidatorAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_validate_simple_valid_schema(self):
        """Test validation of a simple valid schema."""
        json_content = get_valid_simple_json()
        result = await self.agent.run({"schema": json_content})

        assert isinstance(result, dict)
        assert result["validation_status"] == ValidationStatus.PASS.value
        assert result["schema_valid"] is True
        assert result["foreign_keys_valid"] is True
        assert result["dependencies_valid"] is True

        # Should have build order
        assert "build_order" in result
        assert len(result["build_order"]) == 1
        assert result["build_order"][0] == "users"

        # Should not have errors
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_schema_with_relationships(self):
        """Test validation of schema with relationships."""
        json_content = get_valid_with_relationships_json()
        result = await self.agent.run({"schema": json_content})

        assert result["validation_status"] == ValidationStatus.PASS.value
        assert result["schema_valid"] is True
        assert result["foreign_keys_valid"] is True
        assert result["dependencies_valid"] is True

        # Check build order
        build_order = result["build_order"]
        assert len(build_order) == 2
        assert build_order.index("users") < build_order.index("posts")

        # Should not have errors
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_invalid_json_syntax(self):
        """Test validation fails for invalid JSON syntax."""
        result = await self.agent.run({"schema": INVALID_JSON_SYNTAX})

        assert result["validation_status"] == ValidationStatus.FAIL.value
        assert result["schema_valid"] is False
        assert len(result["errors"]) > 0

        # Check that error mentions JSON syntax
        error_messages = [e["message"] for e in result["errors"]]
        assert any("JSON syntax" in msg.lower() for msg in error_messages)

    @pytest.mark.asyncio
    async def test_validate_missing_primary_key(self):
        """Test validation fails when table has no primary key."""
        json_content = get_invalid_no_pk_json()
        result = await self.agent.run({"schema": json_content})

        assert result["validation_status"] == ValidationStatus.FAIL.value
        assert result["schema_valid"] is False
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_invalid_foreign_key(self):
        """Test validation fails for invalid foreign key reference."""
        json_content = get_invalid_fk_json()
        result = await self.agent.run({"schema": json_content})

        assert result["validation_status"] == ValidationStatus.FAIL.value
        assert result["foreign_keys_valid"] is False
        assert len(result["errors"]) > 0

        # Check error mentions foreign key
        error_messages = [e["message"] for e in result["errors"]]
        assert any("foreign key" in msg.lower() for msg in error_messages)

    @pytest.mark.asyncio
    async def test_validate_circular_dependency(self):
        """Test validation fails for circular dependencies."""
        json_content = get_circular_dependency_json()
        result = await self.agent.run({"schema": json_content})

        assert result["validation_status"] == ValidationStatus.FAIL.value
        assert result["dependencies_valid"] is False
        assert len(result["errors"]) > 0

        # Check error mentions circular dependency
        error_messages = [e["message"] for e in result["errors"]]
        assert any("circular" in msg.lower() for msg in error_messages)

    @pytest.mark.asyncio
    async def test_warnings_present_for_valid_schema(self):
        """Test that warnings are present even when schema is valid."""
        # Schema with String without length should produce warning
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
                            "name": "name",
                            "type": "String",
                            # No length specified
                            "nullable": True,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        result = await self.agent.run({"schema": json.dumps(schema)})

        # Should pass but with warnings
        assert result["validation_status"] == ValidationStatus.PASS.value
        assert len(result["warnings"]) > 0

        # Should have recommendation
        warning = result["warnings"][0]
        assert "recommendation" in warning
        assert warning["recommendation"]

    @pytest.mark.asyncio
    async def test_info_messages_for_composite_keys(self):
        """Test that info messages are provided for special cases."""
        schema = {
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

        result = await self.agent.run({"schema": json.dumps(schema)})

        # Should have info messages
        assert len(result["info"]) > 0

    @pytest.mark.asyncio
    async def test_recommendations_provided(self):
        """Test that recommendations are provided."""
        json_content = get_valid_simple_json()
        result = await self.agent.run({"schema": json_content})

        # Should have recommendations
        assert "recommendations" in result
        assert isinstance(result["recommendations"], list)

    @pytest.mark.asyncio
    async def test_tool_outputs_included(self):
        """Test that raw tool outputs are included for debugging."""
        json_content = get_valid_simple_json()
        result = await self.agent.run({"schema": json_content})

        # Should have tool outputs
        assert "tool_outputs" in result
        assert "json_validation" in result["tool_outputs"]
        assert "fk_validation" in result["tool_outputs"]
        assert "dependency_analysis" in result["tool_outputs"]

    @pytest.mark.asyncio
    async def test_invalid_input_missing_schema_key(self):
        """Test that validation fails if input doesn't have schema key."""
        with pytest.raises(ValueError, match="Input must contain 'schema' key"):
            await self.agent.run({"wrong_key": "value"})

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation."""
        # Valid input
        assert await self.agent.validate_input({"schema": "valid json"}) is True

        # Invalid inputs
        assert await self.agent.validate_input({}) is False
        assert await self.agent.validate_input({"schema": 123}) is False
        assert await self.agent.validate_input("not a dict") is False

    @pytest.mark.asyncio
    async def test_build_order_correctness(self):
        """Test that build order is correct for complex dependencies."""
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
                    ],
                    "relationships": [],
                },
            ],
        }

        result = await self.agent.run({"schema": json.dumps(schema)})

        assert result["validation_status"] == ValidationStatus.PASS.value

        build_order = result["build_order"]
        assert len(build_order) == 3

        # Check order is correct
        assert build_order[0] == "users"
        assert build_order.index("posts") < build_order.index("comments")


class TestSchemaValidatorAgentEdgeCases:
    """Test edge cases for Schema Validator Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = SchemaValidatorAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_empty_schema_list(self):
        """Test handling of empty schema list."""
        schema = {
            "project_name": "Empty",
            "db_type": "postgresql",
            "schema": [],
        }

        result = await self.agent.run({"schema": json.dumps(schema)})

        # Should fail validation
        assert result["validation_status"] == ValidationStatus.FAIL.value

    @pytest.mark.asyncio
    async def test_self_referential_table(self):
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

        result = await self.agent.run({"schema": json.dumps(schema)})

        # Should pass - self-references are allowed
        assert result["validation_status"] == ValidationStatus.PASS.value
        assert result["dependencies_valid"] is True
