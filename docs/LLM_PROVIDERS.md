# 🤖 LLM Provider Guide

BackBone-AI supports **3 major LLM providers** with flexible per-agent configuration.

---

## Supported Providers

| Provider | Models | Best For | Cost |
|----------|--------|----------|------|
| **OpenAI** | GPT-4 Turbo, GPT-4, GPT-3.5 | General purpose, fast | $$ |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | Complex reasoning, long context | $$$ |
| **Google** | Gemini 1.5 Pro, Gemini 1.5 Flash | Fast, cost-effective | $ |

---

## Quick Start

### 1. Configure API Keys

Add your API keys to `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-your-openai-key-here
OPENAI_MODEL=gpt-4-turbo-preview

# Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Google Gemini
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_MODEL=gemini-1.5-pro
```

### 2. Set Default Provider

```bash
# Choose your default provider
DEFAULT_LLM_PROVIDER=openai  # or anthropic or google
```

### 3. Test Configuration

```bash
# Test without API calls (checks config only)
python test_llm_providers.py

# Test with live API calls
RUN_LIVE_TESTS=true python test_llm_providers.py
```

---

## Provider Details

### 🟢 OpenAI

**Best for:** General purpose code generation, fast responses

**Available Models:**
```bash
OPENAI_MODEL=gpt-4-turbo-preview  # Best quality (128K context)
OPENAI_MODEL=gpt-4                # High quality (8K context)
OPENAI_MODEL=gpt-3.5-turbo        # Fast and cheap (16K context)
```

**Configuration:**
```bash
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_TEMPERATURE=0.1
OPENAI_MAX_TOKENS=4096
```

**API Key:** Get from https://platform.openai.com/api-keys

**Pricing (as of 2024):**
- GPT-4 Turbo: $0.01/$0.03 per 1K tokens (input/output)
- GPT-4: $0.03/$0.06 per 1K tokens
- GPT-3.5 Turbo: $0.0005/$0.0015 per 1K tokens

**Pros:**
- ✅ Fast response times
- ✅ Excellent code generation
- ✅ Good documentation
- ✅ Reliable API

**Cons:**
- ❌ More expensive than Gemini
- ❌ Shorter context than Claude

---

### 🔵 Anthropic Claude

**Best for:** Complex architectural planning, long context understanding

**Available Models:**
```bash
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # Latest, best balance (200K context)
ANTHROPIC_MODEL=claude-3-opus-20240229      # Most capable (200K context)
ANTHROPIC_MODEL=claude-3-sonnet-20240229    # Balanced (200K context)
ANTHROPIC_MODEL=claude-3-haiku-20240307     # Fast and cheap (200K context)
```

**Configuration:**
```bash
ANTHROPIC_API_KEY=sk-ant-your-key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
ANTHROPIC_TEMPERATURE=0.1
ANTHROPIC_MAX_TOKENS=4096
```

**API Key:** Get from https://console.anthropic.com/

**Pricing (as of 2024):**
- Claude 3.5 Sonnet: $0.003/$0.015 per 1K tokens (input/output)
- Claude 3 Opus: $0.015/$0.075 per 1K tokens
- Claude 3 Sonnet: $0.003/$0.015 per 1K tokens
- Claude 3 Haiku: $0.00025/$0.00125 per 1K tokens

**Pros:**
- ✅ 200K context window (huge!)
- ✅ Excellent reasoning
- ✅ Strong at following instructions
- ✅ Good at architectural planning

**Cons:**
- ❌ Slightly slower than GPT-4
- ❌ More expensive than Gemini

---

### 🔴 Google Gemini

**Best for:** Fast validation, cost-effective operations

**Available Models:**
```bash
GOOGLE_MODEL=gemini-1.5-pro        # Best quality (2M context!)
GOOGLE_MODEL=gemini-1.5-flash      # Fast and cheap (1M context)
GOOGLE_MODEL=gemini-pro            # Standard (32K context)
```

