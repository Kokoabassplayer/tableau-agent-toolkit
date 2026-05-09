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


class TestValidateXsdExecution:
    """Test validate-xsd CLI command execution (actual validation, not just --help)."""

    def test_validate_xsd_valid_twb_exits_zero(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """validate-xsd on valid_full.twb should exit 0 and print Valid."""
        monkeypatch.setenv("TABLEAU_SCHEMAS_ROOT", str(FIXTURES_DIR / "schemas"))
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["validate-xsd", str(valid_twb)])
        assert result.exit_code == 0, f"validate-xsd failed: {result.output}"
        assert "Valid" in result.output or "passes" in result.output

    def test_validate_xsd_invalid_twb_exits_nonzero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """validate-xsd on malformed XML should exit non-zero with error details."""
        monkeypatch.setenv("TABLEAU_SCHEMAS_ROOT", str(FIXTURES_DIR / "schemas"))
        invalid_twb = tmp_path / "invalid.twb"
        invalid_twb.write_text(
            '<?xml version="1.0"?>\n<invalid_root />', encoding="utf-8"
        )
        result = runner.invoke(app, ["validate-xsd", str(invalid_twb)])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "Line" in result.output

    def test_validate_xsd_with_version_option(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """validate-xsd --version 2026.1 should work the same as default."""
        monkeypatch.setenv("TABLEAU_SCHEMAS_ROOT", str(FIXTURES_DIR / "schemas"))
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(
            app, ["validate-xsd", str(valid_twb), "--version", "2026.1"]
        )
        assert result.exit_code == 0, f"validate-xsd --version failed: {result.output}"
        assert "Valid" in result.output or "passes" in result.output


class TestValidateSemanticCommand:
    """Test the validate-semantic command --help and execution."""

    def test_validate_semantic_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["validate-semantic", "--help"])
        assert result.exit_code == 0

    def test_validate_semantic_help_shows_input_option(self) -> None:
        result = runner.invoke(app, ["validate-semantic", "--help"])
        assert "--input" in result.output

    def test_validate_semantic_nonexistent_file_exits_nonzero(self) -> None:
        """validate-semantic on a nonexistent file should exit non-zero."""
        result = runner.invoke(app, ["validate-semantic", "--input", "nonexistent.twb"])
        assert result.exit_code != 0

    def test_validate_semantic_valid_twb_exits_zero(self) -> None:
        """validate-semantic on a valid TWB should exit 0 and print Valid/passes."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["validate-semantic", "--input", str(valid_twb)])
        assert result.exit_code == 0
        assert "Valid" in result.output or "passes" in result.output.lower()

    def test_validate_semantic_broken_twb_exits_nonzero(self) -> None:
        """validate-semantic on broken_references.twb should exit 1 with error text."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        result = runner.invoke(app, ["validate-semantic", "--input", str(broken_twb)])
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
        result = runner.invoke(app, ["qa", "static", "--input", str(valid_twb)])
        assert "# QA Report" in result.output

    def test_qa_static_output_writes_file(self, tmp_path: Path) -> None:
        """qa static --output report.md should write markdown to the specified path."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        report_path = tmp_path / "report.md"
        result = runner.invoke(
            app, ["qa", "static", "--input", str(valid_twb), "--output", str(report_path)]
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

    def test_help_shows_package_command(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "package" in result.output

    def test_help_shows_publish_command(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert "publish" in result.output


class TestPackageCommand:
    """Test the package command --help and execution."""

    def test_package_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["package", "--help"])
        assert result.exit_code == 0

    def test_package_help_shows_input_option(self) -> None:
        result = runner.invoke(app, ["package", "--help"])
        assert "--input" in result.output

    def test_package_help_shows_output_option(self) -> None:
        result = runner.invoke(app, ["package", "--help"])
        assert "--output" in result.output

    def test_package_valid_twb_creates_twbx(self, tmp_path: Path) -> None:
        """Package command on a valid .twb creates a .twbx and prints 'Packaged:'."""
        twb_file = tmp_path / "test.twb"
        twb_file.write_text('<workbook name="test"></workbook>', encoding="utf-8")
        output = tmp_path / "output.twbx"
        result = runner.invoke(app, ["package", "--input", str(twb_file), "--output", str(output)])
        assert result.exit_code == 0
        assert "Packaged:" in result.output
        assert output.exists()

    def test_package_nonexistent_input_exits_nonzero(self) -> None:
        result = runner.invoke(app, ["package", "--input", "nonexistent.twb"])
        assert result.exit_code != 0


class TestValidateSemanticWithSpec:
    """Test validate-semantic --spec integration with line numbers and remediation."""

    def test_broken_references_with_spec_shows_line_numbers(self) -> None:
        """validate-semantic --spec on broken_references.twb shows 'line N' in output."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        broken_spec = FIXTURES_DIR / "broken_references_spec.yaml"
        result = runner.invoke(app, [
            "validate-semantic",
            "--input", str(broken_twb),
            "--spec", str(broken_spec),
        ])
        assert result.exit_code == 1
        assert "line" in result.output
        # Verify the line number format: "filename line N:"
        import re
        assert re.search(r"line \d+:", result.output)

    def test_broken_references_with_spec_shows_remediation(self) -> None:
        """validate-semantic --spec output includes Remediation: lines."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        broken_spec = FIXTURES_DIR / "broken_references_spec.yaml"
        result = runner.invoke(app, [
            "validate-semantic",
            "--input", str(broken_twb),
            "--spec", str(broken_spec),
        ])
        assert result.exit_code == 1
        assert "Remediation:" in result.output

    def test_broken_references_with_spec_shows_nonexistent_sheet(self) -> None:
        """validate-semantic --spec output names the broken reference."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        broken_spec = FIXTURES_DIR / "broken_references_spec.yaml"
        result = runner.invoke(app, [
            "validate-semantic",
            "--input", str(broken_twb),
            "--spec", str(broken_spec),
        ])
        assert result.exit_code == 1
        assert "NonExistentSheet" in result.output

    def test_broken_references_without_spec_no_line_numbers(self) -> None:
        """validate-semantic without --spec does NOT show 'line N:' format."""
        broken_twb = FIXTURES_DIR / "broken_references.twb"
        result = runner.invoke(app, [
            "validate-semantic",
            "--input", str(broken_twb),
        ])
        assert result.exit_code == 1
        assert "ERROR:" in result.output
        # Should NOT contain "line <number>:" format when no --spec
        import re
        assert not re.search(r"\.yaml line \d+:", result.output)

    def test_dangling_datasource_with_spec_shows_remediation(self) -> None:
        """validate-semantic --spec on dangling_datasource shows remediation for warnings."""
        ds_twb = FIXTURES_DIR / "dangling_datasource.twb"
        ds_spec = FIXTURES_DIR / "dangling_datasource_spec.yaml"
        result = runner.invoke(app, [
            "validate-semantic",
            "--input", str(ds_twb),
            "--spec", str(ds_spec),
        ])
        # dangling datasource is a WARNING, not an ERROR, so exit code may be 0
        # But output should contain the warning with remediation
        assert "Remediation:" in result.output or "MissingDS" in result.output


