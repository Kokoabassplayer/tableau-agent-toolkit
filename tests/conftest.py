"""Shared pytest fixtures for tableau-agent-toolkit tests."""

from pathlib import Path

import pytest
import yaml


@pytest.fixture()
def sample_spec_dict() -> dict:
    """Return a minimal valid dashboard spec as a dict."""
    return {
        "workbook": {
            "name": "Test Workbook",
            "template": {
                "id": "test-template",
                "path": "templates/test.twb",
            },
        },
    }


@pytest.fixture()
def sample_spec_path(tmp_path: Path, sample_spec_dict: dict) -> Path:
    """Write sample_spec_dict to a YAML file and return the path."""
    spec_file = tmp_path / "test_spec.yaml"
    with open(spec_file, "w", encoding="utf-8") as f:
        yaml.dump(sample_spec_dict, f, default_flow_style=False, sort_keys=False)
    return spec_file


FIXTURES_DIR = Path(__file__).parent / "fixtures"
