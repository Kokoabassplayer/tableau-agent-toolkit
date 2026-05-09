# Requirements: tableau-agent-toolkit

**Defined:** 2026-05-08
**Core Value:** Deterministic workbook generation from spec + template — the same `dashboard_spec.yaml` + pinned template + pinned XSD version produces the same `.twb` every run.

## v1 Requirements

### Spec Schema

- [ ] **SPEC-01**: Dashboard spec defined as YAML with Pydantic v2 models covering workbook, datasources, parameters, calculations, worksheets, dashboards, publish, and QA sections
- [ ] **SPEC-02**: YAML load/dump with validation — `load_spec(path)` and `dump_spec(spec, path)` that validate on read
- [ ] **SPEC-03**: Deterministic output — same spec + template + XSD version produces byte-identical `.twb`
- [ ] **SPEC-04**: Error messages map XML failures back to spec line numbers (e.g., "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource")
- [ ] **SPEC-05**: JSON Schema auto-generated from Pydantic models for documentation and editor support

### Generation

- [ ] **GEN-01**: Template-based TWB generator using lxml XML patching of known-good template workbooks
- [ ] **GEN-02**: Template registry with catalog.yaml mapping template IDs to file paths and Tableau version compatibility rules
- [ ] **GEN-03**: `<ManifestByVersion />` support — correct XML element insertion based on target Tableau version
- [ ] **GEN-04**: Version mapping utility — converts between XSD filenames (e.g., `twb_2026.1.0.xsd`) and TWB version strings (e.g., `version='26.1'`)
- [ ] **GEN-05**: Workbook name, datasource, calculation, worksheet, and dashboard patching from spec into template

### Validation

- [ ] **VAL-01**: XSD validation against pinned `tableau-document-schemas` with clear error output (line, column, message)
- [ ] **VAL-02**: Semantic validation for sheet references, calculation names, action targets, and field references
- [ ] **VAL-03**: Validation report with errors first, then warnings, then remediation steps
- [ ] **VAL-04**: XSD schemas vendored in `third_party/` with sync script (`scripts/sync_tableau_schemas.py`)

### Packaging

- [ ] **PKG-01**: `.twbx` packager that bundles `.twb` with assets into correct zip structure
- [ ] **PKG-02**: Package integrity verification — validate inner `.twb` + confirm zip structure matches Tableau Desktop output

### Publishing

- [ ] **PUB-01**: TSC publisher with PAT auth as default backend
- [ ] **PUB-02**: REST API fallback publisher for edge cases TSC does not cover
- [ ] **PUB-03**: Publish modes: `CreateNew` and `Overwrite`, with project/site resolution
- [ ] **PUB-04**: Async publish support with chunked upload for workbooks > 64 MB
- [ ] **PUB-05**: Publish receipt with workbook ID, project/site target, mode, and verification results

### QA

- [ ] **QA-01**: Static QA checks on validated workbooks before packaging/publishing
- [ ] **QA-02**: Optional sandbox publish smoke test with preview/PDF export
- [ ] **QA-03**: QA report in markdown with pass/fail per check

### Tableau MCP Integration

- [ ] **MCP-01**: Compatible with official Tableau MCP server for post-publish content exploration and metadata validation
- [ ] **MCP-02**: Optional `.mcp.json` wiring in plugin manifests to connect to Tableau MCP for QA workflows
- [ ] **MCP-03**: Skills can leverage MCP tools for querying published workbook metadata, view images, and data sources

### CLI

- [ ] **CLI-01**: Typer CLI with commands: `spec init`, `generate`, `validate-xsd`, `validate-semantic`, `qa static`, `package`, `publish`, `report`
- [ ] **CLI-02**: Each command has clean help text and typed arguments
- [ ] **CLI-03**: `spec init` scaffolding — generate starter `dashboard_spec.yaml` from prompts

### Agent Skills & Plugins

