"""Unit and Contract Tests for Fase 4 Evaluation Harness and Metrics.

Verifies:
1. Retrieval metrics computation (MRR@5, nDCG@5, Recall@5, Precision@5).
2. Epistemic Oracles (OOD abstention, scoping verification, anti-leakage).
3. Report generator produces valid JSON and Markdown.
4. Evaluation API endpoint returns valid summary without mutating state.
"""

from pathlib import Path
import pytest

from benchmark.metrics.retrieval_metrics import (
    compute_mrr,
    compute_ndcg,
    compute_recall,
    compute_precision,
)
from benchmark.metrics.epistemic_metrics import (
    verify_notebook_scoping,
    verify_fail_closed_abstention,
    compute_evidence_precision,
)
from benchmark.report.report_generator import build_markdown_report, generate_reports


def test_retrieval_metrics_perfect_hit():
    """Rank 1 hit should yield MRR=1.0 and nDCG=1.0."""
    retrieved = ["chunk_1", "chunk_2", "chunk_3"]
    qrels = {"chunk_1": 3, "chunk_2": 1}

    mrr = compute_mrr(retrieved, qrels, k=5)
    ndcg = compute_ndcg(retrieved, qrels, k=5)
    rec = compute_recall(retrieved, qrels, k=5)
    prec = compute_precision(retrieved, qrels, k=5)

    assert mrr == 1.0
    assert ndcg > 0.95
    assert rec == 1.0
    assert prec == pytest.approx(2 / 3, 0.01)


def test_retrieval_metrics_zero_hit():
    """Zero relevant chunks retrieved should yield MRR=0.0 and nDCG=0.0."""
    retrieved = ["chunk_99", "chunk_100"]
    qrels = {"chunk_1": 3, "chunk_2": 2}

    mrr = compute_mrr(retrieved, qrels, k=5)
    ndcg = compute_ndcg(retrieved, qrels, k=5)
    rec = compute_recall(retrieved, qrels, k=5)
    prec = compute_precision(retrieved, qrels, k=5)

    assert mrr == 0.0
    assert ndcg == 0.0
    assert rec == 0.0
    assert prec == 0.0


def test_scoping_oracle_isolation():
    """Verify that chunks outside the authorized notebook are flagged as leakage."""
    authorized_sources = {"src_fadena_so_memoria", "src_fadena_so_procesos"}

    # Authorized candidates
    assert verify_notebook_scoping(["src_fadena_so_memoria", "src_fadena_so_procesos"], authorized_sources) is True

    # Leaked candidate from unauthorized source
    assert verify_notebook_scoping(["src_fadena_so_memoria", "src_unauthorized_leak"], authorized_sources) is False


def test_ood_abstention_oracle():
    """OOD queries must fail-closed with 0 citations to pass."""
    # PASS: Zero citations and formal abstention
    assert verify_fail_closed_abstention(is_ood=True, abstained=True, emitted_citations=[]) is True

    # FAIL: Emitted citations on OOD query (hallucination / leakage)
    assert verify_fail_closed_abstention(is_ood=True, abstained=False, emitted_citations=["E1"]) is False

    # In-domain query with citations is normal
    assert verify_fail_closed_abstention(is_ood=False, abstained=False, emitted_citations=["E1"]) is True


def test_report_generator_markdown_structure():
    """Ensure report generator outputs expected markdown headers and gate results."""
    mock_results = {
        "run_id": "test-run-001",
        "timestamp": "2026-09-24T18:00:00Z",
        "golden_set_version": "v2.400",
        "mode": "fast",
        "overall_status": "PASS",
        "corpus_hash": "sha256:test",
        "vector_index_hash": "sha256:test",
        "gates_status": {
            "evidence_precision": True,
            "citation_correctness": True,
            "fail_closed_abstention": True,
            "notebook_scoping": True,
            "anti_leakage": True,
            "mrr5": True,
            "ndcg5": True,
            "latency_p50": True,
            "runtime": True,
        },
        "metrics": {
            "total_queries": 10,
            "runtime_s": 5.2,
            "evidence_precision": 1.0,
            "citation_correctness": 1.0,
            "fail_closed_abstention": 1.0,
            "notebook_scoping": 1.0,
            "anti_leakage": 1.0,
            "mrr5": 0.88,
            "ndcg5": 0.85,
            "recall5": 0.90,
            "precision5": 0.75,
            "latency_p50_ms": 25.0,
        },
        "baseline_comparison": {
            "mrr5": {"talos": 0.88, "baseline": 0.74, "diff": 0.14},
            "ndcg5": {"talos": 0.85, "baseline": 0.69, "diff": 0.16},
            "recall5": {"talos": 0.90, "baseline": 0.81, "diff": 0.09},
            "fail_closed_abstention": {"talos": 1.0, "baseline": 0.60, "diff": 0.40},
            "notebook_scoping": {"talos": 1.0, "baseline": 0.72, "diff": 0.28},
            "evidence_precision": {"talos": 1.0, "baseline": 0.85, "diff": 0.15},
        },
        "category_breakdown": {
            "fundamentos": {
                "total": 5,
                "mrr5": 0.90,
                "ndcg5": 0.88,
                "abstention_rate": 1.0,
                "scoping_pass_rate": 1.0,
            },
            "ood": {
                "total": 5,
                "mrr5": 1.0,
                "ndcg5": 1.0,
                "abstention_rate": 1.0,
                "scoping_pass_rate": 1.0,
            },
        },
    }

    md = build_markdown_report(mock_results)
    assert "Reporte Formal de Evaluación" in md
    assert "PASS" in md
    assert "MRR@5" in md
    assert "Perímetro Congelado" in md


