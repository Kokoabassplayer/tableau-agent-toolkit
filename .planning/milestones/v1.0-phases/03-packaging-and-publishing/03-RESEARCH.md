# Phase 3: Packaging and Publishing - Research

**Researched:** 2026-05-09
**Domain:** .twbx packaging, Tableau Server publishing, TSC library integration
**Confidence:** HIGH

## Summary

Phase 3 adds the ability to package `.twb` files into `.twbx` archives and publish workbooks to Tableau Server/Cloud. The packaging layer uses Python's stdlib `zipfile` module to create ZIP archives matching Tableau Desktop's output structure. The publishing layer uses `tableauserverclient` (TSC) v0.40 as the exclusive backend for PAT authentication, project/site resolution, chunked upload (automatic for files >= 64 MB), and async job tracking. A REST API fallback publisher handles edge cases TSC does not cover.

The existing codebase already has scaffolding ready for this phase: `security/settings.py` has a stub for PAT env vars, `spec/models.py` has `PackagingEnum` and a `publish: dict | None` field, and the Typer CLI in `cli.py` follows a clean pattern for adding new commands and subcommand groups.

**Primary recommendation:** Use TSC v0.40 for all publishing operations. Activate the `security/settings.py` stub with `pydantic-settings`. Create two new modules (`packaging/` and `publishing/`) following the existing pattern of dataclass results + Pydantic config models. Add `tableauserverclient>=0.40` to `pyproject.toml` dependencies.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | `.twbx` packager that bundles `.twb` with assets into correct zip structure | zipfile stdlib; ZIP_DEFLATED compression; .twb as root entry |
| PKG-02 | Package integrity verification -- validate inner .twb + confirm zip structure matches Tableau Desktop output | zipfile.is_zipfile(); namelist() check; lxml parse inner .twb |
| PUB-01 | TSC publisher with PAT auth as default backend | TSC.PersonalAccessTokenAuth; pydantic-settings for env vars |
| PUB-02 | REST API fallback publisher for edge cases TSC does not cover | requests (TSC dep); multipart/mixed content type; direct REST calls |
| PUB-03 | Publish modes: CreateNew and Overwrite, with project/site resolution | TSC.Server.PublishMode enum; server.projects.filter(); site_id in PAT auth |
| PUB-04 | Async publish support with chunked upload for workbooks > 64 MB | TSC auto-chunks at 64MB (FILESIZE_LIMIT); as_job=True returns JobItem; server.jobs.wait_for_job() |
| PUB-05 | Publish receipt with workbook ID, project/site target, mode, and verification results | Pydantic PublishReceipt model; populate from WorkbookItem/JobItem attrs |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tableauserverclient | 0.40 | Publish workbooks, PAT auth, server operations | Official Tableau library. PROJECT.md mandates TSC as exclusive publisher. v0.40 is latest (2026-02-03). [VERIFIED: PyPI registry] |
| pydantic-settings | 2.14+ | Load TABLEAU_ env vars for PAT credentials | Already in dependencies. Used for Settings class in security/settings.py. [VERIFIED: pyproject.toml] |
| zipfile (stdlib) | stdlib | Create .twbx packaged workbooks | .twbx is a ZIP archive. No third-party library needed. PROJECT.md constraint. |
| requests | (TSC dep) | REST API fallback publisher direct HTTP calls | Already installed as TSC dependency. Avoid adding new HTTP library. [VERIFIED: pip show TSC requires requests] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| lxml | 6.1+ | Verify inner .twb in packaged .twbx (PKG-02) | Already in dependencies. Parse inner XML to confirm valid TWB. |
| pytest | 9.0+ | Unit tests with mocked TSC, integration tests | Standard test framework already in use. |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| TSC | tabcmd CLI | PROJECT.md forbids: "Use as the exclusive publisher backend -- do not shell out to tabcmd" |
| TSC | Direct REST API | TSC wraps REST API with Python types and auth. Only use direct REST as fallback (PUB-02). |
| zipfile stdlib | shutil.make_archive | Less control over internal structure. zipfile gives precise control over archive entries. |

**Installation:**
```bash
pip install tableauserverclient>=0.40
# Note: requests comes as TSC dependency -- no separate install needed
```

