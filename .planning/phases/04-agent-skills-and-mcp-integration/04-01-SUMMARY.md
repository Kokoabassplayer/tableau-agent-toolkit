---
phase: 04-agent-skills-and-mcp-integration
plan: 01
subsystem: agent-skills
tags: [claude-code, codex, mcp, plugin-manifest, skills, agents-md]

# Dependency graph
requires:
  - phase: 01-spec-generation-cli-scaffolding
    provides: CLI commands (spec init, generate) and Pydantic models referenced by skills
  - phase: 03-packaging-and-publishing
    provides: CLI commands (validate-xsd, validate-semantic, qa static, package, publish) referenced by skills
provides:
  - Dual plugin manifests (.claude-plugin/plugin.json, .codex-plugin/plugin.json) with 5 skill references
  - .mcp.json with Tableau MCP server wiring using env var references
  - AGENTS.md with Codex project instructions
  - CLAUDE.md updated with skill listing and pipeline order
  - tableau-dashboard-spec-writer skill (SKILL.md with frontmatter)
  - tableau-twb-generator skill (SKILL.md with frontmatter)
  - Validation test suite (test_skill_manifests.py) for all declarative infrastructure
affects: [04-02, 04-03, 04-04]

# Tech tracking
tech-stack:
  added: []
  patterns: [declarative-plugin-manifest, dual-platform-plugin, incremental-skill-tests]

key-files:
  created:
    - .claude-plugin/plugin.json
    - .codex-plugin/plugin.json
    - .mcp.json
    - AGENTS.md
    - skills/tableau-dashboard-spec-writer/SKILL.md
    - skills/tableau-twb-generator/SKILL.md
    - tests/unit/test_skill_manifests.py
  modified:
    - CLAUDE.md

key-decisions:
  - "Used pytest.skip() for incremental skill tests so Wave 1 suite passes while Wave 2 skills are pending"
  - "Corrected PROJECT_ROOT path resolution from 4-level to 3-level parent traversal for worktree structure"

patterns-established:
  - "Plugin manifest pattern: JSON with name, description, version, skills array, optional mcpServers"
  - "SKILL.md pattern: YAML frontmatter (name, description, allowed-tools) followed by Markdown body"
  - "Incremental test pattern: pytest.skip() for skills not yet created, avoiding CI failures"

requirements-completed: [SKILL-01, SKILL-02, SKILL-06, SKILL-07, MCP-02]

# Metrics
duration: 6min
completed: 2026-05-09
---

# Phase 04 Plan 01: Plugin Foundation and First Two Pipeline Skills Summary

**Dual plugin manifests (Claude + Codex) with 5 skill references, MCP config using env var secrets, AGENTS.md for Codex, and spec-writer + twb-generator skills with incremental validation tests**

## Performance

- **Duration:** 6 min
- **Started:** 2026-05-09T05:47:46Z
- **Completed:** 2026-05-09T05:54:06Z
- **Tasks:** 2
- **Files modified:** 8

## Accomplishments
- Created dual plugin manifests enabling skill discovery in both Claude Code and Codex
- Established MCP server config with no hardcoded secrets (all credentials via ${TABLEAU_*} env vars)
- Built AGENTS.md as the Codex-equivalent of CLAUDE.md with commands table, architecture, and pipeline order
- Created spec-writer and twb-generator skills with proper frontmatter and CLI command references
- Delivered validation test suite (25 passing, 15 skipped for Wave 2 skills) ensuring structural correctness

## Task Commits

Each task was committed atomically:

1. **Task 1: Create plugin manifests, MCP config, AGENTS.md, and update CLAUDE.md** - `0524c80` (feat)
2. **Task 2: Create spec-writer and twb-generator skills with validation tests** - `a98e1e6` (feat)

## Files Created/Modified
- `.claude-plugin/plugin.json` - Claude Code plugin manifest with 5 skills and inline MCP servers
- `.codex-plugin/plugin.json` - Codex plugin manifest with 5 skills (no MCP servers)
- `.mcp.json` - Tableau MCP server config using env var references only
- `AGENTS.md` - Codex project instructions with overview, commands, testing, architecture, pipeline order
- `CLAUDE.md` - Updated GSD:skills section to list five agent skills and pipeline order
- `skills/tableau-dashboard-spec-writer/SKILL.md` - Skill for converting business briefs into dashboard_spec.yaml
- `skills/tableau-twb-generator/SKILL.md` - Skill for generating .twb from spec and template
- `tests/unit/test_skill_manifests.py` - Validation tests for all declarative infrastructure

## Decisions Made
- Used `pytest.skip()` instead of `pytest.skipif()` for incremental skill tests -- skipif is a decorator-only API in pytest, while skip() works as an imperative call inside test methods
- Corrected PROJECT_ROOT from 4-level to 3-level parent traversal to match actual test file location within the worktree structure (tests/unit/ is 2 levels deep from project root)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed PROJECT_ROOT path resolution in test file**
- **Found during:** Task 2 (running validation tests)
- **Issue:** Plan specified `Path(__file__).parent.parent.parent.parent` (4 levels up) but tests/unit/ is only 2 levels deep from project root, causing FileNotFoundError
- **Fix:** Changed to `Path(__file__).resolve().parent.parent.parent` (3 levels up)
- **Files modified:** tests/unit/test_skill_manifests.py
- **Verification:** All Wave 1 tests pass (15/15)
- **Committed in:** a98e1e6 (Task 2 commit)

**2. [Rule 1 - Bug] Fixed pytest.skipif() to pytest.skip() for conditional skips**
- **Found during:** Task 2 (running full test suite)
- **Issue:** `pytest.skipif()` is a decorator-only API, not callable as a function; caused AttributeError across all parametrized skill tests
- **Fix:** Replaced `pytest.skipif(not _skill_exists(...), reason=...)` with `if not _skill_exists(...): pytest.skip(reason=...)`
- **Files modified:** tests/unit/test_skill_manifests.py
- **Verification:** Full suite: 25 passed, 15 skipped (expected for missing Wave 2 skills)
- **Committed in:** a98e1e6 (Task 2 commit)

**3. [Rule 2 - Missing Critical] Added skip logic to test_skill_file_exists**
- **Found during:** Task 2 (running full test suite)
- **Issue:** test_skill_file_exists would fail for Wave 2 skills not yet created, breaking incremental CI
- **Fix:** Added same skip-if-not-exists guard as other parametrized tests
- **Files modified:** tests/unit/test_skill_manifests.py
- **Verification:** 15 skipped for missing skills instead of failing
- **Committed in:** a98e1e6 (Task 2 commit)

---

**Total deviations:** 3 auto-fixed (1 blocking, 1 bug, 1 missing critical)
**Impact on plan:** All auto-fixes necessary for test correctness and incremental CI compatibility. No scope creep.

## Issues Encountered
None beyond the deviations documented above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Plugin foundation and first two skills ready for Wave 2 (plans 04-02 and 04-03)
- Plan 04-02 will create the remaining 3 skills (validator, qa-reviewer, publisher) which will unskip the 15 currently-skipped tests
- Plan 04-04 will add pipeline integration tests

---
*Phase: 04-agent-skills-and-mcp-integration*
*Completed: 2026-05-09*

## Self-Check: PASSED

All 8 created/modified files verified present on disk.
Both task commits verified in git log (0524c80, a98e1e6).
Wave 1 tests: 25 passed, 15 skipped (expected).
