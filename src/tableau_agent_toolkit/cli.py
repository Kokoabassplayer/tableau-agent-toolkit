"""Typer CLI entry point for tableau-agent-toolkit.

Provides the main CLI application with Phase 1 commands:
- generate: Generate a Tableau workbook from a spec and template
- validate-xsd: Validate a TWB file against pinned XSD schema
- spec init: Generate a starter dashboard_spec.yaml

The entry point is registered in pyproject.toml as:
    tableau-agent-toolkit = "tableau_agent_toolkit.cli:app"
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from tableau_agent_toolkit.spec.io import load_spec
from tableau_agent_toolkit.spec.models import DashboardSpec, WorkbookSpec, TemplateSpec
from tableau_agent_toolkit.templates.registry import TemplateRegistry
from tableau_agent_toolkit.twb.generator import WorkbookGenerator
from tableau_agent_toolkit.validation.xsd import XsdValidator

app = typer.Typer(
    name="tableau-agent-toolkit",
    help="Generate, validate, package, and publish Tableau workbooks from YAML specs.",
    add_completion=False,
    invoke_without_command=True,
)


@app.callback()
def main(ctx: typer.Context) -> None:
    """Tableau Agent Toolkit - deterministic workbook generation from specs."""
    if ctx.invoked_subcommand is None:
        typer.echo(ctx.get_help())


@app.command("generate")
def generate(
    spec_path: Path = typer.Argument(
        ...,
        help="Path to dashboard_spec.yaml",
        exists=True,
    ),
    output: Path = typer.Option(
        "output.twb",
        "--output",
        "-o",
        help="Output TWB path",
    ),
    template: Optional[Path] = typer.Option(
        None,
        "--template",
        help="Override template path (bypasses registry lookup)",
    ),
) -> None:
    """Generate a Tableau workbook from a spec and template.

    Loads the spec YAML, resolves the template, patches the workbook XML,
    and writes the output .twb file.
    """
    spec = load_spec(spec_path)
    registry = TemplateRegistry()
    generator = WorkbookGenerator(template_registry=registry)
    result = generator.generate(spec, output, template_override=template)
    typer.echo(f"Generated: {result.output_path}")
    if result.warnings:
        for w in result.warnings:
            typer.echo(f"Warning: {w}", err=True)


@app.command("validate-xsd")
def validate_xsd(
    twb_path: Path = typer.Argument(
        ...,
        help="Path to .twb file",
        exists=True,
    ),
    version: str = typer.Option(
        "2026.1",
        "--version",
        help="Target Tableau version for XSD selection",
    ),
) -> None:
    """Validate a TWB file against pinned XSD schema.

    Performs structural XML validation against the tableau-document-schemas
    XSD for the specified Tableau version. Reports errors with line, column,
    and message.
    """
    schemas_root = (
        Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas"
    )
    validator = XsdValidator(schemas_root=schemas_root)
    result = validator.validate(twb_path, tableau_version=version)
    if result.valid:
        typer.echo(f"Valid: {twb_path} passes XSD validation for version {version}")
    else:
        typer.echo(f"Invalid: {twb_path} failed XSD validation", err=True)
        for err in result.errors:
            typer.echo(
                f"  Line {err.line}, Column {err.column}: {err.message}", err=True
            )
        sys.exit(1)


if __name__ == "__main__":
    app()
