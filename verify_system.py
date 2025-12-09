#!/usr/bin/env python3
"""
System Verification Script
Checks all critical components and integrations.
"""

import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("BackBone-AI System Verification")
print("=" * 70)
print()

# Track results
results = []

# 1. Test critical imports
print("1. Testing Critical Imports...")
try:
    from app.core.config import settings
    from app.core.security import get_current_user, create_access_token
    from app.core.rate_limit import limiter
    from app.core.validation import SecureRequestValidator, validate_project_schema
    from app.core.health import health_checker
    from app.core.metrics import http_requests_total
    from app.api.routes.generate import router as generate_router
    from app.workflows.generation_workflow import GenerationWorkflow
    print("   ✅ All critical imports successful")
    results.append(("Critical Imports", True, "All imports working"))
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    results.append(("Critical Imports", False, str(e)))

# 2. Verify API router
print("\n2. Verifying API Router...")
try:
    from app.api.routes.generate import router
    routes = [r.path for r in router.routes]
    expected_routes = ["/api/v1/generate", "/api/v1/validate", "/api/v1/status"]

    all_present = all(route in routes for route in expected_routes)
    if all_present:
        print(f"   ✅ All {len(expected_routes)} API endpoints registered")
        for route in expected_routes:
            print(f"      - {route}")
        results.append(("API Endpoints", True, f"{len(expected_routes)} endpoints"))
    else:
        missing = [r for r in expected_routes if r not in routes]
        print(f"   ❌ Missing endpoints: {missing}")
        results.append(("API Endpoints", False, f"Missing: {missing}"))
except Exception as e:
    print(f"   ❌ Router verification error: {e}")
    results.append(("API Endpoints", False, str(e)))

# 3. Verify security integration
print("\n3. Verifying Security Integration...")
try:
    from app.api.main import app

    # Check rate limiter
    has_limiter = hasattr(app.state, 'limiter')

    # Check middleware
    middleware_names = [m.__class__.__name__ for m in app.user_middleware]
    has_slowapi = any('SlowAPI' in name for name in middleware_names)

    if has_limiter and has_slowapi:
        print("   ✅ Rate limiting integrated")
        print("   ✅ SlowAPI middleware active")
        results.append(("Security Integration", True, "Rate limiting active"))
    else:
        issues = []
        if not has_limiter: issues.append("Missing limiter")
        if not has_slowapi: issues.append("Missing SlowAPI middleware")
        print(f"   ❌ Issues: {', '.join(issues)}")
        results.append(("Security Integration", False, ', '.join(issues)))
except Exception as e:
    print(f"   ❌ Security verification error: {e}")
    results.append(("Security Integration", False, str(e)))

# 4. Verify configuration
print("\n4. Verifying Configuration...")
try:
    from app.core.config import settings

    required_fields = [
        'app_name', 'app_version', 'enable_auth', 'api_key',
        'jwt_secret_key', 'jwt_algorithm', 'jwt_expiration_hours',
        'max_json_size', 'max_tables', 'max_columns_per_table'
    ]

    missing = [f for f in required_fields if not hasattr(settings, f)]

    if not missing:
        print(f"   ✅ All {len(required_fields)} required config fields present")
        print(f"      - App: {settings.app_name} v{settings.app_version}")
        print(f"      - Auth enabled: {settings.enable_auth}")
        print(f"      - Max tables: {settings.max_tables}")
        results.append(("Configuration", True, "All fields present"))
    else:
        print(f"   ❌ Missing config fields: {missing}")
        results.append(("Configuration", False, f"Missing: {missing}"))
except Exception as e:
    print(f"   ❌ Configuration verification error: {e}")
    results.append(("Configuration", False, str(e)))

# 5. Verify monitoring
print("\n5. Verifying Monitoring...")
try:
    from app.core.health import health_checker
    from app.core.metrics import http_requests_total, llm_tokens_used_total

    # Check health checker
    has_health = health_checker is not None

    # Check metrics
    has_metrics = http_requests_total is not None and llm_tokens_used_total is not None

    if has_health and has_metrics:
        print("   ✅ Health checker initialized")
        print("   ✅ Prometheus metrics configured")
        results.append(("Monitoring", True, "Health + Metrics"))
    else:
        issues = []
        if not has_health: issues.append("Missing health checker")
        if not has_metrics: issues.append("Missing metrics")
        print(f"   ❌ Issues: {', '.join(issues)}")
        results.append(("Monitoring", False, ', '.join(issues)))
except Exception as e:
    print(f"   ❌ Monitoring verification error: {e}")
    results.append(("Monitoring", False, str(e)))

# 6. Verify workflows
print("\n6. Verifying Workflows...")
try:
    from app.workflows.generation_workflow import GenerationWorkflow
    from app.workflows.state import GenerationState

    # Check workflow can be instantiated
    workflow = GenerationWorkflow(llm_provider="openai")
    has_workflow = workflow is not None

    if has_workflow:
        print("   ✅ GenerationWorkflow instantiates successfully")
        print("   ✅ GenerationState type definitions present")
        results.append(("Workflows", True, "LangGraph workflow ready"))
    else:
        print("   ❌ Workflow instantiation failed")
        results.append(("Workflows", False, "Instantiation failed"))
except Exception as e:
    print(f"   ❌ Workflow verification error: {e}")
    results.append(("Workflows", False, str(e)))

# 7. Check file structure
print("\n7. Checking File Structure...")
try:
    critical_files = [
        "app/api/main.py",
        "app/api/routes/__init__.py",
        "app/api/routes/generate.py",
        "app/core/security.py",
        "app/core/rate_limit.py",
        "app/core/validation.py",
        "app/core/health.py",
        "app/core/metrics.py",
        "app/workflows/generation_workflow.py",
        "app/workflows/state.py",
        "docs/SECURITY.md",
        "docs/MONITORING.md",
    ]

    missing_files = []
    for file_path in critical_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)

    if not missing_files:
        print(f"   ✅ All {len(critical_files)} critical files present")
        results.append(("File Structure", True, f"{len(critical_files)} files"))
    else:
        print(f"   ❌ Missing files: {missing_files}")
        results.append(("File Structure", False, f"Missing: {len(missing_files)}"))
except Exception as e:
    print(f"   ❌ File structure check error: {e}")
    results.append(("File Structure", False, str(e)))

# Summary
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for component, success, message in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:10s} | {component:25s} | {message}")

print("-" * 70)
print(f"Result: {passed}/{total} checks passed ({int(passed/total*100)}%)")

if passed == total:
    print("\n🎉 System verification PASSED - All components functional!")
    sys.exit(0)
else:
    print(f"\n⚠️  System verification FAILED - {total - passed} issues found")
    sys.exit(1)
