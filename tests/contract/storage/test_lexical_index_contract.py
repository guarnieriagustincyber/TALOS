"""Contract tests for SearchResult contract and SQLiteLexicalIndex constraints."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.search import SearchResult
from study_engine.storage.lexical_index import SQLiteLexicalIndex
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_search_result_contract_validation():
    # Valid construction
    res = SearchResult(
        chunk_id="doc-1:chunk_00",
        document_id="doc-1",
        source_id="src-1",
        score=2.345,
        snippet="Snippet with [MATCH]term[/MATCH]",
        content="Full chunk content",
        index=0,
    )
    assert res.chunk_id == "doc-1:chunk_00"
    assert res.score == 2.345
    assert res.index == 0

    # Serialization roundtrip
    dumped = res.model_dump()
    assert dumped["chunk_id"] == "doc-1:chunk_00"
    assert dumped["score"] == 2.345

    # Reject empty IDs
    with pytest.raises(ValidationError):
        SearchResult(
            chunk_id="",
            document_id="doc-1",
            source_id="src-1",
            score=1.0,
            snippet="s",
            content="c",
            index=0,
        )

    # Reject negative index
    with pytest.raises(ValidationError):
        SearchResult(
            chunk_id="c1",
            document_id="d1",
            source_id="s1",
            score=1.0,
            snippet="s",
            content="c",
            index=-1,
        )


def test_lexical_index_invalid_query_types(tmp_path):
    engine = SQLiteStorageEngine(tmp_path / "type_contract.db")
    engine.initialize_schema()
    index = SQLiteLexicalIndex(engine)

    # Non-string queries must return [] safely without raising exceptions
    assert index.search(None) == []  # type: ignore
    assert index.search(123) == []  # type: ignore
    assert index.search(["query"]) == []  # type: ignore

    # Non-string sanitize_query
    assert index.sanitize_query(None) == ""  # type: ignore
    assert index.sanitize_query(456) == ""  # type: ignore
