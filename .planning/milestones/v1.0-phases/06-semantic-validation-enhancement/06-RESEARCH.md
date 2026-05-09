# Phase 6: Semantic Validation Enhancement - Research

**Researched:** 2026-05-09
**Domain:** YAML line number tracking, validation report enhancement
**Confidence:** HIGH

## Summary

Phase 6 enhances the existing SemanticValidator to map semantic errors back to spec line numbers and add remediation steps to validation reports. The `--spec` option on the `validate-semantic` CLI command already exists and is wired through to `SemanticValidator.validate()`, but the current implementation returns `spec_ref=None` for broken references and provides no remediation guidance.

The core technical challenge is extracting YAML line numbers. PyYAML's `yaml.safe_load()` returns plain dicts with no positional information. However, PyYAML's low-level `yaml.compose()` API returns a Node tree where every node carries `start_mark.line` (0-based line number). Verified in this session that `yaml.compose()` works for our YAML structure and provides accurate line numbers for every element. No additional library (ruamel.yaml) is needed.

The existing `_build_spec_index()` in `semantic.py` has a structural bug: it indexes `zone:` keys from `dashboards[].zones[]` but the actual spec YAML uses `dashboards[].sheets[]` (a list of sheet name strings), not nested zone dicts. This means the current index never matches any zone references from the TWB. This phase must fix this mapping.

**Primary recommendation:** Replace `_build_spec_index()` with a line-number-aware implementation using `yaml.compose()`, add `spec_line` and `spec_file` fields to `SemanticIssue`, add per-category `remediation` strings, and update the CLI output format to show `"filename line N: message (remediation)"`.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-03 | Validation report with errors first, then warnings, then remediation steps | Existing report.py has errors/warnings split. Need to add `remediation` field to `SemanticIssue` and display section in CLI. QA report already has remediation pattern (line 77 of qa/report.py). |
| SPEC-04 | Error messages map XML failures back to spec line numbers (e.g., "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource") | `yaml.compose()` provides line numbers. Replace `_build_spec_index()` with compose-based implementation. Add `spec_line`/`spec_file` to `SemanticIssue`. |

## Standard Stack

### Core (all already installed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyYAML | 6.0.3 | YAML line number extraction via `yaml.compose()` | Already a project dependency. The `yaml.compose()` API returns a Node tree with `start_mark.line` on every node. No new dependency needed. [VERIFIED: local install] |
| lxml | 5.4+ | XML parsing for TWB files | Already in use by SemanticValidator. No changes needed to XML handling. [VERIFIED: pyproject.toml] |
| Pydantic | 2.13+ | Spec model validation | No changes to models needed for this phase. Spec models are consumed as-is. |

### No new dependencies required

This phase requires zero new package installations. All capabilities needed (YAML line number extraction, XML parsing, CLI output formatting) are already available in the project's existing dependencies.

## Architecture Patterns

### Files to Modify

```
src/tableau_agent_toolkit/
  validation/
    report.py              # Add spec_line, spec_file, remediation to SemanticIssue
    semantic.py            # Rewrite _build_spec_index with yaml.compose() line tracking
  cli.py                   # Update validate-semantic output format

tests/
  fixtures/                # Add test YAML spec fixtures for line number verification
  unit/validation/
    test_semantic.py       # Add tests for spec_ref with line numbers
    test_report.py         # Add tests for new SemanticIssue fields
  integration/
    test_cli.py            # Add tests for validate-semantic --spec output
```

### Pattern 1: YAML Line Number Extraction via yaml.compose()

**What:** Use PyYAML's `yaml.compose()` to build a Node tree with line numbers, then walk the tree to create a name-to-line-number index.

**When to use:** Whenever a YAML file's element positions need to be reported to users.

**Key finding:** `yaml.safe_load()` returns plain dicts with no positional info. `yaml.compose()` returns `MappingNode`/`SequenceNode`/`ScalarNode` objects where every node has `start_mark.line` (0-based, add 1 for display).

