---
phase: 3
slug: packaging-and-publishing
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-09
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short -k "package or publish"` |
| **Full suite command** | `python -m pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short -k "package or publish"`
- **After every plan wave:** Run `python -m pytest tests/ -x --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | PKG-01 | — | N/A | unit | `python -m pytest tests/test_packager.py -x -q` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | PKG-02 | — | N/A | unit | `python -m pytest tests/test_packager.py -x -q -k "integrity"` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | PUB-01 | T-3-01 | PAT secret never logged or serialized | unit | `python -m pytest tests/test_publisher.py -x -q -k "pat_auth"` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | PUB-02 | — | N/A | unit | `python -m pytest tests/test_publisher.py -x -q -k "rest_fallback"` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 1 | PUB-03 | — | N/A | unit | `python -m pytest tests/test_publisher.py -x -q -k "modes"` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 2 | PUB-04 | — | N/A | integration | `python -m pytest tests/test_publisher.py -x -q -k "chunked"` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 2 | PUB-05 | — | N/A | unit | `python -m pytest tests/test_publisher.py -x -q -k "receipt"` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_packager.py` — stubs for PKG-01, PKG-02
- [ ] `tests/test_publisher.py` — stubs for PUB-01 through PUB-05
- [ ] `tests/conftest.py` — shared fixtures for TSC mocks

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Publish to live Tableau Server | PUB-01 | Requires real PAT credentials and server | Set env vars and run `tableau-agent-toolkit publish --input test.twbx --server $URL --project "Test"` |
| Chunked upload > 64MB | PUB-04 | Requires generating large workbook fixture | Create >64MB .twbx and verify upload succeeds |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
