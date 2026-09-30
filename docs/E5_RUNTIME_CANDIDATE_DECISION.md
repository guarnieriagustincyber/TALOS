# E5 Runtime Candidate Decision

**Decision ID:** `e5-runtime-candidate-decision-1`<br>
**Decision date:** `2026-09-29`<br>
**Status:** `PATH_A_SELECTED_FEASIBILITY_PENDING`<br>
**Normative runtime decision:** attempt the existing Python 3.10 lock as the
first resolution path, subject to a read-only host/platform feasibility check<br>
**Environment creation or package installation:** not authorized<br>
**Synthetic harness execution:** not authorized<br>
**Benchmark, corpus, retrieval, embeddings, and blind pool:** not authorized<br>
**Production and existing indexes:** unchanged

## Decision

Use **Path A** as the first candidate for resolving E5 runtime reproducibility:
reconstruct the existing dependency lock in a clean, isolated environment for
its Python 3.10 target, if that target is technically viable for the intended
host and platform.

This decision selects an investigation path; it does not declare the current
lock reproducible on the host, approve an environment build, or make the
observed `.venv` normative. The current `.venv` remains untouched and is
evidence of the local installed state only.

## Required sequence

1. **Read-only feasibility assessment.** Before creating an environment or
   installing anything, identify the exact intended OS, architecture, Python
   implementation/ABI and patch release, available Python 3.10 interpreter,
   uv version, and whether every locked dependency has a compatible artifact
   for that target. Record the commands/evidence and the lock hash. Do not
   resolve new package versions during this check.
2. **Stop if Path A is infeasible.** Document the concrete incompatibility or
   missing prerequisite. Do not silently substitute Python 3.12, relax pins,
   edit the existing lock, or treat the current `.venv` as equivalent.
3. **Open Path B only by a new decision.** If A is infeasible, propose a
   separately versioned Python 3.12.3 runtime specification and lock. The new
   specification must pin the interpreter/platform target and all direct and
   transitive dependencies with hashes. It must explicitly supersede neither
   the existing lock nor frozen compatibility contract until reviewed and
   approved.
4. **Request specific preparation authorization.** A feasibility pass does not
   authorize environment creation, package installation, or harness execution.
   Request those permissions separately and state the isolated location,
   artifacts, and commands before proceeding.
5. **Reconstruct twice after authorization.** Build two clean environments in
   separate disposable locations using only the selected lock and pinned
   interpreter. Do not reuse `.venv`, global packages, or mutable dependency
   resolution. Record runtime/package/platform fingerprints and compare them.
6. **Close the runtime gate only on matching evidence.** Set
   `RUNTIME_REPRODUCIBLE` only if both reconstructions match the selected
   specification and each other, with no dependency on the existing `.venv`
   or global host packages.
7. **Request separate synthetic-harness authorization.** Only after runtime
   closure, and with separate explicit authorization, run the E5 compatibility
   harness on synthetic inputs. Record inputs, artifact hashes, runtime
   fingerprint, padding behavior, numerical tolerances, outputs, and command.
   This still does not authorize a benchmark or blind-pool generation.

## Reproducibility evidence

For each reconstruction, retain a manifest containing at least:

- selected decision and lock identifiers plus SHA-256 of the lock;
- exact OS, architecture, Python implementation/version/ABI, and uv version;
- package inventory with exact versions and installed artifact hashes where
  available;
- E5 ONNX and tokenizer revision, byte size, and SHA-256;
- environment isolation method and the explicit absence of `.venv`/global
  package reuse;
- a canonical fingerprint over the preceding runtime and artifact identity
  fields.

The two canonical fingerprints must be equal and each reconstruction must
independently satisfy the selected specification. Matching fingerprints alone
do not waive missing lock, platform, or artifact evidence.

## Gate boundaries

- **E5 runtime:** Path A selected; feasibility and reproducibility remain
  pending.
- **E5 padding/compatibility harness:** prepared but not authorized to execute.
- **Qwen:** remains blocked independently; this decision does not address its
  artifact provenance or runtime.
- **Blind pool:** remains pending and is not part of runtime validation.
- **Benchmark:** not authorized; closing the E5 runtime does not authorize it.
- **Production and existing indexes:** out of scope and must remain unchanged.

## Decision changes

Any move from A to B requires a new, reviewed, versioned decision recording the
reason A is infeasible, the exact new target, the new lock identity, and the
scope of any supersession. No environment creation, package installation,
model inference, or benchmark execution is implied by that future decision.
