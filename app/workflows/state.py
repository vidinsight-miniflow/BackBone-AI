"""
Workflow state definitions for LangGraph.
"""

from typing import Any, Dict, List, Optional, TypedDict


class WorkflowState(TypedDict, total=False):
    """
    State passed between workflow nodes.

    This TypedDict defines the shared state that flows through the entire
    code generation pipeline. Each agent reads from and writes to this state.
    """

    # Input
    raw_input: Dict[str, Any]  # Original JSON schema from user
    project_name: str
    db_type: str

    # Stage 1: Schema Validation
    validation_report: Optional[Dict[str, Any]]
    validation_passed: bool
    validation_errors: List[str]
    parsed_schema: Optional[Dict[str, Any]]

    # Stage 2: Architecture Planning
    architecture_plan: Optional[Dict[str, Any]]
    build_order: List[str]

    # Stage 3: Code Generation
    generated_files: Dict[str, str]  # {file_path: content}
    generation_summary: Optional[Dict[str, Any]]

    # Metadata
    current_stage: str  # "validation", "planning", "generation", "complete"
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class ValidationState(TypedDict):
    """State for schema validation stage."""
    raw_input: Dict[str, Any]
    validation_report: Dict[str, Any]
    validation_passed: bool
    validation_errors: List[str]
    parsed_schema: Dict[str, Any]


class ArchitectureState(TypedDict):
    """State for architecture planning stage."""
    parsed_schema: Dict[str, Any]
    architecture_plan: Dict[str, Any]
    build_order: List[str]


class GenerationState(TypedDict):
    """State for code generation stage."""
    architecture_plan: Dict[str, Any]
    generated_files: Dict[str, str]
    generation_summary: Dict[str, Any]
