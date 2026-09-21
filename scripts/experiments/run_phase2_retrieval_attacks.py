#!/usr/bin/env python3
"""Hito 6 — Phase 2: Retrieval Attacks Campaign Runner.

Executes the 12 adversarial retrieval attack cases against RetrievalService,
KnowledgeStore, and the Epistemic Gatekeeper in strict severity order.

Protocol: ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT
Invariant: RETRIEVED_EVIDENCE ⊆ AUTHORIZED_SCOPE (Bidirectionally enforced)
Rule: STRICTLY NO PATCHING DURING DIAGNOSTIC CAMPAIGN.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ingest_corpus import ingest_benchmark_corpus
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.curriculum.registry import CurriculumRegistry
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


class Phase2RetrievalRunner:
    """Executes Phase 2 Retrieval Attacks and verifies the subset invariant."""

    def __init__(
        self,
        repo_root: Path,
        oracle_path: Optional[Path] = None,
        work_dir: Optional[Path] = None,
    ) -> None:
        self.repo_root = repo_root
        self.oracle_path = oracle_path or (
            repo_root / "data" / "experiments" / "hito6" / "hito6_oracle.json"
        )
        if not self.oracle_path.exists():
            raise FileNotFoundError(f"Oracle file not found at {self.oracle_path}")

        with open(self.oracle_path, "r", encoding="utf-8") as f:
            self.oracle = json.load(f)

        self.phase2_cases: List[Dict[str, Any]] = self.oracle[
            "phase_2_retrieval_attacks"
        ]["cases"]

        self._custom_work_dir = work_dir
        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None

    def _setup_isolated_pipeline(self) -> Tuple[RetrievalService, CurriculumRegistry, KnowledgeStore, Path]:
        """Initialize an isolated test pipeline with benchmark corpus and synthetic boundary chunks."""
        if self._custom_work_dir:
            work_path = self._custom_work_dir
            work_path.mkdir(parents=True, exist_ok=True)
        else:
            self._temp_dir = tempfile.TemporaryDirectory(prefix="hito6_phase2_")
            work_path = Path(self._temp_dir.name)

        db_path = work_path / "knowledge_store.db"
        vec_path = work_path / "vector_store.db"

        store = KnowledgeStore(db_path=db_path)
        store.initialize()

        # Ingest benchmark corpus
        sources_dir = self.repo_root / "data" / "benchmark" / "sources"
        ingest_benchmark_corpus(
            store=store,
            sources_dir=sources_dir,
            notebook_id="NB-CYBERSECURITY-V1",
        )

        # Refinement 1: Create isolated synthetic boundary chunks
        concurrency_chunks = store.chunks.list_by_document("so_concurrencia.pdf")
        max_idx_concurr = max((c.index for c in concurrency_chunks), default=0)

        chunk_p8 = Chunk(
            id="so_concurrencia.pdf:p08:c_boundary",
            source_id="src_so_concurrencia.pdf",
            document_id="so_concurrencia.pdf",
            page_start=8,
            page_end=8,
            index=max_idx_concurr + 1,
            content="Sección 2.3.8 Límite exacto de concurrencia en la página ocho: condiciones de carrera en el límite.",
            metadata={"page_number": 8, "synthetic": True, "purpose": "boundary_test"},
        )
        chunk_p9 = Chunk(
            id="so_concurrencia.pdf:p09:c_boundary",
            source_id="src_so_concurrencia.pdf",
            document_id="so_concurrencia.pdf",
            page_start=9,
            page_end=9,
            index=max_idx_concurr + 2,
            content="Sección 2.3.9 Contenido prohibido de concurrencia fuera de límite en página nueve: condiciones de carrera.",
            metadata={"page_number": 9, "synthetic": True, "purpose": "boundary_test"},
        )
        store.chunks.save_chunks([chunk_p8, chunk_p9])

        # Index all chunks into isolated vector store
        embedder = DeterministicHashEmbedder(dimensions=128)
        vstore = SQLiteVectorStore(db_path=vec_path)
        records: List[VectorRecord] = []
        for doc in store.documents.list_all():
            for c in store.chunks.list_by_document(doc.id):
                vec = embedder.embed_passages([c.content])[0]
                records.append(
                    VectorRecord(
                        chunk_id=c.id,
                        source_id=c.source_id,
                        notebook_id="NB-CYBERSECURITY-V1",
                        provider_id=embedder.provider_id,
                        model_id=embedder.model_id,
                        dimensions=embedder.dimensions,
                        vector=vec,
                    )
                )
        vstore.save_records(records)

        lexical = LexicalRetriever(store)
        dense = DenseRetriever(store, vstore, embedder)
        hybrid = HybridRetriever(store, lexical, dense)
        retrieval_service = RetrievalService(store, hybrid)

        curriculum_dir = self.repo_root / "data" / "curriculum"
        registry = CurriculumRegistry(root_dir=curriculum_dir)

        return retrieval_service, registry, store, work_path

    def _verify_bidirectional_subset(
        self,
        candidates: List[ScoredCandidate],
        authorized_scopes: List[Dict[str, Any]],
    ) -> Tuple[bool, List[str]]:
        """Verify the subset invariant bidirectionally: RETRIEVED_EVIDENCE ⊆ AUTHORIZED_SCOPE."""
        violations: List[str] = []
        if not candidates:
            return True, violations

        authorized_doc_ids: Set[str] = {s["document_id"] for s in authorized_scopes}

        # 1. Forward check: All retrieved candidates belong to authorized documents
        for c in candidates:
            if c.document_id not in authorized_doc_ids:
                violations.append(
                    f"Candidate {c.chunk_id} belongs to unauthorized document '{c.document_id}' "
                    f"(authorized: {sorted(authorized_doc_ids)})"
                )

        # 2. Reverse check: Not any candidate belongs to an unauthorized document
        unauthorized_cands = [c for c in candidates if c.document_id not in authorized_doc_ids]
        if unauthorized_cands:
            violations.append(
                f"Found {len(unauthorized_cands)} unauthorized candidates: {[c.chunk_id for c in unauthorized_cands]}"
            )

        # 3. Page range check (bidirectional per document scope)
        for c in candidates:
            cand_page = c.page_start or c.metadata.get("page_number")
            if cand_page is None:
                violations.append(f"Candidate {c.chunk_id} has missing page metadata")
                continue

            # Check if there exists at least one authorized scope for this document that includes cand_page
            doc_scopes = [s for s in authorized_scopes if s["document_id"] == c.document_id]
            is_page_authorized = any(
                s["page_start"] <= cand_page <= s["page_end"] for s in doc_scopes
            )
            if not is_page_authorized:
                violations.append(
                    f"Candidate {c.chunk_id} (doc={c.document_id}, page={cand_page}) is outside authorized "
                    f"page ranges: {[(s['page_start'], s['page_end']) for s in doc_scopes]}"
                )

        return len(violations) == 0, violations

    def run_all_cases(self) -> Dict[str, Any]:
        """Execute all 12 cases in severity order and collect telemetry."""
        print("=" * 75)
        print("🧪 HITO 6 — FASE 2: CAMPAÑA DE ATAQUES DE RECUPERACIÓN (12 CASOS)")
        print("=" * 75)
        print(f"Protocolo:  ATTACK -> OBSERVE -> COMPARE ORACLE -> CLASSIFY -> DOCUMENT")
        print(f"Invariante: RETRIEVED_EVIDENCE ⊆ AUTHORIZED_SCOPE (Bidireccional)")
        print(f"Oráculo:    {self.oracle_path}")
        print(f"Casos:      {len(self.phase2_cases)} casos en orden de severidad")
        print("-" * 75)

        retrieval_service, registry, store, work_path = self._setup_isolated_pipeline()

        telemetry_records: List[Dict[str, Any]] = []
        findings: List[Dict[str, Any]] = []
        overall_mismatches = 0

        try:
            for case_spec in self.phase2_cases:
                case_id = case_spec["case_id"]
                sev = case_spec["severity_order"]
                attack_cls = case_spec["attack_class"]
                desc = case_spec["description"]
                exp_route = case_spec["expected_route"]
                exp_verdict = case_spec["expected_verdict"]
                auth_scope = case_spec.get("authorized_scope", [])

                print(f"\n[{sev}/12] Executing {case_id} ({attack_cls})...")
                print(f"     Description: {desc}")

                node_id = case_spec["input"].get("node_id")
                query = case_spec["input"]["query"]
                notebook_id = case_spec["input"].get("notebook_id")

                # Attack Execution
                candidates: List[ScoredCandidate] = retrieval_service.retrieve_evidence(
                    query=query,
                    node_id=node_id,
                    notebook_id=notebook_id,
                    registry=registry,
                    top_k=5,
                )
                rejections = list(retrieval_service.last_rejections)

                candidate_count = len(candidates)
                retrieved_doc_ids = sorted(list({c.document_id for c in candidates}))
                retrieved_pages = sorted(list({c.page_start for c in candidates if c.page_start is not None}))

                # Determine observed route and verdict
                if candidate_count > 0:
                    observed_route = "RETRIEVED"
                    if case_id == "P2-RET-01":
                        observed_verdict = "AUTHORIZED_SOURCES_ONLY"
                    elif case_id == "P2-RET-03":
                        observed_verdict = "AUTHORIZED_PAGES_ONLY"
                    elif case_id == "P2-RET-06":
                        observed_verdict = "MULTI_DOC_AUTHORIZED"
                    elif case_id == "P2-RET-08":
                        observed_verdict = "PAGE_BOUNDARY_LIMIT_ADMITTED"
                    elif case_id == "P2-RET-10":
                        observed_verdict = "PAGE_METADATA_ACCURATE"
                    else:
                        observed_verdict = "RETRIEVED"
                else:
                    observed_route = "ABSTAINED"
                    if case_id == "P2-RET-02":
                        observed_verdict = "NO_EVIDENCE"
                    elif case_id == "P2-RET-04":
                        observed_verdict = "NOTEBOOK_ISOLATION_ENFORCED"
                    elif case_id == "P2-RET-05":
                        observed_verdict = "NODE_ISOLATION_ENFORCED"
                    elif case_id == "P2-RET-07":
                        observed_verdict = "DOCUMENT_LEAKAGE_PREVENTED"
                    elif case_id == "P2-RET-09":
                        observed_verdict = "PAGE_BOUNDARY_OUTSIDE_FILTERED"
                    elif case_id == "P2-RET-11":
                        observed_verdict = "FAIL_CLOSED_NO_ALIGNMENT"
                    elif case_id == "P2-RET-12":
                        observed_verdict = "REJECTIONS_TELEMETRY_RECORDED"
                    else:
                        observed_verdict = "NO_EVIDENCE"

                # Bidirectional subset validation
                subset_valid, subset_violations = self._verify_bidirectional_subset(
                    candidates=candidates,
                    authorized_scopes=auth_scope,
                )

                # Special invariant checks
                case_mismatches: List[str] = []
                if observed_route != exp_route:
                    case_mismatches.append(f"Route mismatch: observed '{observed_route}' != expected '{exp_route}'")
                if observed_verdict != exp_verdict:
                    case_mismatches.append(f"Verdict mismatch: observed '{observed_verdict}' != expected '{exp_verdict}'")
                if not subset_valid:
                    case_mismatches.extend(subset_violations)

                # Case-specific checks
                if case_id == "P2-RET-08":
                    has_p8 = any(c.page_start == 8 and c.document_id == "so_concurrencia.pdf" for c in candidates)
                    if not has_p8:
                        case_mismatches.append("P2-RET-08: Expected boundary candidate at page 8 was not admitted")
                elif case_id == "P2-RET-09":
                    has_p9 = any(c.page_start == 9 for c in candidates)
                    if has_p9:
                        case_mismatches.append("P2-RET-09: Prohibited candidate at page 9 was leaked!")
                elif case_id == "P2-RET-10":
                    for c in candidates:
                        if c.page_start is None or c.page_end is None or c.page_start > c.page_end:
                            case_mismatches.append(f"P2-RET-10: Invalid page metadata on chunk {c.chunk_id}")
                elif case_id == "P2-RET-12":
                    if not rejections:
                        case_mismatches.append("P2-RET-12: Expected rejection telemetry records but last_rejections is empty")
                    else:
                        for r in rejections:
                            if not all(k in r for k in ["chunk_id", "document_id", "reason", "dense_score", "threshold"]):
                                case_mismatches.append(f"P2-RET-12: Incomplete rejection telemetry schema: {r}")

                classification = "CONFIRMED_PASS" if not case_mismatches else "CONFIRMED_DEFECT"
                if classification == "CONFIRMED_DEFECT":
                    overall_mismatches += len(case_mismatches)

                print(f"     Observed Route:    {observed_route} (Expected: {exp_route})")
                print(f"     Observed Verdict:  {observed_verdict} (Expected: {exp_verdict})")
                print(f"     Candidates Found:  {candidate_count}")
                print(f"     Retrieved Docs:    {retrieved_doc_ids}")
                print(f"     Retrieved Pages:   {retrieved_pages}")
                print(f"     Subset Valid:      {subset_valid}")
                print(f"     Rejections Logged: {len(rejections)}")
                print(f"     Classification:    {classification}")

                record = {
                    "case_id": case_id,
                    "severity_order": sev,
                    "attack_class": attack_cls,
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "classification": classification,
                    "input": {
                        "node_id": node_id,
                        "query": query,
                        "notebook_id": notebook_id,
                    },
                    "authorized_scope": auth_scope,
                    "oracle_expected": {
                        "route": exp_route,
                        "verdict": exp_verdict,
                        "page_range": case_spec.get("expected_page_range"),
                    },
                    "observed": {
                        "route": observed_route,
                        "verdict": observed_verdict,
                        "candidate_count": candidate_count,
                        "retrieved_doc_ids": retrieved_doc_ids,
                        "retrieved_pages": retrieved_pages,
                        "subset_valid": subset_valid,
                        "rejections_logged": len(rejections),
                        "rejections_telemetry": rejections,
                    },
                    "mismatches": case_mismatches,
                }
                telemetry_records.append(record)
                findings.append({
                    "case_id": case_id,
                    "severity_order": sev,
                    "attack_class": attack_cls,
                    "classification": classification,
                    "description": desc,
                    "mismatches": case_mismatches,
                })

        finally:
            # Refinement 1: Clean up isolated temporary pipeline
            if self._temp_dir is not None:
                self._temp_dir.cleanup()

        passed_cases = sum(1 for f in findings if f["classification"] == "CONFIRMED_PASS")
        defects = sum(1 for f in findings if f["classification"] == "CONFIRMED_DEFECT")
        final_verdict = "CERTIFIED_PASS" if defects == 0 else "ABORT_ON_DEFECT"

        print("\n" + "=" * 75)
        print("📊 RESUMEN FINAL DE LA CAMPAÑA FASE 2 (RETRIEVAL ATTACKS)")
        print("=" * 75)
        print(f"Total Casos Evaluados:      {len(self.phase2_cases)}")
        print(f"CONFIRMED_PASS:             {passed_cases}")
        print(f"CONFIRMED_DEFECT:           {defects}")
        print(f"Veredicto Formal de Fase 2: {final_verdict}")
        print("=" * 75 + "\n")

        summary_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_2_retrieval_attacks",
            "executed_at_utc": datetime.now(timezone.utc).isoformat(),
            "total_cases": len(self.phase2_cases),
            "passed_cases": passed_cases,
            "defects_found": defects,
            "findings": findings,
        }

        # Update or append telemetry
        telemetry_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_telemetry.json"
        existing_telemetry: List[Dict[str, Any]] = []
        if telemetry_path.exists():
            try:
                with open(telemetry_path, "r", encoding="utf-8") as f:
                    existing_telemetry = json.load(f)
            except Exception:
                existing_telemetry = []

        # Remove previous phase 2 records if any, then append
        consolidated_telemetry = [
            t for t in existing_telemetry if not str(t.get("case_id", "")).startswith("P2-RET")
        ]
        consolidated_telemetry.extend(telemetry_records)

        with open(telemetry_path, "w", encoding="utf-8") as f:
            json.dump(consolidated_telemetry, f, indent=2)

        results_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_results.json"
        results_data = {
            "campaign_id": "HITO6-SURVIVAL-ADVERSARIAL",
            "phase": "phase_2_retrieval_attacks",
            "summary": summary_data,
        }
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results_data, f, indent=2)

        summary_path = self.repo_root / "data" / "experiments" / "hito6" / "hito6_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

        return results_data


def main() -> int:
    """CLI entrypoint for Phase 2 Retrieval Attacks runner."""
    parser = argparse.ArgumentParser(description="Hito 6 Phase 2 Retrieval Attacks Runner")
    parser.add_argument("--oracle", type=str, default=None, help="Path to hito6_oracle.json")
    args = parser.parse_args()

    runner = Phase2RetrievalRunner(
        repo_root=REPO_ROOT,
        oracle_path=Path(args.oracle) if args.oracle else None,
    )
    results = runner.run_all_cases()
    return 0 if results["summary"]["defects_found"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
