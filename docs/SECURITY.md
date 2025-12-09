## 🔒 Security Guide

This document outlines security features, best practices, and configuration for BackBone-AI.

## Table of Contents

- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)
- [Input Validation](#input-validation)
- [Security Configuration](#security-configuration)
- [Security Best Practices](#security-best-practices)
- [Vulnerability Reporting](#vulnerability-reporting)

---

## Authentication

BackBone-AI supports two authentication methods:

### 1. API Key Authentication

Simple and straightforward for service-to-service communication.

**Setup:**
```bash
# .env
ENABLE_AUTH=true
API_KEY=your-secure-api-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Usage:**
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/api/v1/generate
```

**Generating a secure API key:**
```python
import secrets
api_key = secrets.token_urlsafe(32)
print(api_key)  # Use this in .env
```

---

### 2. JWT Token Authentication

More secure for user-based applications with expiration and scopes.

**Creating a token:**
```python
from app.core.security import create_access_token
from datetime import timedelta

token = create_access_token(
    data={"sub": "user@example.com", "scopes": ["generate", "validate"]},
    expires_delta=timedelta(hours=24)
)
```

**Usage:**
```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/generate
```

---

### Disabling Authentication (Development Only)

```bash
# .env
ENABLE_AUTH=false
```

**⚠️ WARNING:** Never disable authentication in production!

---

## Rate Limiting

Protects against abuse and controls costs.

### Rate Limit Tiers

| Tier | Limit | Applies To |
|------|-------|------------|
| **Public** | 20/minute | Unauthenticated requests |
| **Authenticated** | 100/minute | API key or JWT authenticated |
| **Generation** | 10/minute, 50/hour | Code generation endpoints |
| **Validation** | 50/minute | Schema validation endpoints |

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

### Rate Limit Response

When exceeded (429 Too Many Requests):

```json
{
  "error": "Rate limit exceeded",
  "message": "You have exceeded the rate limit. Please try again later.",
  "retry_after": 30
}
```

### Custom Rate Limits

Configure in `.env`:

```bash
# Not yet implemented - coming soon
RATE_LIMIT_PUBLIC=20/minute
RATE_LIMIT_AUTHENTICATED=100/minute
```

---

## Input Validation

Comprehensive validation prevents security issues and resource abuse.

### Size Limits

| Resource | Limit | Configurable |
|----------|-------|--------------|
| **JSON Size** | 10 MB | Yes |
| **Request Size** | 50 MB | Yes |
| **String Length** | 1,000 chars | Yes |
| **Array Length** | 100 items | Yes |

### Schema Limits

| Resource | Limit | Reason |
|----------|-------|--------|
| **Tables** | 50 | Performance |
| **Columns/Table** | 100 | Maintainability |
| **Relationships/Table** | 50 | Complexity |

### Validation Checks

1. **JSON Structure**: Valid JSON syntax
2. **Size Validation**: Within limits
3. **Required Fields**: project_name, schema
4. **Type Validation**: Correct data types
5. **Suspicious Patterns**: SQL injection, XSS, code injection
6. **Sanitization**: Null bytes removed, strings truncated

### Blocked Patterns

The following patterns are blocked in schema input:

- `drop table`
- `delete from`
- `<script>`
- `javascript:`
- `eval(`
- `exec(`

**Error Response (400 Bad Request):**

```json
{
  "detail": "Suspicious pattern detected in schema: drop table"
}
```

---

## Security Configuration

### Environment Variables

```bash
# =====================================================
# SECURITY CONFIGURATION
# =====================================================

# Authentication
ENABLE_AUTH=true  # Enable/disable authentication
API_KEY=your-secure-api-key-32-chars-min

# JWT Settings (if using JWT)
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Rate Limiting
ENABLE_RATE_LIMITING=true  # Always enabled in production

# Input Validation
MAX_JSON_SIZE=10485760  # 10 MB in bytes
MAX_TABLES=50
MAX_COLUMNS_PER_TABLE=100
MAX_RELATIONSHIPS_PER_TABLE=50

# CORS (Cross-Origin Resource Sharing)
CORS_ORIGINS=["https://yourdomain.com"]
CORS_ALLOW_CREDENTIALS=true

# Security Headers
ENABLE_SECURITY_HEADERS=true
```

---

## Security Best Practices

### ✅ Production Checklist

- [ ] **Enable authentication** (`ENABLE_AUTH=true`)
- [ ] **Use strong API keys** (32+ characters, cryptographically random)
- [ ] **Rotate API keys** regularly (every 90 days)
- [ ] **Enable HTTPS** (use reverse proxy like nginx)
- [ ] **Configure CORS** properly (don't use `*`)
- [ ] **Monitor rate limits** and adjust as needed
- [ ] **Enable security headers** (CSP, HSTS, etc.)
- [ ] **Keep dependencies updated** (check weekly)
- [ ] **Enable logging** for security events
- [ ] **Set up alerts** for suspicious activity
- [ ] **Regular security audits** (quarterly)
- [ ] **Backup API keys** securely (use secrets manager)

---

### 🔐 API Key Security

**DO:**
✅ Generate keys with `secrets.token_urlsafe(32)`
✅ Store in environment variables or secrets manager
✅ Use different keys for dev/staging/production
✅ Rotate keys regularly
✅ Log key usage and failures

**DON'T:**
❌ Hardcode keys in code
❌ Commit keys to git
❌ Share keys via email/chat
❌ Use same key across environments
❌ Use predictable keys

---

### 🛡️ Defense in Depth

Multiple layers of security:

1. **Network Level**: Firewall, VPN, IP whitelist
2. **Application Level**: Authentication, rate limiting
3. **Input Level**: Validation, sanitization
4. **Output Level**: Encoding, escaping
5. **Monitoring Level**: Logging, alerting, auditing

---

### 🚨 Incident Response

If you suspect a security breach:

1. **Immediately rotate** all API keys
2. **Review logs** for suspicious activity
3. **Check metrics** for anomalies
4. **Block suspicious IPs** if identified
5. **Notify team** and stakeholders
6. **Document incident** for post-mortem
7. **Update security measures** based on learnings

---

## Dependency Security

### Current Status

Dependencies are updated to latest secure versions:

```txt
langchain==0.3.27  # Updated from 0.3.0
fastapi==0.115.6   # Updated from 0.115.0
pydantic==2.10.5   # Updated from 2.8.0
jinja2==3.1.5      # Updated from 3.1.4
```

### Checking for Vulnerabilities

```bash
# Install safety
pip install safety

# Check dependencies
safety check --json

# Or use pip-audit
pip install pip-audit
pip-audit
```

### Update Schedule

- **Critical vulnerabilities**: Immediate
- **High severity**: Within 7 days
- **Medium severity**: Within 30 days
- **Low severity**: Next release cycle

---

## HTTPS Configuration

Always use HTTPS in production. Configure with nginx:

```nginx
server {
    listen 443 ssl http2;
    server_name api.yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Security Headers

Add security headers via nginx or middleware:

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
add_header Content-Security-Policy "default-src 'self'" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
```

---

## Monitoring Security Events

### What to Monitor

- Failed authentication attempts
- Rate limit violations
- Suspicious input patterns
- Unusual API usage patterns
- Large requests
- Error rate spikes

### Setting Up Alerts

```promql
# Failed auth attempts (Prometheus)
rate(backbone_http_requests_total{status="401"}[5m]) > 5

# Rate limit violations
rate(backbone_http_requests_total{status="429"}[5m]) > 10

# Error rate spike
rate(backbone_http_requests_total{status=~"5.."}[5m]) > 0.1
```

---

## Compliance & Standards

BackBone-AI follows security best practices:

- ✅ **OWASP Top 10** protection
- ✅ **Input validation** and sanitization
- ✅ **Authentication** and authorization
- ✅ **Rate limiting** and DoS protection
- ✅ **Secure defaults** (auth required)
- ✅ **Security logging** and monitoring
- ✅ **Dependency scanning** and updates

---

## Vulnerability Reporting

Found a security issue? Please report responsibly.

**Do NOT:**
- Open public GitHub issues
- Share details publicly

**Instead:**
1. Email: security@yourdomain.com (set this up!)
2. Include:
   - Description of vulnerability
   - Steps to reproduce
   - Impact assessment
   - Suggested fix (if known)

**Response Timeline:**
- Acknowledgment: 24 hours
- Initial assessment: 72 hours
- Fix timeline: Based on severity

---

## Security Audit Log

| Date | Version | Changes |
|------|---------|---------|
| 2024-01-XX | 0.1.0 | Initial security implementation |
| | | - API key authentication |
| | | - JWT authentication |
| | | - Rate limiting |
| | | - Input validation |
| | | - Dependency updates |

---

## Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Rate Limiting Patterns](https://cloud.google.com/architecture/rate-limiting-strategies-techniques)

---

## Support

For security questions or concerns:
- GitHub Issues: https://github.com/vidinsight-miniflow/BackBone-AI/issues
- Documentation: https://github.com/vidinsight-miniflow/BackBone-AI/docs
- Security Email: (set up dedicated email)
