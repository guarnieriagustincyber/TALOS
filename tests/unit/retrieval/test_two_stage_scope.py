"""Two-stage FTS retrieval must fail closed and retain source filters."""

from contextlib import contextmanager
import logging
import sqlite3

from study_engine.retrieval.two_stage import TwoStageRetriever


class _Cursor:
    def __init__(self, rows=()) -> None:
        self.rows = rows
        self.query = ""
        self.params = ()

    def execute(self, query: str, params: tuple) -> None:
        self.query = query
        self.params = params

    def fetchall(self):
        return self.rows


class _Connection:
    def __init__(self, cursor: _Cursor) -> None:
        self._cursor = cursor

    def cursor(self) -> _Cursor:
        return self._cursor


class _Engine:
    def __init__(self, cursor: _Cursor = None, error: Exception = None) -> None:
        self._cursor = cursor
        self._error = error

    @contextmanager
    def transaction(self):
        if self._error is not None:
            raise self._error
        yield _Connection(self._cursor)


class _Store:
    def __init__(self, engine: _Engine) -> None:
        self.engine = engine


def _retriever(engine: _Engine) -> TwoStageRetriever:
    retriever = object.__new__(TwoStageRetriever)
    retriever.store = _Store(engine)
    return retriever


def test_fts_prefilter_preserves_source_filter_in_sql() -> None:
    cursor = _Cursor(
        rows=[
            (
                "allowed-chunk",
                "doc-1",
                "source-allowed",
                "matching content",
                1,
                1,
                0,
                "{}",
                -1.0,
            )
        ]
    )

    candidates = _retriever(_Engine(cursor))._fts5_prefilter(
        query="matching content",
        notebook_id="notebook-a",
        limit=10,
        source_filter=["source-allowed"],
    )

    assert len(candidates) == 1
    assert candidates[0]["source_id"] == "source-allowed"
    assert "c.source_id IN (?)" in cursor.query
    assert cursor.params == ("notebook-a", "matching OR content", "source-allowed", 10)


def test_fts_prefilter_returns_no_candidates_on_sql_failure(
    caplog,
) -> None:
    retriever = _retriever(
        _Engine(error=sqlite3.OperationalError("missing or invalid scope join"))
    )

    with caplog.at_level(logging.ERROR):
        candidates = retriever._fts5_prefilter(
            query="matching content",
            notebook_id="notebook-a",
            limit=10,
        )

    assert candidates == []
    assert "refusing unscoped fallback" in caplog.text


def test_fts_prefilter_empty_source_allowlist_is_empty() -> None:
    retriever = _retriever(
        _Engine(error=AssertionError("An empty source allowlist must not query"))
    )

    assert (
        retriever._fts5_prefilter(
            query="matching content",
            notebook_id="notebook-a",
            limit=10,
            source_filter=[],
        )
        == []
    )
