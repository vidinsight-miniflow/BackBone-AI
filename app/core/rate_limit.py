"""
Rate limiting utilities.
"""

from typing import Callable

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger(__name__)


def get_identifier(request: Request) -> str:
    """
    Get identifier for rate limiting.

    Uses API key if authenticated, otherwise IP address.

    Args:
        request: FastAPI request

    Returns:
        Identifier string for rate limiting
    """
    # Try to get API key from header
    api_key = request.headers.get("x-api-key")
    if api_key:
        return f"apikey:{api_key[:16]}"  # Use first 16 chars for identification

    # Try to get user from JWT
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        return f"token:{token[:16]}"

    # Fall back to IP address
    return get_remote_address(request)


# Create limiter instance
limiter = Limiter(
    key_func=get_identifier,
    default_limits=["100/minute", "1000/hour"],  # Default limits
    enabled=True,  # Always create, but checks can be conditional
    headers_enabled=True,  # Add rate limit headers to responses
    strategy="fixed-window",  # or "moving-window" for more accurate limiting
)


# Rate limit decorators for different tiers
def rate_limit_public(func: Callable) -> Callable:
    """Rate limit for public endpoints (more restrictive)."""
    return limiter.limit("20/minute")(func)


def rate_limit_authenticated(func: Callable) -> Callable:
    """Rate limit for authenticated users (more permissive)."""
    return limiter.limit("100/minute")(func)


def rate_limit_generate(func: Callable) -> Callable:
    """Rate limit for code generation endpoints (very restrictive due to cost)."""
    return limiter.limit("10/minute, 50/hour")(func)


def rate_limit_validation(func: Callable) -> Callable:
    """Rate limit for validation endpoints (moderate)."""
    return limiter.limit("50/minute")(func)


# Custom rate limit messages
RATE_LIMIT_EXCEEDED_MESSAGE = {
    "error": "Rate limit exceeded",
    "message": "You have exceeded the rate limit. Please try again later.",
    "documentation": "https://github.com/vidinsight-miniflow/BackBone-AI/docs/api.md#rate-limits",
}


def get_rate_limit_status(request: Request) -> dict:
    """
    Get current rate limit status for a request.

    Args:
        request: FastAPI request

    Returns:
        Dict with rate limit information
    """
    # This would require storing rate limit data
    # For now, return basic info
    identifier = get_identifier(request)

    return {
        "identifier": identifier,
        "limits": {
            "public": "20/minute",
            "authenticated": "100/minute",
            "generation": "10/minute, 50/hour",
            "validation": "50/minute",
        },
        "current_tier": "authenticated" if "apikey:" in identifier or "token:" in identifier else "public",
    }
