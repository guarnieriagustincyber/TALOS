import json
import sqlite3

import pytest

from study_engine.diagnostics.gate2_segment_validation import (
    Gate2SegmentValidationError,
    validate_gate2_segments,
)


def _write_database(path):
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT, content TEXT);
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO notebook_sources VALUES ('scope-b', 'source-b');
        INSERT INTO chunks VALUES ('chunk-a', 'source-a', 'Direct evidence');
        INSERT INTO chunks VALUES ('chunk-b', 'source-b', 'Partial evidence');
        """)
    connection.commit()
    connection.close()


def _write_inputs(tmp_path, qrel_for_scope_a=None):
    database = tmp_path / "knowledge.db"
    _write_database(database)
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "version": "fixture-v1",
                "metadata": {
                    "counts": {
                        "total_queries": 3,
                        "by_oracle_type": {
                            "negative_by_scope": 1,
                            "ood_global": 1,
                            "positive_in_scope": 1,
                        },
                        "by_scope": {"scope-a": 2, "scope-b": 1},
                        "qrel_queries": 1,
                    }
                },
                "queries": [
                    {
                        "query_id": "positive-a",
                        "query": "Direct?",
                        "scope": "scope-a",
                        "oracle_type": "positive_in_scope",
                        "qrels_status": "approved",
                        "qrels_provenance": "human_verified",
                    },
                    {
                        "query_id": "ood-a",
                        "query": "OOD?",
                        "scope": "scope-a",
                        "oracle_type": "ood_global",
                        "qrels_status": "approved",
                        "qrels_provenance": "historical",
                    },
                    {
                        "query_id": "negative-b",
                        "query": "Out of scope?",
                        "scope": "scope-b",
                        "oracle_type": "negative_by_scope",
                        "qrels_status": "approved",
                        "qrels_provenance": "historical",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(
        json.dumps(
            {
                "qrels": {
                    "positive-a": (
                        qrel_for_scope_a
                        if qrel_for_scope_a is not None
                        else {"chunk-a": 3}
                    ),
                    "ood-a": {},
                    "negative-b": {},
                }
            }
        ),
        encoding="utf-8",
    )
    return dataset, qrels, database


def test_reports_segments_by_scope_and_oracle_read_only(tmp_path):
    dataset, qrels, database = _write_inputs(tmp_path)
    before = database.read_bytes()

    report = validate_gate2_segments(dataset, qrels, database)

    assert report["status"] == "passed"
    assert report["retrieval_executed"] is False
    assert report["release_eligible"] is True
    assert report["pending_adjudication_query_ids"] == []
    assert report["counts"]["total_queries"] == 3
    assert report["counts"]["qrel_queries"] == 1
    assert len(report["segments"]) == 3
    positive = next(
        row for row in report["segments"] if row["oracle_type"] == "positive_in_scope"
    )
    assert positive["scope"] == "scope-a"
    assert positive["qrel_grade_counts"] == {"3": 1}
    assert positive["qrels_provenance_counts"] == {"human_verified": 1}
    assert database.read_bytes() == before


def test_pending_qrel_proposal_passes_structure_but_is_not_release_eligible(
    tmp_path,
):
    dataset, qrels, database = _write_inputs(tmp_path)
    payload = json.loads(dataset.read_text())
    payload["queries"][0]["qrels_status"] = "pending"
    payload["queries"][0]["qrels_provenance"] = "adjudication_proposal"
    dataset.write_text(json.dumps(payload), encoding="utf-8")

    report = validate_gate2_segments(dataset, qrels, database)

    assert report["status"] == "passed"
    assert report["release_eligible"] is False
    assert report["pending_adjudication_query_ids"] == ["positive-a"]


def test_rejects_cross_scope_qrel(tmp_path):
    dataset, qrels, database = _write_inputs(tmp_path, {"chunk-b": 2})

    with pytest.raises(Gate2SegmentValidationError, match="outside ACL"):
        validate_gate2_segments(dataset, qrels, database)


def test_rejects_qrel_grades_outside_approved_scale(tmp_path):
    dataset, qrels, database = _write_inputs(tmp_path, {"chunk-a": 4})

    with pytest.raises(Gate2SegmentValidationError, match="between 1 and 3"):
        validate_gate2_segments(dataset, qrels, database)
