"""Unit tests for SemanticValidator.

Tests semantic cross-reference checks that XSD validation cannot detect:
- Broken sheet references in dashboard zones
- Broken action target references
- Dangling datasource references on worksheets
- Dangling field references in calculation formulas
"""

from pathlib import Path

import pytest

from tableau_agent_toolkit.validation.report import SemanticIssue, SemanticValidationResult, Severity
from tableau_agent_toolkit.validation.semantic import SemanticValidator

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


@pytest.fixture
def validator() -> SemanticValidator:
    """Create a SemanticValidator instance."""
    return SemanticValidator()


class TestSemanticValidator:
    """Tests for SemanticValidator.validate()."""

    def test_valid_full_twb_returns_valid(self, validator: SemanticValidator) -> None:
        """Test 1: validate() returns valid=True with empty errors for valid_full.twb."""
        result = validator.validate(FIXTURES_DIR / "valid_full.twb")
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []

    def test_catches_broken_sheet_reference(self, validator: SemanticValidator) -> None:
        """Test 2: validate() catches broken zone reference 'NonExistentSheet'."""
        result = validator.validate(FIXTURES_DIR / "broken_references.twb")
        assert result.valid is False
        broken_refs = [
            e for e in result.errors if e.category == "broken_sheet_reference"
        ]
        assert len(broken_refs) >= 1
        assert any("NonExistentSheet" in e.message for e in broken_refs)
        assert all(e.severity == Severity.ERROR for e in broken_refs)

    def test_catches_broken_action_target(self, validator: SemanticValidator) -> None:
        """Test 3: validate() catches broken action target 'MissingSheet'."""
        result = validator.validate(FIXTURES_DIR / "broken_references.twb")
        assert result.valid is False
        action_errors = [
            e for e in result.errors if e.category == "broken_action_target"
        ]
        assert len(action_errors) >= 1
        assert any("MissingSheet" in e.message for e in action_errors)
        assert all(e.severity == Severity.ERROR for e in action_errors)

    def test_catches_dangling_field_reference(self, validator: SemanticValidator) -> None:
        """Test 4: validate() catches dangling field reference [MissingField]."""
        result = validator.validate(FIXTURES_DIR / "missing_calculation.twb")
        field_warnings = [
            w for w in result.warnings if w.category == "dangling_field_reference"
        ]
        assert len(field_warnings) >= 1
        assert any("MissingField" in w.message for w in field_warnings)
        assert all(w.severity == Severity.WARNING for w in field_warnings)

    def test_returns_invalid_when_errors_exist(self, validator: SemanticValidator) -> None:
        """Test 5: validate() returns valid=False when errors list is non-empty."""
        result = validator.validate(FIXTURES_DIR / "broken_references.twb")
        assert result.valid is False
        assert len(result.errors) > 0

    def test_catches_dangling_datasource_ref(self, validator: SemanticValidator) -> None:
        """Test 6: validate() catches worksheet referencing undefined datasource."""
        result = validator.validate(FIXTURES_DIR / "dangling_datasource.twb")
        ds_warnings = [
            w for w in result.warnings if w.category == "dangling_datasource_ref"
        ]
        assert len(ds_warnings) >= 1
        assert any("MissingDS" in w.message for w in ds_warnings)
        assert all(w.severity == Severity.WARNING for w in ds_warnings)

    def test_uses_secure_xml_parser(self, validator: SemanticValidator) -> None:
        """Test 7: validate() uses secure XML parser (resolve_entities=False, no_network=True).

        This is a structural test -- we verify that the parser used has the
        expected security settings by checking the module implementation uses
        etree.XMLParser with the correct kwargs.
        """
        import inspect
        from lxml import etree

        source = inspect.getsource(SemanticValidator.validate)
        assert "resolve_entities=False" in source
        assert "no_network=True" in source

    def test_minimal_template_valid(self, validator: SemanticValidator) -> None:
        """Test 8: validate() returns empty errors+warnings for minimal_template.twb."""
        result = validator.validate(FIXTURES_DIR / "minimal_template.twb")
        assert result.valid is True
        assert result.errors == []
        assert result.warnings == []
