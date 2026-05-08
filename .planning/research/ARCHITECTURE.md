# Architecture Research

**Domain:** Tableau workbook generation toolkit with agent plugin support
**Researched:** 2026-05-08
**Confidence:** HIGH

## Standard Architecture

This is a four-layer pipeline system. Each layer is a distinct buildable unit with clear inputs and outputs. The layers are: spec ingestion, workbook generation, validation/QA, and publishing. A fifth cross-cutting layer provides the CLI and agent plugin interfaces.

### System Overview

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Interface Layer (CLI + Agent Skills)                 │
│  ┌──────────────┐  ┌──────────────────┐  ┌──────────────────────┐        │
│  │  Typer CLI   │  │ Claude Plugin    │  │  Codex Plugin        │        │
│  │  (typer app) │  │ (.claude-plugin/)│  │  (.codex-plugin/)    │        │
│  └──────┬───────┘  └───────┬──────────┘  └──────────┬──────────┘        │
│         │                  │                         │                    │
│         └──────────────────┴─────────────────────────┘                    │
│                            │ delegates to                               │
├────────────────────────────┴────────────────────────────────────────────┤
│                      Spec Ingestion Layer                                 │
│  ┌─────────────────┐  ┌───────────────────┐  ┌────────────────────┐     │
│  │ Pydantic v2     │  │ YAML I/O          │  │ Security Settings  │     │
│  │ Models          │  │ (load/dump spec)  │  │ (env-backed creds) │     │
│  └────────┬────────┘  └─────────┬─────────┘  └────────────────────┘     │
│           │                     │                                         │
├───────────┴─────────────────────┴─────────────────────────────────────────┤
│                      Workbook Generation Layer                            │
│  ┌─────────────────┐  ┌───────────────────┐  ┌────────────────────┐     │
│  │ Template         │  │ TWB Generator     │  │ Manifest/Version   │     │
│  │ Registry         │──>│ (lxml patcher)    │──>│ Handler            │     │
│  └─────────────────┘  └─────────┬─────────┘  └────────────────────┘     │
│                                 │                                         │
├─────────────────────────────────┴─────────────────────────────────────────┤
│                      Validation + QA Layer                                │
│  ┌─────────────────┐  ┌───────────────────┐  ┌────────────────────┐     │
│  │ XSD Validator    │  │ Semantic Validator │  │ TWBX Packager      │     │
│  │ (pinned XSDs)   │  │ (ref/calc checks) │  │ (zip packaging)    │     │
│  └─────────────────┘  └───────────────────┘  └────────────────────┘     │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                      Publishing Layer                                     │
│  ┌─────────────────┐  ┌───────────────────┐  ┌────────────────────┐     │
│  │ TSC Publisher    │  │ REST Fallback     │  │ QA Server Checks   │     │
│  │ (primary)       │  │ (edge cases)      │  │ (preview/PDF/meta) │     │
│  └─────────────────┘  └───────────────────┘  └────────────────────┘     │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                      External Assets (read-only, vendored)                │
│  ┌──────────────────────┐  ┌─────────────────────────────────────────┐   │
│  │ third_party/          │  │ templates/                              │   │
│  │ tableau_document_     │  │ (source .twb templates + catalog.yaml)  │   │
│  │ schemas/ (XSDs)       │  │                                         │   │
│  └──────────────────────┘  └─────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| `spec.models` | Strong-typed Pydantic v2 models for `dashboard_spec.yaml` schema | Pydantic BaseModel with validators for version, template ID, datasources, worksheets, dashboards, publish config, QA config |
| `spec.io` | Load/save YAML spec files; validate on load | `pyyaml` or `ruamel.yaml` for YAML round-tripping; calls `spec.models` for validation |
| `templates.registry` | Template lookup, compatibility checking, version matching against target Tableau version | `TemplateRegistry` class with `resolve(template_id, tableau_version)` method; reads `templates/catalog.yaml` |
| `twb.generator` | Core XML patching engine -- takes spec + template, produces `.twb` output | `lxml.etree` for XML parsing/editing; template-first patching (never freehand XML creation) |
| `twb.manifest` | Write `<ManifestByVersion />` and version attributes consistently | Sets `version`, `original-version`, `source-build`, `source-platform` on `<workbook>` root element |
| `twb.packager` | Package `.twb` + assets into `.twbx` (ZIP archive) | Python `zipfile` module; validates inner `.twb` + asset integrity |
| `validation.xsd` | Structural validation against pinned `tableau-document-schemas` XSDs | `lxml.etree.XMLSchema` with error collection; pinned XSDs in `third_party/` |
| `validation.semantic` | Reference integrity checks beyond XSD -- sheet refs, calc names, action targets, field references | Custom Python validators; iterates XML tree and cross-references spec declarations |
| `publisher.tsc_client` | Primary publisher using Tableau Server Client (TSC) | `tableauserverclient` library; PAT auth; handles chunked uploads, project resolution, overwrite/create modes |
| `publisher.rest_client` | Fallback publisher using raw Tableau REST API | `httpx` or `requests`; mirrors TSC behavior for edge cases where TSC has parity gaps |
| `qa.static` | Non-server QA checks: spec completeness, template anchor presence, packaging preconditions | Pure Python checks; no server dependency |
| `qa.server` | Server-dependent QA: sandbox publish, preview PNG, PDF export, metadata sanity checks | TSC for image/PDF export; optional Metadata API (GraphQL) for metadata checks |
| `cli` | Typer-based CLI exposing all commands to users | Typer app with subcommands: `spec init`, `generate`, `validate-xsd`, `validate-semantic`, `qa static`, `package`, `publish`, `report` |
| `security.settings` | Environment-backed credential loading, no secrets in YAML/templates | `pydantic-settings` BaseSettings; reads from env vars, `.env` files, or CI secrets |

