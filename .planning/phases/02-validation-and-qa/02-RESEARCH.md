# Phase 2: Validation and QA - Research

**Researched:** 2026-05-08
**Domain:** TWB semantic validation (cross-reference integrity), static QA checks, markdown report generation, XSD schema vendoring
**Confidence:** HIGH

## Summary

Phase 2 adds the validation layer that makes workbook output trustworthy. Phase 1 already provides XSD validation (syntactic only), so this phase focuses on **semantic validation** -- checking cross-references between TWB XML elements that XSD cannot verify -- and **static QA checks** that produce actionable reports.

The official `tableau-document-schemas` README explicitly states that XSD validation is syntactic only and lists things it cannot verify: "attributes in connection elements, calculated field contents like function names and object references, references to other named workbook contents like tab names" [VERIFIED: github.com/tableau/tableau-document-schemas README]. These are exactly the checks Phase 2 must implement.

The core technical challenge is implementing cross-reference integrity checks using lxml XPath queries over the TWB XML tree. The semantic validator must collect "defined names" (datasources, worksheets, dashboards, calculations, parameters) and then verify every "reference" to those names resolves correctly. This is a graph-consistency problem, not a parsing problem. No new external dependencies are needed -- lxml XPath provides all the querying capability required.

**Primary recommendation:** Build the semantic validator as a class parallel to the existing `XsdValidator`, using lxml XPath to extract defined names and then verifying all cross-references. Build the QA checker as a separate class that runs multiple independent checks and collects results into a structured report. Both integrate into the existing Typer CLI via new commands.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | XSD validation against pinned tableau-document-schemas with clear error output | Already implemented in Phase 1 (`validation/xsd.py`). Phase 2 may need minor enhancements (e.g., passing the spec file path for error mapping) but the core is done. |
| VAL-02 | Semantic validation for sheet references, calculation names, action targets, and field references | lxml XPath verified for all needed queries: `//datasource/@name`, `//worksheet/@name`, `//dashboard/@name`, `//zone/@name`, `//column/calculation/@formula`, `//action/source/@worksheet`. Cross-reference pattern: collect defined names, then verify each reference resolves. |
| VAL-03 | Validation report with errors first, then warnings, then remediation steps | Use dataclass hierarchy (SemanticError, SemanticWarning) with severity levels. Sort by severity in report. Generate markdown output. |
| VAL-04 | XSD schemas vendored in `third_party/` with sync script | Sync script already exists (`scripts/sync_tableau_schemas.py`). The third_party directory has a README but schemas have not been downloaded yet. Phase 2 must ensure the sync script runs successfully and the real XSD is in place. |
| QA-01 | Static QA checks on validated workbooks | Checks include: duplicate worksheet names, unused datasources, missing workbook name, empty dashboards, orphaned calculations. Each check is an independent function returning pass/fail/result. |
| QA-02 | Optional sandbox publish smoke test | Requires live Tableau Server/Cloud infrastructure. Implement as optional CLI flag with graceful skip when server is unavailable. Dependency on tableauserverclient (already in stack). |
| QA-03 | QA report in markdown with pass/fail per check | Markdown generation from structured data. Template: check name, status (PASS/FAIL/WARN), details, remediation steps. |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lxml | 6.1.0 | XPath queries for semantic validation of TWB XML | [VERIFIED: pip show lxml] Already in project. XPath is the natural way to extract cross-references from TWB XML. |
| Pydantic | 2.13.4 | Validation result models, report structures | [VERIFIED: pip show pydantic] Already in project. Use for typed validation result dataclasses. |
| Typer | 0.25.1 | CLI commands for validate-semantic and qa static | [VERIFIED: pip show typer] Already in project. Add new commands to existing app. |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pytest | 9.0.3 | Unit and integration tests for validators | [VERIFIED: pip show pytest] Already in project. |
| tableauserverclient | 0.40+ | Sandbox publish smoke test (QA-02) | Only needed for QA-02. Optional dependency -- import only when sandbox test is requested. |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lxml XPath for cross-references | Custom XML walking | XPath is declarative, battle-tested, and faster. Custom walking is error-prone with namespaces. |
| Dataclass validation results | Pydantic models | Both work; dataclasses are lighter for internal results. Pydantic better for public API types. Use dataclasses to match existing `XsdError`/`XsdValidationResult` pattern from Phase 1. |
| Markdown report via string templates | Jinja2 / rich | No new dependency needed. String templates with f-strings are sufficient for markdown report generation. |

**Installation:**
No new dependencies needed for this phase. All libraries are already installed from Phase 1.

