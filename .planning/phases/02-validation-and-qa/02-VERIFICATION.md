---
phase: 02-validation-and-qa
verified: 2026-05-09T10:30:00Z
status: gaps_found
score: 6/8 must-haves verified
overrides_applied: 0
gaps:
  - truth: "Error messages map XML failures back to spec line numbers"
    status: failed
    reason: "SemanticIssue.spec_ref field exists but is never populated by SemanticValidator.validate(). CLI accepts --spec option but never passes spec_path to the validator. No code maps TWB elements back to spec YAML line numbers."
    artifacts:
      - path: "src/tableau_agent_toolkit/validation/semantic.py"
        issue: "validate() does not accept spec_path parameter; spec_ref is always None on all SemanticIssue instances"
      - path: "src/tableau_agent_toolkit/cli.py"
        issue: "validate_semantic() accepts --spec option but never passes spec_path to SemanticValidator.validate()"
    missing:
      - "SemanticValidator.validate() must accept optional spec_path parameter"
      - "Mapping logic from TWB elements back to dashboard_spec.yaml line numbers"
      - "spec_ref population on SemanticIssue when spec is provided"
  - truth: "User can run validate-semantic --input workbook.twb and qa static --input workbook.twb with --input flag"
    status: failed
    reason: "CLI uses positional TWB_PATH argument instead of --input flag as specified in ROADMAP success criteria. Commands work functionally but do not match the documented interface."
    artifacts:
      - path: "src/tableau_agent_toolkit/cli.py"
        issue: "validate-semantic uses typer.Argument for twb_path, not typer.Option with --input flag"
    missing:
      - "Either change CLI to use --input option, or update ROADMAP.md success criteria to reflect positional argument"
human_verification:
  - test: "Run validate-semantic on a TWB generated from a known spec and verify error quality"
    expected: "Error messages are clear and actionable for a human reader"
    why_human: "Error message clarity and UX quality is subjective"
  - test: "Review qa static markdown report in a text editor for formatting quality"
    expected: "Report is well-formatted markdown with clear section ordering"
    why_human: "Markdown rendering quality is visual/subjective"
---

# Phase 2: Validation and QA Verification Report

**Phase Goal:** Users can validate generated workbooks with semantic checks that catch errors XSD cannot (broken references, invalid calc names, missing targets) and run static QA checks that produce actionable reports.
**Verified:** 2026-05-09T10:30:00Z
**Status:** gaps_found
**Re-verification:** No -- initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | User can run `validate-semantic` and receive a report flagging broken sheet references, invalid calc names, missing action targets, and dangling field references | VERIFIED | CLI command registered; `SemanticValidator.validate()` catches all 4 cross-reference error types (broken_sheet_reference, broken_action_target, dangling_datasource_ref, dangling_field_reference); 8 unit tests + 5 integration tests passing; behavioral spot-check on broken_references.twb exits 1 with correct error output |
| 2 | Error messages map XML failures back to spec line numbers | FAILED | `SemanticIssue.spec_ref` field exists but is always `None`; `SemanticValidator.validate()` does not accept a `spec_path` parameter; CLI `validate_semantic()` accepts `--spec` option but never passes it to the validator |
| 3 | User can run `qa static` and receive a markdown QA report with pass/fail per check, errors first, then warnings, then remediation steps | VERIFIED | `generate_qa_report()` orders sections: Errors, Warnings, Passed Checks with remediation text for failures; behavioral spot-check produces well-structured markdown; `--output` flag writes to file |
| 4 | Vendored XSD schemas exist in `third_party/` and can be refreshed via `scripts/sync_tableau_schemas.py` | VERIFIED | `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd` exists at 304,715 bytes (297KB); `scripts/sync_tableau_schemas.py` exists at 2,984 bytes |
| 5 | `validate-semantic` and `qa static` commands appear in `--help` output | VERIFIED | `--help` output shows `validate-semantic`, `qa` subcommand group; 2 integration tests verify discovery |
| 6 | `qa static --output report.md` writes markdown to file | VERIFIED | `--output` option registered; behavioral spot-check writes file and content contains `# QA Report` header; integration test verifies file exists with correct content |
| 7 | CLI uses `--input` flag for specifying workbook path | FAILED | Both `validate-semantic` and `qa static` use positional `TWB_PATH` argument, not `--input` option. Commands work but do not match ROADMAP-specified interface |
| 8 | All Phase 2 tests pass | VERIFIED | 72 Phase 2-specific tests pass (80 total when including Phase 1 validation tests that remain green); all imports verified working |

