"""Tests for the XSD validator module.

Covers XsdValidator initialization, validation against XSD, error reporting,
and version-based schema resolution.
"""

from pathlib import Path

import pytest
from lxml import etree

from tableau_agent_toolkit.validation.xsd import XsdError, XsdValidationResult, XsdValidator

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
MINIMAL_TEMPLATE = FIXTURES_DIR / "minimal_template.twb"
SCHEMAS_ROOT = FIXTURES_DIR / "schemas"


class TestXsdValidatorInit:
    """Tests for XsdValidator initialization."""

    def test_init_succeeds_with_existing_directory(self) -> None:
        """Test 1: XsdValidator.__init__ succeeds when schemas_root directory exists."""
        validator = XsdValidator(schemas_root=SCHEMAS_ROOT)
        assert validator._schemas_root == SCHEMAS_ROOT

    def test_init_fails_with_nonexistent_directory(self) -> None:
        """XsdValidator.__init__ should raise when schemas_root does not exist."""
        with pytest.raises(FileNotFoundError):
            XsdValidator(schemas_root=Path("/nonexistent/path"))


class TestXsdValidation:
    """Tests for XSD validation of TWB files."""

    def test_validate_returns_valid_for_matching_xml(self) -> None:
        """Test 2: XsdValidator.validate returns valid=True for well-formed XML matching XSD."""
        validator = XsdValidator(schemas_root=SCHEMAS_ROOT)
        result = validator.validate(MINIMAL_TEMPLATE, tableau_version="2026.1")

        assert result.valid is True
        assert result.errors == []

    def test_validate_returns_invalid_for_malformed_xml(self, tmp_path: Path) -> None:
        """Test 3: XsdValidator.validate returns valid=False for malformed XML."""
        # Create an invalid TWB that will fail XSD validation
        invalid_twb = tmp_path / "invalid.twb"
        invalid_twb.write_text(
            '<?xml version="1.0" encoding="utf-8"?>\n<invalid_root />',
            encoding="utf-8",
        )

        validator = XsdValidator(schemas_root=SCHEMAS_ROOT)
        result = validator.validate(invalid_twb, tableau_version="2026.1")

        assert result.valid is False
        assert len(result.errors) > 0


class TestXsdError:
    """Tests for XsdError dataclass."""

    def test_xsd_error_contains_line_column_message(self) -> None:
        """Test 4: XsdError contains line, column, and message fields."""
        error = XsdError(line=10, column=5, message="Element 'foo' not expected")

        assert error.line == 10
        assert error.column == 5
        assert error.message == "Element 'foo' not expected"


class TestXsdValidationResult:
    """Tests for XsdValidationResult dataclass."""

    def test_result_has_valid_and_errors(self) -> None:
        """Test 5: XsdValidationResult has valid boolean and errors list."""
        result = XsdValidationResult(valid=True, errors=[])

        assert result.valid is True
        assert result.errors == []

    def test_result_with_errors(self) -> None:
        """XsdValidationResult correctly stores validation errors."""
        errors = [XsdError(line=1, column=1, message="test error")]
        result = XsdValidationResult(valid=False, errors=errors)

        assert result.valid is False
        assert len(result.errors) == 1
        assert result.errors[0].message == "test error"


class TestVersionResolution:
    """Tests for version-based XSD file resolution."""

    def test_resolves_xsd_by_version_string(self, tmp_path: Path) -> None:
        """Test 6: validate resolves XSD by version string '2026.1' to correct schema file."""
        # Use the fixture schemas directory which has the versioned structure
        validator = XsdValidator(schemas_root=SCHEMAS_ROOT)

        # Verify the schema resolves correctly by validating a valid file
        result = validator.validate(MINIMAL_TEMPLATE, tableau_version="2026.1")
        assert result.valid is True

        # Verify the resolved path is correct
        xsd_path = validator._resolve_xsd("2026.1")
        assert xsd_path == SCHEMAS_ROOT / "2026_1" / "twb_2026.1.0.xsd"
        assert xsd_path.exists()
