"""
Code Generator Agent.

This agent generates SQLAlchemy model code from architectural plans.
It uses Jinja2 templates to create production-ready Python files.
"""

import os
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, Template
from langchain_core.language_models import BaseChatModel

from app.agents.base_agent import BaseAgent
from app.core.logger import get_logger
from app.prompts.generator_prompts import CODE_GENERATOR_SYSTEM_PROMPT
from app.schemas.architect_schema import ArchitecturePlan, MixinType

logger = get_logger(__name__)


class GeneratedFile(dict):
    """Represents a generated file with path and content."""

    def __init__(self, file_path: str, content: str):
        super().__init__(file_path=file_path, content=content)
        self.file_path = file_path
        self.content = content


class CodeGeneratorAgent(BaseAgent):
    """
    Agent for generating SQLAlchemy model code.

    This agent takes an ArchitecturePlan and generates complete,
    production-ready Python code including:
    - Individual model files
    - __init__.py for package exports
    - mixins.py for mixin definitions
    - database.py for Base and session management
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        use_llm: bool = False,
        template_dir: str | None = None,
        format_code: bool = True,
    ):
        """
        Initialize Code Generator Agent.

        Args:
            llm: Language model instance (optional)
            use_llm: Whether to use LLM for code generation
            template_dir: Directory containing Jinja2 templates
            format_code: Whether to format generated code with Black
        """
        super().__init__(
            name="code_generator",
            llm=llm if llm else self._create_dummy_llm(),
            system_prompt=CODE_GENERATOR_SYSTEM_PROMPT,
        )

        self.use_llm = use_llm and llm is not None
        self.format_code = format_code

        # Set up Jinja2 environment
        if template_dir is None:
            # Default to templates directory in project root
            project_root = Path(__file__).parent.parent.parent
            template_dir = str(project_root / "templates")

        self.template_dir = template_dir
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
        )
        
        # Add custom filter for Python boolean values
        def python_bool(value):
            """Convert value to Python boolean string."""
            if isinstance(value, bool):
                return "True" if value else "False"
            elif value is None:
                return "None"
            elif isinstance(value, str):
                return f'"{value}"'
            return str(value)
        
        # Add test for boolean type
        def is_boolean(value):
            """Check if value is boolean."""
            return isinstance(value, bool)
        
        self.jinja_env.filters['python_bool'] = python_bool
        self.jinja_env.tests['boolean'] = is_boolean

        logger.info(
            f"Code Generator Agent initialized "
            f"(LLM mode: {'enabled' if self.use_llm else 'disabled'}, "
            f"Template dir: {template_dir})"
        )

    def _create_dummy_llm(self) -> Any:
        """Create a dummy LLM for non-LLM mode."""

        class DummyLLM:
            pass

        return DummyLLM()  # type: ignore

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return CODE_GENERATOR_SYSTEM_PROMPT

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute code generation.

        Args:
            input_data: Dict with:
                - architecture_plan: ArchitecturePlan as dict

        Returns:
            dict: Generated files as {file_path: content}
        """
        architecture_plan_dict = input_data.get("architecture_plan")

        if not architecture_plan_dict:
            raise ValueError("Input must contain 'architecture_plan'")

        logger.info("Starting code generation")

        # Parse architecture plan
        plan = ArchitecturePlan.model_validate(architecture_plan_dict)
        logger.debug(f"Generating code for project: {plan.project_name}")

        # Generate files
        generated_files: dict[str, str] = {}

        # 1. Generate model files
        for model in plan.models:
            logger.info(f"Generating model: {model.class_name}")
            file_path = model.file_path
            content = self._generate_model_file(model)

            if self.format_code:
                content = self._format_code(content)

            generated_files[file_path] = content

        # 2. Generate __init__.py
        logger.info("Generating __init__.py")
        init_path = f"{plan.models_directory}/__init__.py"
        init_content = self._generate_init_file(plan)
        if self.format_code:
            init_content = self._format_code(init_content)
        generated_files[init_path] = init_content

        # 3. Generate mixins.py if any mixins are used
        if self._has_mixins(plan):
            logger.info("Generating mixins.py")
            mixins_path = f"{plan.models_directory}/mixins.py"
            mixins_content = self._generate_mixins_file()
            if self.format_code:
                mixins_content = self._format_code(mixins_content)
            generated_files[mixins_path] = mixins_content

        # 4. Generate database.py
        logger.info("Generating database.py")
        db_path = "app/core/database.py"
        db_content = self._generate_database_file(plan)
        if self.format_code:
            db_content = self._format_code(db_content)
        generated_files[db_path] = db_content

        logger.info(
            f"Code generation complete: {len(generated_files)} files generated"
        )

        return {"generated_files": generated_files, "summary": self._create_summary(plan)}

    def _generate_model_file(self, model: Any) -> str:
        """
        Generate code for a single model.

        Args:
            model: ModelSpec

        Returns:
            str: Generated Python code
        """
        # Use modern SQLAlchemy 2.0 template
        template = self.jinja_env.get_template("model.py.jinja2")

        # Prepare imports as strings
        imports = [imp.to_string() for imp in model.imports]

        # Render template
        content = template.render(
            model=model,
            imports=imports,
            columns=model.columns,
            relationships=model.relationships,
        )

        return content

    def _generate_init_file(self, plan: ArchitecturePlan) -> str:
        """
        Generate __init__.py file.

        Args:
            plan: ArchitecturePlan

        Returns:
            str: Generated Python code
        """
        template = self.jinja_env.get_template("__init__.py.jinja2")

        content = template.render(
            project_name=plan.project_name, models=plan.models
        )

        return content

    def _generate_mixins_file(self) -> str:
        """
        Generate mixins.py file with improved mixins.

        Returns:
            str: Generated Python code
        """
        # Use mixins template
        template = self.jinja_env.get_template("mixins.py.jinja2")
        content = template.render()
        return content

    def _generate_database_file(self, plan: ArchitecturePlan) -> str:
        """
        Generate database.py file with async support.

        Args:
            plan: ArchitecturePlan

        Returns:
            str: Generated Python code
        """
        # Use database template with async support
        template = self.jinja_env.get_template("database.py.jinja2")

        # Determine database URLs (both sync and async)
        db_url_templates = {
            "postgresql": "postgresql://user:password@localhost/dbname",
            "mysql": "mysql://user:password@localhost/dbname",
            "sqlite": "sqlite:///./database.db",
        }

        async_db_url_templates = {
            "postgresql": "postgresql+asyncpg://user:password@localhost/dbname",
            "mysql": "mysql+aiomysql://user:password@localhost/dbname",
            "sqlite": "sqlite+aiosqlite:///./database.db",
        }

        db_url = db_url_templates.get(
            plan.db_type, "postgresql://user:password@localhost/dbname"
        )

        async_db_url = async_db_url_templates.get(
            plan.db_type, "postgresql+asyncpg://user:password@localhost/dbname"
        )

        content = template.render(
            database_url=db_url,
            async_database_url=async_db_url
        )
        return content

    def _has_mixins(self, plan: ArchitecturePlan) -> bool:
        """
        Check if any models use mixins.

        Args:
            plan: ArchitecturePlan

        Returns:
            bool: True if any mixins are used
        """
        for model in plan.models:
            if model.mixins:
                return True
        return False

    def _format_code(self, code: str) -> str:
        """
        Format code using Black.

        Args:
            code: Python code string

        Returns:
            str: Formatted code
        """
        try:
            import black

            mode = black.Mode(
                target_versions={black.TargetVersion.PY311},
                line_length=100,
                string_normalization=True,
            )

            formatted = black.format_str(code, mode=mode)
            return formatted

        except ImportError:
            logger.warning("Black not installed, skipping code formatting")
            return code
        except black.InvalidInput as e:
            logger.warning(f"Code formatting failed (syntax error): {e}")
            # Return original code if Black can't format it (syntax errors)
            return code
        except Exception as e:
            logger.warning(f"Code formatting failed: {e}")
            return code

    def _create_summary(self, plan: ArchitecturePlan) -> str:
        """
        Create a summary of generated code.

        Args:
            plan: ArchitecturePlan

        Returns:
            str: Summary string
        """
        lines = [
            f"Generated code for {plan.project_name}",
            f"Database: {plan.db_type}",
            f"Models: {plan.total_models}",
            f"Total columns: {plan.total_columns}",
            f"Total relationships: {plan.total_relationships}",
        ]

        has_mixins = self._has_mixins(plan)
        files_count = plan.total_models + 2  # models + __init__.py + database.py
        if has_mixins:
            files_count += 1  # + mixins.py

        lines.append(f"Files generated: {files_count}")

        return "\n".join(lines)

    async def validate_input(self, input_data: Any) -> bool:
        """Validate that input contains required fields."""
        if not isinstance(input_data, dict):
            logger.error("Input must be a dictionary")
            return False

        if "architecture_plan" not in input_data:
            logger.error("Input must contain 'architecture_plan' key")
            return False

        return True

    def write_files(
        self, generated_files: dict[str, str], output_dir: str = "./generated"
    ) -> list[str]:
        """
        Write generated files to disk.

        Args:
            generated_files: Dict of {file_path: content}
            output_dir: Output directory

        Returns:
            list[str]: List of created file paths
        """
        created_files = []
        output_path = Path(output_dir)

        for file_path, content in generated_files.items():
            full_path = output_path / file_path

            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            created_files.append(str(full_path))
            logger.info(f"Created file: {full_path}")

        return created_files