For QA-02 (sandbox smoke test), tableauserverclient is listed in the project stack but not yet installed:
```bash
pip install tableauserverclient>=0.40
```
This is optional and only needed when sandbox testing is enabled.

**Version verification (completed 2026-05-08):**
- lxml: 6.1.0 (installed) [VERIFIED: pip show]
- pydantic: 2.13.4 (installed) [VERIFIED: pip show]
- typer: 0.25.1 (installed) [VERIFIED: pip show]
- pytest: 9.0.3 (installed) [VERIFIED: pip show]

## Architecture Patterns

### Recommended Project Structure (Phase 2 additions)

```
src/tableau_agent_toolkit/
  validation/
    __init__.py          # UPDATE: export new validators
    xsd.py               # EXISTS: no changes needed (or minor enhancements)
    semantic.py          # NEW: SemanticValidator class
    report.py            # NEW: ValidationReport, SemanticError, SemanticWarning
  qa/
    __init__.py          # NEW: QA module init
    checker.py           # NEW: StaticQAChecker class
    report.py            # NEW: QAReport, QACheckResult
  cli.py                 # UPDATE: add validate-semantic and qa static commands

tests/
  unit/
    validation/
      test_xsd.py        # EXISTS
      test_semantic.py   # NEW: semantic validator tests
      test_report.py     # NEW: validation report tests
    qa/
      test_checker.py    # NEW: static QA checker tests
      test_report.py     # NEW: QA report tests
  integration/
    test_cli.py          # UPDATE: add new CLI command tests
  fixtures/
    # NEW fixtures needed:
    broken_references.twb     # TWB with broken sheet/datasource refs
    missing_calculation.twb   # TWB referencing non-existent calc
    empty_dashboard.twb       # TWB with empty dashboard zones
    valid_full.twb            # TWB with all valid cross-references
```

### Pattern 1: Semantic Validator (Cross-Reference Integrity)

**What:** A class that loads a TWB XML tree, collects all defined names (datasources, worksheets, dashboards, calculations), then walks the tree checking every cross-reference resolves.

**When to use:** For every generated TWB before packaging or publishing.

**Example:**
```python
# Source: [VERIFIED: lxml XPath testing] + TWB XSD analysis
from dataclasses import dataclass, field
from pathlib import Path
from lxml import etree
from tableau_agent_toolkit.validation.report import SemanticIssue, Severity

@dataclass
class SemanticValidationResult:
    valid: bool
    errors: list[SemanticIssue] = field(default_factory=list)
    warnings: list[SemanticIssue] = field(default_factory=list)

class SemanticValidator:
    """Validates TWB cross-references that XSD cannot check."""

    def validate(self, twb_path: Path) -> SemanticValidationResult:
        parser = etree.XMLParser(resolve_entities=False, no_network=True)
        tree = etree.parse(str(twb_path), parser)
        root = tree.getroot()

        errors: list[SemanticIssue] = []
        warnings: list[SemanticIssue] = []

        # Collect defined names
        datasources = set(root.xpath("//datasource/@name"))
        worksheets = set(root.xpath("//worksheet/@name"))
        dashboards = set(root.xpath("//dashboard/@name"))
        calculations = set(root.xpath("//column/calculation/.."))
        calc_names = {col.get("name") for col in calculations}

        # Check 1: Dashboard zone references resolve to worksheets
        for zone in root.xpath("//dashboard/zones/zone[@name]"):
            zone_name = zone.get("name")
            if zone_name and zone_name not in worksheets:
                errors.append(SemanticIssue(
                    severity=Severity.ERROR,
                    category="broken_sheet_reference",
                    message=f"Dashboard zone '{zone_name}' references undefined worksheet",
                    element=zone,
                ))

        # Check 2: Action source references resolve
        for source in root.xpath("//action/source[@worksheet]"):
            ws_name = source.get("worksheet")
            if ws_name and ws_name not in worksheets:
                errors.append(SemanticIssue(
                    severity=Severity.ERROR,
                    category="broken_action_target",
                    message=f"Action source references undefined worksheet '{ws_name}'",
                    element=source,
                ))

        # Check 3: Worksheet datasource references resolve
        for ws in root.xpath("//worksheet"):
            ds_ref = ws.get("datasource")
            if ds_ref and ds_ref not in datasources:
                warnings.append(SemanticIssue(
                    severity=Severity.WARNING,
                    category="dangling_datasource_ref",
                    message=f"Worksheet '{ws.get('name')}' references undefined datasource '{ds_ref}'",
                    element=ws,
                ))

        return SemanticValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )
```

### Pattern 2: Spec-to-XML Error Mapping

