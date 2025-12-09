# BackBone-AI Architecture

## Overview

BackBone-AI uses a multi-agent architecture powered by LangChain and LangGraph to generate high-quality backend code from JSON schema definitions.

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Input (JSON Schema)                 │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Orchestrator Agent                        │
│  - Coordinates workflow                                      │
│  - Manages state                                             │
│  - Routes between agents                                     │
└─────┬──────────┬──────────┬──────────┬────────────────────┘
      │          │          │          │
      ▼          ▼          ▼          ▼
┌─────────┐ ┌────────┐ ┌─────────┐ ┌──────────┐
│ Schema  │ │Mimar   │ │Code Gen │ │Validator │
│Validator│ │Ajan    │ │Agent    │ │Agent     │
└─────────┘ └────────┘ └─────────┘ └──────────┘
      │          │          │          │
      └──────────┴──────────┴──────────┘
                   │
         ┌─────────▼─────────┐
         │  Tools & Actions  │
         └───────────────────┘
                   │
         ┌─────────▼─────────┐
         │  Generated Code   │
         └───────────────────┘
```

## Agent Details

### 1. Orchestrator Agent

**Role**: Main coordinator and workflow manager

**Responsibilities**:
- Accept user JSON schema input
- Initialize and coordinate all sub-agents
- Manage workflow state through LangGraph
- Handle errors and retries
- Provide progress updates
- Return final results

**LLM**: Claude 3.5 Sonnet (default) - Best for complex reasoning and coordination

**Tools**:
- State management
- Agent spawner
- Progress tracker

---

### 2. Schema Validator Agent

**Role**: Validate input JSON schema

**Responsibilities**:
- Validate JSON syntax
- Check required fields
- Validate ForeignKey references
- Check for circular dependencies
- Validate Enum values
- Ensure table and column naming conventions

**LLM**: GPT-4 Turbo

**Tools**:
- `json_validator_tool`: Parse and validate JSON structure
- `reference_checker_tool`: Validate ForeignKey references
- `dependency_analyzer_tool`: Check for circular dependencies

**Output**: `ValidationReport` with status and detailed errors

---

### 3. Architect Agent (Mimar Ajan)

**Role**: Create architectural plan for code generation

**Responsibilities**:
- Determine table creation order (dependency resolution)
- Select appropriate mixins (TimestampMixin, SoftDeleteMixin)
- Map relationships between tables
- Plan inheritance structure
- Define file structure

**LLM**: GPT-4 Turbo

**Tools**:
- `dependency_resolver_tool`: Calculate correct table order
- `mixin_selector_tool`: Choose appropriate mixins
- `relationship_mapper_tool`: Map all relationships

**Output**: `ArchitecturePlan` with build order and detailed specifications

---

### 4. Code Generator Agent

**Role**: Generate SQLAlchemy model code

**Responsibilities**:
- Generate model classes using templates
- Create proper imports
- Generate Column definitions
- Generate Relationship definitions
- Add type hints and docstrings
- Format code with Black

**LLM**: GPT-4

**Tools**:
- `template_renderer_tool`: Render Jinja2 templates
- `code_formatter_tool`: Format with Black
- `file_writer_tool`: Write files to disk

**Output**: `GeneratedCode` with file paths and contents

---

### 5. Validator Agent

**Role**: Validate generated code quality

**Responsibilities**:
- Check Python syntax
- Validate imports
- Run linting (Ruff)
- Check SQLAlchemy best practices
- Basic security checks

**LLM**: GPT-3.5 Turbo (cost-effective for validation)

**Tools**:
- `syntax_checker_tool`: Validate Python syntax
- `linter_tool`: Run Ruff
- `security_scanner_tool`: Basic security checks

**Output**: `ValidationReport` with code quality assessment

---

## Workflow States

LangGraph manages the workflow through these states:

```python
class ProjectState(TypedDict):
    original_schema: dict          # Input JSON schema
    validation_report: dict         # Schema validation results
    architecture_plan: dict         # Architectural plan
    generated_files: list           # Generated code files
    validation_results: dict        # Code validation results
    current_step: str               # Current workflow step
    errors: list                    # Any errors encountered
