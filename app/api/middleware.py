"""
Middleware for monitoring and observability.
"""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.logger import get_logger

if settings.enable_metrics:
    from app.core.metrics import (
        http_request_duration_seconds,
        http_request_size_bytes,
        http_requests_total,
        http_response_size_bytes,
    )

logger = get_logger(__name__)


class MonitoringMiddleware(BaseHTTPMiddleware):
    """
    Middleware for monitoring HTTP requests.

    Tracks:
    - Request count by method, endpoint, and status
    - Request/response duration
    - Request/response size
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and collect metrics."""
        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        path = request.url.path

        # Calculate request size
        request_size = 0
        if request.headers.get("content-length"):
            try:
                request_size = int(request.headers["content-length"])
            except ValueError:
                pass

        # Process request
        try:
            response = await call_next(request)
            status_code = response.status_code

        except Exception as e:
            # Log error
            logger.error(f"Request failed: {method} {path} - {e}", exc_info=True)

            # Track error metrics
            if settings.enable_metrics:
                http_requests_total.labels(
                    method=method,
                    endpoint=path,
                    status="500",
                ).inc()

            raise

        # Calculate duration
        duration = time.time() - start_time

        # Calculate response size
        response_size = 0
        if "content-length" in response.headers:
            try:
                response_size = int(response.headers["content-length"])
            except ValueError:
                pass

        # Track metrics
        if settings.enable_metrics:
            http_requests_total.labels(
                method=method,
                endpoint=path,
                status=str(status_code),
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=path,
            ).observe(duration)

            if request_size > 0:
                http_request_size_bytes.labels(
                    method=method,
                    endpoint=path,
                ).observe(request_size)

            if response_size > 0:
                http_response_size_bytes.labels(
                    method=method,
                    endpoint=path,
                ).observe(response_size)

        # Log request (only in debug mode or for errors)
        if settings.debug or status_code >= 400:
            logger.info(
                f"{method} {path} - {status_code} - {duration:.3f}s"
                f" (req: {request_size}B, res: {response_size}B)"
            )

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add request ID to all requests for tracing.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add request ID to request state and response headers."""
        import uuid

        # Generate request ID
        request_id = str(uuid.uuid4())

        # Add to request state
        request.state.request_id = request_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Request-ID"] = request_id

        return response


class ErrorTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track and log errors.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Track errors and exceptions."""
        try:
            response = await call_next(request)
            return response

        except Exception as e:
            # Log error with context
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(
                f"Request {request_id} failed: {request.method} {request.url.path}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client": request.client.host if request.client else "unknown",
                },
            )

            # Re-raise to let FastAPI handle it
            raise
