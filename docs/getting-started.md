# Getting Started with BackBone-AI

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager
- LLM API key (OpenAI, Anthropic, or Google)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/vidinsight-miniflow/BackBone-AI.git
cd BackBone-AI
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and add your API keys:

```bash
# Choose your provider
DEFAULT_LLM_PROVIDER=openai

# Add your API key
OPENAI_API_KEY=sk-your-actual-key-here
```

## Quick Start

### CLI Usage

#### 1. Validate a Schema

```bash
backbone-ai validate --schema examples/simple_schema.json
```

#### 2. Generate Code

```bash
backbone-ai generate \
  --schema examples/simple_schema.json \
  --output ./my_project
```

#### 3. Check Configuration

```bash
backbone-ai config
```

#### 4. Show Version

```bash
backbone-ai version
```

### API Usage

#### 1. Start the API Server

```bash
uvicorn app.api.main:app --reload
```

Or:

```bash
python -m app.api.main
```

#### 2. Access API Documentation

Open your browser:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### 3. Health Check

```bash
curl http://localhost:8000/health
```

#### 4. Generate Code via API

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d @examples/simple_schema.json
```

## Creating Your First Schema

### Basic Schema Structure

```json
{
  "project_name": "MyProject",
  "db_type": "postgresql",
  "description": "My awesome project",
  "schema": [
    {
      "table_name": "users",
      "class_name": "User",
      "description": "User accounts",
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

### Column Types

Supported column types:

- `Integer` - Integer numbers
- `String` - Variable length strings (specify `length`)
- `Text` - Long text
- `Boolean` - True/False
- `DateTime` - Date and time
- `Date` - Date only
- `Time` - Time only
- `Numeric` - Decimal numbers (specify `precision` and `scale`)
- `Float` - Floating point
- `Enum` - Enumeration (specify `values` array)
- `ForeignKey` - Foreign key (specify `target`)

### Column Example

```json
{
  "name": "username",
  "type": "String",
  "length": 50,
  "unique": true,
  "nullable": false,
  "index": true,
  "description": "Unique username"
}
```

### Foreign Key Example

```json
{
  "name": "author_id",
  "type": "ForeignKey",
  "target": "users.id",
  "nullable": false,
  "on_delete": "CASCADE",
  "description": "Author reference"
}
```

### Relationship Types

- `one_to_many` - One-to-many relationship
- `many_to_one` - Many-to-one relationship
- `many_to_many` - Many-to-many (requires junction table)

### Relationship Example

```json
{
  "target_table": "posts",
  "target_class": "Post",
  "type": "one_to_many",
  "back_populates": "author",
  "description": "User's posts"
}
```

## Examples

### Simple Blog System

See: `examples/simple_schema.json`

Two tables:
- `users` (with timestamps)
- `posts` (with timestamps and soft delete)

Relationship: User has many Posts

### E-Commerce System

See: `examples/complex_schema.json`

Five tables:
- `users`
- `products`
- `orders`
- `order_items`
- `reviews`

Multiple relationships with proper foreign keys

## Common Tasks

### Change LLM Provider

Edit `.env`:

```bash
DEFAULT_LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Enable LangSmith Tracing

For debugging and monitoring:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=BackBone-AI
```

### Customize Agent Models

Edit `.env`:

```bash
# Use different models for different agents
ORCHESTRATOR_MODEL=claude-3-5-sonnet-20241022
ARCHITECT_MODEL=gpt-4-turbo-preview
CODE_GENERATOR_MODEL=gpt-4
```

### Auto-format Generated Code

Enabled by default. To disable:

```bash
AUTO_FORMAT=False
AUTO_LINT=False
```

## Troubleshooting

### API Key Errors

Error: `OpenAI API key not found`

Solution: Check your `.env` file and ensure the key is set:

```bash
OPENAI_API_KEY=sk-your-actual-key-here
```

### Import Errors

Error: `ModuleNotFoundError: No module named 'langchain'`

Solution: Reinstall dependencies:

```bash
pip install -r requirements.txt
```

### Schema Validation Errors

Check your JSON syntax:

```bash
# Validate JSON
python -m json.tool examples/simple_schema.json

# Or use jq
jq . examples/simple_schema.json
```

### Port Already in Use

Error: `Address already in use`

Solution: Use a different port:

```bash
uvicorn app.api.main:app --port 8001
```

## Next Steps

- Read [Architecture Guide](architecture.md)
- Explore [Agent Details](agents.md)
- Check [API Reference](api.md)
- See [Project Guide](../GUIDE.md)

## Getting Help

- GitHub Issues: [Report a bug](https://github.com/vidinsight-miniflow/BackBone-AI/issues)
- Discussions: [Ask questions](https://github.com/vidinsight-miniflow/BackBone-AI/discussions)
