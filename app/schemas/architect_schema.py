"""
Pydantic schemas for Architect Agent output.
These schemas define the architectural plan for code generation.
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MixinType(str, Enum):
    """Available mixin types."""

    TIMESTAMP = "TimestampMixin"
    SOFT_DELETE = "SoftDeleteMixin"
    # Future mixins can be added here
    # AUDIT = "AuditMixin"
    # UUID = "UUIDMixin"


class ColumnSpec(BaseModel):
    """Specification for a single column."""

    name: str = Field(..., description="Column name")
    type: str = Field(..., description="SQLAlchemy column type")
    args: list[Any] = Field(default_factory=list, description="Column type arguments (e.g., length)")
    kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Column keyword arguments (nullable, unique, etc.)"
    )
    comment: str | None = Field(None, description="Column comment/description")


class RelationshipSpec(BaseModel):
    """Specification for a relationship."""

    name: str = Field(..., description="Relationship attribute name")
    target_class: str = Field(..., description="Target model class name")
    relationship_type: str = Field(..., description="Relationship type (one-to-many, etc.)")
    back_populates: str = Field(..., description="Back populates attribute name")
    foreign_key: str | None = Field(None, description="Foreign key column name (for many-to-one)")
    kwargs: dict[str, Any] = Field(
        default_factory=dict, description="Additional relationship arguments"
    )


class ImportStatement(BaseModel):
    """Python import statement."""

    module: str = Field(..., description="Module to import from")
    items: list[str] = Field(..., description="Items to import")
    alias: str | None = Field(None, description="Import alias")

    def to_string(self) -> str:
        """Convert to Python import string."""
        if self.alias:
            return f"from {self.module} import {', '.join(self.items)} as {self.alias}"
        return f"from {self.module} import {', '.join(self.items)}"


class ModelSpec(BaseModel):
    """Complete specification for a single model."""

    # Basic info
    table_name: str = Field(..., description="Database table name")
    class_name: str = Field(..., description="Python class name")
    file_path: str = Field(..., description="File path for this model (relative to project root)")

    # Inheritance
    base_classes: list[str] = Field(
        default_factory=list, description="Base classes to inherit from (in order)"
    )
    mixins: list[MixinType] = Field(default_factory=list, description="Mixins to include")

    # Table configuration
    table_args: dict[str, Any] = Field(
        default_factory=dict, description="SQLAlchemy __table_args__"
    )

    # Columns and relationships
    columns: list[ColumnSpec] = Field(..., description="Column specifications")
    relationships: list[RelationshipSpec] = Field(
        default_factory=list, description="Relationship specifications"
    )

    # Imports
    imports: list[ImportStatement] = Field(
        default_factory=list, description="Required import statements"
    )

    # Metadata
    description: str | None = Field(None, description="Model description/docstring")
    depends_on: list[str] = Field(
        default_factory=list, description="Tables this model depends on"
    )

    @property
    def inheritance_chain(self) -> str:
        """Get inheritance chain as string."""
        if not self.base_classes:
            return ""
        return f"({', '.join(self.base_classes)})"

    def get_all_imports(self) -> list[str]:
        """Get all import statements as strings."""
        return [imp.to_string() for imp in self.imports]


class ArchitecturePlan(BaseModel):
    """Complete architectural plan for code generation."""

    # Project info
    project_name: str = Field(..., description="Project name")
    db_type: str = Field(..., description="Database type")
    description: str | None = Field(None, description="Project description")

    # Build order
    build_order: list[str] = Field(..., description="Order to create models (table names)")

    # Model specifications
    models: list[ModelSpec] = Field(..., description="Specifications for each model")

    # Project structure
    output_directory: str = Field(
        default="./generated", description="Output directory for generated code"
    )
    models_directory: str = Field(
        default="app/models", description="Directory for model files (relative to output)"
    )

    # Metadata
    validation_summary: str | None = Field(
        None, description="Summary from schema validation"
    )
    notes: list[str] = Field(default_factory=list, description="Additional notes or warnings")

    def get_model_by_table(self, table_name: str) -> ModelSpec | None:
        """Get model spec by table name."""
        for model in self.models:
            if model.table_name == table_name:
                return model
        return None

    def get_model_by_class(self, class_name: str) -> ModelSpec | None:
        """Get model spec by class name."""
        for model in self.models:
            if model.class_name == class_name:
                return model
        return None

    @property
    def total_models(self) -> int:
        """Total number of models."""
        return len(self.models)

    @property
    def total_columns(self) -> int:
        """Total number of columns across all models."""
        return sum(len(model.columns) for model in self.models)

    @property
    def total_relationships(self) -> int:
        """Total number of relationships."""
        return sum(len(model.relationships) for model in self.models)

    def to_summary_string(self) -> str:
        """Convert plan to summary string."""
        lines = [
            "=" * 80,
            "ARCHITECTURE PLAN",
            "=" * 80,
            "",
            f"Project: {self.project_name}",
            f"Database: {self.db_type}",
            f"Output: {self.output_directory}/{self.models_directory}",
            "",
            f"Total Models: {self.total_models}",
            f"Total Columns: {self.total_columns}",
            f"Total Relationships: {self.total_relationships}",
            "",
            "=" * 80,
            "BUILD ORDER",
            "=" * 80,
            "",
        ]

        for i, table_name in enumerate(self.build_order, 1):
            model = self.get_model_by_table(table_name)
            if model:
                deps = f" (depends on: {', '.join(model.depends_on)})" if model.depends_on else ""
                mixins = f" [Mixins: {', '.join([m.value for m in model.mixins])}]" if model.mixins else ""
                lines.append(f"  {i}. {model.class_name} → {model.file_path}{deps}{mixins}")

        lines.append("")

        if self.notes:
            lines.extend(
                [
                    "=" * 80,
                    "NOTES",
                    "=" * 80,
                    "",
                ]
            )
            for note in self.notes:
                lines.append(f"  • {note}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def to_detailed_string(self) -> str:
        """Convert plan to detailed string with all model specs."""
        lines = [self.to_summary_string(), "", "=" * 80, "MODEL SPECIFICATIONS", "=" * 80, ""]

        for i, model in enumerate(self.models, 1):
            lines.extend(
                [
                    f"{i}. {model.class_name} ({model.table_name})",
                    f"   File: {model.file_path}",
                    f"   Inheritance: {model.inheritance_chain or 'None'}",
                ]
            )

            if model.mixins:
                lines.append(f"   Mixins: {', '.join([m.value for m in model.mixins])}")

            lines.append(f"   Columns: {len(model.columns)}")
            for col in model.columns:
                lines.append(f"     - {col.name}: {col.type}")

            if model.relationships:
                lines.append(f"   Relationships: {len(model.relationships)}")
                for rel in model.relationships:
                    lines.append(f"     - {rel.name} → {rel.target_class} ({rel.relationship_type})")

            if model.imports:
                lines.append(f"   Imports: {len(model.imports)}")
                for imp in model.imports[:3]:  # Show first 3
                    lines.append(f"     - {imp.to_string()}")
                if len(model.imports) > 3:
                    lines.append(f"     ... and {len(model.imports) - 3} more")

            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)
