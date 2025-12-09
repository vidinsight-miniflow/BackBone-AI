"""
Architect Agent.

This agent creates detailed architectural plans for code generation.
It makes decisions about mixins, file structure, imports, and inheritance.
"""

from typing import Any

from langchain_core.language_models import BaseChatModel

from app.agents.base_agent import BaseAgent
from app.core.logger import get_logger
from app.prompts.architect_prompts import ARCHITECT_SYSTEM_PROMPT
from app.schemas.architect_schema import (
    ArchitecturePlan,
    ColumnSpec,
    ImportStatement,
    MixinType,
    ModelSpec,
    RelationshipSpec,
)
from app.schemas.input_schema import ColumnType, ProjectSchema, RelationshipType

logger = get_logger(__name__)


class ArchitectAgent(BaseAgent):
    """
    Agent for creating architectural plans.

    This agent analyzes validated schemas and creates detailed
    specifications for code generation including:
    - Mixin selection
    - File structure
    - Import statements
    - Inheritance chains
    - Column specifications
    - Relationship configurations
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        use_llm: bool = False,
        output_directory: str = "./generated",
        models_directory: str = "app/models",
    ):
        """
        Initialize Architect Agent.

        Args:
            llm: Language model instance (optional)
            use_llm: Whether to use LLM for enhanced planning
            output_directory: Output directory for generated code
            models_directory: Models directory relative to output
        """
        super().__init__(
            name="architect",
            llm=llm if llm else self._create_dummy_llm(),
            system_prompt=ARCHITECT_SYSTEM_PROMPT,
        )

        self.use_llm = use_llm and llm is not None
        self.output_directory = output_directory
        self.models_directory = models_directory

        logger.info(
            f"Architect Agent initialized (LLM mode: {'enabled' if self.use_llm else 'disabled'})"
        )

    def _create_dummy_llm(self) -> Any:
        """Create a dummy LLM for non-LLM mode."""

        class DummyLLM:
            pass

        return DummyLLM()  # type: ignore

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return ARCHITECT_SYSTEM_PROMPT

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute architectural planning.

        Args:
            input_data: Dict with:
                - validated_schema: ProjectSchema as dict
                - build_order: List of table names in build order
                - validation_summary: Summary from validation

        Returns:
            dict: ArchitecturePlan as dictionary
        """
        validated_schema = input_data.get("validated_schema")
        build_order = input_data.get("build_order", [])
        validation_summary = input_data.get("validation_summary", "")

        if not validated_schema:
            raise ValueError("Input must contain 'validated_schema'")

        logger.info("Starting architectural planning")

        # Parse schema
        schema = ProjectSchema.model_validate(validated_schema)
        logger.debug(f"Planning for project: {schema.project_name}")

        # Create model specifications
        models: list[ModelSpec] = []

        for table in schema.schema:
            logger.info(f"Creating spec for table: {table.table_name}")

            model_spec = self._create_model_spec(table, schema, build_order)
            models.append(model_spec)

        # Create architecture plan
        plan = ArchitecturePlan(
            project_name=schema.project_name,
            db_type=schema.db_type.value,
            description=schema.description,
            build_order=build_order if build_order else [t.table_name for t in schema.schema],
            models=models,
            output_directory=self.output_directory,
            models_directory=self.models_directory,
            validation_summary=validation_summary,
            notes=self._generate_notes(schema, models),
        )

        logger.info(
            f"Architecture plan created: {plan.total_models} models, "
            f"{plan.total_columns} columns, {plan.total_relationships} relationships"
        )

        return plan.model_dump()

    def _create_model_spec(
        self, table: Any, schema: ProjectSchema, build_order: list[str]
    ) -> ModelSpec:
        """
        Create detailed model specification for a table.

        Args:
            table: TableSchema
            schema: Full ProjectSchema
            build_order: Build order list

        Returns:
            ModelSpec: Complete model specification
        """
        # Determine mixins
        mixins = self._select_mixins(table.options)

        # Determine base classes
        base_classes = self._determine_base_classes(mixins)

        # Create file path
        file_path = self._create_file_path(table.table_name)

        # Create column specs
        columns = self._create_column_specs(table.columns, mixins)

        # Create relationship specs
        relationships = self._create_relationship_specs(table.relationships)

        # Determine dependencies
        depends_on = self._determine_dependencies(table, schema)

        # Generate imports
        imports = self._generate_imports(table, mixins, relationships)

        return ModelSpec(
            table_name=table.table_name,
            class_name=table.class_name,
            file_path=file_path,
            base_classes=base_classes,
            mixins=mixins,
            columns=columns,
            relationships=relationships,
            imports=imports,
            description=table.description,
            depends_on=depends_on,
        )

    def _select_mixins(self, options: Any) -> list[MixinType]:
        """
        Select appropriate mixins based on table options.

        Args:
            options: TableOptions

        Returns:
            list[MixinType]: Selected mixins
        """
        mixins = []

        if options.use_timestamps:
            mixins.append(MixinType.TIMESTAMP)

        if options.use_soft_delete:
            mixins.append(MixinType.SOFT_DELETE)

        return mixins

    def _determine_base_classes(self, mixins: list[MixinType]) -> list[str]:
        """
        Determine base classes in correct inheritance order.

        Args:
            mixins: Selected mixins

        Returns:
            list[str]: Base classes in order
        """
        base_classes = ["Base"]

        # Add mixins in order
        for mixin in mixins:
            base_classes.append(mixin.value)

        return base_classes

    def _create_file_path(self, table_name: str) -> str:
        """
        Create file path for model.

        Args:
            table_name: Table name

        Returns:
            str: File path
        """
        return f"{self.models_directory}/{table_name}.py"

    def _create_column_specs(
        self, columns: list[Any], mixins: list[MixinType]
    ) -> list[ColumnSpec]:
        """
        Create column specifications.

        Args:
            columns: List of ColumnSchema
            mixins: Selected mixins

        Returns:
            list[ColumnSpec]: Column specifications
        """
        specs = []

        # Check what columns mixins provide
        mixin_columns = set()
        if MixinType.TIMESTAMP in mixins:
            mixin_columns.update(["created_at", "updated_at"])
        if MixinType.SOFT_DELETE in mixins:
            mixin_columns.update(["is_deleted", "deleted_at"])

        for column in columns:
            # Skip columns provided by mixins
            if column.name in mixin_columns:
                continue

            # Convert column type to SQLAlchemy type
            sa_type, args = self._convert_column_type(column)

            # Build kwargs
            kwargs = {}

            if column.primary_key:
                kwargs["primary_key"] = True
            if column.autoincrement:
                kwargs["autoincrement"] = True
            if column.unique:
                kwargs["unique"] = True
            if not column.nullable:
                kwargs["nullable"] = False
            if column.index:
                kwargs["index"] = True
            if column.default is not None:
                kwargs["default"] = column.default

            # Handle ForeignKey
            if column.type == ColumnType.FOREIGN_KEY and column.target:
                target = column.target
                ondelete = column.on_delete.value if column.on_delete else "NO ACTION"
                # For ForeignKey, use Integer type with ForeignKey constraint
                sa_type = "Integer"
                args = []
                kwargs["nullable"] = column.nullable
                # We'll add ForeignKey as a separate constraint in kwargs
                # Format: ForeignKey('table.column', ondelete='CASCADE')
                kwargs["foreign_key"] = f"{target}"
                kwargs["on_delete"] = ondelete

            spec = ColumnSpec(
                name=column.name,
                type=sa_type,
                args=args,
                kwargs=kwargs,
                comment=column.description,
            )

            specs.append(spec)

        return specs

    def _convert_column_type(self, column: Any) -> tuple[str, list[Any]]:
        """
        Convert schema column type to SQLAlchemy type.

        Args:
            column: ColumnSchema

        Returns:
            tuple: (type_name, args)
        """
        col_type = column.type
        args = []

        type_map = {
            ColumnType.INTEGER: "Integer",
            ColumnType.STRING: "String",
            ColumnType.TEXT: "Text",
            ColumnType.BOOLEAN: "Boolean",
            ColumnType.DATETIME: "DateTime",
            ColumnType.DATE: "Date",
            ColumnType.TIME: "Time",
            ColumnType.FLOAT: "Float",
            ColumnType.NUMERIC: "Numeric",
            ColumnType.ENUM: "Enum",
        }

        sa_type = type_map.get(col_type, "String")

        # Add type-specific args
        if col_type == ColumnType.STRING and column.length:
            args.append(column.length)
        elif col_type == ColumnType.NUMERIC:
            if column.precision:
                args.append(column.precision)
            if column.scale:
                args.append(column.scale)
        elif col_type == ColumnType.ENUM and column.values:
            args.extend(column.values)
            # Add name for enum
            args.append(f"{column.name}_enum")

        return sa_type, args

    def _create_relationship_specs(self, relationships: list[Any]) -> list[RelationshipSpec]:
        """
        Create relationship specifications.

        Args:
            relationships: List of RelationshipSchema

        Returns:
            list[RelationshipSpec]: Relationship specifications
        """
        specs = []

        for rel in relationships:
            # Determine relationship attribute name
            # For many-to-one: Use singular form from back_populates
            # For one-to-many: Use plural form from target_table
            if rel.type == RelationshipType.MANY_TO_ONE:
                name = rel.back_populates
            else:
                name = rel.target_table

            spec = RelationshipSpec(
                name=name,
                target_class=rel.target_class,
                relationship_type=rel.type.value,
                back_populates=rel.back_populates,
                foreign_key=rel.foreign_key,
            )

            specs.append(spec)

        return specs

    def _determine_dependencies(self, table: Any, schema: ProjectSchema) -> list[str]:
        """
        Determine which tables this table depends on.

        Args:
            table: TableSchema
            schema: ProjectSchema

        Returns:
            list[str]: List of table names this depends on
        """
        dependencies = set()

        # Check ForeignKey columns
        for column in table.columns:
            if column.type == ColumnType.FOREIGN_KEY and column.target:
                target_table = column.target.split(".")[0]
                if target_table != table.table_name:  # Exclude self-references
                    dependencies.add(target_table)

        return sorted(list(dependencies))

    def _generate_imports(
        self, table: Any, mixins: list[MixinType], relationships: list[RelationshipSpec]
    ) -> list[ImportStatement]:
        """
        Generate required import statements.

        Args:
            table: TableSchema
            mixins: Selected mixins
            relationships: Relationship specs

        Returns:
            list[ImportStatement]: Import statements
        """
        imports = []

        # SQLAlchemy imports
        sa_types = set()
        for column in table.columns:
            if column.type == ColumnType.FOREIGN_KEY:
                sa_types.add("Integer")
                sa_types.add("ForeignKey")
            else:
                sa_type, _ = self._convert_column_type(column)
                sa_types.add(sa_type)

        sa_types.add("Column")

        if sa_types:
            imports.append(
                ImportStatement(
                    module="sqlalchemy", items=sorted(list(sa_types))
                )
            )

        # Relationship import
        if relationships:
            imports.append(
                ImportStatement(module="sqlalchemy.orm", items=["relationship"])
            )

        # Base import
        imports.append(ImportStatement(module="app.core.database", items=["Base"]))

        # Mixin imports
        if mixins:
            mixin_names = [mixin.value for mixin in mixins]
            imports.append(
                ImportStatement(module="app.models.mixins", items=mixin_names)
            )

        # DateTime import if needed (and not using TimestampMixin)
        has_datetime = any(
            col.type == ColumnType.DATETIME for col in table.columns
        )
        if has_datetime and MixinType.TIMESTAMP not in mixins:
            imports.append(
                ImportStatement(module="datetime", items=["datetime"])
            )

        return imports

    def _generate_notes(self, schema: ProjectSchema, models: list[ModelSpec]) -> list[str]:
        """
        Generate helpful notes about the architecture.

        Args:
            schema: ProjectSchema
            models: List of ModelSpec

        Returns:
            list[str]: Notes
        """
        notes = []

        # Check for composite primary keys
        for model in models:
            pk_cols = [col for col in model.columns if col.kwargs.get("primary_key")]
            if len(pk_cols) > 1:
                notes.append(
                    f"{model.class_name} has composite primary key: "
                    f"{', '.join([col.name for col in pk_cols])}"
                )

        # Check for self-referential relationships
        for model in models:
            for rel in model.relationships:
                if rel.target_class == model.class_name:
                    notes.append(
                        f"{model.class_name} has self-referential relationship: {rel.name}"
                    )

        # Check for many-to-many (would need association table)
        for model in models:
            for rel in model.relationships:
                if rel.relationship_type == RelationshipType.MANY_TO_MANY.value:
                    notes.append(
                        f"{model.class_name} has many-to-many relationship with {rel.target_class} "
                        f"- association table may be needed"
                    )

        return notes

    async def validate_input(self, input_data: Any) -> bool:
        """Validate that input contains required fields."""
        if not isinstance(input_data, dict):
            logger.error("Input must be a dictionary")
            return False

        if "validated_schema" not in input_data:
            logger.error("Input must contain 'validated_schema' key")
            return False

        return True
