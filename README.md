# 🤖 BackBone-AI

**AI-Driven Code Generation for FastAPI & SQLAlchemy**

BackBone AI is an innovative multi-agent system powered by LangChain that transforms JSON schema definitions into production-ready Python backends. Say goodbye to repetitive boilerplate code and hello to rapid, high-quality backend development.

## 🎯 Problem Statement

Building backend systems involves repetitive tasks:
- Creating database models with proper relationships
- Setting up Foreign Keys and constraints
- Configuring mixins (timestamps, soft deletes)
- Writing boilerplate SQLAlchemy code
- Managing dependencies between tables

Existing AI coding assistants struggle with:
- Context window limitations in large projects (20+ tables)
- Tracking complex relationships
- Maintaining consistency across multiple files
- Following project-specific patterns

## 💡 Solution

BackBone-AI uses a **specialized multi-agent architecture** with LangChain to:
- Focus on specific, narrow tasks with high quality output
- Maintain context through structured workflows
- Validate relationships and dependencies
- Generate clean, tested, production-ready code

## 🏗️ Architecture

```
User JSON Schema
       ↓
Orchestrator Agent
       ↓
┌──────┴──────┬──────────┬──────────┐
↓             ↓          ↓          ↓
Schema      Architect  Code Gen  Validator
Validator   Agent      Agent     Agent
```

### Agents

1. **Schema Validator Agent**: Validates JSON structure, ForeignKeys, and relationships
2. **Architect Agent**: Creates dependency order and architectural plan
3. **Code Generator Agent**: Generates SQLAlchemy models using templates
4. **Validator Agent**: Validates generated code for syntax and best practices

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/vidinsight-miniflow/BackBone-AI.git
cd BackBone-AI

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your API keys
```

### Configuration

Edit `.env` file and add your LLM API keys:

```bash
# Choose your preferred provider
DEFAULT_LLM_PROVIDER=openai

# Add your API key
OPENAI_API_KEY=sk-your-key-here
# or
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Usage

Create a JSON schema file (see `examples/simple_schema.json`):

```json
{
  "project_name": "MyBackend",
  "db_type": "postgresql",
  "schema": [
    {
      "table_name": "users",
      "class_name": "User",
      "options": {
        "use_timestamps": true,
        "use_soft_delete": false
      },
      "columns": [...],
      "relationships": [...]
    }
  ]
}
```

Run the generator:

```bash
# CLI mode
backbone-ai generate --schema examples/simple_schema.json --output ./my_project

# API mode
uvicorn app.api.main:app --reload
# Then POST your schema to http://localhost:8000/generate
```

## 📦 Features

### Core Functionality
- ✅ **Multi-Agent System**: Specialized agents for validation, planning, generation, and testing
- ✅ **LangChain Integration**: Powered by LangGraph for robust workflow orchestration
- ✅ **3 LLM Providers**: Full support for **OpenAI GPT**, **Anthropic Claude**, **Google Gemini**
  - Mix and match providers per agent
  - Cost optimization (Gemini ~10x cheaper than GPT-4)
  - 128K-2M token context windows
- ✅ **Smart Validation**: Automatic ForeignKey and relationship validation
- ✅ **Dependency Resolution**: Correct table creation order
- ✅ **Mixin Support**: TimestampMixin, SoftDeleteMixin, and custom mixins
- ✅ **Code Quality**: Auto-formatted with Black, linted with Ruff
- ✅ **Type Safety**: Full type hints with mypy validation

### Production Features
- ✅ **Security**: API key + JWT authentication, 4-tier rate limiting, input validation
- ✅ **Monitoring**: Health checks, Prometheus metrics (26 metrics), LangSmith tracing
- ✅ **REST API**: Full-featured API with OpenAPI documentation
- ✅ **Observability**: Request tracking, error monitoring, cost tracking
- ✅ **Documentation**: Comprehensive guides (Security, Monitoring, API, Architecture)

## 🚀 Production Ready (95%)

BackBone-AI is production-ready with enterprise-grade features:

- **Security**: Dual authentication (API key + JWT), rate limiting, input validation
- **Monitoring**: Health checks, 26 Prometheus metrics, distributed tracing
- **Documentation**: 3000+ lines covering security, monitoring, deployment
- **Testing**: Comprehensive test suite with 15+ test cases
- **Dependencies**: All packages updated to latest secure versions

See [Production Readiness Report](docs/PRODUCTION_READINESS.md) for details.

## 🛠️ Technology Stack

- **AI Framework**: LangChain, LangGraph
- **LLM Providers**: OpenAI GPT-4, Anthropic Claude, Google Gemini
- **Backend**: FastAPI, SQLAlchemy 2.0
- **Database**: PostgreSQL (+ others via SQLAlchemy)
- **Code Quality**: Black, Ruff, mypy
- **Testing**: pytest, pytest-asyncio

## 📖 Documentation

### Core Documentation
- [Architecture Guide](docs/ARCHITECTURE.md) - System design and workflows
- [API Reference](docs/API.md) - REST API endpoints and usage
- [Schema Guide](docs/SCHEMAS.md) - JSON schema format and examples
- [LLM Provider Guide](docs/LLM_PROVIDERS.md) - **OpenAI, Claude, Gemini setup & optimization**
- [Project Guide](GUIDE.md) - Development guide

### Production Documentation
- [Production Readiness](docs/PRODUCTION_READINESS.md) - 95% ready status report
- [Security Guide](docs/SECURITY.md) - Authentication, rate limiting, best practices
- [Monitoring Guide](docs/MONITORING.md) - Health checks, metrics, observability

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Built on top of [sqlalchemy-engine-kit](https://github.com/your-repo/sqlalchemy-engine-kit)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)
- Inspired by the need for better AI-assisted backend development

## 📞 Support

- GitHub Issues: [Report bugs or request features](https://github.com/vidinsight-miniflow/BackBone-AI/issues)
- Documentation: [Full documentation](https://github.com/vidinsight-miniflow/BackBone-AI/docs)

---

**Status**: 🚧 Alpha - Active Development

Current Phase: Building core agent system and code generation pipeline.
