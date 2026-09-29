import sqlite3

import pytest

from study_engine.contracts.gate2_oracle import Gate2Dataset
from study_engine.diagnostics.gate2_proposals import (
    Gate2ProposalError,
    generate_qrel_proposals,
)


@pytest.fixture
def snapshot(tmp_path):
    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript("""
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT);
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO chunks VALUES ('chunk-a', 'source-a');
        """)
    connection.commit()
    connection.close()
    return database


@pytest.fixture
def dataset():
    return Gate2Dataset.model_validate(
        {
            "version": "fixture",
            "queries": [
                {
                    "query_id": "positive",
                    "scope": "scope-a",
                    "query": "tema",
                    "oracle_type": "positive_in_scope",
                    "qrels_status": "approved",
                },
                {
                    "query_id": "ood",
                    "scope": "scope-a",
                    "query": "ajeno",
                    "oracle_type": "ood_global",
                    "qrels_status": "approved",
                },
                {
                    "query_id": "negative",
                    "scope": "scope-a",
                    "query": "fuera",
                    "oracle_type": "negative_by_scope",
                    "qrels_status": "approved",
                },
            ],
        }
    )


def test_queries_all_oracle_types_but_only_positive_creates_qrels(snapshot, dataset):
    calls = []

    def retriever(query, notebook_id, source_ids, top_k):
        calls.append((query, notebook_id, source_ids, top_k))
        if query == "tema":
            return [{"chunk_id": "chunk-a", "source_id": "source-a", "score": 2.7}]
        return []

    report = generate_qrel_proposals(dataset, snapshot, retriever, top_k=5)

    assert report["qrels"] == {
        "positive": {"chunk-a": 1},
        "ood": {},
        "negative": {},
    }
    assert report["candidate_proposals"]["positive"] == [
        {
            "chunk_id": "chunk-a",
            "source_id": "source-a",
            "rank": 1,
            "retrieval_score": 2.7,
            "authorized_source": True,
            "proposed_grade": 1,
            "grade_status": "pending_human_review",
        }
    ]
    assert report["metadata"]["approved"] is False
    assert report["metadata"]["negative_oracle_checks_executed"] is True
    assert report["observations"]["ood"]["status"] == "global_ood_check"
    assert report["observations"]["ood"]["candidate_absence_passed"] is True
    assert report["observations"]["negative"]["status"] == "scope_isolation_check"
    assert report["observations"]["negative"]["candidate_absence_passed"] is True
    assert calls == [
        ("tema", "scope-a", ["source-a"], 5),
        ("ajeno", "scope-a", ["source-a"], 5),
        ("fuera", "scope-a", ["source-a"], 5),
    ]


def test_rejects_out_of_scope_candidate(snapshot, dataset):
    def retriever(query, notebook_id, source_ids, top_k):
        return [{"chunk_id": "chunk-a", "source_id": "source-b", "score": 1}]

    with pytest.raises(Gate2ProposalError, match="outside scope"):
        generate_qrel_proposals(dataset, snapshot, retriever)


def test_negative_candidates_are_reported_but_never_become_qrels(snapshot, dataset):
    def retriever(query, notebook_id, source_ids, top_k):
        if query == "fuera":
            return [{"chunk_id": "chunk-a", "source_id": "source-a", "score": 2}]
        return []

    report = generate_qrel_proposals(dataset, snapshot, retriever)

    assert report["qrels"]["negative"] == {}
    assert report["observations"]["negative"]["retrieved_chunk_ids"] == ["chunk-a"]
    assert report["observations"]["negative"]["candidate_absence_passed"] is False


def test_unapproved_queries_are_not_sent_to_retriever(snapshot):
    pending = Gate2Dataset.model_validate(
        {
            "version": "fixture",
            "queries": [
                {
                    "query_id": "pending",
                    "scope": "scope-a",
                    "query": "tema sin decisión",
                    "oracle_type": "positive_in_scope",
                    "qrels_status": "pending",
                }
            ],
        }
    )
    calls = []

    def retriever(*args):
        calls.append(args)
        return []

    report = generate_qrel_proposals(pending, snapshot, retriever)

    assert calls == []
    assert report["qrels"] == {"pending": {}}
    assert report["observations"]["pending"]["status"] == "decision_pending"


def test_rejects_missing_chunk_and_unbounded_top_k(snapshot, dataset):
    def missing_retriever(query, notebook_id, source_ids, top_k):
        return [{"chunk_id": "missing", "source_id": "source-a", "score": 1}]

    with pytest.raises(Gate2ProposalError, match="missing chunks"):
        generate_qrel_proposals(dataset, snapshot, missing_retriever)

    with pytest.raises(Gate2ProposalError, match="between 1 and 5"):
        generate_qrel_proposals(dataset, snapshot, missing_retriever, top_k=6)


def test_rejects_more_candidates_than_requested(snapshot, dataset):
    def excessive_retriever(query, notebook_id, source_ids, top_k):
        return [{"chunk_id": "chunk-a", "source_id": "source-a", "score": 1}] * 2

    with pytest.raises(Gate2ProposalError, match="at most 1"):
        generate_qrel_proposals(dataset, snapshot, excessive_retriever, top_k=1)
