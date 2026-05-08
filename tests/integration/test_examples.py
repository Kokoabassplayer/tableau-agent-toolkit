"""Integration tests for example dashboard specs.

Validates that all example specs in examples/specs/ load successfully
through load_spec, have expected structure, and can generate .twb files.
"""

from pathlib import Path

import pytest

from tableau_agent_toolkit.spec.io import load_spec
from tableau_agent_toolkit.twb.generator import WorkbookGenerator

EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples" / "specs"
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.fixture()
def minimal_template() -> Path:
    """Return path to the minimal template fixture."""
    return FIXTURES_DIR / "minimal_template.twb"


def test_load_finance_spec() -> None:
    """Finance reconciliation spec loads without validation errors."""
    spec = load_spec(EXAMPLES_DIR / "finance-reconciliation.dashboard_spec.yaml")
    assert spec.workbook.name == "Finance Reconciliation Dashboard"


def test_load_executive_kpi_spec() -> None:
    """Executive KPI spec loads without validation errors."""
    spec = load_spec(EXAMPLES_DIR / "executive-kpi.dashboard_spec.yaml")
    assert spec.workbook.name == "Executive KPI Dashboard"


def test_load_ops_monitoring_spec() -> None:
    """Ops monitoring spec loads without validation errors."""
    spec = load_spec(EXAMPLES_DIR / "ops-monitoring.dashboard_spec.yaml")
    assert spec.workbook.name == "Operations Monitoring"


def test_finance_spec_has_finance_datasource() -> None:
    """Finance spec has at least one datasource with finance-related name."""
    spec = load_spec(EXAMPLES_DIR / "finance-reconciliation.dashboard_spec.yaml")
    finance_names = [
        ds.name
        for ds in spec.datasources
        if "finance" in ds.name.lower() or "reconciliation" in ds.name.lower()
    ]
    assert len(finance_names) >= 1, f"Expected finance datasource, got: {[ds.name for ds in spec.datasources]}"


def test_finance_spec_has_worksheets() -> None:
    """Finance spec has at least one worksheet."""
    spec = load_spec(EXAMPLES_DIR / "finance-reconciliation.dashboard_spec.yaml")
    assert len(spec.worksheets) >= 1


def test_finance_spec_has_dashboards() -> None:
    """Finance spec has at least one dashboard."""
    spec = load_spec(EXAMPLES_DIR / "finance-reconciliation.dashboard_spec.yaml")
    assert len(spec.dashboards) >= 1


def test_finance_spec_generates_twb(tmp_path: Path, minimal_template: Path) -> None:
    """Finance reconciliation spec generates a .twb file via WorkbookGenerator."""
    spec = load_spec(EXAMPLES_DIR / "finance-reconciliation.dashboard_spec.yaml")
    output_path = tmp_path / "output.twb"

    generator = WorkbookGenerator.__new__(WorkbookGenerator)
    result = generator.generate(spec, output_path, template_override=minimal_template)

    assert result.output_path == output_path
    assert output_path.exists()
    content = output_path.read_text(encoding="utf-8")
    assert "Finance Reconciliation Dashboard" in content
