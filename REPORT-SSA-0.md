# SYSTEM SURVIVAL AUDIT 0 (SSA-0)
## Forensic Adversarial Verification & Boundary Survival Report (Final Closure Edition)

**Date:** 2026-09-05  
**Audit Protocol:** `READ-ONLY / RED TEAM / NO PATCH`  
**Target Codebase:** Study Engine (`src/study_engine/`)  
**Historical Certification Baseline (S4.4 / P1–P4):** `e3fc4422665a778bdcce302f2a760c3e5c82a056` (1,271 tests pass)  
**SSA-0 Input Baseline:** `e3fc4422665a778bdcce302f2a760c3e5c82a056` (Tree SHA: `07dfd330bdcb04d909325f9f0fcac8dd68ffad3a`, 118 source files)  
**Source Modifications:** **0 lines changed** (`git diff HEAD -- src/study_engine/` is completely EMPTY)  

---

## 1. Master Survival Verdict & Status

$$\mathbf{Master\ Survival\ Verdict:\ PROVISIONALLY\ VALID\ (SURVIVES\ WITH\ FINDINGS)}$$
$$\mathbf{Global\ Closure\ Status:\ NOT\ YET\ RATIFIED}$$

```text
SSA-0 AUDIT DISPOSITION
├── Architectural finding quality: HIGH
├── Real defect discovered:       YES (FINDING-SSA0-01)
├── Read-only source integrity:   PRESERVED (0 lines modified in src/study_engine/)
├── Epistemic containment:        STRONG (9/10 Invariants contained)
├── Concurrency specification:    FROZEN (docs/06-CONCURRENCY-SPECIFICATION-V1.0.md)
├── State hash seal coverage:     PROVEN (20/20 fields sealed, 100% tamper detection)
└── Global closure:               NOT YET RATIFIED (Pending controlled remediation in SSA-0R)
```

---

## 2. Test Execution & Auditability Matrix

To eliminate any ambiguity between collectable tests and executed tests, the entire test suite was executed end-to-end:

| Metric | Full Suite Value | SSA-0 Hostile Suite | Baseline Suite |
| :--- | :---: | :---: | :---: |
| **Tests Collectables** | **1,302** | 31 | 1,271 |
| **Tests Executed** | **1,302** | 31 | 1,271 |
| **PASS** | **1,299** | 28 | 1,271 |
| **EXPECTED XFAIL (Defect Verified)** | **3** | 3 | 0 |
| **UNEXPECTED FAIL** | **0** | 0 | 0 |
| **SKIP** | **0** | 0 | 0 |
| **NOT EXECUTED** | **0** | 0 | 0 |
| **Execution Duration** | **67.93 s** | 0.55 s | 67.38 s |

> [!NOTE]
> **Auditability Guarantee:** The repository is **not** declared "100% green" in the conventional sense. The presence of `3 XFAIL` entries in `tests/survival/test_l5_concurrency_and_crash.py` constitutes the deliberate, permanent empirical proof of the concurrency race condition under the read-only audit policy.

---

## 3. Original Invariants Verification Matrix (1-to-1 Mapping)

In strict alignment with the original approved SSA-0 implementation plan, the 10 fundamental survival invariants are tracked without renaming or absorption:

| Invariant ID | Plan Definition | Tested Layer & Assets | Empirical Status | Audit Taxonomy Class |
| :--- | :--- | :--- | :---: | :---: |
| **INV-01** | `NO UNCONTAINED STATE TRANSITION` | L3 (Shortcuts 1, 3, 7), L6 (Chaos Oracle, 20 seeds / 1000 events) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-02** | `NO UNAUTHORIZED EVIDENCE` | L3 (Shortcut 6: corrupted digest), L1.3 (Authority ID checks) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-03** | `NO CROSS-STUDENT CONTAMINATION` | L4.1 (`test_l4_1_cross_student_evidence_contamination`) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-04** | `NO CURRICULAR BYPASS` | L3 (Shortcut 7: locked node progress blocked despite PASS) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-05** | `NO REPLAY DUPLICATION` | L5.1 (Sequential vs Multi-thread/Instance/Process Replay) | **BROKEN (Concurrent)**<br>**CONTAINED (Sequential)** | `CONFIRMED_DEFECT`<br>(FINDING-SSA0-01) |
| **INV-06** | `NO UNKNOWN -> FAIL COLLAPSE` | L2.1 (Truncation), L2.2 (Omission vs Verified Absence) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-07** | `NO GENERATED -> EVIDENCE LAUNDERING` | L3 (Shortcut 8: raw LLM generated text rejected as evidence) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-08** | `NO AUDIT / CONTEXT DIVERGENCE` | L4.4 (Task/Rubric hash mismatch), L4.2 (Temporal session bounds) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-09** | `NO CRASH-INDUCED PHANTOM STATE` | L5.2 (Pre-ledger clean state; Post-ledger deterministic replay) | **CONTAINED** | `CONFIRMED_PASS` |
| **INV-10** | `NO UNAUTHORIZED AUTHORITY PATH` | L1.1 (AST sovereignty of `EvidenceRecord`), L1.3 (Ontological roles) | **CONTAINED** | `CONFIRMED_PASS`* |

