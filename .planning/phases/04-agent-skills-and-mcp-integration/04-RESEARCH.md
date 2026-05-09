# Phase 4: Agent Skills and MCP Integration - Research

**Researched:** 2026-05-09
**Domain:** Agent plugin systems (Claude Code, OpenAI Codex), SKILL.md format, MCP configuration, Tableau MCP server
**Confidence:** HIGH

## Summary

Phase 4 wraps the proven CLI pipeline (Phases 1-3) as five composable agent skills with dual plugin manifests for Claude Code and Codex. The core technical deliverable is a set of declarative configuration files (two plugin manifests, five SKILL.md files, one .mcp.json, one CLAUDE.md, one AGENTS.md) that teach agents how to use the existing `tableau-agent-toolkit` CLI commands. No new Python code is required for the core skill mechanics -- skills are Markdown instruction files that tell agents which CLI commands to run and how to interpret their output.

The Claude Code plugin system is well-documented: `.claude-plugin/plugin.json` as manifest, `skills/` directories with `SKILL.md` files, and inline `mcpServers` in plugin.json for MCP integration. The Codex side is less structured -- Codex uses `AGENTS.md` files as its primary instruction mechanism, and `.codex-plugin/plugin.json` as a manifest format. Both platforms share the same underlying skill content (Markdown instructions), differing only in their manifest and discovery mechanisms.

**Primary recommendation:** Create all five skills as SKILL.md files under a shared `skills/` directory, then wire them through platform-specific manifests. Each skill should wrap one or two CLI commands with pre/post instructions, input/output expectations, and error handling guidance.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| MCP-01 | Compatible with official Tableau MCP server for post-publish content exploration | Tableau MCP config format documented (npx @tableau/mcp-server, PAT auth env vars) |
| MCP-02 | Optional `.mcp.json` wiring in plugin manifests to connect to Tableau MCP | .mcp.json format documented; can be embedded inline in plugin.json via mcpServers field |
| MCP-03 | Skills can leverage MCP tools for querying published workbook metadata | Post-publish QA skill can reference MCP tools; MCP provides query_tableau, get_workbook etc. |
| SKILL-01 | `tableau-dashboard-spec-writer` skill -- business brief to dashboard_spec.yaml | Maps to `spec init` CLI + spec model knowledge; skill guides agent through spec authoring |
| SKILL-02 | `tableau-twb-generator` skill -- spec + template to workbook draft | Maps to `generate` CLI command; skill handles pre-checks and output validation |
| SKILL-03 | `tableau-twb-validator` skill -- XSD + semantic validation report | Maps to `validate-xsd` and `validate-semantic` CLI commands; skill chains both |
| SKILL-04 | `tableau-dashboard-qa-reviewer` skill -- static + optional sandbox QA | Maps to `qa static` CLI command; skill interprets report and recommends actions |
| SKILL-05 | `tableau-publisher` skill -- publish validated workbook to Tableau Server/Cloud | Maps to `package` + `publish` CLI commands; skill handles pre-flight checks and receipt interpretation |
| SKILL-06 | Dual plugin manifests -- .claude-plugin/plugin.json and .codex-plugin/plugin.json | Both manifest formats researched; Claude Code uses plugin.json with skills array, Codex uses plugin.json with different schema |
| SKILL-07 | CLAUDE.md and AGENTS.md with project-level instructions for agent workflows | CLAUDE.md already exists (project root); AGENTS.md needs creation for Codex; both provide top-level agent guidance |
</phase_requirements>

## Standard Stack

### Core (Declarative -- No Runtime Libraries)

| Component | Format | Purpose | Why Standard |
|-----------|--------|---------|--------------|
| `.claude-plugin/plugin.json` | JSON | Claude Code plugin manifest | Official Claude Code plugin format [CITED: docs.anthropic.com/en/docs/claude-code/plugins] |
| `skills/*/SKILL.md` | Markdown + YAML frontmatter | Agent skill definitions | Official SKILL.md format for Claude Code [CITED: docs.anthropic.com/en/docs/claude-code/skills] |
| `.mcp.json` | JSON | MCP server configuration | Official Claude Code MCP config [CITED: docs.anthropic.com/en/docs/claude-code/mcp] |
| `AGENTS.md` | Markdown | Codex agent instructions | OpenAI Codex convention [CITED: openai.com/index/codex/] |
| `.codex-plugin/plugin.json` | JSON | Codex plugin manifest | Codex plugin discovery format [ASSUMED] |

