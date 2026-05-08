# Phase 1: Spec, Generation, CLI, and Project Scaffolding - Research

**Researched:** 2026-05-08
**Domain:** Python package scaffolding, Pydantic v2 spec models, lxml-based TWB generation, Typer CLI, pytest test infrastructure
**Confidence:** HIGH

## Summary

Phase 1 establishes the entire project foundation: a Python package with src layout, Pydantic v2 models for the `dashboard_spec.yaml` schema, a template-based TWB generator using lxml XML patching, a Typer CLI with subcommand groups, XSD validation against pinned schemas, and project hygiene files (license, CI, examples). This is a near-greenfield phase -- the repo currently contains only `.git/`, `CLAUDE.md`, and `.planning/`. Everything must be built from scratch.

The critical technical decisions are already locked from prior research: template-first generation (never freehand XML), lxml for all XML operations, Pydantic v2 for spec models, Typer for CLI, and hatchling as the build backend. The dominant risk is getting the TWB version mapping wrong (XSD filename `twb_2026.1.0.xsd` corresponds to TWB `version='26.1'`), which would produce workbooks that Tableau refuses to open. A secondary risk is namespace corruption during lxml serialization -- the TWB format requires specific `xmlns:user` declarations that lxml may reorder.

The deep research report at `~/Downloads/deep-research-report.md` provides a comprehensive blueprint including a full repo layout, spec schema design, sample YAML files, generator code skeleton, CI configuration, and skill templates. This phase should implement that blueprint faithfully, adjusting only for package version updates discovered during research (lxml is now 6.1.0, not 5.4; Typer is 0.25.1, not 0.15; Pydantic is 2.13.4).

**Primary recommendation:** Follow the deep research report blueprint exactly. Build in dependency order: `pyproject.toml` + src layout -> `spec/models.py` -> `spec/io.py` -> `twb/manifest.py` -> `templates/registry.py` -> `twb/generator.py` -> `validation/xsd.py` -> `cli.py`. Each module should have corresponding unit tests built alongside it.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| SPEC-01 | Dashboard spec defined as YAML with Pydantic v2 models | Pydantic 2.13.4 verified on PyPI; model design from deep research report; JSON Schema generation is built into Pydantic v2 |
| SPEC-02 | YAML load/dump with validation -- load_spec() and dump_spec() | PyYAML 6.0.3 verified; pattern: yaml.safe_load() then Pydantic model validation |
| SPEC-03 | Deterministic output -- same spec + template + XSD produces same .twb | lxml etree.write() with xml_declaration=True, encoding="utf-8" produces deterministic output when template is fixed |
| SPEC-04 | Error messages map XML failures back to spec line numbers | Pydantic validation errors include field paths; custom error formatting maps to spec sections |
| SPEC-05 | JSON Schema auto-generated from Pydantic models | Pydantic v2 model.model_json_schema() produces JSON Schema for editor support |
| GEN-01 | Template-based TWB generator using lxml XML patching | lxml 6.1.0 verified; etree.parse() + XPath patching pattern from deep research report and ARCHITECTURE.md |
| GEN-02 | Template registry with catalog.yaml mapping | catalog.yaml design from deep research report; Pydantic model for registry entries |
| GEN-03 | ManifestByVersion support | Official tableau-document-schemas README confirms pattern; exact XML fragment documented |
| GEN-04 | Version mapping utility -- XSD filenames to TWB version strings | Official README confirms: XSD twb_2026.1.0.xsd = TWB version='26.1'; derive programmatically |
| GEN-05 | Workbook name, datasource, calculation, worksheet, dashboard patching | lxml XPath + element manipulation; separate methods per patch type for testability |
| CLI-01 | Typer CLI with commands | Typer 0.25.1 verified; subcommand groups via app.add_typer() pattern confirmed in official docs |
| CLI-02 | Each command has clean help text and typed arguments | Typer auto-generates --help from type hints and docstrings |
| CLI-03 | spec init scaffolding | Typer command with rich.prompt for interactive input; generate starter YAML from Pydantic model defaults |
| PROJ-01 | Python package installable via pip with pyproject.toml and src layout | hatchling 1.29.0 verified; src layout with packages = ["src/tableau_agent_toolkit"] confirmed in Hatch docs |
| PROJ-02 | Unit tests, integration tests with fixtures, and smoke test scaffold | pytest 9.0.3 verified; tmp_path fixture for temp files; test structure mirrors src/ layout |
| PROJ-03 | GitHub Actions CI with lint, type check, and test matrix | CI workflow from deep research report; Python 3.12 + 3.13 matrix |
| PROJ-04 | Apache-2.0 license, SECURITY.md, CONTRIBUTING.md, CHANGELOG.md | Standard OSS files; Apache-2.0 aligns with upstream tableau-document-schemas |
| PROJ-05 | Example specs with SQL files | Three example specs from deep research report; finance-reconciliation YAML fully designed |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12+ | Primary language | PROJECT.md constraint; ecosystem fit (TSC, lxml, Pydantic all Python-native) |
| Pydantic | 2.13.4 | Spec schema models, validation, JSON Schema generation | [VERIFIED: PyPI 2026-05-08] De facto standard for Python data validation; v2 provides 5-50x speed over v1 via Rust core |
| Typer | 0.25.1 | CLI application framework | [VERIFIED: PyPI 2026-05-08] PROJECT.md constraint; built on Click with type-hint-driven command definition |
| lxml | 6.1.0 | XML parsing, editing, XSD validation | [VERIFIED: PyPI 2026-05-08] Only production Python XML library with full XSD validation; pre-built Windows wheels available |
| PyYAML | 6.0.3 | Parse dashboard_spec.yaml files | [VERIFIED: PyPI 2026-05-08] Standard YAML library; use yaml.safe_load() exclusively |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic-settings | 2.14.0 | Environment-backed credential loading | [VERIFIED: PyPI 2026-05-08] For security/settings.py module (Phase 1 stub for Phase 3) |
| hatchling | 1.29.0 | Build backend | [VERIFIED: PyPI 2026-05-08] pyproject.toml build system; src layout support via packages option |
| pytest | 9.0.3 | Test framework | [VERIFIED: PyPI 2026-05-08] Unit + integration tests |
| pytest-cov | 7.1.0 | Coverage reporting | [VERIFIED: PyPI 2026-05-08] CI coverage reports |
| ruff | 0.15.12 | Linter and formatter | [VERIFIED: PyPI 2026-05-08] Replaces black, isort, flake8 |
| mypy | 2.0.0 | Static type checking | [VERIFIED: PyPI 2026-05-08] Type-check Pydantic models and CLI code |
| pre-commit | 4.6.0 | Git hook management | [VERIFIED: PyPI 2026-05-08] Run ruff + mypy on commit |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| lxml 6.1.0 | stdlib xml.etree.ElementTree | No XSD validation -- critical gap for this project |
| Typer | Click directly | Typer wraps Click with type hints; less boilerplate, same power |
| hatchling | poetry | poetry is heavier; hatchling is pure build backend, simpler for library+CLI package |
| Pydantic v2 | attrs/dataclasses | No built-in validation, serialization, or JSON Schema generation |

