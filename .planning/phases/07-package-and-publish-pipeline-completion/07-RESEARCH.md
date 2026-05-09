# Phase 7: Package and Publish Pipeline Completion - Research

**Researched:** 2026-05-09
**Domain:** CLI wiring, publish fallback, spec-driven publish configuration
**Confidence:** HIGH

## Summary

Phase 7 wires three Phase 3 components that were built but never connected to production code: `PackageVerifier`, `RESTFallbackPublisher`, and `PublishSpec`. All three classes exist with complete implementations and unit tests. The work is pure CLI wiring -- importing these classes into `cli.py`, adding the missing integration paths, and adding a `--spec` option to the publish command.

The gap was identified in the v1.0 Milestone Audit: `PackageVerifier` is never imported by `cli.py` or the publish pipeline (only unit tests use it); `RESTFallbackPublisher` exists in `publishing/fallback.py` with full REST sign-in and multipart/mixed publish logic but is never called from the publish command; and `PublishSpec` on `DashboardSpec` provides project/site/mode configuration that the publish CLI ignores, reading only from CLI arguments.

**Primary recommendation:** Add three targeted wiring changes to `cli.py`: (1) call `PackageVerifier.verify()` after `WorkbookPackager.package()` in the `package` command, (2) wrap TSC publish in try/except with `RESTFallbackPublisher` as fallback in the `publish` command, and (3) add `--spec` option to the publish command that loads `DashboardSpec.publish` as defaults when CLI args are not provided. Each wiring change is small (5-15 lines) and follows the existing patterns in `cli.py`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-02 | Package integrity verification -- validate inner .twb + confirm zip structure matches Tableau Desktop output | PackageVerifier.verify() exists in packaging/verifier.py with VerificationResult dataclass. Wire into package CLI after WorkbookPackager.package(). [VERIFIED: code read] |
| PUB-01 | TSC publisher with PAT auth as default backend | TSCPublisher works via CLI. PublishSpec model in DashboardSpec provides project/site/mode. Wire spec.publish as CLI arg defaults. [VERIFIED: code read] |
| PUB-02 | REST API fallback publisher for edge cases TSC does not cover | RESTFallbackPublisher exists in publishing/fallback.py with full sign-in, project resolution, multipart/mixed publish. Wire as try/except fallback after TSC publish. [VERIFIED: code read] |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| typer | 0.25+ | CLI framework (already in use) | Existing CLI pattern. No new dependencies needed. [VERIFIED: pyproject.toml] |
| pydantic | 2.13+ | PublishSpec model validation | Existing PublishSpec model in spec/models.py. [VERIFIED: pyproject.toml] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| (none new) | -- | -- | Phase 7 adds zero new dependencies |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| try/except fallback | Publisher chain of responsibility pattern | Chain pattern is over-engineered for 2 publishers. try/except is simpler, explicit, matches audit recommendation. |
| --spec on publish | --config flag | --spec matches existing validate-semantic --spec pattern already in the codebase. |

**Installation:**
```bash
# No new dependencies required
```

**Version verification:** No new packages. All required packages already in pyproject.toml:
- typer >= 0.25 (verified pyproject.toml)
- pydantic >= 2.13 (verified pyproject.toml)
- pydantic-settings >= 2.14 (verified pyproject.toml)

## Architecture Patterns

### Recommended Project Structure
```
src/tableau_agent_toolkit/
  cli.py                    # MODIFY: wire PackageVerifier, RESTFallbackPublisher, PublishSpec
  packaging/
    verifier.py             # EXISTS: PackageVerifier.verify() -- UNWIRED
  publishing/
    fallback.py             # EXISTS: RESTFallbackPublisher.publish() -- UNWIRED
    publisher.py            # EXISTS: TSCPublisher.publish() -- WIRED
    receipt.py              # EXISTS: PublishReceipt -- WIRED
  spec/
    models.py               # EXISTS: PublishSpec model -- WIRED (in spec)
    io.py                   # EXISTS: load_spec() -- WIRED (in generate)

tests/
  integration/
    test_cli.py             # MODIFY: add tests for new wiring
  unit/
    packaging/
      test_packager.py      # EXISTS: covers PackageVerifier already
    publishing/
      test_publisher.py     # EXISTS: covers TSCPublisher and RESTFallbackPublisher
```

