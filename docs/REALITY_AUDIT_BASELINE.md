# TALOS Repository Reality Audit — Baseline

**Captured:** 2026-09-30
**Branch / HEAD at audit start:** `main` / `2ba7811` (`docs: decide E5 runtime resolution path`)
**Initial working tree:** clean
**Current working tree:** contains audit tooling and a subsequently authorized, focused frontend SSE terminal-state fix
**Purpose:** establish repository/environment facts before structural analysis; this is not a cleanup or release approval

## Perimeter and restrictions

At baseline, this audit was read-only with respect to TALOS behavior and data. It did not
authorize refactoring, deletion, renames, API/schema changes, database or
corpus writes, index/embedding generation, migrations, production access, or
E5/Qwen execution. Tool output is evidence or a candidate; it is not proof that
a component is dead, legacy, safe to remove, or production-active.

The user separately authorized installation/configuration of the repository
audit tools before sharing the expanded audit protocol. Accordingly, the
Python audit packages and Playwright Chromium were installed in the existing
`.venv`/user browser cache, and jscpd was added to the UI development
dependencies. No further dependency or environment changes are authorized by
this audit. The E5 `requirements.lock` was not changed.

## Environment observed

| Item | Observation | Evidence status |
|---|---|---|
| OS / architecture | Linux, x86_64 | Observed |
| Python environment | `.venv`, CPython 3.12.3 | Observed |
| pip / uv | pip 26.2.1 / uv 0.12.10 | Observed |
| pytest | 9.1.1, as recorded in the prior repository baseline | Historical observation; not independently re-probed at audit start |
| Radon | 6.0.1 | Observed in `.venv`; it was already present when the audit requirements were installed |
| Vulture | 2.16 | Installed into `.venv` during this task |
| Playwright Python | 1.63.0 | Installed into `.venv` during this task |
| Playwright Chromium | Chrome for Testing 153.0.8010.12 | Installed in the user browser cache; browser smoke test passed |
| Node / npm | Node 20.20.2 / npm 10.8.2 | Observed |
| jscpd | 4.2.0 | Installed in `kasiu-lab/ui` during this task |

## Tool availability at first inspection

| Tool | Initial result | Current state |
|---|---|---|
| jscpd | Not on `PATH`; absent from the inspected UI manifest before setup. Local transitive availability was not queried before installation. | Configured as the UI project's direct dev dependency |
| Radon | Not on `PATH`; `.venv/bin/radon` was subsequently confirmed at 6.0.1 and was not added by the audit install | Available in `.venv` |
| Vulture | Not on `PATH` | Available in `.venv` |
| Playwright | Not on `PATH` | Available in `.venv`, Chromium installed |

`AVAILABLE` means verified installed; `MISSING` means not found in the checked
manifest or executable path; `UNKNOWN` preserves checks that were not performed
before installation. Absence from `PATH` alone is not treated as proof that a
tool was absent from a local project environment.

## Repository snapshot

At initial inspection the tracked tree was clean at `2ba7811`. Since then,
changes in the working tree include:

- Python audit dependency input and lock, plus Radon/Vulture configuration;
- jscpd UI development dependency, npm lock entry, and audit/start scripts;
- a Playwright UI-shell and mocked chat/terminal-state test outside the declared
  `tests/` perimeter;
- a focused frontend SSE completion guard in `chatService.ts`;
- this baseline, the audit-tooling guide, report, and backlog.

The separate E5 `requirements.lock` remains unchanged. A later, focused
frontend change makes the UI reject explicit truncation/abort events and EOF
without `phase_complete`; it was tested with mocked SSE only. No deployed
production environment was changed, no production backend was started, and no
model, corpus query, retrieval benchmark, blind-pool generation, or database
mutation was run.

Tracked inventory at the start: 338 Python source modules under
`src/study_engine`, 473 Python test files, 57 UI source files, 96 Python
scripts, and 50 documentation files. These are counts of tracked paths, not
counts of importable modules, tests collected, runtime routes, or active
components.

## Initial uncertainty register

- A module existing in source does not establish that it is imported,
  instantiated, runtime-reachable, user-visible, or production-observed.
- Test-file counts do not establish collection or behavioral coverage.
- Database/corpus filenames and sizes are inventory metadata only; no records,
  source content, or user data were read by this baseline.
- Radon/Vulture/jscpd findings require reference, route, entrypoint, test, and
  dynamic-loading checks before classification.
- At baseline, the browser smoke test covered only the UI shell. Subsequent
  isolated Playwright tests now verify mocked chat success/error, selected
  notebook ID submission, and synthetic citation rendering. Real backend/SSE
  compatibility and cross-notebook isolation remain unverified.

The initial code-audit observations are recorded separately in
[`REPOSITORY_REALITY_AUDIT.md`](./REPOSITORY_REALITY_AUDIT.md); full
cross-correlation and classification remain pending.
