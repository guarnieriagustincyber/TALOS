# Vector Space v2 Identity Promotion — Offline Gate Design

**Status:** design baseline; synthetic promotion fixtures validated offline;
no index is promoted by this document.
**Scope:** evidence policy and birth contract for future vector indexes.
**Out of scope:** runtime changes, index creation, embedding generation,
reindexing, migration, database edits, or changes to notebook identity records.

This design supplements
[`VECTOR_SPACE_IDENTITY.md`](./VECTOR_SPACE_IDENTITY.md). The v2 contract and
its canonicalization rules remain normative; this document defines what
additional evidence is required to make claims about vectors actually stored.

## 1. Non-negotiable invariant

**Identity and provenance are separate claims.**

- **Identity** describes the vector transformation and defines comparability.
  `vector_space_id` is derived only from the v2 compatibility fields.
- **Provenance** is the evidence that specific artifacts and an executed
  pipeline produced a specific, complete set of stored vectors.

Therefore:

```text
valid vector_space_id != proof that stored vectors belong to that space
```

A complete and reproducible contract may establish what an identity would be
for vectors generated under that contract. It cannot, by itself, promote an
older index. A historical promotion additionally requires a trustworthy,
unbroken link from the contract and actual execution to the exact stored vector
set, with complete coverage and no material contradiction.

The gate records declared metadata, observed facts, and verified execution as
different evidence classes. A label match, dimension match, or configuration
file is not a substitute for execution evidence.

## 2. Evidence record and evidence states

Every evidence item used in a decision must record its source and authority,
scope (model, run, batch, or exact index snapshot), integrity/protection
mechanism, verifier and verification result. Preserve the original item or a
stable reference to it. Do not silently turn missing or unverifiable evidence
into a positive finding.

Use these evidence states to retain why a promotion decision was reached:

| Evidence state | Meaning |
|---|---|
| `UNKNOWN` | No evidence for the claim was found. |
| `UNVERIFIED` | A claim exists, but its source, integrity, or contents have not been verified. |
| `UNBOUND` | Evidence is valid in isolation but is not linked to the exact execution, vector set, or index snapshot under review. |
| `CONTRADICTORY` | Two or more credible evidence items make materially incompatible claims. |
| `INVALID` | Direct verification shows malformed evidence or a violated contract/invariant. |
| `VERIFIED` | Evidence is authentic enough for the stated claim, internally valid, and verified for the stated scope. |

These are evidence-level states, not replacements for the compatibility
assessment statuses already defined by v2. A contradiction is not resolved by
choosing the more convenient record. Record the conflict and keep the promotion
decision blocked until it is authoritatively resolved.

## 3. Promotion decisions

Apply the decision to a clearly bounded vector set and index snapshot. The
following states are promotion outcomes; none means that this offline gate has
actually assigned an identity to an existing index.

### `PROMOTABLE`

An index is eligible for a separately authorized promotion only if every
predicate is verified:

```text
IdentityComplete
AND ArtifactIdentityVerified
AND PipelineIdentityVerified
AND VectorSetBindingVerified
AND CoverageVerified
AND NoMaterialContradiction
```

- `IdentityComplete`: all required v2 compatibility fields validate and
  produce the expected identity.
- `ArtifactIdentityVerified`: the model and tokenizer revisions and complete
  artifact manifests resolve to the declared digests.
- `PipelineIdentityVerified`: the executed input transformations, tokenization,
  truncation, pooling, normalization, and output dimensions implement the
  declared contract.
- `VectorSetBindingVerified`: trustworthy evidence binds that exact execution
  and contract to the exact vector set and stored index snapshot.
- `CoverageVerified`: the binding covers every vector in the bounded index
  snapshot, including partial writes, retries, deletions, and duplicates as
  applicable; no unaccounted records remain.
- `NoMaterialContradiction`: no unresolved evidence conflicts with any of the
  above.

`PROMOTABLE` is eligibility, not promotion. Promotion remains a separate
authorization and operation outside this gate.

### `CANDIDATE / NEEDS VERIFICATION`

Use for a prospective index or a bounded set whose v2 identity appears
complete, but one or more positive verification steps are still pending (for
example, verifying artifact inventory or completing a future execution's
coverage checks). It must not be used to imply an existing historical index is
compatible. If the missing link is historical execution or stored-set
provenance that cannot be established, classify the existing set as
`LEGACY / UNRESOLVED` instead.

### `LEGACY / UNRESOLVED`

Use when normative identity fields or reliable evidence tying them to the
stored vectors are absent, unknown, unverified, or unbound. Do not derive or
assign an identity retrospectively from provider/model labels, dimensions,
notebook code, or a declared contract alone.

