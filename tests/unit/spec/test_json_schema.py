"""Tests for JSON Schema generation from Pydantic models."""

from tableau_agent_toolkit.spec.models import DashboardSpec


def test_json_schema_returns_dict():
    schema = DashboardSpec.json_schema()
    assert isinstance(schema, dict)


def test_json_schema_has_workbook_property():
    schema = DashboardSpec.json_schema()
    assert "workbook" in schema.get("properties", {})


def test_json_schema_has_required_workbook():
    schema = DashboardSpec.json_schema()
    assert "workbook" in schema.get("required", [])


def test_json_schema_has_datasources_property():
    schema = DashboardSpec.json_schema()
    assert "datasources" in schema.get("properties", {})


def test_json_schema_has_worksheets_property():
    schema = DashboardSpec.json_schema()
    assert "worksheets" in schema.get("properties", {})