### Pattern 1: Post-Package Verification (PKG-02)
**What:** After `WorkbookPackager.package()` creates the .twbx, immediately run `PackageVerifier.verify()` on the output.
**When to use:** Every invocation of the `package` CLI command.
**Example:**
```python
# Source: Existing codebase pattern from cli.py package command (line 184-189)
from tableau_agent_toolkit.packaging.verifier import PackageVerifier

@app.command("package")
def package(
    input_path: Path = typer.Option(..., "--input", help="Path to .twb file", exists=True),
    output: Path = typer.Option("output.twbx", "--output", "-o", help="Output .twbx path"),
) -> None:
    packager = WorkbookPackager()
    result = packager.package(input_path, output)
    typer.echo(f"Packaged: {result.output_path}")

    # NEW: Verify integrity after packaging
    verifier = PackageVerifier()
    verification = verifier.verify(result.output_path)
    if verification.valid:
        typer.echo(f"Verification: Package integrity confirmed")
    else:
        for error in verification.errors:
            typer.echo(f"Verification error: {error}", err=True)
        sys.exit(1)
```

### Pattern 2: TSC Fallback to REST (PUB-02)
**What:** Try TSC publish first. If TSC raises an exception, fall back to RESTFallbackPublisher.
**When to use:** Every publish operation where TSC might fail.
**Example:**
```python
# Source: Existing codebase pattern from cli.py publish command (lines 255-273)
from tableau_agent_toolkit.publishing.fallback import RESTFallbackPublisher

# After TSC publish fails:
publisher = TSCPublisher(settings=settings)
try:
    receipt = publisher.publish(
        file_path=publish_path,
        project_name=project,
        mode=mode,
        server_url=server,
        site_id=site,
    )
except Exception as e:
    typer.echo(f"TSC publish failed: {e}", err=True)
    typer.echo("Attempting REST API fallback...", err=True)
    fallback = RESTFallbackPublisher(settings=settings)
    receipt = fallback.publish(
        file_path=publish_path,
        project_name=project,
        mode=mode,
        server_url=server,
        site_id=site,
    )
    typer.echo(f"Published via REST API fallback")
```

### Pattern 3: Spec-Driven Publish (PUB-01 partial)
**What:** Read `DashboardSpec.publish` for server/project/site/mode defaults when not provided via CLI args.
**When to use:** When user provides `--spec dashboard_spec.yaml` to the publish command.
**Example:**
```python
# Source: Follows existing --spec pattern from validate-semantic command (cli.py line 131-139)
@app.command("publish")
def publish(
    input_path: Path = typer.Option(..., "--input", help="Path to file", exists=True),
    server: Optional[str] = typer.Option(None, "--server", help="Tableau Server URL"),
    project: Optional[str] = typer.Option(None, "--project", help="Target project name"),
    site: str = typer.Option("", "--site", help="Target site contentUrl"),
    mode: str = typer.Option("CreateNew", "--mode", help="Publish mode"),
    spec: Optional[Path] = typer.Option(None, "--spec", help="Path to spec for publish defaults"),
) -> None:
    # Load spec-driven defaults
    effective_server = server
    effective_project = project
    effective_site = site
    effective_mode = mode

    if spec:
        dashboard_spec = load_spec(spec)
        if dashboard_spec.publish:
            pub = dashboard_spec.publish
            effective_server = effective_server or ""  # server not in PublishSpec, from env
            effective_project = effective_project or pub.project
            effective_site = effective_site or pub.site_id
            effective_mode = effective_mode or pub.mode.value

    # Validate required args
    if not effective_project:
        typer.echo("Error: --project is required (or provide --spec with publish.project)", err=True)
        raise typer.Exit(code=1)
```

### Anti-Patterns to Avoid
- **Catching all exceptions for fallback:** Only catch known TSC exceptions (RuntimeError, server response errors), not KeyboardInterrupt or TypeError. Broad catch hides bugs.
- **Making --spec required:** The publish command must still work without --spec (pure CLI args). Spec is optional defaults, not a replacement.
- **Overriding explicit CLI args with spec values:** CLI args should take precedence over spec values. Spec provides defaults, CLI overrides them.
- **Modifying PublishSpec model:** The model is already correct. Only the CLI wiring is missing.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Fallback publish logic | Custom retry/chain pattern | Simple try/except with RESTFallbackPublisher | Only 2 publishers. Chain pattern is over-engineering. |
| Spec-to-CLI arg merging | Custom merge logic | Simple `or` operator chain: `cli_arg or spec_value` | Explicit, readable, no edge cases. |
| Verification reporting | Custom status format | VerificationResult dataclass (already exists) | Consistent with existing result types. |

