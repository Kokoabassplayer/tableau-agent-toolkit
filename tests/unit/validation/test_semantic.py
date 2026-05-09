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


class TestSpecLineMapping:
    """Tests for spec line number mapping and remediation in SemanticValidator."""

    def test_build_spec_index_returns_empty_for_empty_file(
        self, validator: SemanticValidator, tmp_path: Path
    ) -> None:
        """_build_spec_index returns empty dict for empty YAML file."""
        empty_yaml = tmp_path / "empty.yaml"
        empty_yaml.write_text("", encoding="utf-8")
        result = validator._build_spec_index(empty_yaml)
        assert result == {}

    def test_build_spec_index_returns_empty_for_missing_file(
        self, validator: SemanticValidator
    ) -> None:
        """_build_spec_index returns empty dict for nonexistent file path."""
        result = validator._build_spec_index(Path("/nonexistent/path/spec.yaml"))
        assert result == {}

    def test_build_spec_index_maps_worksheets_with_lines(
        self, validator: SemanticValidator
    ) -> None:
        """_build_spec_index maps worksheet names to (spec_path_fragment, line_number)."""
        spec_path = FIXTURES_DIR / "broken_references_spec.yaml"
        result = validator._build_spec_index(spec_path)
        key = "worksheets:Sheet1"
        assert key in result
        spec_ref, line = result[key]
        assert spec_ref == "worksheets[0]"
        assert isinstance(line, int)
        assert line >= 1

    def test_build_spec_index_maps_zones_from_sheets_not_zones(
        self, validator: SemanticValidator
    ) -> None:
        """_build_spec_index indexes dashboards[].sheets[] not zones[]."""
        spec_path = FIXTURES_DIR / "broken_references_spec.yaml"
        result = validator._build_spec_index(spec_path)
        # NonExistentSheet is in dashboards[0].sheets[1], not zones[]
        assert "zone:NonExistentSheet" in result
        spec_ref, line = result["zone:NonExistentSheet"]
        assert "sheets[1]" in spec_ref

    def test_build_spec_index_line_numbers_are_1_based(
        self, validator: SemanticValidator
    ) -> None:
        """All line numbers returned by _build_spec_index are >= 1."""
        spec_path = FIXTURES_DIR / "broken_references_spec.yaml"
        result = validator._build_spec_index(spec_path)
        for key, (spec_ref, line) in result.items():
            assert isinstance(line, int), f"Line for {key} is not int: {line}"
            assert line >= 1, f"Line for {key} is not 1-based: {line}"

    def test_validate_with_spec_populates_spec_line(
        self, validator: SemanticValidator
    ) -> None:
        """validate() with --spec populates spec_line on broken_sheet_reference errors."""
        result = validator.validate(
            FIXTURES_DIR / "broken_references.twb",
            spec_path=FIXTURES_DIR / "broken_references_spec.yaml",
        )
        broken_refs = [
            e for e in result.errors if e.category == "broken_sheet_reference"
        ]
        assert len(broken_refs) >= 1
        err = broken_refs[0]
        assert err.spec_line is not None
        assert isinstance(err.spec_line, int)
        assert err.spec_line >= 1

    def test_validate_with_spec_populates_spec_file(
        self, validator: SemanticValidator
    ) -> None:
        """validate() with --spec populates spec_file on errors."""
        result = validator.validate(
            FIXTURES_DIR / "broken_references.twb",
            spec_path=FIXTURES_DIR / "broken_references_spec.yaml",
        )
        broken_refs = [
            e for e in result.errors if e.category == "broken_sheet_reference"
        ]
        assert len(broken_refs) >= 1
        assert broken_refs[0].spec_file == "broken_references_spec.yaml"

    def test_validate_with_spec_populates_remediation(
        self, validator: SemanticValidator
    ) -> None:
        """validate() with --spec populates remediation from REMEDIATION_MAP."""
        result = validator.validate(
            FIXTURES_DIR / "broken_references.twb",
            spec_path=FIXTURES_DIR / "broken_references_spec.yaml",
        )
        broken_refs = [
            e for e in result.errors if e.category == "broken_sheet_reference"
        ]
        assert len(broken_refs) >= 1
        assert broken_refs[0].remediation is not None
        assert len(broken_refs[0].remediation) > 0

    def test_validate_with_spec_dangling_datasource_has_line(
        self, validator: SemanticValidator
    ) -> None:
        """validate() with --spec populates spec_line for dangling datasource warnings."""
        result = validator.validate(
            FIXTURES_DIR / "dangling_datasource.twb",
            spec_path=FIXTURES_DIR / "dangling_datasource_spec.yaml",
        )
        ds_warnings = [
            w for w in result.warnings if w.category == "dangling_datasource_ref"
        ]
        assert len(ds_warnings) >= 1
        assert ds_warnings[0].spec_line is not None
        assert isinstance(ds_warnings[0].spec_line, int)
        assert ds_warnings[0].spec_line >= 1

    def test_validate_without_spec_has_no_spec_fields(
        self, validator: SemanticValidator
    ) -> None:
        """validate() without spec produces spec_file=None, spec_line=None (backward compat)."""
        result = validator.validate(FIXTURES_DIR / "broken_references.twb")
        assert result.valid is False
        for err in result.errors:
            assert err.spec_file is None
            assert err.spec_line is None
