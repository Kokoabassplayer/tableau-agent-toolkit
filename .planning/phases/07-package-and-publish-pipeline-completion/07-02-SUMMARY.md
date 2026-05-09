---
phase: 07
plan: 02
subsystem: cli-publishing
tags: [cli, publish, fallback, spec-driven, integration-tests]
dependency_graph:
  requires:
    - "src/tableau_agent_toolkit/publishing/fallback.py (RESTFallbackPublisher class)"
    - "src/tableau_agent_toolkit/publishing/publisher.py (TSCPublisher class)"
    - "src/tableau_agent_toolkit/spec/models.py (PublishSpec, PublishModeEnum, DashboardSpec)"
    - "src/tableau_agent_toolkit/spec/io.py (load_spec function)"
    - "src/tableau_agent_toolkit/security/settings.py (Settings class)"
  provides:
    - "Publish command with REST fallback on TSC failure"
    - "Publish command --spec option for spec-driven defaults"
    - "7 new integration tests for publish fallback and spec-driven publish"
  affects:
    - "src/tableau_agent_toolkit/cli.py"
    - "tests/integration/test_cli.py"
tech_stack:
  added: []
  patterns:
    - "REST fallback via nested try/except after TSC publish failure"
    - "Spec-driven defaults with CLI arg precedence using or-chaining"
    - "Server URL resolution: CLI arg > TABLEAU_SERVER_URL env var (never from spec)"
key_files:
  created: []
  modified:
    - "src/tableau_agent_toolkit/cli.py"
    - "tests/integration/test_cli.py"
decisions:
  - "Server URL never comes from spec (security: only from --server CLI arg or TABLEAU_SERVER_URL env var)"
  - "TSC error message printed to stderr before fallback attempt so user can diagnose root cause"
  - "CLI args always override spec values using or-chaining (project = project or pub.project)"
  - "Tests requiring PAT credentials provide fake env vars via runner.invoke(env=...) to reach deeper code paths"
metrics:
  duration: 3m
  completed: 2026-05-09
  tasks_completed: 2
  files_modified: 2
  tests_added: 7
  test_results: "293 passed, 0 failed"
---

# Phase 07 Plan 02: Wire REST Fallback and Spec-Driven Publish Summary

Publish command now falls back to REST API when TSC publish fails, and reads project/site/mode defaults from `dashboard_spec.yaml` via a new `--spec` option, with CLI args always taking precedence over spec values. Server URL is intentionally excluded from the spec (security: only from CLI or env var).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Wire REST fallback and spec-driven publish into publish command | e04aed6 | src/tableau_agent_toolkit/cli.py |
| 2 | Add integration tests for publish fallback and spec-driven publish | 6f2c269 | tests/integration/test_cli.py |

## Key Changes

### Task 1: REST fallback and spec-driven publish wired into publish command
- Added `from tableau_agent_toolkit.publishing.fallback import RESTFallbackPublisher` import
- Changed `server` parameter from required (`...`) to `Optional[str] = None` -- resolved from spec or env
- Changed `project` parameter from required (`...`) to `Optional[str] = None` -- resolved from spec
- Changed `mode` parameter from `str = "CreateNew"` to `Optional[str] = None` -- distinguishes "not provided" from "CreateNew"
- Added `spec_path: Optional[Path] = None` option (`--spec`)
- Spec-driven default resolution: CLI arg > spec value > hardcoded default
- Server URL resolution: `server or settings.server_url` (never from spec)
- TSC error message printed before fallback attempt
- Single `except Exception` for TSC with nested try/except for REST fallback

### Task 2: Seven new integration tests
- `test_publish_spec_provides_project` -- spec provides project when --project not given
- `test_publish_cli_project_overrides_spec` -- CLI --project takes precedence over spec
- `test_publish_spec_without_publish_section` -- graceful when spec lacks publish section
- `test_publish_spec_without_server_fails` -- server URL always required (env or CLI)
- `test_publish_falls_back_to_rest` -- REST fallback attempted on TSC failure
- `test_publish_spec_no_publish_no_project_fails` -- project required error without spec+CLI
- `test_publish_help_shows_spec_option` -- --spec option visible in help

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Test env var isolation for PAT credentials**
- **Found during:** Task 2 test execution
- **Issue:** Two tests (`test_publish_spec_without_server_fails` and `test_publish_falls_back_to_rest`) failed because the publish command checks PAT env vars before reaching the server URL check and TSC publish attempt. Without PAT env vars in the test env, the command exits early at the credentials check.
- **Fix:** Added `env={"TABLEAU_PAT_NAME": "fake-name", "TABLEAU_PAT_SECRET": "fake-secret"}` to both tests so the command proceeds past the credential check to the code path under test.
- **Files modified:** tests/integration/test_cli.py
- **Commit:** 6f2c269

## Verification Results

- `pytest tests/integration/test_cli.py::TestPublishCommand -x -q` -- 15 passed (8 existing + 7 new)
- `pytest tests/ -x -q` -- 293 passed, 0 failed
- `grep -c "RESTFallbackPublisher" cli.py` returns 2 (import + instantiation)
- `grep "spec_path" cli.py` shows --spec option parameter
- `grep "effective_server" cli.py` shows server URL resolution logic

## Self-Check

- [x] `src/tableau_agent_toolkit/cli.py` exists and contains RESTFallbackPublisher import and usage
- [x] `tests/integration/test_cli.py` exists and contains 7 new test methods
- [x] Commit e04aed6 exists in git log
- [x] Commit 6f2c269 exists in git log

## Self-Check: PASSED
