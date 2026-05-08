"""QA report types and report generation.

Defines the data structures and report generation for quality assurance checks:
- CheckStatus: outcome of a single QA check (PASS, FAIL, WARN, SKIP)
- QACheckResult: a single QA check result
- generate_qa_report: produces a markdown QA report from check results
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class CheckStatus(str, Enum):
    """Outcome of a single QA check."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class QACheckResult:
    """Result of a single QA check.

    Attributes:
        check_name: Name/identifier of the check that was run.
        status: Outcome of the check.
        message: Human-readable description of the result.
        details: Additional details about the finding.
    """

    check_name: str
    status: CheckStatus
    message: str
    details: list[str] = field(default_factory=list)


def generate_qa_report(results: list[QACheckResult], twb_path: Path) -> str:
    """Generate a markdown QA report from check results.

    Produces a structured markdown report with sections ordered:
    Errors, Warnings, Passed Checks.

    Args:
        results: List of QA check results to include in the report.
        twb_path: Path to the TWB file that was checked.

    Returns:
        Markdown-formatted QA report string.
    """
    failed = [r for r in results if r.status == CheckStatus.FAIL]
    warned = [r for r in results if r.status == CheckStatus.WARN]
    passed = [r for r in results if r.status == CheckStatus.PASS]

    lines: list[str] = []

    # Header
    lines.append(f"# QA Report: {twb_path.name}")
    lines.append("")

    # Summary
    lines.append(
        f"**Summary:** {len(passed)} passed, {len(warned)} warnings, {len(failed)} failed"
    )
    lines.append("")

    # Errors section
    if failed:
        lines.append("## Errors")
        lines.append("")
        for check in failed:
            lines.append(f"- **{check.check_name}**: {check.message}")
            for detail in check.details:
                lines.append(f"  - {detail}")
            lines.append("  - Remediation: Fix the identified issue and re-validate.")
        lines.append("")

    # Warnings section
    if warned:
        lines.append("## Warnings")
        lines.append("")
        for check in warned:
            lines.append(f"- **{check.check_name}**: {check.message}")
            for detail in check.details:
                lines.append(f"  - {detail}")
        lines.append("")

    # Passed checks section
    if passed:
        lines.append("## Passed Checks")
        lines.append("")
        for check in passed:
            lines.append(f"- {check.check_name}")
        lines.append("")

    return "\n".join(lines)
