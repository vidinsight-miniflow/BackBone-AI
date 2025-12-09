"""
CLI interface for BackBone-AI.
Provides command-line tools for code generation.
"""

import asyncio
import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.table import Table

from app.core.config import settings
from app.core.logger import get_logger
from app.workflows.generation_workflow import GenerationWorkflow

app = typer.Typer(
    name="backbone-ai",
    help="AI-driven code generation for FastAPI and SQLAlchemy backends",
    add_completion=False,
)

console = Console()
logger = get_logger(__name__)


@app.command()
def version():
    """Show BackBone-AI version."""
    console.print(
        Panel(
            f"[bold cyan]{settings.app_name}[/bold cyan]\n"
            f"Version: [yellow]{settings.app_version}[/yellow]\n"
            f"Environment: [green]{settings.app_env}[/green]",
            title="BackBone-AI",
            border_style="cyan",
        )
    )


@app.command()
def generate(
    schema: Path = typer.Option(
        ...,
        "--schema",
        "-s",
        help="Path to JSON schema file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
    output: Path = typer.Option(
        "./generated_project",
        "--output",
        "-o",
        help="Output directory for generated code",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing files",
    ),
):
    """
    Generate backend code from JSON schema.

    Example:
        backbone-ai generate --schema examples/simple_schema.json --output ./my_project
    """
    console.print(f"\n[bold cyan]BackBone-AI Code Generator[/bold cyan]\n")

    try:
        # Load schema
        console.print(f"📄 Loading schema from: [yellow]{schema}[/yellow]")
        with open(schema, "r") as f:
            schema_data = json.load(f)

        project_name = schema_data.get("project_name", "UnnamedProject")
        console.print(f"🎯 Project: [bold green]{project_name}[/bold green]")
        console.print(f"📁 Output directory: [yellow]{output}[/yellow]\n")

        # Check if output directory exists
        if output.exists() and not force:
            console.print(
                f"[bold red]Error:[/bold red] Output directory already exists: {output}"
            )
            console.print("Use --force to overwrite existing files")
            raise typer.Exit(code=1)

        # Create output directory
        output.mkdir(parents=True, exist_ok=True)

        # Generate code using workflow
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🤖 Generating code...", total=None)

            # Run workflow
            workflow = GenerationWorkflow(llm_provider=settings.default_llm_provider)
            final_state = asyncio.run(workflow.run(schema_data))

            progress.update(task, completed=True)

        # Check for errors
        if final_state.get("errors"):
            console.print("\n[bold red]❌ Generation failed with errors:[/bold red]")
            for error in final_state["errors"]:
                console.print(f"  • {error}")
            raise typer.Exit(code=1)

        # Write generated files to disk
        generated_files = final_state.get("generated_files", {})
        if not generated_files:
            console.print("[yellow]⚠️  No files were generated[/yellow]")
            raise typer.Exit(code=1)

        console.print(f"\n[bold green]✅ Successfully generated {len(generated_files)} files![/bold green]\n")

        # Write files
        for file_path, content in generated_files.items():
            full_path = output / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            console.print(f"  ✓ {file_path}")

        # Show summary
        summary = final_state.get("generation_summary", {})
        if summary:
            console.print(f"\n[bold cyan]Summary:[/bold cyan]")
            console.print(f"  • Models: {summary.get('total_models', 0)}")
            console.print(f"  • Columns: {summary.get('total_columns', 0)}")
            console.print(f"  • Relationships: {summary.get('total_relationships', 0)}")

        console.print(f"\n[bold green]📁 Output directory: {output}[/bold green]\n")

    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON schema: {e}")
        logger.error(f"JSON decode error: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        logger.error(f"Generation failed: {e}", exc_info=True)
        raise typer.Exit(code=1)


@app.command()
def validate(
    schema: Path = typer.Option(
        ...,
        "--schema",
        "-s",
        help="Path to JSON schema file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
    ),
):
    """
    Validate a JSON schema without generating code.

    Example:
        backbone-ai validate --schema examples/simple_schema.json
    """
    console.print(f"\n[bold cyan]Schema Validator[/bold cyan]\n")

    try:
        # Load schema
        console.print(f"📄 Loading schema from: [yellow]{schema}[/yellow]")
        with open(schema, "r") as f:
            schema_data = json.load(f)

        console.print(f"✅ JSON syntax is valid\n")

        # Run validation using workflow
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🔍 Validating schema...", total=None)

            workflow = GenerationWorkflow(llm_provider=settings.default_llm_provider)
            result = asyncio.run(workflow.validate_only(schema_data))

            progress.update(task, completed=True)

        # Display results
        status = result.get("status", "unknown")
        if status == "passed":
            console.print("\n[bold green]✅ Validation passed![/bold green]\n")
        elif status == "passed_with_warnings":
            console.print("\n[bold yellow]⚠️  Validation passed with warnings[/bold yellow]\n")
        else:
            console.print("\n[bold red]❌ Validation failed[/bold red]\n")

        # Show errors
        errors = result.get("errors", [])
        if errors:
            console.print("[bold red]Errors:[/bold red]")
            for error in errors:
                console.print(f"  • {error.get('message', error)}")
            console.print()

        # Show warnings
        warnings = result.get("warnings", [])
        if warnings:
            console.print("[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                console.print(f"  • {warning.get('message', warning)}")
            console.print()

        # Show info
        info_items = result.get("info", [])
        if info_items:
            console.print("[bold cyan]Info:[/bold cyan]")
            for info in info_items:
                console.print(f"  • {info.get('message', info)}")
            console.print()

        # Show build order
        dependency_analysis = result.get("dependency_analysis", {})
        if dependency_analysis.get("build_order"):
            console.print("[bold cyan]Build Order:[/bold cyan]")
            for i, table in enumerate(dependency_analysis["build_order"], 1):
                console.print(f"  {i}. {table}")
            console.print()

        # Exit with appropriate code
        if status == "failed":
            raise typer.Exit(code=1)

    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error:[/bold red] Invalid JSON: {e}")
        raise typer.Exit(code=1)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command()
def config():
    """Show current configuration."""
    console.print("\n[bold cyan]Current Configuration[/bold cyan]\n")

    console.print(f"App Name: [yellow]{settings.app_name}[/yellow]")
    console.print(f"Version: [yellow]{settings.app_version}[/yellow]")
    console.print(f"Environment: [yellow]{settings.app_env}[/yellow]")
    console.print(f"Debug: [yellow]{settings.debug}[/yellow]")
    console.print(f"Log Level: [yellow]{settings.log_level}[/yellow]")
    console.print(f"\nDefault LLM Provider: [yellow]{settings.default_llm_provider}[/yellow]")
    console.print(f"Output Directory: [yellow]{settings.output_dir}[/yellow]")
    console.print(f"Template Directory: [yellow]{settings.template_dir}[/yellow]")
    console.print(f"\nAuto Format: [yellow]{settings.auto_format}[/yellow]")
    console.print(f"Auto Lint: [yellow]{settings.auto_lint}[/yellow]\n")


def main():
    """Main entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
