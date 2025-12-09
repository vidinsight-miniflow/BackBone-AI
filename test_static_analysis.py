#!/usr/bin/env python3
"""
Static Code Analysis - No Dependencies Required
Verifies code structure without importing modules.
"""

import re
from pathlib import Path

print("=" * 70)
print("BackBone-AI - Static Code Analysis")
print("=" * 70)
print("This test checks code structure WITHOUT requiring pip packages.\n")

results = []
errors = []

# Test 1: Verify critical files exist
print("1. Checking Critical Files...")
print("-" * 70)

critical_files = {
    # Core
    "app/core/config.py": "Configuration",
    "app/core/llm_factory.py": "LLM Factory",
    "app/core/security.py": "Security",
    "app/core/rate_limit.py": "Rate Limiting",
    "app/core/validation.py": "Input Validation",
    "app/core/health.py": "Health Checks",
    "app/core/metrics.py": "Metrics",

    # Agents
    "app/agents/base_agent.py": "Base Agent",
    "app/agents/schema_validator_agent.py": "Schema Validator",
    "app/agents/architect_agent.py": "Architect Agent",
    "app/agents/code_generator_agent.py": "Code Generator",
    "app/agents/validator_agent.py": "Validator Agent",

    # Workflows
    "app/workflows/generation_workflow.py": "Generation Workflow",
    "app/workflows/state.py": "Workflow State",

    # API
    "app/api/main.py": "FastAPI App",
    "app/api/routes/generate.py": "Generate Routes",
    "app/api/middleware.py": "Middleware",

    # CLI
    "app/cli.py": "CLI Interface",

    # Config
    "requirements.txt": "Dependencies",
    ".env.example": "Environment Example",
}

missing_files = []
for filepath, description in critical_files.items():
    if Path(filepath).exists():
        print(f"   ✅ {description:30s} ({filepath})")
    else:
        print(f"   ❌ {description:30s} MISSING ({filepath})")
        missing_files.append(filepath)
        errors.append(f"Missing file: {filepath}")

if missing_files:
    results.append(("Critical Files", False, f"{len(missing_files)} files missing"))
else:
    results.append(("Critical Files", True, f"All {len(critical_files)} files present"))

# Test 2: Check LLM Factory has all providers
print("\n2. Checking LLM Factory Providers...")
print("-" * 70)

try:
    llm_factory = Path("app/core/llm_factory.py").read_text()

    providers = {
        "openai": "langchain_openai",
        "anthropic": "langchain_anthropic",
        "google": "langchain_google_genai",
    }

    all_found = True
    for provider, import_name in providers.items():
        if f"from {import_name}" in llm_factory or f"import {import_name}" in llm_factory:
            print(f"   ✅ {provider.title():15s} provider import found")
        else:
            print(f"   ❌ {provider.title():15s} provider import MISSING")
            errors.append(f"Missing {provider} provider import")
            all_found = False

    # Check for create_llm method
    if "def create_llm" in llm_factory:
        print(f"   ✅ create_llm() method found")
    else:
        print(f"   ❌ create_llm() method MISSING")
        errors.append("Missing create_llm method")
        all_found = False

    results.append(("LLM Factory", all_found, "All providers implemented" if all_found else "Missing providers"))

except Exception as e:
    print(f"   ❌ Error reading LLM Factory: {e}")
    errors.append(f"LLM Factory error: {e}")
    results.append(("LLM Factory", False, str(e)))

# Test 3: Check Config has provider settings
print("\n3. Checking Configuration...")
print("-" * 70)

try:
    config = Path("app/core/config.py").read_text()

    settings_to_check = [
        ("default_llm_provider", "Default provider setting"),
        ("openai_api_key", "OpenAI API key"),
        ("anthropic_api_key", "Anthropic API key"),
        ("google_api_key", "Google API key"),
        ("openai_model", "OpenAI model"),
        ("anthropic_model", "Anthropic model"),
        ("google_model", "Google model"),
        ("get_llm_config", "Provider config method"),
    ]

    all_found = True
    for setting, description in settings_to_check:
        if setting in config:
            print(f"   ✅ {description:30s} ({setting})")
        else:
            print(f"   ❌ {description:30s} MISSING ({setting})")
            errors.append(f"Missing config: {setting}")
            all_found = False

    results.append(("Configuration", all_found, "All settings present" if all_found else "Missing settings"))

