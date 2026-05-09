# tableau-agent-toolkit

## What This Is

An open-source Python-first toolkit that generates, validates, packages, and publishes Tableau workbooks from structured YAML dashboard specifications. It ships as both a Python package/CLI and as a dual plugin (Claude Code + Codex) with five reusable agent skills for repeatable dashboard workflows: spec-writer, TWB generator, validator, QA reviewer, and publisher.

## Core Value

Deterministic workbook generation from spec + template — the same `dashboard_spec.yaml` + pinned template + pinned XSD version produces the same `.twb` every run.

## Requirements

### Validated

- ✓ SPEC-01: Pydantic v2 spec models covering workbook, datasources, parameters, calculations, worksheets, dashboards — v1.0
- ✓ SPEC-02: YAML load/dump with validation (`load_spec`/`dump_spec`) — v1.0
- ✓ SPEC-03: Deterministic output — byte-identical `.twb` from identical inputs — v1.0
- ✓ SPEC-04: Error messages map XML failures back to spec line numbers — v1.0
- ✓ SPEC-05: JSON Schema auto-generated from Pydantic models — v1.0
- ✓ GEN-01: Template-based TWB generator using lxml XML patching — v1.0
- ✓ GEN-02: Template registry with catalog.yaml and version compatibility — v1.0
- ✓ GEN-03: `<ManifestByVersion />` support — v1.0
- ✓ GEN-04: Version mapping utility (XSD filename ↔ TWB version string) — v1.0
- ✓ GEN-05: Workbook name, datasource, calculation, worksheet, dashboard patching — v1.0
- ✓ CLI-01: Typer CLI with 7 commands — v1.0
- ✓ CLI-02: Clean help text and typed arguments — v1.0
- ✓ CLI-03: `spec init` scaffolding — v1.0
- ✓ PROJ-01: pip installable package with pyproject.toml and src layout — v1.0
- ✓ PROJ-02: Unit tests, integration tests, smoke test scaffold (293+ tests) — v1.0
- ✓ PROJ-03: GitHub Actions CI with ruff/mypy/pytest matrix — v1.0
- ✓ PROJ-04: Apache-2.0, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md — v1.0
- ✓ PROJ-05: Example specs (finance, KPI, ops) with SQL files — v1.0
- ✓ VAL-01: XSD validation against pinned schemas — v1.0
- ✓ VAL-02: Semantic validation (sheet refs, calc names, action targets, field refs) — v1.0
- ✓ VAL-03: Validation report with errors, warnings, remediation steps — v1.0
- ✓ VAL-04: Vendored XSD schemas in `third_party/` with sync script — v1.0
- ✓ QA-01: Static QA checks on validated workbooks — v1.0
- ✓ QA-02: Sandbox publish smoke test stub — v1.0
- ✓ QA-03: QA report in markdown with pass/fail per check — v1.0
- ✓ PKG-01: `.twbx` packager — v1.0 (code working, procedural verification gap)
- ✓ PKG-02: Package integrity verification — v1.0
- ✓ PUB-01: TSC publisher with PAT auth — v1.0
- ✓ PUB-02: REST API fallback publisher — v1.0
- ✓ PUB-03: Publish modes CreateNew/Overwrite — v1.0 (code working, procedural verification gap)
- ✓ PUB-04: Async chunked upload > 64 MB — v1.0 (code working, procedural verification gap)
- ✓ PUB-05: Publish receipt with workbook ID, target, mode — v1.0 (code working, procedural verification gap)
- ✓ MCP-01: Compatible with official Tableau MCP server — v1.0
- ✓ MCP-02: Optional `.mcp.json` wiring in plugin manifests — v1.0
- ✓ MCP-03: Skills can leverage MCP tools — v1.0
- ✓ SKILL-01: `tableau-dashboard-spec-writer` — v1.0
- ✓ SKILL-02: `tableau-twb-generator` — v1.0
- ✓ SKILL-03: `tableau-twb-validator` — v1.0
- ✓ SKILL-04: `tableau-dashboard-qa-reviewer` — v1.0
- ✓ SKILL-05: `tableau-publisher` — v1.0
- ✓ SKILL-06: Dual plugin manifests — v1.0
- ✓ SKILL-07: `CLAUDE.md` and `AGENTS.md` — v1.0

### Active

(None — all v1 requirements shipped)

### Out of Scope

- Freehand dashboard authoring without templates — Tableau's XSD only validates syntax, not semantics; template-first is the safe path
- Full `.twbx` XSD validation — validate inner `.twb` + package integrity instead
- Connected-app / JWT auth — ship PAT first, add JWT in v2
- Visual/dashboard designer UI — completely different product
- Multi-BI-tool support (Power BI, Looker) — each tool has completely different format
- Real-time preview / rendering — proprietary Tableau rendering engine
- Calculated field expression parser — proprietary Tableau calc language

## Context

**Shipped v1.0 MVP** with 6,020 LOC Python (2,518 src + 3,502 tests) across 167 files.
Tech stack: Python 3.12+, Pydantic v2, Typer, lxml, PyYAML, tableauserverclient.
Pipeline: spec init → generate → validate-xsd → validate-semantic → qa static → package → publish.
293+ tests passing. GitHub Actions CI matrix (Python 3.12/3.13, ubuntu/windows).
Dual plugin support for Claude Code and Codex with 5 composable agent skills.

**Known tech debt:**
- CLI uses positional TWB_PATH instead of `--input` flag (documentation mismatch, functional)
- 6/7 phases have draft VALIDATION.md (Nyquist non-compliant)
- Phase 03 has no VERIFICATION.md (code verified by Phase 07 integration tests)
- `templates/catalog.yaml` references finance-reconciliation template file not in repo

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Template-first generation, not freehand | XSD is syntactic only; patching known-good templates is safer than inventing XML | ✓ Good — zero rejected workbooks from Tableau |
| Python-first engine | TSC, Document API, tabcmd all Python; MCP (Node) is optional only | ✓ Good — unified ecosystem |
| Standalone repo, not fork of tableau-document-schemas | Scope mismatch — full engine vs XSD files only. Pin XSDs as dependency | ✓ Good — clean separation |
| Dual plugin (Claude + Codex) | Both support SKILL.md workflows; shared skills tree with separate manifests | ✓ Good — tested and working |
| Pin + vendor upstream XSDs | Reproducible validation; sync script to refresh | ✓ Good — deterministic |
| `dashboard_spec.yaml` as input contract | Explicit, versioned, boring — engine can deterministically resolve all fields | ✓ Good — clean API boundary |
| Server URL excluded from PublishSpec | Security: T-07-03 threat model — credentials from CLI/env only | ✓ Good — accepted override |
| REST fallback for publish edge cases | TSC does not cover all server configurations | ✓ Good — proven in Phase 07 tests |

## Constraints

- **Language**: Python 3.12+ (ecosystem fit — TSC, Document API, tabcmd are all Python)
- **XML tooling**: lxml for parsing, editing, and XSD validation
- **Validation limit**: XSD passes ≠ workbook works in Tableau. Must include semantic QA + sandbox publish smoke test.
- **Security**: No secrets in YAML, templates, or plugin manifests. PAT/JWT via env or secrets manager.
- **License**: Apache-2.0 (aligns with upstream `tableau-document-schemas` and `tableau-mcp`)

---
*Last updated: 2026-05-09 after v1.0 milestone completion*