*\*See Section 6 for the epistemological limitation of static AST analysis.*

---

## 4. Deep Dive: Expanded Concurrency Scope (FINDING-SSA0-01)

### The Core Invariant
The survival invariant for deduplication is defined at the persistence level:
$$\forall \text{ concurrent submissions of same identity tuple: } \mathrm{cardinality}(\mathrm{persisted\_semantic\_evidence}) = 1$$

Empirical testing revealed that this invariant is violated across **three distinct concurrency scopes**:

```
CONCURRENCY SCOPE BREAKDOWN
├── Scope A: Same Instance / Multi-Thread
│   └── Race condition: check (L193) vs mutate (L251) during GIL release (fsync).
├── Scope B: Separate Instances / Same Process
│   └── Broken deduplication: self._seen_record_ids is instance-local memory.
└── Scope C: Separate OS Processes
    └── Broken deduplication & file corruption: zero IPC locking (no fcntl.flock).
```

### Empirical Evidence by Scope:

1. **Scope A: Same Instance / Multi-Thread (Test L5.1):**
   - **10 concurrent threads:** 10 admitted, 0 rejected $\to$ **10 duplicate records persisted** to file.
   - **50 concurrent threads:** 50 admitted, 0 rejected $\to$ **50 duplicate records persisted** to file.
   - **100 concurrent threads:** 36 admitted, 64 rejected $\to$ **36 duplicate records persisted** to file.
   - *Root Cause:* In `src/study_engine/state/ledger.py:193-251`, `EvidenceLedger` lacks a `threading.RLock`. During file writing and `os.fsync(f.fileno())`, Python releases the GIL. Multiple threads evaluate `if record.record_id in self._seen_record_ids:` simultaneously before any thread reaches `self._seen_record_ids.add(...)`.

2. **Scope B: Separate Instances / Same Process (`test_concurrency_scope.py`):**
   - Two `EvidenceLedger` instances initialized pointing to the same file path before committing.
   - Instance 1 commits $\to$ succeeds (`entry_index=0`, `parent_entry_hash=GENESIS`).
   - Instance 2 commits identical record $\to$ succeeds (`entry_index=0`, `parent_entry_hash=GENESIS`).
   - **Result:** File contains 2 duplicate lines. Subsequent reload fails with:
     `LedgerIntegrityViolationError: Non-sequential entry_index 0 (expected 1) at line 2.`

3. **Scope C: Separate OS Processes (`test_concurrency_scope.py`):**
   - 4 worker processes spawned concurrently writing to the same ledger file.
   - All 4 worker processes commit successfully (`entry_index=0`).
   - **Result:** File contains 4 duplicate lines. Subsequent reload fails with hash chain violation.

### Decision Outcome vs Persistence Outcome:
| Scenario | Threads/Workers | Decision Outcome (Gate 4) | Persistence Outcome (Ledger File) | Invariant Status |
| :--- | :---: | :---: | :---: | :---: |
| **Sequential Replay** | 10 seq | 1 ADMITTED, 9 DUPLICATE_REJECTED | **1 entry persisted** | **CONTAINED** |
| **Scope A (Multi-Thread)** | 50 threads | 50 ADMITTED, 0 REJECTED | **50 entries persisted** | **BROKEN** |
| **Scope B (Separate Instances)**| 2 instances | 2 ADMITTED, 0 REJECTED | **2 entries persisted (corrupted)**| **BROKEN** |
| **Scope C (Multi-Process)** | 4 processes | 4 ADMITTED, 0 REJECTED | **4 entries persisted (corrupted)**| **BROKEN** |

---

## 5. Impact Propagation Analysis: Shallow Immutability (FINDING-SSA0-02)

Pydantic's `ConfigDict(frozen=True)` prevents top-level attribute reassignment on `EvidenceRecord` and `AdmissionTrace`, but does not recursively freeze nested dictionaries (`metadata`, `details`).

