"""Folder retrieval scopes must follow explicit notebook-source associations."""

from contextlib import contextmanager
import sqlite3
from typing import Iterator

from study_engine.web.routes.chat import (
    GLOBAL_SCOPE_ID,
    _authorized_sources_for_scope,
    _filter_requested_sources,
    _notebook_ids_for_folder,
)


class _Engine:
    def __init__(self) -> None:
        self.connection = sqlite3.connect(":memory:")
        self.connection.executescript("""
            CREATE TABLE folders (id TEXT PRIMARY KEY, parent_folder_id TEXT);
            CREATE TABLE notebooks (id TEXT PRIMARY KEY, folder_id TEXT);
            CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
            """)
        self.connection.executemany(
            "INSERT INTO folders (id, parent_folder_id) VALUES (?, ?);",
            [
                ("folder_root", None),
                ("roadmap", "folder_root"),
                ("roadmap_fase0", "roadmap"),
                ("fadena", "folder_root"),
                ("fadena_1ano", "fadena"),
                ("fadena_1ano_2cuat", "fadena_1ano"),
            ],
        )
        self.connection.executemany(
            "INSERT INTO notebooks (id, folder_id) VALUES (?, ?);",
            [
                ("fase0-soc", "roadmap_fase0"),
                ("fadena-lenguajes", "fadena_1ano_2cuat"),
            ],
        )
        self.connection.executemany(
            "INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, ?);",
            [
                ("fase0-soc", "source-roadmap"),
                ("fadena-lenguajes", "source-lenguajes"),
            ],
        )
        self.connection.commit()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        yield self.connection


class _Store:
    def __init__(self) -> None:
        self.engine = _Engine()


def test_folder_retrieval_stays_within_explicit_descendant_notebooks() -> None:
    store = _Store()

    assert _notebook_ids_for_folder(store, "roadmap") == ["fase0-soc"]
    assert _notebook_ids_for_folder(store, "fadena") == ["fadena-lenguajes"]
    assert _authorized_sources_for_scope(
        store,
        GLOBAL_SCOPE_ID,
        "roadmap",
    ) == {"source-roadmap"}


def test_active_source_ids_and_hashes_are_intersected_with_scope_allowlist() -> None:
    authorized_sources = {"source-roadmap"}
    source_metadata = {
        "source-roadmap": {"sha256": "hash-roadmap"},
        "source-lenguajes": {"sha256": "hash-lenguajes"},
    }

    assert _filter_requested_sources(
        authorized_sources,
        ["hash-roadmap", "source-lenguajes"],
        source_metadata,
    ) == {"source-roadmap"}
    assert (
        _filter_requested_sources(
            authorized_sources,
            ["source-unknown"],
            source_metadata,
        )
        == set()
    )
    assert (
        _filter_requested_sources(
            authorized_sources,
            [],
            source_metadata,
        )
        == set()
    )
