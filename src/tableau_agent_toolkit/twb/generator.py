"""TWB workbook generator using lxml-based XML patching of template workbooks.

Loads a known-good .twb template and patches specific elements (workbook name,
datasources, calculations, worksheets, dashboards) to produce deterministic output.
The same spec + template + version always produces byte-identical .twb files.
"""

from dataclasses import dataclass, field
from pathlib import Path

from lxml import etree

from tableau_agent_toolkit.spec.models import DashboardSpec
from tableau_agent_toolkit.templates.registry import TemplateRegistry
from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version


@dataclass
class GenerationResult:
    """Result of a workbook generation operation.

    Attributes:
        output_path: Path to the generated .twb file.
        warnings: Non-fatal warnings encountered during generation.
    """

    output_path: Path
    warnings: list[str] = field(default_factory=list)


class WorkbookGenerator:
    """Generates Tableau workbooks by patching template .twb files.

    Uses a template-first approach: loads a known-good template, applies XML
    patches for each spec section, and writes deterministic output. The same
    inputs always produce byte-identical output.

    Args:
        template_registry: Registry for resolving template IDs to file paths.
    """

    def __init__(self, template_registry: TemplateRegistry) -> None:
        self._template_registry = template_registry

    def generate(
        self,
        spec: DashboardSpec,
        output_path: Path,
        template_override: Path | None = None,
    ) -> GenerationResult:
        """Generate a .twb workbook from a spec and template.

        Args:
            spec: The dashboard specification to generate from.
            output_path: Where to write the generated .twb file.
            template_override: Optional direct path to a template file.
                If provided, bypasses the template registry.

        Returns:
            GenerationResult with the output path and any warnings.
        """
        # Resolve template path
        if template_override is not None:
            template_path = template_override
        else:
            match = self._template_registry.resolve(
                spec.workbook.template.id,
                spec.workbook.target_tableau_version,
            )
            template_path = match.path

        # Parse template with secure parser (T-01-06 mitigation)
        parser = etree.XMLParser(
            remove_blank_text=True,
            resolve_entities=False,
            no_network=True,
        )
        tree = etree.parse(str(template_path), parser)

        # Apply version manifest
        apply_manifest_by_version(tree, spec.workbook.target_tableau_version)

        # Apply all patch operations
        self._patch_workbook_name(tree, spec.workbook.name)
        self._patch_datasources(tree, spec)
        self._patch_calculations(tree, spec)
        self._patch_worksheets(tree, spec)
        self._patch_dashboards(tree, spec)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write output
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)

        return GenerationResult(output_path=output_path, warnings=[])

    def _patch_workbook_name(self, tree: etree._ElementTree, name: str) -> None:
        """Set the workbook name attribute on the root element.

        Also ensures a <preferences> element exists with the workbook-tabs setting.

        Args:
            tree: The workbook XML tree to modify.
            name: The workbook name to set.
        """
        root = tree.getroot()
        root.attrib["name"] = name

        # Find or create <preferences> element
        preferences = root.find("preferences")
        if preferences is None:
            preferences = etree.SubElement(root, "preferences")

        # Set workbook-tabs preference
        tab_pref = preferences.find("preference[@name='ui.show-workbook-tabs']")
        if tab_pref is None:
            tab_pref = etree.SubElement(preferences, "preference")
            tab_pref.attrib["name"] = "ui.show-workbook-tabs"
        tab_pref.attrib["value"] = "true"

    def _patch_datasources(self, tree: etree._ElementTree, spec: DashboardSpec) -> None:
        """Add datasource elements from the spec to the workbook XML.

        Finds or creates the <datasources> container and adds a <datasource>
        element for each entry in the spec.

        Args:
            tree: The workbook XML tree to modify.
            spec: The dashboard specification containing datasource definitions.
        """
        root = tree.getroot()

        # Find or create <datasources>
        datasources_el = root.find("datasources")
        if datasources_el is None:
            datasources_el = etree.SubElement(root, "datasources")

        for ds in spec.datasources:
            ds_el = etree.SubElement(datasources_el, "datasource")
            ds_el.attrib["name"] = ds.name
            ds_el.attrib["caption"] = ds.name
            ds_el.attrib["inline"] = "true"

            # For custom-sql mode, add a <connection> element with reference
            if ds.mode == "custom-sql":
                conn_el = etree.SubElement(ds_el, "connection")
                conn_el.attrib["class"] = "genericodbc"
                if ds.custom_sql_file:
                    conn_el.attrib["custom_sql_file"] = ds.custom_sql_file

    def _patch_calculations(
        self, tree: etree._ElementTree, spec: DashboardSpec
    ) -> None:
        """Add calculated field elements from the spec to the workbook XML.

        For each calculation, adds a <column> element with a <calculation> child
        to the first datasource found in the XML.

        Args:
            tree: The workbook XML tree to modify.
            spec: The dashboard specification containing calculation definitions.
        """
        if not spec.calculations:
            return

        root = tree.getroot()

        # Find or create <datasources> and target the first datasource
        datasources_el = root.find("datasources")
        if datasources_el is None:
            datasources_el = etree.SubElement(root, "datasources")

        target_ds = datasources_el.find("datasource")
        if target_ds is None:
            target_ds = etree.SubElement(datasources_el, "datasource")
            target_ds.attrib["name"] = "federated"
            target_ds.attrib["inline"] = "true"

        for calc in spec.calculations:
            col_el = etree.SubElement(target_ds, "column")
            col_el.attrib["datatype"] = "string"
            col_el.attrib["name"] = calc.name
            col_el.attrib["role"] = "measure"

            calc_el = etree.SubElement(col_el, "calculation")
            calc_el.attrib["formula"] = calc.formula

    def _patch_worksheets(self, tree: etree._ElementTree, spec: DashboardSpec) -> None:
        """Add worksheet elements from the spec to the workbook XML.

        Finds or creates the <worksheets> container and adds a <worksheet>
        element for each entry in the spec.

        Args:
            tree: The workbook XML tree to modify.
            spec: The dashboard specification containing worksheet definitions.
        """
        root = tree.getroot()

        # Find or create <worksheets>
        worksheets_el = root.find("worksheets")
        if worksheets_el is None:
            worksheets_el = etree.SubElement(root, "worksheets")

        for ws in spec.worksheets:
            ws_el = etree.SubElement(worksheets_el, "worksheet")
            ws_el.attrib["name"] = ws.name

    def _patch_dashboards(self, tree: etree._ElementTree, spec: DashboardSpec) -> None:
        """Add dashboard elements from the spec to the workbook XML.

        Finds or creates the <dashboards> container and adds a <dashboard>
        element with a basic <zones> child for each entry in the spec.

        Args:
            tree: The workbook XML tree to modify.
            spec: The dashboard specification containing dashboard definitions.
        """
        root = tree.getroot()

        # Find or create <dashboards>
        dashboards_el = root.find("dashboards")
        if dashboards_el is None:
            dashboards_el = etree.SubElement(root, "dashboards")

        for db in spec.dashboards:
            db_el = etree.SubElement(dashboards_el, "dashboard")
            db_el.attrib["name"] = db["name"]

            # Add basic <zones> child
            zones_el = etree.SubElement(db_el, "zones")
