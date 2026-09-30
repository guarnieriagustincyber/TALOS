# Approved Addendum — Blind Pool Before Initial Qrels

**Addendum ID:** `backend-selection-contract-v1-addendum-blind-pool-1`<br>
**Status:** `APPROVED_METHODOLOGICAL_ADDENDUM`<br>
**Approved at:** `2026-09-29T18:39:49.840-03:00`<br>
**Execution authorization:** not granted; separate gate remains `PENDING`<br>
**Parent:** [Embedding Backend Selection Benchmark Contract v1](./EMBEDDING_BACKEND_SELECTION_BENCHMARK_CONTRACT.md)<br>
**Reason:** `SOURCE_INSUFFICIENT`, documented by the [Initial Qrels Candidate Source Gate](./INITIAL_QRELS_CANDIDATE_SOURCE_GATE.md).<br>
**Related execution gate:** [Blind Pool Generation Authorization Gate](./BLIND_POOL_GENERATION_AUTHORIZATION_GATE.md).

## 1. Purpose

This addendum resolves the documented circular dependency: no sufficiently
independent source for initial query/chunk pairs was found, while the frozen
pooling rule obtains candidates from Qwen, E5, and the lexical baseline. It
defines a separate, blinded candidate-discovery phase so human judges can
create qrels from the union pool.

The user approved this methodology as a protocol decision only. This approval
does not authorize execution. The execution gate remains
`PENDING`; model access, dependency installation, retrieval, candidate
generation, and pool construction remain unauthorized until execution
prerequisites are recorded and the execution gate receives separate explicit
authorization.

## 2. Exact change proposed to v1 sequence

The v1 sequence says initial judgments are frozen before running Qwen or E5,
then the pooled candidate set is judged. Because the source gate returned
`SOURCE_INSUFFICIENT`, this approved addendum records the following explicit
exception:

```text
v2.400 queries + approved scope snapshot
                 ↓
isolated blind-pool candidate generation
Qwen top-100 + E5 top-100 + lexical top-100
                 ↓
deterministic union, provenance sealed, no metrics
                 ↓
human pair judgments on blinded pool
                 ↓
adjudication and qrels freeze
                 ↓
separate authorization for comparative benchmark
```

This changes only the ordering of candidate discovery relative to the initial
human pair judgments. It does not weaken the frozen pool rule, judgment rubric,
scope/ACL enforcement, unknown handling, exhaustive-judgment requirements, or
the requirement that qrels be frozen before the comparative benchmark.

The parent v1 contract remains byte-for-byte unchanged and governs except for
the explicitly approved sequence exception in this addendum. Retain both
documents and record their hashes together; do not silently edit or relabel v1.

## 3. Proposed authorization boundary

If approved and separately authorized for execution, the phase may do only:

- execute Qwen candidate retrieval up to top-100 per query/scope;
- execute E5 candidate retrieval up to top-100 per query/scope;
- execute the frozen lexical baseline up to top-100 per query/scope;
- union and deduplicate candidates by `(notebook_id, chunk_id)`, preserving
  restricted provenance for every contributing source/rank;
- validate scope/ACL and integrity, serialize deterministically, hash the pool,
  and create independent blinded adjudication packets with necessary chunk
  evidence;
- stop once the pool and reviewer packets are verified and frozen.

Pooling, cutoffs, keys, scope failure behavior, and deterministic serialization
are inherited from the v1 contract and detailed in the execution gate. No
results beyond these limits may be generated.

## 4. Required blindness and integrity

- Judges receive neither backend identity nor candidate source, rank, score,
  original chunk ID, or per-backend result list.
- Reviewers receive distinct aliases and independently randomized candidate
  order. Randomization seeds and alias/provenance mappings remain restricted;
  outputs are reproducible from the restricted record.
- Candidate source metadata is excluded from reviewer packets unless it is
  necessary evidence to judge the chunk; any necessary display must be
  assessed for leakage before packet release.
- Any out-of-scope candidate, source/corpus mismatch, duplicate-key conflict,
  missing content, hash mismatch, or detected unblinding invalidates the
  affected pool version. Stop; do not filter or repair it in place. Create a
  new version and hashes after correction.
- `UNKNOWN` and unjudged pairs remain distinct from explicit grade `0`.
- Human reviewers judge relevance, not backend quality. Preserve both
  independent judgments, rationale, reviewer identity, timestamps, and any
  third-party adjudication.

## 5. Preservation and prohibited work

This addendum does not authorize or permit:

- modification of `golden_set_v2_400.json`, its qrels, v2.401, historical
  reports, existing reviewer packets, corpus, ACLs, or production indexes;
- creation or activation of a production index, vector-space identity, or
  runtime configuration;
- retrieval/embedding activity outside the candidate generation limits above;
- calculating or reporting Recall, Precision, MRR, nDCG, facet coverage,
  latency, RSS/CPU comparisons, statistical tests, or any other benchmark
  metric;
- comparison of Qwen and E5, model ranking, backend selection, or winner
  declaration;
- benchmark execution or claims of `BENCHMARK_READY`.

All outputs belong to a new, isolated, versioned directory. Existing source
files and artifacts remain byte-for-byte unchanged. Access to raw retrieval
outputs and restricted provenance is limited to the designated custodian, not
the judges.

## 6. Stop condition and downstream gates

The candidate-generation phase ends after:

1. the three candidate sources have completed or reported their actual
   candidate counts;
2. scope/ACL, IDs, deduplication, content availability, and all hashes pass
   integrity verification;
3. the union pool and separate blinded reviewer packets are frozen; and
4. the restricted provenance record is sealed and access-controlled.

At that point, execution stops. The output is **only a candidate pool for human
adjudication**, not benchmark evidence and not a result favoring any backend.
Human adjudication is a separate subsequent phase. Disagreements, unknowns,
and coverage gaps must be resolved under the parent contract before qrels can
be frozen. Comparative benchmark execution requires its own later
authorization after `QRELS_FROZEN`.

## 7. Resource and artifact prerequisites

Approval of this methodological addendum does not approve resource limits,
artifact acquisition, or execution. Before execution authorization, record
and approve:

- exact Qwen/E5 model and tokenizer artifacts, revisions, hashes, and
  provenance;
- lexical baseline implementation/configuration and version;
- host, CPU/GPU mode, dependency/environment manifest, and whether downloads
  or installs are required;
- identical corpus/chunk/scope snapshot hashes and isolated output directory;
- measurable RSS, CPU, temperature, concurrency, duration, and stop limits;
- deterministic tie-break, seeds, randomization procedure, and raw-output
  retention/deletion policy.

The provisional 2 GiB TALOS RSS assumption remains
`PENDING_CONFIRMATION`; no CPU threshold has been approved. Do not infer that
either model fits those limits. Approval of this addendum does not waive or
resolve them.

## 8. Decision record

| Decision | State |
|---|---|
| Addendum approved | Yes — `APPROVED_METHODOLOGICAL_ADDENDUM` |
| Parent v1 modified | No |
| Blind-pool execution authorized | No |
| Qwen/E5/lexical retrieval executed under this proposal | No |
| Metrics or model comparison authorized | No |
| Production or index changes authorized | No |

The addendum approval is the methodological decision only. The blind-pool
execution gate must be separately authorized after its resource/artifact
prerequisites are completed. Benchmark execution always remains a later,
separate gate.