## Recommended Project Structure

```
tableau-agent-toolkit/
├── src/
│   └── tableau_agent_toolkit/
│       ├── __init__.py                 # Package init, version
│       ├── cli.py                      # Typer CLI entry point
│       ├── spec/
│       │   ├── __init__.py
│       │   ├── models.py              # Pydantic v2: DashboardSpec, WorkbookSpec, DatasourceSpec, etc.
│       │   └── io.py                  # load_spec(), dump_spec()
│       ├── templates/
│       │   ├── __init__.py
│       │   └── registry.py            # TemplateRegistry class
│       ├── twb/
│       │   ├── __init__.py
│       │   ├── generator.py           # WorkbookGenerator class
│       │   ├── manifest.py            # apply_manifest_by_version()
│       │   └── packager.py            # package_twbx()
│       ├── validation/
│       │   ├── __init__.py
│       │   ├── xsd.py                 # XsdValidator class
│       │   └── semantic.py            # SemanticValidator class
│       ├── publisher/
│       │   ├── __init__.py
│       │   ├── tsc_client.py          # TSC publisher (primary)
│       │   └── rest_client.py         # REST publisher (fallback)
│       ├── qa/
│       │   ├── __init__.py
│       │   ├── static.py              # run_static_qa()
│       │   └── server.py              # run_server_qa()
│       └── security/
│           ├── __init__.py
│           └── settings.py            # pydantic-settings for PAT/JWT
├── skills/                             # Shared agent skill directories
│   ├── tableau-dashboard-spec-writer/
│   │   └── SKILL.md
│   ├── tableau-twb-generator/
│   │   └── SKILL.md
│   ├── tableau-twb-validator/
│   │   └── SKILL.md
│   ├── tableau-dashboard-qa-reviewer/
│   │   └── SKILL.md
│   └── tableau-publisher/
│       └── SKILL.md
├── .claude-plugin/
│   └── plugin.json                    # Claude Code plugin manifest
├── .codex-plugin/
│   └── plugin.json                    # Codex plugin manifest
├── templates/                          # Source .twb templates + metadata
│   ├── catalog.yaml                   # Template registry: IDs, versions, anchors, compatibility
│   └── finance/
│       └── reconciliation_template.twb
├── third_party/
│   └── tableau_document_schemas/      # Pinned upstream XSD snapshots
│       ├── README.md                  # Provenance note + refresh instructions
│       └── schemas/
│           └── 2026_1/
│               └── twb_2026.1.0.xsd
├── examples/
│   ├── specs/                         # Example dashboard_spec.yaml files
│   │   ├── finance-reconciliation.dashboard_spec.yaml
│   │   ├── executive-kpi.dashboard_spec.yaml
│   │   └── ops-monitoring.dashboard_spec.yaml
│   └── sql/                           # Example custom SQL files
│       └── finance_reconciliation.sql
├── scripts/
│   └── sync_tableau_schemas.py        # Refresh pinned XSDs from upstream
├── tests/
│   ├── fixtures/                      # Template fixtures, expected XML, test assets
│   ├── unit/                          # Unit tests per module
│   ├── integration/                   # Integration tests with fixture templates
│   └── smoke/                         # Opt-in sandbox publish smoke tests
├── docs/
│   ├── architecture.md
│   ├── dashboard-spec.md
│   └── release-checklist.md
├── AGENTS.md                          # Codex repo-level instructions
├── CLAUDE.md                          # Claude Code repo-level instructions
├── pyproject.toml                     # Build config, dependencies, entry point
├── LICENSE                            # Apache-2.0
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

### Structure Rationale

- **`src/tableau_agent_toolkit/` (src layout):** Prevents accidental imports during development. Standard Python packaging practice. Each sub-package (`spec/`, `twb/`, `validation/`, etc.) is a self-contained module with a single responsibility.
- **`skills/` at repo root:** Both Claude Code and Codex expect skill directories with `SKILL.md` files. Placing them at the root makes them discoverable by both plugin manifests. Skills are not inside the Python package because they are consumed by agents, not by Python code.
- **`templates/` outside `src/`:** Templates are data files (`.twb` XML + `catalog.yaml`), not Python code. They ship with the package via `pyproject.toml` `package-data` but live outside `src/` for clarity.
- **`third_party/` with provenance:** Vendored XSDs must carry their own license and provenance documentation. The `sync_tableau_schemas.py` script automates refresh from the upstream `tableau/tableau-document-schemas` repo.
- **`tests/` mirrors `src/`:** Unit tests in `tests/unit/` mirror the `src/tableau_agent_toolkit/` structure. Integration tests use fixtures from `tests/fixtures/`. Smoke tests require secrets and are opt-in.
- **Dual plugin manifests:** `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` are separate because each agent platform has its own manifest schema, even though they both point at the same `skills/` tree.

## Architectural Patterns

### Pattern 1: Template-First Generation (Patch, Don't Create)

**What:** The generator never creates Tableau XML from scratch. It loads a known-good `.twb` template and patches specific elements (datasources, worksheets, dashboards, calculations, parameters) using `lxml.etree` XPath queries and element manipulation.

**When to use:** Always. This is the core architectural decision. Tableau's official XSD documentation explicitly states that XSD validation is syntactic only and does not guarantee semantic validity. Freehand XML authoring would produce XML that passes XSD but fails to open in Tableau.

**Trade-offs:**
- Pro: Deterministic output. Same spec + template + XSD version = same `.twb` every run.
- Pro: Leverages Tableau's own template format. Templates created in Tableau Desktop are guaranteed semantically valid as a starting point.
- Con: Requires maintaining a template library. Each dashboard pattern needs a known-good template.
- Con: Less flexibility than freehand authoring. Can only produce variations that templates support.

**Example:**
```python
# twb/generator.py -- core generation pattern
from lxml import etree
from tableau_agent_toolkit.spec.models import DashboardSpec
from tableau_agent_toolkit.templates.registry import TemplateRegistry
from tableau_agent_toolkit.twb.manifest import apply_manifest_by_version