**Configuration:**
```bash
GOOGLE_API_KEY=your-google-key
GOOGLE_MODEL=gemini-1.5-pro
GOOGLE_TEMPERATURE=0.1
```

**API Key:** Get from https://makersuite.google.com/app/apikey

**Pricing (as of 2024):**
- Gemini 1.5 Pro: $0.00125/$0.005 per 1K tokens (input/output)
- Gemini 1.5 Flash: $0.000075/$0.0003 per 1K tokens
- Gemini Pro: Free tier available, then $0.000125/$0.000375 per 1K tokens

**Pros:**
- ✅ **Extremely cost-effective**
- ✅ Massive context (up to 2M tokens!)
- ✅ Very fast (Flash model)
- ✅ Good code understanding

**Cons:**
- ❌ Sometimes less consistent than GPT-4/Claude
- ❌ Newer, less community knowledge

---

## Advanced Configuration

### Per-Agent Provider Selection

You can use different providers for different agents:

```bash
# Use Claude for architectural planning (long context)
ARCHITECT_LLM_PROVIDER=anthropic
ARCHITECT_MODEL=claude-3-5-sonnet-20241022

# Use GPT-4 for code generation (high quality)
CODE_GENERATOR_LLM_PROVIDER=openai
CODE_GENERATOR_MODEL=gpt-4-turbo-preview

# Use Gemini Flash for validation (fast and cheap)
VALIDATOR_LLM_PROVIDER=google
VALIDATOR_MODEL=gemini-1.5-flash

# Use GPT-4 for schema validation (accurate)
SCHEMA_VALIDATOR_LLM_PROVIDER=openai
SCHEMA_VALIDATOR_MODEL=gpt-4-turbo-preview
```

### Cost Optimization Strategy

**Budget Setup (Most Cost-Effective):**
```bash
DEFAULT_LLM_PROVIDER=google
SCHEMA_VALIDATOR_LLM_PROVIDER=google
ARCHITECT_LLM_PROVIDER=google
CODE_GENERATOR_LLM_PROVIDER=google
VALIDATOR_LLM_PROVIDER=google

# All agents use Gemini
# Cost: ~$0.10-0.50 per generation
```

**Balanced Setup (Quality + Cost):**
```bash
DEFAULT_LLM_PROVIDER=openai

# Use GPT-4 for critical tasks
SCHEMA_VALIDATOR_LLM_PROVIDER=openai
SCHEMA_VALIDATOR_MODEL=gpt-4-turbo-preview

CODE_GENERATOR_LLM_PROVIDER=openai
CODE_GENERATOR_MODEL=gpt-4-turbo-preview

# Use Gemini for validation
VALIDATOR_LLM_PROVIDER=google
VALIDATOR_MODEL=gemini-1.5-flash

# Cost: ~$0.50-2.00 per generation
```

**Premium Setup (Maximum Quality):**
```bash
DEFAULT_LLM_PROVIDER=anthropic

# Claude for complex reasoning
ARCHITECT_LLM_PROVIDER=anthropic
ARCHITECT_MODEL=claude-3-5-sonnet-20241022

# GPT-4 for code generation
CODE_GENERATOR_LLM_PROVIDER=openai
CODE_GENERATOR_MODEL=gpt-4-turbo-preview

# GPT-4 for validation
SCHEMA_VALIDATOR_LLM_PROVIDER=openai
SCHEMA_VALIDATOR_MODEL=gpt-4-turbo-preview

# Cost: ~$2.00-5.00 per generation
```

---

## Programmatic Usage

### Using LLM Factory

```python
from app.core.llm_factory import LLMFactory

# Create LLM for specific provider
openai_llm = LLMFactory.create_llm("openai")
claude_llm = LLMFactory.create_llm("anthropic")
gemini_llm = LLMFactory.create_llm("google")

# Override model
gpt4_llm = LLMFactory.create_llm("openai", model="gpt-4")

# Override temperature
creative_llm = LLMFactory.create_llm("anthropic", temperature=0.7)

# Create all agent LLMs from config
agent_llms = LLMFactory.create_agent_llms()
# Returns: {
#   "orchestrator": <LLM>,
#   "schema_validator": <LLM>,
#   "architect": <LLM>,
#   "code_generator": <LLM>,
#   "validator": <LLM>
# }
```

