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
        """Return the TWB version string.

        All modern Tableau versions (2018.3+) use '18.1' as the internal TWB
        format version.  This is separate from the product version (e.g. 2024.2).
        """
        return "18.1"

    @property
    def xsd_version_string(self) -> str:
        """Return the XSD version string (e.g., '2026.1.0' for TableauVersion(26, 1))."""
        return f"20{self.major:02d}.{self.minor}.0"


def _propagate_version_to_descendants(
    tree: etree._ElementTree,
    template_twb: str,
    target_twb: str,
) -> None:
    """Replace version attributes on all descendant elements.

    Finds every element in the tree that has a ``version`` attribute equal to
    *template_twb* and replaces it with *target_twb*.  The root element is
    skipped because ``apply_manifest_by_version`` already handles it.

    Args:
        tree: The workbook XML tree to modify (modified in-place).
        template_twb: The TWB version string from the template (e.g. '26.1').
        target_twb: The TWB version string for the target (e.g. '24.2').
    """
    root = tree.getroot()
    for element in root.iter():
        if element is root:
            continue
        if element.get("version") == template_twb:
            element.set("version", target_twb)


def apply_manifest_by_version(tree: etree._ElementTree, tableau_version: str) -> None:
    """Apply version attributes and ManifestByVersion element to a workbook XML tree.

    Sets version, original-version, source-build, and source-platform attributes on
    the root element. Creates or updates the document-format-change-manifest element
    with a ManifestByVersion child.  When the target version differs from the
    template version, propagates the target version to all descendant elements
    (e.g. ``<datasource version="...">``).

    Args:
        tree: The workbook XML tree to modify (modified in-place).
        tableau_version: Display version string (e.g., '2026.1').
    """
    version = TableauVersion.from_display_version(tableau_version)
    root = tree.getroot()
    target_twb = version.twb_version_string

    # Capture template version before overwriting root attributes
    template_twb = root.get("version")

    # Set version attributes on root
    root.attrib["version"] = target_twb
    root.attrib["original-version"] = target_twb
    # source-build must match Tableau's format: "<YYYYR>.<YY>.<MMDD>.<HHMM>"
    # e.g. Tableau 2024.2 produces "20242.24.0807.0327"
    product_build = f"20{version.major:02d}{version.minor}"
    year_short = f"{2000 + version.major}"[-2:]
    root.attrib["source-build"] = (
        f"{tableau_version}.0 ({product_build}.{year_short}.0000.0000)"
    )
    root.attrib["source-platform"] = "win"

    # Propagate version to all internal elements when template differs
    if template_twb is not None and template_twb != target_twb:
        _propagate_version_to_descendants(tree, template_twb, target_twb)

    # Find or create document-format-change-manifest element.
    # Must use feature-flag entries (not <ManifestByVersion/>) because
    # Tableau Desktop rejects empty ManifestByVersion as "incompatible
    # manifest entries" (error 95B9F4BA).
    manifest = root.find(".//document-format-change-manifest")
    if manifest is None:
        manifest = etree.SubElement(root, "document-format-change-manifest")

    manifest.clear()
    for tag in [
        "_.fcp.AnimationOnByDefault.true...AnimationOnByDefault",
        "_.fcp.MarkAnimation.true...MarkAnimation",
        "_.fcp.ObjectModelEncapsulateLegacy.true...ObjectModelEncapsulateLegacy",
        "_.fcp.ObjectModelTableType.true...ObjectModelTableType",
        "_.fcp.RelationshipCalculations.true...RelationshipCalculations",
        "_.fcp.SchemaViewerObjectModel.true...SchemaViewerObjectModel",
        "SheetIdentifierTracking",
        "WindowsPersistSimpleIdentifiers",
    ]:
        manifest.append(etree.Element(tag))
