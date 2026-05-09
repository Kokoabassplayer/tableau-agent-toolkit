---
phase: 03-packaging-and-publishing
plan: 02
subsystem: publishing
tags: [tableauserverclient, tsc, pat, rest-api, pydantic, secretstr, publishing]

# Dependency graph
requires:
  - phase: 01-spec-generation
    provides: Pydantic models, Settings stub, spec parsing
  - phase: 02-validation-qa
    provides: QA checker patterns, dataclass result patterns
provides:
  - TSCPublisher with PAT auth, project resolution, sync/async publish
  - RESTFallbackPublisher for direct REST API edge cases
  - PublishReceipt Pydantic model for recording publish outcomes
  - PublishSpec model replacing publish dict in DashboardSpec
  - Activated Settings with SecretStr-protected PAT credentials
affects: [cli-publish-command, agent-skills-publisher]

# Tech tracking
tech-stack:
  added: [tableauserverclient>=0.40]
  patterns: [context-manager-auth, async-chunked-upload, receipt-model]

key-files:
  created:
    - src/tableau_agent_toolkit/publishing/__init__.py
    - src/tableau_agent_toolkit/publishing/publisher.py
    - src/tableau_agent_toolkit/publishing/fallback.py
    - src/tableau_agent_toolkit/publishing/receipt.py
    - tests/unit/publishing/__init__.py
    - tests/unit/publishing/test_publisher.py
  modified:
    - pyproject.toml
    - src/tableau_agent_toolkit/security/settings.py
    - src/tableau_agent_toolkit/spec/models.py
    - tests/unit/spec/test_models.py

key-decisions:
  - "Use result from server.workbooks.publish() for sync mode instead of original WorkbookItem -- server populates id/name on return"
  - "PAT secret protected with pydantic.SecretStr -- never logged, printed, or serialized"
  - "TSC mock patches must preserve real TSC.JobItem and TSC.WorkbookItem classes for isinstance checks"

patterns-established:
  - "PublishReceipt: Pydantic model with extra=forbid for structured publish results"
  - "Publisher pattern: Settings injection, context manager auth, project name resolution"
  - "Async threshold: 64MB triggers as_job=True with job tracking via server.jobs.wait_for_job"

requirements-completed: [PUB-01, PUB-02, PUB-03, PUB-04, PUB-05]

# Metrics
duration: 9min
completed: 2026-05-09
---

# Phase 3 Plan 02: Publishing Infrastructure Summary

**TSC-based publisher with PAT auth, project resolution, async chunked upload for large files, REST API fallback, and PublishReceipt model**

## Performance

- **Duration:** 9 min
- **Started:** 2026-05-09T04:25:59Z
- **Completed:** 2026-05-09T04:35:23Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- TSCPublisher authenticates via PAT, resolves project names to UUIDs, publishes with CreateNew/Overwrite modes
- Async chunked upload for files > 64MB with job tracking and configurable timeout
- RESTFallbackPublisher handles direct REST API publish with multipart/mixed content type
- PublishReceipt captures workbook ID, project/site target, mode, verification status
- PAT secret protected with SecretStr -- never appears in str/repr output
- All 11 mocked unit tests pass, full suite green (126 tests total)

## Task Commits

Each task was committed atomically:

1. **Task 1: Activate settings, PublishSpec, TSC dependency, PublishReceipt** - `3e41455` (feat)
2. **Task 2: TSC publisher and REST fallback (TDD)** - `6989675` (test - RED), `5b37cef` (feat - GREEN)

## Files Created/Modified
- `pyproject.toml` - Added tableauserverclient>=0.40 dependency
- `src/tableau_agent_toolkit/security/settings.py` - Activated with server_url, pat_name, pat_secret (SecretStr), site_id
- `src/tableau_agent_toolkit/spec/models.py` - Added PublishModeEnum, PublishSpec; changed DashboardSpec.publish from dict to PublishSpec
- `src/tableau_agent_toolkit/publishing/__init__.py` - Empty module init
- `src/tableau_agent_toolkit/publishing/publisher.py` - TSCPublisher with PAT auth, project resolution, sync/async publish
- `src/tableau_agent_toolkit/publishing/fallback.py` - RESTFallbackPublisher with direct REST API calls
- `src/tableau_agent_toolkit/publishing/receipt.py` - PublishReceipt Pydantic model
- `tests/unit/publishing/__init__.py` - Empty test package init
- `tests/unit/publishing/test_publisher.py` - 11 mocked unit tests covering all publisher behaviors
- `tests/unit/spec/test_models.py` - Updated test_full_spec to use PublishSpec format