### In Workflow

```python
from app.workflows.generation_workflow import GenerationWorkflow

# Use specific provider for workflow
workflow = GenerationWorkflow(llm_provider="anthropic")
workflow = GenerationWorkflow(llm_provider="google")

# Will use DEFAULT_LLM_PROVIDER if not specified
workflow = GenerationWorkflow()
```

### In CLI

```bash
# Use default provider from .env
backbone-ai generate --schema schema.json

# Override provider for this run
DEFAULT_LLM_PROVIDER=anthropic backbone-ai generate --schema schema.json

# Mix providers
SCHEMA_VALIDATOR_LLM_PROVIDER=openai \
CODE_GENERATOR_LLM_PROVIDER=anthropic \
backbone-ai generate --schema schema.json
```

### Via API

```bash
# API uses provider from .env
curl -X POST http://localhost:8000/api/v1/generate \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d @schema.json
```

---

## Model Selection Guide

### For Schema Validation
**Recommended:** OpenAI GPT-4 Turbo or Claude 3.5 Sonnet

- Needs accuracy for foreign key validation
- Moderate token usage
- Critical for correctness

```bash
SCHEMA_VALIDATOR_LLM_PROVIDER=openai
SCHEMA_VALIDATOR_MODEL=gpt-4-turbo-preview
```

### For Architectural Planning
**Recommended:** Claude 3.5 Sonnet or Claude 3 Opus

- Benefits from long context
- Complex reasoning required
- Needs to understand relationships

```bash
ARCHITECT_LLM_PROVIDER=anthropic
ARCHITECT_MODEL=claude-3-5-sonnet-20241022
```

### For Code Generation
**Recommended:** OpenAI GPT-4 Turbo or Claude 3.5 Sonnet

- Highest token usage
- Needs code quality
- Most critical output

```bash
CODE_GENERATOR_LLM_PROVIDER=openai
CODE_GENERATOR_MODEL=gpt-4-turbo-preview
```

### For Code Validation
**Recommended:** Gemini 1.5 Flash or GPT-3.5 Turbo

- Simple validation checks
- Can be fast and cheap
- Low token usage

```bash
VALIDATOR_LLM_PROVIDER=google
VALIDATOR_MODEL=gemini-1.5-flash
```

---

## Cost Tracking

BackBone-AI tracks token usage via Prometheus metrics:

```promql
# Total tokens used by provider
sum(backbone_llm_tokens_used_total) by (provider)

# Total tokens used by model
sum(backbone_llm_tokens_used_total) by (model)

# Estimated cost (OpenAI GPT-4)
(
  rate(backbone_llm_tokens_used_total{provider="openai",type="prompt"}[1h]) * 0.03 / 1000 +
  rate(backbone_llm_tokens_used_total{provider="openai",type="completion"}[1h]) * 0.06 / 1000
) * 3600
```

See [MONITORING.md](MONITORING.md) for more metrics.

---

## Troubleshooting

### "Invalid API key"

**Problem:** API key not set or incorrect

**Solution:**
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Set in .env
OPENAI_API_KEY=sk-your-real-key-here

# Restart application
```

### "Unsupported LLM provider"

**Problem:** Typo in provider name

**Solution:** Use exact names: `openai`, `anthropic`, or `google`

```bash
# ❌ Wrong
DEFAULT_LLM_PROVIDER=gpt4

# ✅ Correct
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4
```

### "Rate limit exceeded"

**Problem:** Too many API calls

**Solution:**
```bash
# Increase retry delay
LLM_RETRY_DELAY=5

# Reduce max tokens
OPENAI_MAX_TOKENS=2048

