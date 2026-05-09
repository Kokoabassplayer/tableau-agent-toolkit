# tableau-agent-toolkit

## What This Is

An open-source Python-first toolkit that generates, validates, packages, and publishes Tableau workbooks from structured YAML dashboard specifications. It ships as both a Python package/CLI and as a dual plugin (Claude Code + Codex) with reusable agent skills for repeatable dashboard workflows.

Target users: analytics engineers, BI developers, data platform teams, and agent users (Claude Code / Codex) who want governed, deterministic workbook generation instead of ad hoc manual editing.

## Core Value

Deterministic workbook generation from spec + template — the same `dashboard_spec.yaml` + pinned template + pinned XSD version produces the same `.twb` every run.

## Requirements

### Validated

- [x] 5 shared agent skills (spec writer, TWB generator, validator, QA reviewer, publisher) — Validated in Phase 04
- [x] Dual plugin manifests (`.claude-plugin/plugin.json` + `.codex-plugin/plugin.json`) — Validated in Phase 04

### Active

- [ ] Python package with Typer CLI (`tableau-agent-toolkit`)
- [ ] Structured dashboard spec schema (`dashboard_spec.yaml`) with Pydantic v2 models
- [ ] Template-first TWB generator using lxml-based XML patching
- [ ] XSD validation against pinned `tableau-document-schemas`
- [ ] Semantic validation (sheet refs, calc names, action targets, field references)
- [ ] `.twbx` packager (separate step from `.twb` generation)
- [ ] Tableau Server Client publisher with PAT auth (REST fallback)
- [ ] Template registry with compatibility rules and version management
- [ ] `<ManifestByVersion />` support for direct workbook authoring
- [ ] Static QA checks and optional sandbox publish smoke tests
- [ ] Static QA checks and optional sandbox publish smoke tests
- [ ] CLI commands: `spec init`, `generate`, `validate-xsd`, `validate-semantic`, `qa static`, `package`, `publish`, `report`

### Out of Scope

- Freehand dashboard authoring without templates — Tableau's XSD only validates syntax, not semantics; template-first is the safe path
- Full `.twbx` XSD validation — validate inner `.twb` + package integrity instead
- Connected-app / JWT auth — ship PAT first, add JWT in v0.4
- Official Tableau MCP as core engine — MCP is optional for post-publish QA only
- Storing credentials in specs, templates, or plugin manifests

## Context

- **Tableau document schemas**: Official `tableau/tableau-document-schemas` repo provides `.twb` XSDs. XSD validation is syntactic only — does not guarantee semantic validity or support `.twbx`.
- **Tableau Server Client (Python)**: Official library for publishing, auth, and server operations. Preferred publisher backend.
- **Tableau Document API (Python)**: Useful for selective inspection/patching, but labeled "As-Is" and unsupported. Does not support creating files from scratch.
- **Deep research report**: Comprehensive design doc already exists at `~/Downloads/deep-research-report.md` — serves as the blueprint for this project.
- **Target Tableau version**: Start with 2026.1, support earlier versions through template passthrough profiles.

## Constraints

- **Language**: Python 3.12+ (ecosystem fit — TSC, Document API, tabcmd are all Python)
- **XML tooling**: lxml for parsing, editing, and XSD validation
- **Validation limit**: XSD passes ≠ workbook works in Tableau. Must include semantic QA + sandbox publish smoke test.
- **Security**: No secrets in YAML, templates, or plugin manifests. PAT/JWT via env or secrets manager.
- **License**: Apache-2.0 (aligns with upstream `tableau-document-schemas` and `tableau-mcp`)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Template-first generation, not freehand | XSD is syntactic only; patching known-good templates is safer than inventing XML | — Pending |
| Python-first engine | TSC, Document API, tabcmd all Python; MCP (Node) is optional only | — Pending |
| Standalone repo, not fork of tableau-document-schemas | Scope mismatch — our repo is a full engine, theirs is XSD files only. Pin their XSDs as third-party dependency | — Pending |
| Dual plugin (Claude + Codex) | Both support SKILL.md workflows; shared skills tree with separate manifests | — Pending |
| Pin + vendor upstream XSDs | Reproducible validation; `scripts/sync_tableau_schemas.py` to refresh | — Pending |
| `dashboard_spec.yaml` as input contract | Explicit, versioned, boring — engine can deterministically choose template and resolve all fields | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-09 after Phase 04 completion*
