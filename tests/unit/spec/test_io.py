"""Tests for YAML I/O: load_spec and dump_spec."""

from pathlib import Path

import pytest
import yaml

from tableau_agent_toolkit.spec.io import SpecValidationError, dump_spec, load_spec
from tableau_agent_toolkit.spec.models import DashboardSpec


# ---------------------------------------------------------------------------
# Test 1: load_spec reads valid YAML and returns DashboardSpec
# ---------------------------------------------------------------------------
def test_load_spec_valid(sample_spec_path: Path) -> None:
    spec = load_spec(sample_spec_path)
    assert isinstance(spec, DashboardSpec)
    assert spec.workbook.name == "Test Workbook"


# ---------------------------------------------------------------------------
# Test 2: load_spec raises error for missing workbook field
# ---------------------------------------------------------------------------
def test_load_spec_missing_workbook(tmp_path: Path) -> None:
    spec_file = tmp_path / "bad.yaml"
    spec_file.write_text("spec_version: '1.0'\n", encoding="utf-8")
    with pytest.raises(SpecValidationError, match="workbook"):
        load_spec(spec_file)


# ---------------------------------------------------------------------------
# Test 3: load_spec raises FileNotFoundError for non-existent file
# ---------------------------------------------------------------------------
def test_load_spec_file_not_found(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError, match="Spec file not found"):
        load_spec(missing)


# ---------------------------------------------------------------------------
# Test 4: dump_spec writes YAML file
# ---------------------------------------------------------------------------
def test_dump_spec_writes_yaml(tmp_path: Path) -> None:
    spec = DashboardSpec(
        workbook={
            "name": "Dump Test",
            "template": {"id": "t1", "path": "templates/test.twb"},
        }
    )
    out_path = tmp_path / "output.yaml"
    dump_spec(spec, out_path)
    assert out_path.exists()
    content = out_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(content)
    assert parsed["workbook"]["name"] == "Dump Test"


# ---------------------------------------------------------------------------
# Test 5: Round-trip: load_spec -> dump_spec -> load_spec
# ---------------------------------------------------------------------------
def test_round_trip(sample_spec_dict: dict, tmp_path: Path) -> None:
    # Write original
    original_path = tmp_path / "original.yaml"
    with open(original_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_spec_dict, f, default_flow_style=False, sort_keys=False)

    # Load, dump, load again
    spec1 = load_spec(original_path)
    dump_path = tmp_path / "dumped.yaml"
    dump_spec(spec1, dump_path)
    spec2 = load_spec(dump_path)

    assert spec1.workbook.name == spec2.workbook.name
    assert spec1.workbook.target_tableau_version == spec2.workbook.target_tableau_version
    assert spec1.spec_version == spec2.spec_version


# ---------------------------------------------------------------------------
# Test 6: Determinism: two dumps produce identical files
# ---------------------------------------------------------------------------
def test_dump_deterministic(tmp_path: Path) -> None:
    spec = DashboardSpec(
        workbook={
            "name": "Determinism Test",
            "template": {"id": "t1", "path": "templates/test.twb"},
        }
    )
    path_a = tmp_path / "dump_a.yaml"
    path_b = tmp_path / "dump_b.yaml"
    dump_spec(spec, path_a)
    dump_spec(spec, path_b)
    assert path_a.read_bytes() == path_b.read_bytes()


# ---------------------------------------------------------------------------
# Test 7: Extra/unknown fields raise validation error
# ---------------------------------------------------------------------------
def test_load_spec_extra_fields(tmp_path: Path) -> None:
    spec_file = tmp_path / "extra.yaml"
    spec_file.write_text(
        "workbook:\n"
        "  name: Test\n"
        "  template:\n"
        "    id: t1\n"
        "    path: templates/test.twb\n"
        "unknown_field: oops\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecValidationError, match="extra"):
        load_spec(spec_file)


# ---------------------------------------------------------------------------
# Test 8: Error message includes field path
# ---------------------------------------------------------------------------
def test_error_message_includes_field_path(tmp_path: Path) -> None:
    spec_file = tmp_path / "bad_path.yaml"
    spec_file.write_text(
        "workbook:\n"
        "  name: ''\n"
        "  template:\n"
        "    id: t1\n"
        "    path: templates/test.twb\n",
        encoding="utf-8",
    )
    with pytest.raises(SpecValidationError) as exc_info:
        load_spec(spec_file)
    # The error message should reference the field path
    assert "workbook" in str(exc_info.value) or "name" in str(exc_info.value)
    assert exc_info.value.field_path is not None
