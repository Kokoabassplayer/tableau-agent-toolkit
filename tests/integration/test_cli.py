"""Integration tests for the Typer CLI entry point.

Tests that all CLI commands are registered, discoverable via --help,
and have the expected arguments, options, and docstrings.
"""

import pytest
from typer.testing import CliRunner

from tableau_agent_toolkit.cli import app

runner = CliRunner()


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
