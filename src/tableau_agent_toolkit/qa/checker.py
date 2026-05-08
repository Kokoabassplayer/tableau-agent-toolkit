"""Static QA checker for Tableau workbook files.

Runs multiple independent quality checks on validated TWB files,
catching issues that go beyond structural/XSD validation:
- Duplicate worksheet names
- Unused datasources
- Empty dashboards
- Orphaned calculations
- Missing workbook name
- Sandbox smoke test (stub)
"""

from collections import Counter
from pathlib import Path

from lxml import etree

from tableau_agent_toolkit.qa.report import CheckStatus, QACheckResult

# Secure XML parser configuration (T-02-06 mitigation)
_SECURE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True)


class StaticQAChecker:
    """Runs static QA checks on a Tableau workbook file.

    Each check method returns a QACheckResult with status PASS, FAIL, WARN,
    or SKIP. Use check_all() to run every check and collect results.
    """

    def _parse(self, twb_path: Path) -> etree._ElementTree:
        """Parse a TWB file with the secure parser.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            Parsed element tree.
        """
        return etree.parse(str(twb_path), _SECURE_PARSER)

    def check_all(self, twb_path: Path) -> list[QACheckResult]:
        """Run all QA checks on a TWB file.

        Args:
            twb_path: Path to the .twb file to check.

        Returns:
            List of 6 QACheckResult items (5 static + 1 sandbox stub).
        """
        return [
            self.check_duplicate_worksheet_names(twb_path),
            self.check_unused_datasources(twb_path),
            self.check_empty_dashboards(twb_path),
            self.check_orphaned_calculations(twb_path),
            self.check_missing_workbook_name(twb_path),
            self.check_sandbox_smoke_test(twb_path),
        ]

    def check_duplicate_worksheet_names(self, twb_path: Path) -> QACheckResult:
        """Check for duplicate worksheet names in the workbook.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            PASS if all names unique, FAIL with duplicates listed otherwise.
        """
        tree = self._parse(twb_path)
        root = tree.getroot()
        names = root.xpath("//worksheet/@name")

        counts = Counter(names)
        duplicates = [name for name, count in counts.items() if count > 1]

        if duplicates:
            return QACheckResult(
                check_name="duplicate_worksheet_names",
                status=CheckStatus.FAIL,
                message=f"Found duplicate worksheet names: {', '.join(duplicates)}",
                details=duplicates,
            )
        return QACheckResult(
            check_name="duplicate_worksheet_names",
            status=CheckStatus.PASS,
            message="All worksheet names are unique",
        )

    def check_unused_datasources(self, twb_path: Path) -> QACheckResult:
        """Check for datasources that are not referenced by any worksheet or action.

        Skips the built-in 'Parameters' datasource.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            PASS if all datasources are used, WARN with unused names otherwise.
        """
        tree = self._parse(twb_path)
        root = tree.getroot()

        # Collect all datasource names, skip Parameters
        all_ds = root.xpath("//datasource/@name")
        ds_names = {str(n) for n in all_ds if str(n) != "Parameters"}

        if not ds_names:
            return QACheckResult(
                check_name="unused_datasources",
                status=CheckStatus.PASS,
                message="No datasources found to check",
            )

        # Collect explicit datasource references via XPath from:
        # - Worksheet view/datasource elements
        # - Worksheet table datasource references
        # - Action source datasources
        # - Zone datasource references
        referenced: set[str] = set()
        for xpath_expr in [
            "//worksheet//datasource/@name",
            "//action/source/@datasource",
            "//action/@datasource",
            "//zone/@datasource",
        ]:
            for ref in root.xpath(xpath_expr):
                referenced.add(str(ref))

        # For datasources not found via XPath, check if the name appears
        # anywhere outside the <datasources> block (implicit usage).
        # This handles minimal TWB fixtures where worksheets exist but
        # don't have explicit nested datasource references.
        datasources_element = root.find("datasources")
        ds_block_text = (
            etree.tostring(datasources_element, encoding="unicode")
            if datasources_element is not None
            else ""
        )

        unused: list[str] = []
        for ds_name in sorted(ds_names):
            if ds_name in referenced:
                continue
            # Check if the name appears somewhere outside the <datasources> block
            full_text = etree.tostring(root, encoding="unicode")
            # Remove the <datasources> block text, then search
            remaining_text = full_text.replace(ds_block_text, "", 1)
            if ds_name not in remaining_text:
                unused.append(ds_name)

        if unused:
            return QACheckResult(
                check_name="unused_datasources",
                status=CheckStatus.WARN,
                message=f"Unused datasources: {', '.join(unused)}",
                details=unused,
            )
        return QACheckResult(
            check_name="unused_datasources",
            status=CheckStatus.PASS,
            message="All datasources are referenced",
        )

    def check_empty_dashboards(self, twb_path: Path) -> QACheckResult:
        """Check for dashboards with no zones or empty zones element.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            PASS if all dashboards have content, FAIL with empty names otherwise.
        """
        tree = self._parse(twb_path)
        root = tree.getroot()

        dashboards = root.xpath("//dashboard")
        empty_names: list[str] = []

        for dashboard in dashboards:
            name = dashboard.get("name", "unnamed")
            zones = dashboard.find("zones")
            if zones is None:
                empty_names.append(name)
            else:
                zone_children = zones.findall("zone")
                if len(zone_children) == 0:
                    empty_names.append(name)

        if empty_names:
            return QACheckResult(
                check_name="empty_dashboards",
                status=CheckStatus.FAIL,
                message=f"Empty dashboards: {', '.join(empty_names)}",
                details=empty_names,
            )
        return QACheckResult(
            check_name="empty_dashboards",
            status=CheckStatus.PASS,
            message="All dashboards have content",
        )

    def check_orphaned_calculations(self, twb_path: Path) -> QACheckResult:
        """Check for calculation columns not referenced anywhere in the workbook.

        Uses simple string search for reference detection -- does not parse
        Tableau formula syntax.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            PASS if all calculations are referenced, WARN with orphaned names.
        """
        tree = self._parse(twb_path)
        root = tree.getroot()

        # Find all columns that have a calculation child
        calc_columns = root.xpath("//column[calculation]")
        if not calc_columns:
            return QACheckResult(
                check_name="orphaned_calculations",
                status=CheckStatus.PASS,
                message="No calculations found to check",
            )

        calc_names: list[str] = []
        for col in calc_columns:
            name = col.get("name")
            if name:
                calc_names.append(name)

        if not calc_names:
            return QACheckResult(
                check_name="orphaned_calculations",
                status=CheckStatus.PASS,
                message="No calculations found to check",
            )

        # Collect all text content and attribute values as searchable text
        # Build a body of all XML text that could reference a calculation
        xml_bytes = etree.tostring(root, encoding="unicode")

        orphaned: list[str] = []
        for name in calc_names:
            # Simple string search: check if the calculation name appears
            # anywhere in the full XML text beyond its own definition
            # Count occurrences -- must appear at least twice (definition + reference)
            count = xml_bytes.count(name)
            if count <= 1:
                orphaned.append(name)

        if orphaned:
            return QACheckResult(
                check_name="orphaned_calculations",
                status=CheckStatus.WARN,
                message=f"Orphaned calculations: {', '.join(orphaned)}",
                details=orphaned,
            )
        return QACheckResult(
            check_name="orphaned_calculations",
            status=CheckStatus.PASS,
            message="All calculations are referenced",
        )

    def check_missing_workbook_name(self, twb_path: Path) -> QACheckResult:
        """Check if the workbook root element has a non-empty name attribute.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            PASS if name exists and is non-empty, FAIL otherwise.
        """
        tree = self._parse(twb_path)
        root = tree.getroot()

        name = root.get("name")

        if not name or not name.strip():
            return QACheckResult(
                check_name="missing_workbook_name",
                status=CheckStatus.FAIL,
                message="Workbook name attribute is missing or empty",
            )
        return QACheckResult(
            check_name="missing_workbook_name",
            status=CheckStatus.PASS,
            message=f"Workbook name: {name}",
        )

    def check_sandbox_smoke_test(self, twb_path: Path) -> QACheckResult:
        """Stub for sandbox publish smoke test.

        Full implementation requires tableauserverclient + server configuration.
        Always returns SKIP status when no server is configured.

        Args:
            twb_path: Path to the .twb file.

        Returns:
            SKIP status with explanation.
        """
        return QACheckResult(
            check_name="sandbox_smoke_test",
            status=CheckStatus.SKIP,
            message="Sandbox smoke test requires live Tableau Server/Cloud configuration",
            details=[],
        )