class WorkbookGenerator:
    def __init__(self, template_registry: TemplateRegistry) -> None:
        self.template_registry = template_registry

    def generate(self, spec: DashboardSpec, output_path: Path) -> GenerationResult:
        # 1. Resolve template by ID + target Tableau version
        template = self.template_registry.resolve(
            spec.workbook.template.id,
            spec.workbook.target_tableau_version,
        )

        # 2. Parse known-good template into lxml tree
        tree = etree.parse(str(template.path))

        # 3. Apply version and manifest consistently
        apply_manifest_by_version(tree, spec.workbook.target_tableau_version)

        # 4. Patch sections using XPath-based element manipulation
        self._patch_workbook_name(tree, spec.workbook.name)
        self._patch_datasources(tree, spec)
        self._patch_calculations(tree, spec)
        self._patch_worksheets(tree, spec)
        self._patch_dashboards(tree, spec)

        # 5. Write output
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)
        return GenerationResult(output_path=output_path, warnings=[])
```

### Pattern 2: Gated Pipeline (Factory with Quality Gates)

**What:** Workbook generation is a linear pipeline with explicit quality gates between stages. A workbook must pass XSD validation before semantic validation, must pass semantic validation before packaging, and must pass packaging checks before publishing.

**When to use:** Always. This prevents false confidence where XSD passes but the workbook is broken in Tableau.

**Trade-offs:**
- Pro: Catches issues early. Each gate prevents wasted work in later stages.
- Pro: Clear error reporting. Failures are attributed to the specific stage that detected them.
- Con: Cannot skip stages. If you want to publish, you must validate first. (This is intentional -- it is a feature, not a bug.)

**Example -- pipeline flow:**
```python
# Conceptual pipeline orchestration (not literal code)
def run_full_pipeline(spec_path: Path) -> PipelineResult:
    spec = load_spec(spec_path)              # Gate: spec schema validation
    result = generator.generate(spec, out)    # Gate: generation succeeds
    xsd_validator.validate(out, version)      # Gate: structural validity
    semantic_validator.validate(tree, spec)   # Gate: reference integrity
    package_twbx(out, assets, out_twbx)       # Gate: package integrity
    publisher.publish(out_twbx, spec.publish)  # Gate: publish succeeds
    return PipelineResult(success=True)
