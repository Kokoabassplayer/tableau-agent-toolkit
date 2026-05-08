# Feature Landscape

**Domain:** Programmatic Tableau workbook generation, validation, and publishing via structured specifications and AI agent integration
**Researched:** 2026-05-08

## Ecosystem Context

This is a near-greenfield domain. The Tableau programmatic authoring ecosystem has four official pieces of infrastructure, none of which solve the "generate a complete workbook from a spec" problem end-to-end:

1. **tableau-document-schemas** (Feb 2026) -- Official XSDs for TWB format. Provides syntactic validation only. Does not validate semantics (calc references, sheet refs, action targets). No TWBX support. Explicitly states "developers and agents" as target users.
2. **tableau-mcp** (Node.js MCP server) -- Agent tool for querying data, exploring content, getting view images. Focused on *reading* Tableau, not *authoring* workbooks. No workbook generation capability.
3. **server-client-python** (TSC, v0.40) -- Publishes workbooks and data sources to Tableau Server/Cloud. Manages users, projects, sites. No workbook *creation* capability.
4. **document-api-python** (As-Is, unsupported, last release Nov 2022) -- Reads/modifies existing TWB/TWBX files. Explicitly *does not support* creating files from scratch, adding extracts, or updating field information.

GitHub searches for "tableau twb generator" and "tableau yaml dashboard" returned essentially zero meaningful existing tools. The only adjacent project found was a Lightdash migration skill that converts Tableau workbooks *to* dbt YAML, not the other direction.

**Confidence: HIGH** -- Based on official GitHub repos and direct repo searches.

## Table Stakes

Features users expect from any "generate Tableau workbooks from spec" tool. Missing any of these means the tool feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| YAML/structured spec input | Declarative, version-controllable specs are the standard for "as-code" tools (Terraform, dbt, Ansible). Without this, you are just writing XML by hand. | Med | Pydantic v2 models provide both validation and schema docs. |
| Template-based TWB generation | Patching known-good templates is the only reliable path since XSD is syntactic-only. Users expect their dashboards to actually open in Tableau. | High | lxml XML patching on pinned template files. |
| XSD validation | The official schema exists; not using it would be negligent. Users expect generated files to pass structural validation. | Low | Pin and vendor XSDs from tableau-document-schemas. Straightforward lxml call. |
| Semantic validation | XSD passes do not mean the workbook works. Users expect the tool to catch broken sheet references, invalid calc names, missing action targets, and dangling field references before they open Tableau. | High | This is the hardest correctness problem. Requires custom validation layer beyond XSD. |
| CLI interface | Developer tooling is expected to be command-line driven. "Just works from terminal" is table stakes for DevOps/CI integration. | Low | Typer CLI wrapping Python engine. |
| Deterministic output | Same spec + same template + same XSD version = same .twb byte-for-byte. Required for diff-based review and CI reproducibility. | Med | Requires controlling XML serialization (attribute order, whitespace, encoding). |
| Tableau Server publishing | Users who generate workbooks need to deploy them. PAT-authenticated publishing via TSC is the standard path. | Med | TSC library handles the heavy lifting; our job is wrapping it correctly. |
| Error messages that point to the spec | When validation fails, users expect to see "dashboard_spec.yaml line 42: sheet 'SalesMap' references undefined datasource 'wh_revenue'" not "XMLSchemaValidationError: element 'worksheet' failed". | Med | Requires mapping XML locations back to YAML spec locations. |

## Differentiators

