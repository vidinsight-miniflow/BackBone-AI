"""
Tests for the generation workflow.
"""

import json
from pathlib import Path

import pytest

from app.workflows.generation_workflow import GenerationWorkflow


@pytest.fixture
def simple_schema():
    """Simple valid schema for testing."""
    return {
        "project_name": "TestProject",
        "db_type": "postgresql",
        "description": "Test project for workflow",
        "schema": [
            {
                "table_name": "users",
                "class_name": "User",
                "options": {
                    "use_timestamps": True,
                    "use_soft_delete": False,
                },
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "username", "type": "String", "length": 50, "unique": True, "nullable": False},
                    {"name": "email", "type": "String", "length": 100, "unique": True, "nullable": False},
                ],
                "relationships": [],
            }
        ],
    }


@pytest.fixture
def schema_with_relationships():
    """Schema with foreign keys and relationships."""
    return {
        "project_name": "BlogProject",
        "db_type": "postgresql",
        "schema": [
            {
                "table_name": "users",
                "class_name": "User",
                "options": {"use_timestamps": True, "use_soft_delete": False},
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "username", "type": "String", "length": 50, "unique": True, "nullable": False},
                ],
                "relationships": [
                    {"target_table": "posts", "target_class": "Post", "type": "one_to_many", "back_populates": "author"}
                ],
            },
            {
                "table_name": "posts",
                "class_name": "Post",
                "options": {"use_timestamps": True, "use_soft_delete": True},
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "title", "type": "String", "length": 200, "nullable": False},
                    {"name": "author_id", "type": "ForeignKey", "target": "users.id"},
                ],
                "relationships": [
                    {"target_table": "users", "target_class": "User", "type": "many_to_one", "back_populates": "posts"}
                ],
            },
        ],
    }


@pytest.fixture
def invalid_schema():
    """Invalid schema with broken foreign key."""
    return {
        "project_name": "InvalidProject",
        "db_type": "postgresql",
        "schema": [
            {
                "table_name": "posts",
                "class_name": "Post",
                "columns": [
                    {"name": "id", "type": "Integer", "primary_key": True},
                    {"name": "author_id", "type": "ForeignKey", "target": "nonexistent_table.id"},  # Invalid FK
                ],
                "relationships": [],
            }
        ],
    }


