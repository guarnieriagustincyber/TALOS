"""Unit tests for Oracle contracts in S3.2."""

from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
    RelevanceGrade,
    RelevantChunk,
)


def test_benchmark_category_enum_values():
    expected_categories = {
        "CODE_SYMBOL",
        "DEFINITION",
        "PARAPHRASE",
        "DIACRITICS_VARIANTS",
        "AMBIGUOUS",
        "CURRICULAR_LEAKAGE",
    }
    actual_categories = {c.value for c in BenchmarkCategory}
    assert actual_categories == expected_categories
    assert "AUTO" not in actual_categories
    assert len(actual_categories) == 6


def test_relevance_grade_enum_values():
    assert RelevanceGrade.PARTIAL == 1
    assert RelevanceGrade.DIRECT == 2
    assert len(RelevanceGrade) == 2


def test_relevant_chunk_instantiation():
    item = RelevantChunk(
        chunk_id="chunk-101",
        grade=RelevanceGrade.DIRECT,
        rationale="Canonical definition of memory paging.",
    )
    assert item.chunk_id == "chunk-101"
    assert item.grade == 2
    assert item.rationale == "Canonical definition of memory paging."


def test_oracle_query_multiple_grade2_and_grade1():
    q = OracleQuery(
        id="q-01",
        notebook_id="fadena-so",
        query="memoria",
        category=BenchmarkCategory.AMBIGUOUS,
        relevant=[
            RelevantChunk(chunk_id="c1", grade=RelevanceGrade.DIRECT, rationale="Direct intro"),
            RelevantChunk(chunk_id="c2", grade=RelevanceGrade.DIRECT, rationale="Direct paging"),
            RelevantChunk(chunk_id="c3", grade=RelevanceGrade.PARTIAL, rationale="Contextual frames"),
        ],
        rationale="Evaluates multi-chunk relevance assignment.",
    )
    assert len(q.relevant) == 3
    assert q.relevant[0].grade == 2
    assert q.relevant[1].grade == 2
    assert q.relevant[2].grade == 1


def test_oracle_dataset_json_roundtrip():
    q = OracleQuery(
        id="q-code",
        notebook_id="fadena-prog",
        query="malloc()",
        category=BenchmarkCategory.CODE_SYMBOL,
        relevant=[
            RelevantChunk(chunk_id="c-malloc", grade=RelevanceGrade.DIRECT, rationale="API definition")
        ],
        rationale="C memory allocation",
    )
    dataset = OracleDataset(
        version="1.0.0",
        queries=[q],
        metadata={"author": "Study Engine Board"},
    )

    json_repr = dataset.model_dump_json()
    restored = OracleDataset.model_validate_json(json_repr)

    assert restored.version == "1.0.0"
    assert len(restored.queries) == 1
    assert restored.queries[0].id == "q-code"
    assert restored.queries[0].relevant[0].chunk_id == "c-malloc"
    assert restored.metadata["author"] == "Study Engine Board"