- [ ] **SKILL-01**: `tableau-dashboard-spec-writer` skill — business brief → structured `dashboard_spec.yaml`
- [ ] **SKILL-02**: `tableau-twb-generator` skill — spec + template → workbook draft
- [ ] **SKILL-03**: `tableau-twb-validator` skill — XSD + semantic validation report
- [ ] **SKILL-04**: `tableau-dashboard-qa-reviewer` skill — static + optional sandbox QA
- [ ] **SKILL-05**: `tableau-publisher` skill — publish validated workbook to Tableau Server/Cloud
- [ ] **SKILL-06**: Dual plugin manifests — `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
- [ ] **SKILL-07**: `CLAUDE.md` and `AGENTS.md` with project-level instructions for agent workflows

### Project Hygiene

- [ ] **PROJ-01**: Python package installable via pip with `pyproject.toml` and src layout
- [ ] **PROJ-02**: Unit tests, integration tests with fixtures, and smoke test scaffold
- [ ] **PROJ-03**: GitHub Actions CI with lint (Ruff), type check (mypy), and test matrix (Python 3.12, 3.13)
- [ ] **PROJ-04**: Apache-2.0 license, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md
- [ ] **PROJ-05**: Example specs (finance reconciliation, executive KPI, ops monitoring) with SQL files

## v2 Requirements

### Advanced Features

- **ADV-01**: `spec init` from existing `.twb` — reverse-engineer spec from workbook for bootstrapping
- **ADV-02**: Connected-app / JWT auth for publishing (enterprise use case)
- **ADV-03**: Multi-version Tableau support via template passthrough profiles (pre-2026.1)
- **ADV-04**: Marketplace packaging for Claude Code and Codex plugin distribution
- **ADV-05**: Connection update support — modify datasource connections at publish time
- **ADV-06**: Richer semantic rules — expression syntax hints, parameter type validation

## Out of Scope

| Feature | Reason |
|---------|--------|
| Freehand XML authoring without templates | XSD is syntactic only; freehand TWBs pass XSD but fail in Tableau |
| Visual/dashboard designer UI | Completely different product; out of scope for CLI/agent tool |
| Full `.twbx` XSD validation | Official schemas do not support `.twbx`; validate inner `.twb` + package integrity |
| Data source connection management | Separate domain handled by Tableau Server REST API directly |
| Real-time preview / rendering | Tableau rendering engine is proprietary; MCP screenshots are the closest option |
| Multi-BI-tool support (Power BI, Looker) | Each tool has completely different format; focus on Tableau TWB |
| Calculated field expression parser | Tableau calc language is proprietary; pass-through expressions in spec, validate field refs only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SPEC-01 | Phase 1 | Pending |
| SPEC-02 | Phase 1 | Pending |
| SPEC-03 | Phase 1 | Pending |
| SPEC-04 | Phase 6 | Pending |
| SPEC-05 | Phase 1 | Pending |
| GEN-01 | Phase 1 | Pending |
| GEN-02 | Phase 1 | Pending |
| GEN-03 | Phase 1 | Pending |
| GEN-04 | Phase 1 | Pending |
| GEN-05 | Phase 1 | Pending |
| CLI-01 | Phase 1 | Pending |
| CLI-02 | Phase 1 | Pending |
| CLI-03 | Phase 1 | Pending |
| PROJ-01 | Phase 1 | Pending |
| PROJ-02 | Phase 1 | Pending |
| PROJ-03 | Phase 1 | Pending |
| PROJ-04 | Phase 1 | Pending |
| PROJ-05 | Phase 1 | Pending |
| VAL-01 | Phase 5 | Pending |
| VAL-02 | Phase 2 | Pending |
| VAL-03 | Phase 6 | Pending |
| VAL-04 | Phase 5 | Pending |
| QA-01 | Phase 2 | Pending |
| QA-02 | Phase 2 | Pending |
| QA-03 | Phase 2 | Pending |
| PKG-01 | Phase 3 | Pending |
| PKG-02 | Phase 7 | Pending |
| PUB-01 | Phase 7 | Pending |
| PUB-02 | Phase 7 | Pending |
| PUB-03 | Phase 3 | Pending |
| PUB-04 | Phase 3 | Pending |
| PUB-05 | Phase 3 | Pending |
| MCP-01 | Phase 4 | Pending |
| MCP-02 | Phase 4 | Pending |
| MCP-03 | Phase 4 | Pending |
| SKILL-01 | Phase 4 | Pending |
| SKILL-02 | Phase 4 | Pending |
| SKILL-03 | Phase 5 | Pending |
| SKILL-04 | Phase 4 | Pending |
| SKILL-05 | Phase 4 | Pending |
| SKILL-06 | Phase 4 | Pending |
| SKILL-07 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 42 total
- Mapped to phases: 42
- Unmapped: 0

---
*Requirements defined: 2026-05-08*
*Last updated: 2026-05-09 after gap closure phase assignment*
