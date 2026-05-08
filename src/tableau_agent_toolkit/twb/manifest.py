"""TWB version mapping and manifest application utilities.

Provides TableauVersion for mapping between XSD filenames and TWB version strings,
and apply_manifest_by_version for setting version attributes on workbook XML trees.
"""

import re
from dataclasses import dataclass

from lxml import etree


@dataclass(frozen=True)
class TableauVersion:
    """Represents a Tableau version with major and minor components.

    Maps between XSD filenames (e.g., twb_2026.1.0.xsd) and TWB version
    strings (e.g., 26.1).
    """

    major: int
    minor: int

    @classmethod
    def from_xsd_filename(cls, filename: str) -> "TableauVersion":
        """Parse an XSD filename like 'twb_2026.1.0.xsd' into a TableauVersion.

        Args:
            filename: XSD filename to parse.

        Returns:
            TableauVersion with major = year - 2000, minor = release number.

        Raises:
            ValueError: If filename does not match the expected pattern.
        """
        match = re.match(r"twb_(\d{4})\.(\d+)\.\d+\.xsd", filename)
        if not match:
            raise ValueError(f"Invalid XSD filename: {filename}")
        year = int(match.group(1))
        release = int(match.group(2))
        return cls(major=year - 2000, minor=release)

    @classmethod
    def from_display_version(cls, version: str) -> "TableauVersion":
        """Parse a display version like '2026.1' into a TableauVersion.

        Args:
            version: Display version string (e.g., '2026.1').

        Returns:
            TableauVersion with major = year - 2000, minor = release number.

        Raises:
            ValueError: If version does not match the expected pattern.
        """
        match = re.match(r"(\d{4})\.(\d+)", version)
        if not match:
            raise ValueError(f"Invalid display version: {version}")
        year = int(match.group(1))
        release = int(match.group(2))
        return cls(major=year - 2000, minor=release)

    @property
    def twb_version_string(self) -> str:
        """Return the TWB version string (e.g., '26.1' for TableauVersion(26, 1))."""
        return f"{self.major}.{self.minor}"

    @property
    def xsd_version_string(self) -> str:
        """Return the XSD version string (e.g., '2026.1.0' for TableauVersion(26, 1))."""
        return f"20{self.major:02d}.{self.minor}.0"


def apply_manifest_by_version(tree: etree._ElementTree, tableau_version: str) -> None:
    """Apply version attributes and ManifestByVersion element to a workbook XML tree.

    Sets version, original-version, source-build, and source-platform attributes on
    the root element. Creates or updates the document-format-change-manifest element
    with a ManifestByVersion child.

    Args:
        tree: The workbook XML tree to modify (modified in-place).
        tableau_version: Display version string (e.g., '2026.1').
    """
    version = TableauVersion.from_display_version(tableau_version)
    root = tree.getroot()

    # Set version attributes on root
    root.attrib["version"] = version.twb_version_string
    root.attrib["original-version"] = version.twb_version_string
    root.attrib["source-build"] = "0.0.0 (0000.0.0.0.0)"
    root.attrib["source-platform"] = "win"

    # Find or create document-format-change-manifest element
    manifest = root.find(".//document-format-change-manifest")
    if manifest is None:
        manifest = etree.SubElement(root, "document-format-change-manifest")

    # Clear existing children and add ManifestByVersion
    manifest.clear()
    manifest.append(etree.Element("ManifestByVersion"))