### `HETEROGENEOUS`

Use when the bounded aggregate contains records from multiple vector spaces or
generation pipelines. Do not assign one identity to the aggregate. Split it
conceptually into independently bounded sets; assess each set on its own
evidence. Do not physically split or rewrite records as part of this gate.

### `REJECTED`

Use when verification detects invalid or materially contradictory evidence,
such as a verified output dimension that contradicts the contract, an
incomplete artifact manifest presented as complete, or evidence that the
claimed execution did not produce the target records. Record the failed
predicate and evidence references. Re-evaluate only when corrected,
authoritative evidence is available; never fall back silently to a plausible
identity.

## 4. v2 evidence matrix

The `vector_space_id` column is derived only by the existing v2 rules. The
“execution evidence” column is additional proof about produced vectors; it
does not add fields to the identity hash. Evidence must be tied to the same
bounded run and stored set where the claim concerns an existing index.

| v2 field / claim | Acceptable evidence | Verification | Execution evidence required for stored vectors | If missing or failed |
|---|---|---|---|---|
| `schema` | Contract bytes with `talos-embedding-contract-v2` | Strict v2 validator; reject unknown/missing fields | Run record identifies these exact contract bytes | Missing: `LEGACY`; malformed/unsupported: `REJECTED` |
| `model_id` | Canonical model identifier in the contract and resolved artifact source | Exact identifier match; do not infer from a row label | Execution record binds the loaded model to the contract | Missing/unverified: no promotion |
| `model_revision` | Immutable lowercase hex revision resolved from an authoritative source | Resolve revision and verify it is immutable | Run record identifies the resolved revision | Mutable alias, absent, or unverifiable: no promotion |
| `model_artifact_sha256` | Canonical `talos-artifact-manifest-v1` and complete model file inventory | Recompute manifest digest; inspect inventory completeness, including effective configuration, weights, pooling modules, and custom code | Evidence identifies the verified artifact inventory loaded by the run | Absent/incomplete/mismatched: no promotion; mismatch: `REJECTED` |
| `dimensions` | Contract plus observed output shape | Validate positive integer and inspect generated vectors' shapes | Complete-set dimension scan against the exact index snapshot | Missing: no promotion; verified contradiction: `REJECTED` |
| `max_length` | Contract and effective tokenizer/model input configuration | Confirm truncation limit used by the executed pipeline | Run-level evidence or equivalent test record shows the effective limit | Missing/unverified: no promotion |
| `truncation_side` | Contract and effective tokenizer configuration | Confirm left/right truncation behavior, including special-token handling | Execution evidence verifies the configured behavior | Missing/unverified: no promotion; contradiction: `REJECTED` |
| `pooling` | Registered v2 pooling identifier and implementation | Match implementation to the exact normative definition | Run/build identity and conformance evidence bind implementation to execution | Unknown or unverified: no promotion |
| `normalization` | Contract and declared v2 normalization rule | Confirm operation and ordering after pooling | Execution evidence or conformance output verifies the operation was applied | Missing/unverified: no promotion; contradiction: `REJECTED` |
| `tokenizer_id` | Canonical tokenizer identifier | Resolve and exact-match the artifact source | Run record binds the loaded tokenizer to the contract | Missing/unverified: no promotion |
| `tokenizer_revision` | Immutable lowercase hex tokenizer revision | Resolve and verify immutable revision | Run record identifies the resolved tokenizer revision | Mutable alias, absent, or unverifiable: no promotion |
| `tokenizer_artifact_sha256` | Canonical manifest of tokenizer vocabulary/merges, configuration, and special tokens | Recompute digest and verify inventory completeness | Evidence identifies the verified inventory loaded by the run | Absent/incomplete/mismatched: no promotion; mismatch: `REJECTED` |
| `query_prefix`, `query_instruction` | Exact strings in the contract | Byte/Unicode-normalized exact match under v2 rules | Query-generation execution evidence when asserting query-vector provenance | Missing/unverified: no promotion of that claim |
| `query_preprocessing` | Ordered registered operation identifiers | Validate registry and order | Run conformance evidence shows the declared query pipeline was executed | Missing/unverified: no promotion of query vectors |
| `passage_prefix`, `passage_instruction` | Exact strings in the contract | Byte/Unicode-normalized exact match under v2 rules | Passage-generation execution evidence linked to stored records | Missing/unverified: no promotion |
| `passage_preprocessing` | Ordered registered operation identifiers | Validate registry and order | Run conformance evidence shows the declared passage pipeline was executed | Missing/unverified: no promotion |
| `vector_space_id` | Validated v2 contract and specified canonical hash | Independently recalculate with implementations A and B; require exact equality | Store/run evidence records the ID for the execution and links it to the exact vector set | Missing/mismatch: no promotion; mismatch: `REJECTED` |
| Artifact-to-run binding | Verified model/tokenizer manifests plus execution record | Verify integrity and that the execution used the manifested artifacts | Run evidence binds loaded artifacts, effective configuration, and contract | Unbound: existing index remains `LEGACY`; contradiction: `REJECTED` |
| Run-to-vector-set binding | Durable run/batch record and bounded vector-set identity | Independently verify references, counts, and content/inventory integrity | Evidence must link execution outputs to every record in the target snapshot | Unbound: `LEGACY`; incomplete: no promotion |
| Complete coverage / no mixture | Exact index snapshot and exhaustive inventory, including record identifiers and vector dimensions | Reconcile generated, written, retried, deleted, and remaining records; check all records, not a sample | Demonstrate that every stored vector in scope is accounted for by a verified run/space | Incomplete or mixed: `HETEROGENEOUS` or `LEGACY`; verified violation: `REJECTED` |
| `provenance` fields | Optional operational metadata allowed by v2 | Validate supplied structure and preserve as evidence metadata | Provider/runtime record may corroborate execution, but is not sufficient alone | Missing provenance does not change the ID; absent execution proof still blocks promotion |

