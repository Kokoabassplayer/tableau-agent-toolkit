---
name: tableau-dashboard-qa-reviewer
description: Run static and optional sandbox QA checks on a validated Tableau workbook, with optional MCP integration for post-publish quality review
allowed-tools:
  - Bash
  - Read
---

# Tableau Dashboard QA Reviewer

## When to Use
Use this skill after validation to run quality checks on a workbook before packaging and publishing. This skill also supports optional post-publish QA using MCP tools.

## Prerequisites
- A `.twb` file that has passed validation (see tableau-twb-validator skill)
- The `tableau-agent-toolkit` CLI must be installed

## Steps

### 1. Run Static QA Checks
```bash
tableau-agent-toolkit qa static --input workbook.twb --output qa-report.md
```
This runs built-in static QA checks:
- Validates workbook structure integrity
- Checks for common issues (empty containers, unused datasources, missing titles)
- Produces a markdown report with pass/fail per check

### 2. Interpret the QA Report
The report contains:
- **PASS**: Check passed, no action needed
- **FAIL**: Check failed, must fix before publishing
- **WARN**: Warning, review and decide whether to proceed
- **SKIP**: Check skipped (not applicable to this workbook)

If any check fails, the command exits non-zero. Fix issues before proceeding to publish.

### 3. Optional: Post-Publish QA with MCP Tools
After publishing (see tableau-publisher skill), you can use MCP tools to verify the published workbook:

Prerequisites for MCP:
- The Tableau MCP server must be configured (see `.mcp.json` in the project root)
- Environment variables must be set: TABLEAU_SERVER_URL, TABLEAU_PAT_NAME, TABLEAU_PAT_SECRET
- Node.js must be installed (npx is used to run the MCP server)

When MCP is available, you can:
- Query published workbook metadata to confirm the upload succeeded
- Retrieve view images to verify visual rendering
- List data sources to confirm connections are intact
- Explore published content structure

Note: MCP tools are optional. All five skills function without MCP. MCP adds post-publish verification capabilities only.

## Pipeline Context
- Previous step: `tableau-twb-validator` (validates the .twb)
- Next step: `tableau-publisher` (packages and publishes the workbook)

## Error Handling
- If any QA check fails, do not proceed to publish. Fix the underlying issue first.
- If the QA command fails to run, check that the input .twb path is correct.
- If MCP tools are unavailable, proceed with CLI-based QA only. The static QA report provides sufficient pre-publish validation.
