# Technology Stack

**Project:** tableau-agent-toolkit
**Researched:** 2026-05-08

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

```bash
# Core dependencies
pip install pydantic>=2.13 typer>=0.15 lxml>=5.4 pyyaml>=6.0.3 tableauserverclient>=0.40

# Dev dependencies
pip install -D pytest>=9.0 ruff>=0.11 mypy>=1.15 pre-commit>=4.0
```

## pyproject.toml Skeleton

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "tableau-agent-toolkit"
version = "0.1.0"
description = "Generate, validate, package, and publish Tableau workbooks from structured YAML specs"
requires-python = ">=3.12"
license = "Apache-2.0"
dependencies = [
    "pydantic>=2.13",
    "typer>=0.15",
    "lxml>=5.4",
    "pyyaml>=6.0.3",
    "tableauserverclient>=0.40",
]

[project.scripts]
tableau-agent-toolkit = "tableau_agent_toolkit.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=9.0",
    "ruff>=0.11",
    "mypy>=1.15",
    "pre-commit>=4.0",
]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.12"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Sources

- PyPI: pydantic v2.13.3 (2026-04-20) -- https://pypi.org/project/pydantic/
- PyPI: typer v0.15.2 (2025-02-27) -- https://pypi.org/project/typer/0.15.2/
- PyPI: lxml v5.4.0 (2025-04-22) -- https://pypi.org/project/lxml/5.4.0/
- PyPI: PyYAML v6.0.3 (2025-09-25) -- https://pypi.org/project/PyYAML/
- PyPI: tableauserverclient v0.40 (2026-02-03) -- https://pypi.org/project/tableauserverclient/
- PyPI: pytest v9.0.3 (2026-04-07) -- https://pypi.org/project/pytest/
- GitHub: tableau/tableau-document-schemas (published Feb 2026) -- https://github.com/tableau/tableau-document-schemas
- GitHub: tableau/server-client-python -- https://github.com/tableau/server-client-python