**Score:** 6/8 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/tableau_agent_toolkit/validation/report.py` | SemanticIssue, Severity, SemanticValidationResult dataclasses | VERIFIED | 55 lines; all 3 types exported; Severity has ERROR/WARNING/INFO; SemanticIssue has spec_ref field |
| `src/tableau_agent_toolkit/qa/report.py` | CheckStatus, QACheckResult, generate_qa_report | VERIFIED | 99 lines; CheckStatus has PASS/FAIL/WARN/SKIP; generate_qa_report produces ordered markdown |
| `src/tableau_agent_toolkit/validation/semantic.py` | SemanticValidator with validate() | VERIFIED | 132 lines; 4 cross-reference checks; secure XML parser; imported in __init__.py |
| `src/tableau_agent_toolkit/qa/checker.py` | StaticQAChecker with check_all() | VERIFIED | 309 lines; 5 static checks + sandbox stub; check_all returns 6 results; imported in __init__.py |
| `src/tableau_agent_toolkit/cli.py` | validate-semantic and qa static commands | VERIFIED | validate-semantic at line 113; qa_app at line 140; qa static at line 144; imports wired |
| `tests/unit/validation/test_semantic.py` | 8 unit tests for semantic validator | VERIFIED | 104 lines; 8 tests in TestSemanticValidator; all passing |
| `tests/unit/qa/test_checker.py` | 13 unit tests for QA checker | VERIFIED | 229 lines; 13 tests across 7 classes; all passing |
| `tests/integration/test_cli.py` | 11 integration tests for new CLI commands | VERIFIED | 165 lines; 11 Phase 2 tests in 3 classes; all passing |
| `tests/fixtures/broken_references.twb` | TWB with NonExistentSheet and MissingSheet | VERIFIED | 845 bytes; contains broken zone and action references |
| `tests/fixtures/valid_full.twb` | TWB with all valid cross-references | VERIFIED | 961 bytes; valid worksheet/dashboard/datasource references |
| `tests/fixtures/empty_dashboard.twb` | TWB with empty dashboard zones | VERIFIED | 662 bytes; empty <zones /> element |
| `tests/fixtures/missing_calculation.twb` | TWB with [MissingField] calc reference | VERIFIED | 714 bytes; formula references undefined field |
| `tests/fixtures/dangling_datasource.twb` | TWB with undefined datasource ref | VERIFIED | 601 bytes; worksheet references MissingDS |
| `third_party/.../twb_2026.1.0.xsd` | Real vendored XSD schema | VERIFIED | 304,715 bytes; real XSD from tableau-document-schemas |
| `scripts/sync_tableau_schemas.py` | XSD sync script | VERIFIED | 2,984 bytes; exists and executable |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `validation/semantic.py` | `validation/report.py` | imports SemanticIssue, Severity, SemanticValidationResult | WIRED | Line 18-22: `from tableau_agent_toolkit.validation.report import ...` |
| `validation/semantic.py` | TWB XML tree | lxml XPath queries | WIRED | Lines 52-55: `root.xpath("//datasource/@name")` and 4 other XPath queries |
| `qa/checker.py` | `qa/report.py` | imports QACheckResult, CheckStatus | WIRED | Line 18: `from tableau_agent_toolkit.qa.report import CheckStatus, QACheckResult` |
| `qa/checker.py` | TWB XML tree | lxml XPath and string search | WIRED | Lines 71, 104, 177, 218, 275: XPath queries via `_parse()` method |
| `cli.py` | `validation/semantic.py` | imports and calls SemanticValidator.validate() | WIRED | Line 26: import; line 128: `validator.validate(twb_path)` |
| `cli.py` | `qa/checker.py` | imports and calls StaticQAChecker.check_all() | WIRED | Line 20: import; line 160: `checker.check_all(twb_path)` |
| `cli.py` | `qa/report.py` | imports generate_qa_report | WIRED | Line 21: import; line 161: `generate_qa_report(results, twb_path)` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `validation/semantic.py` | `errors`, `warnings` lists | XPath queries on TWB XML tree | Yes -- populated from `root.xpath()` results | FLOWING |
| `qa/checker.py` | `QACheckResult` returns | XPath + string search on TWB | Yes -- each check method returns substantive results | FLOWING |
| `qa/report.py` | `generate_qa_report` output | `results` list parameter | Yes -- produces real markdown with check names/counts | FLOWING |
| `cli.py` validate-semantic | `result` from validator | SemanticValidator.validate() | Yes -- printed to stdout with error/warning messages | FLOWING |
| `cli.py` qa static | `report` string | generate_qa_report() | Yes -- written to file or stdout | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| validate-semantic on broken TWB exits 1 with errors | `python -m tableau_agent_toolkit.cli validate-semantic tests/fixtures/broken_references.twb` | Exits 1; prints "Invalid" + "ERROR: Dashboard zone 'NonExistentSheet'" + "ERROR: Action source references undefined worksheet 'MissingSheet'" | PASS |
| validate-semantic on valid TWB exits 0 | `python -m tableau_agent_toolkit.cli validate-semantic tests/fixtures/valid_full.twb` | Exits 0; prints "Valid: tests/fixtures/valid_full.twb passes semantic validation" | PASS |
| qa static produces markdown report | `python -m tableau_agent_toolkit.cli qa static tests/fixtures/broken_references.twb` | Exits 1; prints markdown with "# QA Report:" header, summary line, Errors section, Passed Checks section | PASS |
| qa static --output writes file | `python -m tableau_agent_toolkit.cli qa static tests/fixtures/valid_full.twb --output /tmp/test_qa_report.md` | Exits 1 (missing workbook name); file written with "# QA Report:" content | PASS |
| --help shows validate-semantic and qa | `python -m tableau_agent_toolkit.cli --help` | Shows generate, validate-xsd, validate-semantic, qa, spec commands | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| VAL-01 | 02-02 | XSD validation with clear error output | SATISFIED | XsdValidator exists from Phase 1; vendored XSD at 304KB; CLI command wired |
| VAL-02 | 02-02, 02-04 | Semantic validation for sheet refs, calc names, action targets, field refs | SATISFIED | SemanticValidator catches all 4 types; CLI command working; 8 unit + 5 integration tests |
| VAL-03 | 02-01, 02-02, 02-04 | Validation report with errors first, warnings, remediation steps | PARTIALLY SATISFIED | Report types support ordering; generate_qa_report orders correctly; but validate-semantic output does not include remediation steps (it only prints ERROR/WARNING messages) |
| VAL-04 | 02-02 | XSD schemas vendored in third_party/ with sync script | SATISFIED | twb_2026.1.0.xsd at 304,715 bytes; sync_tableau_schemas.py exists |
| QA-01 | 02-03, 02-04 | Static QA checks on validated workbooks | SATISFIED | StaticQAChecker with 5 checks; CLI qa static command; 13 unit + integration tests |
| QA-02 | 02-03 | Optional sandbox smoke test with preview/PDF | SATISFIED | check_sandbox_smoke_test returns SKIP; stub documented as requiring tableauserverclient |
| QA-03 | 02-01, 02-04 | QA report in markdown with pass/fail per check | SATISFIED | generate_qa_report produces markdown; qa static outputs to stdout or file |

No orphaned requirements found -- all Phase 2 requirements (VAL-01 through VAL-04, QA-01 through QA-03) are claimed by at least one plan.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `src/tableau_agent_toolkit/cli.py` | 120-122 | Dead parameter: `--spec` option accepted but never passed to SemanticValidator | Warning | Users may expect --spec to work and provide spec-line-number mapping, but it does nothing |
| `src/tableau_agent_toolkit/qa/checker.py` | 303-308 | Sandbox smoke test is a stub returning SKIP | Info | By design -- documented as requiring tableauserverclient in future plan |

No TODO/FIXME/PLACEHOLDER markers found in any Phase 2 source files. No empty implementations. All data flows are substantive.

### Human Verification Required

### 1. Error Message Clarity

**Test:** Run `tableau-agent-toolkit validate-semantic` on various TWB files with different error types and review error message quality
**Expected:** Error messages are clear, specific, and actionable for a human reader
**Why human:** Error message clarity and UX quality is subjective; grep cannot assess readability

### 2. QA Report Formatting

**Test:** Run `tableau-agent-toolkit qa static --output report.md` and review the markdown in an editor
**Expected:** Well-formatted markdown with clear section ordering, proper headers, readable summary
**Why human:** Markdown rendering quality and visual formatting is subjective

### Gaps Summary

Two gaps were found that prevent the phase goal from being fully achieved:

**Gap 1: Spec line number mapping not implemented (ROADMAP SC #2)**
The `SemanticIssue` dataclass has a `spec_ref` field and the CLI has a `--spec` option, but neither is connected. `SemanticValidator.validate()` never receives a spec path and never populates `spec_ref`. The ROADMAP success criterion requires errors to map back to spec line numbers (e.g., "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource"). This is also related to SPEC-04 from REQUIREMENTS.md.

To fix:
1. Add `spec_path: Path | None = None` parameter to `SemanticValidator.validate()`
2. When spec_path is provided, load the spec and build a mapping from TWB element names to spec line numbers
3. Populate `spec_ref` on each `SemanticIssue` with the corresponding spec location
4. Update the CLI to pass `spec_path` to the validator
5. Display spec references in error output

**Gap 2: CLI uses positional argument instead of --input flag (ROADMAP SC #1, #3)**
The ROADMAP success criteria specify `--input workbook.twb` but the actual CLI uses a positional `TWB_PATH` argument. The commands work correctly but do not match the documented interface. This is a documentation/interface consistency issue, not a functional gap.

To fix: Either update the CLI to use `--input` as an option, or update the ROADMAP.md success criteria to reflect the positional argument design.

---

_Verified: 2026-05-09T10:30:00Z_
_Verifier: Claude (gsd-verifier)_
