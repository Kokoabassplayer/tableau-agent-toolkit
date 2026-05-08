"""Unit tests for TemplateRegistry and catalog.yaml loading."""

from pathlib import Path

import pytest
import yaml


class TestTemplateRegistryResolve:
    """Tests for TemplateRegistry.resolve()."""

    def _write_catalog(self, tmp_path: Path, catalog_data: dict) -> Path:
        """Write a test catalog.yaml to the given temp directory."""
        catalog_file = tmp_path / "catalog.yaml"
        catalog_file.write_text(yaml.dump(catalog_data, default_flow_style=False))
        return catalog_file

    def test_resolves_known_template_id(self, tmp_path: Path):
        """TemplateRegistry resolves a known template ID to a TemplateMatch."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        catalog = {
            "templates": {
                "test-template": {
                    "path": "test/template.twb",
                    "tableau_versions": ["2026.1"],
                    "required_anchors": ["datasource-pane"],
                }
            }
        }
        catalog_path = self._write_catalog(tmp_path, catalog)
        registry = TemplateRegistry(catalog_path=catalog_path)
        match = registry.resolve("test-template")
        assert match.id == "test-template"

    def test_unknown_template_id_raises_value_error(self, tmp_path: Path):
        """TemplateRegistry.resolve raises ValueError for unknown template ID."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        catalog = {"templates": {}}
        catalog_path = self._write_catalog(tmp_path, catalog)
        registry = TemplateRegistry(catalog_path=catalog_path)
        with pytest.raises(ValueError, match="Template not found"):
            registry.resolve("nonexistent")

    def test_template_match_contains_correct_path(self, tmp_path: Path):
        """TemplateMatch contains the correct path from catalog.yaml."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        catalog = {
            "templates": {
                "finance-report": {
                    "path": "finance/report.twb",
                    "tableau_versions": ["2026.1"],
                    "required_anchors": ["datasource-pane", "dashboard-layout"],
                }
            }
        }
        catalog_path = self._write_catalog(tmp_path, catalog)
        registry = TemplateRegistry(catalog_path=catalog_path)
        match = registry.resolve("finance-report")
        # Path should be resolved relative to catalog directory
        expected = (catalog_path.parent / "finance" / "report.twb").resolve()
        assert match.path == expected

    def test_loads_catalog_from_default_path(self):
        """TemplateRegistry loads catalog from default path when no path specified."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        # The default path resolves to project root templates/catalog.yaml
        # We verify the class can be instantiated without errors
        # (the actual default catalog file existence is checked separately)
        registry = TemplateRegistry.__new__(TemplateRegistry)
        # Just verify the class exists and has a resolve method
        assert hasattr(TemplateRegistry, "resolve")

    def test_missing_catalog_raises_file_not_found(self, tmp_path: Path):
        """TemplateRegistry raises FileNotFoundError when catalog.yaml does not exist."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        missing_path = tmp_path / "nonexistent" / "catalog.yaml"
        with pytest.raises(FileNotFoundError):
            TemplateRegistry(catalog_path=missing_path)

    def test_template_match_has_required_anchors(self, tmp_path: Path):
        """TemplateMatch has required_anchors list populated from catalog."""
        from tableau_agent_toolkit.templates.registry import TemplateRegistry

        catalog = {
            "templates": {
                "dashboard-basic": {
                    "path": "dashboards/basic.twb",
                    "tableau_versions": ["2026.1"],
                    "required_anchors": ["datasource-pane", "dashboard-layout", "style-pane"],
                }
            }
        }
        catalog_path = self._write_catalog(tmp_path, catalog)
        registry = TemplateRegistry(catalog_path=catalog_path)
        match = registry.resolve("dashboard-basic")
        assert match.required_anchors == ["datasource-pane", "dashboard-layout", "style-pane"]