**Version verification:**
```
tableauserverclient 0.40 -- latest, verified via pip index (2026-05-09)
```

**Dependency update required:** Add `tableauserverclient>=0.40` to `pyproject.toml` dependencies list.

## Architecture Patterns

### Recommended Project Structure
```
src/tableau_agent_toolkit/
├── packaging/              # NEW - .twbx packaging
│   ├── __init__.py
│   ├── packager.py         # WorkbookPackager class
│   └── verifier.py         # Package integrity verification (PKG-02)
├── publishing/             # NEW - Server publishing
│   ├── __init__.py
│   ├── publisher.py        # TSC publisher (PUB-01, PUB-03, PUB-04)
│   ├── fallback.py         # REST API fallback (PUB-02)
│   └── receipt.py          # PublishReceipt Pydantic model (PUB-05)
├── security/
│   └── settings.py         # ACTIVATE stub fields for PAT credentials
├── spec/
│   └── models.py           # EXPAND publish: dict to PublishSpec model
└── cli.py                  # ADD package and publish commands
```

### Pattern 1: TSC Publisher with PAT Auth
**What:** Authenticate with Tableau Server using Personal Access Token, resolve project by name, publish workbook.
**When to use:** Every publish operation (PUB-01).
**Example:**
```python
# Source: TSC official docs + verified API signatures
import tableauserverclient as TSC

# Auth -- PAT credentials from env vars
auth = TSC.PersonalAccessTokenAuth(
    token_name=settings.pat_name,
    personal_access_token=settings.pat_secret,
    site_id=settings.site_id,  # contentUrl, empty string for default site
)
server = TSC.Server(settings.server_url, use_server_version=True)

with server.auth.sign_in(auth):
    # Resolve project by name to get project_id (UUID required)
    # Option 1: filter (returns QuerySet)
    projects = server.projects.filter(name="My Project")
    project_id = projects[0].id

    # Option 2: iterate all projects
    all_projects, _ = server.projects.get()
    project_id = next(p.id for p in all_projects if p.name == "My Project")

    # Create workbook item
    wb_item = TSC.WorkbookItem(project_id=project_id, name="My Workbook")

    # Publish -- TSC auto-chunks at 64MB, as_job for async
    result = server.workbooks.publish(
        wb_item,
        file_path="workbook.twbx",
        mode=TSC.Server.PublishMode.Overwrite,
        as_job=True,  # Returns JobItem for async tracking
    )

    # Wait for async job completion
    if isinstance(result, TSC.JobItem):
        job = server.jobs.wait_for_job(result, timeout=300)
```

### Pattern 2: .twbx Packaging
**What:** Create a .twbx ZIP archive containing the .twb file and any assets.
**When to use:** Every packaging operation (PKG-01).
**Example:**
```python
# Source: zipfile stdlib docs + Tableau .twbx format knowledge
import zipfile
from pathlib import Path

def package_twbx(twb_path: Path, output_path: Path, assets: list[Path] | None = None) -> Path:
    """Package a .twb file into a .twbx ZIP archive.

    Tableau Desktop .twbx structure:
    - workbook.twb (root level, matches workbook name)
    - Data/ (optional, for embedded extracts)
    - Images/ (optional, for embedded images)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Add .twb as root-level entry
        zf.write(twb_path, twb_path.name)
        # Add any assets
        for asset in (assets or []):
            zf.write(asset, asset.name)
    return output_path
```

### Pattern 3: Publish Receipt
**What:** Structured record of a publish operation's outcome.
**When to use:** Every publish operation (PUB-05).
**Example:**
```python
# Source: Follows existing Pydantic model pattern from spec/models.py
from pydantic import BaseModel, Field
from datetime import datetime

class PublishReceipt(BaseModel):
    """Receipt confirming a workbook publish operation."""
    workbook_id: str = Field(..., description="Server-assigned workbook UUID")
    workbook_name: str = Field(..., description="Published workbook name")
    project_id: str = Field(..., description="Target project UUID")
    project_name: str = Field(..., description="Target project name")
    site_id: str = Field(..., description="Target site contentUrl")
    server_url: str = Field(..., description="Tableau Server URL")
    mode: str = Field(..., description="Publish mode: CreateNew or Overwrite")
    published_at: datetime = Field(default_factory=datetime.now)
    file_path: str = Field(..., description="Path of published file")
    file_size_bytes: int = Field(..., description="Published file size")
    verification_passed: bool = Field(True, description="Post-publish verification result")
    verification_details: list[str] = Field(default_factory=list)
```

