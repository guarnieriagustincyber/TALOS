# TALOS Repository Reality Audit — Report

**Snapshot:** 2026-09-30
**Repository HEAD at audit start:** `main@2ba7811`
**Status:** evidence collected; classifications and remediation proposals remain
non-destructive
**Baseline:** [`REALITY_AUDIT_BASELINE.md`](./REALITY_AUDIT_BASELINE.md)
**Tool setup:** [`REPOSITORY_REALITY_AUDIT.md`](./REPOSITORY_REALITY_AUDIT.md)
**Backend B0:** [`BACKEND_OPERATIONAL_ARCHAEOLOGY.md`](./BACKEND_OPERATIONAL_ARCHAEOLOGY.md)
**Integrated current plan:** [`PLAN_MAESTRO_CIERRE_TALOS.md`](./PLAN_MAESTRO_CIERRE_TALOS.md)

## Executive summary

This audit confirms a substantial source, test, data, and UI footprint, but
does **not** equate file presence or static references with production use.
The backend has a statically traceable FastAPI chat path and the React entry
tree mounts `ChatWorkspace`; neither was started as a backend during this
audit. Isolated Playwright tests verify the Vite UI shell and chat behavior
against a mocked API/SSE contract; the real backend was not started.

The measurements produced review candidates, not cleanup instructions. A
subsequent focused test-driven change in `chatService.ts` now rejects explicit
`truncated`/`stream_aborted` events and SSE EOF without a completed phase;
isolated browser mocks cover those outcomes. This is not evidence of backend
compatibility.

A follow-up static B0 trace found that normal `AppContainer(use_mock=True)` and
the existing copied-database fixtures do not satisfy a no-project-data-read
boundary. It also found backend abstention/clarification events that are not
recognized by the React event allowlist and end without `phase_complete`;
therefore the current client will classify those backend responses as
incomplete. This is a static contract discrepancy, not a runtime observation.
A subsequent guarded B0.5 subprocess confirmed the import/factory directory
attempts, blocked the `.env` read under the repository CWD before content was
read, and ran the startup handler only with a synthetic container while
suppressing its warmup thread.

B1-A then exercised the actual `/api/chat/query` HTTP route using in-process
ASGI and synthetic domain dependencies under the same data/network/process
guards. Schema validation, empty-prompt rejection, normal SSE framing, and
route conversion of a synthetic pipeline exception to an SSE `error` all
passed. No normal lifespan, real container, retrieval, provider, persistence,
or listening server was used.

- jscpd found **337 clone blocks** across 889 analyzed files, amounting to
  **4,925 duplicated lines (3.03%)** under the configured thresholds. No clone
  cluster has yet been adjudicated as accidental or safe to consolidate.
- Radon analyzed **2,737 complexity blocks**, average **B (5.82)**. The
  configured JSON result includes 780 non-A blocks: B 377, C 252, D 85, E 31,
  F 35. High scores include both runtime-path code and experiment/audit
  scripts.
- Vulture reported **17 unused/unreachable candidates**. They remain
  `DEAD_CANDIDATE`/`UNKNOWN`; no code was removed.
- At the original audit snapshot, pytest collection found **2,947 tests**
  (1,254 under `tests/unit`). Collection is not execution or proof of coverage.
  The then-declared perimeter validated 24 suites and 451 test modules; the
  certification-document count discrepancy was subsequently reconciled in
  the A-PRE-0 update below.
- The isolated React browser suite covers mocked success, error, truncation,
  explicit stream abort, and incomplete EOF. It does not establish compatibility
  with real chat requests or backend SSE behavior.

No deployed production environment, model, corpus, index, embedding, E5/Qwen
artifact, or experiment was changed or executed. One frontend source module was
changed to fail closed on incomplete SSE streams; it was verified only against
mocked browser responses, not a deployed service. The database/corpus inventory
read only path and size metadata; pytest collection imported test modules but
ran no test bodies. No before/after content hash exists for ignored databases,
so bitwise identity of every such file is not claimed. No repository cleanup
decision was applied.

## P0 — Snapshot, perimeter, and tooling

The starting checkout was clean at `2ba7811`. The audit setup changes are
listed in the baseline. The separate E5 `requirements.lock` remains untouched.

