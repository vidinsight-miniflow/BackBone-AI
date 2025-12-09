"""
Pydantic schemas for validating input JSON.
These schemas define the structure of the JSON schema that users provide.
"""

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ColumnType(str, Enum):
    """Supported column types."""

    INTEGER = "Integer"
    STRING = "String"
    TEXT = "Text"
    BOOLEAN = "Boolean"
    DATETIME = "DateTime"
    DATE = "Date"
    TIME = "Time"
    NUMERIC = "Numeric"
    FLOAT = "Float"
    ENUM = "Enum"
    FOREIGN_KEY = "ForeignKey"


class OnDeleteAction(str, Enum):
    """Foreign key on_delete actions."""

    CASCADE = "CASCADE"
    RESTRICT = "RESTRICT"
    SET_NULL = "SET NULL"
    SET_DEFAULT = "SET DEFAULT"
    NO_ACTION = "NO ACTION"


class RelationshipType(str, Enum):
    """Relationship types."""

    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class ColumnSchema(BaseModel):
    """Schema for a single column definition."""

    name: str = Field(..., description="Column name", min_length=1)
    type: ColumnType = Field(..., description="Column type")
    length: int | None = Field(None, description="Length for String types", gt=0)
    precision: int | None = Field(None, description="Precision for Numeric types", gt=0)
    scale: int | None = Field(None, description="Scale for Numeric types", ge=0)
    primary_key: bool = Field(False, description="Is this a primary key?")
    autoincrement: bool = Field(False, description="Auto-increment?")
    unique: bool = Field(False, description="Unique constraint?")
    nullable: bool = Field(True, description="Can be NULL?")
    index: bool = Field(False, description="Create index?")
    default: Any = Field(None, description="Default value")
    values: list[str] | None = Field(None, description="Enum values (for Enum type)")
    target: str | None = Field(
        None, description="Foreign key target (for ForeignKey type) e.g., 'users.id'"
    )
    on_delete: OnDeleteAction = Field(
        OnDeleteAction.NO_ACTION, description="On delete action for ForeignKey"
    )
    description: str | None = Field(None, description="Column description")

    @field_validator("length")
    @classmethod
    def validate_length(cls, v: int | None, info) -> int | None:
        """Validate that length is only provided for String types."""
        if v is not None and info.data.get("type") != ColumnType.STRING:
            raise ValueError("length can only be specified for String type columns")
        return v

    @field_validator("values")
    @classmethod
    def validate_enum_values(cls, v: list[str] | None, info) -> list[str] | None:
        """Validate that values are only provided for Enum types."""
        if v is not None and info.data.get("type") != ColumnType.ENUM:
            raise ValueError("values can only be specified for Enum type columns")
        if info.data.get("type") == ColumnType.ENUM and not v:
            raise ValueError("Enum type requires values to be specified")
        return v

    @field_validator("target")
    @classmethod
    def validate_foreign_key_target(cls, v: str | None, info) -> str | None:
        """Validate that target is only provided for ForeignKey types."""
        if v is not None and info.data.get("type") != ColumnType.FOREIGN_KEY:
            raise ValueError("target can only be specified for ForeignKey type columns")
        if info.data.get("type") == ColumnType.FOREIGN_KEY and not v:
            raise ValueError("ForeignKey type requires target to be specified")
        if v and "." not in v:
            raise ValueError(
                "ForeignKey target must be in format 'table_name.column_name'"
            )
        return v

    @model_validator(mode="after")
    def validate_primary_key_not_nullable(self):
        """Primary keys cannot be nullable."""
        if self.primary_key and self.nullable:
            raise ValueError("Primary key columns cannot be nullable")
        return self


class RelationshipSchema(BaseModel):
    """Schema for a relationship definition."""

    target_table: str = Field(..., description="Target table name", min_length=1)
    target_class: str = Field(..., description="Target class name", min_length=1)
    type: RelationshipType = Field(..., description="Relationship type")
    back_populates: str = Field(..., description="Back populates attribute name", min_length=1)
    foreign_key: str | None = Field(
        None, description="Foreign key column name (for many_to_one)"
    )
    description: str | None = Field(None, description="Relationship description")


class TableOptions(BaseModel):
    """Options for table configuration."""

    use_timestamps: bool = Field(
        False, description="Add TimestampMixin (created_at, updated_at)"
    )
    use_soft_delete: bool = Field(False, description="Add SoftDeleteMixin (is_deleted)")


class TableSchema(BaseModel):
    """Schema for a table definition."""

    table_name: str = Field(..., description="Database table name", min_length=1)
    class_name: str = Field(..., description="Python class name", min_length=1)
    description: str | None = Field(None, description="Table description")
    options: TableOptions = Field(default_factory=TableOptions, description="Table options")
    columns: list[ColumnSchema] = Field(..., description="Column definitions", min_length=1)
    relationships: list[RelationshipSchema] = Field(
        default_factory=list, description="Relationship definitions"
    )

    @field_validator("table_name")
    @classmethod
    def validate_table_name(cls, v: str) -> str:
        """Validate table name follows naming conventions."""
        if not v.islower():
            raise ValueError("table_name must be lowercase")
        if not v.replace("_", "").isalnum():
            raise ValueError("table_name must contain only alphanumeric characters and underscores")
        return v

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        """Validate class name follows Python naming conventions."""
        if not v[0].isupper():
            raise ValueError("class_name must start with an uppercase letter")
        if not v.replace("_", "").isalnum():
            raise ValueError("class_name must contain only alphanumeric characters and underscores")
        return v

    @model_validator(mode="after")
    def validate_primary_key_exists(self):
        """Each table must have at least one primary key."""
        has_pk = any(col.primary_key for col in self.columns)
        if not has_pk:
            raise ValueError(f"Table '{self.table_name}' must have at least one primary key column")
        return self


class DatabaseType(str, Enum):
    """Supported database types."""

    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLITE = "sqlite"
    MSSQL = "mssql"


class ProjectSchema(BaseModel):
    """Root schema for the entire project definition."""

    project_name: str = Field(..., description="Project name", min_length=1)
    db_type: DatabaseType = Field(..., description="Database type")
    description: str | None = Field(None, description="Project description")
    schema: list[TableSchema] = Field(..., description="Table schemas", min_length=1)

    @field_validator("project_name")
    @classmethod
    def validate_project_name(cls, v: str) -> str:
        """Validate project name."""
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "project_name must contain only alphanumeric characters, hyphens, and underscores"
            )
        return v

    @model_validator(mode="after")
    def validate_unique_table_names(self):
        """Table names must be unique."""
        table_names = [table.table_name for table in self.schema]
        if len(table_names) != len(set(table_names)):
            raise ValueError("Table names must be unique")
        return self

    @model_validator(mode="after")
    def validate_unique_class_names(self):
        """Class names must be unique."""
        class_names = [table.class_name for table in self.schema]
        if len(class_names) != len(set(class_names)):
            raise ValueError("Class names must be unique")
        return self