class TestGenerationWorkflow:
    """Test generation workflow."""

    @pytest.mark.asyncio
    async def test_workflow_initialization(self):
        """Test workflow can be initialized."""
        workflow = GenerationWorkflow(llm_provider="openai")

        assert workflow is not None
        assert workflow.schema_validator is not None
        assert workflow.architect is not None
        assert workflow.code_generator is not None
        assert workflow.workflow is not None

    @pytest.mark.asyncio
    async def test_validate_only_simple_schema(self, simple_schema):
        """Test validation-only workflow with simple schema."""
        workflow = GenerationWorkflow(llm_provider="openai")

        result = await workflow.validate_only(simple_schema)

        assert result is not None
        assert result["status"] in ["passed", "passed_with_warnings"]
        assert result.get("validated_schema") is not None

    @pytest.mark.asyncio
    async def test_validate_only_invalid_schema(self, invalid_schema):
        """Test validation-only workflow with invalid schema."""
        workflow = GenerationWorkflow(llm_provider="openai")

        result = await workflow.validate_only(invalid_schema)

        assert result is not None
        assert result["status"] == "failed"
        assert len(result.get("errors", [])) > 0

    @pytest.mark.asyncio
    async def test_full_workflow_simple_schema(self, simple_schema):
        """Test complete workflow with simple schema."""
        workflow = GenerationWorkflow(llm_provider="openai")

        final_state = await workflow.run(simple_schema)

        # Check validation stage
        assert final_state["validation_passed"] is True
        assert final_state["current_stage"] == "complete"

        # Check generated files
        generated_files = final_state.get("generated_files", {})
        assert len(generated_files) > 0
        assert any("user.py" in path.lower() for path in generated_files.keys())
        assert "models/__init__.py" in generated_files or "app/models/__init__.py" in generated_files

        # Check file contents
        user_file = next((content for path, content in generated_files.items() if "user.py" in path.lower()), None)
        assert user_file is not None
        assert "class User" in user_file
        assert "username" in user_file
        assert "email" in user_file

    @pytest.mark.asyncio
    async def test_full_workflow_with_relationships(self, schema_with_relationships):
        """Test complete workflow with relationships."""
        workflow = GenerationWorkflow(llm_provider="openai")

        final_state = await workflow.run(schema_with_relationships)

        # Check validation
        assert final_state["validation_passed"] is True
        assert final_state["current_stage"] == "complete"

        # Check generated files
        generated_files = final_state.get("generated_files", {})
        assert len(generated_files) >= 2  # At least user.py and post.py

        # Check build order (users should come before posts)
        build_order = final_state.get("build_order", [])
        assert "users" in build_order
        assert "posts" in build_order
        assert build_order.index("users") < build_order.index("posts")

        # Check relationship code
        post_file = next((content for path, content in generated_files.items() if "post.py" in path.lower()), None)
        assert post_file is not None
        assert "ForeignKey" in post_file
        assert "relationship" in post_file

    @pytest.mark.asyncio
    async def test_workflow_with_invalid_schema_stops_early(self, invalid_schema):
        """Test that workflow stops after validation failure."""
        workflow = GenerationWorkflow(llm_provider="openai")

        final_state = await workflow.run(invalid_schema)

        # Should fail at validation stage
        assert final_state["validation_passed"] is False
        assert len(final_state.get("errors", [])) > 0

        # Should not have generated files
        assert len(final_state.get("generated_files", {})) == 0

    @pytest.mark.asyncio
    async def test_workflow_state_progression(self, simple_schema):
        """Test that workflow state progresses through stages."""
        workflow = GenerationWorkflow(llm_provider="openai")

        final_state = await workflow.run(simple_schema)

        # Final state should be 'complete'
        assert final_state["current_stage"] == "complete"

        # Should have all required state fields
        assert "validation_report" in final_state
        assert "architecture_plan" in final_state
        assert "generated_files" in final_state

    @pytest.mark.asyncio
    async def test_workflow_accepts_json_string(self, simple_schema):
        """Test that workflow accepts JSON string as input."""
        workflow = GenerationWorkflow(llm_provider="openai")

        json_string = json.dumps(simple_schema)
        final_state = await workflow.run(json_string)

        assert final_state["validation_passed"] is True
        assert len(final_state.get("generated_files", {})) > 0


class TestWorkflowEdgeCases:
    """Test edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_empty_schema(self):
        """Test workflow with empty schema."""
        workflow = GenerationWorkflow(llm_provider="openai")

        schema = {
            "project_name": "EmptyProject",
            "db_type": "postgresql",
            "schema": [],
        }

        final_state = await workflow.run(schema)

        # Should still validate but might have warnings
        assert final_state["validation_passed"] is True
        # Empty schema should generate only basic files
        assert "generated_files" in final_state

    @pytest.mark.asyncio
    async def test_workflow_with_missing_project_name(self):
        """Test workflow handles missing project name gracefully."""
        workflow = GenerationWorkflow(llm_provider="openai")

        schema = {
            "db_type": "postgresql",
            "schema": [
                {
                    "table_name": "users",
                    "class_name": "User",
                    "columns": [
                        {"name": "id", "type": "Integer", "primary_key": True},
                    ],
                    "relationships": [],
                }
            ],
        }

        final_state = await workflow.run(schema)

        # Should use default project name
        assert final_state["project_name"] == "UnnamedProject"

    @pytest.mark.asyncio
    async def test_workflow_metadata(self, simple_schema):
        """Test that workflow includes metadata."""
        workflow = GenerationWorkflow(llm_provider="openai")

        final_state = await workflow.run(simple_schema)

        assert "metadata" in final_state
        assert final_state["metadata"]["llm_provider"] == "openai"