| Tool | Initial evidence | Current status | Classification |
|---|---|---|---|
| Radon | Not on `PATH`; confirmed in `.venv` at 6.0.1 and not newly installed by the audit lock sync | Installed and configured | `AVAILABLE` |
| Vulture | Not on `PATH`; added to `.venv` during the separately authorized setup | Installed and configured | `AVAILABLE` |
| Playwright | Not on `PATH`; added to `.venv` during the separately authorized setup | Python 1.63.0 and Chromium 153.0.8010.12; shell smoke test passed | `AVAILABLE` |
| jscpd | Not on `PATH` or in the inspected UI manifest; nested `node_modules` was not checked before setup | UI dev dependency 4.2.0, command and config verified | Initially `UNKNOWN`; now `AVAILABLE` |
| Browser/package compatibility | Current Node is 20.20.2; current dependency graph contains `commander@15` through KaTeX, which declares Node >=22.12 | jscpd 4.2 uses commander 5.1; npm still reports the separate KaTeX engine warning | `CONFLICTING` dependency warning; UI typecheck and jscpd pass |
| npm advisories | Not measured before dependency setup | Two development-tree advisories: esbuild (moderate), Vite (high); `npm audit --omit=dev` reports none | `OBSERVED`, remediation not part of this audit |

Python audit dependencies are isolated in `requirements-audit.in` /
`requirements-audit.lock`; jscpd is in the UI's own package manifest/lock.
The E5 lock was not changed or regenerated.

## P1 — Physical inventory

Counts below are filesystem/AST inventories, not counts of active components.

| Area | Observed |
|---|---:|
| Python modules in `src/study_engine` | 338 |
| Python scripts in `scripts/` | 96 |
| Python files under `tests/` | 473 |
| Named pytest module files (`test_*.py`) | 451 |
| React/TypeScript source files under UI source | 55 TS/TSX/JS/JSX files; broader UI source glob previously counted 57 files including non-code assets |
| Documentation files | 50 |
| AST class declarations across tracked source/tests/scripts | 959 |
| AST function/async-function declarations, including methods/nested functions | 5,202 |

The default pytest collection result was 2,947 tests. The test perimeter manifest
contains 24 suite classifications and validates 451 test modules, with two
optional modules. Unit tests account for 1,254 collected tests. The remaining
tracked test files are distributed across adversarial, contract, integration,
pedagogy, benchmark, security, retrieval, web, and other suites; see
[`config/test_perimeter.json`](../config/test_perimeter.json) for the declared
profile classifications.

The 96 Python scripts fall into visible naming/path groups: benchmark and
experiment runners (`benchmark_*`, `scripts/experiments/`), gate/audit
utilities (`audit_*`, `quality_gate.py`, `validate_*`, `check_*`), corpus and
index operations (`ingest_*`, `build_*`, `reindex_*`, `sync_*`), and launch or
desktop helpers. This is a static naming inventory only. The declared CLI
entrypoint is `talos = study_engine.cli:main`; `scripts/test.sh` is documented
as the release gate. No script was run to infer its historical or current use.

Metadata-only inventory under `data/`, `benchmark/`, `artifacts/`, `reports/`,
and `kasiu-lab/storage/` found:

| File category by extension | Files | Total bytes |
|---|---:|---:|
| SQLite/database (`.db`, `.sqlite`, `.sqlite3`) | 24 | 2,090,635,264 |
| Corpus-like (`.pdf`, `.txt`, `.md`, `.html`) | 216 | 875,738,962 |
| Standalone model/index/array (`.onnx`, `.npy`, `.npz`, `.faiss`, `.index`) | 0 | 0 |
| JSON/JSONL manifests/data | 262 | 4,988,508 |

Only path, extension, and byte-size metadata were read for this inventory.
Embeddings or indexes may be stored inside database files; their contents were
not inspected.

## P2 — Static import archaeology

An AST-only pass examined 907 tracked Python files across source, tests, and
scripts; it had zero parse failures. It found:

| Reference class | Modules |
|---|---:|
| Imported by at least one `src/study_engine` module | 310 |
| Referenced only by tests in the scanned static graph | 24 |
| Referenced only by scripts | 1 |
| No static importer found in scanned source/tests/scripts | 3 |

The three no-static-importer candidates are `study_engine.pedagogy.socratic_prompts`,
`study_engine.quality`, and `study_engine.tester`. Two recognized dynamic-import
call sites were found. These counts do not resolve string-based loading,
package entry points, framework discovery, reflection, or imports introduced
outside the scanned roots. Therefore the three candidates and all test-only
references remain `UNKNOWN`, not `ORPHAN` or `DEAD_CANDIDATE`.

