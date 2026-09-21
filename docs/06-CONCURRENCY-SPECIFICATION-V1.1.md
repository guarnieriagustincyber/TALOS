# 06-CONCURRENCY-SPECIFICATION-V1.1.md
## Formal Invariant Specification for Multi-Writer Evidence Persistence & Semantic Identity (INV-05)

**Version:** 1.1 (Final Frozen Edition — Post-SSA-0R-D Review)  
**Status:** FROZEN CONTRACT FOR REMEDIATION (SSA-0R-I)  
**Origin:** System Survival Audit SSA-0 (`FINDING-SSA0-01`) & Design Review SSA-0R-D  
**Target Subsystems:** `study_engine.state.ledger` (S5.2.B), `study_engine.state.ingestion_engine` (S5.2.A)  
**Applicability:** Universal across all operational modes (CLI, API, parallel test execution, multi-worker background runners)

---

## 1. The Core Architectural Invariants: Uniqueness, Completeness & Decision Function

The deduplication invariant is disaggregated into three strict mathematical properties:

### A. Strict Uniqueness
For any evaluation attempt $A$:
$$\forall A, \quad |\mathrm{Evidence}(\mathrm{evaluation\_attempt\_id} = A)| \le 1$$

### B. Admissibility Completeness
For any evaluation attempt $A$ that successfully completes admission verification:
$$\mathrm{admitted}(A) \implies |\mathrm{Evidence}(\mathrm{evaluation\_attempt\_id} = A)| = 1$$

### C. The Formal Decision Function $D(K, R)$
Idempotence cannot depend solely on the existence of the attempt key $K$. Accepting an existing key without verifying the evaluative result would silently bless an inconsistent re-evaluation.

The ingestion and ledger commit decision is governed strictly by the function:

$$D(K, R) = \begin{cases}
\mathbf{COMMIT\_OK} & \text{si } K \notin \mathrm{DB} \\
\mathbf{IDEMPOTENT\_ACK} & \text{si } K \in \mathrm{DB} \land R_{\text{incoming}} = R_{\text{stored}} \\
\mathbf{INCONSISTENT\_REPLAY} & \text{si } K \in \mathrm{DB} \land R_{\text{incoming}} \ne R_{\text{stored}}
\end{cases}$$

Where:
- $K = \langle \text{student\_id},\ \text{node\_id},\ \text{evaluation\_attempt\_id} \rangle$ (Primary Idempotency Key).
- $R = \text{assessment\_digest}$ (Canonical Cryptographic Content Digest of the evaluation outcome).

$$\text{Epistemic Rule: } \quad \mathbf{\text{Idempotencia} \equiv \text{Mismo Intento } (K) \ \land \ \text{Mismo Resultado Canónico } (R)}$$

---

## 2. The 3-Tier Identity Hierarchy

A fatal design flaw identified during SSA-0R-D was conflating evaluation content (`assessment_digest`) with attempt identity (`evaluation_attempt_id`). Because `AssessmentResult` includes `assessed_at` (a UTC timestamp), a network timeout followed by a technical retry at $T+2\text{s}$ would generate a divergent digest, bypassing naive digest-based uniqueness constraints and creating phantom duplicates.

To prevent this, identity is formally partitioned into three distinct levels:

```text
                  STUDENT SUBMISSION
                  (submission_id)
                         │
                         ▼
              EVALUATION ATTEMPT
           (evaluation_attempt_id)
                         │
                         ▼
              ASSESSMENT RESULT DIGEST
                (assessment_digest)
```

### Level 1: Submission Identity (`submission_id`)
* **Definition:** Uniquely identifies **what work or artifact was produced by the student** (e.g. code commit hash, lab container output archive, or explanation text payload).
* **Stability:** Stable across all evaluation attempts, re-runs, and retries.
* **Cardinality:** A single `submission_id` may legitimately have multiple evaluation attempts if the student re-submits or if multiple distinct rubrics evaluate the same work.

### Level 2: Evaluation Attempt Identity (`evaluation_attempt_id`)
* **Definition:** Uniquely identifies **a specific execution attempt of evaluating a submission** against a curriculum node.
* **Stability:** **MUST REMAIN STABLE ACROSS RETRIES.** If a worker times out, crashes, or re-attempts commit due to lost network connection, the retry payload MUST carry the original `evaluation_attempt_id`.
* **Primary Unique Constraint:** Governs physical storage deduplication:
  $$\mathbf{UNIQUE}(\text{student\_id}, \text{node\_id}, \text{evaluation\_attempt\_id})$$