def test_eval_summary_endpoint_read_only_contract():
    """Verify that GET /api/eval/summary is strictly read-only and idempotent."""
    from fastapi.testclient import TestClient
    from study_engine.web.app import create_app

    app = create_app()
    client = TestClient(app)

    # First call
    response_1 = client.get("/api/eval/summary")
    assert response_1.status_code == 200
    data_1 = response_1.json()

    # Second call (idempotence verification)
    response_2 = client.get("/api/eval/summary")
    assert response_2.status_code == 200
    data_2 = response_2.json()

    # Ensure identical responses without mutating any state
    assert data_1 == data_2
    assert "metrics" in data_1
    assert "gates_status" in data_1 or "gates" in data_1


def test_eval_summary_graceful_fallback(monkeypatch, tmp_path):
    """Verify that GET /api/eval/summary handles missing results cleanly without 500 errors."""
    from fastapi.testclient import TestClient
    from study_engine.web.app import create_app
    import study_engine.web.routes.eval as eval_route

    # Temporarily redirect RESULTS_DIR to empty directory
    monkeypatch.setattr(eval_route, "RESULTS_DIR", tmp_path)

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/eval/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "NO_RUNS_RECORDED"
    assert "metrics" in data
    assert "gates" in data


def test_eval_runs_endpoint_read_only():
    """Verify that GET /api/eval/runs returns a list without mutating state."""
    from fastapi.testclient import TestClient
    from study_engine.web.app import create_app

    app = create_app()
    client = TestClient(app)

    response = client.get("/api/eval/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_retrieval_metrics_empty_qrels_returns_zero():
    """Dirección Técnica mandate: empty qrels or empty retrieval MUST return 0.0, never 1.0."""
    # Empty qrels
    assert compute_mrr(["c1", "c2"], {}, k=5) == 0.0
    assert compute_ndcg(["c1", "c2"], {}, k=5) == 0.0
    assert compute_recall(["c1", "c2"], {}, k=5) == 0.0
    assert compute_precision(["c1", "c2"], {}, k=5) == 0.0

    # Empty retrieved
    assert compute_mrr([], {"c1": 2}, k=5) == 0.0
    assert compute_ndcg([], {"c1": 2}, k=5) == 0.0
    assert compute_recall([], {"c1": 2}, k=5) == 0.0
    assert compute_precision([], {"c1": 2}, k=5) == 0.0


def test_dataset_integrity_error_on_in_domain_abstention():
    """Enmienda E-HF2 & E-HF5: in-domain queries asserting abstention or missing qrels must abort."""
    from benchmark.run_fase4_eval import DatasetIntegrityError, run_benchmark

    # 1. In-domain with abstention=True must raise DatasetIntegrityError
    invalid_dataset_1 = {
        "golden_set_version": "test-v1",
        "queries": [
            {
                "query_id": "TEST-IN-001",
                "category": "fundamentos",
                "notebook_scope": ["NB-SEC-01-C-PTR"],
                "query": "¿Qué es un puntero?",
                "expected": {"abstention": True, "relevant_chunks": []},
                "oracle_type": "retrieval_citation",
            }
        ]
    }
    with pytest.raises(DatasetIntegrityError, match="no puede tener oracle_type='abstention_oracle' ni expected.abstention=True"):
        run_benchmark(invalid_dataset_1, {"TEST-IN-001": {"c1": 1}})

    # 2. In-domain with empty qrels must raise DatasetIntegrityError
    invalid_dataset_2 = {
        "golden_set_version": "test-v1",
        "queries": [
            {
                "query_id": "TEST-IN-002",
                "category": "fundamentos",
                "notebook_scope": ["NB-SEC-01-C-PTR"],
                "query": "¿Qué es un puntero?",
                "expected": {"abstention": False, "relevant_chunks": ["c1"]},
                "oracle_type": "retrieval_citation",
            }
        ]
    }
    with pytest.raises(DatasetIntegrityError, match="debe poseer qrels válidos y no vacíos"):
        run_benchmark(invalid_dataset_2, {"TEST-IN-002": {}})


def test_golden_set_v2_401_exact_counts_and_separation():
    """Enmienda E-HF1, E-HF2, E-HF5: Verify exact 420 queries, 360 in-domain, 60 OOD."""
    import json
    repo_root = Path(__file__).resolve().parents[2]
    gs_path = repo_root / "data/eval/golden_set_v2_401.json"
    qrels_path = repo_root / "data/eval/qrels/golden_set_v2_401.qrels.json"

    if not gs_path.exists() or not qrels_path.exists():
        pytest.skip("Golden Set v2.401 not generated yet")

    with open(gs_path, "r", encoding="utf-8") as f:
        gs = json.load(f)
    with open(qrels_path, "r", encoding="utf-8") as f:
        qrels_data = json.load(f)

    queries = gs["queries"]
    qrels = qrels_data["qrels"]

    assert len(queries) == 420, f"Expected 420 queries, got {len(queries)}"
    assert len(qrels) == 420, f"Expected 420 qrels entries, got {len(qrels)}"

    # Categorization counts
    from collections import Counter
    cat_counts = Counter(q["category"] for q in queries)
    assert cat_counts["fundamentos"] == 120
    assert cat_counts["sintaxis_codigo"] == 80
    assert cat_counts["multi_capitulo"] == 80
    assert cat_counts["vulnerabilidades"] == 60
    assert cat_counts["depuracion_estudiante"] == 20
    assert cat_counts["ood_trampas"] == 60

    # In-domain vs OOD assertions
    for q in queries:
        qid = q["query_id"]
        cat = q["category"]
        if cat == "ood_trampas":
            assert q["expected"]["abstention"] is True
            assert q["oracle_type"] == "abstention_oracle"
            assert qrels[qid] == {}
        else:
            assert q["expected"]["abstention"] is False
            assert q["oracle_type"] in ("retrieval_citation", "anti_shortcut_oracle")
            assert len(qrels[qid]) > 0
            assert "qrels_provenance" in q
            assert "audit_status" in q


def test_math_audit_consistency_and_ood_exclusion():
    """Enmienda E-HF2: verify math_audit reconciles weighted category MRR with global MRR (< 1e-9)."""
    from benchmark.run_fase4_eval import run_benchmark

    mini_dataset = {
        "golden_set_version": "test-v1",
        "queries": [
            {
                "query_id": "MINI-IN-001",
                "category": "fundamentos",
                "notebook_scope": ["NB-SEC-01-C-PTR"],
                "query": "puntero en C",
                "expected": {"abstention": False, "relevant_chunks": ["chk_1"]},
                "oracle_type": "retrieval_citation",
            },
            {
                "query_id": "MINI-IN-002",
                "category": "sintaxis_codigo",
                "notebook_scope": ["NB-SEC-01-C-PTR"],
                "query": "sintaxis de puntero",
                "expected": {"abstention": False, "relevant_chunks": ["chk_2"]},
                "oracle_type": "retrieval_citation",
            },
            {
                "query_id": "MINI-OOD-001",
                "category": "ood_trampas",
                "notebook_scope": ["NB-SEC-01-C-PTR"],
                "query": "angiospermas xilema secundario",
                "expected": {"abstention": True, "relevant_chunks": []},
                "oracle_type": "abstention_oracle",
            },
        ],
    }
    mini_qrels = {
        "MINI-IN-001": {"chk_1": 3},
        "MINI-IN-002": {"chk_2": 3},
        "MINI-OOD-001": {},
    }

    results = run_benchmark(mini_dataset, mini_qrels)
    assert "math_audit" in results
    audit = results["math_audit"]
    assert audit["consistent"] is True
    assert audit["delta_mrr5"] < 1e-9
    assert audit["in_domain_count"] == 2
    assert audit["ood_count"] == 1
    # Check that OOD category has N/A for MRR and nDCG
    cat_breakdown = results["category_breakdown"]
    assert cat_breakdown["ood_trampas"]["mrr5"] == "N/A"
    assert cat_breakdown["ood_trampas"]["ndcg5"] == "N/A"