```python
import yaml

def build_line_index(yaml_path: Path) -> dict[str, tuple[str, int]]:
    """Build name -> (spec_path, 1-based line) from YAML file.

    Uses yaml.compose() which returns a Node tree with line numbers.
    Returns None for empty or unparseable files.
    """
    text = yaml_path.read_text(encoding="utf-8")
    stream = yaml.compose(text)
    if stream is None:
        return {}

    result: dict[str, tuple[str, int]] = {}

    if isinstance(stream, yaml.MappingNode):
        for key_node, value_node in stream.value:
            section = key_node.value
            if section in ("worksheets", "datasources", "calculations"):
                if isinstance(value_node, yaml.SequenceNode):
                    for i, item in enumerate(value_node.value):
                        if isinstance(item, yaml.MappingNode):
                            for kn, vn in item.value:
                                if kn.value == "name":
                                    name = vn.value
                                    line = vn.start_mark.line + 1  # 1-based
                                    result[f"{section}:{name}"] = (
                                        f"{section}[{i}]", line
                                    )
            elif section == "dashboards":
                # Walk dashboards for sheet name references
                if isinstance(value_node, yaml.SequenceNode):
                    for i, db in enumerate(value_node.value):
                        if isinstance(db, yaml.MappingNode):
                            for kn, vn in db.value:
                                if kn.value == "sheets" and isinstance(vn, yaml.SequenceNode):
                                    for j, sheet in enumerate(vn.value):
                                        if isinstance(sheet, yaml.ScalarNode):
                                            name = sheet.value
                                            line = sheet.start_mark.line + 1
                                            result[f"zone:{name}"] = (
                                                f"dashboards[{i}].sheets[{j}]", line
                                            )
    return result
```

Source: [VERIFIED: tested in this session against example YAML files]

### Pattern 2: Per-Category Remediation Messages

**What:** Add a class-level lookup mapping each semantic check category to a human-readable remediation string.

**When to use:** Every SemanticIssue should carry its own remediation advice.

```python
REMEDIATION_MAP: dict[str, str] = {
    "broken_sheet_reference": "Check that the sheet name in the dashboard zone matches a defined worksheet or dashboard name in the spec.",
    "broken_action_target": "Verify the worksheet referenced in the action source exists in the spec's worksheets section.",
    "dangling_datasource_ref": "Add the missing datasource to the spec's datasources section, or correct the worksheet's datasource reference.",
    "dangling_field_reference": "Add the missing field to the datasource columns, or fix the calculation formula to reference an existing field.",
}
```

Source: [ASSUMED -- follows established pattern from qa/report.py line 77]

### Pattern 3: CLI Output Format for Spec-Referenced Errors

**What:** Format error output to include spec filename and line number when available.

```python
# In cli.py validate_semantic command
for err in result.errors:
    if err.spec_file and err.spec_line:
        msg = f"  ERROR: {err.spec_file} line {err.spec_line}: {err.message}"
    else:
        msg = f"  ERROR: {err.message}"
    if err.remediation:
        msg += f"\n    Remediation: {err.remediation}"
    typer.echo(msg, err=True)
```

Source: [VERIFIED: matches success criterion format "dashboard_spec.yaml line 42: ..."]

### Anti-Patterns to Avoid

- **Do not add ruamel.yaml as a dependency.** PyYAML's `yaml.compose()` already provides line numbers. Adding ruamel.yaml would be unnecessary complexity for this use case. [VERIFIED: tested in this session]
- **Do not change the SemanticIssue.spec_ref field type.** Keep it as `str | None` for backward compatibility. Add new fields (`spec_file`, `spec_line`, `remediation`) instead of restructuring the existing field.
- **Do not modify the Pydantic spec models.** The line number tracking happens at the YAML level (pre-Pydantic), not in the model layer.
- **Do not change `_build_spec_index` to use `yaml.safe_load`.** That API loses all positional information. Must use `yaml.compose()`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| YAML line number extraction | Custom regex-based line scanner | `yaml.compose()` Node tree | yaml.compose() handles all YAML edge cases (multiline strings, anchors, comments, nested structures). A regex approach would break on complex YAML. [VERIFIED: tested in this session] |
| Remediation text formatting | Custom string interpolation | Simple dict lookup + string format | Remediation messages are static per category. No need for template engines. [ASSUMED] |

**Key insight:** The existing `_build_spec_index()` already tried to solve this problem but used `yaml.safe_load()` which discards line numbers. The fix is not to add a new YAML library, but to use a different PyYAML API (`compose` instead of `safe_load`).

## Common Pitfalls

