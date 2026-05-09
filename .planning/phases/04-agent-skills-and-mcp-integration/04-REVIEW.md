---
phase: 04-agent-skills-and-mcp-integration
reviewed: 2026-05-09T12:00:00Z
depth: quick
files_reviewed: 11
files_reviewed_list:
  - skills/tableau-dashboard-spec-writer/SKILL.md
  - skills/tableau-twb-generator/SKILL.md
  - skills/tableau-twb-validator/SKILL.md
  - skills/tableau-dashboard-qa-reviewer/SKILL.md
  - skills/tableau-publisher/SKILL.md
  - tests/integration/test_agent_pipeline.py
  - tests/unit/test_skill_manifests.py
  - .claude-plugin/plugin.json
  - .codex-plugin/plugin.json
  - .mcp.json
  - AGENTS.md
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-05-09T12:00:00Z
**Depth:** quick
**Files Reviewed:** 11
**Status:** issues_found

## Summary

Reviewed all 11 Phase 4 files at quick depth (pattern-matching for hardcoded secrets, dangerous functions, debug artifacts, empty catches, and insecure patterns). All scans came back clean -- no hardcoded secrets, no dangerous function calls, no debug artifacts, no empty catch blocks.

Two info-level observations were identified: (1) the integration test bypasses the `validate-xsd` CLI command, using `XsdValidator` directly, leaving a gap in CLI coverage, and (2) `TestSkillContent` lacks the `_skill_exists` skip guard that `TestSkillFrontmatter` uses, creating an inconsistency in test resilience.

No critical or warning issues found. The skill manifests, plugin configs, MCP config, and agent instructions are structurally sound and consistent.

## Critical Issues

(None found.)

## Warnings

(None found.)

## Info

### IN-01: Integration test bypasses validate-xsd CLI command

**File:** `tests/integration/test_agent_pipeline.py:91-103`
**Issue:** The `test_full_spec_to_package_pipeline` test uses `XsdValidator` directly instead of invoking the CLI `validate-xsd` command. A comment explains this is a workaround for a pre-existing path issue where the CLI looks for schemas at `third_party/tableau_document_schemas/` but the actual files are under `third_party/tableau_document_schemas/schemas/`. This means the `validate-xsd` CLI command is not exercised by the integration test suite.
**Fix:** When the CLI path issue is resolved, replace the direct `XsdValidator` call with a `CliRunner` invocation of `validate-xsd` to restore end-to-end CLI coverage.

### IN-02: TestSkillContent lacks skip guard for missing skills

**File:** `tests/unit/test_skill_manifests.py:188-310`
**Issue:** The `TestSkillContent` class (lines 188-310) reads SKILL.md files directly without the `_skill_exists` guard used by `TestSkillFrontmatter` (lines 140-186). If a skill directory is removed or renamed, `TestSkillFrontmatter` tests would gracefully skip while `TestSkillContent` tests would raise `FileNotFoundError`. All 5 skills currently exist, so this is not a runtime issue today, but the inconsistency makes the test suite less resilient to future changes.
**Fix:** Add `if not _skill_exists(skill_name): pytest.skip(...)` at the start of each `TestSkillContent` test method, matching the pattern in `TestSkillFrontmatter`.

---

_Reviewed: 2026-05-09T12:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: quick_