```

### Pattern 3: Separate Validation Tiers

**What:** Three distinct validation tiers, each catching different classes of errors:
1. **Spec validation** (Pydantic) -- catches malformed YAML, missing required fields, type errors.
2. **XSD validation** (lxml + pinned XSDs) -- catches structural XML errors, invalid element nesting, missing required attributes.
3. **Semantic validation** (custom Python) -- catches broken references: sheet names referenced in dashboards that do not exist, calculated field formulas referencing non-existent columns, action targets pointing to wrong objects.

**When to use:** Always. Tableau's XSD explicitly does not validate: connection attributes, calculated field contents, or references to named workbook objects. The semantic validator fills this gap.

**Trade-offs:**
- Pro: Catches the most common cause of "XSD passes but workbook fails in Tableau."
- Con: The semantic validator must be maintained as Tableau evolves. It will never be 100% complete.
- Con: False negatives possible -- semantic validator cannot catch all semantic errors (e.g., a formula that is syntactically valid but returns wrong results).

### Pattern 4: Dual Plugin with Shared Skills

**What:** A single `skills/` directory contains five `SKILL.md` files that both Claude Code and Codex consume. Each agent platform gets its own plugin manifest (`.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`) that points at the shared skills tree. Platform-specific behavior lives in the manifest, not in skill text.

**When to use:** When supporting multiple agent platforms from a single repo. Avoids skill duplication and drift.

**Trade-offs:**
- Pro: Single source of truth for skill instructions. Update once, both platforms get the change.
- Pro: Simpler maintenance. No need to keep two skill trees in sync.
- Con: Limited to the lowest common denominator of both plugin systems. If one platform supports a feature the other does not, that feature cannot be used in shared skills.
- Con: Each platform's manifest must be tested independently.

**Example -- Claude Code SKILL.md structure:**
```yaml
# skills/tableau-twb-generator/SKILL.md
---
name: tableau-twb-generator
description: Use when the user wants to generate or patch a Tableau workbook
  from dashboard_spec.yaml and a known-good template.