## Decisions Made
- Used `result` from `server.workbooks.publish()` for sync mode instead of original WorkbookItem -- TSC populates id/name on the returned object
- PAT secret uses `pydantic.SecretStr` type to prevent accidental logging or serialization
- Mock patches preserve real `TSC.JobItem` and `TSC.WorkbookItem` classes so `isinstance()` checks work correctly in tests

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Sync publish returned WorkbookItem with None id**
- **Found during:** Task 2 (TDD GREEN phase)
- **Issue:** Publisher used the original `wb_item` (created via `TSC.WorkbookItem()`) instead of the `result` returned by `server.workbooks.publish()`. The original item has `id=None` because the server assigns the ID on publish.
- **Fix:** Added `else: wb_item = result` branch so sync publish uses the server-returned workbook item
- **Files modified:** src/tableau_agent_toolkit/publishing/publisher.py
- **Verification:** All 11 tests pass, receipt has correct workbook_id
- **Committed in:** 5b37cef (Task 2 GREEN commit)

**2. [Rule 3 - Blocking] TSC mock patches broke isinstance check**
- **Found during:** Task 2 (TDD GREEN phase)
- **Issue:** Patching the entire `TSC` module caused `mock_tsc.JobItem` to be a MagicMock (not a real type), making `isinstance(result, TSC.JobItem)` throw TypeError
- **Fix:** Added `mock_tsc.JobItem = TSC.JobItem` and `mock_tsc.WorkbookItem = TSC.WorkbookItem` to all test blocks to preserve real class references
- **Files modified:** tests/unit/publishing/test_publisher.py
- **Verification:** All 11 tests pass
- **Committed in:** 5b37cef (Task 2 GREEN commit)

**3. [Rule 3 - Blocking] Existing test_full_spec failed with PublishSpec change**
- **Found during:** Task 1 (verification)
- **Issue:** `test_full_spec` used `publish={"server": "...", "project": "..."}` (dict format) which was rejected by new `PublishSpec(extra="forbid")` model
- **Fix:** Updated test to use `publish={"project": "Finance"}` (valid PublishSpec fields only)
- **Files modified:** tests/unit/spec/test_models.py
- **Verification:** Full suite passes (115 existing tests + new tests)
- **Committed in:** 3e41455 (Task 1 commit)

---

**Total deviations:** 3 auto-fixed (1 bug, 2 blocking)
**Impact on plan:** All auto-fixes necessary for correctness and test infrastructure. No scope creep.

## Issues Encountered
- None beyond the auto-fixed deviations above

## User Setup Required

External services require manual configuration for live publish testing. Set environment variables:
- `TABLEAU_SERVER_URL` -- Tableau Server/Cloud admin URL
- `TABLEAU_PAT_NAME` -- PAT token name from Settings > Personal Access Tokens
- `TABLEAU_PAT_SECRET` -- Generated PAT secret (shown once at creation)
- `TABLEAU_SITE_ID` -- Site contentUrl (empty string for default site)

Unit tests run without any external configuration (all TSC/REST calls mocked).

## Next Phase Readiness
- Publishing infrastructure complete and ready for CLI integration (`publish` command)
- PublishSpec integrated into DashboardSpec, ready for spec-driven publish workflows
- TSC dependency installed, ready for agent skill publisher integration

---
*Phase: 03-packaging-and-publishing*
*Completed: 2026-05-09*

## Self-Check: PASSED

All 11 files verified present. All 3 commits verified in git log (3e41455, 6989675, 5b37cef). Full test suite: 126 passed, 26 deselected.
