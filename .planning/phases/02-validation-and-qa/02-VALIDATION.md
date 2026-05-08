---
phase: 02-validation-and-qa
created: 2026-05-08
sampling_rate: per-task
framework: pytest 9.0.3
---

# Phase 2: Validation and QA - Validation Strategy

## Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/unit/validation tests/unit/qa -x -q` |
| Full suite command | `pytest --cov=tableau_agent_toolkit --cov-report=term-missing` |

## Phase Requirements to Test Map

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
| CLI | validate-semantic command works | integration | `pytest tests/integration/test_cli.py -x -k semantic` | Wave 0 |
| CLI | qa static command works | integration | `pytest tests/integration/test_cli.py -x -k qa` | Wave 0 |

## Sampling Rate

- **Per task commit:** `pytest tests/unit/validation tests/unit/qa -x -q`
- **Per wave merge:** `pytest --cov=tableau_agent_toolkit --cov-report=term-missing`
- **Phase gate:** Full suite green + `mypy src` clean + `ruff check .` clean

## Wave 0 Gaps

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
