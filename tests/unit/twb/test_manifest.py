"""Unit tests for TableauVersion utility and apply_manifest_by_version handler."""

import re

import pytest
from lxml import etree


class TestTableauVersionFromXsdFilename:
    """Tests for TableauVersion.from_xsd_filename()."""

    def test_parses_2026_1_xsd_filename(self):
        """twb_2026.1.0.xsd maps to TableauVersion(major=26, minor=1)."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        version = TableauVersion.from_xsd_filename("twb_2026.1.0.xsd")
        assert version.major == 26
        assert version.minor == 1

    def test_parses_2025_4_xsd_filename(self):
        """twb_2025.4.0.xsd maps to TableauVersion(major=25, minor=4)."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        version = TableauVersion.from_xsd_filename("twb_2025.4.0.xsd")
        assert version.major == 25
        assert version.minor == 4

    def test_invalid_xsd_filename_raises_value_error(self):
        """Invalid XSD filename raises ValueError."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        with pytest.raises(ValueError, match="Invalid XSD filename"):
            TableauVersion.from_xsd_filename("invalid.xsd")


class TestTableauVersionStrings:
    """Tests for TableauVersion string properties."""

    def test_twb_version_string(self):
        """TableauVersion(26, 1).twb_version_string returns '26.1'."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        version = TableauVersion(26, 1)
        assert version.twb_version_string == "26.1"

    def test_xsd_version_string(self):
        """TableauVersion(26, 1).xsd_version_string returns '2026.1.0'."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        version = TableauVersion(26, 1)
        assert version.xsd_version_string == "2026.1.0"


class TestTableauVersionImmutability:
    """Tests for TableauVersion frozen dataclass behavior."""

    def test_frozen_raises_attribute_error_on_set(self):
        """Attempting to set major raises AttributeError."""
        from tableau_agent_toolkit.twb.manifest import TableauVersion

        version = TableauVersion(26, 1)
        with pytest.raises(AttributeError):
            version.major = 99  # type: ignore[misc]


class TestApplyManifestByVersion:
    """Tests for apply_manifest_by_version function."""

    def _make_workbook_tree(self) -> etree._ElementTree:
        """Create a minimal workbook XML tree for testing."""
        xml = (
            '<workbook xmlns:user="http://www.tableausoftware.com/xml/user"'
            ' source-build="old" source-platform="old">'
            "<worksheet name='Sheet1'/>"
            "</workbook>"
        )
        return etree.fromstring(xml.encode(), parser=etree.XMLParser())

    def test_sets_version_attribute(self):
        """apply_manifest_by_version sets root version attribute to '26.1' when given '2026.1'."""
        from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version

        tree = self._make_workbook_tree()
        root = tree if isinstance(tree, etree._Element) else tree.getroot()
        tree_obj = etree.ElementTree(root)
        apply_manifest_by_version(tree_obj, "2026.1")
        assert root.attrib["version"] == "26.1"

    def test_sets_original_version_attribute(self):
        """apply_manifest_by_version sets root original-version attribute to '26.1'."""
        from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version

        tree = self._make_workbook_tree()
        root = tree if isinstance(tree, etree._Element) else tree.getroot()
        tree_obj = etree.ElementTree(root)
        apply_manifest_by_version(tree_obj, "2026.1")
        assert root.attrib["original-version"] == "26.1"

    def test_creates_manifest_by_version_element(self):
        """apply_manifest_by_version creates document-format-change-manifest with ManifestByVersion child."""
        from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version

        tree = self._make_workbook_tree()
        root = tree if isinstance(tree, etree._Element) else tree.getroot()
        tree_obj = etree.ElementTree(root)
        apply_manifest_by_version(tree_obj, "2026.1")

        manifest = root.find(".//document-format-change-manifest")
        assert manifest is not None
        manifest_by_version = manifest.find("ManifestByVersion")
        assert manifest_by_version is not None

    def test_preserves_namespace_declarations(self):
        """apply_manifest_by_version preserves existing namespace declarations (xmlns:user)."""
        from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version

        tree = self._make_workbook_tree()
        root = tree if isinstance(tree, etree._Element) else tree.getroot()
        tree_obj = etree.ElementTree(root)
        apply_manifest_by_version(tree_obj, "2026.1")

        nsmap = root.nsmap
        assert "user" in nsmap