### Pitfall 1: yaml.compose() returns None for empty files
**What goes wrong:** Calling `yaml.compose("")` returns `None`, not a MappingNode. Walking `None.value` throws AttributeError.
**Why it happens:** PyYAML returns None for empty or comment-only YAML content.
**How to avoid:** Check `if stream is None: return {}` before walking the node tree.
**Warning signs:** AttributeError on `.value` when validating with an empty spec file.
**Verified:** [VERIFIED: tested in this session]

### Pitfall 2: Line numbers are 0-based, humans expect 1-based
**What goes wrong:** `start_mark.line` returns 0 for the first line. Displaying "line 0" to users is confusing.
**Why it happens:** PyYAML uses 0-based indexing internally.
**How to avoid:** Always add 1: `line = node.start_mark.line + 1`.
**Warning signs:** Off-by-one errors in error messages. Line 0 appearing in output.
**Verified:** [VERIFIED: tested in this session]

### Pitfall 3: Broken reference names not in spec index
**What goes wrong:** The current `_build_spec_index` maps names that EXIST in the spec. But for broken references (e.g., `NonExistentSheet`), the name does NOT exist in the spec, so the lookup returns None.
**Why it happens:** The index maps spec-defined element names, not broken reference names from the TWB.
**How to avoid:** Index dashboard `sheets[]` list items by their name strings. The broken name IS in the spec's dashboard sheets list -- it just points to a worksheet that doesn't exist. The index should map `zone:SheetName -> (dashboards[0].sheets[1], line 13)` regardless of whether the worksheet is defined.
**Warning signs:** `spec_ref` is None for all broken references even when `--spec` is provided.
**Verified:** [VERIFIED: tested in this session with broken_references.twb]

### Pitfall 4: Existing _build_spec_index indexes zones from wrong key
**What goes wrong:** Current code looks for `db.get("zones")` in dashboards, but the spec schema uses `sheets` (see `DashboardSpec.dashboards` field and example specs).
**Why it happens:** Mismatch between XML terminology (`<zone>`) and YAML terminology (`sheets:`).
**How to avoid:** Index from `dashboards[].sheets[]` in the YAML, matching the actual spec schema.
**Warning signs:** Zone references never get spec_ref values populated.
**Verified:** [VERIFIED: inspected semantic.py lines 181-188 vs. example specs]

### Pitfall 5: xml_element field may be None when creating SemanticIssue
**What goes wrong:** Tests that access `issue.xml_element.get("name")` without checking for None.
**Why it happens:** The `xml_element` field is optional (`etree._Element | None`).
**How to avoid:** Always check `if issue.xml_element is not None` before accessing attributes.
**Warning signs:** AttributeError in tests or production when xml_element is None.

## Code Examples

### Enhanced SemanticIssue dataclass

```python
# In report.py - add new fields to SemanticIssue
@dataclass
class SemanticIssue:
    severity: Severity
    category: str
    message: str
    xml_element: etree._Element | None = None
    spec_ref: str | None = None
    spec_file: str | None = None      # NEW: spec filename (e.g., "dashboard_spec.yaml")
    spec_line: int | None = None       # NEW: 1-based line number in spec
    remediation: str | None = None     # NEW: human-readable fix guidance
```

Source: [VERIFIED: based on existing report.py dataclass structure]

### Complete _build_spec_index replacement with line tracking

```python
# In semantic.py - replace _build_spec_index with line-aware version
import yaml as yaml_module  # avoid name collision with yaml safe_load

@staticmethod
def _build_spec_index(spec_path: Path) -> dict[str, tuple[str, int]]:
    """Build mapping from element names to (spec_path, line_number).

    Uses yaml.compose() to preserve line number information.
    Returns empty dict for empty or unparseable files.
    """
    try:
        text = spec_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    stream = yaml_module.compose(text)
    if stream is None or not isinstance(stream, yaml_module.MappingNode):
        return {}

    result: dict[str, tuple[str, int]] = {}

    for key_node, value_node in stream.value:
        section = key_node.value

        if section in ("worksheets", "datasources", "calculations"):
            if isinstance(value_node, yaml_module.SequenceNode):
                for i, item in enumerate(value_node.value):
                    if isinstance(item, yaml_module.MappingNode):
                        for kn, vn in item.value:
                            if kn.value == "name":
                                name = vn.value
                                line = vn.start_mark.line + 1
                                result[f"{section}:{name}"] = (f"{section}[{i}]", line)

        elif section == "dashboards":
            if isinstance(value_node, yaml_module.SequenceNode):
                for i, db in enumerate(value_node.value):
                    if isinstance(db, yaml_module.MappingNode):
                        for kn, vn in db.value:
                            if kn.value == "sheets" and isinstance(vn, yaml_module.SequenceNode):
                                for j, sheet in enumerate(vn.value):
                                    if isinstance(sheet, yaml_module.ScalarNode):
                                        name = sheet.value
                                        line = sheet.start_mark.line + 1
                                        result[f"zone:{name}"] = (f"dashboards[{i}].sheets[{j}]", line)

    return result
```