**Installation:**
```bash
pip install pydantic>=2.13 typer>=0.25 lxml>=6.1 pyyaml>=6.0.3 pydantic-settings>=2.14
pip install -D pytest>=9.0 pytest-cov>=7.1 ruff>=0.15 mypy>=2.0 pre-commit>=4.6
```

**Version verification (completed 2026-05-08):**
- pydantic: 2.13.4 (latest) [VERIFIED: pip index versions]
- typer: 0.25.1 (latest) [VERIFIED: pip index versions]
- lxml: 6.1.0 (latest) [VERIFIED: pip index versions]
- pyyaml: 6.0.3 (latest) [VERIFIED: pip index versions]
- pytest: 9.0.3 (latest) [VERIFIED: pip index versions]
- ruff: 0.15.12 (latest) [VERIFIED: pip index versions]
- mypy: 2.0.0 (latest) [VERIFIED: pip index versions]
- hatchling: 1.29.0 (latest) [VERIFIED: pip index versions]

**Note:** The prior STACK.md research specified lxml>=5.4 and typer>=0.15. Current latest versions are significantly newer (6.1.0 and 0.25.1 respectively). The pyproject.toml should use `>=6.1` for lxml and `>=0.25` for typer to match current state.

## Architecture Patterns

### Recommended Project Structure

```
tableau-agent-toolkit/
├── src/
│   └── tableau_agent_toolkit/
│       ├── __init__.py                 # Package init, __version__
│       ├── cli.py                      # Typer CLI entry point + subcommand registration
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
│       │   └── manifest.py            # apply_manifest_by_version(), version mapping
│       ├── validation/
│       │   ├── __init__.py
│       │   └── xsd.py                 # XsdValidator class
│       └── security/
│           ├── __init__.py
│           └── settings.py            # pydantic-settings for env-backed creds (stub)
├── skills/                             # Agent skill directories (skeletons in Phase 1)
├── templates/                          # Source .twb templates + catalog.yaml
│   ├── catalog.yaml
│   └── finance/
│       └── reconciliation_template.twb
├── third_party/
│   └── tableau_document_schemas/      # Pinned upstream XSD snapshots
│       ├── README.md
│       └── schemas/
│           └── 2026_1/
│               └── twb_2026.1.0.xsd
├── examples/
│   ├── specs/
│   │   ├── finance-reconciliation.dashboard_spec.yaml
│   │   ├── executive-kpi.dashboard_spec.yaml
│   │   └── ops-monitoring.dashboard_spec.yaml
│   └── sql/
│       └── finance_reconciliation.sql
├── scripts/
│   └── sync_tableau_schemas.py
├── tests/
│   ├── fixtures/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── .github/
│   └── workflows/
│       └── ci.yml
├── pyproject.toml
├── LICENSE
├── SECURITY.md
├── CONTRIBUTING.md
├── CHANGELOG.md
└── README.md
```

