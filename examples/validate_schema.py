"""
Example script for using Schema Validator Agent.

This script demonstrates how to use the Schema Validator Agent
to validate a JSON schema definition.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.agents.schema_validator_agent import SchemaValidatorAgent
from app.schemas.agent_output_schema import SchemaValidatorOutput


async def validate_schema_file(schema_file: str) -> None:
    """
    Validate a schema file.

    Args:
        schema_file: Path to JSON schema file
    """
    print(f"\n{'=' * 80}")
    print(f"Validating schema: {schema_file}")
    print(f"{'=' * 80}\n")

    # Read schema file
    try:
        with open(schema_file, "r") as f:
            schema_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Schema file not found: {schema_file}")
        return
    except Exception as e:
        print(f"❌ Error reading schema file: {e}")
        return

    # Initialize agent (without LLM for direct tool use)
    agent = SchemaValidatorAgent(use_llm=False)

    # Run validation
    try:
        result = await agent.run({"schema": schema_content})

        # Parse result into output schema
        output = SchemaValidatorOutput.model_validate(result)

        # Print detailed report
        print(output.to_detailed_string())

        # Return exit code based on validation status
        if output.is_valid:
            print("\n✅ Schema validation PASSED!")
            sys.exit(0)
        else:
            print("\n❌ Schema validation FAILED!")
            sys.exit(1)

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(2)


async def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python validate_schema.py <schema_file.json>")
        print("\nExample:")
        print("  python examples/validate_schema.py examples/simple_schema.json")
        sys.exit(1)

    schema_file = sys.argv[1]
    await validate_schema_file(schema_file)


if __name__ == "__main__":
    asyncio.run(main())
