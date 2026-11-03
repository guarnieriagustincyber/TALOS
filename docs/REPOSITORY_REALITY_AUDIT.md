# Repository Reality Audit

**Status:** tooling configured; inventory and interpretation are evidence
gathering, not a cleanup authorization
**Scope:** repository structure, Python duplication/complexity/dead-code
candidates/maintainability, and isolated browser checks of UI shell/chat behavior
against mocked API/SSE
**Out of scope:** E5/Qwen experiments, corpus or database mutation, changes to
deployed production, and automatic removal/refactoring. A focused local
frontend guard for incomplete SSE streams is documented in the report; it is
validated against mocks only.

## Tooling

- **Radon** and **Vulture** run from the project `.venv`.
- **Playwright Python** runs from `.venv`; Chromium is installed separately by
  `python -m playwright install chromium`.
- **jscpd** is a Node development dependency of `kasiu-lab/ui`; it scans tracked
  implementation/test source areas and reports duplication without failing
  builds based on a duplication percentage.

Python audit dependencies have a separate input and generated hashed lock:
`requirements-audit.in` and `requirements-audit.lock`. They are deliberately
separate from `requirements.lock`, which is associated with the E5 Python 3.10
candidate and must not be silently changed by repository-audit tooling.

Install the Python tools into the existing project environment without
replacing its other packages:

```bash
.venv/bin/uv pip install --python .venv/bin/python --require-hashes \
  -r requirements-audit.lock
.venv/bin/python -m playwright install chromium
```

Install the frontend tool from `kasiu-lab/ui` with `npm ci` after the committed
manifest and lockfile are present.

## Commands

From the repository root:

```bash
.venv/bin/radon cc src/study_engine scripts -s -a --total-average
.venv/bin/radon raw src/study_engine scripts --summary
.venv/bin/radon mi src/study_engine scripts -s
.venv/bin/vulture --config .vulture.toml
.venv/bin/pytest -q kasiu-lab/ui/e2e/test_ui_smoke.py
```

From `kasiu-lab/ui`:

```bash
npm run audit:duplicates
```

The Playwright tests launch only the Vite UI server on localhost. Success,
error, truncation, explicit abort, and incomplete-EOF responses are mocked in
the browser; the tests do not start the TALOS backend or access production
data. They verify frontend behavior and terminal-state handling against a mock
contract, not compatibility with the real backend/SSE implementation. Install
the browser binary once with:

```bash
.venv/bin/python -m playwright install chromium
```

## Interpretation rules

Metrics and findings are candidates for review, not automatic quality gates:

- duplication can be intentional in fixtures, tests, adapters, or independent
  contracts;
- complexity identifies review targets, not proof that a component is
  defective;
- Vulture findings require checking dynamic imports, registration, callbacks,
  framework discovery, tests, and runtime reachability;
- the browser checks prove UI shell and selected chat/terminal-state behaviors
  against a mocked API/SSE contract; they do not prove real backend integration,
  actual SSE compatibility, or behavior against production services.

Classify findings as `CANONICAL_ACTIVE`, `ACTIVE_SUPPORT`, `TEST_ONLY`,
`LEGACY`, `ORPHAN`, `DUPLICATE`, `DEAD_CANDIDATE`, or `UNKNOWN`, then record an
explicit `KEEP`, `CONSOLIDATE`, `DEPRECATE`, `REMOVE`, or `INVESTIGATE`
decision. No tool in this audit deletes or rewrites application code.

## Initial tooling check

Checked on 2026-09-30 with Python 3.12.3, Radon 6.0.1, Vulture 2.16,
Playwright 1.63.0 / Chromium 153.0.8010.12, Node 20.20.2, and jscpd 4.2.0.
The browser smoke test passed. The first scans reported duplicated TSX blocks,
17 Vulture dead-code candidates, and a highest observed Radon cyclomatic
complexity of `D (24)` for `sync_vectors`; these are unadjudicated findings, not
approved changes. The isolated Playwright suite now covers **5 chat outcomes**:
success with notebook selection and citation, error, truncation, explicit
stream abort, and incomplete EOF without `phase_complete`; all verify UI
terminal/loading state. `npm audit --omit=dev`
reported no production dependency
advisories; the full development dependency tree reports two advisories and is
not treated as a release gate here.