---
Load the spec, resolve the matching template, and generate a .twb draft.
Write workbook version and document manifest consistently with the selected
Tableau version. Prefer template patching over freehand XML creation.
Return changed files, warnings, and the output path.
```

### Pattern 5: Version Pinning with ManifestByVersion

**What:** The toolkit always writes `<ManifestByVersion />` inside `<document-format-change-manifest>` and pins both the workbook `version`/`original-version` attributes and the XSD validation schema to the target Tableau version from the spec. Earlier Tableau versions are supported through template passthrough profiles, not by attempting XML down-conversion.

**When to use:** Always. Tableau's official documentation recommends `<ManifestByVersion />` for direct workbook authoring. Version mismatches between the TWB XML and the XSD used for validation produce false results.

**Trade-offs:**
- Pro: Reproducible. Same inputs always produce the same output.
- Pro: Matches Tableau's official guidance for programmatic workbook authoring.
- Con: Must maintain XSD snapshots for each supported Tableau version.
- Con: Cannot generate workbooks for Tableau versions newer than the newest pinned XSD.

## Data Flow

### Primary Generation Flow

```
dashboard_spec.yaml
       |
       v
  [spec.io: load_spec()]
       |
       v
  [spec.models: Pydantic validation] -- FAIL --> spec validation error report
       |
       v (DashboardSpec object)
  [templates.registry: resolve(template_id, version)]
       |
       v (template path)
  [twb.generator: parse template .twb with lxml]
       |
       v (lxml ElementTree)
  [twb.manifest: apply version + ManifestByVersion]
       |
       v
  [twb.generator: patch datasources, calcs, worksheets, dashboards]
       |
       v (patched ElementTree)
  [write output .twb]
       |
       v
  [validation.xsd: validate against pinned XSD] -- FAIL --> XSD error report
       |
       v (passes XSD)
  [validation.semantic: check references] -- FAIL --> semantic error report
       |
       v (passes semantic)
  output.twb ready for packaging or direct use
```

### Packaging + Publishing Flow

```
output.twb + asset files
       |
       v
  [twb.packager: create .twbx ZIP] -- FAIL --> packaging error
       |
       v (output.twbx)
  [qa.static: pre-publish checks]
       |
       v
  [publisher.tsc_client: PAT auth + publish]
       |                                    \
       v (publish succeeds)                  v (TSC fails)
  [qa.server: optional smoke checks]    [publisher.rest_client: fallback]
       |
       v
  publish receipt + workbook metadata
```

### Agent Skill Invocation Flow

```
User prompt in Claude Code or Codex
       |
       v
  [Agent matches prompt to skill description in SKILL.md]
       |
       v
  [Agent loads SKILL.md + supporting files]
       |
       v
  [Agent calls CLI commands or Python API directly]
       |                           |
       v                           v
  [tableau-agent-toolkit CLI]  [Python module imports]
       |                           |
       v                           v
  [Same pipeline: spec -> generate -> validate -> publish]
       |
       v
  [Agent reads output files, reports results to user]
