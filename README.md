# tableau-agent-toolkit

An open-source plugin for AI coding agents (Claude Code, Codex, and compatible harnesses) that generates, validates, packages, and publishes Tableau workbooks from structured YAML dashboard specifications.

Five composable agent skills give your AI a deterministic pipeline from business brief to published workbook.

## Installation

### Claude Code

```bash
# Install as a plugin
claude plugin add https://github.com/Kokoabassplayer/tableau-agent-toolkit
```

Or clone and link manually:

```bash
git clone https://github.com/Kokoabassplayer/tableau-agent-toolkit.git
cd tableau-agent-toolkit
claude plugin add .
```

### Codex

```bash
# Clone and add plugin manifest
git clone https://github.com/Kokoabassplayer/tableau-agent-toolkit.git
# Add to your Codex project's plugin configuration
```

### Python CLI (standalone)

The toolkit also works as a standalone CLI without an AI agent. Clone the repo first, then install in editable mode:

```bash
git clone https://github.com/Kokoabassplayer/tableau-agent-toolkit.git
cd tableau-agent-toolkit
pip install -e .
```

## Agent Skills

Once installed, your AI agent can invoke five composable skills in sequence:

| Skill | Purpose | Trigger |
|-------|---------|---------|
| `tableau-dashboard-spec-writer` | Convert a business brief into `dashboard_spec.yaml` | "Create a dashboard spec for..." |
| `tableau-twb-generator` | Generate `.twb` from spec + template | "Generate a workbook from this spec" |
| `tableau-twb-validator` | XSD + semantic validation of `.twb` files | "Validate this workbook" |
| `tableau-dashboard-qa-reviewer` | Static QA checks and optional sandbox test | "Run QA on this workbook" |
| `tableau-publisher` | Package and publish to Tableau Server/Cloud | "Publish this workbook" |

### Pipeline Flow

```
business brief → spec init → generate → validate-xsd → validate-semantic → qa static → package → publish
```

The same `dashboard_spec.yaml` + pinned template + pinned XSD version produces the same `.twb` every run.

## Environment Variables

For publishing to Tableau Server/Cloud, set these environment variables:

```bash
export TABLEAU_SERVER_URL="https://your-tableau-server"
export TABLEAU_SITE_NAME=""              # leave empty for default site
export TABLEAU_PAT_NAME="your-pat-name"
export TABLEAU_PAT_SECRET="your-pat-secret"
```

## Features

- **Spec-driven**: Define dashboards in structured YAML with Pydantic v2 validation
- **Template-first generation**: Patch known-good TWB templates via lxml
- **Three-tier validation**: XSD structural, semantic cross-reference, static QA
- **Deterministic output**: Same inputs produce byte-identical `.twb` files
- **Packaging**: Create `.twbx` packaged workbooks
- **Publishing**: Deploy to Tableau Server/Cloud with PAT auth, REST fallback, async chunked upload
- **MCP integration**: Optional Tableau MCP server connection for post-publish QA

## CLI Commands

```bash
tableau-agent-toolkit spec init              # Scaffold a starter dashboard_spec.yaml
tableau-agent-toolkit generate               # Generate .twb from spec and template
tableau-agent-toolkit validate-xsd           # Validate against pinned XSD schemas
tableau-agent-toolkit validate-semantic      # Semantic cross-reference checks
tableau-agent-toolkit qa static              # Static QA checks
tableau-agent-toolkit package                # Package .twb into .twbx
tableau-agent-toolkit publish                # Publish to Tableau Server/Cloud
```

## License

Apache-2.0
