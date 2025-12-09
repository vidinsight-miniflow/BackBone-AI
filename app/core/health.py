"""
Health check utilities for monitoring system health.
"""

import asyncio
import time
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.llm_factory import LLMFactory
from app.core.logger import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseModel):
    """Health status of a single component."""

    name: str
    status: HealthStatus
    message: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResponse(BaseModel):
    """Overall health check response."""

    status: HealthStatus
    timestamp: float
    uptime_seconds: float
    version: str
    environment: str
    components: Dict[str, ComponentHealth] = Field(default_factory=dict)
    details: Optional[Dict[str, Any]] = None


class HealthChecker:
    """
    Health checker for monitoring system components.
    """

    def __init__(self):
        self.start_time = time.time()
        self.logger = get_logger(__name__)

    async def check_all(self) -> HealthCheckResponse:
        """
        Perform comprehensive health check of all components.

        Returns:
            HealthCheckResponse with status of all components
        """
        components: Dict[str, ComponentHealth] = {}

        # Check LLM connectivity
        llm_health = await self._check_llm()
        components["llm"] = llm_health

        # Check configuration
        config_health = self._check_config()
        components["config"] = config_health

        # Check file system
        fs_health = await self._check_filesystem()
        components["filesystem"] = fs_health

        # Determine overall status
        overall_status = self._determine_overall_status(components)

        # Calculate uptime
        uptime = time.time() - self.start_time

        return HealthCheckResponse(
            status=overall_status,
            timestamp=time.time(),
            uptime_seconds=uptime,
            version=settings.app_version,
            environment=settings.app_env,
            components=components,
            details={
                "app_name": settings.app_name,
                "debug": settings.debug,
                "log_level": settings.log_level,
            },
        )

    async def check_liveness(self) -> bool:
        """
        Liveness probe - checks if application is running.

        Returns:
            True if app is alive
        """
        return True

    async def check_readiness(self) -> HealthCheckResponse:
        """
        Readiness probe - checks if application is ready to serve traffic.

        Returns:
            HealthCheckResponse with component statuses
        """
        return await self.check_all()

    async def _check_llm(self) -> ComponentHealth:
        """Check LLM provider connectivity."""
        start_time = time.time()

        try:
            # Try to create LLM instance
            llm = LLMFactory.create_llm(provider=settings.default_llm_provider)

            # Try a simple test (without actually calling API to save costs)
            if llm is None:
                return ComponentHealth(
                    name="llm",
                    status=HealthStatus.UNHEALTHY,
                    message="Failed to create LLM instance",
                    response_time_ms=(time.time() - start_time) * 1000,
                )

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="llm",
                status=HealthStatus.HEALTHY,
                message=f"LLM provider '{settings.default_llm_provider}' configured",
                response_time_ms=response_time,
                metadata={
                    "provider": settings.default_llm_provider,
                    "configured": True,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"LLM health check failed: {e}")

            return ComponentHealth(
                name="llm",
                status=HealthStatus.UNHEALTHY,
                message=f"LLM check failed: {str(e)}",
                response_time_ms=response_time,
            )

    def _check_config(self) -> ComponentHealth:
        """Check configuration validity."""
        start_time = time.time()

        try:
            # Check critical config values
            issues = []

            if not settings.default_llm_provider:
                issues.append("DEFAULT_LLM_PROVIDER not set")

            if settings.default_llm_provider == "openai" and not settings.openai_api_key:
                issues.append("OPENAI_API_KEY not set")

            if (
                settings.default_llm_provider == "anthropic"
                and not settings.anthropic_api_key
            ):
                issues.append("ANTHROPIC_API_KEY not set")

            if (
                settings.default_llm_provider == "google"
                and not settings.google_api_key
            ):
                issues.append("GOOGLE_API_KEY not set")

            response_time = (time.time() - start_time) * 1000

            if issues:
                return ComponentHealth(
                    name="config",
                    status=HealthStatus.DEGRADED,
                    message=f"Configuration issues: {', '.join(issues)}",
                    response_time_ms=response_time,
                )

            return ComponentHealth(
                name="config",
                status=HealthStatus.HEALTHY,
                message="Configuration valid",
                response_time_ms=response_time,
                metadata={
                    "environment": settings.app_env,
                    "debug": settings.debug,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Config health check failed: {e}")

            return ComponentHealth(
                name="config",
                status=HealthStatus.UNHEALTHY,
                message=f"Config check failed: {str(e)}",
                response_time_ms=response_time,
            )

    async def _check_filesystem(self) -> ComponentHealth:
        """Check filesystem access."""
        start_time = time.time()

        try:
            # Check if output directory is writable
            output_dir = settings.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)

            # Try to write a test file
            test_file = output_dir / ".health_check"
            test_file.write_text("health_check")
            test_file.unlink()

            response_time = (time.time() - start_time) * 1000

            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.HEALTHY,
                message="Filesystem accessible and writable",
                response_time_ms=response_time,
                metadata={
                    "output_dir": str(output_dir),
                    "writable": True,
                },
            )

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.logger.error(f"Filesystem health check failed: {e}")

            return ComponentHealth(
                name="filesystem",
                status=HealthStatus.UNHEALTHY,
                message=f"Filesystem check failed: {str(e)}",
                response_time_ms=response_time,
            )

    def _determine_overall_status(
        self, components: Dict[str, ComponentHealth]
    ) -> HealthStatus:
        """
        Determine overall health status from component statuses.

        Args:
            components: Dictionary of component health statuses

        Returns:
            Overall health status
        """
        statuses = [comp.status for comp in components.values()]

        # If any component is unhealthy, system is unhealthy
        if HealthStatus.UNHEALTHY in statuses:
            return HealthStatus.UNHEALTHY

        # If any component is degraded, system is degraded
        if HealthStatus.DEGRADED in statuses:
            return HealthStatus.DEGRADED

        # All components healthy
        return HealthStatus.HEALTHY


# Global health checker instance
health_checker = HealthChecker()