**What:** When the semantic validator finds an error in the generated TWB, map it back to the originating spec line by correlating element names with spec model fields.

**When to use:** For every validation error message.

**Example:**
```python
# Source: [ASSUMED] -- design pattern for spec-line mapping
def map_to_spec_line(
    issue: SemanticIssue,
    spec: DashboardSpec,
) -> str | None:
    """Map a TWB validation issue back to the originating spec section.

    Returns a string like "dashboard_spec.yaml:42" or None if no mapping found.
    """
    # Strategy: match element names from XML to spec model field names
    # e.g., worksheet name "SalesMap" -> find it in spec.worksheets
    # The spec YAML was the input, so the spec model has the original definitions
    name = issue.element.get("name", "")
    category = issue.category

    if category == "broken_sheet_reference":
        # The zone name should match a worksheet name in the spec
        for i, ws in enumerate(spec.worksheets):
            if ws.name == name:
                # Approximate: spec YAML doesn't store line numbers,
                # but we can reference the spec section
                return f"worksheets[{i}].name: '{name}'"
    return None
```

**Note on SPEC-04 (spec line mapping):** The requirements say "Error messages map XML failures back to spec line numbers (e.g., 'dashboard_spec.yaml line 42')". Since PyYAML does not preserve line numbers by default, the practical approach is to map errors to spec *sections* (e.g., `worksheets[2].datasource: 'SalesMap'`) rather than exact line numbers. If exact line numbers are needed, the spec parser would need to use `ruamel.yaml` or a custom YAML loader that preserves line numbers. [ASSUMED]

### Pattern 3: Static QA Checker (Independent Checks)

**What:** A class that runs multiple independent QA checks on a validated TWB and collects results.

**When to use:** After validation passes (both XSD and semantic).

**Example:**
```python
# Source: [ASSUMED] -- design pattern for composable QA checks
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from lxml import etree

class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"

@dataclass
class QACheckResult:
    check_name: str
    status: CheckStatus
    message: str
    details: list[str]

class StaticQAChecker:
    """Runs static QA checks on a validated TWB workbook."""

    def check_all(self, twb_path: Path) -> list[QACheckResult]:
        return [
            self.check_duplicate_worksheet_names(twb_path),
            self.check_unused_datasources(twb_path),
            self.check_empty_dashboards(twb_path),
            self.check_orphaned_calculations(twb_path),
            self.check_missing_workbook_name(twb_path),
        ]

    def check_duplicate_worksheet_names(self, twb_path: Path) -> QACheckResult:
        tree = etree.parse(str(twb_path))
        names = tree.xpath("//worksheet/@name")
        seen: set[str] = set()
        duplicates: list[str] = []
        for name in names:
            if name in seen:
                duplicates.append(name)
            seen.add(name)
        if duplicates:
            return QACheckResult(
                check_name="duplicate_worksheet_names",
                status=CheckStatus.FAIL,
                message=f"Found duplicate worksheet names: {duplicates}",
                details=duplicates,
            )
        return QACheckResult(
            check_name="duplicate_worksheet_names",
            status=CheckStatus.PASS,
            message="All worksheet names are unique",
            details=[],
        )
```

### Pattern 4: Markdown Report Generation

**What:** Generate structured markdown reports from validation/QA results.

**When to use:** For the `qa static` command output.

**Example:**
```python
# Source: [ASSUMED] -- standard markdown report pattern
def generate_qa_report(results: list[QACheckResult], twb_path: Path) -> str:
    """Generate a markdown QA report."""
    lines: list[str] = []
    lines.append(f"# QA Report: {twb_path.name}")
    lines.append("")

    # Summary
    failed = [r for r in results if r.status == CheckStatus.FAIL]
    warned = [r for r in results if r.status == CheckStatus.WARN]
    passed = [r for r in results if r.status == CheckStatus.PASS]
    lines.append(f"**Summary:** {len(passed)} passed, {len(warned)} warnings, {len(failed)} failed")
    lines.append("")

    # Errors first
    if failed:
        lines.append("## Errors")
        for r in failed:
            lines.append(f"- **{r.check_name}**: {r.message}")
            for d in r.details:
                lines.append(f"  - {d}")
            lines.append(f"  - Remediation: Fix the identified issue and re-validate.")
        lines.append("")

    # Warnings
    if warned:
        lines.append("## Warnings")
        for r in warned:
            lines.append(f"- **{r.check_name}**: {r.message}")
        lines.append("")

    # Passed
    lines.append("## Passed Checks")
    for r in passed:
        lines.append(f"- {r.check_name}")
    lines.append("")

    return "\n".join(lines)
```

