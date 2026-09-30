# TALOS Vector Space Identity — Draft v1

**Status:** offline contract and fixture validator only. This document and
validator do not change retrieval, ingest, Colab, SQLite, or runtime behavior.

## Purpose

Vector dimensionality is a shape constraint, not an identity. Query and index
vectors may be compared only when they have the same `vector_space_id`.
Provider metadata, runtime details, and artifact provenance are recorded
separately from fields that define vector comparability.

This specification is a candidate contract for future integration. It does not
authorize migration or relabeling of existing vectors.

## Contract v2 compatibility fields

A strict `talos-embedding-contract-v2` has the following required fields:

| Field | Meaning |
|---|---|
| `model_id` | Canonical model identifier. |
| `model_revision` | Immutable, lowercase 40- to 64-character hexadecimal revision. Mutable aliases such as `main` are invalid. |
| `model_artifact_sha256` | SHA-256 of a canonical manifest of model artifact paths and file hashes. |
| `dimensions` | Positive output dimensionality. |
| `max_length` | Positive token limit. |
| `truncation_side` | `left` or `right`. |
| `pooling` | Registered, versioned pooling algorithm identifier. |
| `normalization` | `l2` or `none`. |
| `tokenizer_id`, `tokenizer_revision` | Canonical tokenizer and pinned immutable revision. |
| `tokenizer_artifact_sha256` | SHA-256 of a canonical manifest of tokenizer artifact paths and file hashes. |
| `query_prefix`, `query_instruction`, `query_preprocessing` | Exact ordered query-side transformations. |
| `passage_prefix`, `passage_instruction`, `passage_preprocessing` | Exact ordered passage-side transformations. |

Every compatibility field is required and non-null. Empty strings explicitly
mean no prefix/instruction. The two revisions are lowercase hexadecimal
40-to-64-character immutable identifiers; mutable names such as `main`,
`latest`, or tags are not accepted as revisions. Digests are lowercase
64-character SHA-256 values.

The only accepted v2 top-level fields are `schema`, the compatibility fields
above, and optional `provenance`. Unknown fields are rejected. V2 has no
implicit extension mechanism: a new compatibility field requires a new schema
version and corresponding validator. Provenance, when present, is an object
with only the declared provenance keys in the next section. Its core fields
`provider_id`, `provider_version`, `python_version`, `device`, and `precision`
are required; `framework_versions`, `generated_at`, and `hostname` are
optional. `null` is invalid for both compatibility and supplied provenance
fields. Omitting the entire optional provenance object does not change identity.

All string values in the compatibility payload are normalized to Unicode NFC
using Unicode Character Database (UCD) version 15.0.0 before serialization.
The implementation must refuse to calculate an identity if its available UCD
version differs; the implementation's own runtime version is not a substitute
for this fixed canonicalization rule. The canonicalizer does not trim,
case-fold, or otherwise rewrite opaque identifiers. The separate text
transformations applied to queries/passages must be declared in their ordered
preprocessing lists.

Only positive JSON integers are allowed for `dimensions` and `max_length`.
Booleans and decimal numbers such as `1024.0` are rejected. The payload has no
floating-point fields, avoiding `1`, `1.0`, and exponent-form ambiguities.
Preprocessing arrays are ordered pipelines; reordering or repeating operations
changes identity. Absent required fields and explicit `null` both fail
validation, rather than being defaulted.

The artifact digests are hashes over canonical manifests, not directories or
archives whose ordering can vary. `talos-artifact-manifest-v1` contains a
non-empty `files` array. Each entry has exactly `path` and `sha256`; paths are
normalized relative POSIX paths with no absolute paths, backslashes, empty,
`.` or `..` components. Duplicate paths (after NFC normalization) are
rejected. Entries are sorted by normalized path's UTF-8 bytes. The manifest is
serialized with the same JSON settings as the vector-space payload and its
UTF-8 bytes are hashed with SHA-256. The model and tokenizer manifests must
include all files and configuration that affect the effective loaded artifact;
the model manifest includes weights, architecture/configuration, pooling
modules, and any custom code loaded by the model provider. The tokenizer
manifest includes tokenizer vocabulary/merges, tokenizer configuration, and
special-token definitions. Symlinks are not manifest entries: producers must
resolve dependencies and include the bytes of each effective file under its
logical relative path. The validator cannot determine completeness of that
inventory automatically.