```

### Key Data Flows

1. **Spec loading:** `dashboard_spec.yaml` -> `spec.io.load_spec()` -> Pydantic model validation -> `DashboardSpec` object. All downstream modules receive the typed `DashboardSpec` object, never raw YAML.

2. **Template resolution:** `DashboardSpec.workbook.template.id` + `target_tableau_version` -> `TemplateRegistry.resolve()` -> `TemplateMatch` (path, compatibility info, required anchors). The registry reads `templates/catalog.yaml` to find matching templates and verifies version compatibility.

3. **XML patching:** Template `.twb` file -> `lxml.etree.parse()` -> XPath-based element manipulation (datasources, worksheets, dashboards, calculations) -> `tree.write()` -> output `.twb`. Each patch operation is a separate method on `WorkbookGenerator` for testability.

4. **Validation pipeline:** Output `.twb` -> XSD validation (`lxml.etree.XMLSchema`) -> semantic validation (custom Python cross-referencing) -> validation report. XSD validation reads from `third_party/tableau_document_schemas/`. Semantic validation reads both the XML tree and the original `DashboardSpec`.

5. **Credential flow:** Environment variables or `.env` file -> `pydantic-settings.BaseSettings` -> publisher auth. Credentials never appear in spec YAML, templates, or plugin manifests.

## Component Boundaries

| Boundary | Communication Method | Data Contract |
|----------|---------------------|---------------|
| CLI -> spec module | Direct Python function call | `DashboardSpec` Pydantic model |
| CLI -> twb module | Direct Python function call | `DashboardSpec` + `Path` -> `GenerationResult` |
| CLI -> validation module | Direct Python function call | `Path` (twb) + `str` (version) -> `ValidationReport` |
| CLI -> publisher module | Direct Python function call | `Path` (twb/twbx) + `PublishSpec` -> `PublishResult` |
| Agent skills -> CLI | Shell command execution (agent runs CLI commands) | String args, stdout/stderr capture |
| Agent skills -> Python API | Direct module import (agent can import the package) | Same as CLI boundaries |
| twb.generator -> templates.registry | Constructor injection (`TemplateRegistry` passed in) | `TemplateMatch` dataclass |
| twb.generator -> validation.xsd | Constructor injection (`XsdValidator` passed in) | None (generator calls validator) |
| publisher.tsc_client -> Tableau Server | HTTPS REST API via `tableauserverclient` | TSC library handles serialization |
| publisher.rest_client -> Tableau Server | HTTPS REST API via `httpx`/`requests` | Manual request construction |
| validation.xsd -> third_party XSDs | File read (`lxml.etree.parse` on XSD file) | XSD files on local filesystem |

### Dependency Direction Rules

1. **No upward dependencies.** Lower layers never import from higher layers. The spec module does not import from the generator. The generator does not import from the publisher.
2. **No cross-layer shortcuts.** The publisher does not call the generator. Each layer receives its inputs from the caller (CLI or orchestrator).
3. **External assets are read-only.** The Python code reads from `templates/` and `third_party/` but never writes to them. The `sync_tableau_schemas.py` script is the only thing that modifies `third_party/`.
4. **Agent skills are consumers, not dependencies.** The Python package has no import dependency on `skills/` or plugin manifests. Skills invoke the Python package via CLI or import.

## Build Order

The dependency graph between components determines what must be built first. This is the recommended implementation order for the roadmap.

```
Build Order (dependencies flow downward):

Phase 1 -- Foundation (no internal dependencies)
    1. spec/models.py          -- Pydantic models (standalone, no deps)
    2. spec/io.py              -- YAML I/O (depends on models only)
    3. security/settings.py    -- pydantic-settings (standalone)

Phase 2 -- Generation (depends on Phase 1)
    4. templates/registry.py   -- template lookup (depends on spec models for version info)
    5. twb/manifest.py         -- version/manifest writing (depends on spec models for version)
    6. twb/generator.py        -- XML patching engine (depends on registry + manifest + spec)
    7. validation/xsd.py       -- XSD validation (depends on spec models for version)

Phase 3 -- Validation + Packaging (depends on Phase 2)
    8. validation/semantic.py  -- reference checks (depends on spec models + generator output)
    9. twb/packager.py         -- .twbx creation (depends on generator output)

Phase 4 -- Publishing + QA (depends on Phase 3)
   10. publisher/tsc_client.py -- TSC publisher (depends on security/settings + packager output)
   11. publisher/rest_client.py-- REST fallback (depends on security/settings)
   12. qa/static.py            -- static QA checks (depends on spec + generator + validation)
   13. qa/server.py            -- server QA (depends on publisher + TSC)

Phase 5 -- Interface (depends on all above)
   14. cli.py                  -- Typer commands (depends on all modules)
   15. Agent skills            -- SKILL.md files (depends on CLI being functional)
   16. Plugin manifests        -- JSON manifests (depends on skills existing)
