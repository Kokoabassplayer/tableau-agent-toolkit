---
phase: 1
slug: spec-generation-cli-and-project-scaffolding
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-08
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0+ |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `python -m pytest tests/unit -x -q` |
| **Full suite command** | `python -m pytest --cov=tableau_agent_toolkit -v` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/unit -x -q`
- **After every plan wave:** Run `python -m pytest --cov=tableau_agent_toolkit -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | PROJ-01 | — | N/A | unit | `python -m pytest tests/unit/test_package.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | PROJ-04 | — | N/A | unit | `test -f LICENSE && test -f SECURITY.md` | ❌ W0 | ⬜ pending |
| 01-01-03 | 01 | 1 | SPEC-01 | — | N/A | unit | `python -m pytest tests/unit/spec/test_models.py -x` | ❌ W0 | ⬜ pending |
| 01-01-04 | 01 | 1 | SPEC-02 | — | N/A | unit | `python -m pytest tests/unit/spec/test_io.py -x` | ❌ W0 | ⬜ pending |
| 01-01-05 | 01 | 1 | SPEC-05 | — | N/A | unit | `python -m pytest tests/unit/spec/test_json_schema.py -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | GEN-04 | — | N/A | unit | `python -m pytest tests/unit/twb/test_manifest.py -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | GEN-03 | — | N/A | unit | `python -m pytest tests/unit/twb/test_manifest.py -x` | ❌ W0 | ⬜ pending |
| 01-02-03 | 02 | 1 | GEN-02 | — | N/A | unit | `python -m pytest tests/unit/templates/test_registry.py -x` | ❌ W0 | ⬜ pending |
| 01-02-04 | 02 | 1 | GEN-01, GEN-05 | — | N/A | unit | `python -m pytest tests/unit/twb/test_generator.py -x` | ❌ W0 | ⬜ pending |
| 01-02-05 | 02 | 1 | SPEC-03 | — | N/A | unit | `python -m pytest tests/unit/twb/test_determinism.py -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | VAL-04 | — | N/A | unit | `test -d third_party/tableau_document_schemas` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | VAL-01 | — | N/A | unit | `python -m pytest tests/unit/validation/test_xsd.py -x` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | CLI-01, CLI-02 | — | N/A | integration | `python -m pytest tests/integration/test_cli.py -x` | ❌ W0 | ⬜ pending |
| 01-04-02 | 04 | 2 | CLI-03 | — | N/A | integration | `python -m pytest tests/integration/test_spec_init.py -x` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 3 | PROJ-05 | — | N/A | integration | `python -m pytest tests/integration/test_examples.py -x` | ❌ W0 | ⬜ pending |
| 01-05-02 | 05 | 3 | PROJ-02 | — | N/A | unit | `python -m pytest --cov=tableau_agent_toolkit` | ❌ W0 | ⬜ pending |
| 01-05-03 | 05 | 3 | PROJ-03 | — | N/A | ci | `ruff check . && mypy src` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/__init__.py` — empty init
- [ ] `tests/unit/spec/__init__.py` — empty init
- [ ] `tests/unit/twb/__init__.py` — empty init
- [ ] `tests/unit/templates/__init__.py` — empty init
- [ ] `tests/unit/validation/__init__.py` — empty init
- [ ] `tests/integration/__init__.py` — empty init
- [ ] `tests/fixtures/` — minimal TWB template fixture

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| pip install and CLI commands appear | PROJ-01 | Needs venv install | `pip install -e . && tableau-agent-toolkit --help` |
| Example specs generate end-to-end | PROJ-05 | Needs full pipeline | `tableau-agent-toolkit generate --spec examples/specs/finance-reconciliation.dashboard_spec.yaml` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