## P3 — jscpd duplication evidence

Configuration scans Python, TypeScript/TSX, JavaScript, and test sources with
minimum 50 tokens / 5 lines and a 100% threshold so findings are reported
without turning duplication into a pass/fail gate.

| Format | Files | Clones | Duplicated lines | Duplicated lines % |
|---|---:|---:|---:|---:|
| Python | 785 | 319 | 4,713 | 3.35% |
| TSX | 38 | 17 | 193 | 1.79% |
| TypeScript | 10 | 0 | 0 | 0% |
| JavaScript | 44 | 0 | 0 | 0% |
| JSON | 9 | 1 | 19 | 1.61% |
| CSS / markup | 3 | 0 | 0 | 0% |
| **Total** | **889** | **337** | **4,925** | **3.03%** |

The scan reports self-file repeats and cross-file similarity in TSX (for
example, repeated blocks within `CognitiveProfileDrawer.tsx` and related
rendering/view components). Python clones include source, tests, and scripts;
the aggregate alone cannot distinguish fixtures, contracts, structural
similarity, or copy/paste. All 337 clusters remain `UNKNOWN` pending pairwise
review; nothing was consolidated.

## P4 — Radon complexity and maintainability

Commands: `radon cc src/study_engine scripts -s -a --total-average`,
`radon raw ... --summary`, and `radon mi ... -s`. The configured threshold is
`cc_min = B`; it is a review filter, not a quality gate.

- Complexity: **2,737** analyzed blocks; average **B (5.82)**.
- Configured non-A candidates: **780** blocks — B 377, C 252, D 85, E 31,
  F 35.
- Maintainability index: **434** Python files — A 420, B 9, C 5.
- Raw metrics across 434 files: LOC 104,961; LLOC 47,560; SLOC 83,135;
  comments 3,347; multiline comments 3,992; blank lines 13,046.

Highest complexity observations:

| Component | CC | Initial classification |
|---|---:|---|
| `run_campaign` in `scripts/experiments/run_phase7_state_attacks.py` | 124 | `HIGH_COMPLEXITY` script candidate |
| `_assemble_epistemic_context` in `src/study_engine/web/routes/chat.py` | 110 | `HIGH_COMPLEXITY`; statically reachable in chat path |
| `run_campaign` in `scripts/experiments/run_phase8_timeout_boundary.py` | 103 | `HIGH_COMPLEXITY` script candidate |
| `assess_promotion` in `src/study_engine/diagnostics/vector_space_contract.py` | 97 | `HIGH_COMPLEXITY` diagnostic candidate |
| `generate_phased_response` in `src/study_engine/pedagogy/structured_pipeline.py` | 93 | `HIGH_COMPLEXITY`; statically reachable from chat path |
| `_prepare_chat_context` in `src/study_engine/web/routes/chat.py` | 77 | `HIGH_COMPLEXITY`; statically reachable in chat path |

The exact score does not determine whether complexity is justified, tested, or
safe to change. Radon also emitted a Python `SyntaxWarning` for an invalid
escape sequence in `scripts/benchmark_phase_e3.py`; this audit did not modify
it.

## P5 — Vulture dead-code candidates

Configured scan: `.venv/bin/vulture --config .vulture.toml`. It reported 17
findings and returned a nonzero finding status. None is treated as proof of
dead code.

| Candidate | Vulture observation |
|---|---|
| `scripts/experiments/run_phase8_timeout_boundary.py:563` | `thread_to`, unused variable |
| `scripts/survival/test_concurrency_scope.py:11` | `multiprocessing`, unused import |
| `src/study_engine/federation/curriculum_gate.py:46` | `fts_alias`, unused variable |
| `src/study_engine/federation/namespace.py:93` | `evidence_trust`, unused variable |
| `src/study_engine/memory/conversation_state.py:81` | `target_token_range`, unused variable |
| `src/study_engine/metrics/eeu.py:75` | `min_citations_threshold`, unused variable |
| `src/study_engine/pedagogy/dialogue_policy.py:55` | `has_qualifiable_exercises`, unused variable |
| `src/study_engine/pedagogy/state_predictor.py:26` | `var_names`, unused variable |
| `src/study_engine/pedagogy/x86_interpreter.py:117,128` | `default_size`, unused variable |
| `src/study_engine/retrieval/late_chunking.py:67,163` | `return_tensors`, unused variable |
| `src/study_engine/retrieval/symbol_guard.py:330` | code after `return`, unreachable-looking |
| `src/study_engine/retrieval/symbol_guard.py:343` | `assertion_type`, unused variable |
| `src/study_engine/session/orchestrator.py:282` | code after `return`, unreachable-looking |
| `src/study_engine/session/study_loop.py:748` | `student_query`, unused variable |
| `src/study_engine/tutor/local_orchestrator.py:12` | `html`, unused import |

