# Project Research Summary

**Project:** tableau-agent-toolkit
**Domain:** Programmatic Tableau workbook authoring (generation, validation, packaging, publishing) with AI agent plugin integration
**Researched:** 2026-05-08
**Confidence:** HIGH

## Executive Summary

Tableau-agent-toolkit is a Python CLI tool that generates valid Tableau workbooks (.twb/.twbx) from structured YAML specifications, validates them against official schemas and custom semantic rules, and publishes them to Tableau Server/Cloud. This is a near-greenfield domain -- no existing tool solves the generate-a-complete-workbook-from-a-spec problem end-to-end. The four official Tableau infrastructure pieces (document-schemas, MCP, TSC, Document API) each cover a narrow slice but leave the full authoring pipeline unaddressed.

The recommended approach is a **template-first generation engine** built on lxml XML patching. Rather than authoring TWB XML from scratch (which would pass XSD validation but fail to open in Tableau), the generator loads known-good .twb templates created in Tableau Desktop and patches specific elements -- datasources, worksheets, dashboards, calculated fields -- using XPath-based manipulation. This is layered behind a gated pipeline: spec validation (Pydantic), then XSD validation (lxml + pinned schemas), then semantic validation (custom Python reference checks), then packaging, then publishing. The CLI wraps this pipeline via Typer, and dual agent plugins (Claude Code + Codex) expose it as five composable skills.

The dominant risk is false confidence from XSD validation alone. Tableau documentation warns that XSD is syntactic-only and cannot guarantee a workbook opens in Tableau. The mitigation is mandatory semantic validation that catches broken sheet references, invalid calculated field names, missing action targets, and dangling field references. A secondary risk is TWBX packaging structure -- the official schemas do not cover packaged workbooks, so the zip layout must be reverse-engineered from reference files produced by Tableau Desktop. Both risks are addressed in the architecture by treating validation as a multi-tier system and requiring integration tests against known-good artifacts.

## Key Findings

### Recommended Stack

Python 3.12+ is mandated by PROJECT.md and is the right choice given that TSC, lxml, and the entire Tableau Python ecosystem target it. The stack is lean: Pydantic v2 for spec models and validation, Typer for CLI, lxml for XML processing and XSD validation, PyYAML for spec parsing, and tableauserverclient (TSC) for publishing. Vendored XSD files from tableau-document-schemas provide the structural validation baseline. No external databases, no web framework, no JavaScript runtime for the core engine.

**Core technologies:**
- **Python 3.12+:** Primary language -- TSC, lxml, and Pydantic are all Python-native; 3.12 balances modern features with binary wheel support
- **Pydantic v2 (2.13+):** Spec schema models, input validation, JSON Schema generation for documentation -- 5-50x faster than v1 via Rust core
- **Typer (0.15+):** CLI framework built on Click with type-hint-driven command definition and auto-help generation
- **lxml (5.4+):** XML parsing, XPath queries, XSD validation -- the only Python library with production-grade XSD support
- **tableauserverclient (0.40+):** Official Tableau Server Client for publishing, PAT auth, chunked uploads, project resolution
- **PyYAML (6.0.3+):** Spec file parsing, loaded through Pydantic for validation
- **pytest (9.0+):** Testing framework with fixtures for template-based integration tests
- **ruff (0.11+):** Single linter/formatter replacing black, isort, flake8
- **hatchling:** Build backend for pyproject.toml-based packaging

### Expected Features

The feature landscape is well-defined with a clear dependency chain. Spec schema is the foundation -- everything else consumes typed DashboardSpec objects. The template registry feeds the generator, which feeds validation, which feeds packaging and publishing. Agent skills are the final composition layer that wraps CLI commands.

**Must have (table stakes):**
- YAML/structured spec input (Pydantic v2 models) -- declarative, version-controllable specs are the baseline for any as-code tool
- Template-based TWB generation (lxml patching) -- the only reliable path to workbooks that actually open in Tableau
- XSD validation (pinned vendored schemas) -- minimum structural confidence
- Semantic validation (custom reference checks) -- the hard correctness problem that makes the tool trustworthy
- CLI interface (Typer) -- developer tools must be command-line driven
- Deterministic output -- same inputs produce byte-identical output, required for diff-based review
- Error messages pointing to spec locations, not XML locations

**Should have (differentiators):**
- Dual AI agent plugins (Claude Code + Codex) with five shared skills -- no other Tableau tooling offers this
- Template registry with version compatibility rules -- prevents template/Tableau version mismatches
- .twbx packaging as a separate step -- clean separation between generation and bundling
- Static QA checks + optional sandbox smoke test -- layered quality assurance
- Spec schema documentation generation (free from Pydantic JSON Schema export)
- spec init scaffolding from existing .twb files -- lowers onboarding friction

**Defer (v2+):**
- Sandbox smoke tests (requires live Tableau Server infrastructure)
- Template registry with full governance (start with inline template paths)
- spec init from existing .twb (valuable but not core)
- JWT/connected-app auth (PAT is sufficient for v0.1)
- MCP wiring for agent-assisted QA (optional extension)

