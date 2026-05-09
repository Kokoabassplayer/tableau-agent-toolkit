---
phase: 6
slug: semantic-validation-enhancement
status: draft
nyquist_compliant: false
wave_0_complete: false
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
| 06-01-01 | 01 | 1 | VAL-03 | — | N/A | unit | `python -m pytest tests/test_spec_line_mapper.py -x -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | VAL-03 | — | N/A | unit | `python -m pytest tests/test_semantic_validator.py -x -q -k "spec_ref"` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | SPEC-04 | — | N/A | unit | `python -m pytest tests/test_semantic_validator.py -x -q -k "remediation"` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | VAL-03 | — | N/A | integration | `python -m pytest tests/test_validate_semantic_cli.py -x -q -k "spec"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_spec_line_mapper.py` — stubs for spec line mapping tests
- [ ] `tests/test_semantic_validator.py` — existing file, add spec_ref and remediation test cases
- [ ] `tests/test_validate_semantic_cli.py` — existing file, add --spec integration tests

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Error output readability with long spec paths | VAL-03 | Subjective formatting check | Run validate-semantic with --spec on a workbook with errors, verify output is human-readable |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
