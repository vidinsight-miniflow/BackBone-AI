"""
FastAPI application entry point.
Provides REST API for code generation with monitoring and health checks.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse

from app.api.middleware import (
    ErrorTrackingMiddleware,
    MonitoringMiddleware,
    RequestIDMiddleware,
)
from app.core.config import settings
from app.core.health import health_checker
from app.core.logger import get_logger
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.app_env}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Metrics enabled: {settings.enable_metrics}")

    yield

    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-driven code generation for FastAPI and SQLAlchemy backends",
    debug=settings.debug,
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Add custom exception handler for rate limiting
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request, exc):
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "You have exceeded the rate limit. Please try again later.",
            "retry_after": exc.detail,
        },
    )

# Add middleware (order matters - first added = outermost)
app.add_middleware(ErrorTrackingMiddleware)
app.add_middleware(MonitoringMiddleware)
app.add_middleware(RequestIDMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Health check endpoints
@app.get("/health", tags=["Health"], summary="Basic health check")
async def health_check():
    """Basic health check endpoint - returns OK if service is up."""
    return JSONResponse(
        content={
            "status": "healthy",
            "app_name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.app_env,
        }
    )


@app.get("/health/liveness", tags=["Health"], summary="Liveness probe")
async def liveness_probe():
    """
    Liveness probe - checks if application is alive.

    Used by Kubernetes/Docker to determine if container should be restarted.
    Returns 200 if app is alive, 503 if not.
    """
    is_alive = await health_checker.check_liveness()

    if is_alive:
        return JSONResponse(
            content={"status": "alive", "timestamp": health_checker.start_time}
        )
    else:
        return JSONResponse(
            status_code=503,
            content={"status": "dead"},
        )


@app.get("/health/readiness", tags=["Health"], summary="Readiness probe")
async def readiness_probe():
    """
    Readiness probe - checks if application is ready to serve traffic.

    Used by Kubernetes/load balancers to determine if traffic should be routed.
    Returns 200 if ready, 503 if not ready.
    """
    health = await health_checker.check_readiness()

    status_code = 200
    if health.status == "unhealthy":
        status_code = 503
    elif health.status == "degraded":
        status_code = 200  # Still serve traffic but log warnings

    return JSONResponse(
        status_code=status_code,
        content=health.model_dump(),
    )


@app.get("/health/detailed", tags=["Health"], summary="Detailed health check")
async def detailed_health_check():
    """
    Detailed health check - provides comprehensive system health information.

    Includes:
    - Component statuses (LLM, config, filesystem)
    - Response times
    - System metadata
    """
    health = await health_checker.check_all()
    return JSONResponse(content=health.model_dump())


# Metrics endpoint
if settings.enable_metrics:

    @app.get("/metrics", tags=["Monitoring"], summary="Prometheus metrics")
    async def metrics():
        """
        Prometheus metrics endpoint.

        Returns metrics in Prometheus text format for scraping.
        """
        from app.core.metrics import get_metrics

        metrics_data, content_type = get_metrics()
        return Response(content=metrics_data, media_type=content_type)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return JSONResponse(
        content={
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }
    )


# Include routers
from app.api.routes import generate

app.include_router(generate.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
    )
