"""Integration tests for the spec init CLI command."""

from pathlib import Path

from typer.testing import CliRunner

from tableau_agent_toolkit.cli import app
from tableau_agent_toolkit.spec.io import load_spec

runner = CliRunner()


def test_spec_init_creates_valid_yaml(tmp_path: Path) -> None:
    output = tmp_path / "test_spec.yaml"
    result = runner.invoke(app, ["spec", "init", "--output", str(output)])
    assert result.exit_code == 0
    assert output.exists()


def test_spec_init_yaml_round_trips(tmp_path: Path) -> None:
    output = tmp_path / "test_spec.yaml"
    runner.invoke(app, ["spec", "init", "--output", str(output)])
    spec = load_spec(output)
    assert spec.workbook.name == "My Dashboard"


def test_spec_init_default_version(tmp_path: Path) -> None:
    output = tmp_path / "test_spec.yaml"
    runner.invoke(app, ["spec", "init", "--output", str(output)])
    spec = load_spec(output)
    assert spec.workbook.target_tableau_version == "2026.1"


def test_spec_init_empty_sections(tmp_path: Path) -> None:
    output = tmp_path / "test_spec.yaml"
    runner.invoke(app, ["spec", "init", "--output", str(output)])
    spec = load_spec(output)
    assert spec.datasources == []
    assert spec.parameters == []
    assert spec.calculations == []
    assert spec.worksheets == []
    assert spec.dashboards == []


def test_spec_init_rejects_existing_file(tmp_path: Path) -> None:
    output = tmp_path / "test_spec.yaml"
    output.write_text("existing content")
    result = runner.invoke(app, ["spec", "init", "--output", str(output)])
    assert result.exit_code == 1
    assert "already exists" in result.output
