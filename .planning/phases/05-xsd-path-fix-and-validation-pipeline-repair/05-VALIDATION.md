---
phase: 5
slug: xsd-path-fix-and-validation-pipeline-repair
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-09
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 05-01-01 | 01 | 1 | VAL-01 | — | Path resolves to correct XSD | unit | `pytest tests/test_xsd_validator.py -x -q` | ✅ W0 | ⬜ pending |
| 05-01-02 | 01 | 1 | VAL-01 | — | CLI validate-xsd produces results | integration | `pytest tests/test_cli.py -x -q -k validate_xsd` | ✅ W0 | ⬜ pending |
| 05-01-03 | 01 | 1 | VAL-04 | — | Vendored schemas in third_party/ are correct | unit | `pytest tests/test_xsd_validator.py -x -q -k path` | ✅ W0 | ⬜ pending |
| 05-02-01 | 02 | 1 | SKILL-03 | — | Validator skill references working CLI | unit | `pytest tests/test_skills.py -x -q` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_xsd_validator.py` — existing tests for XsdValidator (update path tests)
- [ ] `tests/test_cli.py` — existing CLI tests (update validate-xsd integration test)
- [ ] `tests/test_agent_pipeline.py` — existing pipeline test (remove workaround)

*Existing infrastructure covers all phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| None | — | — | — |

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
