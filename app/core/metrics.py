"""
Prometheus metrics for monitoring.
"""

from prometheus_client import Counter, Gauge, Histogram
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from app.core.config import settings

# Enable metrics only if configured
METRICS_ENABLED = settings.enable_metrics


# HTTP Metrics
http_requests_total = Counter(
    "backbone_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "backbone_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0),
)

http_request_size_bytes = Histogram(
    "backbone_http_request_size_bytes",
    "HTTP request size in bytes",
    ["method", "endpoint"],
)

http_response_size_bytes = Histogram(
    "backbone_http_response_size_bytes",
    "HTTP response size in bytes",
    ["method", "endpoint"],
)


# Agent Metrics
agent_executions_total = Counter(
    "backbone_agent_executions_total",
    "Total agent executions",
    ["agent_name", "status"],
)

agent_execution_duration_seconds = Histogram(
    "backbone_agent_execution_duration_seconds",
    "Agent execution duration in seconds",
    ["agent_name"],
    buckets=(0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

agent_errors_total = Counter(
    "backbone_agent_errors_total",
    "Total agent errors",
    ["agent_name", "error_type"],
)


# Workflow Metrics
workflow_executions_total = Counter(
    "backbone_workflow_executions_total",
    "Total workflow executions",
    ["status"],
)

workflow_duration_seconds = Histogram(
    "backbone_workflow_duration_seconds",
    "Workflow execution duration in seconds",
    buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0, 600.0),
)

workflow_stages_duration_seconds = Histogram(
    "backbone_workflow_stages_duration_seconds",
    "Duration of each workflow stage in seconds",
    ["stage"],
    buckets=(0.1, 0.5, 1.0, 5.0, 10.0, 30.0, 60.0, 120.0),
)


# Code Generation Metrics
code_files_generated_total = Counter(
    "backbone_code_files_generated_total",
    "Total code files generated",
    ["project_name"],
)

code_lines_generated_total = Counter(
    "backbone_code_lines_generated_total",
    "Total lines of code generated",
)

code_models_generated_total = Counter(
    "backbone_code_models_generated_total",
    "Total models generated",
)


# Validation Metrics
validation_checks_total = Counter(
    "backbone_validation_checks_total",
    "Total validation checks performed",
    ["validation_type", "status"],
)

validation_issues_total = Counter(
    "backbone_validation_issues_total",
    "Total validation issues found",
    ["severity", "category"],
)


# LLM Metrics
llm_requests_total = Counter(
    "backbone_llm_requests_total",
    "Total LLM API requests",
    ["provider", "model"],
)

llm_request_duration_seconds = Histogram(
    "backbone_llm_request_duration_seconds",
    "LLM API request duration in seconds",
    ["provider", "model"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
)

llm_tokens_used_total = Counter(
    "backbone_llm_tokens_used_total",
    "Total LLM tokens used",
    ["provider", "model", "type"],  # type: prompt or completion
)

llm_errors_total = Counter(
    "backbone_llm_errors_total",
    "Total LLM API errors",
    ["provider", "error_type"],
)


# System Metrics
system_info = Gauge(
    "backbone_system_info",
    "System information",
    ["version", "environment"],
)

active_workflows = Gauge(
    "backbone_active_workflows",
    "Number of currently active workflows",
)

# Initialize system info
system_info.labels(
    version=settings.app_version,
    environment=settings.app_env,
).set(1)


def get_metrics() -> tuple[bytes, str]:
    """
    Get Prometheus metrics in text format.

    Returns:
        Tuple of (metrics_bytes, content_type)
    """
    return generate_latest(), CONTENT_TYPE_LATEST
