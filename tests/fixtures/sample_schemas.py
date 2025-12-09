"""
Sample schemas for testing.
"""

import json

# Valid simple schema
VALID_SIMPLE_SCHEMA = {
    "project_name": "TestProject",
    "db_type": "postgresql",
    "description": "A simple test schema",
    "schema": [
        {
            "table_name": "users",
            "class_name": "User",
            "description": "User accounts",
            "options": {"use_timestamps": True, "use_soft_delete": False},
            "columns": [
                {
                    "name": "id",
                    "type": "Integer",
                    "primary_key": True,
                    "autoincrement": True,
                    "nullable": False,
                },
                {
                    "name": "username",
                    "type": "String",
                    "length": 50,
                    "unique": True,
                    "nullable": False,
                },
                {
                    "name": "email",
                    "type": "String",
                    "length": 100,
                    "unique": True,
                    "nullable": False,
                },
            ],
            "relationships": [],
        }
    ],
}

# Valid schema with relationships
VALID_SCHEMA_WITH_RELATIONSHIPS = {
    "project_name": "BlogProject",
    "db_type": "postgresql",
    "schema": [
        {
            "table_name": "users",
            "class_name": "User",
            "options": {"use_timestamps": True, "use_soft_delete": False},
            "columns": [
                {
                    "name": "id",
                    "type": "Integer",
                    "primary_key": True,
                    "autoincrement": True,
                    "nullable": False,
                }
            ],
            "relationships": [
                {
                    "target_table": "posts",
                    "target_class": "Post",
                    "type": "one_to_many",
                    "back_populates": "author",
                }
            ],
        },
        {
            "table_name": "posts",
            "class_name": "Post",
            "options": {"use_timestamps": True, "use_soft_delete": True},
            "columns": [
                {
                    "name": "id",
                    "type": "Integer",
                    "primary_key": True,
                    "autoincrement": True,
                    "nullable": False,
                },
                {
                    "name": "author_id",
                    "type": "ForeignKey",
                    "target": "users.id",
                    "nullable": False,
                },
            ],
            "relationships": [
                {
                    "target_table": "users",
                    "target_class": "User",
                    "type": "many_to_one",
                    "back_populates": "posts",
                    "foreign_key": "author_id",
                }
            ],
        },
    ],
}

# Schema with circular dependency
CIRCULAR_DEPENDENCY_SCHEMA = {
    "project_name": "CircularTest",
    "db_type": "postgresql",
    "schema": [
        {
            "table_name": "table_a",
            "class_name": "TableA",
            "options": {"use_timestamps": False, "use_soft_delete": False},
            "columns": [
                {
                    "name": "id",
                    "type": "Integer",
                    "primary_key": True,
                    "nullable": False,
                },
                {
                    "name": "b_id",
                    "type": "ForeignKey",
                    "target": "table_b.id",
                    "nullable": True,
                },
            ],
            "relationships": [],
        },
        {
            "table_name": "table_b",
            "class_name": "TableB",
            "options": {"use_timestamps": False, "use_soft_delete": False},
            "columns": [
                {
                    "name": "id",
                    "type": "Integer",
                    "primary_key": True,
                    "nullable": False,
                },
                {
                    "name": "a_id",
                    "type": "ForeignKey",
                    "target": "table_a.id",
                    "nullable": True,
                },
            ],
            "relationships": [],
        },
    ],
}

# Invalid schema - missing primary key
INVALID_NO_PRIMARY_KEY = {
    "project_name": "InvalidProject",
    "db_type": "postgresql",
    "schema": [
        {
            "table_name": "users",
            "class_name": "User",
            "options": {"use_timestamps": False, "use_soft_delete": False},
            "columns": [
                {"name": "username", "type": "String", "length": 50, "nullable": False}
            ],
            "relationships": [],
        }
    ],
}

# Invalid schema - bad foreign key reference
INVALID_FK_REFERENCE = {
    "project_name": "InvalidFK",
    "db_type": "postgresql",
    "schema": [
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
                    "target": "users.id",  # users table doesn't exist
                    "nullable": False,
                },
            ],
            "relationships": [],
        }
    ],
}

# Invalid JSON syntax
INVALID_JSON_SYNTAX = '{"project_name": "Test", "schema": [}'

# Helper functions
def get_schema_as_json(schema: dict) -> str:
    """Convert schema dict to JSON string."""
    return json.dumps(schema, indent=2)


def get_valid_simple_json() -> str:
    """Get valid simple schema as JSON string."""
    return get_schema_as_json(VALID_SIMPLE_SCHEMA)


def get_valid_with_relationships_json() -> str:
    """Get valid schema with relationships as JSON string."""
    return get_schema_as_json(VALID_SCHEMA_WITH_RELATIONSHIPS)


def get_circular_dependency_json() -> str:
    """Get circular dependency schema as JSON string."""
    return get_schema_as_json(CIRCULAR_DEPENDENCY_SCHEMA)


def get_invalid_no_pk_json() -> str:
    """Get invalid schema (no PK) as JSON string."""
    return get_schema_as_json(INVALID_NO_PRIMARY_KEY)


def get_invalid_fk_json() -> str:
    """Get invalid schema (bad FK) as JSON string."""
    return get_schema_as_json(INVALID_FK_REFERENCE)
