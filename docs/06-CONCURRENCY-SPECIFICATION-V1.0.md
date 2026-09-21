# 06-CONCURRENCY-SPECIFICATION-V1.0.md
## Formal Invariant Specification for Multi-Writer Evidence Persistence (INV-05)

**Status:** FROZEN SPECIFICATION FOR POST-SSA-0 REMEDIATION  
**Origin:** System Survival Audit SSA-0 (`FINDING-SSA0-01`)  
**Target Subsystems:** `study_engine.state.ledger` (S5.2.B), `study_engine.state.ingestion_engine` (S5.2.A)  
**Applicability:** Universal across all operational modes (CLI, API, parallel test execution, multi-worker background runners)

---

## 1. The Core Architectural Invariant

For any valid evidence semantic identity tuple $K$ submitted concurrently $N$ times:

$$\forall \text{ concurrent submissions of } K: \quad \mathrm{cardinality}(\mathrm{persisted\_semantic\_evidence}) = 1$$

### Operational Invariant Properties:
1. **At-Most-Once Persistence:** Exactly one submission successfully writes to the permanent ledger.
2. **Deterministic Convergence of Replicas:** All $N-1$ concurrent or subsequent submissions converge to a deterministic rejection or idempotent acknowledgment (`DUPLICATE_REJECTED`, `IDEMPOTENT_PASS`, or `RACE_LOST`).
3. **Structural Chain Continuity:** Under no circumstance may concurrent execution produce non-sequential `entry_index` values, duplicate entry hashes, or genesis parent hash collisions.
4. **Deterministic Reconstruction:** State projection via `derive_student_state()` from the reconstructed ledger after concurrent submissions must yield identical canonical state hashes regardless of commit order.

---

## 2. Decomposition of the Semantic Identity Tuple ($K$)

A critical finding of SSA-0 is that uniqueness must be enforced upon **semantic identity**, not purely physical record slugs. If two submissions generate distinct random `record_id` strings for the same evaluation, enforcing uniqueness on `record_id` alone fails to prevent duplicate semantic evidence.

### A. The Authority-Bearing Semantic Identity Tuple ($K_{\text{semantic}}$)
The semantic uniqueness of an evaluation attempt is strictly defined by:
$$K_{\text{semantic}} = \langle \text{student\_id}, \text{node\_id}, \text{competency\_id}, \text{evidence\_type}, \text{assessment\_digest}, \text{authority\_id}, \text{roadmap\_revision\_id}, \text{policy\_revision\_id} \rangle$$

Where:
- `assessment_digest` is the canonical SHA-256 hash of the admitted `AssessmentResult` (including observation refs, evaluative facts, and aggregation).
- For direct manual overrides lacking an assessment digest, the identity falls back to $\langle \text{student\_id}, \text{node\_id}, \text{evidence\_type}, \text{timestamp} \rangle$.

### B. Separation of Identity from Metadata
| Field Category | Specific Fields | Role in Uniqueness Enforcement |
| :--- | :--- | :--- |
| **Semantic Identity ($K$)** | `student_id`, `node_id`, `assessment_digest`, `authority_id` | **MANDATORY UNIQUE KEY.** Governs deduplication in Gate 4 and storage uniqueness constraint. |
| **Operational Identifiers** | `record_id`, `timestamp` (event time), `committed_at` (ledger clock) | System lineage and chronological ordering. A divergent `record_id` must NOT bypass deduplication if $K_{\text{semantic}}$ matches. |
| **Non-Authoritative Metadata** | `metadata: dict` (lab metrics, timings, UI trace) | Opaque payload. Changes to metadata across concurrent submissions must NOT create duplicate evidence entries. |

$$\text{Guarantee: } \quad \mathbf{\text{"exactly one physical record"} \equiv \text{"exactly one semantic evidence"}}$$

---

## 3. Invariant Scope Matrix

The concurrency invariant MUST hold across all four operational dimensions:

```
+-------------------------------------------------------------------------+
|                  INV-05 CONCURRENCY ENFORCEMENT SCOPES                  |
+-------------------+-----------------------------------------------------+
| Scope 1: Threads  | Multiple threads in the same Python process sharing |
|                   | the same EvidenceLedger instance.                   |
+-------------------+-----------------------------------------------------+
| Scope 2: Instances| Multiple EvidenceLedger instances in the same       |
|                   | process accessing the same underlying file/store.   |
+-------------------+-----------------------------------------------------+
| Scope 3: Processes| Multiple independent OS processes (e.g., Celery,   |
|                   | gunicorn, pytest-xdist) accessing the same store.   |
+-------------------+-----------------------------------------------------+
| Scope 4: Restart  | Interrupted writes, process kill, or crash followed |
|                   | by restart cleanly reloads or re-establishes state. |
+-------------------+-----------------------------------------------------+
```