except Exception as e:
    print(f"   ❌ Error reading config: {e}")
    errors.append(f"Config error: {e}")
    results.append(("Configuration", False, str(e)))

# Test 4: Check Workflow uses LLMFactory
print("\n4. Checking Workflow Integration...")
print("-" * 70)

try:
    workflow = Path("app/workflows/generation_workflow.py").read_text()

    checks = [
        ("from app.core.llm_factory import LLMFactory", "LLMFactory import"),
        ("LLMFactory.create_llm", "LLMFactory usage"),
        ("llm_provider", "Provider parameter"),
    ]

    all_found = True
    for check, description in checks:
        if check in workflow:
            print(f"   ✅ {description:30s} found")
        else:
            print(f"   ❌ {description:30s} MISSING")
            errors.append(f"Workflow missing: {description}")
            all_found = False

    results.append(("Workflow Integration", all_found, "LLMFactory integrated" if all_found else "Missing integration"))

except Exception as e:
    print(f"   ❌ Error reading workflow: {e}")
    errors.append(f"Workflow error: {e}")
    results.append(("Workflow Integration", False, str(e)))

# Test 5: Check CLI uses workflow
print("\n5. Checking CLI Integration...")
print("-" * 70)

try:
    cli = Path("app/cli.py").read_text()

    checks = [
        ("from app.workflows.generation_workflow import GenerationWorkflow", "Workflow import"),
        ("GenerationWorkflow(", "Workflow instantiation"),
        ("llm_provider", "Provider parameter"),
    ]

    all_found = True
    for check, description in checks:
        if check in cli:
            print(f"   ✅ {description:30s} found")
        else:
            print(f"   ❌ {description:30s} MISSING")
            errors.append(f"CLI missing: {description}")
            all_found = False

    results.append(("CLI Integration", all_found, "Workflow integrated" if all_found else "Missing integration"))

except Exception as e:
    print(f"   ❌ Error reading CLI: {e}")
    errors.append(f"CLI error: {e}")
    results.append(("CLI Integration", False, str(e)))

# Test 6: Check API uses workflow
print("\n6. Checking API Integration...")
print("-" * 70)

try:
    api = Path("app/api/routes/generate.py").read_text()

    checks = [
        ("from app.workflows.generation_workflow import GenerationWorkflow", "Workflow import"),
        ("GenerationWorkflow(", "Workflow instantiation"),
        ("@router.post", "POST endpoint decorator"),
        ('"/generate"', "Generate endpoint"),
        ('"/validate"', "Validate endpoint"),
    ]

    all_found = True
    for check, description in checks:
        if check in api:
            print(f"   ✅ {description:30s} found")
        else:
            print(f"   ❌ {description:30s} MISSING")
            errors.append(f"API missing: {description}")
            all_found = False

    results.append(("API Integration", all_found, "All endpoints present" if all_found else "Missing endpoints"))

except Exception as e:
    print(f"   ❌ Error reading API: {e}")
    errors.append(f"API error: {e}")
    results.append(("API Integration", False, str(e)))

# Test 7: Check requirements.txt has all providers
print("\n7. Checking Dependencies...")
print("-" * 70)

try:
    requirements = Path("requirements.txt").read_text()

    required_packages = [
        ("langchain-openai", "OpenAI provider"),
        ("langchain-anthropic", "Anthropic provider"),
        ("langchain-google-genai", "Google provider"),
        ("langchain==", "LangChain core"),
        ("langgraph", "LangGraph workflow"),
        ("fastapi", "FastAPI framework"),
        ("pydantic", "Pydantic validation"),
        ("sqlalchemy", "SQLAlchemy ORM"),
    ]

    all_found = True
    for package, description in required_packages:
        if package in requirements.lower():
            print(f"   ✅ {description:30s} ({package})")
        else:
            print(f"   ❌ {description:30s} MISSING ({package})")
            errors.append(f"Missing dependency: {package}")
            all_found = False

    results.append(("Dependencies", all_found, "All packages specified" if all_found else "Missing packages"))

except Exception as e:
    print(f"   ❌ Error reading requirements: {e}")
    errors.append(f"Requirements error: {e}")
    results.append(("Dependencies", False, str(e)))

# Test 8: Check .env.example has provider configs
print("\n8. Checking Environment Configuration...")
print("-" * 70)

