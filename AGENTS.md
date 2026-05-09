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
