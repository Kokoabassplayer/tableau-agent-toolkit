"""Tests for the TWB generator module.

Covers WorkbookGenerator.generate(), all patch operations, and integration
with apply_manifest_by_version and TemplateRegistry.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from lxml import etree

from tableau_agent_toolkit.spec.models import (
    CalculationSpec,
    DashboardSpec,
    DatasourceSpec,
    PackagingEnum,
    TemplateSpec,
    WorkbookSpec,
    WorksheetSpec,
)

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
MINIMAL_TEMPLATE = FIXTURES_DIR / "minimal_template.twb"


def _make_spec(
    name: str = "TestWorkbook",
    template_path: Path | None = None,
    datasources: list | None = None,
    calculations: list | None = None,
    worksheets: list | None = None,
    dashboards: list | None = None,
) -> DashboardSpec:
    """Helper to create a DashboardSpec for testing."""
    if template_path is None:
        template_path = MINIMAL_TEMPLATE
    return DashboardSpec(
        spec_version="1.0",
        workbook=WorkbookSpec(
            name=name,
            target_tableau_version="2026.1",
            packaging=PackagingEnum.twb,
            template=TemplateSpec(
                id="test-template",
                path=template_path,
                required_anchors=[],
            ),
        ),
        datasources=datasources or [],
        calculations=calculations or [],
        worksheets=worksheets or [],
        dashboards=dashboards or [],
    )


def _make_registry(template_path: Path | None = None) -> MagicMock:
    """Helper to create a mock TemplateRegistry that resolves to the minimal template."""
    if template_path is None:
        template_path = MINIMAL_TEMPLATE
    registry = MagicMock()
    registry.resolve.return_value = MagicMock(
        id="test-template",
        path=template_path,
    )
    return registry


class TestGenerateOutput:
    """Tests for generate() producing output files."""

    def test_generate_produces_twb_file(self, tmp_path: Path) -> None:
        """Test 1: generate() produces a .twb file at the specified output path."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        spec = _make_spec()
        registry = _make_registry()
        output_path = tmp_path / "output.twb"

        generator = WorkbookGenerator(template_registry=registry)
        result = generator.generate(spec, output_path)

        assert result.output_path == output_path
        assert output_path.exists()

    def test_generated_twb_has_workbook_name(self, tmp_path: Path) -> None:
        """Test 2: Generated .twb has the workbook name from the spec set in the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        spec = _make_spec(name="MyDashboard")
        registry = _make_registry()
        output_path = tmp_path / "output.twb"

        generator = WorkbookGenerator(template_registry=registry)
        generator.generate(spec, output_path)

        tree = etree.parse(str(output_path))
        root = tree.getroot()
        assert root.attrib.get("name") == "MyDashboard"


class TestPatchOperations:
    """Tests for individual XML patch operations."""

    def test_patch_workbook_name_sets_name_attribute(self) -> None:
        """Test 4: _patch_workbook_name changes the workbook name attribute in the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        registry = _make_registry()
        generator = WorkbookGenerator(template_registry=registry)
        tree = etree.parse(str(MINIMAL_TEMPLATE))

        generator._patch_workbook_name(tree, "NewName")

        assert tree.getroot().attrib.get("name") == "NewName"

    def test_patch_datasources_adds_elements(self, tmp_path: Path) -> None:
        """Test 5: _patch_datasources adds datasource elements to the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        datasources = [
            DatasourceSpec(name="SalesData", mode="embedded-extract"),
            DatasourceSpec(
                name="CustomDS",
                mode="custom-sql",
                custom_sql_file="query.sql",
            ),
        ]
        spec = _make_spec(datasources=datasources)
        registry = _make_registry()
        generator = WorkbookGenerator(template_registry=registry)
        tree = etree.parse(str(MINIMAL_TEMPLATE))

        generator._patch_datasources(tree, spec)

        ds_elements = tree.getroot().xpath(".//datasources/datasource")
        # The minimal template already has one datasource (Parameters),
        # plus the two we added
        ds_names = [ds.attrib.get("name") for ds in ds_elements]
        assert "SalesData" in ds_names
        assert "CustomDS" in ds_names

    def test_patch_calculations_adds_elements(self) -> None:
        """Test 6: _patch_calculations adds calculation elements to the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        calculations = [
            CalculationSpec(name="Revenue", formula="[Sales] * [Price]"),
            CalculationSpec(name="Growth", formula="[Revenue] - PREVIOUS_VALUE(0)"),
        ]
        spec = _make_spec(calculations=calculations)
        registry = _make_registry()
        generator = WorkbookGenerator(template_registry=registry)
        tree = etree.parse(str(MINIMAL_TEMPLATE))

        generator._patch_calculations(tree, spec)

        # Calculations are added as <column> with <calculation> child in datasources
        calc_elements = tree.getroot().xpath(".//datasources/datasource/column/calculation")
        assert len(calc_elements) >= 2
        formulas = [el.attrib.get("formula") for el in calc_elements]
        assert "[Sales] * [Price]" in formulas
        assert "[Revenue] - PREVIOUS_VALUE(0)" in formulas

    def test_patch_worksheets_adds_elements(self) -> None:
        """Test 7: _patch_worksheets adds worksheet elements to the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        worksheets = [
            WorksheetSpec(name="SalesChart", datasource="SalesData"),
            WorksheetSpec(name="RevenueTable", datasource="SalesData"),
        ]
        spec = _make_spec(worksheets=worksheets)
        registry = _make_registry()
        generator = WorkbookGenerator(template_registry=registry)
        tree = etree.parse(str(MINIMAL_TEMPLATE))

        generator._patch_worksheets(tree, spec)

        ws_elements = tree.getroot().xpath(".//worksheets/worksheet")
        assert len(ws_elements) == 2
        ws_names = [ws.attrib.get("name") for ws in ws_elements]
        assert "SalesChart" in ws_names
        assert "RevenueTable" in ws_names

    def test_patch_dashboards_adds_elements(self) -> None:
        """Test 8: _patch_dashboards adds dashboard elements to the XML."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        dashboards = [
            {"name": "Executive Overview"},
            {"name": "Sales Detail"},
        ]
        spec = _make_spec(dashboards=dashboards)
        registry = _make_registry()
        generator = WorkbookGenerator(template_registry=registry)
        tree = etree.parse(str(MINIMAL_TEMPLATE))

        generator._patch_dashboards(tree, spec)

        db_elements = tree.getroot().xpath(".//dashboards/dashboard")
        assert len(db_elements) == 2
        db_names = [db.attrib.get("name") for db in db_elements]
        assert "Executive Overview" in db_names
        assert "Sales Detail" in db_names


class TestManifestIntegration:
    """Tests for manifest version application during generation."""

    @patch("tableau_agent_toolkit.twb.generator.apply_manifest_by_version")
    def test_apply_manifest_called_during_generation(
        self, mock_manifest: MagicMock, tmp_path: Path
    ) -> None:
        """Test 9: apply_manifest_by_version is called during generation."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        spec = _make_spec()
        registry = _make_registry()
        output_path = tmp_path / "output.twb"

        generator = WorkbookGenerator(template_registry=registry)
        generator.generate(spec, output_path)

        mock_manifest.assert_called_once()
        call_args = mock_manifest.call_args
        assert call_args[0][1] == "2026.1"


class TestDirectoryCreation:
    """Tests for output path directory creation."""

    def test_generate_creates_parent_directories(self, tmp_path: Path) -> None:
        """Test 10: generate() creates parent directories for output path if they do not exist."""
        from tableau_agent_toolkit.twb.generator import WorkbookGenerator

        spec = _make_spec()
        registry = _make_registry()
        output_path = tmp_path / "nested" / "dir" / "output.twb"

        generator = WorkbookGenerator(template_registry=registry)
        result = generator.generate(spec, output_path)

        assert output_path.exists()
        assert result.output_path == output_path