```

### Build Order Implications for Roadmap

| Phase | Builds | Why This Order |
|-------|--------|----------------|
| v0.1 MVP | Phase 1-2 + Phase 5 (CLI + skills skeleton) | Spec models and generator are the core value. Ship a working `generate` command with XSD validation. Include skill skeletons and plugin manifests so agents can invoke the toolkit. |
| v0.2 | Phase 3 + Phase 4 (partial: TSC publisher, PAT auth, packager) | Add packaging, publishing, and static semantic QA. This is the "factory" completion. |
| v0.3 | Phase 4 (remaining: server QA, preview/PDF, metadata checks) | Add server-dependent QA. Requires a live Tableau instance for testing, so it comes after the publisher works. |
| v0.4 | Optional MCP wiring, JWT auth, marketplace packaging | These are extensions that depend on the core pipeline being stable. |

## Anti-Patterns

### Anti-Pattern 1: Freehand XML Authoring

**What people do:** Generate Tableau workbook XML from scratch using string templates or XML builders, relying on XSD validation to catch errors.

**Why it is wrong:** Tableau's official XSD documentation states that XSD validation is syntactic only. It does not validate connection attributes, calculated field contents, or references to named workbook objects. A workbook that passes XSD can still fail to open in Tableau. The XSD even uses `processContents="skip"` for many elements, meaning the validator ignores their content entirely.

**Do this instead:** Always start from a known-good template created in Tableau Desktop. Patch specific elements using `lxml` XPath queries. Validate with XSD for structure, then run custom semantic validators for reference integrity.

### Anti-Pattern 2: Using Document API as Core Engine

**What people do:** Build the entire generation engine on top of `tableau/document-api-python`.

**Why it is wrong:** The Document API is labeled "As-Is" and unsupported. Its own README says it does not support creating files from scratch. The last release (v0.11) was November 2022. It is useful for selective inspection and connection patching on existing workbooks, but it is not a foundation for a generation engine.

**Do this instead:** Use `lxml` directly for XML parsing and manipulation. This gives full control over the XML tree without depending on an unsupported library's abstractions. The Document API can be an optional dependency for users who want its convenience methods for specific inspection tasks.

### Anti-Pattern 3: Treating XSD Validation as Sufficient

**What people do:** Run XSD validation, see "valid", and ship the workbook.

**Why it is wrong:** Tableau's own documentation explicitly warns that XSD validation cannot guarantee a workbook will open in Tableau. The most common real-world failures are broken references (sheet names, calculated field names, action targets) that XSD does not check.

**Do this instead:** Layer validation: (1) XSD for structure, (2) custom semantic validator for references, (3) optional sandbox publish smoke test for runtime verification. Never claim "validated" based on XSD alone.

### Anti-Pattern 4: Secrets in Spec Files

**What people do:** Put database passwords, PAT tokens, or API keys directly in `dashboard_spec.yaml` or `catalog.yaml`.

**Why it is wrong:** These files are committed to git. Even in private repos, secrets in config files are a leak risk. They also make specs non-portable -- a spec with hardcoded credentials cannot be shared across environments.

**Do this instead:** Use `pydantic-settings` to load credentials from environment variables or `.env` files. The spec can reference credential names (e.g., `server_env: "TABLEAU_DB_HOST"`) but never contains actual values.

### Anti-Pattern 5: Monolithic Generator

**What people do:** Put all XML patching logic (datasources, worksheets, dashboards, calculations, parameters, manifest) in a single function or class.

**Why it is wrong:** Tableau XML is complex and deeply nested. A monolithic generator becomes unmaintainable quickly. Each patch operation (datasources vs worksheets vs dashboards) has different XPath patterns, different edge cases, and different test requirements.

**Do this instead:** Separate patch operations into distinct methods on the generator class (`_patch_datasources`, `_patch_worksheets`, `_patch_dashboards`, `_patch_calculations`). Each method can be unit-tested independently with a minimal XML fixture.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user / small team | Monolithic Python package is ideal. CLI + local templates. No server required for generation or validation. |
| Team / CI pipeline | Add GitHub Actions CI. Template registry grows. Snapshot tests for generated XML. Smoke tests gated on secrets. |
| Enterprise / multi-team | Template catalog becomes a shared resource. Consider template storage in a centralized location (S3, Artifactory). Publisher may need connection update batching. Metadata API checks across many workbooks. |

### Scaling Priorities

1. **First bottleneck: Template library maintenance.** As the template catalog grows, managing compatibility across Tableau versions becomes the primary maintenance burden. Mitigate with automated compatibility checks in the registry and `sync_tableau_schemas.py` for XSD updates.

2. **Second bottleneck: Semantic validator coverage.** The custom semantic validator will always be incomplete. As users encounter new classes of "XSD passes but Tableau fails" errors, the validator must be extended. Design it for easy addition of new check rules.

3. **Third bottleneck: Test fixture explosion.** Each template + version combination needs fixture XML for integration tests. Use snapshot testing (compare generated XML against known-good snapshots) to keep this manageable.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Tableau Server / Cloud | `tableauserverclient` Python library (primary) | Handles auth, chunked uploads, project resolution, preview/PDF export. Latest release v0.40 (Feb 2026). MIT licensed. |
| Tableau REST API | `httpx`/`requests` raw HTTP (fallback) | For edge cases where TSC has parity gaps. Must mirror TSC auth flow (PAT sign-in). |
| Tableau Metadata API | GraphQL over REST (optional, in QA layer) | Post-publish metadata sanity checks. Uses same auth token as REST. Not available on all Tableau Server deployments -- must be capability-detected. |
| Tableau MCP | Node.js server (optional, for agent-assisted QA only) | Not a core engine dependency. If used, bundle a `.mcp.json` pointing to the official Tableau MCP server. Requires Node.js 22.7.5+. |
| `tableau-document-schemas` | Vendored XSD files in `third_party/` | Read-only. Refresh via `sync_tableau_schemas.py`. Apache-2.0 licensed. |
| `tableau/document-api-python` | Optional dependency (NOT core) | "As-Is" unsupported. Last release Nov 2022. Use only for selective inspection if users opt in. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI -> Engine modules | Direct Python function calls | CLI is a thin Typer wrapper. Each command calls one or two engine functions. |
| Agent skills -> CLI | Shell command execution | Skills are YAML/markdown instructions that tell the agent which CLI commands to run. |
| Agent skills -> Python API | Direct module import | Advanced usage where agents import and call Python functions directly. |
| Generator -> Template registry | Constructor injection | `WorkbookGenerator.__init__(template_registry, xsd_validator)`. Dependency injection enables testing with mock registries. |
| Publisher -> Security settings | Constructor injection | Publisher receives a `Settings` object with validated credentials. Never reads env vars directly. |
| Validation -> XSD files | File path resolution | XSD files are loaded from `third_party/` by version string. Cached per process. |

## Sources

- [tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas) -- Official XSD repo, version compatibility guidance, ManifestByVersion documentation, syntactic vs semantic validation limits (HIGH confidence)
- [tableau/server-client-python](https://github.com/tableau/server-client-python) -- Official Python library for Tableau Server REST API, v0.40 (Feb 2026), MIT licensed (HIGH confidence)
- [tableau/document-api-python](https://github.com/tableau/document-api-python) -- Unsupported "As-Is" library, last release Nov 2022, does not support creating files from scratch (HIGH confidence)
- [Claude Code Skills Documentation](https://docs.anthropic.com/en/docs/claude-code/skills) -- Skill structure, SKILL.md format, plugin skill distribution, model-invoked discovery (HIGH confidence)
- Deep research report at `~/Downloads/deep-research-report.md` -- Comprehensive blueprint covering architecture, spec schema, repo layout, skills matrix, risk register, and implementation timeline (HIGH confidence -- project-specific design document)

---
*Architecture research for: tableau-agent-toolkit*
*Researched: 2026-05-08*
