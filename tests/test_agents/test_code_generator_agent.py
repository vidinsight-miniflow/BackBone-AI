"""
Tests for Code Generator Agent.
"""

import pytest

from app.agents.architect_agent import ArchitectAgent
from app.agents.code_generator_agent import CodeGeneratorAgent
from tests.fixtures.sample_schemas import (
    VALID_SCHEMA_WITH_RELATIONSHIPS,
    VALID_SIMPLE_SCHEMA,
)


class TestCodeGeneratorAgent:
    """Tests for CodeGeneratorAgent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = CodeGeneratorAgent(use_llm=False, format_code=False)
        self.architect = ArchitectAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_generate_simple_model(self):
        """Test generating code for a simple schema."""
        # First, create architecture plan
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        # Generate code
        result = await self.agent.run({"architecture_plan": arch_plan})

        assert isinstance(result, dict)
        assert "generated_files" in result
        assert "summary" in result

        files = result["generated_files"]

        # Should have generated files
        assert len(files) > 0

        # Should have model file
        assert any("users.py" in path for path in files.keys())

        # Should have __init__.py
        assert any("__init__.py" in path for path in files.keys())

        # Should have database.py
        assert any("database.py" in path for path in files.keys())

    @pytest.mark.asyncio
    async def test_generated_model_content(self):
        """Test that generated model contains expected content."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Get users.py content
        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check class definition
        assert "class User" in users_file

        # Check __tablename__
        assert '__tablename__ = "users"' in users_file

        # Check columns
        assert "id = Column" in users_file
        assert "username = Column" in users_file
        assert "email = Column" in users_file

        # Check imports
        assert "from sqlalchemy import" in users_file
        assert "Column" in users_file
        assert "Integer" in users_file
        assert "String" in users_file

    @pytest.mark.asyncio
    async def test_generated_model_with_relationships(self):
        """Test generating models with relationships."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Get users.py
        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check relationship
        assert "posts = relationship" in users_file
        assert "Post" in users_file
        assert "back_populates" in users_file

        # Check relationship import
        assert "from sqlalchemy.orm import relationship" in users_file

    @pytest.mark.asyncio
    async def test_generated_model_with_foreign_key(self):
        """Test generating model with foreign keys."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Get posts.py
        posts_file = next(
            (content for path, content in files.items() if "posts.py" in path),
            None,
        )

        assert posts_file is not None

        # Check ForeignKey
        assert "ForeignKey" in posts_file
        assert "users.id" in posts_file

    @pytest.mark.asyncio
    async def test_generated_init_file(self):
        """Test that __init__.py is generated correctly."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Get __init__.py
        init_file = next(
            (content for path, content in files.items() if "__init__.py" in path),
            None,
        )

        assert init_file is not None

        # Check imports
        assert "from .users import User" in init_file
        assert "from .posts import Post" in init_file

        # Check __all__
        assert "__all__" in init_file
        assert "User" in init_file
        assert "Post" in init_file

    @pytest.mark.asyncio
    async def test_generated_mixins_file(self):
        """Test that mixins.py is generated when mixins are used."""
        # Use schema with timestamps
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_timestamps"] = True

        arch_plan = await self.architect.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Should have mixins.py
        mixins_file = next(
            (content for path, content in files.items() if "mixins.py" in path),
            None,
        )

        assert mixins_file is not None

        # Check TimestampMixin
        assert "class TimestampMixin" in mixins_file
        assert "created_at" in mixins_file
        assert "updated_at" in mixins_file

    @pytest.mark.asyncio
    async def test_generated_database_file(self):
        """Test that database.py is generated correctly."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Get database.py
        db_file = next(
            (content for path, content in files.items() if "database.py" in path),
            None,
        )

        assert db_file is not None

        # Check Base
        assert "Base = declarative_base()" in db_file

        # Check engine
        assert "engine = create_engine" in db_file

        # Check SessionLocal
        assert "SessionLocal = sessionmaker" in db_file

        # Check get_db function
        assert "def get_db" in db_file

    @pytest.mark.asyncio
    async def test_model_with_timestamps_mixin(self):
        """Test that models with TimestampMixin are generated correctly."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_timestamps"] = True

        arch_plan = await self.architect.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check inheritance
        assert "class User(Base, TimestampMixin)" in users_file

        # Check mixin import
        assert "from app.models.mixins import TimestampMixin" in users_file

        # Should NOT have created_at/updated_at columns (provided by mixin)
        assert "created_at = Column" not in users_file

    @pytest.mark.asyncio
    async def test_model_with_soft_delete_mixin(self):
        """Test that models with SoftDeleteMixin are generated correctly."""
        schema = VALID_SIMPLE_SCHEMA.copy()
        schema["schema"][0]["options"]["use_soft_delete"] = True

        arch_plan = await self.architect.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check inheritance
        assert "SoftDeleteMixin" in users_file

        # Check mixin import
        assert "from app.models.mixins import" in users_file
        assert "SoftDeleteMixin" in users_file

    @pytest.mark.asyncio
    async def test_model_repr_method(self):
        """Test that __repr__ method is generated."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check __repr__
        assert "def __repr__" in users_file
        assert "return f" in users_file

    @pytest.mark.asyncio
    async def test_summary_generation(self):
        """Test that summary is generated."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})

        assert "summary" in result
        summary = result["summary"]

        assert "TestProject" in summary
        assert "Models: 1" in summary

    @pytest.mark.asyncio
    async def test_invalid_input_missing_plan(self):
        """Test that validation fails if architecture_plan is missing."""
        with pytest.raises(ValueError, match="Input must contain 'architecture_plan'"):
            await self.agent.run({})

    @pytest.mark.asyncio
    async def test_input_validation(self):
        """Test input validation."""
        # Valid input (with dict, not validated yet)
        assert (
            await self.agent.validate_input({"architecture_plan": {}})
            is True
        )

        # Invalid inputs
        assert await self.agent.validate_input({}) is False
        assert await self.agent.validate_input("not a dict") is False


class TestCodeGeneratorAgentEdgeCases:
    """Test edge cases for Code Generator Agent."""

    def setup_method(self):
        """Set up test fixtures."""
        self.agent = CodeGeneratorAgent(use_llm=False, format_code=False)
        self.architect = ArchitectAgent(use_llm=False)

    @pytest.mark.asyncio
    async def test_enum_column_generation(self):
        """Test that Enum columns are generated correctly."""
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
                            "values": ["active", "inactive"],
                            "default": "active",
                            "nullable": False,
                        },
                    ],
                    "relationships": [],
                }
            ],
        }

        arch_plan = await self.architect.run(
            {
                "validated_schema": schema,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        users_file = next(
            (content for path, content in files.items() if "users.py" in path),
            None,
        )

        assert users_file is not None

        # Check Enum import
        assert "Enum" in users_file

        # Check enum values
        assert "active" in users_file
        assert "inactive" in users_file

    @pytest.mark.asyncio
    async def test_multiple_models_generation(self):
        """Test generating multiple models."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SCHEMA_WITH_RELATIONSHIPS,
                "build_order": ["users", "posts"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Should have both model files
        assert any("users.py" in path for path in files.keys())
        assert any("posts.py" in path for path in files.keys())

        # Each should be valid
        for file_path, content in files.items():
            if file_path.endswith(".py"):
                # Basic syntax check - should have valid Python structure
                assert "class" in content or "def" in content or "import" in content

    @pytest.mark.asyncio
    async def test_no_mixins_no_mixins_file(self):
        """Test that mixins.py is not generated when no mixins are used."""
        arch_plan = await self.architect.run(
            {
                "validated_schema": VALID_SIMPLE_SCHEMA,
                "build_order": ["users"],
            }
        )

        result = await self.agent.run({"architecture_plan": arch_plan})
        files = result["generated_files"]

        # Should NOT have mixins.py
        mixins_file = next(
            (content for path, content in files.items() if "mixins.py" in path),
            None,
        )

        assert mixins_file is None
