"""YAML I/O for dashboard specifications.

Provides load_spec and dump_spec for reading and writing
dashboard_spec.yaml files with Pydantic validation.
"""

from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from tableau_agent_toolkit.spec.models import DashboardSpec


class SpecValidationError(Exception):
    """Raised when spec validation fails, with field path context."""

    def __init__(self, message: str, field_path: str | None = None) -> None:
        self.field_path = field_path
        super().__init__(message)


def load_spec(path: Path) -> DashboardSpec:
    """Load and validate a dashboard spec from YAML.

    Uses yaml.safe_load() exclusively (never yaml.load()).
    Validates through Pydantic and formats errors with field paths.

    Args:
        path: Path to the YAML spec file.

    Returns:
        Validated DashboardSpec object.

    Raises:
        FileNotFoundError: If the spec file does not exist.
        SpecValidationError: If validation fails, with field path context.
    """
    if not path.exists():
        raise FileNotFoundError(f"Spec file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        raw: Any = yaml.safe_load(f)
    if raw is None:
        raise SpecValidationError("Spec file is empty")
    try:
        return DashboardSpec.model_validate(raw)
    except ValidationError as e:
        errors = e.errors()
        parts = []
        for err in errors:
            loc = " -> ".join(str(loc_item) for loc_item in err["loc"])
            msg = err["msg"]
            parts.append(f"{loc}: {msg}")
        message = "; ".join(parts)
        field_path = " -> ".join(str(loc_item) for loc_item in errors[0]["loc"]) if errors else None
        raise SpecValidationError(message, field_path=field_path) from e


def dump_spec(spec: DashboardSpec, path: Path) -> None:
    """Serialize a DashboardSpec to YAML.

    Uses sort_keys=False and default_flow_style=False for deterministic output.

    Args:
        spec: The DashboardSpec to serialize.
        path: Output file path.
    """
    data = spec.model_dump(mode="json", exclude_none=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