### Pattern 1: Template-First Generation (Patch, Don't Create)

**What:** The generator never creates Tableau XML from scratch. It loads a known-good `.twb` template and patches specific elements using lxml XPath queries.

**When to use:** Always. This is the core architectural decision.

**Example:**
```python
# Source: deep research report + ARCHITECTURE.md
from lxml import etree
from tableau_agent_toolkit.spec.models import DashboardSpec

class WorkbookGenerator:
    def generate(self, spec: DashboardSpec, output_path: Path) -> GenerationResult:
        template = self.template_registry.resolve(
            spec.workbook.template.id,
            spec.workbook.target_tableau_version,
        )
        tree = etree.parse(str(template.path))
        apply_manifest_by_version(tree, spec.workbook.target_tableau_version)
        self._patch_workbook_name(tree, spec.workbook.name)
        self._patch_datasources(tree, spec)
        self._patch_calculations(tree, spec)
        self._patch_worksheets(tree, spec)
        self._patch_dashboards(tree, spec)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(str(output_path), encoding="utf-8", xml_declaration=True)
        return GenerationResult(output_path=output_path, warnings=[])
```

### Pattern 2: Typer Subcommand Groups via app.add_typer()

**What:** Each command group (spec, generate, validate, qa, package, publish, report) is a separate Typer app registered into the main app using `app.add_typer()`.

**When to use:** For any multi-command CLI with grouped subcommands.

**Example:**
```python
# Source: [CITED: typer.tiangolo.com/tutorial/subcommands/add-typer/]
# cli.py
import typer
from tableau_agent_toolkit.spec.cli import app as spec_app
from tableau_agent_toolkit.twb.cli import app as generate_app

app = typer.Typer(name="tableau-agent-toolkit", help="Generate, validate, and publish Tableau workbooks")
app.add_typer(spec_app, name="spec", help="Spec file operations")
app.add_typer(generate_app, name="generate", help="Generate workbooks")

if __name__ == "__main__":
    app()
```

### Pattern 3: Pydantic v2 Spec Models with YAML I/O

**What:** Dashboard spec YAML is loaded via PyYAML, then validated through Pydantic v2 models. The models provide type safety, validation, and free JSON Schema generation.

**When to use:** All spec file reading and writing.

**Example:**
```python
# Source: deep research report spec schema design
# spec/io.py
import yaml
from pathlib import Path
from tableau_agent_toolkit.spec.models import DashboardSpec

def load_spec(path: Path) -> DashboardSpec:
    """Load and validate a dashboard spec from YAML."""
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return DashboardSpec.model_validate(raw)

def dump_spec(spec: DashboardSpec, path: Path) -> None:
    """Serialize a DashboardSpec to YAML."""
    data = spec.model_dump(mode="json", exclude_none=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)
```

### Pattern 4: Version Mapping Utility

**What:** Converts between XSD filenames and TWB version strings programmatically. Never allow these to be set independently.

**When to use:** All manifest and version operations.

**Example:**
```python
# Source: [CITED: github.com/tableau/tableau-document-schemas] official README
# twb/manifest.py
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class TableauVersion:
    major: int
    minor: int

    @classmethod
    def from_xsd_filename(cls, filename: str) -> "TableauVersion":
        """Parse 'twb_2026.1.0.xsd' -> TableauVersion(26, 1)."""
        match = re.match(r"twb_(\d{4})\.(\d+)\.\d+\.xsd", filename)
        if not match:
            raise ValueError(f"Invalid XSD filename: {filename}")
        year = int(match.group(1))
        release = int(match.group(2))
        return cls(major=year - 2000, minor=release)

    @property
    def twb_version_string(self) -> str:
        """Returns '26.1' for TableauVersion(26, 1)."""
        return f"{self.major}.{self.minor}"

    @property
    def xsd_version_string(self) -> str:
        """Returns '2026.1.0' for TableauVersion(26, 1)."""
        return f"20{self.major:02d}.{self.minor}.0"
```

### Pattern 5: lxml XSD Validation

**What:** Validate generated TWB files against pinned XSD schemas from `third_party/`.

**When to use:** After every generation step.

