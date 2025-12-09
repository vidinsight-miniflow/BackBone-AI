"""
Pytest configuration and fixtures.
"""

import sys
from pathlib import Path

import pytest

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def sample_valid_schema():
    """Provide a valid sample schema."""
    from tests.fixtures.sample_schemas import VALID_SIMPLE_SCHEMA

    return VALID_SIMPLE_SCHEMA


@pytest.fixture
def sample_schema_with_relationships():
    """Provide a schema with relationships."""
    from tests.fixtures.sample_schemas import VALID_SCHEMA_WITH_RELATIONSHIPS

    return VALID_SCHEMA_WITH_RELATIONSHIPS


@pytest.fixture
def sample_circular_schema():
    """Provide a schema with circular dependencies."""
    from tests.fixtures.sample_schemas import CIRCULAR_DEPENDENCY_SCHEMA

    return CIRCULAR_DEPENDENCY_SCHEMA