### Anti-Patterns to Avoid
- **Shelling out to tabcmd:** PROJECT.md explicitly forbids. Use TSC library exclusively.
- **Storing PAT secrets in YAML spec files:** Security constraint in PROJECT.md. Load from env vars only.
- **Hardcoding project_id in spec:** Projects are server-specific. Use project name in spec, resolve to UUID at publish time.
- **Ignoring async publish for large files:** TSC returns JobItem when as_job=True. Must wait for job completion, not assume instant success.
- **Treating site_id as display name:** site_id is the contentUrl (URL path segment after /site/), NOT the display name. Empty string for default site.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Chunked file upload for large workbooks | Custom chunking logic | TSC auto-chunking | TSC checks FILESIZE_LIMIT (64MB) and auto-chunks via InitiateFileUpload + AppendToFileUpload REST endpoints. Verified in TSC source. |
| PAT authentication flow | Custom auth headers | TSC.PersonalAccessTokenAuth | Handles token exchange, session management, and auth headers automatically. |
| Project name to UUID resolution | Manual REST calls | server.projects.filter() or server.projects.get() | TSC provides typed filtering with pagination. |
| Job status polling | Custom polling loop | server.jobs.wait_for_job() | Uses exponential backoff, handles timeout, raises on failure. |

**Key insight:** TSC v0.40 handles the full publish lifecycle. The only reason for a REST API fallback (PUB-02) is edge cases like custom HTTP options, proxy configurations, or unpublished REST endpoints that TSC does not yet wrap.

## Common Pitfalls

### Pitfall 1: Project ID is a UUID, Not a Name
**What goes wrong:** TSC.WorkbookItem requires `project_id` as a UUID string. Passing a project name causes a server error.
**Why it happens:** The CLI accepts `--project "My Project"` but TSC needs the UUID.
**How to avoid:** Always resolve project name to UUID using `server.projects.filter(name=project_name)` before creating WorkbookItem.
**Warning signs:** ServerResponseError with "Invalid project ID" or 400 status.

### Pitfall 2: site_id vs Site Display Name
**What goes wrong:** Using the site's display name instead of its contentUrl for PAT auth.
**Why it happens:** Users see "Marketing Team" in the UI but the contentUrl is "marketingteam" (no spaces, lowercase).
**How to avoid:** Document that TABLEAU_SITE_ID must be the contentUrl (URL segment after /site/). Empty string for default site. Default site on Tableau Cloud is NOT empty -- must provide a value.
**Warning signs:** 401 Unauthorized when signing in with PAT.

### Pitfall 3: Async Publish Without Job Tracking
**What goes wrong:** Calling `publish(as_job=True)` and immediately returning success without waiting for the job.
**Why it happens:** TSC returns a JobItem, not a WorkbookItem, when as_job=True. The job may fail asynchronously.
**How to avoid:** Always call `server.jobs.wait_for_job(job, timeout=N)` after async publish. Check `job.finish_code` (0 = success).
**Warning signs:** Publish appears to succeed but workbook doesn't appear on server.

### Pitfall 4: .twbx Without Proper ZIP Structure
**What goes wrong:** Creating a ZIP with nested directory structure that doesn't match Tableau Desktop output.
**Why it happens:** zipfile preserves directory paths by default.
**How to avoid:** The .twb file must be at the root level of the ZIP archive. Use `arcname` parameter: `zf.write(twb_path, arcname=twb_path.name)`.
**Warning signs:** Tableau Desktop cannot open the .twbx, or opens it as corrupted.

### Pitfall 5: TSC Not in Dependencies
**What goes wrong:** Code imports TSC but `pip install tableau-agent-toolkit` doesn't pull it in.
**Why it happens:** TSC is installed locally for development but not listed in pyproject.toml dependencies.
**How to avoid:** Add `tableauserverclient>=0.40` to the `dependencies` list in pyproject.toml as the first task in this phase.
**Warning signs:** ImportError when running CLI in a fresh environment.