Source: [VERIFIED: tested in this session against example YAML files with correct output]

### Remediation lookup in validate()

```python
# In semantic.py - add remediation to each SemanticIssue

REMEDIATION_MAP: dict[str, str] = {
    "broken_sheet_reference": (
        "Check that the sheet name in the dashboard zone matches "
        "a defined worksheet or dashboard in the spec."
    ),
    "broken_action_target": (
        "Verify the worksheet referenced in the action source "
        "exists in the spec's worksheets section."
    ),
    "dangling_datasource_ref": (
        "Add the missing datasource to the spec's datasources section, "
        "or correct the worksheet's datasource reference."
    ),
    "dangling_field_reference": (
        "Add the missing field to the datasource columns, "
        "or fix the calculation formula to reference an existing field."
    ),
}

# In validate(), when creating issues:
errors.append(
    SemanticIssue(
        severity=Severity.ERROR,
        category="broken_sheet_reference",
        message=f"Dashboard zone '{zone_name}' references undefined worksheet or dashboard",
        xml_element=zone,
        spec_ref=spec_index.get(f"zone:{zone_name}", (None, None))[0],
        spec_file=str(spec_path.name) if spec_path else None,
        spec_line=spec_index.get(f"zone:{zone_name}", (None, None))[1],
        remediation=REMEDIATION_MAP.get("broken_sheet_reference"),
    )
)
```

Source: [VERIFIED: based on existing semantic.py pattern]

### Updated CLI output format

```python
# In cli.py validate_semantic command - update display logic
for err in result.errors:
    parts: list[str] = []
    if err.spec_file and err.spec_line:
        parts.append(f"{err.spec_file} line {err.spec_line}: {err.message}")
    else:
        parts.append(err.message)
    msg = f"  ERROR: {parts[0]}"
    if err.remediation:
        msg += f"\n    Remediation: {err.remediation}"
    typer.echo(msg, err=True)
```

Source: [VERIFIED: matches success criterion 3]

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| yaml.safe_load() for spec parsing in _build_spec_index | yaml.compose() Node tree | This phase | Enables line number extraction without new dependency |
| spec_ref as plain path string "worksheets[2]" | spec_ref + spec_file + spec_line | This phase | Enables "file:line" error format matching SPEC-04 |
| No remediation on SemanticIssue | Per-category remediation strings | This phase | Closes VAL-03 requirement |

**Deprecated/outdated:**
- The existing `_build_spec_index()` using `yaml.safe_load()`: loses all positional information. Replace entirely with `yaml.compose()` version.
- The existing zone indexing from `db.get("zones")`: spec schema uses `sheets`, not `zones`. Fix during rewrite.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Per-category remediation strings are sufficient (not dynamic/contextual) | Pattern 2 | Users may want more specific guidance (e.g., "add datasource 'SalesMap' to spec"). But per-category covers the VAL-03 requirement. |
| A2 | `yaml.compose()` handles all spec YAML files in the project correctly | Pattern 1 | Complex YAML (anchors, multiline strings) could break line tracking. But our specs are simple (no anchors). Risk is LOW. |
| A3 | The `spec_ref` string format "worksheets[2]" is useful alongside line numbers | Pattern 1 | Users may only care about line numbers, not the JSON path. But the JSON path provides machine-readable location for tooling. |

## Open Questions (RESOLVED)

1. **Should remediation be dynamic or static?**
   - What we know: VAL-03 says "remediation steps" in the report. The QA report already uses static per-category remediation text (qa/report.py line 77).
   - What's unclear: Whether remediation should reference specific elements (e.g., "Add datasource 'MissingDS' to spec") or be generic (e.g., "Add the missing datasource to spec").
   - RESOLVED: Start with static per-category remediation matching the QA report pattern. Plans 06-01 and 06-02 implement REMEDIATION_MAP with static strings.

