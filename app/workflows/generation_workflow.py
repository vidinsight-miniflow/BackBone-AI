"""
Main code generation workflow using LangGraph.

This workflow orchestrates three agents in sequence:
1. Schema Validator Agent - validates JSON schema
2. Architect Agent - creates architectural plan
3. Code Generator Agent - generates SQLAlchemy models
"""

import json
from typing import Any, Dict

from langgraph.graph import END, START, StateGraph

from app.agents.architect_agent import ArchitectAgent
from app.agents.code_generator_agent import CodeGeneratorAgent
from app.agents.schema_validator_agent import SchemaValidatorAgent
from app.core.llm_factory import LLMFactory
from app.core.logger import get_logger
from app.workflows.state import WorkflowState

logger = get_logger(__name__)


class GenerationWorkflow:
    """
    LangGraph workflow for code generation.

    This workflow chains together validation, planning, and generation
    agents to transform a JSON schema into production-ready code.
    """

    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the generation workflow.

        Args:
            llm_provider: LLM provider name (openai, anthropic, google)
        """
        self.llm_provider = llm_provider
        self.llm = LLMFactory.create_llm(provider=llm_provider)

        # Initialize agents
        logger.info("Initializing agents for workflow")
        self.schema_validator = SchemaValidatorAgent(llm=self.llm, use_llm=False)
        self.architect = ArchitectAgent(llm=self.llm)
        self.code_generator = CodeGeneratorAgent(format_code=True)

        # Build workflow graph
        self.workflow = self._build_workflow()
        logger.info("Generation workflow initialized")

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow.

        Returns:
            Compiled StateGraph workflow
        """
        # Create state graph
        workflow = StateGraph(WorkflowState)

        # Add nodes (each represents an agent)
        workflow.add_node("validate_schema", self._validate_schema_node)
        workflow.add_node("plan_architecture", self._plan_architecture_node)
        workflow.add_node("generate_code", self._generate_code_node)

        # Define edges (workflow flow)
        workflow.add_edge(START, "validate_schema")

        # Conditional edge: only proceed if validation passed
        workflow.add_conditional_edges(
            "validate_schema",
            self._should_continue_after_validation,
            {
                "continue": "plan_architecture",
                "end": END,
            },
        )

        workflow.add_edge("plan_architecture", "generate_code")
        workflow.add_edge("generate_code", END)

        # Compile workflow
        return workflow.compile()

    async def _validate_schema_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Node 1: Validate JSON schema.

        Args:
            state: Current workflow state

        Returns:
            Updated state with validation results
        """
        logger.info("=" * 60)
        logger.info("STAGE 1: Schema Validation")
        logger.info("=" * 60)

        try:
            # Convert raw input to JSON string if it's a dict
            raw_input = state["raw_input"]
            if isinstance(raw_input, dict):
                schema_json = json.dumps(raw_input)
            else:
                schema_json = raw_input

            # Execute validation
            result = await self.schema_validator.execute({"schema": schema_json})

            # Update state
            validation_passed = result.get("status") == "passed"

            return {
                "validation_report": result,
                "validation_passed": validation_passed,
                "validation_errors": result.get("errors", []),
                "parsed_schema": result.get("validated_schema"),
                "current_stage": "validation",
                "errors": [] if validation_passed else [e["message"] for e in result.get("errors", [])],
                "warnings": [w["message"] for w in result.get("warnings", [])],
            }

        except Exception as e:
            logger.error(f"Validation failed with exception: {e}", exc_info=True)
            return {
                "validation_passed": False,
                "validation_errors": [str(e)],
                "current_stage": "validation",
                "errors": [str(e)],
            }

    def _should_continue_after_validation(self, state: WorkflowState) -> str:
        """
        Conditional edge: check if validation passed.

        Args:
            state: Current workflow state

        Returns:
            "continue" if validation passed, "end" otherwise
        """
        if state.get("validation_passed", False):
            logger.info("✅ Validation passed, continuing to architecture planning")
            return "continue"
        else:
            logger.error("❌ Validation failed, stopping workflow")
            return "end"

    async def _plan_architecture_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Node 2: Plan architecture.

        Args:
            state: Current workflow state

        Returns:
            Updated state with architecture plan
        """
        logger.info("=" * 60)
        logger.info("STAGE 2: Architecture Planning")
        logger.info("=" * 60)

        try:
            # Extract validation results
            validation_report = state["validation_report"]
            parsed_schema = state["parsed_schema"]

            # Get build order from validation report
            build_order = validation_report.get("dependency_analysis", {}).get("build_order", [])

            # Execute architecture planning
            result = await self.architect.execute({
                "validated_schema": parsed_schema,
                "build_order": build_order,
                "validation_summary": validation_report.get("summary", ""),
            })

            return {
                "architecture_plan": result,
                "build_order": build_order,
                "current_stage": "planning",
            }

        except Exception as e:
            logger.error(f"Architecture planning failed: {e}", exc_info=True)
            errors = state.get("errors", [])
            errors.append(f"Architecture planning error: {str(e)}")
            return {
                "errors": errors,
                "current_stage": "planning",
            }

    async def _generate_code_node(self, state: WorkflowState) -> Dict[str, Any]:
        """
        Node 3: Generate code.

        Args:
            state: Current workflow state

        Returns:
            Updated state with generated code
        """
        logger.info("=" * 60)
        logger.info("STAGE 3: Code Generation")
        logger.info("=" * 60)

        try:
            # Execute code generation
            result = await self.code_generator.execute({
                "architecture_plan": state["architecture_plan"]
            })

            return {
                "generated_files": result.get("generated_files", {}),
                "generation_summary": result.get("summary", {}),
                "current_stage": "complete",
            }

        except Exception as e:
            logger.error(f"Code generation failed: {e}", exc_info=True)
            errors = state.get("errors", [])
            errors.append(f"Code generation error: {str(e)}")
            return {
                "errors": errors,
                "current_stage": "generation",
            }

    async def run(self, json_schema: Dict[str, Any] | str) -> WorkflowState:
        """
        Run the complete workflow.

        Args:
            json_schema: JSON schema as dict or string

        Returns:
            Final workflow state with generated code
        """
        logger.info("🚀 Starting code generation workflow")

        # Parse input
        if isinstance(json_schema, str):
            raw_input = json.loads(json_schema)
        else:
            raw_input = json_schema

        # Extract metadata
        project_name = raw_input.get("project_name", "UnnamedProject")
        db_type = raw_input.get("db_type", "postgresql")

        logger.info(f"Project: {project_name}")
        logger.info(f"Database: {db_type}")

        # Initialize state
        initial_state: WorkflowState = {
            "raw_input": raw_input,
            "project_name": project_name,
            "db_type": db_type,
            "validation_passed": False,
            "validation_errors": [],
            "current_stage": "starting",
            "errors": [],
            "warnings": [],
            "metadata": {
                "llm_provider": self.llm_provider,
            },
        }

        # Execute workflow
        final_state = await self.workflow.ainvoke(initial_state)

        # Log results
        if final_state.get("errors"):
            logger.error(f"❌ Workflow completed with errors: {final_state['errors']}")
        else:
            num_files = len(final_state.get("generated_files", {}))
            logger.info(f"✅ Workflow completed successfully! Generated {num_files} files")

        return final_state

    async def validate_only(self, json_schema: Dict[str, Any] | str) -> Dict[str, Any]:
        """
        Run only the validation stage (for CLI validate command).

        Args:
            json_schema: JSON schema as dict or string

        Returns:
            Validation report
        """
        logger.info("🔍 Running validation only")

        # Convert to JSON string if needed
        if isinstance(json_schema, dict):
            schema_json = json.dumps(json_schema)
        else:
            schema_json = json_schema

        # Execute validation
        result = await self.schema_validator.execute({"schema": schema_json})

        return result
