# KASIU — Architecture Baseline & Repository Audit (Phase 0)

**Date**: 2026-09-08
**Branch**: `main`
**Base Commit / Tag**: `3438b1a` (`v0.2.2`)

---

## 1. Executive Summary

This document establishes the real, audited state of the **KASIU** repository prior to executing the master plan towards v1.0.0. Certification claims are derived exclusively from actual automated test runs, static typing checks, and immutable contract structures.

---

## 2. Frozen Perimeter Integrity

The following core epistemic subsystems remain **frozen and untouched**:
- `study_engine/state/` (Pure state derivation, ledger, append-only events)
- `study_engine/execution/` (Deterministic sandboxing & execution adapters)
- `study_engine/assessment/` (Evaluators, fact extractors, aggregators)
- `study_engine/audit/` (Forensic auditor S4.4, lexical guards, citation verifiers)

*Invariant*: Zero relaxation of the trust model. LLMs act as intent interpreters and language generators; they are never epistemic authorities.

---

## 3. Subsystems Status Matrix

| Subsystem | Certified Status | Test Coverage | Key Contracts & Components |
|---|---|---|---|
| **S1 Curriculum** | Certified | Complete | `CurriculumRegistry`, `CurricularRoadmap`, `RoadmapNode`, `RoadmapDependency` |
| **S2 Catalog / Storage** | Certified | Complete | `KnowledgeStore`, `SQLiteStorageEngine`, `Notebook`, `Source`, `Document`, `Chunk` |
| **S3 Epistemic Retrieval** | Certified | Complete | `ContextPacker`, `HybridRetrieval`, Epistemic isolation, Citation packaging |
| **S4.3 Generation / LLM** | Certified | Complete | `ProviderFactory`, `HttpOpenAIBackend`, `MockBackend`, Multi-provider fallback |
| **S4.4 Forensic Audit** | Certified | Complete | `ForensicAuditReport`, fail-closed grounding checks |
| **S5.3 / S7 Study Loop** | Certified | Complete | `StudyLoopController`, `SessionOrchestrator`, `DeterministicTutorPolicy` |
| **Semantic Router & Policy** | Implemented (v0.3.x) | Certified | `SemanticRouter`, `IntentContract`, `DeterministicPolicyValidator`, `LocalOrchestrator` |

---

## 4. Notebook / Study Context Analysis

### Existing Capabilities
- `Notebook` contract exists in `src/study_engine/contracts/notebook.py` with `id`, `name`, `description`, `subject`, `sources`, `metadata`, `created_at`, `updated_at`.
- `KnowledgeStore` natively implements ACID-compliant `create_notebook`, `get_notebook`, `delete_notebook`, `list_notebooks`, and `notebook_sources` (M:N isolation).
- Full chunk/document isolation per notebook is already enforced by the SQLite foreign key structure and storage layer.

### Identified Gaps for v0.4.0
1. `Notebook` contract does not yet have an explicit, top-level `curriculum_id` field (currently stored in metadata).
2. `StudyLoopController` currently resolves `active_node_id` from session targets, but does not explicitly take a sovereign `Notebook` context envelope as the primary unit of study context.

---

## 5. Verification Baseline Metrics

- **Mypy Strict**: `0 issues` across all modules.
- **Pytest Suite**:
  - `tests/integration/`: 56 passed, 7 skipped (real LLM keys skipped hermetically).
  - `tests/integration/test_semantic_router.py`: 5 passed.
  - `tests/integration/test_question_type.py`, `test_local_orchestrator.py`, `test_followup_deterministic.py`: 11 passed.

---

## 6. Known Technical Debt & Execution Sequence

1. **Phase 1 (v0.4.0)**: Bind `curriculum_id` explicitly to `Notebook` contract; implement sovereign notebook tests with strict cross-notebook isolation.
2. **Phase 2 (v0.3.x / v0.4.0)**: Router adversarial test suite (malformed JSON, timeout, prompt injection, fallback safety).
3. **Phase 3 (v0.4.0+)**: Wire `Notebook` directly into `StudyLoopController` as the central study context container.