### Pattern 5: Typer CLI Command Registration

**What:** Add `validate-semantic` and `qa static` commands to the existing Typer app.

**When to use:** For the new CLI commands.

**Example:**
```python
# Source: [VERIFIED: existing cli.py pattern] + Typer docs
# In cli.py, add to the existing app:

@app.command("validate-semantic")
def validate_semantic(
    twb_path: Path = typer.Argument(..., help="Path to .twb file", exists=True),
    spec_path: Path | None = typer.Option(
        None, "--spec", help="Path to original spec for error mapping"
    ),
) -> None:
    """Validate TWB cross-references (sheet refs, calc names, action targets)."""
    validator = SemanticValidator()
    result = validator.validate(twb_path)
    if result.valid:
        typer.echo(f"Valid: {twb_path} passes semantic validation")
    else:
        typer.echo(f"Invalid: {twb_path} failed semantic validation", err=True)
        for err in result.errors:
            typer.echo(f"  ERROR: {err.message}", err=True)
        for warn in result.warnings:
            typer.echo(f"  WARNING: {warn.message}", err=True)
        sys.exit(1)


qa_app = typer.Typer(help="QA operations")
app.add_typer(qa_app, name="qa")

@qa_app.command("static")
def qa_static(
    twb_path: Path = typer.Argument(..., help="Path to .twb file", exists=True),
    output: Path | None = typer.Option(
        None, "--output", "-o", help="Output markdown report path"
    ),
) -> None:
    """Run static QA checks and generate report."""
    checker = StaticQAChecker()
    results = checker.check_all(twb_path)
    report = generate_qa_report(results, twb_path)
    if output:
        output.write_text(report, encoding="utf-8")
        typer.echo(f"QA report written to {output}")
    else:
        typer.echo(report)
```

### Anti-Patterns to Avoid

- **Parsing calculation formulas as Tableau expressions:** The calc language is proprietary. Only check that referenced field names exist, not that the formula syntax is valid. [CITED: REQUIREMENTS.md "Out of Scope" section]
- **Re-implementing XSD validation:** XSD validation is already done. The semantic validator must not duplicate structural checks. Focus only on cross-reference integrity.
- **Tight coupling to spec model in validator:** The semantic validator should work on TWB XML directly (lxml tree), not require the spec model. Spec-to-XML mapping is a separate concern.
- **Single monolithic validator class:** Separate checks into distinct methods or functions for independent testability. Each check should be runnable independently.
- **Requiring live server for all QA:** QA-02 (sandbox smoke test) is optional. The static QA checker must work completely offline.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| XML cross-reference extraction | Manual tree walking | lxml XPath (`//datasource/@name`, `//worksheet/@name`) | XPath is declarative, handles namespaces, and is battle-tested. Manual walking with lxml's Python API is verbose and error-prone with namespace handling. |
| Validation result types | Dict-based results | Dataclasses (matching Phase 1 pattern: `XsdError`, `XsdValidationResult`) | Consistency with existing code. Type safety. Clear error/warning separation. |
| Markdown report | Custom HTML or JSON | Simple string formatting (f-strings + join) | Markdown is plain text. No template engine needed for reports of this complexity. |
| XSD schema download | Custom HTTP client | Existing `scripts/sync_tableau_schemas.py` using `urllib.request` | Already built in Phase 1. Just needs to be run. |
| Duplicate name detection | Custom loop | Python `set()` + comparison | One-liner: `duplicates = [n for n in names if names.count(n) > 1]` or set-based dedup. |

**Key insight:** This phase has zero new external dependencies. Everything is built with lxml, Pydantic/dataclasses, and Typer -- all already in the project. The value is in the cross-reference checking logic, not in tooling.

## Common Pitfalls

### Pitfall 1: XPath Queries Missing Namespaced Elements

**What goes wrong:** lxml XPath queries return empty results for elements with namespace prefixes (e.g., `user:calculation`) because XPath requires namespace mapping.
**Why it happens:** The TWB root element declares `xmlns:user='http://www.tableausoftware.com/xml/user'`. If you query `//calculation` without registering the namespace, lxml will not find elements that use the `user:` prefix.
**How to avoid:** Test all XPath queries against real TWB fixtures. Use `root.xpath("//*")` to discover all element names first. If elements use namespace prefixes, register them with `root.xpath("//user:calculation", namespaces={"user": "http://www.tableausoftware.com/xml/user"})`.
**Warning signs:** XPath query returns empty list for an element you know exists in the XML.
**Phase:** Phase 2 (semantic validator). [VERIFIED: lxml documentation]