---

## 4. Disaggregation: Decision vs Persistence Outcome

An implementation is architecturally valid if and only if both the decision and the persistence requirements are met:

| Outcome Dimension | Requirement | Permitted Implementations | Forbidden Behaviors |
| :--- | :--- | :--- | :--- |
| **Decision Outcome** | Preflight Gate 4 or Ledger commit must classify concurrent submissions cleanly. | `1 ADMITTED`, `N-1 DUPLICATE_REJECTED`<br>— OR —<br>`1 ADMITTED`, `N-1 IDEMPOTENT_ACK` | Multiple submissions receiving `ADMITTED` without mutual exclusion. |
| **Persistence Outcome** | Permanent storage must contain exactly 1 entry for the identity tuple $K$. | Append protected by OS-level file lock (`fcntl.flock`)<br>— OR —<br>Transactional ACID table (`SQLite` with `UNIQUE(student_id, node_id, assessment_digest)` constraint). | Multiple raw lines written with identical semantic identity. |
| **Chain Integrity** | `entry_index` is strictly monotonic $(0, 1, 2, \dots, M-1)$. `parent_entry_hash` links strictly to entry $i-1$. | Mutex over index assignment, parent hash fetch, write, and fsync. | Resetting `entry_index=0` or parent hash to `_GENESIS_HASH` from uncoordinated instances. |

---

## 5. Evaluation of Technical Remediation Strategies (For Future Phase)

| Strategy | Scope 1 (Threads) | Scope 2 (Instances) | Scope 3 (Processes) | Scope 4 (Restart) | Assessment |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **A. `threading.RLock` only** | ✅ Solves | ❌ Fails | ❌ Fails | ❌ Irrelevant | **INSUFFICIENT.** Only covers Scope 1. Does not protect separate instances or OS processes. |
| **B. `fcntl.flock` around JSONL file** | ✅ Solves | ✅ Solves | ✅ Solves | ⚠️ Partial | **VIABLE FOR FILE LEDGER.** Protects across processes on POSIX, but requires atomic index sync and file reload on lock acquisition. |
| **C. SQLite Transactional Ledger** | ✅ Solves | ✅ Solves | ✅ Solves | ✅ Solves | **HIGHLY RESILIENT ARCHITECTURE.** Leverages SQLite WAL mode, atomic `BEGIN IMMEDIATE`, and database-enforced `UNIQUE` constraints on $K_{\text{semantic}}$. Eliminates in-memory set race conditions permanently. |
| **D. Lock + In-Memory Cache Sync** | ✅ Solves | ✅ Solves | ❌ Fails | ⚠️ Partial | **INSUFFICIENT.** In-memory sets cannot be reliably synced across processes without IPC. |

---

## 6. Formal Acceptance Criteria for SSA-0R (Re-Audit)

Prior to issuing final system ratification in SSA-0R, the candidate remediation implementation must **simultaneously satisfy all 7 mandatory conditions**:

1. **`INV-05` satisfied under threads (Scope 1):** Tested with 10, 50, and 100 concurrent worker threads submitting identical $K \to$ exactly 1 persisted record, 0 chain corruptions.
2. **`INV-05` satisfied under multiple instances (Scope 2):** Tested with separate `EvidenceLedger` instances concurrently committing to the same store $\to$ exactly 1 persisted record, subsequent reloads strictly valid.
3. **`INV-05` satisfied under multiple OS processes (Scope 3):** Tested with 4+ independent OS worker processes committing concurrently $\to$ exactly 1 persisted record, subsequent reloads strictly valid.
4. **`INV-05` satisfied after restart (Scope 4):** Ledger state across restarts preserves complete integrity and monotonic indexing.
5. **Independent Differential Oracle Verification:** An independent oracle confirms `cardinality(persisted_semantic_evidence) == 1` for all concurrent submission batches.
6. **Zero Regression on Invariants 01–04 and 06–10:** All other 9 survival invariants remain 100% `CONTAINED` without behavioral drift.
7. **Clean Full-Suite Accounting:**
   - **Collected:** `1,302`
   - **Executed:** `1,302`
   - **PASS:** `1,302`
   - **EXPECTED XFAIL:** `0` (the 3 current XFAILs transition cleanly to PASS)
   - **UNEXPECTED FAIL:** `0`
   - **SKIP:** `0`
   - **NOT EXECUTED:** `0`.