**Key insight:** All three components already exist with complete implementations. This phase is pure wiring -- importing and calling existing code from the right places in cli.py.

## Common Pitfalls

### Pitfall 1: Verification Failure Blocking Package
**What goes wrong:** PackageVerifier finds a real integrity issue but the user cannot get the .twbx file at all because sys.exit(1) runs before the file path is printed.
**Why it happens:** Printing happens before verification, but the exit code prevents downstream use.
**How to avoid:** Print the packaged path BEFORE running verification. If verification fails, the .twbx still exists on disk (user can inspect it), but the non-zero exit code signals the failure.
**Warning signs:** Tests that check only for exit code without verifying output messages.

### Pitfall 2: Silent Fallback Masking TSC Configuration Issues
**What goes wrong:** TSC publish fails due to misconfigured PAT credentials, then REST fallback also fails with the same credentials, but the user sees "REST API fallback failed" and thinks the problem is REST-specific.
**Why it happens:** Both publishers use the same Settings/PAT credentials.
**How to avoid:** Print the TSC error message before attempting fallback. Users should see the original TSC error to diagnose root cause (e.g., bad credentials, wrong site, network issues).
**Warning signs:** Error messages that only show "REST API fallback failed" without the original TSC error.

### Pitfall 3: Spec Missing Publish Section
**What goes wrong:** User provides `--spec dashboard_spec.yaml` but the spec has no `publish:` section. The code tries to access `spec.publish.project` and crashes.
**Why it happens:** PublishSpec is `PublishSpec | None = None` in DashboardSpec.
**How to avoid:** Always check `dashboard_spec.publish is not None` before accessing its fields. When publish section is absent, fall through to CLI arg validation (current behavior).
**Warning signs:** AttributeError on `None.project`.

### Pitfall 4: Server URL Not in PublishSpec
**What goes wrong:** PublishSpec has project, site_id, and mode, but no server_url field. Users expect `--spec` to provide everything needed for publishing, but server URL still requires --server or TABLEAU_SERVER_URL env var.
**Why it happens:** PublishSpec was designed without server_url (security decision: server URLs should come from env vars, not spec files).
**How to avoid:** Document clearly that --server or TABLEAU_SERVER_URL is always required for publishing. Spec provides project/site/mode only. Validate server URL presence before attempting publish.
**Warning signs:** User provides --spec without --server and gets a confusing error.

### Pitfall 5: Overwrite Mode String vs Enum Mismatch
**What goes wrong:** CLI accepts `--mode CreateNew` as string, but PublishSpec.mode is `PublishModeEnum`. When reading from spec, `pub.mode.value` returns the string.
**Why it happens:** Typer passes strings; PublishSpec stores enums.
**How to avoid:** When reading from spec, use `pub.mode.value` to get the string. When passing to publishers, both accept string "CreateNew"/"Overwrite".
**Warning signs:** TypeError when mixing enum and string types.

## Code Examples

### Existing Code to Reference (NO CHANGES NEEDED)

**PackageVerifier.verify()** -- already complete in `packaging/verifier.py`:
```python
# Source: packaging/verifier.py (read from codebase)
class PackageVerifier:
    def verify(self, twbx_path: Path) -> VerificationResult:
        # Checks: valid ZIP, contains .twb, .twb parses as XML
        ...
```

**RESTFallbackPublisher.publish()** -- already complete in `publishing/fallback.py`:
```python
# Source: publishing/fallback.py (read from codebase)
class RESTFallbackPublisher:
    def __init__(self, settings: Settings | None = None) -> None: ...
    def publish(self, file_path, project_name, mode, server_url, site_id) -> PublishReceipt: ...
```

**PublishSpec model** -- already complete in `spec/models.py`:
```python
# Source: spec/models.py (read from codebase)
class PublishSpec(BaseModel):
    project: str = Field(..., min_length=1)
    site_id: str = Field(default="")
    mode: PublishModeEnum = Field(default=PublishModeEnum.CreateNew)
    as_job: bool = Field(default=False)
    skip_connection_check: bool = Field(default=False)
```

### CLI Wiring Changes (ONLY CHANGES NEEDED)