### Pitfall 2: Zone Name vs. Zone Type Ambiguity

**What goes wrong:** Dashboard `<zone>` elements have a `name` attribute that may reference a worksheet name, but not all zones do. Some zones are layout containers with no sheet reference.
**Why it happens:** The `name` attribute on `<zone>` is optional (`<xs:attribute name="name" type="xs:string"/>` -- no `use="required"`). Some zones have names that are not worksheet names (e.g., layout zones, blank zones, image zones).
**How to avoid:** Only check zone names that match the pattern of worksheet names. Use the zone `type-v2` attribute or check if the name exists in the worksheets set. Zones without names or with names that don't match any worksheet are layout containers, not sheet references.
**Warning signs:** False positives on zones that are layout containers, not sheet embeds.
**Phase:** Phase 2 (semantic validator). [VERIFIED: XSD analysis -- Zone-G has optional `name` attribute]

### Pitfall 3: QualifiedName Bracket Syntax in Field References

**What goes wrong:** Field references in Tableau calculations use `[Field Name]` syntax, but the `name` attribute on `<column>` uses `QualifiedName-ST` which has a specific pattern: `[\[([^\]]*(\]\])?)*\](\.\[([^\]]*(\]\])?)*\])*` -- bracketed names possibly dot-separated.
**Why it happens:** The formula `SUM([Variance Amount])` references `[Variance Amount]`, but the column's `name` attribute might be `[Variance Amount]` (with brackets) or `Variance Amount` (without). The QualifiedName pattern includes brackets.
**How to avoid:** When checking if a field reference in a formula resolves, strip brackets from the reference and compare against column names with brackets also stripped. Use a normalization function.
**Warning signs:** False negatives on valid calculation references.
**Phase:** Phase 2 (semantic validator). [VERIFIED: XSD QualifiedName-ST pattern]

### Pitfall 4: Real XSD Not Downloaded to third_party

**What goes wrong:** The sync script exists but has never been run, so `third_party/tableau_document_schemas/schemas/` is empty. The XSD validator will fail with `FileNotFoundError` when validating against the real schema.
**Why it happens:** The sync script was built in Phase 1 but only the test fixture XSD exists (in `tests/fixtures/schemas/`), not the real one in `third_party/`.
**How to avoid:** Run `python scripts/sync_tableau_schemas.py` as an early step in Phase 2. Verify the real XSD file exists at `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd`.
**Warning signs:** `FileNotFoundError: Schemas root not found` or `XSD schema not found` errors.
**Phase:** Phase 2 (VAL-04). [VERIFIED: filesystem check -- only README.md exists in third_party]

### Pitfall 5: Spec Line Number Mapping Without YAML Line Preservation

**What goes wrong:** The requirement says "Error messages map XML failures back to spec line numbers (e.g., 'dashboard_spec.yaml line 42')" but PyYAML's `safe_load()` does not preserve line numbers.
**Why it happens:** PyYAML discards source position information during parsing. To get line numbers, you would need `ruamel.yaml` (which preserves round-trip editing metadata) or a custom loader.
**How to avoid:** Map errors to spec *sections* rather than exact lines (e.g., `worksheets[2].datasource: 'SalesMap'`). This is more useful than line numbers because it identifies the exact field. If line numbers are strictly required, add `ruamel.yaml` as a dependency.
**Warning signs:** Cannot provide line-number-based error messages.
**Phase:** Phase 2 (VAL-02, SPEC-04). [ASSUMED]

### Pitfall 6: Sandbox Smoke Test Without Server Access

**What goes wrong:** QA-02 requires connecting to a Tableau Server/Cloud instance, which may not be available in all environments.
**Why it happens:** The smoke test is marked "optional" in the roadmap, but if the code doesn't handle the missing server gracefully, it will crash.
**How to avoid:** The sandbox smoke test must have a `--skip-smoke` flag (or auto-skip when no server config is provided). Never make it a blocking step in the QA pipeline.
**Warning signs:** Any test or command that fails when TABLEAU_SERVER_URL is not set.
**Phase:** Phase 2 (QA-02). [CITED: ROADMAP.md -- "QA-02 stays in Phase 2 despite requiring live infrastructure -- it is optional"]

## Code Examples

### Verified TWB Cross-Reference Points from XSD

The real `twb_2026.1.0.xsd` (297,129 bytes) defines these cross-reference points that XSD cannot validate:

