"""XSD validator for Tableau workbook files.

Validates .twb files against pinned XSD schemas from the vendored
tableau-document-schemas directory. Reports validation errors with
line, column, and message information.
"""

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree


@dataclass
class XsdError:
    """A single XSD validation error.

    Attributes:
        line: Line number where the error was found.
        column: Column number where the error was found.
        message: Human-readable error description.
    """

    line: int
    column: int
    message: str


@dataclass
class XsdValidationResult:
    """Result of an XSD validation operation.

    Attributes:
        valid: Whether the TWB file passed XSD validation.
        errors: List of validation errors (empty if valid).
    """

    valid: bool
    errors: list[XsdError] = field(default_factory=list)


class XsdValidator:
    """Validates Tableau workbook files against pinned XSD schemas.

    Resolves the correct XSD file based on a Tableau version string
    (e.g., '2026.1' -> '2026_1/twb_2026.1.0.xsd') and validates TWB files
    using lxml's XMLSchema.

    Args:
        schemas_root: Root directory containing versioned XSD schema files.

    Raises:
        FileNotFoundError: If schemas_root does not exist.
    """

    def __init__(self, schemas_root: Path) -> None:
        self._schemas_root = Path(schemas_root)
        if not self._schemas_root.exists():
            raise FileNotFoundError(f"Schemas root not found: {self._schemas_root}")

    def _resolve_xsd(self, tableau_version: str) -> Path:
        """Resolve a Tableau version string to an XSD file path.

        Converts a display version like '2026.1' to the path
        '2026_1/twb_2026.1.0.xsd' relative to schemas_root.

        Args:
            tableau_version: Display version string (e.g., '2026.1').

        Returns:
            Absolute path to the XSD file.

        Raises:
            FileNotFoundError: If the resolved XSD file does not exist.
        """
        # Parse version: "2026.1" -> parts ["2026", "1"]
        parts = tableau_version.split(".")
        year = parts[0]
        release = parts[1] if len(parts) > 1 else "1"

        # Build path: 2026_1/twb_2026.1.0.xsd
        dir_name = f"{year}_{release}"
        filename = f"twb_{year}.{release}.0.xsd"
        xsd_path = self._schemas_root / dir_name / filename

        if not xsd_path.exists():
            raise FileNotFoundError(f"XSD schema not found: {xsd_path}")

        return xsd_path

    def validate(
        self, twb_path: Path, tableau_version: str = "2026.1"
    ) -> XsdValidationResult:
        """Validate a TWB file against the XSD schema for the given version.

        Args:
            twb_path: Path to the .twb file to validate.
            tableau_version: Target Tableau version for schema resolution.

        Returns:
            XsdValidationResult with valid flag and any errors.
        """
        xsd_path = self._resolve_xsd(tableau_version)

        # Load XSD schema
        schema_doc = etree.parse(str(xsd_path))
        schema = etree.XMLSchema(schema_doc)

        # Load TWB with secure parser (T-01-08 mitigation)
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        doc = etree.parse(str(twb_path), parser)

        # Validate
        valid = schema.validate(doc)

        # Collect errors
        errors = [
            XsdError(line=e.line, column=e.column, message=e.message)
            for e in schema.error_log
        ]

        return XsdValidationResult(valid=valid, errors=errors)
