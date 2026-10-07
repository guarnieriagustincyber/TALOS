# TALOS Backend Operational Archaeology — B0

**Captured:** 2026-09-30
**Evidence level:** static source trace; B0.5 guarded lifecycle probe
**Execution boundary:** B0 itself imported/started nothing. The separate B0.5
probe imported the web package, constructed the app, and invoked startup with a
synthetic container under file/SQLite/network/process/thread guards. No request
was sent in B0.5 and no database, corpus, model, or real provider was accessed.
A later B1-A probe exercised the real HTTP route through in-process ASGI with
synthetic dependencies; it did not start a listening server or normal app
lifespan.

## Finding

The chat route is statically connected to the application, but the normal
application/container initialization path is **not safe to execute under a
"no project DB/corpus reads or writes" constraint**. In particular,
`AppContainer(use_mock=True)` is not an isolated-data mode. A backend endpoint
slice is feasible, but its first harness must avoid constructing
`AppContainer` and avoid application lifespan/startup.

## Operational path and effects

| Layer | Static path / evidence | Initialization or request effects | Replaceability / safe-test implication |
|---|---|---|---|
| Entrypoints | [`scripts/run_ui.py`](../scripts/run_ui.py#L51) asks Uvicorn to load `study_engine.web.app:create_app` as a factory. [`scripts/start_backend.sh`](../scripts/start_backend.sh) loads `src.study_engine.web.app:app`. `pyproject.toml` exposes the separate `talos` CLI. | The backend launch paths load the web application. | Entrypoints are explicit, but the shell launcher binds `0.0.0.0`; do not use it for this audit. |
| App package/factory | [`study_engine.web.__init__`](../src/study_engine/web/__init__.py) imports `create_app`; [`app.py`](../src/study_engine/web/app.py#L66) registers routers. Module scope calls `app = create_app()` at [line 242](../src/study_engine/web/app.py#L242). | Guarded B0.5 observed `mkdir(..., exist_ok=True)` attempts for `src/study_engine/web/static` and `kasiu-lab/storage` during both import and explicit `create_app()`. Both directories already existed; no creation occurred. An initial guarded import from the repo CWD also attempted to read `.env` through `Settings(env_file=".env")`; the guard blocked it before reading content. Re-running from a temporary CWD with provider-like environment variables scrubbed imported successfully without `.env`. The factory also exposes a shutdown endpoint that can send SIGTERM if called. | Import/factory are feasible under a constrained subprocess if CWD is temporary, environment credentials are removed, sensitive file/network/process access is guarded, and app directory creation is allowed only when target directories already exist. Never call the shutdown route. |
| Startup/lifespan | `create_app()` registers `on_startup` at [app.py:94](../src/study_engine/web/app.py#L94). Startup calls `get_container()` directly, reads the KC catalog on the container, then schedules `_schedule_retrieval_warmup`. | In guarded B0.5, the single startup handler called a monkeypatched `get_container()` once with a synthetic empty catalog/container. It then attempted to start the `retrieval-warmup` daemon thread; `Thread.start` was suppressed, so `_warmup_notebooks` and vector search did not run. The guards recorded no SQLite, protected-file, network, or process access. | The startup structure is experimentally confirmed; normal startup remains unsafe because it constructs the real container and starts warmup. A FastAPI dependency override alone does **not** replace the direct startup call. The sanitized startup probe is not evidence about real container initialization. |
| Dependency container | [`dependencies.py`](../src/study_engine/web/dependencies.py#L651) lazily creates a process-global `AppContainer`; `set_container()` mutates the same singleton at [line 661](../src/study_engine/web/dependencies.py#L661). Chat declares `Depends(get_container)` in [`chat.py`](../src/study_engine/web/routes/chat.py#L2026). | Singleton state persists across tests unless explicitly restored. Container construction reads `.env` into process environment and creates `working_dir`. | The dependency is replaceable at the route boundary, but `set_container` is global mutable state. Prefer a synthetic container via app dependency override; do not construct `AppContainer` for B1. |
| Core/store construction | [`AppContainer.__init__`](../src/study_engine/web/dependencies.py#L101) defaults `working_dir` to `repo_root/data/web_state` and invokes a fixed initialization sequence. It calls `StudyLoopExperimentRunner.initialize_pipeline()` at [line 139](../src/study_engine/web/dependencies.py#L139). | Runner opens/initializes `knowledge_store.db`; if the store is empty, it reads and ingests PDFs from `data/benchmark/sources`. It creates/updates `vector_store.db`, embeds available pointer chunks, and reads curriculum/oracle/replay files. Container also seeds folder/notebook state. | Passing a temporary `working_dir` redirects some outputs, but does not prevent reads from the repository corpus/config. `use_mock=True` does not bypass this runner or store setup. |
| `use_mock` boundary | `use_mock` affects provider selection and chooses `:memory:` for `StudentStorage` at [`dependencies.py:421`](../src/study_engine/web/dependencies.py#L421). | Other state remains outside that guarantee: runner-created knowledge/vector stores use `working_dir`; quota manager uses `working_dir/quotas.db`; seeded notebook links write to the knowledge store. The constructor also reads `.env`; provider objects are configured from process environment. | Treat `use_mock=True` as a model/provider behavior switch, **not** as proof of filesystem/data isolation. |
| Test fixtures | [`tests/conftest.py`](../tests/conftest.py#L21) copies `data/web_state/knowledge_store.db` and `vector_store.db` into a temp directory and hashes the source files; it rejects non-empty WAL files. Several endpoint tests then construct `AppContainer(use_mock=True)`. | Fixture setup reads the two repository databases before the tests use the copies. If the copied DB lacks sources, runner initialization can additionally read benchmark PDFs. | These fixtures may isolate writes, but are not suitable evidence for a strict no-read-of-project-databases/corpus B1. They were not run in B0. |
| Scope/context preparation | [`chat_query`](../src/study_engine/web/routes/chat.py#L2026) calls `_prepare_chat_context` directly inside `asyncio.to_thread` at [line 2098](../src/study_engine/web/routes/chat.py#L2098); it is not a separately injected dependency. The helper resolves folder/notebook scope and prepares routing/BKT context. | `ScopeResolver.resolve()` queries the supplied store and can fall back to `NotebookRegistry`; a missing root folder may be created. Context preparation reads module-global TTL caches and may write the last verified context pack. | To test the route without data stores, the first harness must replace `_prepare_chat_context` (or supply a wholly synthetic store/resolver); `dependency_overrides` cannot replace this direct helper call. |
| Retrieval/evidence | [`_assemble_epistemic_context`](../src/study_engine/web/routes/chat.py#L837) reads source metadata and explicit `notebook_sources` authorization through store transactions, applies optional source restrictions, calls chapter-summary and hybrid/lexical search, filters results to authorized sources, applies presentation filtering, and may expand sections. | Search may invoke the store's configured retrieval/vector stack. Authorization-resolution failure or an empty allowlist abstains; hybrid/search failures can fall back to lexical search, with some exception paths returning no results. | A synthetic DB/store is required to test the real helper safely. A fake helper result only verifies the HTTP/SSE route layer, not scope isolation or retrieval behavior. |
| Provider/pipeline | `_resolve_chat_backend()` at [`chat.py:674`](../src/study_engine/web/routes/chat.py#L674) selects the container backend; the handler constructs `StructuredResponsePipeline` at [line 2196](../src/study_engine/web/routes/chat.py#L2196) and streams its events. | Provider network/model work occurs when generation is invoked. Container configuration reads environment-derived provider keys; non-mock mode can configure external providers. | A route-only B1 must inject a fake backend/pipeline. A later core test can use the real `StructuredResponsePipeline` with a deterministic fake backend, without invoking a provider. |
| Persistence/state | The route stores conversation/phase/protected-assessment state in module-global `TTLCache`s. On completion it calls `_update_curriculum_progress` and `_trigger_background_memory_extraction` at [`chat.py:2513`](../src/study_engine/web/routes/chat.py#L2513). | Curriculum progress writes student storage. Memory extraction can schedule an async task and persist cognitive/pedagogical memory. | B1 must replace these side-effect hooks and use unique synthetic session/scope IDs. Test the persistence helpers separately against temporary stores in a later layer. |

## SSE contract: current source and consumer behavior

The backend emits JSON objects in `data:` frames with an `event_type` and
optional object `payload`. The pipeline event vocabulary includes
`phase_start`, `phase_token`, `guard_blocked`, `audit_verdict`,
`evidence_manifest`, `phase_complete`, `stream_aborted`, `error`, `abstention`,
and `truncated`; the route also emits `clarification`, `citation_audit`, and
`exercise_proposal`.

Current route ordering is significant. During a normal pipeline completion,
the route performs its phase-completion bookkeeping and may emit an
`exercise_proposal` immediately before it serializes the pipeline's
`phase_complete` event ([`chat.py`](../src/study_engine/web/routes/chat.py#L2550),
[`chat.py`](../src/study_engine/web/routes/chat.py#L2717), and the final yield
at [`chat.py`](../src/study_engine/web/routes/chat.py#L2736)). Thus the actual
wire order is `exercise_proposal → phase_complete`; the proposal is not
post-terminal. The UI parser accepts that order and rejects every event after
`phase_complete`, including another proposal or a duplicate phase completion.
Success requires a completed phase followed by clean EOF.

Route-level `abstention` and `clarification` are separate successful terminal
outcomes: the route emits `evidence_manifest`, then the outcome event, and
closes without `phase_complete` ([`chat.py`](../src/study_engine/web/routes/chat.py#L2392)).
The consumer accepts these outcomes only when they carry a non-empty public
reason. They remain distinguishable in the returned UI model.
`truncated`, `error`, and `stream_aborted` are failures, including when they
occur after `phase_complete`; they cannot be converted into success by a later
close event.

The consumer parses actual `chatService.ts` logic: malformed JSON in a `data:`
frame, an unknown `event_type`, or a malformed event/payload shape fails closed
with a safe error. SSE comments and non-data framing fields such as `event:`,
`id:`, and `retry:` are ignored rather than parsed as JSON. EOF without a
terminal outcome, including an incomplete trailing `data:` frame, is rejected.
These parser and response-state behaviors have focused tests in
[`chatService.test.js`](../kasiu-lab/ui/tests/chatService.test.js); the route
serialization has endpoint tests in
[`test_chat_sse_endpoint.py`](../tests/pedagogy/test_chat_sse_endpoint.py).
They do not establish real-provider, browser-to-FastAPI, or production behavior.

## B1 readiness and recommended boundary

**Verdict: conditionally feasible, not safe through the normal app/container
startup path.** B0.5 confirms import/factory and startup can be exercised with
guards and a synthetic container, but not the normal container or warmup. The
first backend runtime slice should verify only the real chat route's request
validation and SSE serialization using synthetic inputs:

1. Build a short-lived test application without running the registered startup
   handler or retrieval warmup.
2. Supply a synthetic container through the route dependency override; do not
   call `AppContainer`, `get_container()`, or `set_container()`.
3. Replace `_prepare_chat_context`, provider resolution/pipeline generation,
   curriculum progress, and background-memory hooks with deterministic
   synthetic implementations.
4. Cover malformed/empty input, normal terminal SSE, error SSE, and the
   abstention/clarification terminal events identified above.
5. Keep this claim narrow: it verifies endpoint/SSE framing, not the real scope
   resolver, retrieval, provider, persistence, or product call path.

The B0.5 import/factory condition is to run in a subprocess with a temporary
working directory, no provider credentials in its environment, and tripwires
that deny access to `.env`, data/database/corpus/model files, sockets, and
process creation. The current static/storage directories already exist; if
they do not, the harness must abort before allowing their creation. Startup
must use the synthetic container and suppress thread starts. Do not use the
shell launcher, normal real-container startup, existing copied-DB fixtures,
real `.env` provider configuration, or project database/corpus.

After this route-only slice, test `_prepare_chat_context` and
`_assemble_epistemic_context` against a purpose-built temporary SQLite schema
and synthetic source/chunk fixtures; only later combine the actual pipeline
with a fake provider. A Playwright-to-FastAPI test is downstream of those
boundaries, not the immediate next step.

## What B0 did not establish

- B0 itself was static only. B0.5 exercised import, factory, and a sanitized
  startup handler, but not normal container construction, normal warmup, or an
  HTTP request.
- No database or corpus file was read, hashed, copied, or written during B0.
- B0.5 scrubbed provider-like environment variables in its child process,
  avoided the repository `.env`, guarded database/corpus/model file opens,
  SQLite, network, process, and directory creation, and suppressed thread
  starts. No provider, model, actual retrieval warmup, session, or persistence
  behavior was run.
- Whether existing deployment data is production or development data remains
  outside this source-only assessment.

## B1-A — Synthetic HTTP/SSE route contract

**Result: PASS for the narrow route boundary tested.** A one-shot guarded
subprocess imported the web application from a temporary working directory,
constructed an app, installed a fail-fast startup handler, and sent requests
through HTTPX `ASGITransport`. It did not use `TestClient` or enter FastAPI
lifespan. The real `/api/chat/query` route, Pydantic request validation,
`StreamingResponse`, and SSE framing ran.

The route's domain boundary was synthetic:

- `get_container` dependency override returned a synthetic container/store;
- `_prepare_chat_context` returned a deterministic 11-field context tuple;
- provider resolution and pipeline generation used a fake backend/pipeline;
- citation validation, progress persistence, and background-memory hooks were
  replaced with deterministic no-op fakes;
- `asyncio.to_thread` was replaced with an inline wrapper that asserted it was
  called only for the synthetic context helper. No worker thread was started.

| Case | Observed result |
|---|---|
| Invalid `requested_phase` schema | HTTP 422; context preparation not called |
| Empty/whitespace prompt | HTTP 422; context preparation not called |
| Synthetic normal response | HTTP 200, `text/event-stream`; ordered events `phase_start`, `phase_token`, `evidence_manifest`, `phase_complete` |
| Synthetic pipeline exception | HTTP 200, `text/event-stream`; terminal SSE `error` with the route's expected error message |

The guard denied `.env`, project data/DB/corpus/model access, SQLite, network,
subprocess/system calls, thread starts, and project file writes. All observed
directory creation calls targeted already-existing app directories
(`static`, `storage`, `storage/sources`, `storage/covers`) and were idempotent
no-ops. No guard violation occurred. FastAPI emitted an existing Starlette
deprecation warning for the 422 status constant; it did not affect the result
and was not changed.

**Limits:** the context helper, pipeline, provider, citation logic and
persistence were replaced, so this proves HTTP request validation and route
SSE serialization only. It does not prove real scope resolution, retrieval,
pipeline behavior, persistence, streaming concurrency, or React compatibility.
The one-shot harness is evidence, not yet a committed reusable test.

## B1-B — Synthetic terminal-event route contract

**Result: PASS for route serialization of the four synthetic terminal paths.**
The guarded ASGI route probe reused B1-A's temporary working directory,
scrubbed credential-like environment variables, fail-fast startup, synthetic
container/context, inline context helper, and denials for project data/files,
SQLite, network sockets, processes, threads, and project writes. It made no
guarded access and did not enter the FastAPI lifespan.

| Case | HTTP/SSE events | Last event / EOF | `phase_complete` |
|---|---|---|---|
| Abstention | `evidence_manifest → abstention` | `abstention`; response EOF received | No |
| Clarification | `evidence_manifest → clarification` | `clarification`; response EOF received | No |
| Truncated | `phase_start → truncated → audit_verdict → evidence_manifest → phase_complete` | `phase_complete`; response EOF received | Yes |
| Stream aborted | `phase_start → stream_aborted` | `stream_aborted`; response EOF received after cancellation | No |

For abstention and clarification, the synthetic context took the route's
early abstention branch; pipeline generation was not invoked. For truncation,
the fake pipeline emitted the event sequence found in the source path. For
abort, it emitted `stream_aborted` and then raised `CancelledError`; the route
logged the disconnect and returned, preserving the already-emitted event.
The route returned HTTP 200 `text/event-stream` for each case.

**Interpretation and limits:** `truncated` is not the terminal event in the
pipeline's source flow: it is followed by audit, evidence manifest, and
`phase_complete`. `stream_aborted` is the last observable event, and route
closure follows cancellation. Abstention and clarification are route-level
terminal events with ordinary EOF but no `phase_complete`. These results
verify route serialization with synthetic inputs, not real context generation,
provider behavior, the actual pipeline's runtime, a client disconnect on a
real socket, or React/browser integration. Static source tracing shows the
actual pipeline emits `truncated` before its later completion events and
yields `stream_aborted` before re-raising cancellation; neither real pipeline
path was run.

The UI parser now recognizes both outcomes and validates response termination.
The earlier statement in this B1-B snapshot that the consumer ignores them is
historical and superseded by the current-contract section above. The synthetic
route observations in this section remain limited to their original tested
scope and do not demonstrate browser/FastAPI integration.

## B1-R — Repeatable synthetic regression

The objective criteria are in the
[`B1-R acceptance contract`](./B1R_ACCEPTANCE_CONTRACT.md).

B1-A/B were one-shot probes. They are evidence for the observed route slice,
not a reusable regression suite. The bounded harness reconstruction found no
versioned B1-A/B probe in the repository. Existing `TestClient` tests and
fixtures use or can construct the real container/stores, so they are not reused
for this boundary.

### Harness map

| Part | B1-R implementation/evidence |
|---|---|
| Entrypoint | `tests/audit/test_b1_route_repeatability.py` starts itself as a dedicated Python subprocess with temporary CWD/home, scrubbed allowlist environment, and bytecode writes disabled. |
| Route invocation | Imports the real app under guards, installs a fail-fast startup handler, then uses HTTPX `ASGITransport`; normal lifespan is not entered. |
| Fake dependencies | Async `get_container` override; direct `AppContainer` construction is denied and counted; deterministic context helper, backend resolver, pipeline, and no-op citation/progress/memory boundaries. `asyncio.to_thread` runs inline only for the synthetic context helper. |
| Request and SSE observer | Sends a fixed synthetic `/api/chat/query` request per case; parses SSE JSON, preserving event order while omitting volatile payload fields. |
| Guards | Audit hook rejects `.env`, project data/corpus/model/database files, all SQLite connections, project writes/mutations, unapproved directory creation, network operations and process creation; thread starts and direct outbound socket helpers are blocked. Local AF_UNIX streams are permitted for asyncio's self-pipe. Any prohibited attempt fails the worker. |
| Consumer | `chatService` remains source-traced, not runtime-tested: the UI has no existing unit-test runner for this service, and Playwright/UI integration remains out of scope. |

Reusable: synthetic route setup, fail-fast guard and normalized observer are
versioned in the test. The parent pytest process launches the isolated worker;
the worker itself denies subprocess/process creation. Specific to this
execution: each scenario supplies fake
pipeline events; these are not claims about the actual pipeline. Missing by
design: real pipeline/provider/context, normal lifespan, worker threads,
socket-level client disconnect, and runtime UI consumer observation.

### Result — TECHNICAL PASS

Ten deterministic cases ran three times each (30 synthetic HTTP requests):
success, error, abstention, clarification, truncation, synthetic
`stream_aborted`, EOF without terminal, duplicate terminal, error after tokens,
and synthetic abrupt generator exhaustion. The worker returned HTTP 200 and
`text/event-stream` for all cases, the response body closed, normalized event
sequences matched in all repetitions, and the guards recorded zero forbidden
accesses, external calls, protected-data accesses, real-provider calls or
normal-lifespan runs. Backend resolution and pipeline construction were
replaced by fakes for every request.

The `abrupt_close` case models a fake generator ending after partial output; it
does **not** model a real client disconnect or socket closure. Likewise,
`stream_aborted` is a synthetic `CancelledError` after the fake abort event.
`consumer_observer` is explicitly `SOURCE_TRACED_NOT_RUNTIME_TESTED`. These
limits prevent this result from adjudicating terminal semantics or closing
F6. The contract and independent verifier now turn this result into an
objective `TECHNICAL PASS`; no human engineering ACCEPT/REWORK is needed for
this gate. A-PRE-0 is eligible as the next separate task, but is not started
by B1-R. An unreadable, mismatched, or unsupported evidence envelope returns
`REVIEW REQUIRED`; unmet supported criteria return `TECHNICAL FAIL`.

**Technical exit condition:** normalized observations match across
repetitions, all intended cases are reached, and there are zero forbidden
accesses or external calls. This establishes only a repeatable synthetic route
harness; it is not an F6/PED-F6 pass, a production claim, or React↔FastAPI
integration evidence. A-PRE-0 is the next eligible block; it has not started.

**Subsequent status:** A-PRE-0 is now specified in
[`A_PRE_0_BASELINE_SPEC.md`](./A_PRE_0_BASELINE_SPEC.md), but was not executed.
A-PRE-1 remains `PENDING / NOT AUTHORIZED`.
