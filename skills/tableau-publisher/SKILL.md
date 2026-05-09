---
name: tableau-publisher
description: Package and publish a validated Tableau workbook to Tableau Server or Tableau Cloud with PAT authentication
allowed-tools:
  - Bash
  - Read
---

# Tableau Publisher

## When to Use
Use this skill to publish a validated and QA-checked workbook to Tableau Server or Tableau Cloud. This is the final step in the pipeline.

## Prerequisites
- A `.twb` or `.twbx` file that has passed validation and QA checks
- Environment variables must be set:
  - `TABLEAU_PAT_NAME`: Personal Access Token name
  - `TABLEAU_PAT_SECRET`: Personal Access Token secret value
- Target server URL and project name
- The `tableau-agent-toolkit` CLI must be installed

**Important**: Only publish workbooks that have passed both XSD validation and semantic validation. Publishing unvalidated workbooks may result in errors on the server.

## Steps

### 1. Package (if needed)
If you have a `.twb` file (not yet packaged):
```bash
tableau-agent-toolkit package --input workbook.twb --output workbook.twbx
```

Note: The publish command auto-packages .twb files, but explicit packaging gives you a chance to verify the .twbx before uploading.

### 2. Publish
```bash
tableau-agent-toolkit publish --input workbook.twbx --server https://tableau.example.com --project "My Project"
```

Options:
- `--site`: Target site contentUrl (omit or use empty string for default site)
- `--mode CreateNew`: Create a new workbook (default)
- `--mode Overwrite`: Overwrite an existing workbook with the same name

Example with all options:
```bash
tableau-agent-toolkit publish --input workbook.twbx --server https://tableau.example.com --project "Sales Dashboards" --site "marketing" --mode Overwrite
```

### 3. Verify the Publish Receipt
On success, the command outputs:
- Workbook name and ID (confirmed uploaded)
- Project name and ID (confirmed placement)
- Site (confirmed targeting)
- Server URL (confirmed destination)
- File size (confirms complete upload)
- Verification details (if available)

Review the receipt to confirm the workbook landed in the correct project and site.

## Pipeline Context
- Previous steps: `tableau-twb-validator` (validation) and `tableau-dashboard-qa-reviewer` (QA checks)
- Optional next step: `tableau-dashboard-qa-reviewer` skill's MCP section for post-publish verification

## Error Handling
- If `TABLEAU_PAT_NAME` or `TABLEAU_PAT_SECRET` is not set, the command prints an error. Set the environment variables and retry.
- If the server URL is unreachable, check the URL and network connectivity.
- If the project does not exist, create it in Tableau Server first, or use an existing project name.
- If `--mode Overwrite` fails, the workbook may not exist yet. Try `--mode CreateNew` first.
- If upload fails for large files (>64 MB), the publisher uses chunked upload automatically.
