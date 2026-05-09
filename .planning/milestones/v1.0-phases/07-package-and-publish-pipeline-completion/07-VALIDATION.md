---
phase: 07
slug: package-and-publish-pipeline-completion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-09
---

# Phase 07 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/ -x -q -k "package or publish"` |
| **Full suite command** | `python -m pytest tests/ -x --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 07-01-01 | 01 | 1 | PKG-02 | T-07-01 | Verifier exit non-zero on corrupt package | integration | `python -m pytest tests/integration/test_cli.py::TestPackageCommand -x -q` | Expand existing | ⬜ pending |
| 07-02-01 | 02 | 1 | PUB-02 | T-07-02 | REST fallback uses same PAT credentials; no credential logging | integration | `python -m pytest tests/integration/test_cli.py::TestPublishCommand -x -q` | Expand existing | ⬜ pending |
| 07-02-02 | 02 | 1 | PUB-01 | T-07-03 | Spec server_url omitted; from env/CLI only | integration | `python -m pytest tests/integration/test_cli.py::TestPublishCommand -x -q` | Expand existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements. Tests will extend existing `tests/integration/test_cli.py`.

---

## Manual-Only Verifications

All phase behaviors have automated verification.

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
