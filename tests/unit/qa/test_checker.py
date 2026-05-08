"""Unit tests for StaticQAChecker.

Tests the 5 static QA checks and sandbox smoke test stub:
- duplicate worksheet names
- unused datasources
- empty dashboards
- orphaned calculations
- missing workbook name
- sandbox smoke test (skip stub)
"""

from pathlib import Path

import pytest

from tableau_agent_toolkit.qa.checker import StaticQAChecker
from tableau_agent_toolkit.qa.report import CheckStatus

# Path to fixtures
FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


class TestDuplicateWorksheetNames:
    """Tests for check_duplicate_worksheet_names."""

    def test_pass_when_all_names_unique(self, tmp_path: Path) -> None:
        """Test 1: PASS when all worksheet names are unique (valid_full.twb)."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_duplicate_worksheet_names(twb_path)
        assert result.status == CheckStatus.PASS
        assert "unique" in result.message.lower()

    def test_fail_when_duplicate_names(self, tmp_path: Path) -> None:
        """Test 2: FAIL when duplicate names exist."""
        twb_content = """<?xml version='1.0' encoding='utf-8'?>
<workbook name='DupTest' version='26.1'>
  <worksheets>
    <worksheet name='Sheet1' />
    <worksheet name='Sheet1' />
    <worksheet name='Sheet2' />
  </worksheets>
</workbook>"""
        twb_path = tmp_path / "duplicates.twb"
        twb_path.write_text(twb_content, encoding="utf-8")

        checker = StaticQAChecker()
        result = checker.check_duplicate_worksheet_names(twb_path)
        assert result.status == CheckStatus.FAIL
        assert "Sheet1" in result.details
        assert "duplicate" in result.message.lower()


class TestUnusedDatasources:
    """Tests for check_unused_datasources."""

    def test_pass_when_all_datasources_used(self, tmp_path: Path) -> None:
        """Test 3: PASS when all datasources are referenced."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_unused_datasources(twb_path)
        assert result.status == CheckStatus.PASS

    def test_warn_when_unused_datasource(self, tmp_path: Path) -> None:
        """Test 4: WARN when a datasource is not referenced by any worksheet."""
        twb_content = """<?xml version='1.0' encoding='utf-8'?>
<workbook name='UnusedDsTest' version='26.1'>
  <datasources>
    <datasource caption='UsedDS' inline='true' name='UsedDS' version='26.1'>
      <column name='Amount' datatype='float' />
    </datasource>
    <datasource caption='OrphanDS' inline='true' name='OrphanDS' version='26.1'>
      <column name='Value' datatype='float' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sheet1'>
      <table>
        <view>
          <datasources>
            <datasource name='UsedDS' />
          </datasources>
        </view>
      </table>
    </worksheet>
  </worksheets>
</workbook>"""
        twb_path = tmp_path / "unused_ds.twb"
        twb_path.write_text(twb_content, encoding="utf-8")

        checker = StaticQAChecker()
        result = checker.check_unused_datasources(twb_path)
        assert result.status == CheckStatus.WARN
        assert "OrphanDS" in result.details

    def test_skip_parameters_datasource(self, tmp_path: Path) -> None:
        """Parameters datasource should be excluded from unused checks."""
        twb_path = FIXTURES_DIR / "minimal_template.twb"
        checker = StaticQAChecker()
        result = checker.check_unused_datasources(twb_path)
        # Parameters DS should be skipped, so result should be PASS
        assert result.status == CheckStatus.PASS


class TestEmptyDashboards:
    """Tests for check_empty_dashboards."""

    def test_pass_when_dashboards_have_zones(self, tmp_path: Path) -> None:
        """Test 5: PASS when all dashboards have zones with content."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_empty_dashboards(twb_path)
        assert result.status == CheckStatus.PASS

    def test_fail_when_dashboard_empty(self, tmp_path: Path) -> None:
        """Test 6: FAIL when a dashboard has no zones."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "empty_dashboard.twb"
        result = checker.check_empty_dashboards(twb_path)
        assert result.status == CheckStatus.FAIL
        assert "EmptyDash" in result.details


class TestOrphanedCalculations:
    """Tests for check_orphaned_calculations."""

    def test_pass_when_all_calculations_referenced(self, tmp_path: Path) -> None:
        """Test 7: PASS when all calculations are referenced."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_orphaned_calculations(twb_path)
        assert result.status == CheckStatus.PASS

    def test_warn_when_orphaned_calculation(self, tmp_path: Path) -> None:
        """Test 8: WARN when a calculation column is not referenced anywhere."""
        twb_content = """<?xml version='1.0' encoding='utf-8'?>
<workbook name='OrphanCalcTest' version='26.1'>
  <datasources>
    <datasource caption='Data' inline='true' name='Data' version='26.1'>
      <column name='Amount' datatype='float' />
      <column name='UnusedCalc' datatype='real'>
        <calculation formula='[Amount] * 2' class='tableau' />
      </column>
      <column name='UsedCalc' datatype='real'>
        <calculation formula='[Amount] + 1' class='tableau' />
      </column>
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sheet1' />
  </worksheets>
  <dashboards>
    <dashboard name='Dash1'>
      <zones>
        <zone name='UsedCalc zone' />
      </zones>
    </dashboard>
  </dashboards>
</workbook>"""
        twb_path = tmp_path / "orphan_calc.twb"
        twb_path.write_text(twb_content, encoding="utf-8")

        checker = StaticQAChecker()
        result = checker.check_orphaned_calculations(twb_path)
        assert result.status == CheckStatus.WARN
        assert "UnusedCalc" in result.details


class TestMissingWorkbookName:
    """Tests for check_missing_workbook_name."""

    def test_pass_when_name_present(self, tmp_path: Path) -> None:
        """Test 9: PASS when root element has name attribute."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_missing_workbook_name(twb_path)
        assert result.status == CheckStatus.PASS

    def test_fail_when_name_missing(self, tmp_path: Path) -> None:
        """Test 10: FAIL when root element has no name attribute."""
        twb_content = """<?xml version='1.0' encoding='utf-8'?>
<workbook version='26.1'>
  <worksheets />
</workbook>"""
        twb_path = tmp_path / "no_name.twb"
        twb_path.write_text(twb_content, encoding="utf-8")

        checker = StaticQAChecker()
        result = checker.check_missing_workbook_name(twb_path)
        assert result.status == CheckStatus.FAIL
        assert "missing" in result.message.lower() or "empty" in result.message.lower()


class TestCheckAll:
    """Tests for check_all() orchestration."""

    def test_returns_six_results(self, tmp_path: Path) -> None:
        """Test 11: check_all() returns exactly 6 results (5 static + 1 sandbox)."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        results = checker.check_all(twb_path)
        assert len(results) == 6
        # Verify each has a check name
        names = [r.check_name for r in results]
        assert "duplicate_worksheet_names" in names
        assert "unused_datasources" in names
        assert "empty_dashboards" in names
        assert "orphaned_calculations" in names
        assert "missing_workbook_name" in names
        assert "sandbox_smoke_test" in names


class TestSandboxSmokeTest:
    """Tests for check_sandbox_smoke_test stub."""

    def test_returns_skip_status(self, tmp_path: Path) -> None:
        """Test 12: Sandbox smoke test returns SKIP when no server configured."""
        checker = StaticQAChecker()
        twb_path = FIXTURES_DIR / "valid_full.twb"
        result = checker.check_sandbox_smoke_test(twb_path)
        assert result.status == CheckStatus.SKIP
        assert result.check_name == "sandbox_smoke_test"