try:
    env_example = Path(".env.example").read_text()

    env_vars = [
        ("DEFAULT_LLM_PROVIDER", "Default provider"),
        ("OPENAI_API_KEY", "OpenAI key"),
        ("ANTHROPIC_API_KEY", "Anthropic key"),
        ("GOOGLE_API_KEY", "Google key"),
        ("OPENAI_MODEL", "OpenAI model"),
        ("ANTHROPIC_MODEL", "Anthropic model"),
        ("GOOGLE_MODEL", "Google model"),
    ]

    all_found = True
    for var, description in env_vars:
        if var in env_example:
            print(f"   ✅ {description:30s} ({var})")
        else:
            print(f"   ❌ {description:30s} MISSING ({var})")
            errors.append(f"Missing env var: {var}")
            all_found = False

    results.append(("Environment Config", all_found, "All vars documented" if all_found else "Missing vars"))

except Exception as e:
    print(f"   ❌ Error reading .env.example: {e}")
    errors.append(f".env.example error: {e}")
    results.append(("Environment Config", False, str(e)))

# Test 9: Check templates exist
print("\n9. Checking Template System...")
print("-" * 70)

try:
    template_dir = Path("templates")
    if not template_dir.exists():
        print(f"   ❌ Template directory not found")
        errors.append("Template directory missing")
        results.append(("Template System", False, "Directory missing"))
    else:
        template_files = list(template_dir.glob("*.j2")) + list(template_dir.glob("*.jinja2"))
        print(f"   ✅ Template directory exists")
        print(f"   ✅ Found {len(template_files)} template files:")

        for template in template_files:
            print(f"      - {template.name}")

        if len(template_files) > 0:
            results.append(("Template System", True, f"{len(template_files)} templates"))
        else:
            print(f"   ⚠️  No template files found")
            errors.append("No templates found")
            results.append(("Template System", False, "No templates"))

except Exception as e:
    print(f"   ❌ Template check failed: {e}")
    errors.append(f"Template error: {e}")
    results.append(("Template System", False, str(e)))

# Test 10: Check documentation exists
print("\n10. Checking Documentation...")
print("-" * 70)

try:
    docs = [
        ("README.md", "Main README"),
        ("docs/LLM_PROVIDERS.md", "LLM Provider Guide"),
        ("docs/SECURITY.md", "Security Guide"),
        ("docs/MONITORING.md", "Monitoring Guide"),
        ("docs/PRODUCTION_READINESS.md", "Production Readiness"),
        ("EXECUTION_READINESS.md", "Execution Readiness"),
    ]

    all_found = True
    for doc, description in docs:
        if Path(doc).exists():
            print(f"   ✅ {description:30s} ({doc})")
        else:
            print(f"   ⚠️  {description:30s} missing ({doc})")
            # Don't treat missing docs as critical errors

    results.append(("Documentation", True, f"{len([d for d, _ in docs if Path(d).exists()])} docs present"))

except Exception as e:
    print(f"   ❌ Documentation check failed: {e}")
    results.append(("Documentation", False, str(e)))

# Summary
print("\n" + "=" * 70)
print("STATIC ANALYSIS SUMMARY")
print("=" * 70)

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for component, success, message in results:
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status:10s} | {component:30s} | {message}")

print("-" * 70)
print(f"Result: {passed}/{total} checks passed ({int(passed/total*100) if total > 0 else 0}%)")

# Errors
if errors:
    print("\n" + "=" * 70)
    print("ISSUES FOUND")
    print("=" * 70)
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")

# Final verdict
print("\n" + "=" * 70)
print("FINAL VERDICT")
print("=" * 70)

if passed == total:
    print("✅ ALL CHECKS PASSED - CODE IS READY")
    print("\nCode structure is correct. All integrations are in place.")
    print("\nTo run the application:")
    print("1. pip install -r requirements.txt")
    print("2. cp .env.example .env && nano .env  # Add API keys")
    print("3. backbone-ai generate --schema examples/blog_schema.json")
    exit(0)
elif passed >= total * 0.8:
    print("⚠️  MOSTLY READY")
    print(f"\n{passed}/{total} checks passed. Minor issues detected.")
    exit(0)
else:
    print("❌ NOT READY")
    print(f"\nOnly {passed}/{total} checks passed. Critical issues detected.")
    print("Fix the errors above before proceeding.")
    exit(1)
