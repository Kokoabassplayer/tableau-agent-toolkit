---
phase: 04
slug: agent-skills-and-mcp-integration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-05-09
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.3 |
| **Config file** | pyproject.toml (tool.pytest.ini_options) |
| **Quick run command** | `pytest tests/unit/test_skill_manifests.py -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/unit/test_skill_manifests.py -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 04-01-01 | 01 | 1 | SKILL-06, SKILL-07, MCP-02 | T-04-01 | Env var refs, no hardcoded secrets | unit | `pytest tests/unit/test_skill_manifests.py::TestPluginManifests tests/unit/test_skill_manifests.py::TestMCPConfig tests/unit/test_skill_manifests.py::TestAgentInstructions -x -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | SKILL-01, SKILL-02 | — | N/A | unit | `pytest tests/unit/test_skill_manifests.py::TestSkillFrontmatter -x -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 2 | SKILL-03, SKILL-04, SKILL-05, MCP-01, MCP-03 | T-04-05 | Skills validate via CLI, not raw strings | unit | `pytest tests/unit/test_skill_manifests.py::TestSkillFrontmatter -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/unit/test_skill_manifests.py` — covers SKILL-06, SKILL-07, MCP-01, MCP-02 (JSON validation, frontmatter validation, file existence)

*Existing infrastructure covers all other phase requirements.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| QA reviewer skill documents MCP tool usage for post-publish queries | MCP-03 | Requires running an actual agent with MCP server connected | Install plugin, configure MCP env vars, invoke skill from agent, verify agent can query published workbook metadata |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
