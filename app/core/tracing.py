"""
LangSmith tracing configuration and utilities.
"""

import os
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def setup_langsmith_tracing() -> bool:
    """
    Setup LangSmith tracing if enabled.

    Sets environment variables for LangSmith to enable tracing.

    Returns:
        bool: True if tracing was enabled, False otherwise
    """
    if not settings.langchain_tracing_v2:
        logger.info("LangSmith tracing is disabled")
        return False

    if not settings.langchain_api_key:
        logger.warning(
            "LangSmith tracing enabled but LANGCHAIN_API_KEY not set. "
            "Tracing will not work."
        )
        return False

    # Set environment variables for LangSmith
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_ENDPOINT"] = settings.langchain_endpoint
    os.environ["LANGCHAIN_API_KEY"] = settings.langchain_api_key
    os.environ["LANGCHAIN_PROJECT"] = settings.langchain_project

    logger.info(
        f"LangSmith tracing enabled. Project: {settings.langchain_project}, "
        f"Endpoint: {settings.langchain_endpoint}"
    )

    return True


def create_run_metadata(
    user_id: Optional[str] = None,
    request_id: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """
    Create metadata for LangSmith run.

    Args:
        user_id: Optional user ID
        request_id: Optional request ID
        **kwargs: Additional metadata

    Returns:
        Dictionary of metadata
    """
    metadata = {
        "environment": settings.app_env,
        "version": settings.app_version,
    }

    if user_id:
        metadata["user_id"] = user_id

    if request_id:
        metadata["request_id"] = request_id

    metadata.update(kwargs)

    return metadata


def get_tracing_status() -> Dict[str, Any]:
    """
    Get current tracing status.

    Returns:
        Dictionary with tracing configuration
    """
    return {
        "enabled": settings.langchain_tracing_v2,
        "endpoint": settings.langchain_endpoint if settings.langchain_tracing_v2 else None,
        "project": settings.langchain_project if settings.langchain_tracing_v2 else None,
        "api_key_set": bool(settings.langchain_api_key),
    }


# Setup tracing on module import
_tracing_enabled = setup_langsmith_tracing()