```python
# Source: [VERIFIED: GitHub API fetch of real twb_2026.1.0.xsd]

# 1. Action source references (ActionList-ActionSource-G):
# <source type="sheet" worksheet="SheetName" datasource="DSName" dashboard="DashName" />
# All of worksheet, datasource, dashboard attributes are optional xs:string
# These reference defined names that must exist in the workbook

# 2. Dashboard zone references (Zone-G):
# <zone name="SheetName" x="0" y="0" w="500" h="400" id="1" />
# The name attribute references a worksheet or dashboard name

# 3. Column/calculation references (Column-G + DataSource-Calculation-G):
# <column name="[CalcName]" datatype="string" role="measure">
#   <calculation formula="SUM([Field1]) + [Field2]" class="tableau" />
# </column>
# The formula text contains field references in [brackets] that must resolve

# 4. QualifiedName pattern for field references:
# FullValue-ST pattern: (\[([^\]]*(\]\])?)*\](\.\[([^\]]*(\]\])?)*\])*)
# Example: [Variance Amount] or [Data].[Amount]

# 5. processContents="skip" locations (19 occurrences):
# These are elements/attributes that the XSD explicitly does NOT validate:
# - Connection element attributes (anyAttribute processContents="skip")
# - Layer element attributes
# - Document manifest content
# These are where semantic checks add value beyond XSD
```

### Semantic Validator Test Fixture

```python
# Source: [ASSUMED] -- test fixture design based on XSD analysis
# tests/fixtures/broken_references.twb
TWB_BROKEN_REFS = '''<?xml version='1.0' encoding='utf-8'?>
<workbook version='26.1' original-version='26.1' source-build='0.0.0 (0000.0.0.0.0)' source-platform='win' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest>
    <ManifestByVersion />
  </document-format-change-manifest>
  <datasources>
    <datasource name='Data' inline='true'>
      <column name='Amount' datatype='float' role='measure' type='quantitative' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sheet1' />
  </worksheets>
  <dashboards>
    <dashboard name='Dash1'>
      <zones>
        <zone name='Sheet1' x='0' y='0' w='500' h='400' id='1' />
        <zone name='NonExistentSheet' x='500' y='0' w='500' h='400' id='2' />
      </zones>
    </dashboard>
  </dashboards>
</workbook>'''
# This fixture has a broken reference: zone 'NonExistentSheet' -> undefined worksheet
```

### Existing Phase 1 Patterns to Follow

