# Phase 5: XSD Path Fix and Validation Pipeline Repair - Research

**Researched:** 2026-05-09
**Domain:** XSD path resolution bug in CLI validate-xsd command
**Confidence:** HIGH

## Summary

The `validate-xsd` CLI command is broken at runtime due to a path mismatch between where `cli.py` resolves the XSD schemas root and where the actual XSD files are stored on disk. The CLI constructs `third_party/tableau_document_schemas/2026_1/twb_2026.1.0.xsd` but the actual file lives at `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd`. The missing `schemas/` subdirectory causes a `FileNotFoundError` every time `tableau-agent-toolkit validate-xsd` is invoked. The fix is a one-line path correction in `cli.py`. Additionally, the integration test suite has a workaround that bypasses the CLI for XSD validation (using `XsdValidator` directly); this workaround should be replaced with a proper CLI invocation once the bug is fixed.

**Primary recommendation:** Fix the `schemas_root` path in `cli.py` line 104 to append `schemas/`, then update `test_agent_pipeline.py` to exercise the actual `validate-xsd` CLI command, and add a dedicated CLI-level integration test for validate-xsd.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | XSD validation against pinned tableau-document-schemas with clear error output (line, column, message) | XsdValidator implementation is correct; bug is in CLI path wiring only. Fix path in cli.py to include `schemas/` subdirectory. |
| VAL-04 | XSD schemas vendored in `third_party/` with sync script (`scripts/sync_tableau_schemas.py`) | Schemas are correctly vendored at `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd` (verified 304,715 bytes). Sync script correctly targets this path. Bug is that CLI does not match the vendored structure. |
| SKILL-03 | `tableau-twb-validator` skill -- XSD + semantic validation report | Skill SKILL.md is correct; it references `tableau-agent-toolkit validate-xsd workbook.twb --version 2026.1`. No changes needed to the skill itself; fixing the CLI unblocks the skill. |
</phase_requirements>

## Standard Stack

### Core (No new dependencies needed)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| lxml | 5.4+ | XSD validation engine | Already in use. `XsdValidator` uses `lxml.etree.XMLSchema` correctly. |
| typer | 0.15+ | CLI framework | Already in use. `validate-xsd` command is registered correctly. |
| pytest | 9.0+ | Test framework | 260 tests already collected. Framework is fully operational. |

**Installation:** No new packages required. This phase is a bug fix using existing dependencies.

## Architecture Patterns

### Bug Location (Root Cause)

```
cli.py line 103-105 (CURRENT - BROKEN):
    schemas_root = (
        Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas"
    )

cli.py line 103-105 (FIXED):
    schemas_root = (
        Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas" / "schemas"
    )
```

### Why the Bug Exists

The `third_party` directory structure follows the upstream `tableau-document-schemas` repo layout:

```
third_party/
  tableau_document_schemas/        <-- sync script writes HERE (TARGET_DIR)
    README.md
    schemas/                       <-- intermediate directory from upstream repo
      2026_1/
        twb_2026.1.0.xsd
```

The sync script (`scripts/sync_tableau_schemas.py` line 16) correctly targets:
```python
TARGET_DIR = Path(__file__).parent.parent / "third_party" / "tableau_document_schemas" / "schemas"
```

But `cli.py` line 104 omits the `schemas/` subdirectory:
```python
schemas_root = Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas"
```

The `XsdValidator._resolve_xsd()` method then appends `2026_1/twb_2026.1.0.xsd` relative to `schemas_root`, producing the wrong path.

### Path Resolution Chain

| Component | Resolves To | Correct? |
|-----------|-------------|----------|
| `cli.py` schemas_root | `.../third_party/tableau_document_schemas` | NO - missing `schemas/` |
| `XsdValidator._resolve_xsd("2026.1")` | `schemas_root / "2026_1" / "twb_2026.1.0.xsd"` | YES (relative logic is correct) |
| Combined CLI path | `.../third_party/tableau_document_schemas/2026_1/twb_2026.1.0.xsd` | NO - FileNotFoundError |
| Actual file location | `.../third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd` | Ground truth |
| Test fixture schemas_root | `tests/fixtures/schemas` | YES - tests pass because fixtures match expected structure |
| Test _resolve_xsd | `tests/fixtures/schemas/2026_1/twb_2026.1.0.xsd` | YES - test fixtures have no extra nesting |

