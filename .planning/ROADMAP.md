# Roadmap: tableau-agent-toolkit

## Overview

Build a deterministic Tableau workbook generation pipeline in four phases. Start with the spec schema and generator (the core value proposition), add validation to make output trustworthy, add packaging and publishing to complete the pipeline, then wrap everything as agent skills for Claude Code and Codex integration.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Spec, Generation, CLI, and Project Scaffolding** - Write a YAML spec, generate a .twb from a template, and validate it against pinned XSD schemas
- [ ] **Phase 2: Validation and QA** - Validate workbooks semantically and run static QA checks so output is trustworthy before packaging
- [ ] **Phase 3: Packaging and Publishing** - Package validated workbooks into .twbx and publish to Tableau Server/Cloud
- [ ] **Phase 4: Agent Skills and MCP Integration** - Expose the proven CLI pipeline as five composable agent skills with dual plugin manifests

## Phase Details

### Phase 1: Spec, Generation, CLI, and Project Scaffolding
**Goal**: Users can define a dashboard spec in YAML, generate a .twb workbook from a template, and validate it against pinned XSD schemas -- all via CLI commands and a properly structured Python package.
**Depends on**: Nothing (first phase)
**Requirements**: SPEC-01, SPEC-02, SPEC-03, SPEC-04, SPEC-05, GEN-01, GEN-02, GEN-03, GEN-04, GEN-05, CLI-01, CLI-02, CLI-03, PROJ-01, PROJ-02, PROJ-03, PROJ-04, PROJ-05
**Success Criteria** (what must be TRUE):
  1. User can run `tableau-agent-toolkit spec init` to scaffold a starter `dashboard_spec.yaml` from prompts
  2. User can run `tableau-agent-toolkit generate --spec dashboard_spec.yaml --template template.twb` and get a deterministic `.twb` file where identical inputs produce byte-identical output
  3. User can run `tableau-agent-toolkit validate-xsd --input workbook.twb` and receive XSD validation results against pinned schemas with clear line/column/message error output
  4. User can `pip install` the package and all CLI commands appear with typed arguments and help text
  5. Example specs (finance reconciliation, executive KPI, ops monitoring) exist in the repository and generate successfully through the full spec-to-twb pipeline

**Plans**: 5 plans in 3 waves

Plans:
- [x] 01-01: Project scaffolding, Pydantic spec models, and YAML I/O (PROJ-01, PROJ-04, SPEC-01, SPEC-02, SPEC-04, SPEC-05)
- [x] 01-02: TWB version mapping, manifest handler, and template registry (GEN-02, GEN-03, GEN-04)
- [x] 01-03: TWB generator with XML patching and XSD validator (GEN-01, GEN-05, SPEC-03)
- [x] 01-04: Typer CLI with generate, validate-xsd, and spec init commands (CLI-01, CLI-02, CLI-03)
- [x] 01-05: CI pipeline, example specs, and XSD sync script (PROJ-02, PROJ-03, PROJ-05)

### Phase 2: Validation and QA
**Goal**: Users can validate generated workbooks with semantic checks that catch errors XSD cannot (broken references, invalid calc names, missing targets) and run static QA checks that produce actionable reports.
**Depends on**: Phase 1
**Requirements**: VAL-01, VAL-02, VAL-03, VAL-04, QA-01, QA-02, QA-03
**Success Criteria** (what must be TRUE):
  1. User can run `tableau-agent-toolkit validate-semantic --input workbook.twb` and receive a report flagging broken sheet references, invalid calculation names, missing action targets, and dangling field references
  2. Error messages map XML failures back to spec line numbers (e.g., "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource")
  3. User can run `tableau-agent-toolkit qa static --input workbook.twb` and receive a markdown QA report with pass/fail per check, errors first, then warnings, then remediation steps
  4. Vendored XSD schemas exist in `third_party/` and can be refreshed via `scripts/sync_tableau_schemas.py`

**Plans**: 4 plans in 3 waves

Plans:
- [ ] 02-01: Validation report types, QA report types, and TWB test fixtures (VAL-03, QA-03)
- [ ] 02-02: Semantic validator with cross-reference checks and XSD sync (VAL-01, VAL-02, VAL-03, VAL-04)
- [ ] 02-03: Static QA checker with 5 checks and sandbox smoke test stub (QA-01, QA-02)
- [ ] 02-04: CLI commands validate-semantic and qa static with integration tests (VAL-02, VAL-03, QA-01, QA-03)

### Phase 3: Packaging and Publishing
**Goal**: Users can package validated workbooks into .twbx archives and publish them to Tableau Server or Tableau Cloud with PAT authentication, receiving a publish receipt confirming the upload.
**Depends on**: Phase 2
**Requirements**: PKG-01, PKG-02, PUB-01, PUB-02, PUB-03, PUB-04, PUB-05
**Success Criteria** (what must be TRUE):
  1. User can run `tableau-agent-toolkit package --input workbook.twb` and receive a `.twbx` file with correct zip structure matching Tableau Desktop output
  2. User can run `tableau-agent-toolkit publish --input workbook.twbx --server https://server --project "My Project"` and the workbook appears on Tableau Server with PAT auth
  3. Publishing supports `CreateNew` and `Overwrite` modes with project/site resolution, and works for workbooks larger than 64 MB via chunked upload
  4. Each publish produces a receipt with workbook ID, project/site target, mode used, and verification results
  5. REST API fallback publisher handles edge cases the Tableau Server Client library does not cover

**Plans**: TBD

Plans:
- [ ] 03-01: TBD
- [ ] 03-02: TBD

### Phase 4: Agent Skills and MCP Integration
**Goal**: Agent users (Claude Code and Codex) can invoke five composable skills that wrap the proven CLI pipeline, with dual plugin manifests and optional MCP integration for post-publish QA workflows.
**Depends on**: Phase 3
**Requirements**: MCP-01, MCP-02, MCP-03, SKILL-01, SKILL-02, SKILL-03, SKILL-04, SKILL-05, SKILL-06, SKILL-07
**Success Criteria** (what must be TRUE):
  1. `tableau-dashboard-spec-writer` skill exists and an agent can use it to convert a business brief into a structured `dashboard_spec.yaml`
  2. `tableau-twb-generator`, `tableau-twb-validator`, and `tableau-publisher` skills exist and an agent can chain them to go from spec to published workbook
  3. `tableau-dashboard-qa-reviewer` skill exists and an agent can use it to run static and optional sandbox QA checks
  4. Both `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` manifests exist with correct skill references
  5. `CLAUDE.md` and `AGENTS.md` project-level instructions exist, and optional `.mcp.json` wiring connects to Tableau MCP for post-publish metadata queries

**Plans**: TBD

Plans:
- [ ] 04-01: TBD
- [ ] 04-02: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Spec, Generation, CLI, and Project Scaffolding | 0/5 | Not started | - |
| 2. Validation and QA | 0/4 | Not started | - |
| 3. Packaging and Publishing | 0/? | Not started | - |
| 4. Agent Skills and MCP Integration | 0/? | Not started | - |