```python
# Source: [VERIFIED: existing codebase -- validation/xsd.py]
# The existing XsdValidator pattern to follow:
from dataclasses import dataclass, field
from pathlib import Path
from lxml import etree

@dataclass
class XsdError:
    line: int
    column: int
    message: str

@dataclass
class XsdValidationResult:
    valid: bool
    errors: list[XsdError] = field(default_factory=list)

class XsdValidator:
    def __init__(self, schemas_root: Path) -> None:
        self._schemas_root = Path(schemas_root)
        if not self._schemas_root.exists():
            raise FileNotFoundError(f"Schemas root not found: {self._schemas_root}")

    def validate(self, twb_path: Path, tableau_version: str = "2026.1") -> XsdValidationResult:
        # ... validation logic
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No official TWB XSD | Official tableau-document-schemas (Feb 2026) | Feb 2026 | Can now validate TWB structure against an official standard; XSD is syntactic only, semantic checks still needed |
| Manual XML cross-reference checking | lxml XPath-based cross-reference validation | Continuous | XPath provides declarative, efficient querying; no need for custom XML walking |
| Separate black/isort/flake8 | ruff (single tool) | 2023-2024 | Already in project; no change |
| PyYAML safe_load only | ruamel.yaml for line preservation | N/A | Not adopted yet; if exact line numbers are needed, this would be the path forward |

**Deprecated/outdated:**
- Tableau Document API: "As-Is" and unsupported. Do not use for validation. [CITED: CLAUDE.md]
- Manual XML walking without XPath: Use lxml XPath for all element queries.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PyYAML `safe_load()` does not preserve line numbers, so spec-to-line mapping must use section references instead of exact lines | Pattern 2 | Medium -- if line numbers are strictly required, ruamel.yaml would need to be added as a dependency |
| A2 | Dashboard zone `name` attribute that matches a worksheet name is a sheet reference; zones without matching names are layout containers | Pitfall 2 | Medium -- if some zones use names that are not sheet references, there could be false positives |
| A3 | The `tableauserverclient` library can be imported optionally for QA-02 without adding it as a hard dependency | Standard Stack | Low -- Python handles optional imports well |
| A4 | Field references in calculation formulas use `[FieldName]` syntax and can be extracted with a simple regex like `\[([^\]]+)\]` | Pattern 1, Pitfall 3 | Medium -- nested brackets `]]` are allowed per QualifiedName-ST pattern; regex must handle escapes |
| A5 | The real XSD from GitHub will download successfully via the sync script | Pitfall 4 | Low -- the repo is public and officially supported; the sync script was tested in Phase 1 |
| A6 | The sandbox smoke test (QA-02) can be stubbed as a "not yet implemented" or "skipped" check since it requires live infrastructure | QA-02 | Low -- the roadmap says it is optional |

## Open Questions

1. **Spec Line Number Mapping Strategy**
   - What we know: SPEC-04 requires "Error messages map XML failures back to spec line numbers." PyYAML `safe_load()` does not preserve line numbers.
   - What's unclear: Whether section-based references (e.g., `worksheets[2].datasource: 'SalesMap'`) are an acceptable substitute for exact line numbers.
   - Recommendation: Use section-based references. If exact line numbers are required, add `ruamel.yaml` as an optional dependency and implement a line-preserving loader.

2. **Dashboard Zone Name Interpretation**
   - What we know: The `<zone>` element has an optional `name` attribute. When the name matches a worksheet name, it is a sheet embed. Other zones may be layout containers, text zones, image zones, etc.
   - What's unclear: Whether there is a reliable way to distinguish "sheet zone" from "layout zone" purely from XML attributes. The `type-v2` attribute might help but its values are not documented in the XSD.
   - Recommendation: Only flag zones whose `name` does not match any defined worksheet/dashboard AND whose `name` is non-empty. This avoids false positives on layout zones that happen to have names.

3. **QA-02 Implementation Depth**
   - What we know: The roadmap says QA-02 "stays in Phase 2 despite requiring live infrastructure -- it is optional." The `tableauserverclient` library is in the stack but not yet installed.
   - What's unclear: Whether to implement a full sandbox publish/unpublish cycle or just a connectivity check.
   - Recommendation: Implement as a stub that checks for server configuration, and if present, attempts to publish and immediately unpublish. If no server config, emit SKIP status.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Core runtime | Yes | 3.13.7 | 3.12+ required |
| lxml | XML processing | Yes | 6.1.0 | -- |
| Pydantic | Data models | Yes | 2.13.4 | -- |
| Typer | CLI framework | Yes | 0.25.1 | -- |
| pytest | Test runner | Yes | 9.0.3 | -- |
| tableauserverclient | Sandbox smoke test (QA-02) | No | -- | Skip smoke test when unavailable |
| Tableau Server/Cloud | QA-02 smoke test | No | -- | Skip with SKIP status |

**Missing dependencies with no fallback:**
- None for the core semantic validator and static QA checker.

**Missing dependencies with fallback:**
- tableauserverclient: Not needed for semantic validation or static QA. Only needed for QA-02 (sandbox smoke test). Install when implementing QA-02, or stub it as optional.
- Tableau Server/Cloud: Required for QA-02. If unavailable, the smoke test emits SKIP and does not block the pipeline.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/validation tests/unit/qa -x -q` |
| Full suite command | `pytest --cov=tableau_agent_toolkit --cov-report=term-missing` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | XSD validation with clear error output | unit | `pytest tests/unit/validation/test_xsd.py -x` | Yes (Phase 1) |
| VAL-02 | Semantic validation catches broken sheet refs, invalid calc names, missing action targets, dangling field refs | unit | `pytest tests/unit/validation/test_semantic.py -x` | Wave 0 |
| VAL-02 | Semantic validation returns valid for well-formed TWB | unit | `pytest tests/unit/validation/test_semantic.py::test_valid_twb -x` | Wave 0 |
| VAL-03 | Validation report sorts errors first, then warnings, with remediation steps | unit | `pytest tests/unit/validation/test_report.py -x` | Wave 0 |
| VAL-04 | XSD schemas vendored in third_party/ with sync script | integration | `python scripts/sync_tableau_schemas.py && ls third_party/tableau_document_schemas/schemas/2026_1/` | Wave 0 (run script) |
| QA-01 | Static QA checks detect duplicates, unused datasources, empty dashboards, orphaned calcs | unit | `pytest tests/unit/qa/test_checker.py -x` | Wave 0 |
| QA-02 | Sandbox smoke test skips gracefully when no server | unit | `pytest tests/unit/qa/test_checker.py::test_smoke_skip -x` | Wave 0 |
| QA-03 | QA report in markdown with pass/fail per check | unit | `pytest tests/unit/qa/test_report.py -x` | Wave 0 |
| CLI | validate-semantic command works | integration | `pytest tests/integration/test_cli.py::test_validate_semantic -x` | Wave 0 |
| CLI | qa static command works | integration | `pytest tests/integration/test_cli.py::test_qa_static -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/unit/validation tests/unit/qa -x -q`
- **Per wave merge:** `pytest --cov=tableau_agent_toolkit --cov-report=term-missing`
- **Phase gate:** Full suite green + `mypy src` clean + `ruff check .` clean