Features that set this tool apart from ad hoc scripting or manual authoring. Not universally expected, but highly valued.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Dual AI agent plugins (Claude + Codex) | Enables "describe your dashboard in natural language, get a validated .twb" workflow. No other Tableau tooling offers this. | Med | Shared SKILL.md definitions, separate plugin manifests. Agent invokes CLI commands under the hood. |
| 5 shared agent skills (spec-writer, generator, validator, QA-reviewer, publisher) | Breaks the workbook lifecycle into composable agent-callable steps. An agent can write a spec, generate, validate, review, and publish in a single session. | Med | Each skill is a focused prompt + CLI invocation. Reusable across Claude and Codex. |
| Template registry with version compatibility rules | Users can register, version, and pin templates. Prevents "template X broke when we upgraded Tableau" incidents. | Med | Registry maps template version to Tableau version compatibility. |
| `<ManifestByVersion />` support | The official XSD docs recommend this for direct workbook authoring -- it replaces a complex manual feature manifest with a single element. Using it demonstrates XSD-fluency. | Low | Single XML element substitution. But understanding *when* and *why* matters. |
| .twbx packaging as separate step | Clean separation between "generate the XML" and "bundle with extracts/assets". Users can validate .twb before packaging. | Med | zipfile-based packaging. Separate from generation keeps the pipeline composable. |
| Static QA checks + optional sandbox smoke test | XSD + semantic validation are static. An optional sandbox publish to Tableau Server and verify-render step catches issues that static analysis cannot. | High | Sandbox smoke test requires a running Tableau instance (Server or Public). Flag as optional. |
| Multi-version Tableau support via template passthrough profiles | Start with 2026.1, but templates can target earlier versions through compatibility profiles. Users with older Tableau deployments are not left out. | Med | Requires maintaining template sets per version. Passthrough profile maps spec features to template capabilities. |
| Spec schema documentation generation | Auto-generate JSON Schema or Markdown docs from Pydantic models so users know what the spec accepts without reading source code. | Low | Pydantic v2 natively supports JSON Schema export. |
| `spec init` scaffolding command | Generate a starter dashboard_spec.yaml from an existing .twb file (reverse-engineer spec from workbook). Lowers onboarding friction dramatically. | Med | Read existing .twb XML, extract structure, emit YAML. Not a full round-trip but enough for bootstrapping. |

## Anti-Features

Features to explicitly NOT build. These are traps that seem useful but cause maintenance burden, scope creep, or architectural problems.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| Freehand XML authoring without templates | XSD validates syntax only. Freehand-authored TWBs will pass XSD but fail to open in Tableau. The debugging surface is enormous and unmaintainable. | Template-first generation only. Patch known-good templates. |
| Visual/dashboard designer UI | Building a visual layout editor is a completely different product with entirely different engineering challenges. Outside the scope of a CLI/agent tool. | Keep the interface as YAML spec + CLI + agent skills. Users who want visual authoring use Tableau Desktop. |
| Full .twbx XSD validation | The official schemas do not support .twbx. Attempting to validate the packaged format at the XSD level is inventing a specification that does not exist. | Validate the inner .twb against XSD + verify package integrity (file exists, not corrupt). |
| Connected-app / JWT auth for publishing | JWT adds OAuth complexity that is orthogonal to workbook generation. Ship PAT first, validate the core workflow. | PAT auth via TSC. Add JWT in v0.4 after core workflow is proven. |
| Data source connection management | Managing live/hyper connections, refresh schedules, and extract configuration is a separate domain handled by Tableau Server REST API directly. | TSC handles publishing. Connection info in spec is limited to what the template needs. |
| Real-time preview / rendering | Rendering Tableau visualizations outside of Tableau is not feasible (proprietary rendering engine). Screenshots via MCP are the closest option. | Optional post-publish QA via MCP to capture rendered views. No in-tool rendering. |
| Tableau REST API proxy/full client | TSC already exists and is well-maintained. Re-implementing REST API calls would be wasted effort. | Use TSC as the publishing backend. Wrap it, do not replace it. |
| Multi-BI-tool support (Power BI, Looker, etc.) | Each BI tool has a completely different document format, rendering engine, and semantic model. Supporting multiple tools would spread the architecture thin. | Focus exclusively on Tableau TWB format. Be excellent at one thing. |
| Calculated field expression builder | Tableau's calculation language is proprietary and complex. Building an expression parser/validator is a project unto itself. | Pass-through calc expressions in the spec YAML. Validate that referenced fields exist, but do not parse expression logic. |