**Example:**
```python
# Source: [CITED: deep research report] + lxml docs
# validation/xsd.py
from lxml import etree
from pathlib import Path

class XsdValidator:
    def __init__(self, schemas_root: Path) -> None:
        self._schemas_root = schemas_root

    def validate(self, twb_path: Path, tableau_version: str) -> XsdValidationResult:
        xsd_path = self._resolve_xsd(tableau_version)
        schema_doc = etree.parse(str(xsd_path))
        schema = etree.XMLSchema(schema_doc)
        doc = etree.parse(str(twb_path))
        valid = schema.validate(doc)
        errors = [
            XsdError(line=e.line, column=e.column, message=e.message)
            for e in schema.error_log
        ]
        return XsdValidationResult(valid=valid, errors=errors)
```

### Anti-Patterns to Avoid

- **Freehand XML generation:** Never construct TWB XML from string literals or builders. Always patch known-good templates. [CITED: tableau-document-schemas README]
- **Using Document API as core engine:** Labeled "As-Is" and unsupported; does not support creating files from scratch. Use lxml directly. [CITED: tableau/document-api-python README]
- **Treating XSD validation as sufficient:** XSD is syntactic only. The semantic validator is Phase 2, but do not advertise XSD-pass as "valid workbook." [CITED: tableau-document-schemas README]
- **Monolithic generator:** Separate patch operations into distinct methods (_patch_datasources, _patch_worksheets, etc.) for independent testability. [CITED: ARCHITECTURE.md]
- **Secrets in spec files:** Never put credentials in YAML. Use pydantic-settings for env-backed loading. [CITED: PROJECT.md constraints]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Spec validation | Custom YAML validation logic | Pydantic v2 BaseModel with validators | Free JSON Schema, type coercion, clear error messages, 5-50x faster than v1 |
| CLI argument parsing | Manual argparse or sys.argv parsing | Typer with type hints | Auto --help, type coercion, subcommand groups, rich error formatting |
| XML parsing/editing | String manipulation or regex on XML | lxml.etree with XPath | Handles namespaces, CDATA, encoding correctly; provides XSD validation |
| XSD validation | Custom XML structure checking | lxml.etree.XMLSchema | Battle-tested XSD 1.0 validator built on libxml2 |
| YAML parsing | Custom YAML tokenizer | PyYAML yaml.safe_load() | Handles all YAML edge cases; safe_load prevents arbitrary code execution |
| Version string mapping | Ad hoc string manipulation | TableauVersion dataclass with from_xsd_filename() | Single source of truth; catches invalid filenames early |
| Build/packaging | setup.py or setuptools | hatchling with pyproject.toml | Modern standard; src layout support; no setup.py needed |
| Linting/formatting | Separate black, isort, flake8 configs | ruff (single tool) | Orders of magnitude faster; replaces 3+ tools |

**Key insight:** Every component in this phase has a well-tested library solution. The only custom code should be the domain logic (spec model field definitions, XPath patching strategies, version mapping rules).

## Common Pitfalls

### Pitfall 1: TWB Version String / XSD Filename Mismatch

**What goes wrong:** Writing `version='2026.1'` or `version='26.1.0'` instead of `version='26.1'` in the TWB XML causes Tableau to refuse to load the workbook.
**Why it happens:** The version correspondence is non-obvious. XSD file `twb_2026.1.0.xsd` maps to TWB `version='26.1'` (not `'2026.1'` or `'26.1.0'`).
**How to avoid:** Derive the TWB version string programmatically from the XSD filename using the TableauVersion utility class. Never allow these to be set independently.
**Warning signs:** Any test that validates a TWB against an XSD should also assert the `version` attribute matches.
**Phase:** Phase 1 (generator + manifest). [CITED: tableau-document-schemas README + PITFALLS.md]

### Pitfall 2: lxml Namespace Corruption During Serialization