The matrix does not make `provider_id`, package versions, device, precision,
timestamps, hostnames, or a similarity metric normative v2 identity fields.
They may help substantiate execution, but the v2 contract deliberately excludes
them from `vector_space_id`. A transformed or quantized model must be represented
by the appropriate distinct artifact identity as specified by v2.

### Minimum evidence chain

For a stored index, the evidence must support this complete chain:

```text
validated v2 contract and vector_space_id
        -> verified model/tokenizer artifacts
        -> identified executed pipeline
        -> generated output batches
        -> complete exact vector set
        -> exact stored index snapshot
```

Integrity hashes can detect changes to the evidence they cover; they do not by
themselves prove who created the evidence, that it is truthful, or that it
covers every record. The evidence source and scope must therefore also be
verifiable. Sampling may support diagnostics but is not complete-coverage proof.
The concrete serialization and storage format for these bindings is a later
implementation decision; this gate does not prescribe or create one.

## 5. Contract for future index birth (design only)

A future implementation may claim an index was born under v2 only if it
implements and verifies the following sequence:

1. Resolve immutable model and tokenizer revisions and complete artifact
   manifests; fail closed if any identity field is unavailable.
2. Construct and validate the v2 contract from effective configuration, not
   merely intended/default configuration. Calculate `vector_space_id` using
   the canonicalization rules in `VECTOR_SPACE_IDENTITY.md`.
3. Bind a run identifier to the exact contract, identity, artifact manifests,
   and pipeline implementation/build needed to verify declared behavior.
4. Generate and write records while retaining enough run/batch linkage to
   account for retries and partial failures. Do not silently mix identities.
5. At completion, verify dimensions and reconcile the complete generated
   inventory with the exact stored index snapshot. Publish a completed
   provenance record only after the checks pass.
6. On reopen/read, verify that the index snapshot is still bound to the same
   identity and complete evidence. If contents changed without a verifiable
   update record, fail closed for promotion/compatibility claims.

This is a future behavior contract, not an implementation specification. This
gate does **not** create a real manifest or run record, load a model, generate
embeddings, write SQLite, modify runtime code, or create an index.

## 6. Offline case dispositions

These are dispositions from the existing read-only audit and the approved
scope. They do not result from re-reading or modifying production data in this
gate.

| Case | Gate disposition | Rationale |
|---|---|---|
| `fadena-std`, Qwen, 1024 dimensions | `LEGACY / UNRESOLVED` | Existing labels and dimensions do not establish immutable artifact identity, executed v2 transformations, or historical binding to the exact stored vectors. |
| Local multilingual-E5 shards, 384 dimensions | `LEGACY / UNRESOLVED` | Shard presence, model labels, dimension, and duplicate observations do not prove complete generation provenance or historical query use. |
| `NB-SEC-01-C-PTR` aggregate | `HETEROGENEOUS` | The audited aggregate includes Qwen/1024 and deterministic-hash/128 vectors. Do not assign one identity to the aggregate; do not physically separate or relabel it here. |
| Hypothetical index born under v2 | Synthetic fixture only: `CANDIDATE`, then eligible for `PROMOTABLE` only after every predicate is verified | The fixture describes decision behavior; it is not a TALOS index and must not create data or imply certification. |

