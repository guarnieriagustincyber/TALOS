# B1-R Objective Acceptance Contract

**Contract ID:** `TALOS-B1-R-1`
**Scope:** synthetic `POST /api/chat/query` HTTP/SSE route boundary
**Status:** versioned; evaluated by the independent artifact verifier

B1-R tests whether a repeatable, sterile synthetic observation can detect the
declared route traces and prohibited-operation attempts. It does **not** assert
that TALOS is correct, adjudicate SSE terminal semantics, verify the UI
consumer at runtime, or certify production integration.

## Objective pass criteria

The versioned machine-readable criteria are in
[`tests/audit/b1r_contract.json`](../tests/audit/b1r_contract.json). A
`TECHNICAL PASS` requires all of the following:

1. Exactly the ten contract scenarios, each executed exactly three times
   through the real FastAPI route.
2. For every observation: HTTP status, `text/event-stream` content type,
   stream closure, expected exception, `phase_complete` presence, and ordered
   event sequence match the contract.
3. Each scenario's normalized observations are identical across all three
   runs. Normalization retains semantic fields and excludes timestamps,
   request IDs, object IDs, and volatile event payloads.
4. The route request count and synthetic context/backend/pipeline invocation
   counts each equal 30. No real `AppContainer`, provider, protected data,
   normal startup/lifespan, thread, external call, or functional change is
   recorded.
5. All nine negative probes are rejected exactly once by the expected guard:
   protected-file read, SQLite connection, outbound socket, subprocess
   creation, project write, real container construction, normal startup,
   thread start, and provider construction.
6. The isolated worker uses temporary CWD/home and a scrubbed allowlist
   environment. The outer test confirms `git status --porcelain` is identical
   before and after the run.
7. The runner writes a temporary JSON artifact. A separate verifier process,
   which imports no TALOS application code, checks the artifact against the
   versioned contract. The artifact records the SHA-256 of the exact contract
   bytes used by the worker; the verifier requires a match. Mutation tests
   prove that the verifier rejects representative missing/altered requirements.

The individual scenario traces and expected exceptions are normative only for
this synthetic harness. In particular, `stream_aborted` is a fake pipeline
event followed by synthetic cancellation; `abrupt_close` is fake generator
exhaustion, not a real socket disconnect. The UI consumer remains
`SOURCE_TRACED_NOT_RUNTIME_TESTED`.

## Result states

| Result | Meaning | Process exit |
|---|---|---:|
| `TECHNICAL PASS` | Every supported contract criterion and negative guard test passed. B1-R is objectively cleared; A-PRE-0 becomes eligible as the next separate task. | 0 |
| `TECHNICAL FAIL` | Evidence is interpretable, but one or more defined criteria failed. Do not advance; repair the failed criterion and rerun. | 1 |
| `REVIEW REQUIRED` | The verifier cannot safely adjudicate because the artifact/contract is unreadable, malformed, mismatched, or uses an unsupported schema. This is not a pass or a product failure. | 2 |

No human technical ACCEPT/REWORK judgment is required after `TECHNICAL PASS`.
Human intervention is reserved for `REVIEW REQUIRED` or a separate governance
decision to authorize/sequence later work. B1-R does not start A-PRE-0 or
A-PRE-1 itself.

## Verification design and limits

The runner is
[`tests/audit/test_b1_route_repeatability.py`](../tests/audit/test_b1_route_repeatability.py).
The independent verifier is
[`scripts/verify_b1r_artifact.py`](../scripts/verify_b1r_artifact.py).
Sensitivity tests are
[`tests/audit/test_b1r_verifier.py`](../tests/audit/test_b1r_verifier.py).

Negative probes invoke only safe synthetic operations that are intercepted
before the OS/resource action occurs. The provider probe validates the
explicit provider-construction sentinel and the route replaces backend
resolution; it is not a universal proof that every provider library is
unreachable. Likewise, absence of real provider calls is claimed only for this
replaced route slice. No live provider, real filesystem data, DB, corpus,
model, browser, or lifecycle is touched.

Mutation tests alter evidence fields independently (including cases,
repetitions, events, status, closure, exceptions, counters, guard results and
route reachability) and require the verifier to reject each mutation. They
validate verifier sensitivity; they are not mutations of TALOS product code.

Because contract, artifact and verifier are versioned independently of the
route runner's assertions, a runner assertion alone cannot produce a pass.
Changes to the expected behavior require a reviewed versioned contract change;
they must not be silently inferred from a new observation.