```

## Workflow Transitions

```
START
  ↓
[Orchestrator] → Initialize state
  ↓
[Schema Validator] → Validate JSON
  ↓
  ├─ Invalid → Return errors → END
  └─ Valid → Continue
      ↓
[Architect Agent] → Create plan
  ↓
[Code Generator] → Generate code
  ↓
[Validator Agent] → Validate code
  ↓
  ├─ Invalid → Retry (max 3 times) → [Code Generator]
  └─ Valid → Return results → END
```

## Technology Stack

### Core Framework
- **LangChain**: Agent framework and tools
- **LangGraph**: Workflow orchestration
- **LangSmith**: Monitoring and debugging (optional)

### LLM Providers
- **OpenAI GPT-4**: Code generation and planning
- **Anthropic Claude**: Orchestration
- **Google Gemini**: Alternative provider

### Code Generation
- **Jinja2**: Template rendering
- **Black**: Code formatting
- **Ruff**: Linting
- **mypy**: Type checking

### Backend (Generated)
- **SQLAlchemy 2.0**: ORM
- **FastAPI**: Web framework
- **Pydantic**: Data validation

## Configuration

All agents are configured through environment variables:

```bash
# Orchestrator
ORCHESTRATOR_LLM_PROVIDER=anthropic
ORCHESTRATOR_MODEL=claude-3-5-sonnet-20241022

# Schema Validator
SCHEMA_VALIDATOR_LLM_PROVIDER=openai
SCHEMA_VALIDATOR_MODEL=gpt-4-turbo-preview

# Architect
ARCHITECT_LLM_PROVIDER=openai
ARCHITECT_MODEL=gpt-4-turbo-preview

# Code Generator
CODE_GENERATOR_LLM_PROVIDER=openai
CODE_GENERATOR_MODEL=gpt-4

# Validator
VALIDATOR_LLM_PROVIDER=openai
VALIDATOR_MODEL=gpt-3.5-turbo
```

## Error Handling

### Retry Strategy

All agents use exponential backoff retry:
- Max retries: 3 (configurable)
- Initial delay: 2 seconds
- Exponential multiplier: 2
- Max delay: 10 seconds

### Error Recovery

1. **Schema Validation Errors**: Return immediately to user with detailed errors
2. **Planning Errors**: Retry with adjusted context
3. **Code Generation Errors**: Retry up to 3 times with validation feedback
4. **Validation Errors**: Return to code generator with specific issues

## Monitoring

### LangSmith Integration

Enable tracing for debugging:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-key
LANGCHAIN_PROJECT=BackBone-AI
```

### Logging

- **Console**: Colored output with Loguru
- **Files**: Error logs and debug logs in `logs/` directory
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL

## Performance

### Agent Selection Strategy

- **Orchestrator**: Claude (best reasoning, cost-effective at scale)
- **Planning**: GPT-4 Turbo (excellent at structured planning)
- **Code Generation**: GPT-4 (highest code quality)
- **Validation**: GPT-3.5 Turbo (cost-effective for simple validation)

### Optimization

- Agents run sequentially (required for dependencies)
- Tools can be parallelized within agents
- Caching for repeated operations
- Template pre-compilation

## Security

### API Key Management
- Environment variables only
- Never commit to version control
- Use different keys for different environments

### Generated Code Security
- SQL injection prevention (parameterized queries)
- Input validation in generated code
- Security linting with Ruff

## Scalability

### Current Phase
- Single-threaded execution
- Suitable for projects with 1-50 tables

### Future Enhancements
- Parallel agent execution where possible
- Distributed processing for large schemas
- Incremental code generation
- Code update/migration support

## Next Steps

1. Implement Schema Validator Agent
2. Implement Architect Agent
3. Implement Code Generator Agent
4. Implement Validator Agent
5. Build LangGraph workflow
6. Add comprehensive testing
7. Add monitoring and metrics