### Pitfall 6: Context Manager vs Manual sign_in/sign_out
**What goes wrong:** Using `server.auth.sign_in()` without matching `sign_out()`, leaving sessions open.
**Why it happens:** The non-context-manager form requires explicit cleanup.
**How to avoid:** Always use `with server.auth.sign_in(auth):` pattern. TSC supports context manager protocol.
**Warning signs:** Session exhaustion on Tableau Server after multiple publish operations.

## Code Examples

Verified patterns from official sources and codebase inspection:

### TSC Auth and Publish (Full Flow)
```python
# Source: TSC v0.40 API reference + verified method signatures
import tableauserverclient as TSC
from tableau_agent_toolkit.security.settings import Settings

settings = Settings()  # Loads TABLEAU_* env vars

auth = TSC.PersonalAccessTokenAuth(
    token_name=settings.pat_name,
    personal_access_token=settings.pat_secret,
    site_id=settings.site_id,
)
server = TSC.Server(settings.server_url, use_server_version=True)

with server.auth.sign_in(auth):
    # Resolve project
    project_id: str | None = None
    for project in server.projects.filter(name=target_project):
        project_id = project.id
        break
    if not project_id:
        raise ValueError(f"Project '{target_project}' not found")

    # Create workbook item
    wb_item = TSC.WorkbookItem(project_id=project_id)
    # Name defaults to filename stem if not set

    # Determine if async needed (file > 64MB)
    file_size = Path(file_path).stat().st_size
    use_async = file_size > 64 * 1024 * 1024  # 64MB threshold

    result = server.workbooks.publish(
        wb_item,
        file_path,
        TSC.Server.PublishMode.Overwrite,
        as_job=use_async,
    )

    if isinstance(result, TSC.JobItem):
        job = server.jobs.wait_for_job(result, timeout=600)
        # Get the actual workbook from the job's workbook_id
        wb_item = server.workbooks.get_by_id(job.workbook_id)
    else:
        wb_item = result
```

### Activating security/settings.py
```python
# Source: Existing stub in src/tableau_agent_toolkit/security/settings.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Tableau Server connection settings loaded from environment variables.

    Set these via environment variables:
      TABLEAU_SERVER_URL    - Tableau Server URL (e.g. https://tableau.example.com)
      TABLEAU_PAT_NAME      - Personal Access Token name
      TABLEAU_PAT_SECRET    - Personal Access Token secret
      TABLEAU_SITE_ID       - Site contentUrl (empty string for default site)
    """
    model_config = SettingsConfigDict(env_prefix="TABLEAU_")

    server_url: str = ""
    pat_name: str = ""
    pat_secret: str = ""
    site_id: str = ""
```

### PublishSpec Model (expand spec/models.py publish field)
```python
# Source: Follows existing Pydantic pattern in spec/models.py
class PublishModeEnum(str, Enum):
    CreateNew = "CreateNew"
    Overwrite = "Overwrite"

class PublishSpec(BaseModel):
    """Publish configuration within a dashboard spec."""
    model_config = {"extra": "forbid"}

    server_url: str | None = Field(default=None, description="Override server URL (env var preferred)")
    project: str = Field(..., min_length=1, description="Target project name on server")
    site_id: str = Field(default="", description="Target site contentUrl (empty for default)")
    mode: PublishModeEnum = Field(default=PublishModeEnum.CreateNew, description="Publish mode")
    as_job: bool = Field(default=False, description="Use async publishing")
    skip_connection_check: bool = Field(default=False, description="Skip connection check at upload")
```