# Use slower model with higher limits
OPENAI_MODEL=gpt-3.5-turbo
```

### "Context length exceeded"

**Problem:** Schema too large for model

**Solution:** Use model with larger context:

```bash
# ❌ GPT-3.5 (16K context)
OPENAI_MODEL=gpt-3.5-turbo

# ✅ GPT-4 Turbo (128K context)
OPENAI_MODEL=gpt-4-turbo-preview

# ✅ Claude 3.5 Sonnet (200K context)
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# ✅ Gemini 1.5 Pro (2M context!)
GOOGLE_MODEL=gemini-1.5-pro
```

---

## Testing

### Test Configuration

```bash
# Test all providers (no API calls)
python test_llm_providers.py
```

### Test with Live API Calls

```bash
# Set all required API keys in .env first
RUN_LIVE_TESTS=true python test_llm_providers.py
```

### Test Specific Provider

```python
from app.core.llm_factory import LLMFactory

# Test OpenAI
llm = LLMFactory.create_llm("openai")
response = llm.invoke("Say hello")
print(response.content)

# Test Anthropic
llm = LLMFactory.create_llm("anthropic")
response = llm.invoke("Say hello")
print(response.content)

# Test Google
llm = LLMFactory.create_llm("google")
response = llm.invoke("Say hello")
print(response.content)
```

---

## Best Practices

### 1. Use Multiple Providers

Don't rely on a single provider:

```bash
# Primary
DEFAULT_LLM_PROVIDER=openai

# Backup (if OpenAI is down)
# Change to: DEFAULT_LLM_PROVIDER=anthropic
```

### 2. Optimize for Cost

Use cheaper models for simple tasks:

```bash
# Expensive validation
VALIDATOR_LLM_PROVIDER=openai
VALIDATOR_MODEL=gpt-4

# ✅ Cheaper validation
VALIDATOR_LLM_PROVIDER=google
VALIDATOR_MODEL=gemini-1.5-flash
```

### 3. Monitor Usage

Track costs via Prometheus:

```bash
# Enable metrics
ENABLE_METRICS=true

# Check /metrics endpoint
curl http://localhost:8000/metrics | grep llm_tokens
```

### 4. Test Before Production

```bash
# Test with cheap model first
DEFAULT_LLM_PROVIDER=google
backbone-ai generate --schema test_schema.json

# Then use production model
DEFAULT_LLM_PROVIDER=openai
OPENAI_MODEL=gpt-4-turbo-preview
```

### 5. Set Budget Alerts

Configure Prometheus alerts for costs:

```yaml
# alertmanager.yml
- alert: HighLLMCost
  expr: sum(rate(backbone_llm_tokens_used_total[1h])) * 0.03 / 1000 * 24 * 30 > 1000
  annotations:
    summary: "Monthly LLM cost exceeds $1000"
```

---

## Provider Comparison

### Quick Reference Table

| Feature | OpenAI | Anthropic | Google |
|---------|--------|-----------|--------|
| **Context Window** | 128K | 200K | 2M |
| **Speed** | ⚡⚡⚡ | ⚡⚡ | ⚡⚡⚡⚡ |
| **Cost** | $$ | $$$ | $ |
| **Code Quality** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reasoning** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Reliability** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Best For** | General | Complex | Fast/Cheap |

---

## Additional Resources

- **OpenAI:** https://platform.openai.com/docs
- **Anthropic:** https://docs.anthropic.com
- **Google AI:** https://ai.google.dev/docs
- **LangChain:** https://python.langchain.com/docs/integrations/chat/

---

## Support

For issues with LLM providers:

1. Check API key is valid
2. Run `python test_llm_providers.py`
3. Check provider status pages:
   - OpenAI: https://status.openai.com
   - Anthropic: https://status.anthropic.com
   - Google: https://status.cloud.google.com

4. See [MONITORING.md](MONITORING.md) for debugging
5. Open issue: https://github.com/vidinsight-miniflow/BackBone-AI/issues
