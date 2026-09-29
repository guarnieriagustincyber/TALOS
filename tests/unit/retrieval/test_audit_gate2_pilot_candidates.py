import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3] / "scripts" / "audit_gate2_pilot_candidates.py"
)
SPEC = importlib.util.spec_from_file_location("audit_gate2_pilot_candidates", SCRIPT)
assert SPEC and SPEC.loader
auditor = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auditor)


def test_anchor_matching_ignores_case_and_diacritics():
    assert auditor._anchor_matches(
        "La planificación Round-Robin usa un quantum temporal.",
        ["round robin", "quantum", "MÉXICO"],
    ) == ["round robin", "quantum"]


def test_anchor_matching_rejects_broad_word_in_unrelated_context():
    assert (
        auditor._anchor_matches(
            "La comunidad informática mundial revisó el currículo.",
            ["final del mundial", "mundial de méxico 1986", "argentina", "alemania"],
        )
        == []
    )


def test_audits_retrieval_and_historical_qrels_read_only(tmp_path):
    import sqlite3

    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript("""
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE sources (source_id TEXT PRIMARY KEY, title TEXT NOT NULL);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT, content TEXT);
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO sources VALUES ('source-a', 'Operating Systems');
        INSERT INTO chunks VALUES ('relevant', 'source-a', 'Round Robin quantum scheduling');
        INSERT INTO chunks VALUES ('noise', 'source-a', 'La planificación usa colas de prioridad');
        """)
    connection.commit()
    connection.close()
    before = (database.read_bytes(), database.stat().st_mtime_ns)

    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "golden_set_version": "fixture",
                "queries": [
                    {
                        "query_id": "q1",
                        "oracle_type": "negative_by_scope",
                        "scope": "scope-a",
                        "topic_anchors": ["round robin", "quantum"],
                    }
                ],
            }
        )
    )
    observations = tmp_path / "observations.json"
    observations.write_text(
        json.dumps(
            {
                "observations": {"q1": {"retrieved_chunk_ids": ["noise"]}},
                "candidate_proposals": {},
            }
        )
    )
    qrels = tmp_path / "historical-qrels.json"
    qrels.write_text(json.dumps({"qrels": {"q1": {"relevant": 2, "missing": 1}}}))

    report = auditor.audit_candidates(dataset, observations, database, qrels)

    query = report["queries"][0]
    assert query["retrieved_candidate_count"] == 1
    assert query["topic_supported_candidate_count"] == 0
    assert query["irrelevant_candidate_count"] == 1
    historical = {row["chunk_id"]: row for row in query["historical_qrels"]}
    assert historical["relevant"]["topic_supported"] is True
    assert historical["relevant"]["authorized"] is True
    assert historical["missing"]["exists"] is False
    assert historical["missing"]["adjudication_recommendation"] == (
        "review_remove_as_unrelated_qrel"
    )
    assert (database.read_bytes(), database.stat().st_mtime_ns) == before


def test_rejects_missing_observations(tmp_path):
    import sqlite3

    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "q1",
                        "oracle_type": "ood_global",
                        "scope": "scope-a",
                        "topic_anchors": ["mundial"],
                    }
                ]
            }
        )
    )
    observations = tmp_path / "observations.json"
    observations.write_text(json.dumps({"observations": {}, "candidate_proposals": {}}))
    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript("""
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE sources (source_id TEXT PRIMARY KEY, title TEXT NOT NULL);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT, content TEXT);
        """)
    connection.commit()
    connection.close()
    with pytest.raises(auditor.Gate2CandidateAuditError, match="Missing observation"):
        auditor.audit_candidates(dataset, observations, database)
