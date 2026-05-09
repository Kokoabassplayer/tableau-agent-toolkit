---
phase: 01-spec-generation-cli-and-project-scaffolding
plan: 03
subsystem: twb-generation, validation
tags: [lxml, xml-patching, xsd-validation, template-first, determinism, pydantic]

# Dependency graph
requires:
  - phase: 01-spec-generation-cli-and-project-scaffolding
    provides: "DashboardSpec Pydantic models from Plan 01 (spec/models.py)"
  - phase: 01-spec-generation-cli-and-project-scaffolding
    provides: "TableauVersion, apply_manifest_by_version from Plan 02 (twb/manifest.py)"
  - phase: 01-spec-generation-cli-and-project-scaffolding
    provides: "TemplateRegistry from Plan 02 (templates/registry.py)"
provides:
  - "WorkbookGenerator class with generate() and 5 XML patch operations"
  - "GenerationResult dataclass for generation output"
  - "XsdValidator class with validate() method and version-based XSD resolution"
  - "XsdError and XsdValidationResult dataclasses for validation reporting"
  - "Minimal TWB test fixture for generator testing"
  - "Minimal test XSD for validator infrastructure testing"
  - "Third-party provenance documentation for vendored schemas"
affects: [packaging, publishing, semantic-validation, qa, cli-commands]

# Tech tracking
tech-stack:
  added: [lxml-etree-XMLSchema, lxml-XMLParser-secure]
  patterns: [template-first-xml-patching, deterministic-output, version-based-xsd-resolution, secure-xml-parsing]

key-files:
  created:
    - src/tableau_agent_toolkit/twb/generator.py
    - src/tableau_agent_toolkit/validation/__init__.py
    - src/tableau_agent_toolkit/validation/xsd.py
    - tests/unit/twb/test_generator.py
    - tests/unit/twb/test_determinism.py
    - tests/unit/validation/__init__.py
    - tests/unit/validation/test_xsd.py
    - tests/fixtures/minimal_template.twb
    - tests/fixtures/minimal_test.xsd
    - tests/fixtures/schemas/2026_1/twb_2026.1.0.xsd
    - third_party/tableau_document_schemas/README.md
  modified: []

key-decisions:
  - "Secure XML parsing enforced in both generator and validator (resolve_entities=False, no_network=True) to mitigate XXE attacks"
  - "Calculations patched into first datasource found in template XML as <column> with <calculation> child"
  - "Dashboards patched with basic <zones> child element for structural completeness"
  - "XSD validator uses minimal test XSD for infrastructure testing; full XSD vendoring deferred to production"

patterns-established:
  - "Template-first generation: load known-good .twb, patch elements via lxml XPath, write deterministic output"
  - "Secure XML parsing: always use resolve_entities=False and no_network=True when parsing untrusted XML"
  - "Version-based XSD resolution: display version '2026.1' maps to directory '2026_1/twb_2026.1.0.xsd'"

requirements-completed: [GEN-01, GEN-05, SPEC-03]

# Metrics
duration: 9min
completed: 2026-05-08
---

# Phase 1 Plan 03: TWB Generator and XSD Validator Summary

**Template-first TWB generator with lxml XML patching and deterministic output, plus XSD validator with version-based schema resolution**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-08T14:52:29Z
- **Completed:** 2026-05-08T15:01:31Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments
- WorkbookGenerator produces deterministic .twb files via template patching (5 patch operations)
- Same spec + template produces byte-identical output on repeated runs
- XsdValidator validates TWB files against versioned XSD schemas with line/column error reporting
- Secure XML parsing enforced throughout (XXE mitigation for T-01-06, T-01-08)
- 18 new tests passing (10 generator + 8 validator)

## Task Commits

Each task was committed atomically via TDD (RED then GREEN):

1. **Task 1: Create TWB generator with patching operations and test fixture** - RED: `3742f1f` (test), GREEN: `d701a9c` (feat)
2. **Task 2: Create basic XSD validator** - RED: `5e28365` (test), GREEN: `e17a919` (feat)

_Note: TDD tasks have multiple commits (test then feat)_

## Files Created/Modified
- `src/tableau_agent_toolkit/twb/generator.py` - WorkbookGenerator with generate() and 5 XML patch operations
- `src/tableau_agent_toolkit/validation/__init__.py` - Validation module init
- `src/tableau_agent_toolkit/validation/xsd.py` - XsdValidator with validate(), XsdError, XsdValidationResult
- `tests/unit/twb/test_generator.py` - 9 tests covering generate(), all patch operations, manifest integration
- `tests/unit/twb/test_determinism.py` - 1 test for byte-identical output on repeated runs
- `tests/unit/validation/__init__.py` - Validation test module init
- `tests/unit/validation/test_xsd.py` - 8 tests covering XsdValidator, XsdError, XsdValidationResult, version resolution
- `tests/fixtures/minimal_template.twb` - Minimal TWB template for generator testing
- `tests/fixtures/minimal_test.xsd` - Minimal XSD for validator infrastructure testing
- `tests/fixtures/schemas/2026_1/twb_2026.1.0.xsd` - Versioned XSD for version resolution testing
- `third_party/tableau_document_schemas/README.md` - Provenance docs for vendored schemas

## Decisions Made
- Secure XML parsing enforced in both generator and validator (resolve_entities=False, no_network=True) to mitigate XXE attacks per threat model T-01-06, T-01-08
- Calculations are patched into the first datasource found in the template XML as <column> elements with <calculation> children
- Dashboards are created with a basic <zones> child element for structural completeness
- XSD validator uses a minimal test XSD for infrastructure testing; full XSD vendoring will happen when real schemas are synced

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Generator ready for integration with CLI `generate` command
- XSD validator ready for integration with CLI `validate-xsd` command
- Template registry integration tested and working
- Deterministic output verified for reproducibility

## Self-Check: PASSED

All 11 files verified present. All 4 commit hashes verified in git log.

---
*Phase: 01-spec-generation-cli-and-project-scaffolding*
*Completed: 2026-05-08*
