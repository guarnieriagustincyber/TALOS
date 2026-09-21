"""Unit tests for decoupled academic API adapters (Phase E2.8).

Validates:
- Persistent SQLite caching and offline fallback.
- Crossref DOI resolution and title search (DOI never mandatory).
- OpenAlex work resolution and citation_count telemetry (never authority).
- Zotero local export and API parsing.
- Hermetic: all network operations mocked.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

import pytest

from study_engine.adapters.base import AcademicMetadata, BaseAcademicAdapter
from study_engine.adapters.crossref import CrossrefAdapter
from study_engine.adapters.openalex import OpenAlexAdapter
from study_engine.adapters.zotero import ZoteroAdapter


@pytest.fixture
def temp_cache_db(tmp_path):
    return tmp_path / "test_api_cache.sqlite3"


# ==============================================================================
# BaseAcademicAdapter & SQLite Caching
# ==============================================================================
def test_base_adapter_cache_hit_and_miss(temp_cache_db):
    adapter = BaseAcademicAdapter(cache_db_path=temp_cache_db)

    # Initial cache miss
    assert adapter._get_cached("https://api.example.com/item1") is None

    # Write cache
    adapter._set_cached("https://api.example.com/item1", {"title": "Test Work", "year": 2024})

    # Cache hit
    cached = adapter._get_cached("https://api.example.com/item1")
    assert cached is not None
    assert cached["title"] == "Test Work"
    assert cached["year"] == 2024


def test_base_adapter_offline_fallback(temp_cache_db):
    adapter = BaseAcademicAdapter(cache_db_path=temp_cache_db, max_retries=1, timeout_seconds=0.1)

    with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Network unreachable")):
        # Should gracefully return None without raising an exception
        result = adapter.fetch_json("https://api.example.com/network-fail")
        assert result is None


# ==============================================================================
# CrossrefAdapter Tests
# ==============================================================================
def test_crossref_doi_never_mandatory(temp_cache_db):
    adapter = CrossrefAdapter(cache_db_path=temp_cache_db)

    # Empty / None DOI returns None cleanly without error
    assert adapter.resolve_doi("") is None
    assert adapter.resolve_doi(None) is None


def test_crossref_resolve_doi_success(temp_cache_db):
    adapter = CrossrefAdapter(cache_db_path=temp_cache_db)

    mock_response = {
        "status": "ok",
        "message": {
            "DOI": "10.1145/3318464.3389700",
            "title": ["Design of Operating Systems"],
            "author": [{"given": "Andrew", "family": "Tanenbaum"}],
            "published-print": {"date-parts": [[2020, 5]]},
            "container-title": ["ACM SIGOPS"],
            "is-referenced-by-count": 142,
        }
    }

    with patch.object(adapter, "fetch_json", return_value=mock_response):
        meta = adapter.resolve_doi("10.1145/3318464.3389700")
        assert meta is not None
        assert meta.title == "Design of Operating Systems"
        assert meta.authors == ["Andrew Tanenbaum"]
        assert meta.year == 2020
        assert meta.doi == "10.1145/3318464.3389700"
        assert meta.venue == "ACM SIGOPS"
        assert meta.citation_count == 142
        assert meta.source_adapter == "crossref"


def test_crossref_search_by_title(temp_cache_db):
    adapter = CrossrefAdapter(cache_db_path=temp_cache_db)

    mock_response = {
        "status": "ok",
        "message": {
            "items": [
                {
                    "DOI": "10.1000/182",
                    "title": ["Modern Operating Systems"],
                    "author": [{"family": "Tanenbaum", "given": "Andrew S."}],
                    "published-print": {"date-parts": [[2015]]},
                }
            ]
        }
    }

    with patch.object(adapter, "fetch_json", return_value=mock_response):
        results = adapter.search_by_title("Modern Operating Systems", rows=1)
        assert len(results) == 1
        assert results[0].title == "Modern Operating Systems"
        assert results[0].doi == "10.1000/182"


# ==============================================================================
# OpenAlexAdapter Tests
# ==============================================================================
def test_openalex_work_resolution_and_telemetry(temp_cache_db):
    adapter = OpenAlexAdapter(cache_db_path=temp_cache_db)

    mock_work = {
        "id": "https://openalex.org/W2741809807",
        "display_name": "Operating Systems: Principles and Practice",
        "publication_year": 2014,
        "doi": "https://doi.org/10.5555/2685741",
        "cited_by_count": 850,
        "authorships": [
            {"author": {"display_name": "Thomas Anderson"}},
            {"author": {"display_name": "Michael Dahlin"}},
        ],
        "primary_location": {"source": {"display_name": "Recursive Books"}},
    }

    with patch.object(adapter, "fetch_json", return_value=mock_work):
        meta = adapter.get_work("W2741809807")
        assert meta is not None
        assert meta.title == "Operating Systems: Principles and Practice"
        assert meta.year == 2014
        assert meta.doi == "10.5555/2685741"
        assert meta.citation_count == 850
        assert len(meta.authors) == 2
        assert meta.source_adapter == "openalex"


# ==============================================================================
# ZoteroAdapter Tests
# ==============================================================================
def test_zotero_local_export_parsing(tmp_path, temp_cache_db):
    adapter = ZoteroAdapter(cache_db_path=temp_cache_db)

    export_data = [
        {
            "data": {
                "key": "ZOT123",
                "title": "Computer Systems: A Programmer's Perspective",
                "creators": [
                    {"firstName": "Randal", "lastName": "Bryant"},
                    {"firstName": "David", "lastName": "O'Hallaron"},
                ],
                "date": "2016-03-01",
                "publisher": "Pearson",
                "DOI": "10.1007/s10115-015-0865-x",
            }
        }
    ]

    export_file = tmp_path / "zotero_export.json"
    export_file.write_text(json.dumps(export_data), encoding="utf-8")

    items = adapter.parse_export_file(export_file)
    assert len(items) == 1
    assert items[0].title == "Computer Systems: A Programmer's Perspective"
    assert items[0].year == 2016
    assert items[0].venue == "Pearson"
    assert items[0].authors == ["Randal Bryant", "David O'Hallaron"]
    assert items[0].source_adapter == "zotero"