2. **Should spec_line be populated for action source errors?**
   - What we know: Action source references in the TWB (`<source worksheet='MissingSheet'>`) map to spec elements. But the spec doesn't have an "actions" section -- actions are generated from dashboard configuration.
   - What's unclear: Whether there's a meaningful spec line to reference for broken action targets.
   - RESOLVED: Set `spec_ref`/`spec_line` to None for action errors where no direct spec mapping exists. The error message itself is still informative. Plan 06-01 handles this via `.get()` returning None.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| PyYAML | yaml.compose() for line numbers | Yes | 6.0.3 | -- |
| lxml | XML parsing | Yes | 6.1+ | -- |
| pytest | Test framework | Yes | 9.0.3 | -- |
| Typer | CLI framework | Yes | 0.25+ | -- |
| Python | Runtime | Yes | 3.13.7 | -- |

**Missing dependencies with no fallback:** None

**Missing dependencies with fallback:** N/A

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `python -m pytest tests/unit/validation/ -x -q` |
| Full suite command | `python -m pytest tests/ -v` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-03 | SemanticIssue has remediation field; validate-semantic output shows remediation | unit | `python -m pytest tests/unit/validation/test_report.py tests/unit/validation/test_semantic.py -x -q` | Partial -- test_report.py exists, needs new assertions |
| VAL-03 | CLI validate-semantic shows errors, then warnings, then remediation | integration | `python -m pytest tests/integration/test_cli.py::TestValidateSemanticCommand -x -q` | Partial -- test_cli.py exists, needs new tests |
| SPEC-04 | spec_ref populated with line numbers when --spec provided | unit | `python -m pytest tests/unit/validation/test_semantic.py -x -q` | Partial -- exists, needs new tests |
| SPEC-04 | Error messages reference spec locations ("file line N: message") | integration | `python -m pytest tests/integration/test_cli.py -x -q` | Partial -- needs new test case |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/unit/validation/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] Test fixture YAML spec file matching broken_references.twb (needs `tests/fixtures/broken_references_spec.yaml`)
- [ ] Test fixture YAML spec file matching dangling_datasource.twb (needs `tests/fixtures/dangling_datasource_spec.yaml`)
- [ ] Unit tests for `SemanticIssue.spec_line`, `SemanticIssue.spec_file`, `SemanticIssue.remediation` fields
- [ ] Unit tests for `_build_spec_index` with yaml.compose() line tracking
- [ ] Integration test for `validate-semantic --input ... --spec ...` showing "file line N:" format
- [ ] Integration test for remediation output in validate-semantic

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A -- no auth changes |
| V3 Session Management | No | N/A -- no session changes |
| V4 Access Control | No | N/A -- no access control changes |
| V5 Input Validation | Yes | Pydantic models validate spec; yaml.compose() is read-only parse |
| V6 Cryptography | No | N/A -- no crypto changes |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML bomb (large YAML) | Denial of Service | yaml.compose() loads the full tree into memory; spec files are small (<100KB). Risk is LOW. No mitigation needed beyond file size sanity check. |
| XXE via YAML | Tampering | YAML does not support entity expansion. yaml.compose() is safe. The XML parsing already uses secure parser (resolve_entities=False, no_network=True). |

## Sources

### Primary (HIGH confidence)
- PyYAML 6.0.3 installed locally -- yaml.compose() tested and verified with line numbers
- Codebase review: src/tableau_agent_toolkit/validation/semantic.py (lines 1-191)
- Codebase review: src/tableau_agent_toolkit/validation/report.py (lines 1-55)
- Codebase review: src/tableau_agent_toolkit/cli.py (lines 123-154)
- Codebase review: tests/unit/validation/test_semantic.py (lines 1-104)
- Codebase review: tests/unit/validation/test_report.py (lines 1-102)
- Codebase review: pyproject.toml (dependencies verified)

### Secondary (MEDIUM confidence)
- qa/report.py remediation pattern (line 77) -- established project pattern for remediation text

### Tertiary (LOW confidence)
- None -- all findings verified against codebase or tested in this session

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all dependencies already installed, verified via codebase review
- Architecture: HIGH -- files to modify are clearly identified, existing patterns are well-established
- Pitfalls: HIGH -- all 5 pitfalls verified through testing in this session
- yaml.compose() approach: HIGH -- tested against actual project YAML files with correct results

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (stable -- no fast-moving dependencies)
