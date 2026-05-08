---
phase: "01-spec-generation-cli-and-project-scaffolding"
plan: "01"
subsystem: "spec"
tags: ["foundation", "pydantic", "yaml-io", "project-scaffolding"]
dependency_graph:
  requires: []
  provides: ["DashboardSpec", "load_spec", "dump_spec", "json_schema"]
  affects: ["spec/models.py", "spec/io.py"]
tech_stack:
  added: ["pydantic>=2.13", "pydantic-settings>=2.14", "pyyaml>=6.0.3", "hatchling", "pytest>=9.0"]
  patterns: ["src-layout", "pydantic-v2-models", "yaml-safe-load", "tdd-red-green"]
key_files:
  created:
    - pyproject.toml
    - src/tableau_agent_toolkit/__init__.py
    - src/tableau_agent_toolkit/spec/__init__.py
    - src/tableau_agent_toolkit/spec/models.py
    - src/tableau_agent_toolkit/spec/io.py
    - src/tableau_agent_toolkit/security/__init__.py
    - src/tableau_agent_toolkit/security/settings.py
    - tests/conftest.py
    - tests/unit/spec/test_models.py
    - tests/unit/spec/test_json_schema.py
    - tests/unit/spec/test_io.py
    - LICENSE
    - SECURITY.md
    - CONTRIBUTING.md
    - CHANGELOG.md
    - README.md
  modified: []
decisions:
  - "Used src-layout (src/tableau_agent_toolkit/) per hatchling best practices"
  - "All Pydantic models use extra='forbid' to reject unknown fields"
  - "SpecValidationError wraps Pydantic ValidationError with field path context"
  - "dump_spec uses exclude_none=True and sort_keys=False for deterministic YAML output"
metrics:
  duration: "11 minutes"
  completed_date: "2026-05-08"
---

# Phase 1 Plan 01: Project Scaffolding and Spec Models Summary

Pydantic v2 spec models with YAML I/O, JSON Schema generation, and full project scaffolding using hatchling src-layout with 23 passing unit tests.

## Tasks Completed

| # | Task | Type | Commit | Files |
|---|------|------|--------|-------|
| 1 | Create pyproject.toml, src layout, and project hygiene files | auto | 89b1231 | pyproject.toml, __init__.py, LICENSE, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, README.md, conftest.py |
| 2 | Create Pydantic v2 spec models and JSON Schema generation | tdd | 5332c5f (RED), 0482089 (GREEN) | spec/models.py, test_models.py, test_json_schema.py |
| 3 | Create YAML I/O with validation and spec-line error messages | tdd | f01e8cd (RED), 0afb5b3 (GREEN) | spec/io.py, test_io.py |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed case-sensitive regex match in test_load_spec_extra_fields**
- **Found during:** Task 3 GREEN phase
- **Issue:** Pydantic error message uses "Extra" (capital E) but test regex `match="extra"` is case-sensitive, causing `AssertionError`
- **Fix:** Changed to `match="(?i)extra"` for case-insensitive match
- **Files modified:** tests/unit/spec/test_io.py
- **Commit:** 0afb5b3

## Verification Results

- `pip install -e ".[dev]"` -- succeeded
- `python -c "import tableau_agent_toolkit"` -- succeeded (version 0.1.0)
- `python -m pytest tests/unit/spec/ -x -v` -- 23 passed
- `python -c "from tableau_agent_toolkit.spec.io import load_spec, dump_spec"` -- succeeded
- All project hygiene files present: LICENSE, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md, README.md

## Key Interfaces Created

### DashboardSpec (spec/models.py)
Root Pydantic v2 model with 9 fields: spec_version, workbook, datasources, parameters, calculations, worksheets, dashboards, publish, qa. Supports JSON Schema generation via `json_schema()` class method.

### load_spec / dump_spec (spec/io.py)
YAML I/O functions using `yaml.safe_load()` exclusively. `load_spec` validates through Pydantic and wraps errors with field path context. `dump_spec` produces deterministic YAML via `sort_keys=False` and `exclude_none=True`.

### SpecValidationError (spec/io.py)
Custom exception carrying `field_path` attribute for programmatic access to the error location.

## Self-Check: PASSED

All 18 files verified present. All 5 commits verified in git log.