`query_preprocessing` and `passage_preprocessing` are ordered lists of stable
operation identifiers. The v2 registry currently defines:

| Operation ID | Normative meaning |
|---|---|
| `unicode-nfc-u15.0-v1` | Normalize input text to Unicode 15.0 Normalization Form C. |
| `strip-unicode-whitespace-u15.0-v1` | Remove leading/trailing code points in Unicode 15.0 `White_Space`: U+0009–U+000D, U+0020, U+0085, U+00A0, U+1680, U+2000–U+200A, U+2028–U+2029, U+202F, U+205F, and U+3000. |

Unknown operation identifiers fail validation. Any additional operation
requires a registry/spec update and fixture coverage before use. Registry
operations execute in listed order on the raw text. After preprocessing, the
exact model input is formed by literal concatenation:
`instruction + prefix + processed_text`; the fields include any desired
separators, and no implicit spaces/newlines are inserted. Tokenization follows
this concatenation. Truncation applies to the token sequence after tokenizer
special-token handling, with `max_length` counting all tokens supplied to the
model. An implementation must configure the declared truncation side.

`pooling` must use one of these registered definitions:

| Pooling ID | Normative meaning |
|---|---|
| `mean-attention-mask-v1` | Arithmetic mean of last-hidden-state token vectors whose attention-mask value is 1, including special tokens if the tokenizer marks them attended. |
| `cls-token-v1` | Last-hidden-state vector at sequence position 0. |
| `last-attended-token-v1` | Last-hidden-state vector at the greatest position whose attention-mask value is 1. |

`normalization = l2` means divide the pooled vector by its Euclidean L2 norm;
if the norm is exactly zero, leave the vector unchanged. `normalization = none`
means no post-pooling normalization. Pooling and normalization happen in that
order. Unknown pooling and normalization identifiers are rejected rather than
treated as free-form labels.

## Fields deliberately excluded from `vector_space_id`

The following are provenance/operational metadata, nested in the optional
`provenance` object, not compatibility fields:

- provider/package and framework versions;
- Python version, operating system, device, and accelerator;
- execution timestamp, hostname, batch size, and checkpoint path;
- runtime precision when it changes only numerical precision, not model
  weights or input/output transformations.

`provenance` may be omitted. If supplied, it must be an object containing
non-empty `provider_id`, `provider_version`, `python_version`, `device`, and
`precision`; it may additionally contain a string-to-string
`framework_versions` map, `generated_at`, and `hostname`. Null values and
unknown provenance keys are rejected. New provenance keys require a versioned
schema update, but do not enter the compatibility hash.

These fields remain useful for reproducing or diagnosing generation and should
be retained as provenance. A quantized or otherwise transformed model is not
merely a precision detail: its transformed model artifact must have a distinct
artifact digest and therefore a distinct vector-space identity.

Excluding a provider implementation does not assert bitwise equivalence among
all implementations. Any alternate provider must demonstrate that it loads the same pinned
model/tokenizer artifacts and implements the declared input, pooling,
normalization, and truncation semantics. Numerical parity tolerance is a
separate qualification test, not part of this offline identity validator; its
acceptance threshold remains unspecified and blocks production equivalence
claims.

## Identity calculation

1. Validate all required v2 fields and reject unknown fields.
2. Select exactly the compatibility fields listed above; exclude provenance.
3. Normalize all compatibility strings to Unicode 15.0 NFC; preserve
   preprocessing array order.
4. Serialize as UTF-8 JSON with lexicographically sorted object keys,
   separators `(',', ':')`, `ensure_ascii=false`, and non-finite JSON values
   disallowed.
