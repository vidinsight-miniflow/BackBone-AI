"""
Schema Validator Agent.

This agent validates JSON schema definitions using specialized tools.
It performs comprehensive validation including structure, foreign keys, and dependencies.
"""

import json
from typing import Any

from langchain_core.language_models import BaseChatModel

from app.agents.base_agent import BaseAgent
from app.core.logger import get_logger
from app.prompts.validator_prompts import (
    SCHEMA_VALIDATOR_SIMPLE_PROMPT,
    SCHEMA_VALIDATOR_SYSTEM_PROMPT,
)
from app.schemas.agent_output_schema import (
    SchemaValidatorOutput,
    ValidationErrorDetail,
    ValidationInfoDetail,
    ValidationStatus,
    ValidationWarningDetail,
)
from app.schemas.validation_schema import ValidationSeverity
from app.tools.json_tools import JSONValidatorTool, SchemaParserTool
from app.tools.relationship_tools import DependencyAnalyzerTool, ForeignKeyCheckerTool

logger = get_logger(__name__)


class SchemaValidatorAgent(BaseAgent):
    """
    Agent for validating JSON schema definitions.

    This agent orchestrates multiple validation tools to provide
    comprehensive schema validation including:
    - JSON syntax and structure
    - Foreign key references
    - Table dependencies and build order
    """

    def __init__(
        self,
        llm: BaseChatModel | None = None,
        use_llm: bool = False,
    ):
        """
        Initialize Schema Validator Agent.

        Args:
            llm: Language model instance (optional, for LLM-enhanced validation)
            use_llm: Whether to use LLM for enhanced validation (default: False)
        """
        super().__init__(
            name="schema_validator",
            llm=llm if llm else self._create_dummy_llm(),
            system_prompt=SCHEMA_VALIDATOR_SYSTEM_PROMPT,
        )

        self.use_llm = use_llm and llm is not None

        # Initialize tools
        self.json_validator = JSONValidatorTool()
        self.schema_parser = SchemaParserTool()
        self.fk_checker = ForeignKeyCheckerTool()
        self.dependency_analyzer = DependencyAnalyzerTool()

        logger.info(
            f"Schema Validator Agent initialized (LLM mode: {'enabled' if self.use_llm else 'disabled'})"
        )

    def _create_dummy_llm(self) -> Any:
        """Create a dummy LLM for non-LLM mode."""
        # Return a dummy object that satisfies the type checker
        class DummyLLM:
            pass

        return DummyLLM()  # type: ignore

    def _default_system_prompt(self) -> str:
        """Default system prompt for the agent."""
        return SCHEMA_VALIDATOR_SYSTEM_PROMPT

    async def execute(self, input_data: dict[str, Any]) -> dict[str, Any]:
        """
        Execute schema validation.

        Args:
            input_data: Dict with 'schema' key containing JSON string

        Returns:
            dict: SchemaValidatorOutput as dictionary
        """
        json_content = input_data.get("schema")

        if not json_content:
            raise ValueError("Input must contain 'schema' key with JSON content")

        logger.info("Starting schema validation")

        # Step 1: Validate JSON structure
        logger.info("Step 1: Validating JSON structure")
        json_validation = self.json_validator._run(json_content)
        logger.debug(f"JSON validation result: {json_validation['valid']}")

        # If JSON is invalid, return early
        if not json_validation["valid"]:
            return self._create_failed_output(
                summary="JSON validation failed",
                json_validation=json_validation,
            ).model_dump()

        # Step 2: Parse schema
        logger.info("Step 2: Parsing schema")
        try:
            parsed_schema = self.schema_parser._run(json_content)
        except Exception as e:
            logger.error(f"Schema parsing failed: {e}")
            return self._create_failed_output(
                summary="Schema parsing failed",
                json_validation=json_validation,
                parse_error=str(e),
            ).model_dump()

        # Step 3: Validate foreign keys
        logger.info("Step 3: Validating foreign keys")
        fk_validation = self.fk_checker._run(parsed_schema)
        logger.debug(f"FK validation result: {fk_validation['valid']}")

        # Step 4: Analyze dependencies
        logger.info("Step 4: Analyzing dependencies")
        dependency_analysis = self.dependency_analyzer._run(parsed_schema)
        logger.debug(f"Dependency analysis result: {dependency_analysis['valid']}")

        # Step 5: Compile results
        logger.info("Step 5: Compiling validation results")
        output = self._compile_results(
            json_validation=json_validation,
            fk_validation=fk_validation,
            dependency_analysis=dependency_analysis,
        )

        logger.info(
            f"Validation complete: {output.validation_status.value} "
            f"(Errors: {len(output.errors)}, Warnings: {len(output.warnings)})"
        )

        return output.model_dump()

    def _compile_results(
        self,
        json_validation: dict,
        fk_validation: dict,
        dependency_analysis: dict,
    ) -> SchemaValidatorOutput:
        """
        Compile all validation results into a single output.

        Args:
            json_validation: JSON validation results
            fk_validation: Foreign key validation results
            dependency_analysis: Dependency analysis results

        Returns:
            SchemaValidatorOutput: Compiled validation output
        """
        errors: list[ValidationErrorDetail] = []
        warnings: list[ValidationWarningDetail] = []
        info: list[ValidationInfoDetail] = []
        recommendations: list[str] = []

        # Process JSON validation issues
        for issue in json_validation.get("issues", []):
            if issue["severity"] == ValidationSeverity.ERROR.value:
                errors.append(
                    ValidationErrorDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                        recommendation=self._get_recommendation_for_issue(issue),
                    )
                )
            elif issue["severity"] == ValidationSeverity.WARNING.value:
                warnings.append(
                    ValidationWarningDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                        recommendation=self._get_recommendation_for_issue(issue),
                    )
                )
            elif issue["severity"] == ValidationSeverity.INFO.value:
                info.append(
                    ValidationInfoDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                    )
                )

        # Process FK validation issues
        for issue in fk_validation.get("issues", []):
            if issue["severity"] == ValidationSeverity.ERROR.value:
                errors.append(
                    ValidationErrorDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                        recommendation=self._get_recommendation_for_issue(issue),
                    )
                )
            elif issue["severity"] == ValidationSeverity.WARNING.value:
                warnings.append(
                    ValidationWarningDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                        recommendation=self._get_recommendation_for_issue(issue),
                    )
                )

        # Process dependency analysis issues
        for issue in dependency_analysis.get("issues", []):
            if issue["severity"] == ValidationSeverity.ERROR.value:
                errors.append(
                    ValidationErrorDetail(
                        message=issue["message"],
                        location=issue.get("location"),
                        recommendation=self._get_recommendation_for_issue(issue),
                    )
                )

        # Determine overall status
        schema_valid = json_validation["valid"]
        fk_valid = fk_validation["valid"]
        deps_valid = dependency_analysis["valid"]

        all_valid = schema_valid and fk_valid and deps_valid
        validation_status = ValidationStatus.PASS if all_valid else ValidationStatus.FAIL

        # Create summary
        summary = self._create_summary(schema_valid, fk_valid, deps_valid, errors, warnings)

        # Add general recommendations
        recommendations.extend(self._generate_recommendations(warnings, info))

        return SchemaValidatorOutput(
            validation_status=validation_status,
            summary=summary,
            schema_valid=schema_valid,
            foreign_keys_valid=fk_valid,
            dependencies_valid=deps_valid,
            build_order=dependency_analysis.get("build_order", []),
            errors=errors,
            warnings=warnings,
            info=info,
            recommendations=recommendations,
            tool_outputs={
                "json_validation": json_validation,
                "fk_validation": fk_validation,
                "dependency_analysis": dependency_analysis,
            },
        )

    def _create_failed_output(
        self,
        summary: str,
        json_validation: dict | None = None,
        parse_error: str | None = None,
    ) -> SchemaValidatorOutput:
        """Create a failed validation output."""
        errors: list[ValidationErrorDetail] = []

        if json_validation:
            for issue in json_validation.get("issues", []):
                if issue["severity"] == ValidationSeverity.ERROR.value:
                    errors.append(
                        ValidationErrorDetail(
                            message=issue["message"],
                            location=issue.get("location"),
                            recommendation=self._get_recommendation_for_issue(issue),
                        )
                    )

        if parse_error:
            errors.append(
                ValidationErrorDetail(
                    message=f"Schema parsing error: {parse_error}",
                    recommendation="Fix JSON structure and syntax errors first",
                )
            )

        return SchemaValidatorOutput(
            validation_status=ValidationStatus.FAIL,
            summary=summary,
            schema_valid=False,
            foreign_keys_valid=False,
            dependencies_valid=False,
            build_order=[],
            errors=errors,
            warnings=[],
            info=[],
            recommendations=["Fix critical errors before proceeding"],
            tool_outputs={"json_validation": json_validation} if json_validation else {},
        )

    def _create_summary(
        self,
        schema_valid: bool,
        fk_valid: bool,
        deps_valid: bool,
        errors: list,
        warnings: list,
    ) -> str:
        """Create a summary string."""
        if schema_valid and fk_valid and deps_valid:
            if warnings:
                return f"Schema validation passed with {len(warnings)} warning(s)"
            return "Schema validation passed successfully"
        else:
            failed_checks = []
            if not schema_valid:
                failed_checks.append("structure")
            if not fk_valid:
                failed_checks.append("foreign keys")
            if not deps_valid:
                failed_checks.append("dependencies")

            return f"Validation failed: {', '.join(failed_checks)} ({len(errors)} error(s))"

    def _get_recommendation_for_issue(self, issue: dict) -> str:
        """Generate recommendation based on issue code."""
        code = issue.get("code", "")

        recommendations = {
            "JSON_SYNTAX_ERROR": "Fix JSON syntax errors. Use a JSON validator or linter.",
            "SCHEMA_VALIDATION_ERROR": "Review the error message and correct the schema structure.",
            "FK_TABLE_NOT_FOUND": "Ensure the referenced table is defined in the schema.",
            "FK_COLUMN_NOT_FOUND": "Check that the target column exists in the referenced table.",
            "FK_NOT_PK_OR_UNIQUE": "Foreign keys should reference primary key or unique columns.",
            "CIRCULAR_DEPENDENCY": "Remove circular foreign key references. Consider using nullable FKs or restructuring relationships.",
            "STRING_NO_LENGTH": "Specify a length for String columns, e.g., 'length': 100",
            "NO_RELATIONSHIPS": "Consider adding relationships if this table relates to others.",
            "TOO_MANY_COLUMNS": "Consider normalizing the table by splitting it into multiple tables.",
        }

        return recommendations.get(code, "Review the validation message and make necessary corrections.")

    def _generate_recommendations(
        self, warnings: list, info: list
    ) -> list[str]:
        """Generate general recommendations based on validation results."""
        recommendations = []

        if not warnings and not info:
            recommendations.append(
                "Schema is well-structured and follows best practices!"
            )

        if warnings:
            recommendations.append(
                "Address warnings to improve schema quality and prevent potential issues."
            )

        # Check for specific patterns in warnings
        warning_codes = [w.location for w in warnings if w.location]

        if any("String" in str(w) for w in warnings):
            recommendations.append(
                "Always specify length constraints for String columns to ensure database compatibility."
            )

        return recommendations

    async def validate_input(self, input_data: Any) -> bool:
        """Validate that input contains required schema field."""
        if not isinstance(input_data, dict):
            logger.error("Input must be a dictionary")
            return False

        if "schema" not in input_data:
            logger.error("Input must contain 'schema' key")
            return False

        if not isinstance(input_data["schema"], str):
            logger.error("Schema must be a string")
            return False

        return True
