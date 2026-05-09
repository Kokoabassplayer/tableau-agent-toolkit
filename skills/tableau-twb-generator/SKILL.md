---
name: tableau-twb-generator
description: Generate a Tableau workbook (.twb) from a YAML spec and template using the tableau-agent-toolkit pipeline
allowed-tools:
  - Bash
  - Read
---

# Tableau TWB Generator

## When to Use
Use this skill when you need to generate a Tableau workbook (.twb) from a dashboard_spec.yaml file. This is the second step in the pipeline after spec authoring.

## Prerequisites
- A valid `dashboard_spec.yaml` file must exist (see tableau-dashboard-spec-writer skill)
- A template `.twb` file must exist or be referenced in the spec
- The `tableau-agent-toolkit` CLI must be installed

## Steps

### 1. Verify Prerequisites
Check that:
- The spec file exists and is valid YAML
- The template path referenced in the spec exists (or the template ID is registered in the catalog)

### 2. Generate the Workbook
```bash
tableau-agent-toolkit generate dashboard_spec.yaml --output output.twb
```
Or with an explicit template override:
```bash
tableau-agent-toolkit generate dashboard_spec.yaml --output output.twb --template path/to/template.twb
```

### 3. Verify Output
- Check that `output.twb` was created
- If warnings were printed, review them -- they may indicate issues that will fail validation

### 4. Next Steps
After generation, validate the workbook:
- XSD validation: see `tableau-twb-validator` skill
- Semantic validation: see `tableau-twb-validator` skill
- QA checks: see `tableau-dashboard-qa-reviewer` skill

## Output
- A `.twb` file at the specified output path
- Console output confirming generation or listing warnings

## Error Handling
- If generation fails with a template error, check that the template path in the spec is correct and the file exists
- If generation fails with a spec validation error, return to the tableau-dashboard-spec-writer skill to fix the spec
- If warnings appear about unsupported features, review and decide whether to proceed or update the spec

## Pipeline Context
- Previous step: `tableau-dashboard-spec-writer` (creates the spec)
- Next step: `tableau-twb-validator` (validates the generated .twb)