### Architecture Approach

The system is a four-layer pipeline: spec ingestion, workbook generation, validation/QA, and publishing. A fifth cross-cutting layer provides the CLI and agent plugin interfaces. The key architectural decision is **template-first generation** -- never author XML from scratch, always patch known-good templates. The second key decision is **gated validation tiers** -- spec validation (Pydantic), then XSD validation (lxml), then semantic validation (custom Python), each catching different error classes.

**Major components:**
1. **spec/ (models.py, io.py)** -- Pydantic v2 models for dashboard_spec.yaml schema; YAML load/save with validation on load
2. **twb/ (generator.py, manifest.py, packager.py)** -- lxml-based XML patching engine, ManifestByVersion handler, zipfile-based .twbx packager
3. **validation/ (xsd.py, semantic.py)** -- pinned XSD structural validation, custom semantic reference checks
4. **publisher/ (tsc_client.py, rest_client.py)** -- TSC-based primary publisher, REST fallback for edge cases
5. **templates/registry.py** -- Template lookup, version compatibility, catalog.yaml management
6. **cli.py** -- Typer app with subcommands: spec init, generate, validate-xsd, validate-semantic, qa static, package, publish, report
7. **skills/** -- Five shared SKILL.md files consumed by both Claude Code and Codex plugins
8. **security/settings.py** -- pydantic-settings for environment-backed credential loading

### Critical Pitfalls

1. **XSD validation is syntactic-only, not sufficient** -- Tableau docs state XSD cannot guarantee a workbook opens. Must implement semantic validation (reference checks, calc names, sheet targets) as a mandatory second tier. Do not defer this.
2. **Freehand XML generation produces broken workbooks** -- The TWB format has undocumented conventions the XSD does not capture. Always patch known-good templates via lxml, never construct XML from scratch.
3. **TWB version string / XSD filename mismatch** -- Version 26.1 in TWB XML corresponds to XSD file twb_2026.1.0.xsd. Derive the mapping programmatically; never allow independent setting.
4. **TWBX zip structure is undocumented** -- Official schemas do not cover packaged workbooks. Reverse-engineer the structure from reference .twbx files produced by Tableau Desktop; integration test against them.
5. **Document API is unsupported As-Is** -- Cannot create files from scratch, last release Nov 2022. Use lxml directly for all XML manipulation; limit Document API to optional read-only inspection.

## Implications for Roadmap

Based on research, the following phase structure is recommended:

### Phase 1: Foundation and Core Generation
**Rationale:** The spec schema is the foundation that everything else consumes. Without typed Pydantic models, no other component can function. The TWB generator is the core value proposition -- it must produce output before validation is meaningful.
**Delivers:** Working generate command that takes a YAML spec and a template, produces a .twb file, and validates it against pinned XSD.
**Addresses:** YAML spec input, template-based generation, XSD validation, CLI interface, deterministic output
**Avoids:** Freehand XML generation (Pitfall 3), XSD version mismatch (Pitfall 2), Document API dependency (Pitfall 5)
**Build order:** spec/models.py -> spec/io.py -> security/settings.py -> templates/registry.py -> twb/manifest.py -> twb/generator.py -> validation/xsd.py -> cli.py (generate + validate-xsd commands)

### Phase 2: Semantic Validation and Packaging
**Rationale:** XSD validation alone gives false confidence. Semantic validation is the hard correctness problem that makes the tool trustworthy. Packaging enables .twbx output, which is required before publishing is meaningful.
**Delivers:** validate-semantic command, package command, and integration tests that verify the full generate-validate-package pipeline.
**Addresses:** Semantic validation, .twbx packaging, error messages pointing to spec locations
**Avoids:** False XSD confidence (Pitfall 1), broken TWBX structure (Pitfall 4), namespace corruption (Pitfall 9), template-field mismatch (Pitfall 12)
**Build order:** validation/semantic.py -> twb/packager.py -> qa/static.py -> cli.py (validate-semantic + package + qa static commands)

### Phase 3: Publishing and Server Integration
**Rationale:** Publishing completes the end-to-end pipeline. It depends on both packaging (for .twbx) and validation (for confidence in what is published). TSC handles the heavy lifting, but credential handling and chunked upload require careful design.
**Delivers:** publish command with PAT auth, chunked upload for large files, async publish mode, and TSC session management.
**Addresses:** Tableau Server publishing, connection credential handling, overwrite protection
**Avoids:** Publish timeout on large files (Pitfall 6), credential handling errors (Pitfall 7), TSC version mismatch (Pitfall 10), overwrite without backup (Pitfall 11), session leaks (Pitfall 15), TWB vs TWBX publish differences (Pitfall 16)
**Build order:** publisher/tsc_client.py -> publisher/rest_client.py -> qa/server.py -> cli.py (publish + report commands)

### Phase 4: Agent Plugin Integration
**Rationale:** Agent skills are a composition layer that wraps CLI commands. They depend on the CLI being functional and stable. Building them last ensures the skills wrap a proven pipeline rather than influencing its design.
**Delivers:** Five SKILL.md files, dual plugin manifests (Claude Code + Codex), agent-facing documentation.
**Addresses:** Dual AI agent plugins, shared skills, plugin manifests
**Avoids:** Agent generating invalid specs (phase warning), incorrect plugin manifests
**Build order:** skills/ (5 SKILL.md files) -> .claude-plugin/plugin.json -> .codex-plugin/plugin.json -> AGENTS.md + CLAUDE.md

### Phase 5: Polish and Extensions
**Rationale:** Quality-of-life features that improve the developer experience but are not part of the core generation pipeline.
**Delivers:** spec init scaffolding, spec schema documentation generation, template registry governance, multi-version Tableau support.
**Addresses:** Onboarding, documentation, template governance
**Build order:** spec init command -> Pydantic JSON Schema export -> template compatibility profiles -> version compatibility matrix

### Phase Ordering Rationale

- **Spec schema first** because every other module (generator, validator, publisher) consumes typed DashboardSpec objects. This is the root of the dependency tree.
- **Generation before validation** because validating nothing is useless. The generator must produce output before validators have anything to check.
- **Semantic validation alongside packaging** because both operate on generator output and are independent of each other. They can be built in parallel within the phase.
- **Publishing after packaging** because you cannot publish a .twbx that does not exist yet, and publishing unvalidated workbooks would erode trust.
- **Agent skills last** because they are a composition layer. They invoke CLI commands and should not constrain the engine design.

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 2 (Semantic Validation):** The semantic validator must cover sheet references, calc field names, action targets, and field references. The exact set of checks depends on reverse-engineering Tableau failure modes from known-broken TWBs. Needs dedicated research into which semantic errors are most common and how to detect them.
- **Phase 3 (Publishing):** TSC chunked upload, async publish, and connection credential handling have edge cases that require testing against a live Tableau Server instance. The REST fallback needs research into which TSC parity gaps exist.
- **Phase 4 (Agent Skills):** Skill prompt design is emergent -- each SKILL.md must be tested iteratively with actual agent sessions. No amount of upfront research replaces prompt engineering iteration.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation + Generation):** Pydantic models, lxml XML patching, and Typer CLI are all well-documented patterns. The template-first approach is validated by official Tableau docs. No research needed.
- **Phase 5 (Polish):** JSON Schema export, scaffolding, and template governance are standard patterns. No domain-specific research required.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All technologies verified on PyPI with current versions. Official Tableau libraries confirmed. No untested combinations. |
| Features | HIGH | Ecosystem analysis confirms no competing tools exist. Feature list derived from official infrastructure gaps. Anti-features validated against official documentation. |
| Architecture | HIGH | Template-first approach validated by official tableau-document-schemas README. Gated pipeline pattern is standard for code-generation tools. Component boundaries are clean. |
| Pitfalls | HIGH | All critical pitfalls sourced from official Tableau documentation (XSD README, TSC API reference, REST API reference, Document API README). No inference or speculation needed. |

**Overall confidence:** HIGH

### Gaps to Address

- **Semantic validator completeness:** Research cannot fully enumerate which semantic checks are needed. The validator will need iterative extension as users encounter XSD-passes-but-Tableau-fails errors. Design the validator for easy addition of new rules from day one.
- **TWBX internal structure:** The exact zip layout (directory nesting, metadata entries) must be reverse-engineered from reference .twbx files produced by Tableau Desktop. Research confirms the official schemas do not cover this. Address by comparing against reference files during Phase 2 implementation.
- **Agent skill effectiveness:** SKILL.md prompt quality determines whether agents correctly invoke the CLI. This requires iterative testing with real agent sessions during Phase 4. No amount of upfront research replaces this.
- **Tableau Server version compatibility matrix:** The toolkit targets Tableau 2026.1 initially. Support for earlier versions depends on maintaining compatible template sets and XSD snapshots. The exact version boundaries need testing against real Tableau Server instances.

## Sources

### Primary (HIGH confidence)
- tableau/tableau-document-schemas -- Official XSDs, syntactic vs semantic validation limits, ManifestByVersion guidance, processContents skip, no TWBX support
- tableau/server-client-python -- TSC v0.40, publish API, PAT auth, chunked upload, session management
- tableau/document-api-python -- As-Is status, no creation from scratch, last release Nov 2022
- Tableau REST API reference -- 64 MB limit, multipart format, overwrite behavior, connection credentials, asJob, skipConnectionCheck
- PyPI -- Version verification for pydantic, typer, lxml, pyyaml, pytest, ruff, mypy, tableauserverclient

### Secondary (MEDIUM confidence)
- GitHub search for tableau twb generator and tableau yaml dashboard -- confirms no competing tools exist in the space
- GitHub topic tableau-automation -- confirms the programmatic authoring niche is unoccupied
- Deep research report at ~/Downloads/deep-research-report.md -- project-specific blueprint covering architecture, spec schema, skills matrix, risk register

---
*Research completed: 2026-05-08*
*Ready for roadmap: yes*
