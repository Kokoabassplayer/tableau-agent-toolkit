# Milestones

## v1.0 MVP (Shipped: 2026-05-09)

**Phases completed:** 7 phases, 21 plans, 32 tasks
**Timeline:** 2 days (2026-05-08 to 2026-05-09)
**Code:** 2,518 LOC src + 3,502 LOC tests (Python) | 167 files | 293+ tests passing

**Key accomplishments:**

- Complete E2E pipeline: spec init → generate → validate-xsd → validate-semantic → qa static → package → publish
- Dual agent support: Claude Code + Codex plugin manifests with 5 composable skills
- Three-tier validation: XSD structural, semantic cross-reference with line-number mapping, static QA with remediation
- Enterprise publishing: TSC PAT auth, async chunked upload, REST fallback, spec-driven defaults
- Deterministic TWB generation: template-first lxml XML patching produces byte-identical output
- Enterprise CI/CD: GitHub Actions matrix (Python 3.12/3.13, ubuntu/windows), pre-commit hooks, ruff/mypy

**Known gaps (procedural):**
- PKG-01, PUB-03, PUB-04, PUB-05 lack formal VERIFICATION.md (Phase 03 executed before verify-work was added; code verified by Phase 07 integration tests)
- 6/7 phases Nyquist non-compliant (VALIDATION.md in draft status)
- CLI uses positional TWB_PATH instead of --input flag (documentation mismatch)

**Archived:**
- [v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- [v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)
- [v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md)

---
