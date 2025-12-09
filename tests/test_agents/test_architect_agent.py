"""
Tests for Architect Agent.
"""

import pytest

from app.agents.architect_agent import ArchitectAgent
from app.schemas.architect_schema import MixinType
from tests.fixtures.sample_schemas import (
    VALID_SCHEMA_WITH_RELATIONSHIPS,
    VALID_SIMPLE_SCHEMA,
)


class TestArchitectAgent:
    """Tests for ArchitectAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ArchitectAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_create_plan_simple_schema(self):
        """Test creating architecture plan for simple schema."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
                "validation_summary": "Schema is valid",
            }
        )

        assert isinstance(result, dict)
        assert result["project_name"] == "TestProject"
        assert len(result["models"]) == 1

        # Check model spec
        model = result["models"][0]
        assert model["table_name"] == "users"
        assert model["class_name"] == "User"
        assert model["file_path"] == "app/models/users.py"

    @pytest.mark.asyncio
    async def test_mixin_selection_timestamps(self):
        """Test that TimestampMixin is selected when use_timestamps is true."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_timestamps"] = True

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        assert MixinType.TIMESTAMP.value in model["mixins"]
        assert MixinType.TIMESTAMP.value in model["base_classes"]

    @pytest.mark.asyncio
    async def test_mixin_selection_soft_delete(self):
        """Test that SoftDeleteMixin is selected when use_soft_delete is true."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_soft_delete"] = True

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        assert MixinType.SOFT_DELETE.value in model["mixins"]
        assert MixinType.SOFT_DELETE.value in model["base_classes"]

    @pytest.mark.asyncio
    async def test_base_classes_order(self):
        """Test that base classes are in correct order."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_timestamps"] = True
        schema["schema"][0]["options"]["use_soft_delete"] = True

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        base_classes = model["base_classes"]

        # Base should be first
        assert base_classes[0] == "Base"

        # Mixins should follow
        assert "TimestampMixin" in base_classes
        assert "SoftDeleteMixin" in base_classes

    @pytest.mark.asyncio
    async def test_column_specs_creation(self):
        """Test that column specifications are created correctly."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        columns = model["columns"]

        # Check id column
        id_col = next(col for col in columns if col["name"] == "id")
        assert id_col["type"] == "Integer"
        assert id_col["kwargs"]["primary_key"] is True

        # Check username column
        username_col = next(col for col in columns if col["name"] == "username")
        assert username_col["type"] == "String"
        assert username_col["args"] == [50]
        assert username_col["kwargs"]["unique"] is True
        assert username_col["kwargs"]["nullable"] is False

    @pytest.mark.asyncio
    async def test_relationship_specs_creation(self):
        """Test that relationship specifications are created correctly."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        # Check users model relationships
        users_model = next(m for m in result["models"] if m["table_name"] == "users")
        assert len(users_model["relationships"]) == 1

        rel = users_model["relationships"][0]
        assert rel["name"] == "posts"
        assert rel["target_class"] == "Post"
        assert rel["relationship_type"] == "one_to_many"
        assert rel["back_populates"] == "author"

        # Check posts model relationships
        posts_model = next(m for m in result["models"] if m["table_name"] == "posts")
        assert len(posts_model["relationships"]) == 1

        rel = posts_model["relationships"][0]
        assert rel["name"] == "author"
        assert rel["target_class"] == "User"
        assert rel["relationship_type"] == "many_to_one"

    @pytest.mark.asyncio
    async def test_foreign_key_column_spec(self):
        """Test that foreign key columns are specified correctly."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        posts_model = next(m for m in result["models"] if m["table_name"] == "posts")
        fk_col = next(col for col in posts_model["columns"] if col["name"] == "author_id")

        assert fk_col["type"] == "Integer"
        assert "foreign_key" in fk_col["kwargs"]
        assert fk_col["kwargs"]["foreign_key"] == "users.id"

    @pytest.mark.asyncio
    async def test_dependencies_determination(self):
        """Test that dependencies are correctly determined."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        # Users has no dependencies
        users_model = next(m for m in result["models"] if m["table_name"] == "users")
        assert len(users_model["depends_on"]) == 0

        # Posts depends on users
        posts_model = next(m for m in result["models"] if m["table_name"] == "posts")
        assert "users" in posts_model["depends_on"]

    @pytest.mark.asyncio
    async def test_imports_generation(self):
        """Test that import statements are generated correctly."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        imports = model["imports"]

        # Check SQLAlchemy imports
        sa_import = next(imp for imp in imports if imp["module"] == "sqlalchemy")
        assert "Column" in sa_import["items"]
        assert "Integer" in sa_import["items"]
        assert "String" in sa_import["items"]

        # Check Base import
        base_import = next(imp for imp in imports if imp["module"] == "app.core.database")
        assert "Base" in base_import["items"]

    @pytest.mark.asyncio
    async def test_imports_with_relationships(self):
        """Test that relationship imports are included."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        users_model = next(m for m in result["models"] if m["table_name"] == "users")
        imports = users_model["imports"]

        # Should have relationship import
        rel_import = next(
            (imp for imp in imports if imp["module"] == "sqlalchemy.orm"), None
        )
        assert rel_import is not None
        assert "relationship" in rel_import["items"]

    @pytest.mark.asyncio
    async def test_imports_with_mixins(self):
        """Test that mixin imports are included."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_timestamps"] = True

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        imports = model["imports"]

        # Should have mixin import
        mixin_import = next(
            (imp for imp in imports if imp["module"] == "app.models.mixins"), None
        )
        assert mixin_import is not None
        assert "TimestampMixin" in mixin_import["items"]

    @pytest.mark.asyncio
    async def test_build_order_respected(self):
        """Test that build order is preserved in the plan."""
        build_order = ["users", "posts"]

        result = await self.agent.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": build_order,
            }
        )

        assert result["build_order"] == build_order

    @pytest.mark.asyncio
    async def test_file_path_generation(self):
        """Test that file paths are generated correctly."""
        result = await self.agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        assert model["file_path"] == "app/models/users.py"

    @pytest.mark.asyncio
    async def test_notes_for_composite_primary_key(self):
        """Test that notes are generated for composite primary keys."""
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

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["user_roles"],
            }
        )

        # Should have note about composite PK
        assert len(result["notes"]) > 0
        assert any("composite primary key" in note.lower() for note in result["notes"])

    @pytest.mark.asyncio
    async def test_plan_metadata(self):
        """Test that plan includes correct metadata."""
        validation_summary = "Schema validation passed"

        result = await self.agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
                "validation_summary": validation_summary,
            }
        )

        assert result["project_name"] == VALID_SIMPLE_SCHEMA["project_name"]
        assert result["db_type"] == VALID_SIMPLE_SCHEMA["db_type"]
        assert result["validation_summary"] == validation_summary

    @pytest.mark.asyncio
    async def test_invalid_input_missing_schema(self):
        """Test that validation fails if validated_schema is missing."""
        with pytest.raises(ValueError, match="Input must contain 'validated_schema'"):
            await self.agent.run({"build_order": ["users"]})

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation."""
        # Valid input
        assert (
            await self.agent.validate_input({"validated_schema": VALID_SIMPLE_SCHEMA})
            is True
        )

        # Invalid inputs
        assert await self.agent.validate_input({}) is False
        assert await self.agent.validate_input("not a dict") is False


class TestArchitectAgentEdgeCases:
    """Test edge cases for Architect Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = ArchitectAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_enum_column_specification(self):
        """Test that Enum columns are handled correctly."""
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
                            "name": "status",
                            "type": "Enum",
                            "values": ["active", "inactive", "banned"],
                            "default": "active",
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        model = result["models"][0]
        status_col = next(col for col in model["columns"] if col["name"] == "status")

        assert status_col["type"] == "Enum"
        assert "active" in status_col["args"]
        assert "inactive" in status_col["args"]
        assert "banned" in status_col["args"]

    @pytest.mark.asyncio
    async def test_self_referential_table(self):
        """Test handling of self-referential foreign keys."""
        schema = {
            "project_name": "Test",
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

        result = await self.agent.run(
            {
                "validated_schema": schema,
                "build_order": ["employees"],
            }
        )

        model = result["models"][0]

        # Should not have itself in depends_on
        assert "employees" not in model["depends_on"]

        # Should have manager_id column
        manager_col = next(
            col for col in model["columns"] if col["name"] == "manager_id"
        )
        assert manager_col["type"] == "Integer"
        assert manager_col["kwargs"]["foreign_key"] == "employees.id"

    @pytest.mark.asyncio
    async def test_custom_output_directories(self):
        """Test custom output directories."""
        custom_agent = ArchitectAgent(
            use_llm=False,
            output_directory="./custom_output",
            models_directory="models",
        )

        result = await custom_agent.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        assert result["output_directory"] == "./custom_output"
        assert result["models_directory"] == "models"

        model = result["models"][0]
        assert model["file_path"] == "models/users.py"
