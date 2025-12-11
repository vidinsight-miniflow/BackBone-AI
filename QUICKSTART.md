# 🚀 Quick Start Guide

Get BackBone-AI running in 5 minutes.

---

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** Version pins removed for maximum compatibility. If you encounter conflicts, create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

---

## 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit and add your API key
nano .env
```

**Minimum configuration:**
```bash
# Choose ONE provider
DEFAULT_LLM_PROVIDER=openai

# Add its API key
OPENAI_API_KEY=sk-your-key-here
```

**Provider options:**
- `openai` - Fast, high quality (requires OPENAI_API_KEY)
- `anthropic` - Best for complex schemas (requires ANTHROPIC_API_KEY)
- `google` - Most cost-effective (requires GOOGLE_API_KEY)

---

## 3. Generate Your First Project

```bash
# Use the simple blog example
backbone-ai generate \
  --schema examples/simple_schema.json \
  --output ./my_blog

# Or use the CLI without flags
backbone-ai generate
# Then follow the prompts
```

---

## 4. Check Generated Code

```bash
cd my_blog
tree .

# You should see:
# ├── models/
# │   ├── __init__.py
# │   ├── database.py
# │   ├── mixins.py
# │   ├── user.py
# │   └── post.py
# └── README.md
```

---

## 5. Use the Generated Models

```python
from models.database import create_tables, SessionLocal
from models.user import User
from models.post import Post

# Create tables
create_tables()

# Create a session
db = SessionLocal()

# Create a user
user = User(
    username="john_doe",
    email="john@example.com",
    status="active"
)
db.add(user)
db.commit()

# Create a post
post = Post(
    title="My First Post",
    content="Hello, World!",
    author_id=user.id,
    status="published"
)
db.add(post)
db.commit()

# Query
all_users = db.query(User).all()
print(f"Found {len(all_users)} users")

db.close()
```

---

## Common Issues

### ImportError: No module named 'X'

**Fix:** Install dependencies
```bash
pip install -r requirements.txt
```

### No API key configured

**Fix:** Add API key to .env
```bash
echo "OPENAI_API_KEY=sk-your-key" >> .env
```

### Rate limit exceeded

**Fix:** Use a different provider or wait
```bash
# Switch to Google (cheaper, higher limits)
DEFAULT_LLM_PROVIDER=google
GOOGLE_API_KEY=your-google-key
```

---

## Next Steps

- 📖 Read [LLM_PROVIDERS.md](docs/LLM_PROVIDERS.md) for provider comparison
- 🔒 Read [SECURITY.md](docs/SECURITY.md) for production deployment
- 📊 Read [MONITORING.md](docs/MONITORING.md) for observability
- 🏗️ Read [ARCHITECTURE.md](docs/ARCHITECTURE.md) for system design

---

## API Mode

Start the REST API:

```bash
uvicorn app.api.main:app --reload
```

Then visit: http://localhost:8000/docs

Generate code via API:

```bash
curl -X POST http://localhost:8000/api/v1/generate \
  -H "Content-Type: application/json" \
  -d @examples/simple_schema.json
```

---

## Example Schemas

Try different complexity levels:

```bash
# Simple (2 tables)
backbone-ai generate --schema examples/simple_schema.json

# Medium (5 tables)
backbone-ai generate --schema examples/blog_schema.json

# Complex (10+ tables)
backbone-ai generate --schema examples/ecommerce_schema.json
```

---

## Tips

1. **Start simple** - Use simple_schema.json first
2. **Check output** - Review generated code before using
3. **Customize** - Edit templates in `templates/` directory
4. **Test** - Run `python test_static_analysis.py` to verify setup
5. **Save money** - Use Google Gemini for testing ($0.001/1K tokens vs $0.03 for GPT-4)

---

## Help

- Run tests: `python test_static_analysis.py`
- Check config: `backbone-ai config`
- Get help: `backbone-ai --help`
- Report issues: https://github.com/vidinsight-miniflow/BackBone-AI/issues