### Unit Tests vs CLI Runtime Divergence

The unit tests in `tests/unit/validation/test_xsd.py` use `FIXTURES_DIR / "schemas"` as `schemas_root`, which resolves to `tests/fixtures/schemas/2026_1/twb_2026.1.0.xsd`. This matches the `_resolve_xsd` logic (`schemas_root / "2026_1" / "twb_2026.1.0.xsd"`), so unit tests pass. The bug only manifests when the CLI constructs its own `schemas_root` path pointing to the production `third_party/` directory.

### Integration Test Workaround

`tests/integration/test_agent_pipeline.py` lines 91-103 explicitly document the bug and work around it:

```python
# NOTE: The validate-xsd CLI command has a pre-existing path issue where it
# looks for schemas at third_party/tableau_document_schemas/ but the actual
# schema files are under third_party/tableau_document_schemas/schemas/. We
# use XsdValidator directly with the fixture schemas root to test the actual
# validation logic while the CLI path issue is resolved separately.
fixture_schemas_root = FIXTURES_DIR / "schemas"
xsd_validator = XsdValidator(schemas_root=fixture_schemas_root)
xsd_result = xsd_validator.validate(valid_twb, tableau_version="2026.1")
```

This bypasses the CLI entirely, meaning the `validate-xsd` CLI command has zero test coverage for actual validation execution.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path resolution | Custom path detection logic | Fix existing path constant in cli.py | The architecture is correct; only the constant is wrong. Do not add fallback logic, environment variables, or config files. |
| CLI testing | Manual CLI invocation tests | Typer CliRunner | Already in use. The fix should add a test using `runner.invoke(app, ["validate-xsd", str(valid_twb)])`. |

## Common Pitfalls

### Pitfall 1: Fixing in the Wrong Place
**What goes wrong:** Modifying `XsdValidator._resolve_xsd()` to add `schemas/` to the path instead of fixing `cli.py`.
**Why it happens:** The validator is the component that raises `FileNotFoundError`, so it looks like the right place to fix.
**How to avoid:** The validator correctly resolves paths relative to its `schemas_root` parameter. The bug is in the CLI which passes the wrong `schemas_root`. Fix cli.py, not xsd.py. Changing `_resolve_xsd` would break the unit tests that pass `tests/fixtures/schemas` as root.
**Warning signs:** If fixing xsd.py causes test_xsd.py failures, you fixed the wrong file.

### Pitfall 2: Forgetting the `--input` Flag Inconsistency
**What goes wrong:** Adding a test using `--input` flag for validate-xsd when it actually uses a positional argument.
**Why it happens:** Other commands (validate-semantic, qa static, package, publish) use `--input` as an option. validate-xsd uses a positional `twb_path` argument.
**How to avoid:** Check cli.py carefully. validate-xsd takes `twb_path` as a positional argument, not `--input`. The skill SKILL.md uses `tableau-agent-toolkit validate-xsd workbook.twb --version 2026.1` (positional, no flag).
**Warning signs:** Test using `["validate-xsd", "--input", "workbook.twb"]` will fail with unknown option error.

### Pitfall 3: Pip-Installed Package Path Resolution
**What goes wrong:** The fix uses `Path(__file__).parent.parent.parent` which only works in development (source layout). When pip-installed, the path chain differs.
**Why it happens:** With hatch's src layout, `cli.py` is at `src/tableau_agent_toolkit/cli.py`. After pip install, it moves to `site-packages/tableau_agent_toolkit/cli.py` -- only 3 parents, same as now. The `third_party/` directory won't exist in site-packages.
**How to avoid:** This is a pre-existing architectural issue (not introduced by this fix). The current approach only works in development. For this phase, we fix the immediate bug (missing `schemas/`). A pip-installable approach would need `importlib.resources` or packaging the XSD files as package data, which is out of scope.
**Warning signs:** None for this phase -- the fix is additive only.

