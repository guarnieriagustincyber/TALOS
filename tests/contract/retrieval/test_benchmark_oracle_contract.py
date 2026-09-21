"""Contract tests for benchmark Oracle dataset in S3.6.2."""

import json
from pathlib import Path
import sys
import pytest

from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    RelevanceGrade,
)
from study_engine.retrieval.oracle import validate_oracle_dataset


ORACLE_PATH = Path("data/benchmark/benchmark_oracle.json")
CORPUS_PATH = Path("data/benchmark/benchmark_corpus.json")


def test_benchmark_oracle_dataset_exists_and_loads():
    """Verify benchmark_oracle.json exists and satisfies Oracle schema."""
    if not ORACLE_PATH.exists():
        pytest.fail(f"Benchmark oracle artifact missing at: {ORACLE_PATH}")

    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset = OracleDataset.model_validate(data)
    assert dataset.version == "1.0.0"
    assert len(dataset.queries) > 0
    validate_oracle_dataset(dataset)


def test_benchmark_oracle_size_and_notebook_balance():
    """Verify Oracle size is within 30-50 queries with balanced notebooks."""
    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    queries = data["queries"]
    # Requirement: 30 to 50 queries
    assert 30 <= len(queries) <= 50

    so_queries = [q for q in queries if q["notebook_id"] == "fadena-so"]
    prog_queries = [q for q in queries if q["notebook_id"] == "fadena-prog"]

    # Balanced representation
    assert len(so_queries) >= 15
    assert len(prog_queries) >= 15
    assert len(so_queries) == len(prog_queries)


def test_benchmark_oracle_category_coverage():
    """Verify all 6 categories have representative representation."""
    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    queries = data["queries"]
    categories = {q["category"] for q in queries}

    expected_categories = {c.value for c in BenchmarkCategory}
    assert categories == expected_categories

    counts = {
        cat: sum(1 for q in queries if q["category"] == cat)
        for cat in categories
    }
    assert counts[BenchmarkCategory.DEFINITION.value] >= 6
    assert counts[BenchmarkCategory.PARAPHRASE.value] >= 6
    assert counts[BenchmarkCategory.CODE_SYMBOL.value] >= 6
    assert counts[BenchmarkCategory.DIACRITICS_VARIANTS.value] >= 4
    assert counts[BenchmarkCategory.AMBIGUOUS.value] >= 4
    assert counts[BenchmarkCategory.CURRICULAR_LEAKAGE.value] >= 4


def test_benchmark_oracle_relational_integrity():
    """Verify chunk ground truth in corpus and respects notebook scoping."""
    with open(ORACLE_PATH, "r", encoding="utf-8") as f:
        oracle_data = json.load(f)
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    corpus_map = {c["id"]: c for c in corpus_data["chunks"]}

    for q in oracle_data["queries"]:
        cat_leak = BenchmarkCategory.CURRICULAR_LEAKAGE.value
        is_leakage = q["category"] == cat_leak
        if is_leakage:
            assert len(q["relevant"]) == 0
        else:
            assert len(q["relevant"]) > 0
            # Must have at least one grade 2 (direct relevance) chunk
            direct_grades = [
                r for r in q["relevant"] if r["grade"] == RelevanceGrade.DIRECT
            ]
            assert len(direct_grades) >= 1

            for rel in q["relevant"]:
                cid = rel["chunk_id"]
                assert cid in corpus_map, (
                    f"Query {q['id']} references missing chunk '{cid}'"
                )
                chunk = corpus_map[cid]
                msg = (
                    f"Query {q['id']} ({q['notebook_id']}) references "
                    f"chunk '{cid}' from wrong '{chunk['notebook_id']}'"
                )
                assert chunk["notebook_id"] == q["notebook_id"], msg


def test_load_and_validate_oracle_cli_function(tmp_path: Path):
    """Test load_and_validate_oracle function error and success paths."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
    from scripts.build_benchmark_oracle import load_and_validate_oracle

    res = load_and_validate_oracle(ORACLE_PATH)
    assert res["metadata"]["total_queries"] == 40

    non_existent = tmp_path / "missing_oracle.json"
    with pytest.raises(FileNotFoundError) as exc:
        load_and_validate_oracle(non_existent)
    assert "Oracle file not found" in str(exc.value)
