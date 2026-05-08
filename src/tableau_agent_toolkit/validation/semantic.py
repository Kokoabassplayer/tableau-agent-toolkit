"""Semantic validator for Tableau workbook files.

Catches cross-reference errors that XSD validation cannot detect:
- Broken sheet references in dashboard zones
- Broken action target references
- Dangling datasource references on worksheets
- Dangling field references in calculation formulas

Uses secure XML parsing (resolve_entities=False, no_network=True) to
prevent XXE and SSRF attacks (T-02-02 mitigation).
"""

import re
from pathlib import Path

from lxml import etree

from tableau_agent_toolkit.validation.report import (
    SemanticIssue,
    SemanticValidationResult,
    Severity,
)


class SemanticValidator:
    """Validates semantic cross-references in Tableau workbook files.

    Checks that all references within a TWB file resolve to existing
    elements: dashboard zones reference real worksheets/dashboards,
    action sources reference real worksheets, worksheets reference
    real datasources, and calculation formulas reference real columns.
    """

    def validate(self, twb_path: Path) -> SemanticValidationResult:
        """Validate a TWB file for semantic cross-reference errors.

        Args:
            twb_path: Path to the .twb file to validate.

        Returns:
            SemanticValidationResult with valid flag, errors, and warnings.
        """
        errors: list[SemanticIssue] = []
        warnings: list[SemanticIssue] = []

        # Parse with secure parser (T-02-02 mitigation)
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        tree = etree.parse(str(twb_path), parser)
        root = tree.getroot()

        # Collect defined names
        datasources: set[str] = set(root.xpath("//datasource/@name"))
        worksheets: set[str] = set(root.xpath("//worksheet/@name"))
        dashboards: set[str] = set(root.xpath("//dashboard/@name"))

        # Collect all column names (normalized - stripped of brackets)
        all_column_names: set[str] = set()
        for col_name in root.xpath("//column/@name"):
            all_column_names.add(col_name.strip("[]"))

        # Check 1: Broken sheet references in dashboard zones
        for zone in root.xpath("//dashboard/zones/zone[@name]"):
            zone_name = zone.get("name", "")
            if zone_name and zone_name not in worksheets and zone_name not in dashboards:
                errors.append(
                    SemanticIssue(
                        severity=Severity.ERROR,
                        category="broken_sheet_reference",
                        message=f"Dashboard zone '{zone_name}' references undefined worksheet or dashboard",
                        xml_element=zone,
                    )
                )

        # Check 2: Broken action targets
        for source in root.xpath("//action/source[@worksheet]"):
            worksheet_ref = source.get("worksheet", "")
            if worksheet_ref and worksheet_ref not in worksheets:
                errors.append(
                    SemanticIssue(
                        severity=Severity.ERROR,
                        category="broken_action_target",
                        message=f"Action source references undefined worksheet '{worksheet_ref}'",
                        xml_element=source,
                    )
                )

        # Check 3: Dangling datasource references on worksheets
        for ws in root.xpath("//worksheet"):
            ds_ref = ws.get("datasource", "")
            ws_name = ws.get("name", "<unknown>")
            if ds_ref and ds_ref not in datasources:
                warnings.append(
                    SemanticIssue(
                        severity=Severity.WARNING,
                        category="dangling_datasource_ref",
                        message=f"Worksheet '{ws_name}' references undefined datasource '{ds_ref}'",
                        xml_element=ws,
                    )
                )

        # Check 4: Dangling field references in calculations
        for col in root.xpath("//column[calculation]"):
            calc_elem = col.find("calculation")
            if calc_elem is None:
                continue
            formula = calc_elem.get("formula", "")
            calc_name = col.get("name", "<unknown>")

            if not formula:
                continue

            # Extract field references from formula: [FieldName]
            field_refs = re.findall(r"\[([^\]]+)\]", formula)
            for field_name in field_refs:
                # Normalize: strip brackets for comparison
                normalized = field_name.strip("[]")
                if normalized not in all_column_names:
                    warnings.append(
                        SemanticIssue(
                            severity=Severity.WARNING,
                            category="dangling_field_reference",
                            message=f"Calculation '{calc_name}' references undefined field '{field_name}'",
                            xml_element=col,
                        )
                    )

        return SemanticValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