An empirical impact propagation test ([`verify_immutability_impact_propagation.py`](file:///media/agustin/Laboratorio/study-engie/scripts/survival/verify_immutability_impact_propagation.py)) was executed:

```
record.metadata["tampered_injected"] = "malicious_payload"
record.metadata["original_key"] = "corrupted_val"
```

### Propagation Tracing:
1. **Impact on Cryptographic Verification (`ledger.verify_integrity()`):**
   - **DETECTED.** Because `canonicalize_ledger_entry_payload` includes `"metadata": dict(sorted(record.metadata.items()))`, mutating metadata in memory causes `recomputed_hash != entry.entry_hash`.
   - `verify_integrity()` immediately shifts from `VALID` to `HASH_CHAIN_BROKEN` (`Tampered content at index 0: declared ... != computed ...`).
2. **Impact on Disk Persistence:**
   - **NONE.** The on-disk file was serialized during `append_record()`. In-memory mutations post-commit do not alter on-disk bytes.
3. **Impact on Student Progression (`derive_student_state()`):**
   - **NONE.** `policy_engine.py` evaluates criteria based strictly on first-class fields (`outcome`, `score`, `evidence_type`, `actor_type`, `verifier_id`). Metadata is not consumed for progression rules. The student state progress remains `ASSESSED_PROFICIENT`.
4. **Classification:**
   - **`DESIGN_GAP`**. The vulnerability causes in-memory cryptographic verification divergence, but does **not** allow an attacker to forge student progression or bypass policy gates.

---

## 6. Epistemological Boundaries & Methodological Limitations

### A. AST Sovereignty Boundary (L1.1 / INV-10)
- The AST audit (`test_l1_ast_and_immutability.py`) proved that across all 118 source files, only `src/study_engine/state/ingestion_engine.py` contains the syntax pattern `Call(func=Name(id='EvidenceRecord'))`.
- **Epistemological Limitation:** Static AST parsing detects direct syntactic construction. It does **not** preclude dynamic construction via reflection (`getattr(module, 'EvidenceRecord')`), indirect factory functions, or runtime monkeypatching. Absolute sovereignty requires runtime instrumentation (`sys.settrace` or sealed module loader).

### B. Chaos Curriculum & Differential Oracle Multi-Seed Characterization (L6 / INV-01)
- Initial testing with a single seed ($N=50$ events) showed 100% parity.
- Extended testing across 20 distinct seeds ($N=1,000$ events) via [`verify_multi_seed_chaos.py`](file:///media/agustin/Laboratorio/study-engie/scripts/survival/verify_multi_seed_chaos.py) revealed:
  1. **Oracle Independence:** The reference oracle imports zero code or constants from S5.2.C.
  2. **Parameter Sensitivity:** When the policy's `regression_threshold_failures` was configured at default (2) while the oracle assumed 1, differential mismatches emerged on regression steps. When parameters were explicitly aligned (`regression_threshold_failures=1`), the oracle and S5 StateEngine achieved **1,000 / 1,000 exact state projection matches (100.0% parity)**.

---

## 7. Audit of StudentState Canonical Hash Coverage

To ensure that no authority-bearing field was accidentally omitted from `canonicalize_student_state_payload`, an exhaustive field-level mutation audit was executed ([`verify_state_hash_coverage.py`](file:///media/agustin/Laboratorio/study-engie/scripts/survival/verify_state_hash_coverage.py)):

| Field Hierarchy | Specific Fields Audited | Fields Tested | Tamper Detected | Coverage |
| :--- | :--- | :---: | :---: | :---: |
| **Top-Level `StudentState`** | `student_id`, `roadmap_revision_id`, `policy_revision_id`, `ledger_cutoff_hash`, `as_of_time`, `cutoff_mode` | 6 | 6 | **100.0%** |
| **`NodeState`** | `node_id`, `status`, `unfulfilled_hard_prerequisites`, `unfulfilled_soft_prerequisites`, `total_evidence_count`, `last_event_timestamp`, `last_commit_timestamp` | 7 | 7 | **100.0%** |
| **`CriteriaEvaluationResult`** | `criteria_id`, `verdict`, `satisfied_requirements`, `missing_requirements`, `subsequent_failures_count`, `evaluation_timestamp`, `rationale` | 7 | 7 | **100.0%** |
| **TOTAL** | **All authority-bearing & operational fields** | **20** | **20** | **100.0%** |

> **Conclusion:** Every authority-bearing and operational field of `StudentState` is strictly incorporated into the canonical hash calculation. Modifying any single field immediately causes `validate_student_state_hash()` to fail with `StateHashMismatchError`. No field is silently ignored.

---

## 8. Formal Concurrency Requirement Frozen for Remediation

In order to prevent superficial fixes (such as applying an in-memory lock that only addresses single-process threads), the formal concurrency requirement has been frozen in:
[`docs/06-CONCURRENCY-SPECIFICATION-V1.0.md`](file:///media/agustin/Laboratorio/study-engie/docs/06-CONCURRENCY-SPECIFICATION-V1.0.md)

### The Architectural Specification Mandate:
$$\forall \text{ valid identity tuple } K: \quad \mathrm{cardinality}(\mathrm{persisted\_semantic\_evidence}) = 1$$
$$\text{MUST HOLD ACROSS: } \quad \text{threads} \land \text{instances} \land \text{processes} \land \text{restart}$$

Future remediation must eliminate the reliance on the in-memory set `_seen_record_ids` as the source of truth, transitioning persistence to an atomic locking mechanism (`fcntl.flock`) or an ACID transactional store (e.g. SQLite WAL mode with unique constraints).

---

## 9. Catalog of Unverified Surfaces (`UNVERIFIED`)

In accordance with strict audit taxonomy, the following areas were **not** proven by SSA-0 and must remain classified as `UNVERIFIED`:

| Surface | Classification | Reason / Scope Not Covered |
| :--- | :---: | :--- |
| **Multi-Process Concurrency** | `UNVERIFIED` | Safe concurrent access across independent OS processes requires file/process locking (`fcntl.flock` / database transactions) not yet implemented. |
| **Physical Torn Writes / Power Loss** | `UNVERIFIED` | Crash simulation tested logical boundaries (pre-ledger, post-ledger). Mid-write byte truncation during `os.fsync` was not subjected to block-level fault injection. |
| **Real OS SIGKILL Recovery** | `UNVERIFIED` | Tests simulated Python-level exceptions; abnormal OS termination via `kill -9` during active disk write was not executed in sandbox. |
| **Filesystem Exhaustion (ENOSPC)** | `UNVERIFIED` | Behavior under full disk during `f.write()` or `os.fsync()` was not tested. |
| **Dynamic Runtime Reflection** | `UNVERIFIED` | AST verifies static code; runtime reflection bypasses were not dynamically trapped. |

---

## 10. Summary of Architectural Findings

| Finding ID | Classification | Component | Severity | Description |
| :--- | :---: | :--- | :---: | :--- |
| **FINDING-SSA0-01** | `CONFIRMED_DEFECT` | `study_engine.state.ledger.EvidenceLedger` | **HIGH** | TOCTOU concurrency race (missing mutex and file lock) allows duplicate evidence commits across threads, instances, and processes. |
| **FINDING-SSA0-02** | `DESIGN_GAP` | `state_contracts.EvidenceRecord.metadata` | **MEDIUM** | Shallow immutability on frozen models permits in-place dict mutation, causing in-memory ledger hash verification divergence. |
| **FINDING-SSA0-03** | `DESIGN_GAP` | `contracts.student_state.StudentState` | **LOW** | Legacy mutable model coexists with sealed modern model, creating ontological duality. |
| **FINDING-SSA0-04** | `DOCUMENTATION_GAP` | `verify_l0_baseline.py` | **LOW** | Separation of `BASELINE_MATCH` from `TRUST_ROOT_UNVERIFIED` formalized. |

---

## 11. Final Forensic Disposition & SSA-0R Roadmap

SSA-0 is concluded and established as **`PROVISIONALLY_VALID (SURVIVES_WITH_FINDINGS)`**.

### Definitive Roadmap to System Ratification:
1. **Freeze SSA-0 Artifacts:** Commit audit scripts, tests, data, and specifications under audit tag.
2. **Open Remediation Workstream (S5/S6):** Design and implement the transactional/locked ledger satisfying `docs/06-CONCURRENCY-SPECIFICATION-V1.0.md` under a new commit.
3. **Execute SSA-0R (Re-Audit):**
   - Re-run the full hostile concurrency suite across threads, instances, and processes.
   - Prove that all 3 `XFAIL` tests transition cleanly to `PASS`.
   - Re-verify that the other 9 invariants remain 100% `CONTAINED`.
   - Verify full repository suite (1,302/1,302 PASS, 0 XFAIL, 0 FAIL).
4. **Issue Final Ratification Certificate.**
