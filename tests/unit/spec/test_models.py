"""Tests for Pydantic v2 spec models."""

import pytest
from pydantic import ValidationError

from tableau_agent_toolkit.spec.models import (
    CalculationSpec,
    DashboardSpec,
    DatasourceSpec,
    PackagingEnum,
    ParameterSpec,
    TemplateSpec,
    WorkbookSpec,
    WorksheetSpec,
)


# ---------------------------------------------------------------------------
# Test 1: Minimal valid spec with only workbook section
# ---------------------------------------------------------------------------
def test_minimal_valid_spec():
    spec = DashboardSpec(
        workbook={
            "name": "Test",
            "template": {"id": "t1", "path": "templates/test.twb"},
        }
    )
    assert spec.workbook.name == "Test"
    assert spec.workbook.template.id == "t1"


# ---------------------------------------------------------------------------
# Test 2: Missing workbook field raises ValidationError
# ---------------------------------------------------------------------------
def test_missing_workbook_raises():
    with pytest.raises(ValidationError, match="workbook"):
        DashboardSpec(spec_version="1.0")


# ---------------------------------------------------------------------------
# Test 3: Empty workbook.name raises ValidationError
# ---------------------------------------------------------------------------
def test_empty_workbook_name_raises():
    with pytest.raises(ValidationError, match="name"):
        DashboardSpec(
            workbook={
                "name": "",
                "template": {"id": "t1", "path": "templates/test.twb"},
            }
        )


# ---------------------------------------------------------------------------
# Test 4: Full spec with all sections populated
# ---------------------------------------------------------------------------
def test_full_spec():
    spec = DashboardSpec(
        workbook={
            "name": "Full Workbook",
            "target_tableau_version": "2026.1",
            "packaging": "twbx",
            "template": {"id": "finance-recon", "path": "templates/finance/recon.twb"},
        },
        datasources=[
            {"name": "ds1", "mode": "published", "connection": {"server": "localhost"}},
        ],
        parameters=[
            {"name": "p1", "data_type": "string", "default_value": "hello"},
        ],
        calculations=[
            {"name": "calc1", "formula": "[Sales] * 2", "comment": "Double sales"},
        ],
        worksheets=[
            {"name": "Sheet1", "datasource": "ds1"},
        ],
        dashboards=[{"name": "Dashboard1"}],
        publish={"server": "https://tableau.example.com", "project": "Finance"},
        qa={"static_checks": True},
    )
    assert spec.workbook.packaging == PackagingEnum.twbx
    assert len(spec.datasources) == 1
    assert spec.datasources[0].name == "ds1"
    assert len(spec.parameters) == 1
    assert spec.parameters[0].data_type == "string"
    assert len(spec.calculations) == 1
    assert spec.calculations[0].formula == "[Sales] * 2"
    assert len(spec.worksheets) == 1
    assert spec.worksheets[0].name == "Sheet1"
    assert len(spec.dashboards) == 1
    assert spec.publish is not None
    assert spec.qa is not None


# ---------------------------------------------------------------------------
# Test 5: Default target_tableau_version is "2026.1"
# ---------------------------------------------------------------------------
def test_default_target_tableau_version():
    spec = WorkbookSpec(
        name="Test",
        template={"id": "t1", "path": "templates/test.twb"},
    )
    assert spec.target_tableau_version == "2026.1"


# ---------------------------------------------------------------------------
# Test 6: Default packaging is "twb"
# ---------------------------------------------------------------------------
def test_default_packaging():
    spec = WorkbookSpec(
        name="Test",
        template={"id": "t1", "path": "templates/test.twb"},
    )
    assert spec.packaging == PackagingEnum.twb


# ---------------------------------------------------------------------------
# Test 7: DatasourceSpec rejects empty name
# ---------------------------------------------------------------------------
def test_datasource_empty_name_raises():
    with pytest.raises(ValidationError, match="name"):
        DatasourceSpec(name="", mode="published")


# ---------------------------------------------------------------------------
# Test 8: PackagingEnum only accepts twb or twbx
# ---------------------------------------------------------------------------
def test_packaging_enum_invalid():
    with pytest.raises(ValidationError):
        WorkbookSpec(
            name="Test",
            packaging="invalid",
            template={"id": "t1", "path": "templates/test.twb"},
        )


# ---------------------------------------------------------------------------
# Test 9: Extra fields are rejected (extra="forbid")
# ---------------------------------------------------------------------------
def test_extra_fields_rejected():
    with pytest.raises(ValidationError, match="extra"):
        DashboardSpec(
            workbook={
                "name": "Test",
                "template": {"id": "t1", "path": "templates/test.twb"},
            },
            unknown_field="oops",
        )


# ---------------------------------------------------------------------------
# Test 10: Default spec_version is "1.0"
# ---------------------------------------------------------------------------
def test_default_spec_version():
    spec = DashboardSpec(
        workbook={
            "name": "Test",
            "template": {"id": "t1", "path": "templates/test.twb"},
        }
    )
    assert spec.spec_version == "1.0"
