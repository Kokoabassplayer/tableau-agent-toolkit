"""Tests for validation report types (SemanticIssue, Severity, SemanticValidationResult)."""

from dataclasses import fields

from lxml import etree

from tableau_agent_toolkit.validation.report import (
    SemanticIssue,
    SemanticValidationResult,
    Severity,
)


class TestSeverity:
    """Tests for the Severity enum."""

    def test_has_error_value(self) -> None:
        assert Severity.ERROR.value == "error"

    def test_has_warning_value(self) -> None:
        assert Severity.WARNING.value == "warning"

    def test_has_info_value(self) -> None:
        assert Severity.INFO.value == "info"

    def test_three_members(self) -> None:
        assert len(Severity) == 3


class TestSemanticIssue:
    """Tests for the SemanticIssue dataclass."""

    def test_has_required_fields(self) -> None:
        field_names = {f.name for f in fields(SemanticIssue)}
        assert "severity" in field_names
        assert "category" in field_names
        assert "message" in field_names
        assert "xml_element" in field_names
        assert "spec_ref" in field_names

    def test_create_with_required_fields(self) -> None:
        issue = SemanticIssue(
            severity=Severity.ERROR,
            category="reference",
            message="Sheet not found",
        )
        assert issue.severity is Severity.ERROR
        assert issue.category == "reference"
        assert issue.message == "Sheet not found"
        assert issue.xml_element is None
        assert issue.spec_ref is None

    def test_create_with_xml_element(self) -> None:
        elem = etree.Element("zone", name="BadSheet")
        issue = SemanticIssue(
            severity=Severity.WARNING,
            category="reference",
            message="Missing sheet",
            xml_element=elem,
            spec_ref="sheet-001",
        )
        assert issue.xml_element is not None
        assert issue.xml_element.get("name") == "BadSheet"
        assert issue.spec_ref == "sheet-001"


class TestSemanticValidationResult:
    """Tests for the SemanticValidationResult dataclass."""

    def test_has_required_fields(self) -> None:
        field_names = {f.name for f in fields(SemanticValidationResult)}
        assert "valid" in field_names
        assert "errors" in field_names
        assert "warnings" in field_names

    def test_valid_when_no_errors(self) -> None:
        result = SemanticValidationResult(valid=True)
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_valid_false_with_errors(self) -> None:
        error = SemanticIssue(
            severity=Severity.ERROR,
            category="reference",
            message="Broken reference",
        )
        result = SemanticValidationResult(valid=False, errors=[error])
        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "Broken reference"

    def test_warnings_stored_separately(self) -> None:
        warning = SemanticIssue(
            severity=Severity.WARNING,
            category="naming",
            message="Non-standard name",
        )
        result = SemanticValidationResult(valid=True, warnings=[warning])
        assert result.errors == []
        assert len(result.warnings) == 1
