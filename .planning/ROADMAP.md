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
- [ ] **Phase 5: XSD Path Fix and Validation Pipeline Repair** - Fix XSD path resolution and restore validate-xsd CLI flow
- [ ] **Phase 6: Semantic Validation Enhancement** - Wire spec-to-semantic error mapping and add remediation steps
- [ ] **Phase 7: Package and Publish Pipeline Completion** - Wire PackageVerifier, RESTFallbackPublisher, and spec-driven publish

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
- [x] 02-01: Validation report types, QA report types, and TWB test fixtures (VAL-03, QA-03)
- [x] 02-02: Semantic validator with cross-reference checks and XSD sync (VAL-01, VAL-02, VAL-03, VAL-04)
- [x] 02-03: Static QA checker with 5 checks and sandbox smoke test stub (QA-01, QA-02)
- [x] 02-04: CLI commands validate-semantic and qa static with integration tests (VAL-02, VAL-03, QA-01, QA-03)

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

**Plans**: 3 plans in 2 waves

Plans:
- [x] 03-01: Packaging module (WorkbookPackager, PackageVerifier) and package CLI command (PKG-01, PKG-02)
- [x] 03-02: Publishing infrastructure (TSCPublisher, RESTFallback, PublishReceipt, Settings, PublishSpec) (PUB-01, PUB-02, PUB-03, PUB-04, PUB-05)
- [x] 03-03: Publish CLI command with auto-package and integration tests (PUB-01, PUB-03, PUB-05)

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

**Plans**: 4 plans in 3 waves

Plans:
- [x] 04-01: Plugin manifests, MCP config, AGENTS.md, CLAUDE.md update, spec-writer skill, and generator skill (SKILL-01, SKILL-02, SKILL-06, SKILL-07, MCP-02)
- [x] 04-02: Validator, QA reviewer, and publisher skills with MCP integration references (SKILL-03, SKILL-04, SKILL-05, MCP-01, MCP-03)
- [x] 04-03: End-to-end pipeline integration test exercising all 5 skills' CLI commands (SKILL-01, SKILL-02, SKILL-03, SKILL-04, SKILL-05, SKILL-06, SKILL-07, MCP-01, MCP-02, MCP-03)
- [x] 04-04: Extended skill content quality tests (error handling, prerequisites, cross-references) (SKILL-01, SKILL-02, SKILL-03, SKILL-04, SKILL-05, SKILL-06, SKILL-07, MCP-01, MCP-02, MCP-03)

### Phase 5: XSD Path Fix and Validation Pipeline Repair
**Goal**: Fix the XSD path resolution bug that breaks the validate-xsd CLI command, restoring the validation pipeline and unblocking the tableau-twb-validator skill.
**Depends on**: Phase 1, Phase 2, Phase 4
**Requirements**: VAL-01, VAL-04, SKILL-03
**Gap Closure**: Fixes XSD path mismatch (critical), restores validate-xsd flow, unblocks SKILL-03
**Success Criteria** (what must be TRUE):
  1. `tableau-agent-toolkit validate-xsd --input workbook.twb` resolves XSD correctly and produces validation results (no FileNotFoundError)
  2. XSD path resolves to `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd`
  3. `tableau-twb-validator` skill references a working validate-xsd CLI command

**Plans**: 1 plan in 1 wave

Plans:
- [x] 05-01: Fix XSD path constant, add CLI execution tests, remove pipeline workaround (VAL-01, VAL-04, SKILL-03)

### Phase 6: Semantic Validation Enhancement
**Goal**: Wire the --spec option to SemanticValidator so semantic errors map back to spec line numbers, and add remediation steps to validation reports.
**Depends on**: Phase 1, Phase 2, Phase 5
**Requirements**: VAL-03, SPEC-04
**Gap Closure**: Populates spec_ref on SemanticIssue, adds remediation steps to validate-semantic output
**Success Criteria** (what must be TRUE):
  1. `tableau-agent-toolkit validate-semantic --input workbook.twb --spec dashboard_spec.yaml` populates spec_ref on SemanticIssue objects, mapping errors back to spec line numbers
  2. Validation report output includes remediation steps after errors and warnings
  3. Error messages reference spec locations (e.g., "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource")

**Plans**: 2 plans in 2 waves

Plans:
- [x] 06-01: Add spec_file/spec_line/remediation fields to SemanticIssue, rewrite _build_spec_index with yaml.compose() line tracking, add REMEDIATION_MAP, add unit tests (VAL-03, SPEC-04)
- [x] 06-02: Update validate-semantic CLI output format with line numbers and remediation, add integration tests (VAL-03, SPEC-04)

### Phase 7: Package and Publish Pipeline Completion
**Goal**: Wire the three unwired Phase 3 components (PackageVerifier, RESTFallbackPublisher, PublishSpec) into the CLI and publish pipeline so packaging verifies integrity and publishing supports fallback and spec-driven configuration.
**Depends on**: Phase 3, Phase 5
**Requirements**: PKG-02, PUB-01, PUB-02
**Gap Closure**: Wires PackageVerifier into package CLI, wires RESTFallbackPublisher as publish fallback, wires PublishSpec for spec-driven publish
**Success Criteria** (what must be TRUE):
  1. `tableau-agent-toolkit package --input workbook.twb` runs PackageVerifier after packaging and reports integrity results
  2. Publish command falls back to RESTFallbackPublisher when TSC publish fails
  3. Publish command reads server/project/site from spec.publish when not provided via CLI args

**Plans**: 2 plans in 2 waves

Plans:
- [ ] 07-01: Wire PackageVerifier into package CLI command with integration tests (PKG-02)
- [ ] 07-02: Wire REST fallback and spec-driven publish into publish command with integration tests (PUB-01, PUB-02)

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Spec, Generation, CLI, and Project Scaffolding | 0/5 | Not started | - |
| 2. Validation and QA | 0/4 | Not started | - |
| 3. Packaging and Publishing | 0/3 | Planned | - |
| 4. Agent Skills and MCP Integration | 0/4 | Planned | - |
| 5. XSD Path Fix and Validation Pipeline Repair | 0/1 | Planned | - |
| 6. Semantic Validation Enhancement | 0/2 | Planned | - |
| 7. Package and Publish Pipeline Completion | 0/2 | Planned | - |