## Feature Dependencies

```
YAML Spec Schema (Pydantic models)
  |
  +---> Template Registry (templates must exist to generate)
  |       |
  |       +---> TWB Generator (spec + template -> .twb)
  |               |
  |               +---> XSD Validation (validates generated .twb)
  |               |       |
  |               |       +---> Semantic Validation (validates references, calc names)
  |               |               |
  |               |               +---> QA Checks (static analysis on validated output)
  |               |                       |
  |               |                       +---> [Optional] Sandbox Smoke Test
  |               |
  |               +---> .twbx Packager (bundles .twb + assets)
  |                       |
  |                       +---> Publisher (deploys to Tableau Server)
  |
  +---> Agent Skills (invoke CLI commands)
          |
          +---> Spec Writer Skill
          +---> Generator Skill (depends on spec + template)
          +---> Validator Skill (depends on generated output)
          +---> QA Reviewer Skill (depends on validated output)
          +---> Publisher Skill (depends on packaged output)
```

### Critical Dependency Chain

1. **Spec schema** must be defined before anything else (all other features consume specs)
2. **Template registry** must exist before generation works (generator needs templates to patch)
3. **TWB generator** must produce output before validation is meaningful
4. **XSD validation** must pass before semantic validation is worth running
5. **Semantic validation** must exist before QA checks add value
6. **Packaging** must follow generation (operates on .twb output)
7. **Publishing** depends on both packaging (for .twbx) and validation (for confidence)
8. **Agent skills** wrap CLI commands -- they come last as composition layer

### Independent Features (can be built in parallel)

- CLI framework (Typer setup, command structure)
- XSD vendoring script (`scripts/sync_tableau_schemas.py`)
- Pydantic spec models
- `<ManifestByVersion />` support (small, well-defined XML element)
- Spec schema documentation generation

## MVP Recommendation

Prioritize:
1. **YAML spec schema with Pydantic v2 models** -- foundation for everything
2. **Template-based TWB generator** -- core value prop, produces output
3. **XSD validation** -- minimum confidence that output is structurally valid
4. **Semantic validation** -- the hard correctness problem that makes the tool trustworthy
5. **CLI with `generate`, `validate-xsd`, `validate-semantic` commands** -- developer interface

Defer:
- **Agent plugins/skills**: High visibility but dependent on solid CLI engine. Build v0.1 CLI-first, add agents in v0.2.
- **Template registry**: Start with inline template paths. Registry adds governance but is not needed for the first working generation.
- **Sandbox smoke tests**: Requires Tableau Server infrastructure. Purely optional at launch.
- **`spec init` from existing .twb**: Valuable onboarding feature but not needed for core generation loop.
- **JWT auth**: PAT is sufficient for v0.1. Add JWT when enterprise users request it.

## Sources

- [tableau/tableau-document-schemas](https://github.com/tableau/tableau-document-schemas) -- Official XSDs, published Feb 2026 (HIGH confidence)
- [tableau/tableau-mcp](https://github.com/tableau/tableau-mcp) -- Official MCP server for reading Tableau, not authoring (HIGH confidence)
- [tableau/server-client-python](https://github.com/tableau/server-client-python) -- TSC v0.40, publish/manage workbooks (HIGH confidence)
- [tableau/document-api-python](https://github.com/tableau/document-api-python) -- As-Is Document API, cannot create from scratch (HIGH confidence)
- GitHub search for "tableau twb generator" -- 2 results, neither maintained (HIGH confidence that this space is empty)
- GitHub search for "tableau yaml dashboard" -- 2 results, 1 is a Lightdash migration skill (HIGH confidence that no competing tool exists)
- GitHub topic "tableau-automation" -- 2 repos, neither relevant to workbook generation (HIGH confidence)