class TestPublishCommand:
    """Test the publish command --help and option validation."""

    def test_publish_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["publish", "--help"])
        assert result.exit_code == 0

    def test_publish_help_shows_input_option(self) -> None:
        result = runner.invoke(app, ["publish", "--help"])
        assert "--input" in result.output

    def test_publish_help_shows_server_option(self) -> None:
        result = runner.invoke(app, ["publish", "--help"])
        assert "--server" in result.output

    def test_publish_help_shows_project_option(self) -> None:
        result = runner.invoke(app, ["publish", "--help"])
        assert "--project" in result.output

    def test_publish_help_shows_mode_option(self) -> None:
        result = runner.invoke(app, ["publish", "--help"])
        assert "--mode" in result.output

    def test_publish_missing_server_exits_nonzero(self, tmp_path: Path) -> None:
        """publish without --server should fail."""
        twb = tmp_path / "test.twb"
        twb.write_text("<workbook/>", encoding="utf-8")
        result = runner.invoke(app, ["publish", "--input", str(twb), "--project", "Test"])
        assert result.exit_code != 0

    def test_publish_missing_project_exits_nonzero(self, tmp_path: Path) -> None:
        """publish without --project should fail."""
        twb = tmp_path / "test.twb"
        twb.write_text("<workbook/>", encoding="utf-8")
        result = runner.invoke(app, ["publish", "--input", str(twb), "--server", "https://example.com"])
        assert result.exit_code != 0

    def test_publish_invalid_mode_exits_nonzero(self, tmp_path: Path) -> None:
        """publish with invalid --mode should fail with error message."""
        twb = tmp_path / "test.twb"
        twb.write_text("<workbook/>", encoding="utf-8")
        result = runner.invoke(app, [
            "publish", "--input", str(twb),
            "--server", "https://example.com",
            "--project", "Test",
            "--mode", "InvalidMode",
        ])
        assert result.exit_code != 0
        assert "Invalid mode" in result.output
