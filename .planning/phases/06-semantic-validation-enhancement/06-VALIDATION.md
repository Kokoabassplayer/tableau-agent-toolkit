---
phase: 6
slug: semantic-validation-enhancement
status: active
nyquist_compliant: true
wave_0_complete: true
created: 2026-05-09
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short -k "semantic or spec_line or remediation"` |
| **Full suite command** | `python -m pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short -k "semantic or spec_line or remediation"`
- **After every plan wave:** Run `python -m pytest tests/ -x --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | VAL-03, SPEC-04 | — | N/A | unit | `python -m pytest tests/unit/validation/test_report.py tests/unit/validation/test_semantic.py -x -q --tb=short` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 2 | VAL-03, SPEC-04 | — | N/A | integration | `python -m pytest tests/integration/test_cli.py::TestValidateSemanticWithSpec -x -q --tb=short` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/unit/validation/test_report.py` — created by Plan 01 Task 1 (SemanticIssue fields + remediation tests)
- [x] `tests/unit/validation/test_semantic.py` — existing file, Plan 01 adds spec_line + remediation test cases
- [x] `tests/integration/test_cli.py` — existing file, Plan 02 adds TestValidateSemanticWithSpec

Existing infrastructure covers all phase requirements.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Error output readability with long spec paths | VAL-03 | Subjective formatting check | Run validate-semantic with --spec on a workbook with errors, verify output is human-readable |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 15s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
