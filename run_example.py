#!/usr/bin/env python3
"""
Run a real-life example of the generation workflow.
"""

import asyncio
import json
from pathlib import Path

from app.workflows.generation_workflow import GenerationWorkflow


async def main():
    """Run the workflow with a real example schema."""
    print("=" * 70)
    print("🚀 Running Real-Life Example: Simple Blog System")
    print("=" * 70)
    print()

    # Load the schema
    schema_path = Path("examples/simple_schema.json")
    print(f"📄 Loading schema from: {schema_path}")
    
    with open(schema_path, "r") as f:
        schema_data = json.load(f)
    
    print(f"   Project: {schema_data['project_name']}")
    print(f"   Database: {schema_data['db_type']}")
    print(f"   Tables: {len(schema_data['schema'])}")
    print()

    # Initialize workflow
    print("🔧 Initializing workflow...")
    workflow = GenerationWorkflow(
        llm_provider="openai",  # or use default from settings
        enable_code_validation=True,
        strict_validation=False,
    )
    print("   ✅ Workflow initialized")
    print()

    # Run the workflow
    print("⚙️  Executing workflow...")
    print("-" * 70)
    
    try:
        final_state = await workflow.run(schema_data)
        
        print("-" * 70)
        print()
        
        # Display results
        print("📊 Workflow Results:")
        print("=" * 70)
        
        # Validation status
        validation_passed = final_state.get("validation_passed", False)
        print(f"✅ Schema Validation: {'PASSED' if validation_passed else 'FAILED'}")
        
        if not validation_passed:
            errors = final_state.get("errors", [])
            print(f"   Errors: {len(errors)}")
            for error in errors[:3]:
                print(f"   - {error}")
        
        # Architecture plan
        if final_state.get("architecture_plan"):
            plan = final_state["architecture_plan"]
            print(f"✅ Architecture Planning: COMPLETE")
            print(f"   Models planned: {plan.get('total_models', 0)}")
            print(f"   Build order: {', '.join(final_state.get('build_order', []))}")
        
        # Generated files
        generated_files = final_state.get("generated_files", {})
        print(f"✅ Code Generation: COMPLETE")
        print(f"   Files generated: {len(generated_files)}")
        
        if generated_files:
            print("\n   Generated files:")
            for file_path in sorted(generated_files.keys()):
                lines = len(generated_files[file_path].split('\n'))
                print(f"   • {file_path} ({lines} lines)")
        
        # Code validation
        if final_state.get("code_validation_report"):
            validation_report = final_state["code_validation_report"]
            overall_passed = validation_report.get("overall_passed", False)
            status = validation_report.get("status", "unknown")
            print(f"✅ Code Quality Validation: {status.upper()}")
            
            metrics = validation_report.get("metrics", {})
            if metrics:
                print(f"   Total lines: {metrics.get('total_lines', 0)}")
                print(f"   Errors: {metrics.get('total_errors', 0)}")
                print(f"   Warnings: {metrics.get('total_warnings', 0)}")
                score = metrics.get('maintainability_score', 0)
                print(f"   Maintainability score: {score:.1f}/100")
        
        # Errors summary
        errors = final_state.get("errors", [])
        if errors:
            print(f"\n⚠️  Errors: {len(errors)}")
            for error in errors[:5]:
                print(f"   - {error}")
        
        # Warnings summary
        warnings = final_state.get("warnings", [])
        if warnings:
            print(f"\n⚠️  Warnings: {len(warnings)}")
            for warning in warnings[:5]:
                print(f"   - {warning}")
        
        print()
        print("=" * 70)
        
        # Show a sample of generated code
        if generated_files:
            print("\n📝 Sample Generated Code:")
            print("=" * 70)
            
            # Find a model file
            model_file = next(
                (path for path in generated_files.keys() if path.endswith(".py") and "model" not in path.lower() and "__init__" not in path),
                None
            )
            
            if not model_file:
                model_file = next(
                    (path for path in generated_files.keys() if path.endswith(".py") and "__init__" not in path),
                    None
                )
            
            if model_file:
                print(f"\nFile: {model_file}")
                print("-" * 70)
                content = generated_files[model_file]
                # Show first 50 lines
                lines = content.split('\n')
                for i, line in enumerate(lines[:50], 1):
                    print(f"{i:3} | {line}")
                if len(lines) > 50:
                    print(f"... ({len(lines) - 50} more lines)")
        
        print()
        print("=" * 70)
        print("✅ Workflow execution completed successfully!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error during workflow execution: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

