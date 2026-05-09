"""Typer CLI entry point for tableau-agent-toolkit.

Provides the main CLI application with commands:
- generate: Generate a Tableau workbook from a spec and template
- validate-xsd: Validate a TWB file against pinned XSD schema
- validate-semantic: Validate TWB cross-references
- package: Package a .twb file into a .twbx archive
- publish: Publish a workbook to Tableau Server/Cloud
- spec init: Generate a starter dashboard_spec.yaml
- qa static: Run static QA checks and generate report

The entry point is registered in pyproject.toml as:
    tableau-agent-toolkit = "tableau_agent_toolkit.cli:app"
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import typer

from tableau_agent_toolkit.packaging.packager import WorkbookPackager
from tableau_agent_toolkit.packaging.verifier import PackageVerifier
from tableau_agent_toolkit.publishing.fallback import RESTFallbackPublisher
from tableau_agent_toolkit.publishing.publisher import TSCPublisher
from tableau_agent_toolkit.security.settings import Settings
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
    schemas_root = Path(
        os.environ.get(
            "TABLEAU_SCHEMAS_ROOT",
            str(Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas" / "schemas"),
        )
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
        if err.spec_file and err.spec_line:
            msg = f"  ERROR: {err.spec_file} line {err.spec_line}: {err.message}"
        else:
            msg = f"  ERROR: {err.message}"
        typer.echo(msg, err=True)
        if err.remediation:
            typer.echo(f"    Remediation: {err.remediation}", err=True)
    for warn in result.warnings:
        if warn.spec_file and warn.spec_line:
            msg = f"  WARNING: {warn.spec_file} line {warn.spec_line}: {warn.message}"
        else:
            msg = f"  WARNING: {warn.message}"
        typer.echo(msg, err=True)
        if warn.remediation:
            typer.echo(f"    Remediation: {warn.remediation}", err=True)
    if not result.valid:
        sys.exit(1)


@app.command("package")
def package(
    input_path: Path = typer.Option(
        ...,
        "--input",
        help="Path to .twb file to package",
        exists=True,
    ),
    output: Path = typer.Option(
        "output.twbx",
        "--output",
        "-o",
        help="Output .twbx path",
    ),
) -> None:
    """Package a .twb file into a .twbx archive.

    Creates a ZIP archive containing the .twb file, matching the
    Tableau Desktop .twbx output structure.
    """
    packager = WorkbookPackager()
    result = packager.package(input_path, output)
    typer.echo(f"Packaged: {result.output_path}")
    if result.warnings:
        for w in result.warnings:
            typer.echo(f"Warning: {w}", err=True)

    # Verify package integrity
    verifier = PackageVerifier()
    verification = verifier.verify(result.output_path)
    if verification.valid:
        typer.echo("Verification: Package integrity confirmed")
    else:
        for error in verification.errors:
            typer.echo(f"Verification error: {error}", err=True)
        raise typer.Exit(code=1)


@app.command("publish")
def publish(
    input_path: Path = typer.Option(
        ...,
        "--input",
        help="Path to .twb or .twbx file to publish",
        exists=True,
    ),
    server: Optional[str] = typer.Option(
        None,
        "--server",
        help="Tableau Server URL (e.g. https://tableau.example.com)",
    ),
    project: Optional[str] = typer.Option(
        None,
        "--project",
        help="Target project name on Tableau Server",
    ),
    site: str = typer.Option(
        "",
        "--site",
        help="Target site contentUrl (empty string for default site)",
    ),
    mode: Optional[str] = typer.Option(
        None,
        "--mode",
        help="Publish mode: CreateNew or Overwrite",
    ),
    spec_path: Optional[Path] = typer.Option(
        None,
        "--spec",
        help="Path to spec for publish defaults",
    ),
) -> None:
    """Publish a workbook to Tableau Server or Cloud.

    Accepts both .twb and .twbx files. If a .twb file is provided,
    it is automatically packaged into a .twbx before publishing.
    Uses PAT authentication via TABLEAU_PAT_NAME and TABLEAU_PAT_SECRET
    environment variables.

    When --spec is provided, reads project/site/mode defaults from the
    spec's publish section. CLI args always override spec values.
    """
    # Resolve spec-driven defaults
    effective_mode = mode
    if spec_path:
        dashboard_spec = load_spec(spec_path)
        if dashboard_spec.publish:
            pub = dashboard_spec.publish
            project = project or pub.project
            site = site or pub.site_id
            effective_mode = effective_mode or pub.mode.value

    # Apply defaults for values not set by spec or CLI
    effective_mode = effective_mode or "CreateNew"

    # Validate required args
    if not project:
        typer.echo(
            "Error: --project is required (or provide --spec with publish.project)",
            err=True,
        )
        raise typer.Exit(code=1)

    # Validate mode
    if effective_mode not in ("CreateNew", "Overwrite"):
        typer.echo(
            f"Error: Invalid mode '{effective_mode}'. Must be CreateNew or Overwrite.",
            err=True,
        )
        raise typer.Exit(code=1)

    publish_path = input_path

    # Auto-package .twb to .twbx
    if input_path.suffix.lower() == ".twb":
        typer.echo(f"Auto-packaging {input_path.name} to .twbx...")
        packager = WorkbookPackager()
        tmp_dir = tempfile.mkdtemp()
        twbx_path = Path(tmp_dir) / f"{input_path.stem}.twbx"
        package_result = packager.package(input_path, twbx_path)
        publish_path = package_result.output_path
        typer.echo(f"Packaged to: {publish_path}")

    # Load credentials from env
    settings = Settings()
    if not settings.pat_name or not settings.pat_secret.get_secret_value():
        typer.echo(
            "Error: TABLEAU_PAT_NAME and TABLEAU_PAT_SECRET environment variables must be set.",
            err=True,
        )
        raise typer.Exit(code=1)

    # Resolve server URL: CLI arg > env var
    effective_server = server or settings.server_url
    if not effective_server:
        typer.echo(
            "Error: --server or TABLEAU_SERVER_URL env var required",
            err=True,
        )
        raise typer.Exit(code=1)

    # Publish with TSC, fall back to REST API
    receipt = None
    publisher = TSCPublisher(settings=settings)
    try:
        receipt = publisher.publish(
            file_path=publish_path,
            project_name=project,
            mode=effective_mode,
            server_url=effective_server,
            site_id=site,
        )
    except Exception as e:
        typer.echo(f"TSC publish failed: {e}", err=True)
        typer.echo("Attempting REST API fallback...", err=True)
        try:
            fallback = RESTFallbackPublisher(settings=settings)
            receipt = fallback.publish(
                file_path=publish_path,
                project_name=project,
                mode=effective_mode,
                server_url=effective_server,
                site_id=site,
            )
            typer.echo("Published via REST API fallback")
        except Exception as fallback_e:
            typer.echo(f"REST API fallback also failed: {fallback_e}", err=True)
            raise typer.Exit(code=1)

    if receipt is None:
        typer.echo("Error: No publish receipt returned", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Published: {receipt.workbook_name} (ID: {receipt.workbook_id})")
    typer.echo(f"  Mode: {receipt.mode}")
    typer.echo(f"  Project: {receipt.project_name} (ID: {receipt.project_id})")
    typer.echo(f"  Site: {receipt.site_id or '(default)'}")
    typer.echo(f"  Server: {receipt.server_url}")
    typer.echo(f"  File: {receipt.file_path} ({receipt.file_size_bytes} bytes)")
    if receipt.verification_details:
        for detail in receipt.verification_details:
            typer.echo(f"  Verification: {detail}")


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
