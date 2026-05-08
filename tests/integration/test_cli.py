"""Integration tests for the Typer CLI entry point.

Tests that all CLI commands are registered, discoverable via --help,
and have the expected arguments, options, and docstrings.
"""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from tableau_agent_toolkit.cli import app

runner = CliRunner()
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


class TestTopLevelHelp:
    """Test the top-level --help output."""

    def test_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0

    def test_help_shows_generate(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "Generate" in result.output or "generate" in result.output

    def test_help_shows_validate_xsd(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "validate-xsd" in result.output

    def test_no_args_shows_help(self) -> None:
        """Running with no arguments should show help (exit 0)."""
        result = runner.invoke(app, [])
        assert result.exit_code == 0


class TestGenerateCommand:
    """Test the generate command --help and argument discovery."""

    def test_generate_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert result.exit_code == 0

    def test_generate_help_shows_spec_argument(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert "spec" in result.output.lower()

    def test_generate_help_shows_output_option(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert "--output" in result.output

    def test_generate_help_shows_template_option(self) -> None:
        result = runner.invoke(app, ["generate", "--help"])
        assert "--template" in result.output

    def test_generate_has_docstring(self) -> None:
        """The generate command should have a docstring visible in help."""
        result = runner.invoke(app, ["generate", "--help"])
        assert "Generate" in result.output or "generate" in result.output.lower()

    def test_generate_nonexistent_spec_exits_nonzero(self) -> None:
        """Passing a nonexistent spec file should exit non-zero."""
        result = runner.invoke(app, ["generate", "nonexist.yaml"])
        assert result.exit_code != 0


class TestValidateXsdCommand:
    """Test the validate-xsd command --help and option discovery."""

    def test_validate_xsd_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["validate-xsd", "--help"])
        assert result.exit_code == 0

    def test_validate_xsd_help_shows_xsd(self) -> None:
        result = runner.invoke(app, ["validate-xsd", "--help"])
        assert "xsd" in result.output.lower() or "XSD" in result.output

    def test_validate_xsd_help_shows_version_option(self) -> None:
        result = runner.invoke(app, ["validate-xsd", "--help"])
        assert "--version" in result.output

    def test_validate_xsd_has_docstring(self) -> None:
        """The validate-xsd command should have a docstring visible in help."""
        result = runner.invoke(app, ["validate-xsd", "--help"])
        assert "Validate" in result.output or "validate" in result.output.lower()


class TestValidateSemanticCommand:
    """Test the validate-semantic command --help and execution."""

    def test_validate_semantic_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["validate-semantic", "--help"])
        assert result.exit_code == 0

    def test_validate_semantic_help_shows_input_argument(self) -> None:
        result = runner.invoke(app, ["validate-semantic", "--help"])
        assert "input" in result.output.lower() or "TWB" in result.output or "twb" in result.output.lower()

    def test_validate_semantic_nonexistent_file_exits_nonzero(self) -> None:
        """validate-semantic on a nonexistent file should exit non-zero."""
        result = runner.invoke(app, ["validate-semantic", "nonexistent.twb"])
        assert result.exit_code != 0

    def test_validate_semantic_valid_twb_exits_zero(self) -> None:
        """validate-semantic on a valid TWB should exit 0 and print Valid/passes."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["validate-semantic", str(valid_twb)])
        assert result.exit_code == 0
        assert "Valid" in result.output or "passes" in result.output.lower()

    def test_validate_semantic_broken_twb_exits_nonzero(self) -> None:
        """validate-semantic on broken_references.twb should exit 1 with error text."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        result = runner.invoke(app, ["validate-semantic", str(broken_twb)])
        assert result.exit_code == 1
        assert "Invalid" in result.output or "ERROR" in result.output


class TestQaStaticCommand:
    """Test the qa static command --help and execution."""

    def test_qa_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["qa", "--help"])
        assert result.exit_code == 0

    def test_qa_help_shows_static_subcommand(self) -> None:
        result = runner.invoke(app, ["qa", "--help"])
        assert "static" in result.output.lower()

    def test_qa_static_help_shows_output_option(self) -> None:
        result = runner.invoke(app, ["qa", "static", "--help"])
        assert "--output" in result.output

    def test_qa_static_valid_twb_prints_markdown(self) -> None:
        """qa static on valid_full.twb should print markdown with QA Report heading."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["qa", "static", str(valid_twb)])
        assert "# QA Report" in result.output

    def test_qa_static_output_writes_file(self, tmp_path: Path) -> None:
        """qa static --output report.md should write markdown to the specified path."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        report_path = tmp_path / "report.md"
        result = runner.invoke(
            app, ["qa", "static", str(valid_twb), "--output", str(report_path)]
        )
        # File should be written even if some QA checks fail (exit may be non-zero)
        assert report_path.exists()
        content = report_path.read_text(encoding="utf-8")
        assert "# QA Report" in content


class TestHelpDiscovery:
    """Test that new commands appear in top-level --help output."""

    def test_help_shows_validate_semantic(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "validate-semantic" in result.output

    def test_help_shows_qa_subcommand(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "qa" in result.output.lower()
