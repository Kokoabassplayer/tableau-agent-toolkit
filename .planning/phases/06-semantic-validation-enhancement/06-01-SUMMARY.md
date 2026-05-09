---
phase: 06-semantic-validation-enhancement
plan: 01
subsystem: validation
tags: [yaml, semantic-validation, line-mapping, remediation, pyyaml]

# Dependency graph
requires:
  - phase: 05-xsd-path-fix-and-validation-pipeline-repair
    provides: SemanticValidator with basic cross-reference checks and SemanticIssue dataclass
provides:
  - SemanticIssue with spec_file, spec_line, remediation fields for spec line mapping
  - _build_spec_index using yaml.compose() with 1-based line number tracking
  - REMEDIATION_MAP constant with human-readable fix guidance for all 4 check categories
  - Test fixture YAML files for broken_references and dangling_datasource scenarios
affects: [06-02, 07, qa-reporting]

# Tech tracking
tech-stack:
  added: [pyyaml.compose-node-tree]
  patterns: [yaml.compose-line-tracking, remediation-map-constant, backward-compatible-dataclass-extension]

key-files:
  created:
    - tests/fixtures/broken_references_spec.yaml
    - tests/fixtures/dangling_datasource_spec.yaml
  modified:
    - src/tableau_agent_toolkit/validation/report.py
    - src/tableau_agent_toolkit/validation/semantic.py
    - tests/unit/validation/test_report.py
    - tests/unit/validation/test_semantic.py

key-decisions:
  - "Use yaml.compose() Node tree instead of yaml.safe_load() to preserve line numbers for spec error mapping"
  - "Key format uses singular form (worksheet:, zone:, calculation:, datasource:) for consistency with validate() lookups"
  - "Index dashboards[].sheets[] instead of zones[] to match actual spec YAML schema"

patterns-established:
  - "REMEDIATION_MAP: module-level constant mapping check categories to human-readable fix guidance"
  - "Spec index returns dict[str, tuple[str, int]] mapping element keys to (spec_path_fragment, 1-based line number)"

requirements-completed: [VAL-03, SPEC-04]

# Metrics
duration: 5min
completed: 2026-05-09
---

# Phase 06 Plan 01: Semantic Validation Spec Line Mapping Summary

**Spec-to-line-number mapping via yaml.compose() Node tree with remediation guidance for all 4 check categories**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-09T12:48:12Z
- **Completed:** 2026-05-09T12:53:12Z
- **Tasks:** 1
- **Files modified:** 6

## Accomplishments
- SemanticIssue dataclass extended with spec_file, spec_line, and remediation fields (backward compatible)
- _build_spec_index rewritten to use yaml.compose() Node tree for 1-based line number tracking
- Dashboard zone indexing now reads from dashboards[].sheets[] matching actual spec schema
- REMEDIATION_MAP provides human-readable fix guidance for broken_sheet_reference, broken_action_target, dangling_datasource_ref, and dangling_field_reference
- validate() populates all new fields on SemanticIssues when spec_path is provided

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for spec line mapping** - `4331d70` (test)
2. **Task 1 (GREEN): Implementation of spec line mapping and remediation** - `a1266d6` (feat)

## Files Created/Modified
- `src/tableau_agent_toolkit/validation/report.py` - Added spec_file, spec_line, remediation fields to SemanticIssue dataclass
- `src/tableau_agent_toolkit/validation/semantic.py` - Rewrote _build_spec_index with yaml.compose(), added REMEDIATION_MAP, updated validate() to populate new fields
- `tests/fixtures/broken_references_spec.yaml` - Test fixture matching broken_references.twb
- `tests/fixtures/dangling_datasource_spec.yaml` - Test fixture matching dangling_datasource.twb
- `tests/unit/validation/test_report.py` - Added 5 tests for new SemanticIssue fields
- `tests/unit/validation/test_semantic.py` - Added TestSpecLineMapping class with 10 tests for line mapping and remediation

## Decisions Made
- Used yaml.compose() Node tree instead of yaml.safe_load() because yaml.safe_load() discards line information; yaml.compose() preserves start_mark.line on every node
- Singular key format (worksheet:, zone:, etc.) in spec index to match the lookup patterns used in validate()
- dashboards[].sheets[] indexing instead of zones[] to match the actual dashboard_spec.yaml schema

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test key format mismatch**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Plan specified `"worksheets:Sheet1"` (plural) as key format in test, but the index uses singular `worksheet:` to match validate() lookups. Test assertion expected wrong key.
- **Fix:** Changed test key from `"worksheets:Sheet1"` to `"worksheet:Sheet1"` to match the actual index key format
- **Files modified:** tests/unit/validation/test_semantic.py
- **Verification:** All 34 tests pass
- **Committed in:** a1266d6 (part of GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal - test expectation corrected to match actual key format. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

All 7 files verified present. Both commits (4331d70, a1266d6) verified in git log.

## Next Phase Readiness
- Semantic validation now maps errors to spec line numbers with remediation guidance
- Ready for enhanced QA reporting (phase 07) or additional semantic check categories
- All 34 tests pass including 8 existing tests confirming backward compatibility

---
*Phase: 06-semantic-validation-enhancement*
*Completed: 2026-05-09*
