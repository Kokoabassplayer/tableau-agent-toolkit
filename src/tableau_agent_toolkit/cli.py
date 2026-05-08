"""Typer CLI entry point for tableau-agent-toolkit.

Provides the main CLI application with commands:
- generate: Generate a Tableau workbook from a spec and template
- validate-xsd: Validate a TWB file against pinned XSD schema
- validate-semantic: Validate TWB cross-references
- spec init: Generate a starter dashboard_spec.yaml
- qa static: Run static QA checks and generate report

The entry point is registered in pyproject.toml as:
    tableau-agent-toolkit = "tableau_agent_toolkit.cli:app"
"""

import sys
from pathlib import Path
from typing import Optional

import typer

from tableau_agent_toolkit.qa.checker import StaticQAChecker
from tableau_agent_toolkit.qa.report import generate_qa_report
from tableau_agent_toolkit.spec.io import load_spec, dump_spec
from tableau_agent_toolkit.spec.models import DashboardSpec, WorkbookSpec, TemplateSpec
from tableau_agent_toolkit.templates.registry import TemplateRegistry
from tableau_agent_toolkit.twb.generator import WorkbookGenerator
from tableau_agent_toolkit.validation.semantic import SemanticValidator
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


@app.command("validate-semantic")
def validate_semantic(
    input_path: Path = typer.Option(
        ...,
        "--input",
        help="Path to .twb file",
        exists=True,
    ),
    spec_path: Optional[Path] = typer.Option(
        None,
        "--spec",
        help="Path to original spec for error mapping",
    ),
) -> None:
    """Validate TWB cross-references (sheet refs, calc names, action targets, field refs)."""
    validator = SemanticValidator()
    result = validator.validate(input_path, spec_path=spec_path)
    if result.valid:
        typer.echo(f"Valid: {input_path} passes semantic validation")
    else:
        typer.echo(f"Invalid: {input_path} failed semantic validation", err=True)
        for err in result.errors:
            msg = f"  ERROR: {err.message}"
            if err.spec_ref:
                msg += f" (spec: {err.spec_ref})"
            typer.echo(msg, err=True)
        for warn in result.warnings:
            msg = f"  WARNING: {warn.message}"
            if warn.spec_ref:
                msg += f" (spec: {warn.spec_ref})"
            typer.echo(msg, err=True)
        sys.exit(1)


qa_app = typer.Typer(help="QA operations")
app.add_typer(qa_app, name="qa")


@qa_app.command("static")
def qa_static(
    input_path: Path = typer.Option(
        ...,
        "--input",
        help="Path to .twb file",
        exists=True,
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output markdown report path",
    ),
) -> None:
    """Run static QA checks and generate report."""
    checker = StaticQAChecker()
    results = checker.check_all(input_path)
    report = generate_qa_report(results, input_path)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8")
        typer.echo(f"QA report written to {output}")
    else:
        typer.echo(report)

    # Exit non-zero if any check failed
    if any(r.status.value == "FAIL" for r in results):
        sys.exit(1)


spec_app = typer.Typer(help="Spec file operations")
app.add_typer(spec_app, name="spec")


@spec_app.command("init")
def spec_init(
    output: Path = typer.Option(
        "dashboard_spec.yaml",
        "--output",
        "-o",
        help="Output spec file path",
    ),
    workbook_name: str = typer.Option(
        "My Dashboard",
        "--name",
        help="Workbook display name",
    ),
    template_id: str = typer.Option(
        "finance-reconciliation",
        "--template",
        help="Template ID from catalog",
    ),
    tableau_version: str = typer.Option(
        "2026.1",
        "--version",
        help="Target Tableau version",
    ),
) -> None:
    """Generate a starter dashboard_spec.yaml from prompts.

    Creates a minimal valid spec file with the specified workbook name,
    template, and Tableau version. Edit the generated file to add
    datasources, calculations, worksheets, and dashboards.
    """
    if output.exists():
        typer.echo(f"Error: {output} already exists. Remove it or use a different path.", err=True)
        raise typer.Exit(code=1)

    spec = DashboardSpec(
        spec_version="1.0",
        workbook=WorkbookSpec(
            name=workbook_name,
            target_tableau_version=tableau_version,
            template=TemplateSpec(
                id=template_id,
                path="",
                required_anchors=[],
            ),
        ),
        datasources=[],
        parameters=[],
        calculations=[],
        worksheets=[],
        dashboards=[],
    )
    dump_spec(spec, output)
    typer.echo(f"Created starter spec: {output}")


if __name__ == "__main__":
    app()