Dynamic references, framework registration, and call-site behavior remain to
be checked before any candidate can be classified beyond `DEAD_CANDIDATE`.

## P6 — Backend runtime map

Static evidence only; the application was not imported or started.

- `create_app()` is the authoritative factory in
  [`src/study_engine/web/app.py`](../src/study_engine/web/app.py#L66); module
  import also constructs the ASGI app.
- The factory registers 20 router groups, CORS middleware, one startup hook,
  and static/storage mounts. Static decorators show 67 router endpoint
  handlers, plus four direct app handlers (`/`, retired session route, and two
  system routes). This is a source-derived count, not a runtime route-table
  introspection.
- The registered router groups are health, curriculum, student, chat, LLM
  pool, sources, practice, evidence, ingestion, federation, threat intel,
  telemetry, pedagogy, dialogue, study session, notebook, notebook admin,
  student exercises, retrieval, and evaluation.
- Startup initializes `get_container()` and schedules daemon-thread retrieval
  warmup; neither startup nor warmup was run.
- Static chat request flow:
  `POST /api/chat/query` → input/PII guard → `_prepare_chat_context` →
  scope/fast-path decisions → `_assemble_epistemic_context` → `search_hybrid`
  (fallback `search`) → evidence filtering → provider resolution →
  `StructuredResponsePipeline.generate_phased_response` and SSE.
- The handler is in
  [`src/study_engine/web/routes/chat.py`](../src/study_engine/web/routes/chat.py#L2025);
  container wiring is in
  [`src/study_engine/web/dependencies.py`](../src/study_engine/web/dependencies.py#L145).
- Static source establishes the intended call path and registration, not the
  selected backend, actual branch, successful database/retrieval access, or
  production traffic. No provider health or production reachability was
  observed.

## P7 — Frontend reality map

- [`kasiu-lab/ui/index.html`](../kasiu-lab/ui/index.html#L16) mounts `#root`
  and loads `src/main.tsx`; `main.tsx` renders `App`.
- [`kasiu-lab/ui/src/App.tsx`](../kasiu-lab/ui/src/App.tsx#L15) directly mounts
  `ChatWorkspace`; this entry path has no React Router. Workspace `currentView`
  conditionally selects chat and imported panels.
- `ChatWorkspace` manages chat state and hands requests to
  [`chatService.ts`](../kasiu-lab/ui/src/services/chatService.ts#L197), which
  POSTs `/api/chat/query` and parses SSE events including tokens, evidence,
  completion, and errors. `vite.config.ts` proxies `/api` and `/storage` to
  localhost port 8000.
- UI evidence rendering and error/loading branches are present in
  [`ChatMessages.tsx`](../kasiu-lab/ui/src/presentation/features/chat/components/ChatMessages.tsx#L574).
- Existing backend SSE tests use `TestClient`; an existing static contract test
  checks the legacy JavaScript UI, not the React SSE service. No pre-existing
  browser test for React user journeys was found in the inspected tree.
- Source imports/conditionals and one shell-mount test do not establish which
  panels users select or whether API/SSE/citation flows work end-to-end.

## P8 — Playwright evidence

`kasiu-lab/ui/e2e/test_ui_smoke.py` starts only Vite on `127.0.0.1:4173`,
blocks external HTTPS requests, and does not start the backend or access
databases. The five parameterized scenarios cover success, error, `truncated`,
`stream_aborted`, and EOF without `phase_complete`; each verifies React mounts
and the request finishes with loading indicators cleared. The success case
selects Sistemas Operativos II, verifies `notebook_id` is `fadena-so2`, renders
a synthetic citation, and opens its evidence popover. Truncation, abort, and
incomplete EOF must surface as errors rather than successful partial answers.
No uncaught `pageerror` was observed. These tests are browser
`RUNTIME_VERIFIED` for frontend behavior against a mock contract, not for
connectivity or protocol compatibility with the real backend; real API/SSE
integration remains `UNKNOWN`.

## P9 — Test reality at the original audit snapshot

- `pytest --collect-only -q`: 2,947 cases collected; 1,254 in `tests/unit`.
- Test-perimeter validator at the original audit snapshot: 24 suites, 451
  modules, two optional modules; validation passed without running test bodies.
- `tests/web` and `tests/pedagogy` have backend/API/SSE tests. They are not
  browser E2E evidence.
- No broad test suite was run. The only test bodies executed were the five
  isolated Playwright scenarios described in P8.
- Collection emitted a `StarletteDeprecationWarning` concerning
  `starlette.testclient`/`httpx`; it was not changed.
- The new E2E smoke lives outside `tests/`, so the existing test perimeter
  remains unchanged.

## P10 — Documentation versus implementation at the original audit snapshot

| Statement/resource | Evidence comparison | Classification |
|---|---|---|
| README lists Python package and test-suite structure | Tracked paths and top-level test directories correspond to the documented structure; its tree explicitly says it omits files | `PARTIALLY_VERIFIED` |
| `TEST_CERTIFICATION_PERIMETER.md` said 446 current test modules | Original filesystem and perimeter validator found 451 `test_*.py` modules | `CONTRADICTORY` at the audit snapshot; reconciled in the A-PRE-0 update below |
| `config/test_perimeter.json` and `scripts/quality_gate.py` are normative test-perimeter sources | Original validator succeeded for 24 suites and 451 modules; it separated required, qualification, optional, and support-only | `VERIFIED` as configuration/validation behavior at that snapshot; test execution not performed |
| README says `pyproject.toml` is the single dependency source | The new audit-only tools use separate `requirements-audit.in`/lock files to preserve the E5 lock and avoid changing runtime extras | `PARTIALLY_VERIFIED`; this scoped tooling exception should be reconciled in future documentation |
| Historical audit reports | `docs/audit_diagnostico.md` explicitly warns its evidence is historical; `docs/audit_comparativo_v1.md` is dated 2026-09-23 | `LEGACY_DOCUMENTATION` for current-state claims unless revalidated |
| Existing `tests/unit/web/test_chat_ui_sse_contract.py` | Checks legacy static JavaScript, while current React entrypoint is `kasiu-lab/ui/src/main.tsx` | `PARTIALLY_VERIFIED`; not React E2E evidence |
| Existing `scripts/audit_codebase.py` | Contains shell-based audit commands and labels the run completed without checking each command's return status | `IMPLEMENTED`, but reliability and current applicability `UNKNOWN` |

No existing documentation was rewritten to hide discrepancies.

## P11 — Cross-analysis and classification

| Finding | Combined evidence | Classification | Confidence |
|---|---|---|---|
| Chat context assembly is complex and on the statically reachable chat path | Radon CC 110 plus source call path from `/api/chat/query` | `CANONICAL_ACTIVE` at source-registration level; production observation unknown | HIGH for static path; LOW for production use |
| Streaming generation is complex and on ordinary chat path | Radon CC 93 plus static pipeline construction/stream call | `ACTIVE_SUPPORT` at source-path level | HIGH for static path |
| Several experiment campaign functions score E/F | Radon paths are under `scripts/experiments`; they are scripts, not automatically app runtime | `UNKNOWN` until entrypoint/use classification | HIGH for location/score |
| 337 jscpd clones | Clone data spans Python source/tests/scripts and TSX; fixtures and structural similarities are plausible but unadjudicated | `DUPLICATE` evidence label only; cause `UNKNOWN` | HIGH for reported similarity; LOW for architectural meaning |
| 17 Vulture results | Static tool findings with no runtime/dynamic resolution review | `DEAD_CANDIDATE` | HIGH that the tool reported them; LOW that they are dead |
| Three modules without static importers | AST graph finds no static import edge in scanned roots | `UNKNOWN` | MEDIUM |
| UI startup | Playwright root mount and source tree | `CANONICAL_ACTIVE` for entry/root mount | HIGH for local shell; no inference about backend paths |
| Database/corpus presence | File metadata only | `OBSERVED`; data role/active use `UNKNOWN` | HIGH for path/size; none for contents/use |

No component is classified `LEGACY`, `ORPHAN`, or `REMOVE` by this audit.

## P12 — Reality scorecard

| Dimension | Result | Evidence tier |
|---|---|---|
| Repository inventory | Counts and metadata recorded; database contents not inspected | `OBSERVED` |
| Static imports | 907 Python files parsed, zero AST parse failures, approximate edges computed | `STATICALLY_VERIFIED` |
| FastAPI registration/chat path | Source trace plus guarded B1-A/B ASGI requests with synthetic domain dependencies | `STATICALLY_VERIFIED` + `RUNTIME_VERIFIED` for route slice only |
| Python complexity/dead-code candidates | Radon/Vulture reports captured; findings not adjudicated | `CANDIDATE` |
| Duplication | 337 clone blocks reported; clusters not manually classified | `CANDIDATE` |
| Test perimeter | 24 suites / 451 modules validated; 2,947 tests collected | `TEST_VERIFIED` for collection only |
| Browser | Mocked success/error/truncation/abort/incomplete-EOF scenarios | `RUNTIME_VERIFIED` for UI behavior against mock API/SSE |
| Real backend/SSE compatibility and cross-notebook isolation | B1-A/B exercised the route with synthetic dependencies; real domain, provider, browser integration, and cross-notebook isolation remain untested | `PARTIALLY_VERIFIED` only at the route boundary |
| Backend HTTP route validation/SSE framing with synthetic dependencies | B1-A validation/normal/error and B1-B terminal sequences passed under guards; not a domain integration test | `RUNTIME_VERIFIED` for tested route serialization only |
| B1-R synthetic repeatability/sterility | Ten cases × three runs through real route with synthetic domain; independent verifier, negative guard probes, verifier mutations; UI consumer is source-traced, not runtime-tested | `TECHNICAL PASS` for normalized synthetic route observations only; not F6 or product integration |
| Documentation alignment | One stale test-module count and historical reports identified | `PARTIALLY_VERIFIED` |
| Production / E5 / Qwen / blind pool | Not accessed or changed | `NOT_RUN / UNCHANGED` |

## P13 — Backend operational archaeology (B0)

The static trace found explicit CLI/server entrypoints and a registered
`POST /api/chat/query` call path, but it did not import or execute the app.
Importing the web package runs module-level app construction, which attempts
idempotent directory creation for static/storage paths and, under repository
CWD, settings initialization attempts to read `.env`. Normal startup eagerly
builds the container and schedules a retrieval warmup thread.

The default container writes under `data/web_state`; its pipeline runner reads
the experiment oracle and may ingest PDFs from `data/benchmark/sources` when
the knowledge store is empty. `use_mock=True` changes provider/student-storage
choices but does not bypass the KnowledgeStore/VectorStore initialization,
curriculum seeding, or all on-disk state. Existing test fixtures copy the
repository's web-state databases before constructing mock containers.

**B1-A is now complete under a synthetic boundary; the normal
factory/lifespan/container path remains unsafe as an isolated harness.** B1-A
explicitly bypassed normal startup/container construction and replaced direct
context preparation and persistence/background hooks. This verifies only
route/SSE serialization. Real scope, retrieval, pipeline, and persistence
require subsequent isolated fixtures. See the
[`B0 operational map`](./BACKEND_OPERATIONAL_ARCHAEOLOGY.md) for effects,
replaceability, and the proposed safe boundary.

## P14 — Guarded lifecycle probe (B0.5)

A short-lived child process imported `study_engine.web`, explicitly called
`create_app()`, and invoked its sole startup handler under instrumentation. The
probe used a temporary working directory, removed API-key/token-like
environment variable names from the child, denied opens of `.env`, project
`data/`, stores/corpus/model file types, SQLite connections, sockets, and
subprocess/system calls, and suppressed all thread starts.

- Import and explicit factory construction each attempted `mkdir` for
  `src/study_engine/web/static` and `kasiu-lab/storage`; both already existed,
  so the calls were no-ops. No other targeted filesystem write was observed.
- The first import attempt with repository CWD tried to open `.env`; the guard
  blocked it before any file content was read. The successful probe used a
  temporary CWD, so project `.env` was not loaded.
- The sanitized startup handler called the synthetic `get_container` exactly
  once and attempted to start `retrieval-warmup`; the thread start was
  suppressed, so its body and any vector-store access did not run.
- No guarded SQLite/data/corpus/model access, network, or process action was
  observed. No HTTP request was made and the real container was never
  constructed.

This proves the app import, factory and startup handler can be reached under
explicit guards with a synthetic container; it does **not** establish that
normal startup is sterile or that the chat endpoint is safe to call without
additional route/domain stubs. B1-A carried forward the temporary-CWD,
environment scrub, existing-directory precondition, and
startup/thread/container guards without changing the app factory.

## P15 — Synthetic route contract (B1-A)

A separate guarded child process constructed the app and exercised the actual
`POST /api/chat/query` route with HTTPX `ASGITransport`; a fail-fast startup
handler ensured app lifespan was not invoked. The synthetic async dependency
returned a fake container. Direct context preparation, provider resolution,
pipeline generation, citation validation, persistence, and memory extraction
were replaced; the route itself performed request validation and serialized
the SSE response.

Results:

- invalid request schema: HTTP 422 before context preparation;
- whitespace-only prompt: HTTP 422 before context preparation;
- normal fake pipeline: HTTP 200 `text/event-stream` with
  `phase_start → phase_token → evidence_manifest → phase_complete`;
- fake pipeline exception: HTTP 200 `text/event-stream` with terminal `error`.

File/SQLite/network/process/thread/write guards reported no violation. App
imports attempted idempotent `mkdir` calls only for directories already
present (`static`, `storage`, `storage/sources`, `storage/covers`). To avoid
creating an executor thread, the route's `asyncio.to_thread` call was replaced
with an inline wrapper that asserted its only target was the synthetic context
helper. Thus the probe does not test concurrency or threadpool behavior.

This is `RUNTIME_VERIFIED` for the narrow HTTP route/request-validation/SSE
serialization boundary only. It is not evidence for real context resolution,
retrieval, provider, pipeline, persistence, end-to-end backend operation, or
React compatibility. The probe was one-shot, not yet a committed repeatable
test. B1-B terminal observations are recorded in P16.

## P16 — Synthetic terminal SSE contract (B1-B)

A second guarded ASGI probe sent four synthetic terminal paths through the
actual `POST /api/chat/query` route. It reused B1-A's temporary CWD,
credential scrub, fail-fast startup, fake container/context, inline context
helper, and denials for project-data/file access, SQLite, network, processes,
threads, and project writes. No guard violation occurred; the real lifecycle,
domain, provider, and pipeline were not invoked.

| Case | HTTP status | Ordered SSE events | Last event / phase completion |
|---|---:|---|---|
| Abstention | 200 | `evidence_manifest → abstention` | `abstention`; EOF; no `phase_complete` |
| Clarification | 200 | `evidence_manifest → clarification` | `clarification`; EOF; no `phase_complete` |
| Truncated | 200 | `phase_start → truncated → audit_verdict → evidence_manifest → phase_complete` | `phase_complete`; EOF |
| Stream aborted | 200 | `phase_start → stream_aborted` | `stream_aborted`; route closes after cancellation; no `phase_complete` |

Abstention and clarification took the route's early context-pack branch and
did not call the fake pipeline. The truncation case supplied the source-traced
post-truncation events through a fake pipeline. The abort case supplied
`stream_aborted`, then raised `CancelledError`; the route caught the
cancellation and returned after the event. Thus the runtime evidence is
route-level serialization, not runtime execution of `StructuredResponsePipeline`
or a real client disconnect.

The source path establishes that `truncated` is an intermediate warning in
the actual pipeline: audit, `evidence_manifest`, and `phase_complete` follow.
The actual cancellation handler yields `stream_aborted` and re-raises
`CancelledError`. Neither source path was executed with a real provider.

**Cross-surface finding:** the current `chatService` allowlist contains
neither `abstention` nor `clarification`. The client ignores unknown event
types; after EOF, its `phase_complete` guard rejects either route sequence as
an incomplete stream. This is a source-traced incompatibility corroborated by
the synthetic route outputs, not a Playwright/FastAPI integration result.
`truncated` and `stream_aborted` are explicitly rejected by the client when
seen. No backend or frontend behavior was changed; the normative terminal
contract remains a human technical decision.

## P17 — Repeatable synthetic route regression (B1-R)

Added `tests/audit/test_b1_route_repeatability.py`. It runs the real
`POST /api/chat/query` route in an isolated child process from a temporary CWD
with a minimal allowlist environment. The app is imported under fail-fast file,
SQLite, network, process, thread and filesystem guards; startup is replaced
with a fail-fast sentinel, and HTTPX `ASGITransport` does not enter FastAPI
lifespan.

Ten scenarios ran three times each (30 synthetic requests): success, error,
abstention, clarification, truncation, synthetic abort/cancellation, EOF
without terminal, duplicate terminal, error after tokens, and partial abrupt
generator exhaustion. All normalized event traces matched per scenario;
HTTP status was 200, content type was `text/event-stream`, and each response
closed. There were zero guard violations, protected-data accesses, real
provider calls, external calls, real `AppContainer` constructions, or
normal-lifespan runs. Backend resolution, context preparation, pipeline, and
persistence/memory hooks remained synthetic or no-op. The event loop's local
Unix self-pipe is allowed; outbound/network sockets and network operations are
denied.

Nine negative probes verified fail-fast rejection of protected-file reads,
SQLite, outbound socket creation, subprocess creation, project writes, real
container construction, normal startup, thread start, and provider
construction. Sixteen verifier mutation cases altered run counts, trace,
status, close, exception, guard, side-effect and route-reachability evidence;
each was rejected. The artifact verifier runs as a separate process and has no
TALOS application imports.

The synthetic `stream_aborted` case raises `CancelledError` from the fake
pipeline. The abrupt-close case is fake generator exhaustion after partial
output; neither simulates a real client disconnect. The frontend consumer is
source-traced only because no unit-test runner exists for `chatService` and
Playwright remains frozen. B1-R therefore supplies repeatable backend route
evidence only. The independent verifier returned `TECHNICAL PASS`; no human
technical ACCEPT/REWORK is required for this gate. A-PRE-0 is eligible as a
separate next task. No SSE semantics were adjudicated and F6 is not closed.

## P18 — A-PRE-0 and perimeter reconciliation

The perimeter classifies `tests/audit` as `required`; the current working tree
has 456 `test_*.py` modules in 25 suites: 440 required, 13
qualification-required, 2 optional overrides and 1 support-only. The
historical 446 count came from the `99bd754` perimeter snapshot:
446 executable test modules plus `tests/utils/test_registry.py`, a
`support-only` helper. Four executable modules were added between that
snapshot and `b12e340`. The exact paths and interpretation are recorded in
[`TEST_CERTIFICATION_PERIMETER.md`](./TEST_CERTIFICATION_PERIMETER.md).

[`A_PRE_0_BASELINE_SPEC.md`](./A_PRE_0_BASELINE_SPEC.md) specifies identity,
perimeter, dependencies/runtime, artifact policy, output schema and PRE→POST
comparability. CPython 3.10.21 with uv 0.12.20 resolved and installed 61
packages in a temporary external venv; `uv pip check` and dependency imports
passed. This establishes dependency-set viability only, not TALOS imports,
collection or test results. `scripts/test.sh` would select the existing Python
3.12 `.venv`, so the eventual gate invokes Python 3.10 directly. The lock
shared with E5 remains unchanged.

The opt-in [`scripts/apre_harness.py`](../scripts/apre_harness.py) connects
bubblewrap isolation, syscall tracing, the quality-gate collector,
`result.json` emission and an independent verifier. Bubblewrap fixtures
confirm read-only snapshot/system mounts, writable external scratch, a PID
isolated `/proc`, blocked network and permitted synthetic SQLite/process
operations. Six harness fixtures join 14 reporter and 6 observer fixtures;
all 26 focused tests pass. The builder emits the complete schema from collector
data and evidence artifacts, but forces global `ERROR` if syscall observation
is incomplete; its synthetic tracer preflight blocks the release-gate launch
unless tracing is attached and complete. This host refuses strace attachment with
`PTRACE_TRACEME: Operation not permitted`; the trace is therefore not
qualified, and no `result.json` from TALOS was generated. An external clean
overlay snapshot was regenerated after the harness and the hidden-parent
perimeter-discovery correction; its object store passes `git fsck`.

A-PRE-0 remains `REVIEW REQUIRED / NOT READY FOR A-PRE-1`. No TALOS release
suite, import, or collection was run; A-PRE-1 remains
`PENDING / NOT AUTHORIZED`. E5/Qwen, protected production data and blind pool
remain unchanged and outside execution. Actual effect adjudication belongs to
the authorized baseline run; requiring it before the first run would be
circular.

## Remaining work

The audit stops at evidence and proposed human decisions. Items requiring
follow-up are in [`REALITY_AUDIT_PURIFICATION_BACKLOG.md`](./REALITY_AUDIT_PURIFICATION_BACKLOG.md);
none was executed.