5. Set `vector_space_id` to lowercase hexadecimal SHA-256 of those bytes.

Only strings, positive integers, and ordered string arrays occur in the
compatibility payload. No floats, nulls, or nested extension objects are
allowed there. Missing fields do not receive defaults.

The identifier is a compatibility key over declared and artifact-hashed
inputs. It is not proof that an external producer actually used those files.
Producer authenticity and execution provenance require separate evidence.

## Index policy

The initial policy is one declared vector space per notebook, with precedence:

- invalid query contract: `QUERY_INVALID` (terminal; index is not assessed);
- no vector records: `DENSE_NOT_CONFIGURED`;
- any malformed/unsupported index contract: `INDEX_INVALID`;
- more than one distinct identity in the notebook: `INDEX_MIXED`;
- otherwise, any record without a v2 identity: `INDEX_LEGACY`;
- one identity equal to the query identity: `DENSE_ACTIVE`;
- one identity different from the query identity: `DENSE_INCOMPATIBLE`.

Only `DENSE_ACTIVE` may authorize dense similarity. A legacy record is never
made compatible by matching its dimension or provider/model labels. If known
records establish multiple spaces, `INDEX_MIXED` takes precedence over legacy
entries, and the result reports the legacy count. `INDEX_INVALID` takes
precedence over `INDEX_MIXED`; invalid records prevent trusting the inventory.
An unsupported schema is invalid; absent identity and recognized v1 contracts
are legacy. `QUERY_INVALID` is terminal for that assessment and does not
authorize inspecting/comparing the index. Mixed spaces fail as a notebook
inventory even if one matches the query.
Lexical fallback policy and its user-visible status are outside this offline
validator.

## Existing v1 data

The existing `data/colab/embedding_contract.json` is v1 and does not pin
immutable model and tokenizer artifact identities. Existing SQLite rows only
store provider, model label, and dimension. They therefore have no v2
`vector_space_id` and must be classified as `INDEX_LEGACY` by a future strict
runtime until an explicitly reviewed migration establishes their identity.

No identity may be assigned to existing rows from dimensionality alone. This
draft does not select Qwen or E5 for query-time use, prove historical model
provenance, or authorize editing production databases.

## Offline validator and fixtures

The pure helper in
[`src/study_engine/diagnostics/vector_space_contract.py`](../src/study_engine/diagnostics/vector_space_contract.py)
has no runtime call sites. The fixture suite uses synthetic contracts and
identifiers only; digests in the fixture are illustrative and do not identify
real model artifacts.

Run it from the repository root:

```bash
./.venv/bin/python scripts/validate_vector_space_fixtures.py
./.venv/bin/python -m pytest tests/unit/diagnostics/test_vector_space_contract.py
./.venv/bin/python scripts/check_vector_space_reproducibility.py
```

The suite covers identical contracts, differing revisions, different models
with equal dimensions, Qwen/E5 mismatch, hash/Qwen equal dimensions, provenance
changes, missing legacy identity, mixed index spaces, and an unconfigured
index. Unit tests additionally cover every compatibility field, provenance
exclusion, unknown fields/operations, NFC equivalence, strict numeric/null
handling, manifest ordering/path validation, invalid-state precedence, and a
separate reference canonicalizer. `reference_vector_space_contract.py` is a
second standard-library implementation which does not import the implementation
under test. The reproducibility check compares vector-space IDs, artifact
manifest IDs, and assessment state/count fields for every fixture case. Its
human-readable error messages are intentionally not compared. Both
implementations are maintained in this repository, so this is an independent
implementation check, not an independent author review or production
certification. It does not open production SQLite files or load embedding
models.

## Not yet specified

- Which immutable model/tokenizer revisions and artifact manifests will anchor
  the current Qwen index.
- The evidence and approval required to migrate legacy rows.
- How runtime configuration selects an active contract and surfaces dense vs.
  lexical-only status.
- Numerical parity tolerances for alternate provider implementations.
- Whether any notebook needs multiple simultaneously active vector spaces.
