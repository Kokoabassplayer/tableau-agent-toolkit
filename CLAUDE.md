<!-- GSD:project-start source:PROJECT.md -->
## Project

**tableau-agent-toolkit**

An open-source Python-first toolkit that generates, validates, packages, and publishes Tableau workbooks from structured YAML dashboard specifications. It ships as both a Python package/CLI and as a dual plugin (Claude Code + Codex) with reusable agent skills for repeatable dashboard workflows.

Target users: analytics engineers, BI developers, data platform teams, and agent users (Claude Code / Codex) who want governed, deterministic workbook generation instead of ad hoc manual editing.

**Core Value:** Deterministic workbook generation from spec + template — the same `dashboard_spec.yaml` + pinned template + pinned XSD version produces the same `.twb` every run.

### Constraints

- **Language**: Python 3.12+ (ecosystem fit — TSC, Document API, tabcmd are all Python)
- **XML tooling**: lxml for parsing, editing, and XSD validation
- **Validation limit**: XSD passes ≠ workbook works in Tableau. Must include semantic QA + sandbox publish smoke test.
- **Security**: No secrets in YAML, templates, or plugin manifests. PAT/JWT via env or secrets manager.
- **License**: Apache-2.0 (aligns with upstream `tableau-document-schemas` and `tableau-mcp`)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Language
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Python | 3.12+ | Primary language | PROJECT.md constraint. TSC, Document API, and tabcmd are all Python-native. Python 3.12 provides performance improvements (faster CPython, better error messages), `type` statement, and stable ABI. 3.12 is the sweet spot: new enough for modern features, old enough for broad binary wheel support from lxml and PyYAML. |
### Data Validation & Schema
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Pydantic | 2.13+ | Spec schema models, config validation | Pydantic v2 is the standard for Python data validation (v2.13.3 released 2026-04-20, verified PyPI). Use for `dashboard_spec.yaml` models, template registry config, and CLI input validation. V2 provides 5-50x performance over v1 via Rust core (`pydantic-core`). Type-hint-driven models give us free JSON Schema generation for spec documentation. Only use v2 API -- do not use the `pydantic.v1` compatibility shim. |
### CLI Framework
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| Typer | 0.15+ | CLI application framework | PROJECT.md specifies Typer. Built on Click, adds type-hint-driven CLI definition with automatic `--help` generation. v0.15.2 (released 2025-02-27, verified PyPI) supports subcommand groups needed for our multi-command CLI (`spec init`, `generate`, `validate-xsd`, `validate-semantic`, `qa static`, `package`, `publish`, `report`). Includes `rich` for formatted error output and `shellingham` for shell auto-completion detection. |
### XML Processing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| lxml | 5.4+ | XML parsing, editing, XSD validation | PROJECT.md constraint. The only production-grade Python XML library with full XSD validation support. v5.4.0 (released 2025-04-22, verified PyPI) uses libxml2 2.13.8 with CVE fixes. Provides `lxml.etree.XMLSchema` for loading pinned XSDs and validating TWB files. Also provides XPath, XSLT, and C14N for advanced XML operations. Pre-built wheels available for Windows (including win_amd64 for cp312), macOS, and Linux. Do not use stdlib `xml.etree.ElementTree` -- it lacks XSD validation. |
### YAML Processing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| PyYAML | 6.0.3+ | Parse dashboard_spec.yaml files | The standard YAML library for Python. v6.0.3 (released 2025-09-25, verified PyPI) adds Python 3.14 support and security fixes. Use `yaml.safe_load()` exclusively -- never `yaml.load()` without Loader. For the spec parser, load YAML then validate through Pydantic models. |
### Tableau Integration
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| tableauserverclient | 0.40+ | Publish workbooks, PAT auth, server operations | Official Tableau Server Client library. v0.40 (released 2026-02-03, verified PyPI) is the latest. Tableau-supported (not "As-Is"). Provides `Server.publish()` for workbook deployment, PAT authentication via `tableauserverclient.PersonalAccessTokenAuth`, and full REST API coverage. Requires Python >=3.9. Use as the exclusive publisher backend -- do not shell out to `tabcmd`. |
### Upstream Schemas (Vendored)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| tableau-document-schemas | 2026.1 | XSD files for TWB validation | Official `tableau/tableau-document-schemas` repo (formally published Feb 2026). Pin and vendor the XSD files as a third-party dependency. Use `scripts/sync_tableau_schemas.py` to refresh from upstream. Start with `twb_2026.1.0.xsd`. Do not install as a package -- these are static `.xsd` files, vendored into `schemas/2026_1/`. |
### Packaging (.twbx)
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| zipfile (stdlib) | stdlib | Create .twbx packaged workbooks | `.twbx` is a ZIP archive containing the `.twb` and any extracted data. Use Python's stdlib `zipfile` module. No third-party library needed. This is a separate step from `.twb` generation per PROJECT.md. |
### Testing
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| pytest | 9.0+ | Test framework | The standard Python test framework. v9.0.3 (released 2026-04-07, verified PyPI). Use for unit tests (spec parsing, XML patching, validation logic) and integration tests (full generate-validate-package pipeline). Fixtures for loading test templates and specs. |
| pytest-tmp-files | -- | Temporary file fixtures | Use pytest's built-in `tmp_path` fixture for test workbooks. No additional library needed. |
### Code Quality
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| ruff | 0.11+ | Linter and formatter | Single tool replacing flake8, isort, black, and more. Extremely fast (Rust-based). Use as the sole linter/formatter. |
| mypy | 1.15+ | Static type checking | Type-check Pydantic models and CLI code. Ensures type-hint correctness across the engine. |
| pre-commit | 4.0+ | Git hook management | Run ruff, mypy, and other checks on commit. |
### Build & Packaging
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| hatch | 1.14+ | Build backend and versioning | Modern Python build backend. Use `hatchling` for the build system in `pyproject.toml`. Simpler than poetry for a library+CLI package. |
| pip | latest | Package installation | Standard installer. |
### Agent Plugin Infrastructure
| Technology | Version | Purpose | Why |
|------------|---------|---------|-----|
| (filesystem) | N/A | Plugin manifests and skills | Claude Code uses `.claude-plugin/plugin.json` + `SKILL.md` files. Codex uses `.codex-plugin/plugin.json`. Both are declarative manifest formats -- no runtime library needed. Skills are Markdown files with instructions. |
## Alternatives Considered
| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| CLI | Typer | Click directly | Typer wraps Click with type hints. Less boilerplate, same power. Click is still the underlying engine. |
| CLI | Typer | argparse | No auto-help, no type coercion, more boilerplate. |
| CLI | Typer | docopt | Declining maintenance, less Pythonic. |
| XML | lxml | stdlib xml.etree.ElementTree | No XSD validation support. Critical gap -- XSD validation is a core requirement. |
| XML | lxml | xmlschema (library) | Adds dependency for something lxml already does natively. lxml's `XMLSchema` class is battle-tested. |
| YAML | PyYAML | ruamel.yaml | Heavier, more suited to round-trip editing. We only need parse + emit. PyYAML is the standard. |
| YAML | Pydantic | strictyaml | Not Pydantic-compatible, smaller ecosystem. Pydantic's YAML support comes via PyYAML. |
| Validation | Pydantic v2 | Pydantic v1 | v1 is in maintenance mode. v2 is 5-50x faster. v1 shim available but should not be used. |
| Validation | Pydantic v2 | attrs / dataclasses | No built-in validation, serialization, or JSON Schema generation. Pydantic gives us all three. |
| Publisher | tableauserverclient | tabcmd (CLI) | Shelling out to a CLI is fragile, harder to test, and provides no type safety. TSC is the official Python library. |
| Publisher | tableauserverclient | Tableau REST API directly | TSC wraps the REST API with Python types and auth handling. No reason to re-implement. |
| Publisher | tableauserverclient | Tableau Document API | Labeled "As-Is" and unsupported. Does not support creating files from scratch. Only useful for selective inspection/patching, which we handle with lxml directly. |
| Testing | pytest | unittest | More boilerplate, no fixtures ecosystem, no plugin architecture. pytest is the standard. |
| Formatting | ruff | black + isort + flake8 | Three tools replaced by one. ruff is orders of magnitude faster. |
| Build | hatchling | poetry | poetry is heavier, opinionated about dependency management. hatchling is a pure build backend -- simpler for a library package. |
| Build | hatchling | setuptools | Older, more configuration. hatchling is the modern standard with `pyproject.toml` only. |
## Installation
# Core dependencies
# Dev dependencies
## pyproject.toml Skeleton
## Sources
- PyPI: pydantic v2.13.3 (2026-04-20) -- https://pypi.org/project/pydantic/
- PyPI: typer v0.15.2 (2025-02-27) -- https://pypi.org/project/typer/0.15.2/
- PyPI: lxml v5.4.0 (2025-04-22) -- https://pypi.org/project/lxml/5.4.0/
- PyPI: PyYAML v6.0.3 (2025-09-25) -- https://pypi.org/project/PyYAML/
- PyPI: tableauserverclient v0.40 (2026-02-03) -- https://pypi.org/project/tableauserverclient/
- PyPI: pytest v9.0.3 (2026-04-07) -- https://pypi.org/project/pytest/
- GitHub: tableau/tableau-document-schemas (published Feb 2026) -- https://github.com/tableau/tableau-document-schemas
- GitHub: tableau/server-client-python -- https://github.com/tableau/server-client-python
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

Five agent skills in `skills/` directory:
- `tableau-dashboard-spec-writer` -- Convert business brief into dashboard_spec.yaml
- `tableau-twb-generator` -- Generate .twb from spec and template
- `tableau-twb-validator` -- XSD + semantic validation of .twb files
- `tableau-dashboard-qa-reviewer` -- Static and optional sandbox QA checks
- `tableau-publisher` -- Package and publish validated workbooks

Pipeline order: spec init -> generate -> validate-xsd -> validate-semantic -> qa static -> package -> publish
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
