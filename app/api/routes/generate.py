"""
Code generation API routes.
"""

import asyncio
from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.logger import get_logger
from app.core.rate_limit import limiter, rate_limit_generate, rate_limit_validation
from app.core.security import get_current_user
from app.core.validation import SecureRequestValidator, validate_project_schema
from app.workflows.generation_workflow import GenerationWorkflow

logger = get_logger(__name__)

# Create router
router = APIRouter(prefix="/api/v1", tags=["Generation"])


class GenerateRequest(BaseModel):
    """Request body for code generation."""

    schema: Dict = Field(..., description="Project schema in JSON format")
    enable_code_validation: bool = Field(
        default=True, description="Enable code quality validation"
    )
    strict_validation: bool = Field(
        default=False, description="Treat warnings as errors in validation"
    )


class GenerateResponse(BaseModel):
    """Response for code generation."""

    status: str
    project_name: str
    files_generated: int
    summary: Dict
    generated_files: Dict[str, str] = Field(
        default_factory=dict, description="Generated file contents"
    )
    errors: list = Field(default_factory=list)
    warnings: list = Field(default_factory=list)


class ValidateRequest(BaseModel):
    """Request body for schema validation."""

    schema: Dict = Field(..., description="Project schema in JSON format")


class ValidateResponse(BaseModel):
    """Response for schema validation."""

    status: str
    valid: bool
    errors: list = Field(default_factory=list)
    warnings: list = Field(default_factory=list)
    info: list = Field(default_factory=list)
    build_order: list = Field(default_factory=list)


@router.post(
    "/generate",
    response_model=GenerateResponse,
    summary="Generate code from schema",
    description="Generate SQLAlchemy models and backend code from JSON schema",
)
@limiter.limit("10/minute")  # Rate limiting
async def generate_code(
    request: GenerateRequest,
    current_user: Dict = Depends(get_current_user),  # Authentication
):
    """
    Generate backend code from JSON schema.

    This endpoint:
    1. Validates the schema
    2. Creates architectural plan
    3. Generates SQLAlchemy models
    4. Optionally validates generated code quality

    Rate limited to 10 requests per minute.
    Requires authentication if ENABLE_AUTH=true.
    """
    logger.info(f"Code generation request from user: {current_user.get('auth_type', 'none')}")

    try:
        # Validate request
        SecureRequestValidator.validate_generation_request(request.schema)
        validated_schema = validate_project_schema(request.schema)

        # Create workflow
        workflow = GenerationWorkflow(
            llm_provider=settings.default_llm_provider,
            enable_code_validation=request.enable_code_validation,
            strict_validation=request.strict_validation,
        )

        # Run workflow
        logger.info(f"Starting workflow for project: {validated_schema.get('project_name')}")
        final_state = await workflow.run(validated_schema)

        # Check for errors
        if final_state.get("errors"):
            logger.error(f"Workflow failed: {final_state['errors']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "message": "Code generation failed",
                    "errors": final_state["errors"],
                },
            )

        # Prepare response
        generated_files = final_state.get("generated_files", {})
        summary = final_state.get("generation_summary", {})

        response = GenerateResponse(
            status="success",
            project_name=final_state.get("project_name", "Unknown"),
            files_generated=len(generated_files),
            summary=summary,
            generated_files=generated_files,
            warnings=final_state.get("warnings", []),
        )

        logger.info(f"Code generation successful: {len(generated_files)} files generated")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Code generation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Code generation failed: {str(e)}",
        )


@router.post(
    "/validate",
    response_model=ValidateResponse,
    summary="Validate schema",
    description="Validate JSON schema without generating code",
)
@limiter.limit("50/minute")  # More permissive rate limit
async def validate_schema(
    request: ValidateRequest,
    current_user: Dict = Depends(get_current_user),
):
    """
    Validate JSON schema without generating code.

    This endpoint:
    1. Validates JSON structure
    2. Checks foreign key references
    3. Analyzes dependencies
    4. Returns build order

    Rate limited to 50 requests per minute.
    Requires authentication if ENABLE_AUTH=true.
    """
    logger.info(f"Validation request from user: {current_user.get('auth_type', 'none')}")

    try:
        # Validate request
        validated_schema = validate_project_schema(request.schema)

        # Create workflow
        workflow = GenerationWorkflow(llm_provider=settings.default_llm_provider)

        # Run validation only
        logger.info("Running schema validation")
        result = await workflow.validate_only(validated_schema)

        # Prepare response
        validation_status = result.get("status", "unknown")
        is_valid = validation_status in ["passed", "passed_with_warnings"]

        response = ValidateResponse(
            status=validation_status,
            valid=is_valid,
            errors=[e.get("message", str(e)) for e in result.get("errors", [])],
            warnings=[w.get("message", str(w)) for w in result.get("warnings", [])],
            info=[i.get("message", str(i)) for i in result.get("info", [])],
            build_order=result.get("dependency_analysis", {}).get("build_order", []),
        )

        logger.info(f"Validation complete: {validation_status}")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Validation error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}",
        )


@router.get("/status", summary="Get API status")
async def get_status():
    """
    Get API status and configuration.

    Returns current API status, authentication state, and rate limits.
    """
    return {
        "status": "operational",
        "version": settings.app_version,
        "environment": settings.app_env,
        "authentication_enabled": settings.enable_auth,
        "metrics_enabled": settings.enable_metrics,
        "rate_limits": {
            "generation": "10/minute",
            "validation": "50/minute",
        },
    }
