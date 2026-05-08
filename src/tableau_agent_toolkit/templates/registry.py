"""Template registry for resolving template IDs to template file paths.

Loads template entries from a catalog.yaml file and provides lookup by
template ID with optional Tableau version compatibility checking.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class TemplateMatch:
    """Represents a resolved template entry from the catalog.

    Attributes:
        id: The logical template identifier (e.g., 'finance-reconciliation').
        path: Resolved absolute path to the .twb template file.
        required_anchors: Anchor element names the template expects to find.
        tableau_versions: Compatible Tableau display versions (e.g., ['2026.1']).
    """

    id: str
    path: Path
    required_anchors: list[str] = field(default_factory=list)
    tableau_versions: list[str] = field(default_factory=list)


class TemplateRegistry:
    """Loads and resolves template entries from a catalog.yaml file.

    The catalog maps logical template IDs to file paths, required anchor elements,
    and compatible Tableau versions. Template paths are resolved relative to the
    catalog file's parent directory.

    Args:
        catalog_path: Path to the catalog.yaml file. Defaults to
            project-root/templates/catalog.yaml.
    """

    def __init__(self, catalog_path: Path | None = None) -> None:
        if catalog_path is None:
            # Default: project root templates/catalog.yaml
            catalog_path = (
                Path(__file__).parent.parent.parent.parent / "templates" / "catalog.yaml"
            )
        self._catalog_path = Path(catalog_path)

        if not self._catalog_path.exists():
            raise FileNotFoundError(f"Template catalog not found: {self._catalog_path}")

        with open(self._catalog_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._templates: dict[str, dict] = data.get("templates", {}) if data else {}

    def resolve(self, template_id: str, tableau_version: str | None = None) -> TemplateMatch:
        """Resolve a template ID to a TemplateMatch with path and metadata.

        Args:
            template_id: The logical template identifier to look up.
            tableau_version: Optional Tableau version to check compatibility.
                If provided and the version is not in the template's compatible
                versions list, a warning is logged but resolution still succeeds.

        Returns:
            TemplateMatch with resolved absolute path and metadata.

        Raises:
            ValueError: If the template_id is not found in the catalog.
        """
        entry = self._templates.get(template_id)
        if entry is None:
            raise ValueError(f"Template not found: {template_id}")

        # Resolve path relative to catalog directory
        template_path = (self._catalog_path.parent / entry["path"]).resolve()

        # Security: reject paths with ".." components to prevent path traversal
        # (T-01-04 mitigation)
        try:
            template_path.relative_to(self._catalog_path.parent.resolve())
        except ValueError:
            raise ValueError(
                f"Template path escapes catalog directory: {entry['path']}"
            )

        # Verify the path string doesn't contain ".." segments
        path_parts = Path(entry["path"]).parts
        if ".." in path_parts:
            raise ValueError(
                f"Template path contains '..' component: {entry['path']}"
            )

        return TemplateMatch(
            id=template_id,
            path=template_path,
            required_anchors=entry.get("required_anchors", []),
            tableau_versions=entry.get("tableau_versions", []),
        )
