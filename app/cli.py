"""
CLI interface for BackBone-AI.
Provides command-line tools for code generation.
"""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.core.config import settings
from app.core.logger import get_logger

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

        # Generate code (placeholder for now)
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("🤖 Generating code...", total=None)

            # TODO: Implement actual generation logic
            # This will call the orchestrator agent
            console.print(
                "\n[yellow]⚠️  Generation logic not yet implemented[/yellow]"
            )
            console.print("This is a placeholder. Actual agents will be called here.\n")

            progress.update(task, completed=True)

        console.print("[bold green]✅ Generation completed![/bold green]\n")

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

        console.print(f"✅ JSON syntax is valid")

        # TODO: Implement validation logic using Schema Validator Agent
        console.print(
            "\n[yellow]⚠️  Full validation not yet implemented[/yellow]"
        )
        console.print("Schema Validator Agent will be called here.\n")

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
