"""Tests for QA report types (CheckStatus, QACheckResult, generate_qa_report)."""

from dataclasses import fields
from pathlib import Path

from tableau_agent_toolkit.qa.report import (
    CheckStatus,
    QACheckResult,
    generate_qa_report,
)


class TestCheckStatus:
    """Tests for the CheckStatus enum."""

    def test_has_pass(self) -> None:
        assert CheckStatus.PASS.value == "PASS"

    def test_has_fail(self) -> None:
        assert CheckStatus.FAIL.value == "FAIL"

    def test_has_warn(self) -> None:
        assert CheckStatus.WARN.value == "WARN"

    def test_has_skip(self) -> None:
        assert CheckStatus.SKIP.value == "SKIP"

    def test_four_members(self) -> None:
        assert len(CheckStatus) == 4


class TestQACheckResult:
    """Tests for the QACheckResult dataclass."""

    def test_has_required_fields(self) -> None:
        field_names = {f.name for f in fields(QACheckResult)}
        assert "check_name" in field_names
        assert "status" in field_names
        assert "message" in field_names
        assert "details" in field_names

    def test_create_with_required_fields(self) -> None:
        result = QACheckResult(
            check_name="empty_dashboard",
            status=CheckStatus.PASS,
            message="No empty dashboards found",
        )
        assert result.check_name == "empty_dashboard"
        assert result.status is CheckStatus.PASS
        assert result.message == "No empty dashboards found"
        assert result.details == []

    def test_create_with_details(self) -> None:
        result = QACheckResult(
            check_name="broken_ref",
            status=CheckStatus.FAIL,
            message="Broken references found",
            details=["Sheet X not found", "Datasource Y missing"],
        )
        assert len(result.details) == 2


class TestGenerateQaReport:
    """Tests for the generate_qa_report function."""

    def _make_results(self) -> list[QACheckResult]:
        return [
            QACheckResult(
                check_name="empty_dashboard",
                status=CheckStatus.FAIL,
                message="Dashboard has no zones",
                details=["Dashboard 'EmptyDash' has zero zones"],
            ),
            QACheckResult(
                check_name="broken_reference",
                status=CheckStatus.WARN,
                message="Potential broken reference",
                details=["Action references unknown sheet"],
            ),
            QACheckResult(
                check_name="field_coverage",
                status=CheckStatus.PASS,
                message="All fields have valid sources",
            ),
        ]

    def test_starts_with_header(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        assert report.startswith("# QA Report: test.twb")

    def test_has_summary_line(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        assert "**Summary:** 1 passed, 1 warnings, 1 failed" in report

    def test_errors_section_before_warnings(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        errors_pos = report.find("## Errors")
        warnings_pos = report.find("## Warnings")
        assert errors_pos < warnings_pos

    def test_warnings_section_before_passed(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        warnings_pos = report.find("## Warnings")
        passed_pos = report.find("## Passed Checks")
        assert warnings_pos < passed_pos

    def test_failed_check_shows_remediation(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        assert "Remediation:" in report

    def test_check_name_appears_in_error_section(self) -> None:
        results = self._make_results()
        report = generate_qa_report(results, Path("output/test.twb"))
        assert "empty_dashboard" in report
