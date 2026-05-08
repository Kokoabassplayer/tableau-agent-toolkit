---
phase: 02-validation-and-qa
plan: 03
subsystem: qa
tags: [lxml, xpath, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-validation-and-qa/01
    provides: QACheckResult, CheckStatus, generate_qa_report from qa.report module
provides:
  - StaticQAChecker class with check_all() and 6 individual check methods
  - 5 static QA checks (duplicate worksheets, unused datasources, empty dashboards, orphaned calculations, missing workbook name)
  - Sandbox smoke test stub (SKIP status)
affects: [02-validation-and-qa/04, cli qa static command, agent skills]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Secure XML parser (resolve_entities=False, no_network=True) for all TWB parsing"
    - "Hybrid reference detection: XPath for structured references + string search for implicit usage"
    - "TDD workflow: RED test commit then GREEN implementation commit"

key-files:
  created:
    - src/tableau_agent_toolkit/qa/checker.py
    - tests/unit/qa/test_checker.py
  modified:
    - src/tableau_agent_toolkit/qa/__init__.py

key-decisions:
  - "Hybrid XPath + string search for datasource reference detection to handle both structured and minimal TWB fixtures"
  - "String-search approach for orphaned calculation detection (count occurrences in full XML text)"
  - "Sandbox smoke test as explicit SKIP stub, not a no-op or error"

patterns-established:
  - "TDD with separate RED and GREEN commits for checker logic"
  - "StaticQAChecker uses module-level secure parser instance for efficiency"

requirements-completed: [QA-01, QA-02]

# Metrics
duration: 5min
completed: 2026-05-08
---

# Phase 2 Plan 3: Static QA Checker Summary

**StaticQAChecker with 5 static checks (duplicates, unused DS, empty dashboards, orphaned calcs, missing name) and sandbox SKIP stub, all via TDD**

## Performance

- **Duration:** 5 min
- **Started:** 2026-05-08T16:47:56Z
- **Completed:** 2026-05-08T16:53:25Z
- **Tasks:** 1 (TDD: RED + GREEN)
- **Files modified:** 3

## Accomplishments
- StaticQAChecker detects 5 quality issue types beyond structural validation
- Sandbox smoke test stub gracefully returns SKIP when no server configured
- 13 unit tests passing (12 planned + 1 Parameters DS exclusion)
- All 27 QA module tests passing (no regressions)

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Failing tests for StaticQAChecker** - `174ae75` (test)
2. **Task 1 (GREEN): Implement StaticQAChecker** - `e5c2c02` (feat)

## Files Created/Modified
- `src/tableau_agent_toolkit/qa/checker.py` - StaticQAChecker class with check_all(), 5 static checks, and sandbox stub
- `tests/unit/qa/test_checker.py` - 13 unit tests covering all check methods
- `src/tableau_agent_toolkit/qa/__init__.py` - Updated to export StaticQAChecker

## Decisions Made
- Used hybrid XPath + string search for unused datasource detection: XPath catches explicit `<datasource name="">` references in worksheets/actions/zones; string search (outside `<datasources>` block) catches implicit usage in minimal TWB fixtures
- Used occurrence-counting string search for orphaned calculation detection: a calculation name must appear at least twice in the full XML (definition + reference) to be considered used
- Sandbox smoke test is an explicit SKIP stub, not a no-op, making it clear in QA reports that the check was intentionally skipped

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test 9 used valid_full.twb which lacks workbook name attribute**
- **Found during:** Task 1 (GREEN phase)
- **Issue:** Test expected PASS for missing_workbook_name check on valid_full.twb, but that fixture has no `name` attribute on root element
- **Fix:** Changed test to use inline TWB fixture with explicit `name='MyWorkbook'` attribute
- **Files modified:** tests/unit/qa/test_checker.py
- **Verification:** All 13 tests pass
- **Committed in:** e5c2c02 (part of GREEN commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Minimal - test fixture selection issue, no logic change needed.

## Known Stubs

| File | Stub | Reason |
|------|------|--------|
| src/tableau_agent_toolkit/qa/checker.py | check_sandbox_smoke_test returns SKIP | Per plan: full implementation requires tableauserverclient + server config. Future plan will wire live connection. |

## Next Phase Readiness
- StaticQAChecker ready for CLI integration (`qa static` command)
- Sandbox smoke test stub ready for tableauserverclient wiring in future plan
- QACheckResult + generate_qa_report from plan 02-01 integrate seamlessly with checker output

## Self-Check: PASSED

All files verified present. All commits verified in git log.

---
*Phase: 02-validation-and-qa*
*Completed: 2026-05-08*
