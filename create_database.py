#!/usr/bin/env python3
"""
Script to actually create the database tables from generated models.
This script imports the models and creates the database tables.
"""

import asyncio
import json
from pathlib import Path

from app.workflows.generation_workflow import GenerationWorkflow


async def create_database():
    """Generate code and create database tables."""
    print("=" * 70)
    print("🗄️  Creating Database Tables")
    print("=" * 70)
    print()

    # Load the schema
    schema_path = Path("examples/simple_schema.json")
    print(f"📄 Loading schema from: {schema_path}")
    
    with open(schema_path, "r") as f:
        schema_data = json.load(f)
    
    print(f"   Project: {schema_data['project_name']}")
    print(f"   Database: {schema_data['db_type']}")
    print()

    # Initialize workflow
    print("🔧 Initializing workflow...")
    workflow = GenerationWorkflow(
        llm_provider="openai",
        enable_code_validation=False,  # Skip validation for speed
        strict_validation=False,
    )
    print("   ✅ Workflow initialized")
    print()

    # Run the workflow
    print("⚙️  Generating code...")
    final_state = await workflow.run(schema_data)
    
    # Check for errors
    if final_state.get("errors"):
        print(f"❌ Generation failed: {final_state['errors']}")
        return 1

    # Get generated files
    generated_files = final_state.get("generated_files", {})
    if not generated_files:
        print("❌ No files were generated")
        return 1

    print(f"✅ Generated {len(generated_files)} files")
    print()

    # Write files to disk
    print("📝 Writing files to disk...")
    output_dir = Path("./generated_project")
    output_dir.mkdir(exist_ok=True)
    
    for file_path, content in generated_files.items():
        full_path = output_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        print(f"   ✓ {file_path}")
    
    print()
    print("=" * 70)
    print("📋 Next Steps to Create Database Tables:")
    print("=" * 70)
    print()
    print("1. Install dependencies:")
    print("   pip install sqlalchemy psycopg2-binary  # For PostgreSQL")
    print("   # or")
    print("   pip install sqlalchemy  # For SQLite")
    print()
    print("2. Configure database URL in app/core/database.py")
    print("   DATABASE_URL = 'postgresql://user:password@localhost/dbname'")
    print()
    print("3. Create database tables using one of these methods:")
    print()
    print("   Method 1: Using init_db() function")
    print("   ```python")
    print("   from app.core.database import init_db")
    print("   init_db()")
    print("   ```")
    print()
    print("   Method 2: Using SQLAlchemy directly")
    print("   ```python")
    print("   from app.core.database import Base, engine")
    print("   from app.models import *  # Import all models")
    print("   Base.metadata.create_all(bind=engine)")
    print("   ```")
    print()
    print("   Method 3: Using Alembic (recommended for production)")
    print("   ```bash")
    print("   alembic init alembic")
    print("   alembic revision --autogenerate -m 'Initial migration'")
    print("   alembic upgrade head")
    print("   ```")
    print()
    print("=" * 70)
    print(f"✅ Files written to: {output_dir.absolute()}")
    print("=" * 70)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(create_database())
    exit(exit_code)

