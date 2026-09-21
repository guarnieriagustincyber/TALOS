"""Contract tests for S3.6.3 Three-Way Benchmark Certification."""

import json
from pathlib import Path
import sys
import pytest

from study_engine.retrieval.embedding import MockEmbeddingProvider


RESULTS_PATH = Path("data/benchmark/benchmark_results.json")
CORPUS_PATH = Path("data/benchmark/benchmark_corpus.json")
ORACLE_PATH = Path("data/benchmark/benchmark_oracle.json")


def test_production_benchmark_results_integrity():
    """Verify saved certification artifact satisfies contract invariants."""
    if not RESULTS_PATH.exists():
        pytest.fail(f"Benchmark results missing at: {RESULTS_PATH}")

    with open(RESULTS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["phase"] == "S3.6.3"
    assert data["total_queries"] == 40

    globals_data = data["global_metrics"]
    for strat in ["bm25", "dense", "hybrid_rrf"]:
        assert strat in globals_data
        # Hard invariant: Strict zero curricular leakage across all strategies
        assert globals_data[strat]["leakage_rate"] == 0.0
        assert globals_data[strat]["total_illegal_candidates_count"] == 0

    counts = data["summary_counts"]
    assert counts["leakage_controls_passed"] == 6
    assert counts["rrf_degradations"] == 0
    assert counts["consensus_wins"] >= 5

    # Dense and Hybrid recall standards
    assert globals_data["dense"]["mean_direct_recall_at_5"] >= 0.90
    assert globals_data["hybrid_rrf"]["mean_direct_recall_at_5"] >= 0.90
    assert globals_data["hybrid_rrf"]["mrr"] >= 0.85

    # BM25 symbol dominance check
    cat_bm25 = data["by_category"]["bm25"]
    assert cat_bm25["CODE_SYMBOL"]["mean_direct_recall_at_5"] >= 0.80

    # Latency telemetry present
    lat = data["latency_stats"]
    assert lat["lexical"]["total_ms"]["p50"] > 0.0
    assert lat["dense"]["total_ms"]["p50"] > 0.0
    assert lat["hybrid"]["total_ms"]["p50"] > 0.0


def test_compute_percentiles_helper():
    """Test latency percentiles calculator."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.run_three_way_certification import compute_percentiles

    empty_stats = compute_percentiles([])
    assert empty_stats["mean"] == 0.0
    assert empty_stats["p50"] == 0.0

    stats = compute_percentiles([10.0, 20.0, 30.0, 40.0, 50.0])
    assert stats["p50"] == 30.0
    assert stats["min"] == 10.0
    assert stats["max"] == 50.0


def test_run_certification_mock_fast_path(tmp_path: Path):
    """Verify run_certification execution with MockEmbeddingProvider."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.run_three_way_certification import run_certification

    out_file = tmp_path / "mock_results.json"
    mock_provider = MockEmbeddingProvider(dimensions=384)

    results = run_certification(
        corpus_path=CORPUS_PATH,
        oracle_path=ORACLE_PATH,
        output_path=out_file,

        db_dir=tmp_path / "db",
        provider=mock_provider,
    )

    assert out_file.exists()
    assert results["total_queries"] == 40
    assert results["summary_counts"]["leakage_controls_passed"] == 6
