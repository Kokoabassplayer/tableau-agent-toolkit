---
phase: 06-semantic-validation-enhancement
plan: 02
subsystem: validation
tags: [cli, semantic-validation, line-numbers, remediation, typer]

# Dependency graph
requires:
  - phase: 06-01
    provides: SemanticIssue with spec_file, spec_line, remediation fields and _build_spec_index with line tracking
provides:
  - Updated validate-semantic CLI output showing "file line N: message" and "Remediation: ..." format
  - Warnings displayed even when validation passes (no errors only)
  - Integration tests proving end-to-end --spec flow with line numbers and remediation
affects: [07, qa-reporting]

# Tech tracking
tech-stack:
  added: []
  patterns: [cli-conditional-output-format, warnings-always-displayed]

key-files:
  created: []
  modified:
    - src/tableau_agent_toolkit/cli.py
    - tests/integration/test_cli.py

key-decisions:
  - "Display warnings even when validation passes (result.valid=True) so users see remediation guidance for warnings"
  - "Remove old spec_ref display format from CLI output; spec_ref kept on SemanticIssue for machine-readable consumers"

patterns-established:
  - "CLI conditional output: if err.spec_file and err.spec_line, show enriched format; else show plain format"
  - "Warnings are always displayed regardless of validation pass/fail status"

requirements-completed: [VAL-03, SPEC-04]

# Metrics
duration: 4min
completed: 2026-05-09
---

# Phase 06 Plan 02: Validate-Semantic CLI Output Enhancement Summary

**CLI validate-semantic command now displays spec file line numbers and remediation steps, with warnings always visible even on passing validation**

## Performance

- **Duration:** 4 min
- **Started:** 2026-05-09T12:56:34Z
- **Completed:** 2026-05-09T12:59:59Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- CLI output format updated to show "spec_file line N: message" when spec_file and spec_line are populated
- CLI output format shows "Remediation: ..." on the line after each error/warning when remediation is set
- Backward compatible: plain "ERROR: message" when no spec file is provided
- Warnings now displayed even when validation passes (only errors cause the "Invalid" header and exit code 1)
- Old spec_ref display format removed from CLI output (spec_ref kept on SemanticIssue for machine consumers)
- 5 new integration tests in TestValidateSemanticWithSpec class proving end-to-end --spec flow

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for --spec output format** - `922f490` (test)
2. **Task 1 (GREEN): CLI output format with line numbers and remediation** - `7930d32` (feat)

## Files Created/Modified
- `src/tableau_agent_toolkit/cli.py` - Updated validate_semantic command: conditional output format for errors/warnings with spec_file/spec_line/remediation, warnings always displayed
- `tests/integration/test_cli.py` - Added TestValidateSemanticWithSpec class with 5 integration tests

## Decisions Made
- Display warnings even when validation passes (result.valid=True) because the original code only showed errors/warnings inside the else branch, meaning warnings were invisible on passing validation. Warnings carry remediation guidance users need to see.
- Remove old spec_ref display format from CLI output since spec_file/spec_line provide better location info. spec_ref field kept on SemanticIssue for machine-readable consumers.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Warnings not displayed when validation passes**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** The original CLI code displayed errors and warnings only inside the `else` branch (when result.valid was False). Warnings like dangling_datasource_ref have valid=True (since they are warnings not errors), making them invisible to users.
- **Fix:** Moved error and warning display loops outside the if/else block so warnings are always shown. Only `sys.exit(1)` is gated on `not result.valid`.
- **Files modified:** src/tableau_agent_toolkit/cli.py
- **Verification:** test_dangling_datasource_with_spec_shows_remediation passes; all 49 integration tests pass
- **Committed in:** 7930d32 (GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal - necessary fix for warnings to be visible. No scope creep.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Self-Check: PASSED

Both files verified present. Both commits (922f490, 7930d32) verified in git log. All 49 integration tests pass.

## Next Phase Readiness
- CLI validate-semantic output now shows actionable spec line numbers and remediation guidance
- Ready for enhanced QA reporting (phase 07) which can consume the enriched output
- All 49 integration tests pass confirming backward compatibility

---
*Phase: 06-semantic-validation-enhancement*
*Completed: 2026-05-09*