### Supporting (Existing Python Stack from Phases 1-3)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typer | 0.25.1 | CLI commands that skills invoke | Every skill wraps CLI commands |
| pydantic | 2.13.4 | Spec models that skills reference | Spec-writer skill needs model knowledge |
| lxml | 6.1.0 | XML processing (skills don't use directly) | Referenced in skill documentation |
| tableauserverclient | 0.40+ | Publishing (skills invoke via CLI) | Publisher skill wraps publish command |

### External Dependencies

| Component | Version | Purpose | When to Use |
|-----------|---------|---------|-------------|
| `@tableau/mcp-server` | latest npm | Tableau MCP server for post-publish QA | MCP-01/MCP-03: optional, for querying published workbooks |

**Installation:**
No Python package installation needed -- all Phase 4 deliverables are declarative configuration and documentation files. The Tableau MCP server is an npm package:
```bash
# Optional: for MCP integration testing
npx @tableau/mcp-server
```

## Architecture Patterns

### Recommended Project Structure
```
tableau-agent-toolkit/
├── .claude-plugin/
│   └── plugin.json              # Claude Code plugin manifest (SKILL-06)
├── .codex-plugin/
│   └── plugin.json              # Codex plugin manifest (SKILL-06)
├── .mcp.json                    # Optional MCP config for Tableau MCP (MCP-02)
├── CLAUDE.md                    # Project-level agent instructions (SKILL-07) -- already exists
├── AGENTS.md                    # Codex agent instructions (SKILL-07) -- to create
├── skills/
│   ├── tableau-dashboard-spec-writer/
│   │   └── SKILL.md             # Skill 1: brief -> spec (SKILL-01)
│   ├── tableau-twb-generator/
│   │   └── SKILL.md             # Skill 2: spec -> twb (SKILL-02)
│   ├── tableau-twb-validator/
│   │   └── SKILL.md             # Skill 3: twb -> validation report (SKILL-03)
│   ├── tableau-dashboard-qa-reviewer/
│   │   └── SKILL.md             # Skill 4: twb -> QA report (SKILL-04)
│   └── tableau-publisher/
│       └── SKILL.md             # Skill 5: twb/twbx -> published (SKILL-05)
├── src/
│   └── tableau_agent_toolkit/   # Existing Python package (Phases 1-3)
├── tests/
│   └── ...                      # Existing tests
└── examples/
    └── specs/                   # Example specs for skill documentation
```

### Pattern 1: SKILL.md with YAML Frontmatter
**What:** Each skill is a Markdown file with YAML frontmatter containing metadata and a Markdown body with instructions.
**When to use:** Every agent skill definition.
**Example:**
```markdown
---
name: tableau-twb-generator
description: Generate a Tableau workbook (.twb) from a YAML spec and template
allowed-tools:
  - Bash
  - Read
  - Write
---

# Tableau TWB Generator

## When to Use
Use this skill when you need to generate a Tableau workbook from a dashboard_spec.yaml file.

## Prerequisites
- A valid `dashboard_spec.yaml` file must exist
- A template `.twb` file must exist or be referenced in the spec
- The `tableau-agent-toolkit` CLI must be installed

## Steps
1. Read and validate the spec file
2. Run the generate command:
   ```bash
   tableau-agent-toolkit generate dashboard_spec.yaml --output output.twb
   ```
3. Verify the output file was created
4. Optionally run validation (see tableau-twb-validator skill)

## Output
- A `.twb` file at the specified output path
- Console output confirming generation or listing warnings

## Error Handling
- If generation fails, check that the template path in the spec is correct
- If warnings appear, review them before proceeding to validation
```
[Source: docs.anthropic.com/en/docs/claude-code/skills]

### Pattern 2: Claude Code Plugin Manifest
**What:** JSON manifest that declares the plugin and references its skills.
**When to use:** Plugin registration for Claude Code.
**Example:**
```json
{
  "name": "tableau-agent-toolkit",
  "description": "Generate, validate, package, and publish Tableau workbooks from YAML specs",
  "version": "0.1.0",
  "skills": [
    "skills/tableau-dashboard-spec-writer",
    "skills/tableau-twb-generator",
    "skills/tableau-twb-validator",
    "skills/tableau-dashboard-qa-reviewer",
    "skills/tableau-publisher"
  ],
  "mcpServers": {
    "tableau": {
      "command": "npx",
      "args": ["-y", "@tableau/mcp-server"],
      "env": {
        "SERVER": "${TABLEAU_SERVER_URL}",
        "SITE_NAME": "${TABLEAU_SITE_NAME}",
        "PAT_NAME": "${TABLEAU_PAT_NAME}",
        "PAT_VALUE": "${TABLEAU_PAT_SECRET}"
      }
    }
  }
}
```
[Source: docs.anthropic.com/en/docs/claude-code/plugins]

Key fields:
- `name`: Plugin identifier
- `description`: Human-readable description shown to agents
- `version`: Semantic version
- `skills`: Array of paths to skill directories (each containing SKILL.md)
- `mcpServers`: Optional inline MCP server definitions (supports MCP-02)

### Pattern 3: MCP Configuration (.mcp.json)
**What:** Standalone MCP server configuration file for Claude Code.
**When to use:** When not using inline plugin.json mcpServers, or for project-level MCP config.
**Example:**
```json
{
  "mcpServers": {
    "tableau": {
      "command": "npx",
      "args": ["-y", "@tableau/mcp-server"],
      "env": {
        "SERVER": "${TABLEAU_SERVER_URL}",
        "SITE_NAME": "${TABLEAU_SITE_NAME}",
        "PAT_NAME": "${TABLEAU_PAT_NAME}",
        "PAT_VALUE": "${TABLEAU_PAT_SECRET}"
      }
    }
  }
}
```
[Source: docs.anthropic.com/en/docs/claude-code/mcp]

Transport types supported:
- **stdio**: Command-based (most common, used by Tableau MCP)
- **http**: HTTP-based server
- **sse**: Server-Sent Events

Environment variable expansion: `${VAR}` or `${VAR:-default}` for optional defaults.

### Pattern 4: AGENTS.md for Codex
**What:** Markdown instruction file that tells Codex agents about project structure and conventions.
**When to use:** Codex agent guidance (equivalent to CLAUDE.md for Claude Code).
**Content structure:**
```markdown
# Tableau Agent Toolkit

## Project Overview
[Description of the project]

## Commands
- Build: `pip install -e .`
- Test: `pytest tests/`
- Lint: `ruff check src/`
- Generate: `tableau-agent-toolkit generate dashboard_spec.yaml --output output.twb`
- Validate: `tableau-agent-toolkit validate-xsd workbook.twb`
- Package: `tableau-agent-toolkit package --input workbook.twb`
- Publish: `tableau-agent-toolkit publish --input workbook.twbx --server URL --project NAME`

## Architecture
[Key modules and their purposes]

## Conventions
[Coding standards, naming, etc.]
```
[Source: openai.com/index/codex/ -- confirms AGENTS.md pattern for guiding Codex agents]

### Anti-Patterns to Avoid

- **Embedding secrets in manifests:** Plugin manifests and SKILL.md files are checked into git. Never embed PAT tokens, API keys, or connection strings directly. Use environment variable references (`${TABLEAU_PAT_SECRET}`) in MCP config. [VERIFIED: CLAUDE.md constraint]
- **Skills that bypass the CLI:** Skills should invoke CLI commands, not import Python modules directly. The CLI is the stable interface; internal Python APIs may change between versions.
- **Monolithic skill files:** Each skill should map to a single pipeline step. Avoid creating one mega-skill that does everything. Composability is the goal.
- **Hardcoded paths in skills:** Use relative paths and environment variables. Agents may run in different working directories.
- **Duplicating CLAUDE.md content in every skill:** Skills should reference project-level instructions, not repeat them. CLAUDE.md provides context; skills provide procedure.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| MCP server for Tableau | Custom MCP server | `@tableau/mcp-server` npm package | Official Tableau MCP server already exists and is maintained |
| Agent instruction format | Custom instruction schema | SKILL.md with YAML frontmatter | Claude Code standard; agents know how to parse it |
| Plugin discovery | Custom plugin registry | `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json` | Platform-standard manifest formats |
| CLI invocation from skills | Subprocess wrappers | Direct CLI command instructions in skill body | Agents can run CLI commands natively via Bash tool |

**Key insight:** Phase 4 is almost entirely declarative. The "code" is Markdown and JSON configuration. The Python CLI already exists from Phases 1-3. The skills are instruction documents that teach agents how to use that CLI.

## Common Pitfalls

### Pitfall 1: Codex Plugin Format Ambiguity
**What goes wrong:** The `.codex-plugin/plugin.json` format is not well-documented publicly. Using incorrect schema may prevent Codex from discovering skills.
**Why it happens:** OpenAI's Codex documentation focuses on AGENTS.md, not plugin.json specifics.
**How to avoid:** Research the Codex plugin format from the official OpenAI Codex repository or examples. If the format cannot be confirmed, use AGENTS.md as the primary Codex mechanism and treat .codex-plugin/plugin.json as best-effort.
**Warning signs:** Codex agent ignores plugin skills; skills not appearing in Codex agent's available tools.

### Pitfall 2: SKILL.md Frontmatter Validation
**What goes wrong:** Incorrect YAML frontmatter (misspelled fields, invalid types) causes Claude Code to silently skip the skill.
**Why it happens:** Frontmatter parsing errors are not always surfaced to the user; the skill simply doesn't appear.
**How to avoid:** Use exactly the documented fields: `name` (string), `description` (string), `allowed-tools` (list of strings). Do not add custom fields. Test skill discovery after creation.
**Warning signs:** Skill does not appear when agent lists available skills; agent does not invoke skill even when context matches.

### Pitfall 3: MCP Server Path Resolution
**What goes wrong:** The `npx @tableau/mcp-server` command fails because npx is not in PATH or Node.js is not installed.
**Why it happens:** MCP servers run as child processes; the host environment must have the required runtime.
**How to avoid:** Document Node.js as a prerequisite for MCP features. Make MCP optional -- skills should work without MCP (MCP-02 says "optional"). Use `${VAR:-default}` syntax for env vars that may not be set.
**Warning signs:** MCP server connection failures at agent startup; `tableau` MCP tools not available.

### Pitfall 4: Skill Ordering and Dependencies
**What goes wrong:** An agent invokes the publisher skill before validation, publishing a broken workbook.
**Why it happens:** Skills are independent instructions; there is no enforced execution order.
**How to avoid:** Each skill should document its prerequisites clearly. The publisher skill should say "only publish workbooks that pass both XSD and semantic validation." The CLAUDE.md/AGENTS.md should document the recommended pipeline order: spec -> generate -> validate -> qa -> publish.
**Warning signs:** Agent publishes workbooks that fail to open in Tableau; validation errors found post-publish.

### Pitfall 5: CLAUDE.md Conflicts with SKILL.md
**What goes wrong:** CLAUDE.md project-level instructions contradict or duplicate skill-level instructions, causing agent confusion.
**Why it happens:** Both CLAUDE.md and SKILL.md can define conventions; if they disagree, the agent may follow either.
**How to avoid:** CLAUDE.md should define project-level context (what this project is, how to install, how to test). SKILL.md should define procedural steps (what commands to run, what to check). No overlapping authority.
**Warning signs:** Agent behavior differs when skill is invoked directly vs. as part of a pipeline.

## Code Examples

### Example: Minimal plugin.json for Claude Code
```json
// .claude-plugin/plugin.json
// Source: docs.anthropic.com/en/docs/claude-code/plugins
{
  "name": "tableau-agent-toolkit",
  "description": "Generate, validate, package, and publish Tableau workbooks from YAML specs. Provides five composable skills for deterministic dashboard workflows.",
  "version": "0.1.0",
  "skills": [
    "skills/tableau-dashboard-spec-writer",
    "skills/tableau-twb-generator",
    "skills/tableau-twb-validator",
    "skills/tableau-dashboard-qa-reviewer",
    "skills/tableau-publisher"
  ]
}
```

### Example: Plugin.json with Inline MCP Servers
```json
// .claude-plugin/plugin.json with optional MCP wiring (MCP-02)
// Source: docs.anthropic.com/en/docs/claude-code/plugins + docs.anthropic.com/en/docs/claude-code/mcp
{
  "name": "tableau-agent-toolkit",
  "description": "Generate, validate, package, and publish Tableau workbooks from YAML specs.",
  "version": "0.1.0",
  "skills": [
    "skills/tableau-dashboard-spec-writer",
    "skills/tableau-twb-generator",
    "skills/tableau-twb-validator",
    "skills/tableau-dashboard-qa-reviewer",
    "skills/tableau-publisher"
  ],
  "mcpServers": {
    "tableau": {
      "command": "npx",
      "args": ["-y", "@tableau/mcp-server"],
      "env": {
        "SERVER": "${TABLEAU_SERVER_URL}",
        "SITE_NAME": "${TABLEAU_SITE_NAME:-}",
        "PAT_NAME": "${TABLEAU_PAT_NAME}",
        "PAT_VALUE": "${TABLEAU_PAT_SECRET}"
      }
    }
  }
}
```

### Example: Standalone .mcp.json (Alternative to Inline)
```json
// .mcp.json -- project-level MCP configuration
// Source: docs.anthropic.com/en/docs/claude-code/mcp
{
  "mcpServers": {
    "tableau": {
      "command": "npx",
      "args": ["-y", "@tableau/mcp-server"],
      "env": {
        "SERVER": "${TABLEAU_SERVER_URL}",
        "SITE_NAME": "${TABLEAU_SITE_NAME:-}",
        "PAT_NAME": "${TABLEAU_PAT_NAME}",
        "PAT_VALUE": "${TABLEAU_PAT_SECRET}"
      }
    }
  }
}
```

### Example: Skill -- tableau-dashboard-spec-writer (SKILL-01)
```markdown
---
name: tableau-dashboard-spec-writer
description: Convert a business brief or requirements document into a structured dashboard_spec.yaml file for the tableau-agent-toolkit pipeline
allowed-tools:
  - Read
  - Write
  - Bash
---

# Tableau Dashboard Spec Writer

## When to Use
Use this skill when you need to create or update a Tableau dashboard specification from a business brief, requirements document, or user description.

## Prerequisites
- The `tableau-agent-toolkit` CLI must be installed (`pip install tableau-agent-toolkit`)
- Understand the spec schema defined in `src/tableau_agent_toolkit/spec/models.py`

## Steps

### 1. Gather Requirements
Ask the user for:
- Dashboard purpose and target audience
- Data sources (type, server, database)
- Key metrics and calculations needed
- Worksheet names and purposes
- Dashboard layout preferences

### 2. Initialize Spec (Optional)
For a starter structure:
```bash
tableau-agent-toolkit spec init --output dashboard_spec.yaml --name "Dashboard Name" --template finance-reconciliation --version 2026.1
```

### 3. Author the Spec
Create or edit `dashboard_spec.yaml` following the schema:
- `spec_version`: "1.0"
- `workbook`: name, version, template reference
- `datasources`: connection definitions
- `parameters`: reusable parameters
- `calculations`: Tableau calculation formulas
- `worksheets`: sheet definitions with datasource references
- `dashboards`: layout with sheet references

### 4. Validate the Spec
```bash
# The spec is validated on load, but verify explicitly:
python -c "from tableau_agent_toolkit.spec.io import load_spec; load_spec('dashboard_spec.yaml')"
```

## Reference
- Example specs: `examples/specs/` directory
- Spec models: `src/tableau_agent_toolkit/spec/models.py`
- JSON Schema: generated from Pydantic models
```

### Example: Skill -- tableau-twb-validator (SKILL-03)
```markdown
---
name: tableau-twb-validator
description: Validate a Tableau workbook (.twb) against XSD schemas and semantic rules to catch errors before packaging and publishing
allowed-tools:
  - Bash
  - Read
---

# Tableau TWB Validator

## When to Use
Use this skill after generating a .twb workbook to validate it before packaging and publishing. Always run validation before publish.

## Prerequisites
- A `.twb` file to validate
- XSD schemas vendored in `third_party/tableau_document_schemas/`

## Steps

### 1. XSD Validation (Structural)
```bash
tableau-agent-toolkit validate-xsd workbook.twb --version 2026.1
```
If this fails, the workbook has structural XML errors. Fix the spec or template before proceeding.

### 2. Semantic Validation (Cross-references)
```bash
tableau-agent-toolkit validate-semantic --input workbook.twb --spec dashboard_spec.yaml
```
This checks:
- Sheet references exist in the workbook
- Calculation names are valid
- Action targets resolve correctly
- Field references are not dangling

### 3. Interpret Results
- **Errors**: Must be fixed before proceeding. Map back to spec line numbers using the `--spec` flag.
- **Warnings**: Review and decide whether to proceed. Warnings indicate potential issues that may not block functionality.

## Pipeline Context
- Previous step: `tableau-twb-generator` (generates the .twb)
- Next step: `tableau-dashboard-qa-reviewer` (quality checks) or `tableau-publisher` (if QA passed)
```

### Example: AGENTS.md for Codex (SKILL-07)
```markdown
# Tableau Agent Toolkit

## Project Overview
A Python toolkit that generates, validates, packages, and publishes Tableau workbooks from structured YAML dashboard specifications. It ships as a CLI tool and as agent skills for Claude Code and Codex.

## Setup
```bash
pip install -e ".[dev]"
```

## Commands
| Command | Description |
|---------|-------------|
| `tableau-agent-toolkit spec init --output spec.yaml --name "Name"` | Create starter spec |
| `tableau-agent-toolkit generate spec.yaml --output out.twb` | Generate workbook |
| `tableau-agent-toolkit validate-xsd workbook.twb` | XSD validation |
| `tableau-agent-toolkit validate-semantic --input workbook.twb` | Semantic validation |
| `tableau-agent-toolkit qa static --input workbook.twb` | QA checks |
| `tableau-agent-toolkit package --input workbook.twb` | Package to .twbx |
| `tableau-agent-toolkit publish --input workbook.twbx --server URL --project NAME` | Publish to server |

## Testing
```bash
pytest tests/                          # All tests
pytest tests/unit/                     # Unit tests only
pytest tests/integration/              # Integration tests only
pytest tests/ -x                       # Stop on first failure
```

## Architecture
- `src/tableau_agent_toolkit/spec/` -- Spec models (Pydantic v2) and YAML I/O
- `src/tableau_agent_toolkit/twb/` -- TWB generator (lxml XML patching)
- `src/tableau_agent_toolkit/validation/` -- XSD and semantic validators
- `src/tableau_agent_toolkit/qa/` -- Static QA checker and report generator
- `src/tableau_agent_toolkit/packaging/` -- .twbx packager and verifier
- `src/tableau_agent_toolkit/publishing/` -- TSC publisher with REST fallback
- `src/tableau_agent_toolkit/templates/` -- Template registry and catalog

## Pipeline Order
spec init -> generate -> validate-xsd -> validate-semantic -> qa static -> package -> publish

## Example Specs
See `examples/specs/` for working spec files:
- `finance-reconciliation.dashboard_spec.yaml`
- `executive-kpi.dashboard_spec.yaml`
- `ops-monitoring.dashboard_spec.yaml`
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Custom agent instructions in README | SKILL.md with YAML frontmatter | Claude Code 2025 | Structured skill discovery and invocation |
| Hardcoded MCP config per project | `.mcp.json` with env expansion | Claude Code 2025 | Portable, shareable MCP configurations |
| Single-platform plugins | Dual plugin manifests (Claude + Codex) | 2025-2026 | Skills work across multiple agent platforms |
| Codex without project instructions | AGENTS.md convention | OpenAI Codex 2025 | Codex agents can follow project conventions |

**Deprecated/outdated:**
- Custom `.cursorrules` files: Replaced by `.cursor/skills/` SKILL.md format [ASSUMED]
- Ad-hoc agent prompts: Replaced by structured SKILL.md with frontmatter

## Skill-to-CLI Mapping

| Skill (SKILL-##) | Skill Name | Primary CLI Commands | Secondary CLI Commands |
|-------------------|------------|---------------------|----------------------|
| SKILL-01 | tableau-dashboard-spec-writer | `spec init` | (spec model validation via Python) |
| SKILL-02 | tableau-twb-generator | `generate` | (template lookup via registry) |
| SKILL-03 | tableau-twb-validator | `validate-xsd`, `validate-semantic` | (XSD sync script) |
| SKILL-04 | tableau-dashboard-qa-reviewer | `qa static` | (optional MCP tools for post-publish) |
| SKILL-05 | tableau-publisher | `package`, `publish` | (auto-package when .twb input) |

## Skill Dependency Graph

```
SKILL-01 (spec-writer)
    |
    v
SKILL-02 (twb-generator)  -- requires spec from SKILL-01
    |
    v
SKILL-03 (twb-validator)  -- requires .twb from SKILL-02
    |
    v
SKILL-04 (qa-reviewer)    -- requires validated .twb from SKILL-03
    |
    v
SKILL-05 (publisher)      -- requires QA-passed .twb from SKILL-04
    |
    v
MCP-03 (post-publish QA)  -- optional, queries published workbook via MCP
```

Note: Dependencies are procedural guidance in skill instructions, not enforced constraints. An agent could skip steps, but the skills should document why that is risky.

## Recommended Plan Breakdown

### Wave 1: Foundation (Manifests + Core Skills)
**Plan 04-01: Plugin manifests, AGENTS.md, and spec-writer/generator skills**
- SKILL-06: `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`
- SKILL-07: Update `CLAUDE.md` (already exists, needs agent workflow section), create `AGENTS.md`
- SKILL-01: `skills/tableau-dashboard-spec-writer/SKILL.md`
- SKILL-02: `skills/tableau-twb-generator/SKILL.md`

Rationale: These have no external dependencies. The manifests and first two skills can be created together since they form the start of the pipeline. CLAUDE.md already exists, so this is an update + AGENTS.md creation.

### Wave 2: Validation, QA, and Publishing Skills + MCP
**Plan 04-02: Validator, QA, publisher skills, and MCP configuration**
- SKILL-03: `skills/tableau-twb-validator/SKILL.md`
- SKILL-04: `skills/tableau-dashboard-qa-reviewer/SKILL.md`
- SKILL-05: `skills/tableau-publisher/SKILL.md`
- MCP-01: Document Tableau MCP server compatibility
- MCP-02: Create `.mcp.json` with Tableau MCP wiring (or embed in plugin.json)
- MCP-03: Add MCP tool references to QA reviewer skill

Rationale: Wave 2 skills depend on the pipeline structure established in Wave 1. MCP configuration is placed here because it is referenced by the QA reviewer skill.

## Tableau MCP Server Configuration

The official `@tableau/mcp-server` npm package provides MCP tools for Tableau Server/Cloud interaction. Configuration:

```json
{
  "mcpServers": {
    "tableau": {
      "command": "npx",
      "args": ["-y", "@tableau/mcp-server"],
      "env": {
        "SERVER": "${TABLEAU_SERVER_URL}",
        "SITE_NAME": "${TABLEAU_SITE_NAME:-}",
        "PAT_NAME": "${TABLEAU_PAT_NAME}",
        "PAT_VALUE": "${TABLEAU_PAT_SECRET}"
      }
    }
  }
}
```

Required environment variables:
- `SERVER`: Tableau Server or Cloud URL
- `PAT_NAME`: Personal Access Token name
- `PAT_VALUE`: Personal Access Token secret
- `SITE_NAME`: Site contentUrl (optional, empty for default site)

[Source: github.com/tableau/mcp-server README -- verified via webReader]

MCP tools provided (used by SKILL-04 for post-publish QA):
- Query workbook metadata
- List data sources
- Get view images
- Explore published content

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `.codex-plugin/plugin.json` format mirrors Claude Code plugin.json with skills array | Standard Stack | Codex skills may not be discovered; fallback to AGENTS.md as primary mechanism |
| A2 | The Tableau MCP server (`@tableau/mcp-server`) is stable and publicly available on npm | MCP Configuration | MCP integration may fail; need to verify package exists and is maintained |
| A3 | Codex agents follow AGENTS.md files located at the project root | AGENTS.md pattern | Codex agents may not pick up instructions; need testing with actual Codex instance |
| A4 | Claude Code discovers skills via the `skills` array in plugin.json pointing to directories containing SKILL.md | Plugin Manifest | Skills may not appear; verify with Claude Code plugin installation |
| A5 | The `allowed-tools` field in SKILL.md frontmatter is optional and restricts which tools the skill can use | SKILL.md format | Omitting it may allow broader access than intended; including wrong values may block legitimate tool use |

## Open Questions

1. **Codex Plugin Manifest Schema**
   - What we know: Codex uses AGENTS.md for instructions; `.codex-plugin/` directory exists as a convention
   - What's unclear: Exact JSON schema for `.codex-plugin/plugin.json` -- fields, required vs optional, skill discovery mechanism
   - Recommendation: Use AGENTS.md as primary Codex mechanism. If `.codex-plugin/plugin.json` schema can be confirmed, add it as supplementary. Test with an actual Codex instance if possible.

2. **Tableau MCP Server Tool Names**
   - What we know: The server provides tools for querying workbooks, views, data sources
   - What's unclear: Exact tool names and parameter schemas for MCP-03 skill references
   - Recommendation: Document MCP integration as "use available MCP tools" rather than hardcoding specific tool names. The MCP server may add/remove tools between versions.

3. **SKILL.md `allowed-tools` Values**
   - What we know: The field exists and accepts a list of tool names
   - What's unclear: Complete list of valid tool name strings (Bash, Read, Write, Edit, etc.)
   - Recommendation: Use conservative tool lists (Bash for CLI invocation, Read for file inspection, Write for file creation). Omit `allowed-tools` if uncertain -- this allows the agent to use all available tools.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js / npm | Tableau MCP server (optional) | Not verified | -- | MCP features disabled; skills work without MCP |
| npx | MCP server invocation | Not verified | -- | Same as above |
| `tableau-agent-toolkit` CLI | All skills | Yes | 0.1.0 | -- |
| `@tableau/mcp-server` | MCP-01/MCP-02/MCP-03 | Not verified | -- | Skills function without MCP; post-publish QA uses CLI only |

**Missing dependencies with no fallback:**
- None -- all MCP features are explicitly optional per requirements (MCP-02: "optional .mcp.json wiring")

**Missing dependencies with fallback:**
- Node.js/npm: Required for Tableau MCP server only. Without it, MCP-01/MCP-03 features are unavailable but all five skills still function (they use CLI commands, not MCP).

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SKILL-01 | Spec-writer SKILL.md has correct frontmatter and references CLI | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_skill_frontmatter -x` | Wave 0 |
| SKILL-02 | Generator SKILL.md has correct frontmatter and references CLI | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_skill_frontmatter -x` | Wave 0 |
| SKILL-03 | Validator SKILL.md references both validate commands | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_skill_frontmatter -x` | Wave 0 |
| SKILL-04 | QA reviewer SKILL.md references qa static and optional MCP | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_skill_frontmatter -x` | Wave 0 |
| SKILL-05 | Publisher SKILL.md references package and publish commands | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_skill_frontmatter -x` | Wave 0 |
| SKILL-06 | Both plugin.json manifests are valid JSON with correct fields | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_plugin_manifests -x` | Wave 0 |
| SKILL-07 | CLAUDE.md has agent workflow section; AGENTS.md exists with project commands | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_agent_instructions -x` | Wave 0 |
| MCP-01 | MCP config references @tableau/mcp-server with correct env vars | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_mcp_config -x` | Wave 0 |
| MCP-02 | .mcp.json or plugin.json mcpServers exists and is valid | unit (validation) | `pytest tests/unit/test_skill_manifests.py::test_mcp_config -x` | Wave 0 |
| MCP-03 | QA skill references MCP tools for post-publish queries | manual-only | Manual review of SKILL.md content | N/A |

Note: Phase 4 testing is primarily structural validation (files exist, JSON is valid, frontmatter is correct, CLI commands are referenced). Functional testing would require running an actual agent, which is out of scope for automated tests.

### Sampling Rate
- **Per task commit:** `pytest tests/unit/test_skill_manifests.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/unit/test_skill_manifests.py` -- covers SKILL-06, SKILL-07, MCP-01, MCP-02 (JSON validation, frontmatter validation, file existence)

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | PAT auth via env vars (TABLEAU_PAT_NAME, TABLEAU_PAT_SECRET) -- never in config files |
| V3 Session Management | no | MCP sessions are transient; no persistent sessions |
| V4 Access Control | no | Plugin manifests are read-only; no access control needed |
| V5 Input Validation | yes | Skill instructions guide agents to validate inputs via CLI validation commands |
| V6 Cryptography | no | No cryptographic operations in Phase 4 |

### Known Threat Patterns for Agent Skills

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Secrets leakage in config files | Information Disclosure | Use `${ENV_VAR}` references in MCP config; never hardcode tokens |
| Prompt injection via spec files | Tampering | Skills validate specs through CLI (Pydantic validation), not raw string parsing |
| Unauthorized publish | Elevation of Privilege | Publisher skill requires TABLEAU_PAT_* env vars; cannot publish without credentials |

## Sources

### Primary (HIGH confidence)
- docs.anthropic.com/en/docs/claude-code/plugins -- Claude Code plugin manifest format
- docs.anthropic.com/en/docs/claude-code/skills -- SKILL.md format with YAML frontmatter
- docs.anthropic.com/en/docs/claude-code/mcp -- .mcp.json format and env variable expansion
- github.com/tableau/mcp-server README -- Tableau MCP server configuration and env vars

### Secondary (MEDIUM confidence)
- openai.com/index/codex/ -- Codex AGENTS.md convention confirmed
- Codebase inspection: cli.py, models.py, pyproject.toml -- verified CLI commands and spec structure

### Tertiary (LOW confidence)
- `.codex-plugin/plugin.json` schema -- [ASSUMED] based on Claude Code pattern; not independently verified from official Codex documentation

## Metadata

**Confidence breakdown:**
- Standard stack (declarative formats): HIGH -- verified from official Anthropic docs and project codebase
- Architecture (skill/manifest structure): HIGH -- follows documented Claude Code patterns
- Pitfalls (agent behavior): MEDIUM -- some pitfalls are hypothesized based on general agent behavior, not observed failures
- MCP integration: MEDIUM -- Tableau MCP server config verified from GitHub README, but tool names and exact capabilities not independently verified
- Codex plugin format: LOW -- no official documentation found for .codex-plugin/plugin.json schema

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (30 days -- plugin formats are relatively stable)