No historical index is promoted, and no equivalence between Qwen and E5 is
asserted.

## 7. Offline verification and closure criteria

The design is ready for a separately scoped implementation proposal when all
of the following are addressed:

- The v2 normative field list, canonicalization, hash calculation, and existing
  compatibility statuses are reused without redefining identity.
- The evidence-state and promotion-decision meanings above are accepted.
- The matrix distinguishes configuration/declared intent from executed
  behavior and stored-vector provenance for every relevant claim.
- The exact evidence chain, complete-coverage requirement, and handling of
  partial writes, retries, contradictions, and mixtures are explicit.
- The future birth sequence fails closed and is clearly separated from this
  offline design.
- Synthetic positive and adversarial fixtures cover complete binding, missing
  fields, mutable revisions, incomplete manifests, unbound execution, partial
  coverage, dimension/configuration mismatch, mixed spaces, and contradictory
  evidence. No fixture contains production vector data.
- Existing implementation A/B identity and compatibility results remain
  exactly reproducible for equivalent valid contracts; incomplete or invalid
  contracts fail closed. Any new executable validator or runtime behavior
  requires its own implementation gate and tests.

This document closes the **design scope only**. It does not certify an index,
authorize an identity assignment, or authorize implementation or migration.

## 8. Promotion Fixture Gate — offline result

The synthetic decision gate is implemented and validated without runtime
integration. Implementation A is `assess_promotion` in
[`vector_space_contract.py`](../src/study_engine/diagnostics/vector_space_contract.py);
implementation B is the standalone reference in
[`reference_promotion_gate.py`](../tests/unit/diagnostics/reference_promotion_gate.py).
Both return exactly the same `status`, stable `reason` code, and calculated
`vector_space_id` for every fixture. B independently calculates the identity
using the existing reference implementation.

The fixture suite
[`cases.json`](../tests/fixtures/vector_space_promotion/cases.json) covers:

| Fixture | Decision | Reason |
|---|---|---|
| `PROMOTABLE` | `PROMOTABLE` | `ALL_PROMOTION_PREDICATES_VERIFIED` |
| `NEW_V2_INDEX` | `PROMOTABLE` | `ALL_PROMOTION_PREDICATES_VERIFIED` |
| `CONTRACT_ONLY` | `CANDIDATE` | `CONTRACT_ONLY` |
| `PROVENANCE_MISSING` | `LEGACY / UNRESOLVED` | `PROVENANCE_MISSING` |
| `ARTIFACT_UNVERIFIED` | `CANDIDATE` | `ARTIFACT_UNVERIFIED` |
| `PARTIAL_COVERAGE` | `LEGACY / UNRESOLVED` | `PARTIAL_COVERAGE` |
| `INVENTORY_COUNT_MISMATCH` | `LEGACY / UNRESOLVED` | `PARTIAL_COVERAGE` |
| `MANIFEST_MISMATCH` | `REJECTED` | `MANIFEST_MISMATCH` |
| `MIXED_VECTOR_SPACES` | `HETEROGENEOUS` | `MIXED_VECTOR_SPACES` |
| `CONTRADICTORY_EVIDENCE` | `REJECTED` | `CONTRADICTORY_EVIDENCE` |
| `MUTABLE_REVISION` | `REJECTED` | `MUTABLE_REVISION` |
| `INVALID_INDEX` | `REJECTED` | `INVALID_INDEX` |
| `DIMENSION_MISMATCH` | `REJECTED` | `INVALID_INDEX` |
| `INVALID_CONTRACT` | `REJECTED` | `INVALID_CONTRACT` |
| `HISTORICAL_PLAUSIBLE_ID_WITHOUT_PROVENANCE` | `LEGACY / UNRESOLVED` | `PROVENANCE_MISSING` |

The last case deliberately supplies the mathematically correct, plausible
`vector_space_id` and a synthetic historical record, while leaving execution
and index binding evidence unknown. It remains `LEGACY / UNRESOLVED`. This
demonstrates that identity alone cannot promote historically incomplete data.
The inventory-count case additionally prevents a claimed complete coverage
count from overriding an incomplete synthetic record inventory.

Run the offline check and focused tests from the repository root:

```bash
.venv/bin/python scripts/check_vector_space_promotion_fixtures.py
.venv/bin/python -m pytest tests/unit/diagnostics/test_vector_space_promotion.py -q
```

All fixture data is synthetic. The validator is not wired into retrieval,
ingestion, persistence, Colab, or runtime behavior. The passing result closes
the **Promotion Fixture Gate only**; it does not promote or certify any real
index and does not authorize migration.
