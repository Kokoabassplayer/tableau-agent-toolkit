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
- `workbook`: name, target_tableau_version, template reference (id, path, required_anchors)
- `datasources`: list of connection definitions (name, connection type, server, database, schema)
- `parameters`: reusable parameters (name, data_type, default_value)
- `calculations`: Tableau calculation formulas (name, formula, datasource)
- `worksheets`: sheet definitions with datasource references, column selections, filters
- `dashboards`: layout with zone references to worksheets

### 4. Validate the Spec
```bash
python -c "from tableau_agent_toolkit.spec.io import load_spec; load_spec('dashboard_spec.yaml')"
```
If validation passes, the spec is structurally valid.

## Reference
- Example specs: `examples/specs/` directory
  - `finance-reconciliation.dashboard_spec.yaml`
  - `executive-kpi.dashboard_spec.yaml`
  - `ops-monitoring.dashboard_spec.yaml`
- Spec models: `src/tableau_agent_toolkit/spec/models.py`
- The spec uses Pydantic v2 validation -- any field not in the model will cause a validation error

## Error Handling
- If `spec init` fails, check that the CLI is installed and the output path is writable
- If Pydantic validation fails, the error message will name the invalid field and expected type
- If template_id is not in the registry, note it in the spec and the generator will flag it

## Pipeline Context
- Previous step: None (this is the first step in the pipeline)
- Next step: `tableau-twb-generator` (generates the .twb from the spec)