**What goes wrong:** lxml reorders or removes namespace declarations on the root `<workbook>` element, producing XML that Tableau cannot parse.
**Why it happens:** lxml's default serialization may reorganize namespace prefixes. The TWB format requires `xmlns:user='http://www.tableausoftware.com/xml/user'` on the root element.
**How to avoid:** When parsing templates, preserve original namespace declarations. Use `lxml.etree.XMLParser(remove_blank_text=True)` for clean formatting but do not strip namespaces. Compare the first 5 lines of generated TWB against the template.
**Warning signs:** Any difference in namespace declarations between template and output is a bug.
**Phase:** Phase 1 (generator). [CITED: PITFALLS.md #9]

### Pitfall 3: Missing ManifestByVersion Element

**What goes wrong:** Omitting `<ManifestByVersion />` or using individual feature flags instead causes Tableau to refuse the workbook or silently downgrade it.
**Why it happens:** Historically the manifest required listing individual features. The new simplified approach uses a single self-closing element.
**How to avoid:** Always include `<ManifestByVersion />` inside `<document-format-change-manifest>`. Pin this in templates. Verify it is present in every generated TWB.
**Warning signs:** Any generated TWB missing the `<document-format-change-manifest>` element.
**Phase:** Phase 1 (manifest module). [CITED: tableau-document-schemas README]

### Pitfall 4: hatchling src Layout Misconfiguration

**What goes wrong:** The package installs but imports fail because hatchling does not know the package lives under `src/`.
**Why it happens:** hatchling needs explicit configuration for src layout: `packages = ["src/tableau_agent_toolkit"]` or `sources = ["src"]`.
**How to avoid:** Configure pyproject.toml with `[tool.hatch.build.targets.wheel] packages = ["src/tableau_agent_toolkit"]`. Test with `pip install -e .` then `python -c "import tableau_agent_toolkit"`.
**Warning signs:** ImportError after pip install.
**Phase:** Phase 1 (project scaffolding). [CITED: hatch.pypa.io/latest/config/build/]

### Pitfall 5: PyYAML Unsafe Load

**What goes wrong:** Using `yaml.load()` without a Loader allows arbitrary Python code execution from malicious YAML files.
**Why it happens:** Default yaml.load() with no Loader is a known security issue.
**How to avoid:** Always use `yaml.safe_load()` exclusively. Never use `yaml.load()` without specifying `Loader=yaml.SafeLoader`.
**Warning signs:** Any call to yaml.load() without a Loader argument.
**Phase:** Phase 1 (spec/io.py). [ASSUMED] -- standard Python security practice.

### Pitfall 6: Typer Subcommand Discovery Issues

**What goes wrong:** Typer commands are not discovered or help text is missing when using subcommand groups.
**Why it happens:** Forgetting to call `app.add_typer()` or missing the `name` parameter.
**How to avoid:** Each command group is a separate Typer app registered with `app.add_typer(group_app, name="group-name")`. Each command function needs `@app.command()` decorator with docstring for help text.
**Warning signs:** Running the CLI shows only the top-level help with no subcommands.
**Phase:** Phase 1 (cli.py). [CITED: typer.tiangolo.com/tutorial/subcommands/add-typer/]

## Code Examples

Verified patterns from official sources and the deep research report.

### Pydantic v2 Spec Models

```python
# Source: deep research report spec schema + [VERIFIED: PyPI pydantic 2.13.4]
from pydantic import BaseModel, Field
from enum import Enum
from pathlib import Path

class PackagingEnum(str, Enum):
    twb = "twb"
    twbx = "twbx"

class TemplateSpec(BaseModel):
    id: str = Field(..., description="Logical template name")
    path: Path = Field(..., description="Path to source template workbook")
    required_anchors: list[str] = Field(default_factory=list)

class WorkbookSpec(BaseModel):
    name: str = Field(..., min_length=1, description="Display name / filename base")
    target_tableau_version: str = Field(default="2026.1")
    packaging: PackagingEnum = Field(default=PackagingEnum.twb)
    template: TemplateSpec

class DatasourceSpec(BaseModel):
    name: str = Field(..., min_length=1)
    mode: str = Field(..., description="published, embedded-live, embedded-extract, or custom-sql")
    connection: dict | None = None
    custom_sql_file: str | None = None

class DashboardSpec(BaseModel):
    spec_version: str = Field(default="1.0")
    workbook: WorkbookSpec
    datasources: list[DatasourceSpec] = Field(default_factory=list)
    parameters: list[dict] = Field(default_factory=list)
    calculations: list[dict] = Field(default_factory=list)
    worksheets: list[dict] = Field(default_factory=list)
    dashboards: list[dict] = Field(default_factory=list)
    publish: dict | None = None
    qa: dict | None = None

    @classmethod
    def json_schema(cls) -> dict:
        """Generate JSON Schema for editor support (SPEC-05)."""
        return cls.model_json_schema()
```

### ManifestByVersion Application

```python
# Source: [CITED: github.com/tableau/tableau-document-schemas] official README
from lxml import etree

def apply_manifest_by_version(tree: etree._ElementTree, tableau_version: str) -> None:
    """Apply version attributes and ManifestByVersion to workbook root element."""
    root = tree.getroot()
    # Parse version like "2026.1" -> twb version "26.1"
    parts = tableau_version.split(".")
    twb_version = f"{int(parts[0]) - 2000}.{parts[1]}"

    root.attrib["version"] = twb_version
    root.attrib["original-version"] = twb_version
    root.attrib["source-build"] = "0.0.0 (0000.0.0.0)"
    root.attrib["source-platform"] = "win"

    # Ensure xmlns:user namespace is present
    ns_map = root.nsmap
    if "user" not in ns_map:
        ns_map["user"] = "http://www.tableausoftware.com/xml/user"

    # Find or create document-format-change-manifest
    manifest = root.find(".//document-format-change-manifest")
    if manifest is None:
        manifest = etree.SubElement(root, "document-format-change-manifest")

    # Clear any existing children and add ManifestByVersion
    manifest.clear()
    manifest.append(etree.Element("ManifestByVersion"))
```

### Typer CLI with Subcommand Groups

```python
# Source: [CITED: typer.tiangolo.com/tutorial/subcommands/add-typer/]
# src/tableau_agent_toolkit/cli.py
import typer
from pathlib import Path
from typing import Optional

app = typer.Typer(
    name="tableau-agent-toolkit",
    help="Generate, validate, package, and publish Tableau workbooks from YAML specs.",
)

# --- Spec commands ---
spec_app = typer.Typer(help="Spec file operations")
app.add_typer(spec_app, name="spec")

@spec_app.command("init")
def spec_init(
    output: Path = typer.Option("dashboard_spec.yaml", "--output", "-o", help="Output spec file path"),
    template_id: Optional[str] = typer.Option(None, "--template", help="Template ID to use"),
) -> None:
    """Generate a starter dashboard_spec.yaml from prompts."""
    ...

# --- Generate command ---
@app.command("generate")
def generate(
    spec_path: Path = typer.Argument(..., help="Path to dashboard_spec.yaml", exists=True),
    output: Path = typer.Option("output.twb", "--output", "-o", help="Output TWB path"),
    template: Optional[Path] = typer.Option(None, "--template", help="Override template path"),
) -> None:
    """Generate a Tableau workbook from a spec and template."""
    ...

# --- Validate commands ---
@app.command("validate-xsd")
def validate_xsd(
    twb_path: Path = typer.Argument(..., help="Path to .twb file", exists=True),
    version: str = typer.Option("2026.1", "--version", help="Target Tableau version"),
) -> None:
    """Validate a TWB file against pinned XSD schema."""
    ...

if __name__ == "__main__":
    app()
```

### pyproject.toml for src Layout

```toml
# Source: [CITED: hatch.pypa.io/latest/config/build/] + deep research report
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
    "typer>=0.25",
    "lxml>=6.1",
    "pyyaml>=6.0.3",
    "pydantic-settings>=2.14",
]

[project.scripts]
tableau-agent-toolkit = "tableau_agent_toolkit.cli:app"

[project.optional-dependencies]
dev = [
    "pytest>=9.0",
    "pytest-cov>=7.1",
    "ruff>=0.15",
    "mypy>=2.0",
    "pre-commit>=4.6",
]

[tool.hatch.build.targets.wheel]
packages = ["src/tableau_agent_toolkit"]

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

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| lxml 5.x | lxml 6.1.0 | 2025-2026 | Major version bump; libxml2 updates; API compatible |
| Typer 0.15 | Typer 0.25.1 | 2025-2026 | Significant API improvements; subcommand patterns stable |
| Pydantic v1 | Pydantic v2 (2.13.4) | 2023-2024 | 5-50x faster via Rust core; new model_ API; v1 shim deprecated |
| mypy 1.x | mypy 2.0.0 | 2026 | Major version bump; improved type inference |
| ruff 0.11 | ruff 0.15.12 | 2025-2026 | More rules, faster; format mode stable |
| setuptools/setup.py | hatchling + pyproject.toml | 2023-2024 | Modern build backend; no setup.py needed |
| black + isort + flake8 | ruff (single tool) | 2023-2024 | Orders of magnitude faster; one config |
| tableau-document-schemas (unpublished) | tableau-document-schemas (published Feb 2026) | Feb 2026 | Official supported XSDs; can be vendored with confidence |

**Deprecated/outdated:**
- Document API (tableau/document-api-python): "As-Is" and unsupported since Nov 2022. Do not use as core engine.
- Pydantic v1: In maintenance mode. v2 API only -- no `pydantic.v1` shim.
- `yaml.load()` without Loader: Security vulnerability. Always use `yaml.safe_load()`.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Python 3.12+ is the correct target despite the dev machine having 3.13 | Standard Stack | Low -- 3.12 is specified by PROJECT.md; 3.13 is backward compatible |
| A2 | The deep research report blueprint is authoritative and should be followed | Architecture | Medium -- report was researched thoroughly but is not a locked decision document |
| A3 | A minimal test fixture template (.twb) can be created by hand or extracted from Tableau Desktop | Code Examples | Medium -- without Tableau Desktop, may need to construct a minimal valid TWB XML fixture |
| A4 | lxml 6.1.0 API is backward-compatible with 5.x for the features used (etree.parse, XMLSchema, XPath) | Standard Stack | Low -- lxml maintains API stability across major versions |
| A5 | Vendored XSD files can be downloaded from tableau-document-schemas GitHub releases | Standard Stack | Low -- the repo is public and officially supported |

**If this table is empty:** All claims in this research were verified or cited -- no user confirmation needed.

## Open Questions

1. **Minimal TWB test fixture creation**
   - What we know: Phase 1 needs at least one known-good .twb template for testing. The deep research report references `templates/finance/reconciliation_template.twb`.
   - What's unclear: Whether a minimal TWB fixture can be hand-crafted (without Tableau Desktop) that passes XSD validation. The TWB format has hundreds of elements but the XSD may allow a minimal subset.
   - Recommendation: Attempt to create a minimal valid TWB by hand using the XSD as a guide. If this fails, create a Python script that generates the minimum-valid TWB XML structure. Document this in the test fixtures.

2. **XSD file acquisition method**
   - What we know: The tableau-document-schemas repo is public at github.com/tableau/tableau-document-schemas with schemas/2026_1/twb_2026.1.0.xsd.
   - What's unclear: Whether to vendor the XSD directly in the repo or have the sync script download it. The deep research report recommends vendoring.
   - Recommendation: Vendor the XSD in `third_party/` with a provenance README. The sync script refreshes from upstream. This matches the project decision.

3. **Phase 1 scope boundary for generator patching**
   - What we know: GEN-05 requires patching workbook name, datasources, calculations, worksheets, and dashboards.
   - What's unclear: Whether all five patch types should be fully implemented in Phase 1 or whether some can be stubbed with TODO for Phase 2. The deep research report shows stubs for _patch_datasources, _patch_calculations, _patch_worksheets, _patch_dashboards.
   - Recommendation: Fully implement _patch_workbook_name (trivial). Stub the others with working method signatures that log "not yet implemented" but do not crash. Full patching implementation is a large task that may span Phase 1 and Phase 2.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Core runtime | Yes | 3.13.7 | 3.12+ required per PROJECT.md |
| pip | Package installation | Yes | 25.2 | -- |
| git | Version control | Yes | 2.39.1 | -- |
| pytest | Test runner | Not installed | 9.0.3 (available) | Install in dev deps |
| lxml | XML processing | Not installed | 6.1.0 (available) | Install in core deps |
| Tableau Desktop | Template creation | Unknown | -- | Hand-craft minimal TWB fixture |

**Missing dependencies with no fallback:**
- None -- all required tools are available via pip.

**Missing dependencies with fallback:**
- Tableau Desktop: If not available, hand-craft a minimal TWB fixture XML that passes XSD validation. The XSD defines the minimum required elements.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 |
| Config file | pyproject.toml [tool.pytest.ini_options] -- see Wave 0 |
| Quick run command | `pytest tests/unit -x -q` |
| Full suite command | `pytest --cov=tableau_agent_toolkit --cov-report=term-missing` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SPEC-01 | Pydantic models validate spec YAML structure | unit | `pytest tests/unit/spec/test_models.py -x` | Wave 0 |
| SPEC-02 | load_spec/dump_spec round-trip correctly | unit | `pytest tests/unit/spec/test_io.py -x` | Wave 0 |
| SPEC-03 | Same spec+template+XSD produces identical .twb | unit | `pytest tests/unit/twb/test_determinism.py -x` | Wave 0 |
| SPEC-04 | Error messages reference spec locations | unit | `pytest tests/unit/spec/test_error_messages.py -x` | Wave 0 |
| SPEC-05 | JSON Schema generated from models | unit | `pytest tests/unit/spec/test_json_schema.py -x` | Wave 0 |
| GEN-01 | Generator patches template correctly | unit+integration | `pytest tests/unit/twb/test_generator.py -x` | Wave 0 |
| GEN-02 | Template registry resolves by ID and version | unit | `pytest tests/unit/templates/test_registry.py -x` | Wave 0 |
| GEN-03 | ManifestByVersion inserted correctly | unit | `pytest tests/unit/twb/test_manifest.py -x` | Wave 0 |
| GEN-04 | XSD filename maps to TWB version string | unit | `pytest tests/unit/twb/test_version_mapping.py -x` | Wave 0 |
| GEN-05 | Patching operations modify XML correctly | unit | `pytest tests/unit/twb/test_patching.py -x` | Wave 0 |
| CLI-01 | CLI commands registered and discoverable | integration | `pytest tests/integration/test_cli.py -x` | Wave 0 |
| CLI-02 | Help text generated for all commands | integration | `pytest tests/integration/test_cli.py::test_help_text -x` | Wave 0 |
| CLI-03 | spec init generates valid starter YAML | integration | `pytest tests/integration/test_spec_init.py -x` | Wave 0 |
| PROJ-01 | Package installs and imports work | manual | `pip install -e . && python -c "import tableau_agent_toolkit"` | Wave 0 |
| PROJ-02 | Test infrastructure exists and passes | -- | `pytest` | Wave 0 |
| PROJ-03 | CI workflow runs lint+type+test | manual | `.github/workflows/ci.yml` exists | Wave 0 |
| PROJ-04 | License and docs present | manual | Verify files exist | Wave 0 |
| PROJ-05 | Example specs are valid | integration | `pytest tests/integration/test_example_specs.py -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/unit -x -q`
- **Per wave merge:** `pytest --cov=tableau_agent_toolkit --cov-report=term-missing`
- **Phase gate:** Full suite green + `mypy src` clean + `ruff check .` clean

### Wave 0 Gaps

- [ ] `tests/unit/spec/test_models.py` -- covers SPEC-01, SPEC-05
- [ ] `tests/unit/spec/test_io.py` -- covers SPEC-02
- [ ] `tests/unit/spec/test_error_messages.py` -- covers SPEC-04
- [ ] `tests/unit/twb/test_generator.py` -- covers GEN-01, GEN-05
- [ ] `tests/unit/twb/test_manifest.py` -- covers GEN-03, GEN-04
- [ ] `tests/unit/templates/test_registry.py` -- covers GEN-02
- [ ] `tests/unit/twb/test_determinism.py` -- covers SPEC-03
- [ ] `tests/integration/test_cli.py` -- covers CLI-01, CLI-02
- [ ] `tests/integration/test_spec_init.py` -- covers CLI-03
- [ ] `tests/integration/test_example_specs.py` -- covers PROJ-05
- [ ] `tests/fixtures/` -- minimal TWB fixture for testing
- [ ] `tests/conftest.py` -- shared fixtures (spec loading, template paths)
- [ ] Framework install: `pip install -e ".[dev]"` -- includes pytest, ruff, mypy

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Not in Phase 1 (Phase 3 publisher) |
| V3 Session Management | no | Not in Phase 1 (Phase 3 publisher) |
| V4 Access Control | no | Not in Phase 1 |
| V5 Input Validation | yes | Pydantic v2 BaseModel validators for all spec inputs |
| V6 Cryptography | no | Not in Phase 1 |

### Known Threat Patterns for Python Package + YAML + XML

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| YAML deserialization RCE (yaml.load) | Tampering | Use yaml.safe_load() exclusively -- never yaml.load() without Loader |
| XML External Entity (XXE) | Information Disclosure | lxml defaults to safe parsing; use etree.XMLParser(resolve_entities=False) if loading untrusted XML |
| Path traversal in spec file paths | Tampering | Validate Path arguments stay within expected directories; use resolve() to canonicalize |
| Secrets in committed files | Information Disclosure | pydantic-settings for env-backed creds; pre-commit hook to scan for secrets |
| Supply chain (dependency tampering) | Tampering | Pin dependency versions in pyproject.toml; use pip hash-checking in CI |

## Sources

### Primary (HIGH confidence)

- [PyPI] pydantic 2.13.4, typer 0.25.1, lxml 6.1.0, pyyaml 6.0.3, pytest 9.0.3, ruff 0.15.12, mypy 2.0.0, hatchling 1.29.0, pydantic-settings 2.14.0 -- all verified via `pip index versions` on 2026-05-08
- [github.com/tableau/tableau-document-schemas] -- Official XSD repo README confirming version mapping (twb_2026.1.0.xsd -> version='26.1'), ManifestByVersion pattern, directory structure (schemas/2026_1/), syntactic-only validation, and processContents="skip" elements
- [typer.tiangolo.com/tutorial/subcommands/add-typer/] -- Official Typer docs confirming app.add_typer() pattern for subcommand groups
- [hatch.pypa.io/latest/config/build/] -- Official Hatch docs confirming src layout configuration via packages = ["src/tableau_agent_toolkit"]
- [~/Downloads/deep-research-report.md] -- Project blueprint with repo layout, spec schema design, generator code skeleton, CI configuration, and skill templates

### Secondary (MEDIUM confidence)

- [.planning/research/STACK.md] -- Prior stack research (version numbers now updated)
- [.planning/research/ARCHITECTURE.md] -- Architecture design with component responsibilities and data flow
- [.planning/research/PITFALLS.md] -- Domain pitfalls research with official source citations
- [.planning/research/SUMMARY.md] -- Research synthesis with confidence assessments

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all versions verified against PyPI on 2026-05-08; multiple packages updated from prior research
- Architecture: HIGH -- follows deep research report blueprint; patterns verified against official Typer and Hatch docs
- Pitfalls: HIGH -- sourced from official tableau-document-schemas README and prior PITFALLS.md research
- Code examples: HIGH -- patterns verified against official library documentation

**Research date:** 2026-05-08
**Valid until:** 2026-06-08 (30 days -- stable Python ecosystem)