**1. Package command -- add verification (cli.py)**
```python
# Source: Extension of existing cli.py package command
from tableau_agent_toolkit.packaging.verifier import PackageVerifier

@app.command("package")
def package(
    input_path: Path = typer.Option(..., "--input", help="Path to .twb file to package", exists=True),
    output: Path = typer.Option("output.twbx", "--output", "-o", help="Output .twbx path"),
) -> None:
    """Package a .twb file into a .twbx archive."""
    packager = WorkbookPackager()
    result = packager.package(input_path, output)
    typer.echo(f"Packaged: {result.output_path}")
    if result.warnings:
        for w in result.warnings:
            typer.echo(f"Warning: {w}", err=True)

    # Verify package integrity
    verifier = PackageVerifier()
    verification = verifier.verify(result.output_path)
    if verification.valid:
        typer.echo("Verification: Package integrity confirmed")
    else:
        for error in verification.errors:
            typer.echo(f"Verification error: {error}", err=True)
        raise typer.Exit(code=1)
```

**2. Publish command -- add --spec option and REST fallback (cli.py)**
```python
# Source: Extension of existing cli.py publish command
from tableau_agent_toolkit.publishing.fallback import RESTFallbackPublisher

@app.command("publish")
def publish(
    input_path: Path = typer.Option(..., "--input", help="Path to .twb or .twbx file", exists=True),
    server: Optional[str] = typer.Option(None, "--server", help="Tableau Server URL"),
    project: Optional[str] = typer.Option(None, "--project", help="Target project name"),
    site: str = typer.Option("", "--site", help="Target site contentUrl"),
    mode: str = typer.Option("CreateNew", "--mode", help="Publish mode: CreateNew or Overwrite"),
    spec_path: Optional[Path] = typer.Option(None, "--spec", help="Path to spec for publish defaults"),
) -> None:
    """Publish a workbook to Tableau Server or Cloud."""
    # Resolve spec-driven defaults
    if spec_path:
        dashboard_spec = load_spec(spec_path)
        if dashboard_spec.publish:
            pub = dashboard_spec.publish
            project = project or pub.project
            site = site or pub.site_id
            mode = mode if mode != "CreateNew" or pub.mode.value != "CreateNew" else mode
            # Note: server_url not in PublishSpec -- comes from env/CLI

    # Validate required args
    if not project:
        typer.echo("Error: --project is required (or provide --spec with publish.project)", err=True)
        raise typer.Exit(code=1)

    # Load server URL from env if not provided via CLI
    settings = Settings()
    effective_server = server or settings.server_url
    if not effective_server:
        typer.echo("Error: --server or TABLEAU_SERVER_URL env var required", err=True)
        raise typer.Exit(code=1)

    # Validate mode
    if mode not in ("CreateNew", "Overwrite"):
        typer.echo(f"Error: Invalid mode '{mode}'. Must be CreateNew or Overwrite.", err=True)
        raise typer.Exit(code=1)

    # ... auto-package .twb if needed (existing code) ...

    # Publish with fallback
    publisher = TSCPublisher(settings=settings)
    try:
        receipt = publisher.publish(
            file_path=publish_path,
            project_name=project,
            mode=mode,
            server_url=effective_server,
            site_id=site,
        )
    except Exception as e:
        typer.echo(f"TSC publish failed: {e}", err=True)
        typer.echo("Attempting REST API fallback...", err=True)
        try:
            fallback = RESTFallbackPublisher(settings=settings)
            receipt = fallback.publish(
                file_path=publish_path,
                project_name=project,
                mode=mode,
                server_url=effective_server,
                site_id=site,
            )
        except Exception as fallback_e:
            typer.echo(f"REST API fallback also failed: {fallback_e}", err=True)
            raise typer.Exit(code=1)

    # ... print receipt (existing code) ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Unwired verifier | Post-package verification in CLI | Phase 7 | Users get immediate feedback on package integrity |
| TSC-only publish | TSC with REST fallback | Phase 7 | Resilience against TSC library edge cases |
| CLI-args-only publish | Spec-driven publish with CLI overrides | Phase 7 | Users can define publish config in spec, override per invocation |

**Deprecated/outdated:**
- None for this phase. All existing code remains valid.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | PublishSpec intentionally omits server_url (security: server in env vars, not spec files) | Architecture Patterns | If wrong, users may expect --spec to provide server URL. Currently --server or TABLEAU_SERVER_URL is always required. |
| A2 | REST fallback should catch Exception (broad) to handle all TSC failures, not specific exception types | Architecture Patterns | If TSC adds new exception types, broad catch handles them. But could mask programming errors. |
| A3 | CLI args always override spec values for --mode when explicitly provided | Architecture Patterns | Distinguishing "user typed --mode CreateNew" from "default CreateNew" is tricky. May need Optional mode parameter. |

## Open Questions

1. **Should --mode use Optional[str] to distinguish default from explicit?**
   - What we know: Current mode default is "CreateNew" (string). When reading from spec, pub.mode has a value. If user didn't type --mode, we can't tell if "CreateNew" is default or explicit.
   - What's unclear: Whether Typer supports distinguishing default from explicit for string options.
   - Recommendation: Use `Optional[str] = None` for mode. If None, check spec. If spec has no mode, default to "CreateNew". This cleanly separates "user didn't provide" from "user provided CreateNew".

2. **Should REST fallback be opt-in or automatic?**
   - What we know: REST fallback exists for edge cases TSC doesn't cover. Both use same credentials.
   - What's unclear: Whether fallback should always attempt or only when user opts in.
   - Recommendation: Always attempt fallback automatically. If TSC fails, REST fallback is the safety net. No additional flag needed.

3. **Should verification failure be a warning or an error?**
   - What we know: PackageVerifier catches real issues (corrupt ZIP, malformed XML). But the .twbx file still exists on disk.
   - What's unclear: Whether to exit non-zero (blocking downstream publish) or just print warnings.
   - Recommendation: Exit non-zero. A corrupt .twbx should not be published. Users can see the file path in output before the error.

## Environment Availability

Step 2.6: SKIPPED (no new external dependencies -- phase only changes existing code)

All required tools and libraries are already installed and verified:
- Python 3.12+: Available
- pytest 9.0+: Available
- typer, pydantic, pydantic-settings, lxml, tableauserverclient: All in pyproject.toml

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `python -m pytest tests/ -x -q -k "package or publish"` |
| Full suite command | `python -m pytest tests/ -x --tb=short` |

### Phase Requirements to Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-02 | Package command runs verifier and reports integrity | integration | `python -m pytest tests/integration/test_cli.py::TestPackageCommand -x -q` | Expand existing |
| PUB-02 | Publish command falls back to REST when TSC fails | integration | `python -m pytest tests/integration/test_cli.py::TestPublishCommand -x -q` | Expand existing |
| PUB-01 | Publish command reads spec.publish when --spec provided | integration | `python -m pytest tests/integration/test_cli.py::TestPublishCommand -x -q` | Expand existing |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/ -x -q`
- **Per wave merge:** `python -m pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green (283 tests baseline + new tests)

### Wave 0 Gaps
- None -- existing test infrastructure covers all phase requirements. Tests will be added to existing `tests/integration/test_cli.py` and potentially `tests/unit/packaging/test_packager.py` / `tests/unit/publishing/test_publisher.py`.

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | PAT auth via TSC.PersonalAccessTokenAuth (unchanged) |
| V3 Session Management | yes | TSC context manager (unchanged) |
| V4 Access Control | yes | Project/site resolution (unchanged) |
| V5 Input Validation | yes | Pydantic PublishSpec validation; Typer path validation |
| V6 Cryptography | no | No new crypto concerns |

### Known Threat Patterns for CLI Wiring

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Spec file path injection | Tampering | Typer `exists=True` validates path; Pydantic validates content |
| Credential logging in error | Information Disclosure | Error messages should not include PAT secret; Settings uses SecretStr |
| Spec overriding server URL | Spoofing | PublishSpec intentionally omits server_url; comes from env/CLI only |

## Sources

### Primary (HIGH confidence)
- Codebase inspection: `cli.py`, `packaging/verifier.py`, `publishing/fallback.py`, `publishing/publisher.py`, `spec/models.py`, `security/settings.py` [Read 2026-05-09]
- v1.0 Milestone Audit Report (`.planning/v1.0-MILESTONE-AUDIT.md`) [Read 2026-05-09]
- Phase 3 Research (`.planning/phases/03-packaging-and-publishing/03-RESEARCH.md`) [Read 2026-05-09]
- Phase 3 Review (`.planning/phases/03-packaging-and-publishing/03-REVIEW.md`) [Read 2026-05-09]
- Existing test suite: 283 tests passing [Verified 2026-05-09]

### Secondary (MEDIUM confidence)
- Phase 3 Plan 03 Summary (`.planning/phases/03-packaging-and-publishing/03-03-SUMMARY.md`) [Read 2026-05-09]

### Tertiary (LOW confidence)
- None -- all findings verified against source code.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - zero new dependencies; all libraries already in use
- Architecture: HIGH - wiring changes follow exact patterns from existing cli.py
- Pitfalls: HIGH - derived from codebase analysis and audit report
- Code examples: HIGH - verified against actual source code

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (30 days - stable codebase, no external dependencies)
