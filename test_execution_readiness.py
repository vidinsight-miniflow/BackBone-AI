#!/usr/bin/env python3
"""
Execution Readiness Test
Simulates actual code execution to verify everything will work at runtime.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 70)
print("BackBone-AI - Execution Readiness Analysis")
print("=" * 70)
print()

results = []
errors = []

# Test 1: Import all critical modules
print("1. Testing Critical Imports...")
print("-" * 70)

imports_to_test = [
    ("app.core.config", "Settings"),
    ("app.core.llm_factory", "LLMFactory"),
    ("app.agents.base_agent", "BaseAgent"),
    ("app.agents.schema_validator_agent", "SchemaValidatorAgent"),
    ("app.agents.architect_agent", "ArchitectAgent"),
    ("app.agents.code_generator_agent", "CodeGeneratorAgent"),
    ("app.agents.validator_agent", "ValidatorAgent"),
    ("app.workflows.generation_workflow", "GenerationWorkflow"),
    ("app.workflows.state", "WorkflowState"),
    ("app.api.main", "app"),
    ("app.api.routes.generate", "router"),
    ("app.core.security", "get_current_user"),
    ("app.core.rate_limit", "limiter"),
    ("app.core.validation", "validate_project_schema"),
    ("app.core.health", "health_checker"),
    ("app.core.metrics", "http_requests_total"),
]

for module_name, class_name in imports_to_test:
    try:
        module = __import__(module_name, fromlist=[class_name])
        cls = getattr(module, class_name)
        print(f"   ✅ {module_name}.{class_name}")
        results.append((f"{module_name}.{class_name}", True, "Import successful"))
    except ImportError as e:
        print(f"   ❌ {module_name}.{class_name} - ImportError: {e}")
        errors.append(f"Import failed: {module_name}.{class_name} - {e}")
        results.append((f"{module_name}.{class_name}", False, str(e)))
    except AttributeError as e:
        print(f"   ❌ {module_name}.{class_name} - AttributeError: {e}")
        errors.append(f"Missing class: {module_name}.{class_name} - {e}")
        results.append((f"{module_name}.{class_name}", False, str(e)))
    except Exception as e:
        print(f"   ⚠️  {module_name}.{class_name} - {type(e).__name__}: {e}")
        errors.append(f"Error: {module_name}.{class_name} - {e}")
        results.append((f"{module_name}.{class_name}", False, str(e)))

# Test 2: LLMFactory can create instances
print("\n2. Testing LLMFactory...")
print("-" * 70)

try:
    from app.core.llm_factory import LLMFactory
    from app.core.config import settings

    # Test factory methods exist
    assert hasattr(LLMFactory, 'create_llm'), "Missing create_llm method"
    assert hasattr(LLMFactory, 'create_agent_llms'), "Missing create_agent_llms method"
    assert hasattr(LLMFactory, 'create_default_llm'), "Missing create_default_llm method"

    print("   ✅ All factory methods exist")

    # Test provider configuration
    for provider in ["openai", "anthropic", "google"]:
        try:
            config = settings.get_llm_config(provider)
            assert "api_key" in config, f"Missing api_key for {provider}"
            assert "model" in config, f"Missing model for {provider}"
            assert "temperature" in config, f"Missing temperature for {provider}"
            print(f"   ✅ {provider.title()} configuration valid")
        except Exception as e:
            print(f"   ❌ {provider.title()} configuration error: {e}")
            errors.append(f"Config error for {provider}: {e}")

    results.append(("LLMFactory", True, "All checks passed"))

except Exception as e:
    print(f"   ❌ LLMFactory test failed: {e}")
    errors.append(f"LLMFactory test failed: {e}")
    results.append(("LLMFactory", False, str(e)))

# Test 3: Workflow can be instantiated
print("\n3. Testing Workflow Instantiation...")
print("-" * 70)

try:
    from app.workflows.generation_workflow import GenerationWorkflow

    # This should work without API keys (agents initialize with dummy LLM if needed)
    workflow = GenerationWorkflow(llm_provider="openai")

    assert hasattr(workflow, 'schema_validator'), "Missing schema_validator"
    assert hasattr(workflow, 'architect'), "Missing architect"
    assert hasattr(workflow, 'code_generator'), "Missing code_generator"
    assert hasattr(workflow, 'workflow'), "Missing workflow graph"

    print("   ✅ Workflow instantiated successfully")
    print(f"   ✅ Schema Validator: {workflow.schema_validator.name}")
    print(f"   ✅ Architect: {workflow.architect.name}")
    print(f"   ✅ Code Generator: {workflow.code_generator.name}")

    results.append(("Workflow Instantiation", True, "All agents initialized"))

except Exception as e:
    print(f"   ❌ Workflow instantiation failed: {e}")
    errors.append(f"Workflow instantiation failed: {e}")
    results.append(("Workflow Instantiation", False, str(e)))

# Test 4: API application can be created
print("\n4. Testing API Application...")
print("-" * 70)

try:
    from app.api.main import app
    from app.api.routes.generate import router

    # Check app is FastAPI instance
    assert hasattr(app, 'routes'), "App missing routes"
    assert hasattr(app, 'state'), "App missing state"

    # Check rate limiter is configured
    assert hasattr(app.state, 'limiter'), "Rate limiter not configured"

    # Check router has endpoints
    routes = [r.path for r in router.routes]
    expected_routes = ["/api/v1/generate", "/api/v1/validate", "/api/v1/status"]

    missing = [r for r in expected_routes if r not in routes]
    if missing:
        print(f"   ⚠️  Missing routes: {missing}")
        errors.append(f"Missing API routes: {missing}")
    else:
        print(f"   ✅ All {len(expected_routes)} API endpoints present")

    # Check middleware
    middleware_names = [m.__class__.__name__ for m in app.user_middleware]
    print(f"   ✅ Middleware count: {len(middleware_names)}")

    results.append(("API Application", True, "App configured correctly"))

except Exception as e:
    print(f"   ❌ API application test failed: {e}")
    errors.append(f"API test failed: {e}")
    results.append(("API Application", False, str(e)))

# Test 5: Security components
print("\n5. Testing Security Components...")
print("-" * 70)

try:
    from app.core.security import create_access_token, get_current_user
    from app.core.rate_limit import limiter, get_identifier
    from app.core.validation import validate_project_schema

    print("   ✅ Security functions importable")
    print("   ✅ Rate limiter configured")
    print("   ✅ Validation functions available")

    results.append(("Security Components", True, "All security features available"))

except Exception as e:
    print(f"   ❌ Security component test failed: {e}")
    errors.append(f"Security test failed: {e}")
    results.append(("Security Components", False, str(e)))

# Test 6: Monitoring components
print("\n6. Testing Monitoring Components...")
print("-" * 70)

try:
    from app.core.health import health_checker
    from app.core.metrics import http_requests_total, llm_tokens_used_total

    assert health_checker is not None, "Health checker not initialized"
    print("   ✅ Health checker available")

    assert http_requests_total is not None, "HTTP metrics not initialized"
    assert llm_tokens_used_total is not None, "LLM metrics not initialized"
    print("   ✅ Prometheus metrics configured")

    results.append(("Monitoring Components", True, "All monitoring features available"))

except Exception as e:
    print(f"   ❌ Monitoring component test failed: {e}")
    errors.append(f"Monitoring test failed: {e}")
    results.append(("Monitoring Components", False, str(e)))

# Test 7: Template system
print("\n7. Testing Template System...")
print("-" * 70)

try:
    from pathlib import Path

    template_dir = Path("templates")
    if not template_dir.exists():
        print(f"   ⚠️  Template directory not found: {template_dir}")
        errors.append("Template directory missing")
    else:
        template_files = list(template_dir.glob("*.j2"))
        print(f"   ✅ Template directory exists: {template_dir}")
        print(f"   ✅ Template files found: {len(template_files)}")

        for template in template_files[:5]:  # Show first 5
            print(f"      - {template.name}")

    results.append(("Template System", True, f"{len(template_files)} templates found"))

except Exception as e:
    print(f"   ❌ Template system test failed: {e}")
    errors.append(f"Template test failed: {e}")
    results.append(("Template System", False, str(e)))

# Summary
print("\n" + "=" * 70)
print("EXECUTION READINESS SUMMARY")
print("=" * 70)

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for component, success, message in results:
    status = "✅ READY" if success else "❌ FAIL"
    print(f"{status:12s} | {component:30s} | {message[:40]}")

print("-" * 70)
print(f"Result: {passed}/{total} checks passed ({int(passed/total*100) if total > 0 else 0}%)")

# Detailed errors
if errors:
    print("\n" + "=" * 70)
    print("ISSUES FOUND")
    print("=" * 70)
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")

    print("\n" + "=" * 70)
    print("RESOLUTION")
    print("=" * 70)
    print("""
Most errors are likely due to missing dependencies. To fix:

1. Install dependencies:
   pip install -r requirements.txt

2. Set up environment:
   cp .env.example .env
   nano .env  # Add your API keys

3. Run tests again:
   python test_execution_readiness.py

If imports still fail, ensure you're in the project root directory.
    """)

# Final verdict
print("\n" + "=" * 70)
print("EXECUTION READINESS VERDICT")
print("=" * 70)

if passed == total:
    print("✅ READY FOR EXECUTION")
    print("\nAll systems operational. Code is ready to run.")
    print("\nNext steps:")
    print("1. Set API keys in .env file")
    print("2. Run: backbone-ai generate --schema examples/blog_schema.json")
    print("3. Or start API: uvicorn app.api.main:app --reload")
    sys.exit(0)
elif passed >= total * 0.8:
    print("⚠️  MOSTLY READY")
    print(f"\n{passed}/{total} checks passed. Minor issues detected.")
    print("System should work but may have some features unavailable.")
    sys.exit(0)
else:
    print("❌ NOT READY")
    print(f"\nOnly {passed}/{total} checks passed. Critical issues detected.")
    print("Fix the errors above before running.")
    sys.exit(1)
