# Monitoring & Observability Guide

This guide covers monitoring, observability, and debugging for BackBone-AI in production.

## Table of Contents

- [Health Checks](#health-checks)
- [Prometheus Metrics](#prometheus-metrics)
- [LangSmith Tracing](#langsmith-tracing)
- [Logging](#logging)
- [Alerting](#alerting)
- [Troubleshooting](#troubleshooting)

---

## Health Checks

BackBone-AI provides multiple health check endpoints for monitoring.

### Endpoints

#### 1. Basic Health Check: `/health`

Simple health check that returns OK if service is running.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "healthy",
  "app_name": "BackBone-AI",
  "version": "0.1.0",
  "environment": "production"
}
```

**Use Case:** Simple uptime monitoring

---

#### 2. Liveness Probe: `/health/liveness`

Checks if the application is alive and should not be restarted.

```bash
curl http://localhost:8000/health/liveness
```

**Response:**
```json
{
  "status": "alive",
  "timestamp": 1704000000.0
}
```

**Status Codes:**
- `200`: Application is alive
- `503`: Application is dead (should restart)

**Use Case:** Kubernetes liveness probe

**Kubernetes Config:**
```yaml
livenessProbe:
  httpGet:
    path: /health/liveness
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

---

#### 3. Readiness Probe: `/health/readiness`

Checks if the application is ready to serve traffic.

```bash
curl http://localhost:8000/health/readiness
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1704000000.0,
  "uptime_seconds": 3600.0,
  "version": "0.1.0",
  "environment": "production",
  "components": {
    "llm": {
      "name": "llm",
      "status": "healthy",
      "message": "LLM provider 'openai' configured",
      "response_time_ms": 15.2,
      "metadata": {
        "provider": "openai",
        "configured": true
      }
    },
    "config": {
      "name": "config",
      "status": "healthy",
      "message": "Configuration valid",
      "response_time_ms": 2.1
    },
    "filesystem": {
      "name": "filesystem",
      "status": "healthy",
      "message": "Filesystem accessible and writable",
      "response_time_ms": 8.5
    }
  }
}
```

**Status Codes:**
- `200`: Ready to serve traffic (healthy or degraded)
- `503`: Not ready (unhealthy)

**Component Statuses:**
- `healthy`: Component is working normally
- `degraded`: Component has issues but system can still function
- `unhealthy`: Component is down

**Use Case:** Kubernetes readiness probe, load balancer health checks

**Kubernetes Config:**
```yaml
readinessProbe:
  httpGet:
    path: /health/readiness
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  successThreshold: 1
  failureThreshold: 3
```

---

#### 4. Detailed Health Check: `/health/detailed`

Comprehensive health information with component details.

```bash
curl http://localhost:8000/health/detailed
```

**Use Case:** Manual debugging, detailed monitoring dashboards

---

## Prometheus Metrics

BackBone-AI exposes Prometheus metrics for comprehensive monitoring.

### Enabling Metrics

Set in `.env`:
```bash
ENABLE_METRICS=true
METRICS_PORT=9090  # Optional, defaults to 9090
```

### Metrics Endpoint

```bash
curl http://localhost:8000/metrics
```

### Available Metrics

#### HTTP Metrics

- `backbone_http_requests_total{method, endpoint, status}` - Total HTTP requests
- `backbone_http_request_duration_seconds{method, endpoint}` - Request duration histogram
- `backbone_http_request_size_bytes{method, endpoint}` - Request size histogram
- `backbone_http_response_size_bytes{method, endpoint}` - Response size histogram

**Example Queries:**
```promql
# Request rate by endpoint
rate(backbone_http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(backbone_http_request_duration_seconds_bucket[5m]))

# Error rate
rate(backbone_http_requests_total{status=~"5.."}[5m])
```

---

#### Agent Metrics

- `backbone_agent_executions_total{agent_name, status}` - Total agent executions
- `backbone_agent_execution_duration_seconds{agent_name}` - Agent execution time
- `backbone_agent_errors_total{agent_name, error_type}` - Agent errors

**Example Queries:**
```promql
# Agent execution rate
rate(backbone_agent_executions_total[5m])

# Agent P99 latency
histogram_quantile(0.99, rate(backbone_agent_execution_duration_seconds_bucket[5m]))

# Agent error rate
rate(backbone_agent_errors_total[5m])
```

---

#### Workflow Metrics

- `backbone_workflow_executions_total{status}` - Total workflow executions
- `backbone_workflow_duration_seconds` - Workflow execution time
- `backbone_workflow_stages_duration_seconds{stage}` - Duration per stage

**Example Queries:**
```promql
# Workflow success rate
rate(backbone_workflow_executions_total{status="completed"}[5m]) /
rate(backbone_workflow_executions_total[5m])

# Slowest workflow stage
max(backbone_workflow_stages_duration_seconds) by (stage)
```

---

#### Code Generation Metrics

- `backbone_code_files_generated_total{project_name}` - Files generated
- `backbone_code_lines_generated_total` - Lines of code generated
- `backbone_code_models_generated_total` - Models generated

---

#### LLM Metrics

- `backbone_llm_requests_total{provider, model}` - LLM API requests
- `backbone_llm_request_duration_seconds{provider, model}` - LLM API latency
- `backbone_llm_tokens_used_total{provider, model, type}` - Tokens used (prompt/completion)
- `backbone_llm_errors_total{provider, error_type}` - LLM API errors

**Example Queries:**
```promql
# LLM cost estimation (OpenAI GPT-4)
(
  rate(backbone_llm_tokens_used_total{provider="openai", model="gpt-4", type="prompt"}[5m]) * 0.03 / 1000 +
  rate(backbone_llm_tokens_used_total{provider="openai", model="gpt-4", type="completion"}[5m]) * 0.06 / 1000
) * 3600  # Cost per hour in USD
```

---

### Prometheus Configuration

**prometheus.yml:**
```yaml
scrape_configs:
  - job_name: 'backbone-ai'
    scrape_interval: 15s
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

---

## LangSmith Tracing

LangSmith provides detailed tracing of LLM calls and agent execution.

### Enabling LangSmith

1. Get API key from [LangSmith](https://smith.langchain.com)

2. Configure in `.env`:
```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-api-key-here
LANGCHAIN_PROJECT=BackBone-AI
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
```

3. Restart application

### What's Traced

- All LLM calls (prompts, responses, tokens)
- Agent executions (inputs, outputs, errors)
- Workflow stages
- Tool calls
- Execution times and costs

### Viewing Traces

1. Go to [LangSmith Dashboard](https://smith.langchain.com)
2. Select your project: "BackBone-AI"
3. View traces, runs, and analytics

### Useful Features

- **Trace View**: See complete execution flow
- **Playground**: Replay and debug LLM calls
- **Datasets**: Create test cases from production traces
- **Annotations**: Tag and annotate runs
- **Cost Tracking**: Monitor LLM API costs

---

## Logging

BackBone-AI uses structured logging with Loguru.

### Log Levels

Configure in `.env`:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Production Recommendation:** `WARNING` or `ERROR`

### Log Format

```
2024-01-01 12:00:00.000 | INFO     | app.workflows.generation_workflow:run:145 - Starting workflow
2024-01-01 12:00:01.234 | WARNING  | app.agents.validator:execute:89 - Validation warning: unused import
2024-01-01 12:00:02.456 | ERROR    | app.core.llm_factory:create:67 - LLM creation failed
```

### Request ID Tracking

Every request gets a unique request ID:
```bash
curl -i http://localhost:8000/health
# Response header: X-Request-ID: 123e4567-e89b-12d3-a456-426614174000
```

Use request ID to trace requests across logs:
```bash
grep "123e4567-e89b-12d3-a456-426614174000" logs/app.log
```

---

## Alerting

### Recommended Alerts

#### 1. High Error Rate
```promql
rate(backbone_http_requests_total{status=~"5.."}[5m]) > 0.05
```
**Action:** Check logs, health endpoints

---

#### 2. High Latency
```promql
histogram_quantile(0.95, rate(backbone_http_request_duration_seconds_bucket[5m])) > 10
```
**Action:** Check LLM latency, system resources

---

#### 3. LLM Errors
```promql
rate(backbone_llm_errors_total[5m]) > 0.1
```
**Action:** Check LLM API status, rate limits

---

#### 4. Service Down
```promql
up{job="backbone-ai"} == 0
```
**Action:** Check service status, restart if needed

---

#### 5. High LLM Costs
```promql
sum(rate(backbone_llm_tokens_used_total[1h])) * 0.03 / 1000 > 10
```
**Action:** Review usage patterns, implement rate limiting

---

### Alertmanager Configuration

**alertmanager.yml:**
```yaml
route:
  receiver: 'team-email'
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h

receivers:
  - name: 'team-email'
    email_configs:
      - to: 'team@example.com'
        from: 'alerts@example.com'
        smarthost: 'smtp.gmail.com:587'
```

---

## Troubleshooting

### Common Issues

#### 1. Service Not Starting

**Symptoms:**
- Health check returns 503
- Container keeps restarting

**Diagnosis:**
```bash
# Check logs
docker logs backbone-ai

# Check health
curl http://localhost:8000/health/detailed
```

**Common Causes:**
- Missing API keys
- Invalid configuration
- Port already in use

---

#### 2. High Latency

**Symptoms:**
- Slow responses
- Timeouts

**Diagnosis:**
```bash
# Check metrics
curl http://localhost:8000/metrics | grep duration

# Check LangSmith for slow LLM calls
```

**Common Causes:**
- LLM API slow/rate limited
- Large input schemas
- Network issues

---

#### 3. Validation Failures

**Symptoms:**
- Workflows fail at validation stage

**Diagnosis:**
```bash
# Check detailed health
curl http://localhost:8000/health/detailed

# Check logs
grep "validation" logs/app.log
```

**Common Causes:**
- Invalid JSON schema
- Missing foreign key references
- Circular dependencies

---

### Debug Mode

Enable debug mode for verbose logging:

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

**Warning:** Only use in development. Debug mode logs sensitive information.

---

## Monitoring Stack Setup

### Quick Start with Docker Compose

```yaml
version: '3.8'

services:
  backbone-ai:
    image: backbone-ai:latest
    ports:
      - "8000:8000"
    environment:
      - ENABLE_METRICS=true
      - LANGCHAIN_TRACING_V2=true

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  grafana-data:
```

### Grafana Dashboards

Import pre-built dashboards:

1. **HTTP Metrics Dashboard** - Request rates, latencies, errors
2. **Agent Performance Dashboard** - Agent execution times, success rates
3. **LLM Usage Dashboard** - Token usage, costs, latencies
4. **System Health Dashboard** - Component health, uptime

---

## Best Practices

1. **Always enable health checks** in production
2. **Use readiness probe** for load balancer routing
3. **Enable Prometheus metrics** for production monitoring
4. **Enable LangSmith tracing** for debugging (can be expensive)
5. **Set up alerts** for critical errors and high costs
6. **Use structured logging** with request IDs
7. **Monitor LLM costs** closely
8. **Review traces** regularly for optimization opportunities
9. **Keep logs for 30+ days** for debugging
10. **Test health checks** in CI/CD pipeline

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/vidinsight-miniflow/BackBone-AI/issues
- Documentation: https://github.com/vidinsight-miniflow/BackBone-AI/docs
