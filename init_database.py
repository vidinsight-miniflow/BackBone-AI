#!/usr/bin/env python3
"""
Script to actually create database tables.
This imports the generated models and creates the tables.
"""

import sys
import os
from pathlib import Path

# Add generated_project to path
generated_path = Path(__file__).parent / "generated_project"
if not generated_path.exists():
    print(f"❌ Generated project directory not found: {generated_path}")
    print("   Run create_database.py first to generate the files.")
    sys.exit(1)

# Change to generated_project directory so imports work
os.chdir(generated_path)
sys.path.insert(0, str(generated_path))

try:
    # Import database and models
    from app.core.database import Base, engine, init_db
    from app.models import User, Post  # Import all models
    
    print("=" * 70)
    print("🗄️  Creating Database Tables")
    print("=" * 70)
    print()
    
    print("📦 Imported models:")
    print(f"   - User (table: users)")
    print(f"   - Post (table: posts)")
    print()
    
    print("🔧 Creating tables...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    print("✅ Database tables created successfully!")
    print()
    print("Created tables:")
    print("   - users")
    print("   - posts")
    print()
    print("=" * 70)
    print("✅ Database initialization complete!")
    print("=" * 70)
    print()
    print("Note: Make sure your database is running and DATABASE_URL is correct.")
    print("      Check app/core/database.py for configuration.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print()
    print("Make sure you've run create_database.py first to generate the files.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error creating database: {e}")
    print()
    print("Common issues:")
    print("  1. Database server is not running")
    print("  2. DATABASE_URL is incorrect")
    print("  3. Database doesn't exist (create it first)")
    print("  4. Missing dependencies (pip install sqlalchemy psycopg2-binary)")
    sys.exit(1)

