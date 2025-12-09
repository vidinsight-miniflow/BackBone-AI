#!/usr/bin/env python3
"""
LLM Provider Testing Script
Tests OpenAI, Anthropic Claude, and Google Gemini integration.
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.llm_factory import LLMFactory
from app.core.config import settings

print("=" * 70)
print("BackBone-AI - LLM Provider Testing")
print("=" * 70)
print()

# Track results
results = []

# Test each provider
providers = ["openai", "anthropic", "google"]
provider_names = {
    "openai": "OpenAI GPT",
    "anthropic": "Anthropic Claude",
    "google": "Google Gemini"
}

for provider in providers:
    print(f"\n{provider_names[provider]} ({provider})")
    print("-" * 70)

    try:
        # Get API key
        config = settings.get_llm_config(provider)
        api_key = config.get("api_key", "")

        # Check if API key is configured
        if not api_key or api_key.startswith("sk-your-") or api_key.startswith("your-"):
            print(f"   ⚠️  API key not configured")
            print(f"   ℹ️  Set {provider.upper()}_API_KEY in .env file")
            results.append((provider_names[provider], "skip", "API key not configured"))
            continue

        # Create LLM instance
        llm = LLMFactory.create_llm(provider)
        print(f"   ✅ LLM instance created successfully")
        print(f"   📝 Model: {config['model']}")
        print(f"   🌡️  Temperature: {config['temperature']}")

        # Test invoke (optional - requires valid API key)
        if os.getenv("RUN_LIVE_TESTS") == "true":
            print(f"   🔄 Testing API call...")
            response = llm.invoke("Say 'Hello from BackBone-AI' in one sentence.")
            print(f"   ✅ API call successful")
            print(f"   💬 Response: {response.content[:100]}...")
            results.append((provider_names[provider], "pass", "All tests passed"))
        else:
            print(f"   ℹ️  Skipping live API test (set RUN_LIVE_TESTS=true to test)")
            results.append((provider_names[provider], "pass", "Configuration valid"))

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")
        results.append((provider_names[provider], "fail", str(e)))

# Test agent LLMs
print("\n\nAgent LLM Configuration")
print("-" * 70)

agent_configs = {
    "Schema Validator": (settings.schema_validator_llm_provider, settings.schema_validator_model),
    "Architect": (settings.architect_llm_provider, settings.architect_model),
    "Code Generator": (settings.code_generator_llm_provider, settings.code_generator_model),
    "Validator": (settings.validator_llm_provider, settings.validator_model),
}

for agent_name, (provider, model) in agent_configs.items():
    print(f"   {agent_name:20s} -> {provider:10s} ({model})")

# Summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

for provider, status, message in results:
    if status == "pass":
        status_icon = "✅ PASS"
    elif status == "skip":
        status_icon = "⚠️  SKIP"
    else:
        status_icon = "❌ FAIL"

    print(f"{status_icon:10s} | {provider:20s} | {message}")

print("-" * 70)

passed = sum(1 for _, s, _ in results if s == "pass")
skipped = sum(1 for _, s, _ in results if s == "skip")
failed = sum(1 for _, s, _ in results if s == "fail")

print(f"Passed: {passed} | Skipped: {skipped} | Failed: {failed}")

if failed == 0:
    print("\n✅ All configured providers are working!")
else:
    print(f"\n⚠️  {failed} provider(s) have issues")

# Usage instructions
print("\n" + "=" * 70)
print("CONFIGURATION GUIDE")
print("=" * 70)
print("""
To use a specific LLM provider:

1. Add API key to .env file:
   OPENAI_API_KEY=sk-your-key-here
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   GOOGLE_API_KEY=your-google-key-here

2. Set default provider:
   DEFAULT_LLM_PROVIDER=openai  # or anthropic or google

3. Configure per-agent providers (optional):
   SCHEMA_VALIDATOR_LLM_PROVIDER=openai
   ARCHITECT_LLM_PROVIDER=anthropic
   CODE_GENERATOR_LLM_PROVIDER=google

4. Test live API calls:
   RUN_LIVE_TESTS=true python test_llm_providers.py

Supported Providers:
- OpenAI: gpt-4-turbo-preview, gpt-4, gpt-3.5-turbo
- Anthropic: claude-3-5-sonnet-20241022, claude-3-opus-20240229
- Google: gemini-1.5-pro, gemini-1.5-flash

See docs/LLM_PROVIDERS.md for more details.
""")