### Level 3: Assessment Result Digest (`assessment_digest`)
* **Definition:** Cryptographic SHA-256 digest of the evaluative output produced by the evaluation engine ($S9$).
* **Role:** Integrity verification and audit provenance. It validates that the content committed matches the evaluative facts and instrumental facts.
* **Relationship to Identity:** `assessment_digest` atavistically attests *what verdict was rendered*; `evaluation_attempt_id` attests *which attempt rendered it*.

### Summary Table of Semantic Roles:
| Identifier | Governs | Survives Retries? | Uniqueness Scope |
| :--- | :--- | :---: | :--- |
| **`submission_id`** | Student's source work | Yes | Global student submission |
| **`evaluation_attempt_id`** | **Deduplication, Idempotency, Concurrency** | **Yes (Mandatory)** | **Storage constraint `UNIQUE`** |
| **`assessment_digest`** | Epistemic Integrity & Consistency Check | No (varies if re-evaluated) | Cryptographic verification & $R_{\text{stored}}$ check |
| **`assessed_at`** | Audit Trail / Historical Timestamp | No | Descriptive Telemetry ONLY |

> [!IMPORTANT]
> **Architectural Rule:** `assessed_at` is strictly a descriptive audit timestamp. It MUST NOT participate in deduplication identity. Passing time between retries does not mint a new evaluation attempt.

---

## 3. Physical Storage Architecture: SQLite WAL as Authoritative Source of Truth

The persistence architecture is established around a decoupled, authoritative transactional model:

```text
               Worker A               Worker B
                  │                      │
                  └──────────┬───────────┘
                             ▼
                    SQLite Transaction
                (BEGIN IMMEDIATE; in C)
                             │
            UNIQUE(student_id, node_id, evaluation_attempt_id)
                             │
                     ┌───────┴───────┐
                     │               │
                  INSERT          CONFLICT
                     │               │
                     │      Verify R_incoming == R_stored?
                     │       ├── YES: IDEMPOTENT_ACK
                     │       └── NO:  INCONSISTENT_REPLAY (Fail-Closed)
                     ▼
             AUTHORITATIVE LEDGER
            (evidence_ledger.db)
                     │
                     ├── entry_index
                     ├── parent_hash
                     ├── entry_hash
                     ├── evaluation_attempt_id
                     ├── assessment_digest
                     └── payload_json
                             │
                             ▼
                      JSONL EXPORT
                  (Derived Audit View)
```

### A. Authoritative Source vs Derived View
1. **SQLite (`evidence_ledger.db`):** The **sole authoritative source of truth**. All writes, index assignments, parent hash linking, and uniqueness checks happen inside atomic SQLite transactions.
2. **JSONL File (`evidence_ledger.jsonl`):** A **derived, regenerable projection / audit export**.
   - No distributed transactions between SQLite and JSONL are attempted.
   - If a crash occurs after SQLite commits, the JSONL export can be deterministically regenerated from SQLite at any time via `EvidenceLedger.export_jsonl()`.

### B. Elimination of Python TOCTOU Races & Inconsistency Defense
* **Strict Prohibition:** Code in Python MUST NOT execute `SELECT ... if not exists ... INSERT`.
* **Atomic Storage Decision:** Uniqueness enforcement is delegated completely to the SQLite C-engine via:
  ```sql
  BEGIN IMMEDIATE;
  INSERT INTO evidence_ledger (
      entry_index, record_id, student_id, node_id, evaluation_attempt_id,
      assessment_digest, payload_json, parent_entry_hash, entry_hash, committed_at
  ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
  ```
* **Conflict Handling in Python:**
  If SQLite raises `sqlite3.IntegrityError` on the `UNIQUE(student_id, node_id, evaluation_attempt_id)` constraint:
  1. The engine reads the existing committed record for that $K$.
  2. If `existing.assessment_digest == incoming.assessment_digest`:
     - Cleanly returns `AdmissionDecision.IDEMPOTENT_ACK`.
     - Preserves existing entry without state or ledger mutation.
  3. If `existing.assessment_digest != incoming.assessment_digest`:
     - Raises `InconsistentReplayError` (or fail-closed conflict).
     - Returns `AdmissionDecision.INCONSISTENT_REPLAY`.
     - **Strictly refuses to overwrite or silently bless divergent evaluative results under the same attempt ID.**

---

## 4. Crash Consistency & Ambiguous Crash Window Semantics

The recovery model explicitly handles three distinct temporal windows:

```text
[ Pre-Commit Window ] ──────> [ Atomic Commit ] ──────> [ Ambiguous ACK Window ]
       │                              │                            │
  Worker dies                    SQLite commits               Worker dies after commit
  before commit                  authoritatively              before caller receives ACK
       │                              │                            │
       ▼                              ▼                            ▼
  0 records in DB               1 record in DB               On retry: UNIQUE conflict
  (Clean state)                 (Monotonic state)            -> Evaluates D(K, R):
                                                                R_in == R_db -> IDEMPOTENT_ACK
                                                                R_in != R_db -> INCONSISTENT_REPLAY
```

1. **Pre-Commit Crash:** If worker dies or crashes prior to SQLite `COMMIT`, the transaction rolls back cleanly via SQLite WAL journal. Zero dirty entries exist.
2. **Post-Commit Success:** Exactly 1 record is committed, indexed, and chained.
3. **Ambiguous ACK Window:** If a worker dies or network terminates *after* SQLite commits but *before* the caller receives confirmation:
   - On retry, the worker submits the identical $K = (\text{student\_id}, \text{node\_id}, \text{evaluation\_attempt\_id})$.
   - SQLite immediately rejects the insert with a `UNIQUE` constraint conflict.
   - The engine evaluates $D(K, R)$:
     - If $R_{\text{incoming}} == R_{\text{stored}} \implies \mathbf{IDEMPOTENT\_ACK}$ (cardinality remains 1).
     - If $R_{\text{incoming}} \ne R_{\text{stored}} \implies \mathbf{INCONSISTENT\_REPLAY}$ (rejection, fail-closed).

---

## 5. Scope Matrix: Required Concurrency Dimensions

The implementation in `SSA-0R-I` MUST satisfy the invariant across all four scopes:

| Scope | Execution Context | Mechanism of Protection |
| :--- | :--- | :--- |
| **Scope 1: Threads** | Multiple threads sharing the same process and ledger instance | SQLite connection pool / `BEGIN IMMEDIATE` serialization |
| **Scope 2: Instances** | Multiple `EvidenceLedger` instances in the same process pointing to same DB | SQLite file lock / WAL mode atomic coordination |
| **Scope 3: Processes** | Multiple independent OS processes (pytest workers, Celery, API workers) | SQLite inter-process WAL locking |
| **Scope 4: Restart** | Process kill, abnormal termination, crash followed by restart | SQLite WAL recovery + `D(K, R)` decision function |

---

## 6. Formal Acceptance Criteria for SSA-0R (Re-Audit)

Prior to declaring SSA-0R closed, the remediation implementation must **simultaneously satisfy all 7 mandatory conditions**:

1. **`INV-05` under Threads (Scope 1):** 10, 50, and 100 concurrent threads submitting identical $(K, R) \to$ exactly 1 persisted record, $N-1$ `IDEMPOTENT_ACK`, 0 chain corruptions.
2. **`INV-05` under Multiple Instances (Scope 2):** Independent instances concurrently committing to same DB $\to$ exactly 1 persisted record, clean subsequent reload.
3. **`INV-05` under Multiple Processes (Scope 3):** 4+ OS worker processes concurrently committing $\to$ exactly 1 persisted record, clean subsequent reload.
4. **`INV-05` under Ambiguous Crash Window (Scope 4):**
   - Post-commit crash + retry with same $(K, R) \implies \mathbf{IDEMPOTENT\_ACK}$ and $|\mathrm{Evidence}(K)| = 1$.
   - Post-commit crash + retry with same $K$ but divergent $R' \implies \mathbf{INCONSISTENT\_REPLAY}$ (strictly rejected, fail-closed).
5. **Differential Oracle 4-Way Truth Table Verification:**
   An independent external oracle verifies:
   | Input Tuple | Expected Architectural Outcome |
   | :--- | :--- |
   | Initial $(K_1, R_1)$ | `COMMIT_OK` ($|\mathrm{Evidence}(K_1)| = 1$) |
   | Replay $(K_1, R_1)$ (Identical result) | `IDEMPOTENT_ACK` ($|\mathrm{Evidence}(K_1)| = 1$) |
   | Replay $(K_1, R_2)$ (Divergent result) | `INCONSISTENT_REPLAY` ($|\mathrm{Evidence}(K_1)| = 1$) |
   | New Attempt $(K_2, R_2)$ | `COMMIT_OK` ($|\mathrm{Evidence}(K_2)| = 1$) |
6. **Zero Regression on Invariants 01–04 and 06–10:** All other 9 invariants remain 100% `CONTAINED`.
7. **Clean Full-Suite Accounting:**
   $$\text{1.302 collectable} \land \text{1.302 executed} \land \text{1.302 PASS} \land \text{0 XFAIL} \land \text{0 FAIL} \land \text{0 SKIP} \land \text{0 NO EXEC}$$