### CLI Commands (package and publish)
```python
# Source: Follows existing Typer CLI pattern in cli.py
@app.command("package")
def package(
    input_path: Path = typer.Argument(..., help="Path to .twb file", exists=True),
    output: Path = typer.Option("output.twbx", "--output", "-o", help="Output .twbx path"),
) -> None:
    """Package a .twb file into a .twbx archive."""
    ...

@app.command("publish")
def publish(
    input_path: Path = typer.Argument(..., help="Path to .twb or .twbx file", exists=True),
    server: str = typer.Option(..., "--server", help="Tableau Server URL"),
    project: str = typer.Option(..., "--project", help="Target project name"),
    site: str = typer.Option("", "--site", help="Target site contentUrl"),
    mode: str = typer.Option("CreateNew", "--mode", help="Publish mode: CreateNew or Overwrite"),
) -> None:
    """Publish a workbook to Tableau Server or Cloud."""
    ...
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| tabcmd CLI for publishing | TSC Python library | TSC v0.10+ (2018) | Type-safe, testable, no subprocess |
| Manual chunked upload | TSC auto-chunking at 64MB | TSC v0.14+ (2020) | No custom chunking code needed |
| Sync-only publish | Async publish with as_job=True | TSC v0.23+ (REST API 3.0) | Large workbooks don't block |
| Username/password auth | PAT auth (preferred) | TSC v0.14+ | More secure, no password exposure |

**Deprecated/outdated:**
- tabcmd: PROJECT.md explicitly excludes. Use TSC only.
- Tableau Document API: Labeled "As-Is" and unsupported. Does not support creating files from scratch.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | .twbx internal structure is flat (twb at root level) with optional Data/ and Images/ subdirectories | Architecture Patterns | ZIP structure won't match Tableau Desktop output |
| A2 | REST API fallback (PUB-02) only needs to handle direct multipart/mixed POST calls, not a full REST client | Don't Hand-Roll | Fallback publisher may be underspecified |
| A3 | `server.projects.filter(name=...)` returns at most one result for exact name match | Architecture Patterns | May need additional disambiguation for duplicate project names |
| A4 | Tableau Cloud requires a non-empty site_id value in PAT auth | Common Pitfalls | Default site handling differs between Server and Cloud |

**If this table is empty:** All claims in this research were verified or cited -- no user confirmation needed.

## Open Questions

1. **What assets go into a .twbx beyond the .twb?**
   - What we know: .twbx is a ZIP containing .twb and optionally Data/ (extracts) and Images/ directories. Our generator currently only produces .twb files without embedded extracts.
   - What's unclear: Whether Phase 3 needs to handle embedded extracts at all, or if packaging is just wrapping the .twb in a ZIP.
   - Recommendation: Start with .twb-only packaging. The .twbx with just a .twb is valid and Tableau will generate extracts on the server side. Document this as a known limitation.

2. **What specific edge cases require the REST API fallback (PUB-02)?**
   - What we know: TSC covers standard publish, chunked upload, PAT auth, async jobs. The REST API fallback is for "edge cases TSC does not cover."
   - What's unclear: Which specific edge cases to implement in Phase 3.
   - Recommendation: Implement a minimal fallback that handles: (a) custom HTTP options/proxy settings, (b) publish with connection credentials that TSC doesn't expose, (c) any future REST API features not yet in TSC. Document that the fallback is a thin wrapper around direct REST calls.

3. **Should `publish` command accept both .twb and .twbx files?**
   - What we know: TSC accepts both file extensions (ALLOWED_FILE_EXTENSIONS = ["twb", "twbx"]).
   - What's unclear: Whether to auto-package .twb before publish, or require the user to run `package` first.
   - Recommendation: Accept both. If the input is .twb and the user hasn't specified --no-package, auto-package to .twbx first. This gives the best UX while maintaining composability.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| tableauserverclient | Publishing (PUB-01 through PUB-05) | Available (dev install) | 0.40 | Must be in pyproject.toml for production |
| Python 3.12+ | All | Available | 3.13 | -- |
| lxml | Package verification (PKG-02) | Available | 6.1+ | -- |
| zipfile (stdlib) | Packaging (PKG-01) | Available | stdlib | -- |
| requests | REST fallback (PUB-02) | Available (TSC dep) | bundled | -- |
| pydantic-settings | Credential loading | Available | 2.14+ | -- |
| Tableau Server instance | Integration testing | NOT available locally | -- | Mock all TSC calls; integration test against real server is manual |

**Missing dependencies with no fallback:**
- None for code implementation. All required libraries are available.

**Missing dependencies with fallback:**
- Tableau Server/Cloud instance: Not available in dev environment. All TSC interactions must be mocked in automated tests. Manual integration testing requires a real server.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| PKG-01 | Package .twb into .twbx with correct ZIP structure | unit | `pytest tests/test_packager.py -x` | Wave 0 |
| PKG-02 | Verify .twbx integrity (valid ZIP, parseable inner .twb) | unit | `pytest tests/test_packager.py::test_verify_integrity -x` | Wave 0 |
| PUB-01 | Publish with PAT auth via TSC | unit (mocked) | `pytest tests/test_publisher.py -x` | Wave 0 |
| PUB-02 | REST API fallback publish | unit (mocked) | `pytest tests/test_fallback.py -x` | Wave 0 |
| PUB-03 | CreateNew and Overwrite modes with project/site resolution | unit (mocked) | `pytest tests/test_publisher.py -x` | Wave 0 |
| PUB-04 | Async publish with chunked upload (> 64MB) | unit (mocked) | `pytest tests/test_publisher.py::test_async_publish -x` | Wave 0 |
| PUB-05 | Publish receipt with all required fields | unit | `pytest tests/test_receipt.py -x` | Wave 0 |
| CLI | package and publish commands with --help and typed args | integration | `pytest tests/integration/test_cli.py -x` | Expand existing |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before /gsd-verify-work

### Wave 0 Gaps
- [ ] `tests/test_packager.py` -- covers PKG-01, PKG-02
- [ ] `tests/test_publisher.py` -- covers PUB-01, PUB-03, PUB-04
- [ ] `tests/test_fallback.py` -- covers PUB-02
- [ ] `tests/test_receipt.py` -- covers PUB-05
- [ ] `tests/integration/test_cli.py` -- expand with TestPackageCommand and TestPublishCommand

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | PAT auth via TSC.PersonalAccessTokenAuth; no username/password |
| V3 Session Management | yes | TSC context manager (with statement) for auto sign-out |
| V4 Access Control | yes | Project/site resolution ensures user has publish permissions |
| V5 Input Validation | yes | Pydantic models for PublishSpec; Path validation in CLI |
| V6 Cryptography | yes | HTTPS required for server_url; PAT token never logged or stored |

### Known Threat Patterns for Publishing

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Credential exposure in env vars | Information Disclosure | pydantic-settings; env vars not in YAML or git; Secrets field marking |
| Man-in-the-middle on publish | Tampering, Spoofing | HTTPS required; TSC uses certificate verification by default |
| Unauthorized publish to wrong project | Elevation of Privilege | Project name resolution + server-side permissions; validate project_id before publish |
| Large file upload timeout | Denial of Service | Chunked upload (auto by TSC); configurable timeout on wait_for_job |

## Sources

### Primary (HIGH confidence)
- TSC v0.40 API reference -- https://tableau.github.io/server-client-python/docs/api-ref [Fetched 2026-05-09]
- TSC v0.40 installed package -- method signatures verified via Python inspect module
- PyPI: tableauserverclient v0.40 -- https://pypi.org/project/tableauserverclient/
- Existing codebase: cli.py, models.py, settings.py, generator.py, report.py [Read 2026-05-09]
- pyproject.toml -- dependency list verified [Read 2026-05-09]

### Secondary (MEDIUM confidence)
- TSC workbooks.publish() source code -- inspected via Python inspect.getsource() [Verified 2026-05-09]
- TSC FILESIZE_LIMIT = 64MB, ALLOWED_FILE_EXTENSIONS = ["twb", "twbx"] -- extracted from source [Verified 2026-05-09]
- TSC.PublishMode enum values: Append, CreateNew, Overwrite, Replace -- verified via dir() [Verified 2026-05-09]

### Tertiary (LOW confidence)
- .twbx internal ZIP structure (flat .twb at root) -- [ASSUMED] based on Tableau Desktop behavior observation
- REST API fallback multipart/mixed content type -- [ASSUMED] from Tableau REST API publish endpoint documentation

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - all versions verified against PyPI and installed packages
- Architecture: HIGH - follows existing codebase patterns; TSC API signatures verified via inspect
- Pitfalls: HIGH - derived from TSC API behavior and documented error conditions

**Research date:** 2026-05-09
**Valid until:** 2026-06-09 (30 days - stable domain with locked TSC version)
