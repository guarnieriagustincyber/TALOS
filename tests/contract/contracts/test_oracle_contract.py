"""Contract tests for Oracle domain validation in S3.2."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
    RelevanceGrade,
    RelevantChunk,
)


def test_oracle_query_rejects_empty_query():
    with pytest.raises(ValidationError):
        OracleQuery(
            id="q1", notebook_id="nb-so", query="   ",
            category=BenchmarkCategory.DEFINITION, rationale="r",
        )


def test_oracle_query_rejects_empty_notebook_id():
    with pytest.raises(ValidationError):
        OracleQuery(
            id="q1", notebook_id="  ", query="valid query",
            category=BenchmarkCategory.DEFINITION, rationale="r",
        )


def test_oracle_query_rejects_invalid_category():
    with pytest.raises(ValidationError):
        OracleQuery(
            id="q1", notebook_id="nb-so", query="valid query",
            category="AUTO",  # type: ignore
            rationale="r",
        )


def test_relevant_chunk_rejects_invalid_grade():
    with pytest.raises(ValidationError):
        RelevantChunk(chunk_id="c1", grade=3, rationale="r")  # type: ignore

    with pytest.raises(ValidationError):
        RelevantChunk(chunk_id="c1", grade=0, rationale="r")  # type: ignore

    with pytest.raises(ValidationError):
        RelevantChunk(chunk_id="c1", grade="high", rationale="r")  # type: ignore


def test_oracle_query_rejects_duplicate_chunk_ids():
    with pytest.raises(ValidationError) as exc_info:
        OracleQuery(
            id="q-dup",
            notebook_id="nb-so",
            query="test",
            category=BenchmarkCategory.DEFINITION,
            relevant=[
                RelevantChunk(chunk_id="chunk-dup", grade=RelevanceGrade.DIRECT, rationale="first"),
                RelevantChunk(chunk_id="chunk-dup", grade=RelevanceGrade.PARTIAL, rationale="second"),
            ],
            rationale="r",
        )
    assert "Duplicate chunk_id 'chunk-dup'" in str(exc_info.value)


def test_oracle_query_rejects_leakage_with_non_empty_relevant():
    with pytest.raises(ValidationError) as exc_info:
        OracleQuery(
            id="q-leak",
            notebook_id="nb-so",
            query="árboles en SO",
            category=BenchmarkCategory.CURRICULAR_LEAKAGE,
            relevant=[
                RelevantChunk(chunk_id="so:chunk1", grade=RelevanceGrade.DIRECT, rationale="should not exist")
            ],
            rationale="r",
        )
    assert "Curricular leakage queries must have an empty relevant list" in str(exc_info.value)


def test_oracle_query_accepts_valid_leakage_with_empty_relevant():
    q = OracleQuery(
        id="q-leak-valid",
        notebook_id="nb-so",
        query="árboles binarios en SO",
        category=BenchmarkCategory.CURRICULAR_LEAKAGE,
        relevant=[],
        rationale="Algebra query inside SO notebook must have zero relevant chunks",
    )
    assert q.relevant == []


def test_oracle_dataset_rejects_duplicate_query_ids():
    q1 = OracleQuery(
        id="q-same", notebook_id="nb1", query="query 1",
        category=BenchmarkCategory.DEFINITION, rationale="r1",
    )
    q2 = OracleQuery(
        id="q-same", notebook_id="nb1", query="query 2",
        category=BenchmarkCategory.DEFINITION, rationale="r2",
    )

    with pytest.raises(ValidationError) as exc_info:
        OracleDataset(version="1.0.0", queries=[q1, q2])

    assert "Duplicate query ID 'q-same'" in str(exc_info.value)


def test_oracle_dataset_rejects_blank_version():
    with pytest.raises(ValidationError):
        OracleDataset(version="   ", queries=[])

from study_engine.retrieval.oracle import OracleValidationError, validate_oracle_dataset


def test_relevant_chunk_rejects_blank_strings():
    with pytest.raises(ValidationError):
        RelevantChunk(chunk_id="   ", grade=RelevanceGrade.DIRECT, rationale="valid rationale")

    with pytest.raises(ValidationError):
        RelevantChunk(chunk_id="valid-id", grade=RelevanceGrade.DIRECT, rationale="   ")


def test_validate_oracle_dataset_catches_unvalidated_duplicates_and_leakage():
    q1 = OracleQuery(
        id="q-dup-raw", notebook_id="nb", query="query text",
        category=BenchmarkCategory.DEFINITION, rationale="r",
    )
    # Bypass pydantic with model_construct to test validator defense-in-depth
    ds_dup = OracleDataset.model_construct(version="1.0", queries=[q1, q1])
    with pytest.raises(OracleValidationError) as exc1:
        validate_oracle_dataset(ds_dup, store=None)
    assert "Duplicate query ID 'q-dup-raw'" in str(exc1.value)

    # Bypass pydantic with model_construct to test leakage check defense-in-depth
    bad_leak_query = OracleQuery.model_construct(
        id="q-leak-bad",
        notebook_id="nb",
        query="text",
        category=BenchmarkCategory.CURRICULAR_LEAKAGE,
        relevant=[RelevantChunk(chunk_id="c1", grade=RelevanceGrade.DIRECT, rationale="r")],
        rationale="r",
    )
    ds_leak = OracleDataset.model_construct(version="1.0", queries=[bad_leak_query])
    with pytest.raises(OracleValidationError) as exc2:
        validate_oracle_dataset(ds_leak, store=None)
    assert "Curricular leakage query 'q-leak-bad' must have zero relevant chunks" in str(exc2.value)