### Wave 0 Gaps

- [ ] `tests/unit/validation/test_semantic.py` -- covers VAL-02
- [ ] `tests/unit/validation/test_report.py` -- covers VAL-03
- [ ] `tests/unit/qa/__init__.py` -- QA test package
- [ ] `tests/unit/qa/test_checker.py` -- covers QA-01, QA-02
- [ ] `tests/unit/qa/test_report.py` -- covers QA-03
- [ ] `tests/fixtures/broken_references.twb` -- TWB with broken cross-references
- [ ] `tests/fixtures/valid_full.twb` -- TWB with all valid cross-references
- [ ] `tests/fixtures/empty_dashboard.twb` -- TWB with empty dashboard zones
- [ ] `tests/fixtures/missing_calculation.twb` -- TWB referencing non-existent calc
- [ ] Run `scripts/sync_tableau_schemas.py` to download real XSD to third_party/

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Not in Phase 2 (Phase 3 publisher) |
| V3 Session Management | no | Not in Phase 2 |
| V4 Access Control | no | Not in Phase 2 |
| V5 Input Validation | yes | lxml XMLParser(resolve_entities=False, no_network=True) for all TWB parsing; Pydantic models for report structures |
| V6 Cryptography | no | Not in Phase 2 |

### Known Threat Patterns for XML Validation

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XML External Entity (XXE) injection | Information Disclosure | lxml XMLParser(resolve_entities=False, no_network=True) -- already used in Phase 1 |
| Billion Laughs (XML bomb) | Denial of Service | lxml has built-in protection against entity expansion attacks; use default parser settings |
| XPath injection | Tampering | Not applicable -- XPath queries are hardcoded, not user-supplied |
| Malicious TWB with excessive nesting | Denial of Service | lxml default parser limits; no custom defense needed for CLI tool use case |

## Sources

### Primary (HIGH confidence)

- [GitHub: tableau/tableau-document-schemas README] -- Confirmed XSD is syntactic only; lists what XSD cannot validate (connection attrs, calc contents, tab name references). Confirmed `processContents="skip"` marks unvalidated elements. Confirmed version mapping (XSD `twb_2026.1.0.xsd` = TWB `version='26.1'`).
- [GitHub API: raw twb_2026.1.0.xsd] -- Fetched and analyzed the real 297KB XSD. Verified cross-reference points: ActionList-ActionSource-G (worksheet/datasource/dashboard attributes), Zone-G (name attribute on zones), Column-G + DataSource-Calculation-G (formula attribute), QualifiedName-ST pattern for field names.
- [Codebase: src/tableau_agent_toolkit/validation/xsd.py] -- Existing XsdValidator pattern with dataclasses for results. Phase 2 follows same pattern.
- [Codebase: src/tableau_agent_toolkit/cli.py] -- Existing Typer CLI structure. Phase 2 adds commands to same app.
- [Codebase: src/tableau_agent_toolkit/spec/models.py] -- DashboardSpec model with worksheet names, datasource names, calculation names. Used for spec-to-XML error mapping.
- [pip show] -- lxml 6.1.0, pydantic 2.13.4, typer 0.25.1, pytest 9.0.3 all verified installed.

### Secondary (MEDIUM confidence)

- [Codebase: tests/fixtures/schemas/2026_1/twb_2026.1.0.xsd] -- Simplified test fixture XSD (not the real one). Real XSD fetched from GitHub API separately.
- [Codebase: examples/specs/] -- Three example specs showing cross-reference patterns (worksheets reference datasources, dashboards reference worksheets).
- [Codebase: scripts/sync_tableau_schemas.py] -- Sync script that downloads XSD from GitHub. Uses urllib.request, no new dependencies.

### Tertiary (LOW confidence)

- [ASSUMED] ruamel.yaml for line number preservation -- not verified as needed; section-based mapping may suffice.
- [ASSUMED] Zone name interpretation heuristics -- based on XSD analysis; real-world TWB files may have edge cases not covered by the XSD.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- no new dependencies; all libraries verified installed and tested.
- Architecture: HIGH -- follows existing Phase 1 patterns; XPath verified against real XSD.
- Pitfalls: HIGH -- sourced from real XSD analysis and official documentation.
- Code examples: HIGH -- XPath patterns tested against lxml 6.1.0.

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (30 days -- stable Python ecosystem, no new dependencies)
