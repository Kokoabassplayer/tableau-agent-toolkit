# tableau-agent-toolkit

An open-source Python-first toolkit that generates, validates, packages, and publishes
Tableau workbooks from structured YAML dashboard specifications.

## Getting Started

```bash
pip install -e .
```

### Quick Example

```python
from tableau_agent_toolkit.spec.io import load_spec
from pathlib import Path

spec = load_spec(Path("dashboard_spec.yaml"))
print(spec.workbook.name)
```

## Features

- **Spec-driven**: Define dashboards in structured YAML with Pydantic v2 validation
- **Template-first generation**: Patch known-good TWB templates via lxml
- **XSD validation**: Validate generated workbooks against pinned Tableau schemas
- **Semantic validation**: Check sheet references, calc names, action targets
- **Packaging**: Create .twbx packaged workbooks
- **Publishing**: Deploy to Tableau Server via REST API with PAT auth
- **Agent-ready**: Dual plugin for Claude Code and Codex with reusable skills

## License

Apache-2.0