## Code Examples

### The Fix (cli.py line 103-105)

```python
# BEFORE (BROKEN):
schemas_root = (
    Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas"
)

# AFTER (FIXED):
schemas_root = (
    Path(__file__).parent.parent.parent / "third_party" / "tableau_document_schemas" / "schemas"
)
```

### Updated Integration Test (test_agent_pipeline.py)

Replace the workaround in `test_full_spec_to_package_pipeline` with actual CLI invocation:

```python
# BEFORE (workaround):
fixture_schemas_root = FIXTURES_DIR / "schemas"
xsd_validator = XsdValidator(schemas_root=fixture_schemas_root)
xsd_result = xsd_validator.validate(valid_twb, tableau_version="2026.1")
assert xsd_result.valid, ...

# AFTER (proper CLI test):
result = runner.invoke(
    app,
    ["validate-xsd", str(valid_twb), "--version", "2026.1"],
)
assert result.exit_code == 0, f"validate-xsd failed: {result.output}"
assert "Valid" in result.output or "passes" in result.output
```

### New CLI Integration Test for validate-xsd

```python
class TestValidateXsdExecution:
    """Test validate-xsd CLI command execution (not just --help)."""

    def test_validate_xsd_valid_twb_exits_zero(self) -> None:
        """validate-xsd on valid_full.twb should exit 0 and print Valid."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["validate-xsd", str(valid_twb)])
        assert result.exit_code == 0
        assert "Valid" in result.output or "passes" in result.output

    def test_validate_xsd_invalid_twb_exits_nonzero(self, tmp_path: Path) -> None:
        """validate-xsd on malformed XML should exit 1 with error details."""
        invalid_twb = tmp_path / "invalid.twb"
        invalid_twb.write_text('<?xml version="1.0"?>\n<invalid_root />', encoding="utf-8")
        result = runner.invoke(app, ["validate-xsd", str(invalid_twb)])
        assert result.exit_code != 0
        assert "Invalid" in result.output or "Line" in result.output

    def test_validate_xsd_with_version_option(self) -> None:
        """validate-xsd --version 2026.1 should work the same as default."""
        valid_twb = FIXTURES_DIR / "valid_full.twb"
        result = runner.invoke(app, ["validate-xsd", str(valid_twb), "--version", "2026.1"])
        assert result.exit_code == 0
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| N/A (bug fix) | N/A (bug fix) | N/A | This is a pure bug fix with no technology changes. |

**No deprecations in this phase.**

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `third_party/tableau_document_schemas/schemas/` directory structure is the canonical location and will not be restructured | Architecture | Path fix would need updating again |
| A2 | The `valid_full.twb` test fixture passes XSD validation against the real `twb_2026.1.0.xsd` schema | Code Examples | Integration test would fail if fixture is not XSD-conformant |
| A3 | When pip-installed, the `third_party/` path resolution via `Path(__file__)` does not need to work (development-only usage) | Common Pitfalls | Production users would need a different path resolution strategy |

**Verification of assumptions:**
- A1: [VERIFIED: sync_tableau_schemas.py TARGET_DIR, actual filesystem]
- A2: [VERIFIED: test_agent_pipeline.py already validates valid_full.twb with XsdValidator successfully]
- A3: [ASSUMED] - The project is at v0.1.0 and CLI usage appears development-focused. This may need addressing in a future phase.

## Open Questions

1. **Should the SKILL.md prerequisite path be updated?**
   - What we know: `skills/tableau-twb-validator/SKILL.md` line 16 says "XSD schemas vendored in `third_party/tableau_document_schemas/`" which is technically correct (the schemas ARE under that directory, just in a subdirectory).
   - What's unclear: Whether this path reference should be more precise (`third_party/tableau_document_schemas/schemas/`).
   - Recommendation: Minor update to clarify the path. Low priority since the skill itself does not need changes.

2. **Should there be a defensive path fallback in cli.py?**
   - What we know: The current code has no fallback. If `third_party/` is missing or restructured, it fails with FileNotFoundError.
   - What's unclear: Whether a fallback (checking both paths) would be more robust.
   - Recommendation: No fallback. Keep it simple. The path structure is controlled by the sync script and should be deterministic.

## Environment Availability

Step 2.6: SKIPPED (no new external dependencies -- this is a code-only bug fix using existing libraries)

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml (tool.pytest.ini_options) |
| Quick run command | `python -m pytest tests/unit/validation/test_xsd.py tests/integration/test_cli.py::TestValidateXsdCommand -x` |
| Full suite command | `python -m pytest tests/ -x` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| VAL-01 | validate-xsd CLI resolves XSD path correctly and produces validation results | integration | `python -m pytest tests/integration/test_cli.py -k "validate_xsd" -x` | Partial -- only --help tests exist; execution tests needed in Wave 0 |
| VAL-04 | Vendored XSD schemas accessible from CLI at correct path | integration | `python -m pytest tests/integration/test_cli.py::TestValidateXsdExecution -x` | Wave 0 needed |
| SKILL-03 | tableau-twb-validator skill references working validate-xsd CLI | integration | `python -m pytest tests/integration/test_agent_pipeline.py::TestFullPipeline -x` | Exists but uses workaround; needs update in Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/unit/validation/test_xsd.py tests/integration/test_cli.py -k "validate_xsd" -x`
- **Per wave merge:** `python -m pytest tests/ -x`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/integration/test_cli.py` -- Add `TestValidateXsdExecution` class with actual CLI execution tests (not just --help)
- [ ] `tests/integration/test_agent_pipeline.py` -- Remove workaround in `test_full_spec_to_package_pipeline`, replace with CLI invocation
- [ ] Remove the `from tableau_agent_toolkit.validation.xsd import XsdValidator` import from test_agent_pipeline.py if no longer needed

## Security Domain

> This phase modifies a file path constant only. No new security surface area is introduced.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V5 Input Validation | yes | Path validation via `Path.exists()` check in XsdValidator.__init__ |
| V6 Cryptography | no | N/A |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal | Tampering | XsdValidator validates schemas_root exists before use; CLI constructs path from __file__, not user input |

## Sources

### Primary (HIGH confidence)
- Source code: `src/tableau_agent_toolkit/cli.py` lines 103-106 (bug location)
- Source code: `src/tableau_agent_toolkit/validation/xsd.py` lines 61-88 (correct relative path resolution)
- Source code: `scripts/sync_tableau_schemas.py` line 16 (canonical TARGET_DIR)
- Filesystem: `third_party/tableau_document_schemas/schemas/2026_1/twb_2026.1.0.xsd` (verified 304,715 bytes)
- Test code: `tests/unit/validation/test_xsd.py` (unit tests pass, SCHEMAS_ROOT = fixtures/schemas)
- Test code: `tests/integration/test_agent_pipeline.py` lines 91-103 (documented workaround)
- Milestone audit: `.planning/v1.0-MILESTONE-AUDIT.md` (identified bug, affected requirements)

### Secondary (MEDIUM confidence)
- Previous phase plan: `.planning/phases/01-spec-generation-cli-and-project-scaffolding/01-04-PLAN.md` line 220 (original path was specified without `schemas/`)
- Previous phase summary: `.planning/phases/02-validation-and-qa/02-02-SUMMARY.md` (sync script ran, populated real XSD)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - no new dependencies; existing stack verified
- Architecture: HIGH - root cause identified with line precision; fix is single-line path change
- Pitfalls: HIGH - pitfalls identified from code review and test analysis

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (stable; bug is structural, not version-dependent)
