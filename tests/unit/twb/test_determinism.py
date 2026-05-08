"""Tests for TWB generator output determinism.

Verifies that generating the same spec + template twice produces byte-identical
output files.
"""

from pathlib import Path

import pytest

from tableau_agent_toolkit.spec.models import (
    DashboardSpec,
    PackagingEnum,
    TemplateSpec,
    WorkbookSpec,
)
from tableau_agent_toolkit.twb.generator import WorkbookGenerator

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"
MINIMAL_TEMPLATE = FIXTURES_DIR / "minimal_template.twb"


def _make_spec() -> DashboardSpec:
    """Create a minimal DashboardSpec for determinism testing."""
    return DashboardSpec(
        spec_version="1.0",
        workbook=WorkbookSpec(
            name="DeterminismTest",
            target_tableau_version="2026.1",
            packaging=PackagingEnum.twb,
            template=TemplateSpec(
                id="test-template",
                path=MINIMAL_TEMPLATE,
                required_anchors=[],
            ),
        ),
    )


def _make_registry() -> "MagicMock":
    """Create a mock TemplateRegistry resolving to the minimal template."""
    from unittest.mock import MagicMock

    registry = MagicMock()
    registry.resolve.return_value = MagicMock(
        id="test-template",
        path=MINIMAL_TEMPLATE,
    )
    return registry


def test_deterministic_output(tmp_path: Path) -> None:
    """Test 3: Same spec + template produces byte-identical output on two runs."""
    spec = _make_spec()
    registry = _make_registry()
    output_a = tmp_path / "run_a.twb"
    output_b = tmp_path / "run_b.twb"

    generator = WorkbookGenerator(template_registry=registry)
    generator.generate(spec, output_a)
    generator.generate(spec, output_b)

    content_a = output_a.read_bytes()
    content_b = output_b.read_bytes()
    assert content_a == content_b, "Identical spec + template must produce byte-identical .twb"
