import json
import sqlite3
from pathlib import Path

import pytest

from study_engine.diagnostics.gate2_evidence_relations import (
    EvidenceRecord,
    Gate2EvidenceRelationError,
    analyze_evidence_relations,
    compare_evidence_records,
    load_evidence_records,
)

ADVERSARIAL_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "gate2_evidence_relations_adversarial.json"
)


def _record(
    evidence_id,
    text,
    *,
    source_id="source-a",
    document_id="document-a",
    author="Author A",
    page_start=10,
    page_end=10,
):
    return EvidenceRecord(
        evidence_id=evidence_id,
        text=text,
        source_id=source_id,
        document_id=document_id,
        author=author,
        page_start=page_start,
        page_end=page_end,
    )


def test_near_duplicate_text_is_a_review_signal_not_an_independence_decision():
    left = _record(
        "chunk-a",
        "A pipe is a FIFO buffer that lets two processes communicate.",
    )
    right = _record(
        "chunk-b",
        "A pipe is a FIFO buffer that lets two processess communicate.",
        page_start=11,
        page_end=11,
    )

    result = compare_evidence_records(left, right)

    assert result["relation"] == "REVIEW_POSSIBLE_DUPLICATE"
    assert result["text_similarity_ratio"] > 0.95
    assert result["simhash_distance"] <= 16
    assert result["provenance"]["same_source_id"] is True
    assert result["provenance"]["overlapping_page_range"] is False
    assert result["independence_decision"] == "NOT_ADJUDICATED"
    assert result["canonical_decision"] is None
    assert result["human_review_required"] is True


def test_same_page_provenance_is_reported_without_claiming_duplicate_text():
    left = _record("chunk-a", "A pipe transfers data between processes.")
    right = _record("chunk-b", "The scheduler chooses a runnable process.")

    result = compare_evidence_records(left, right)

    assert result["provenance"]["overlapping_page_range"] is True
    assert result["relation"] == "REVIEW_SHARED_PROVENANCE"
    assert result["independence_decision"] == "NOT_ADJUDICATED"


def test_overlapping_pages_detected_when_document_ids_differ_within_source():
    left = _record("chunk-a", "A passage about pipes.", document_id="doc-a")
    right = _record(
        "chunk-b",
        "A different extraction from the same page.",
        document_id="doc-b",
    )

    result = compare_evidence_records(left, right)

    assert result["provenance"]["same_source_id"] is True
    assert result["provenance"]["same_document"] is False
    assert result["provenance"]["overlapping_page_range"] is True
    assert result["relation"] == "REVIEW_SHARED_PROVENANCE"
    assert result["independence_decision"] == "NOT_ADJUDICATED"


def test_identical_text_across_sources_stays_unadjudicated():
    left = _record(
        "chunk-a",
        "The pipe is a circular FIFO buffer.",
        source_id="a",
    )
    right = _record(
        "chunk-b",
        "The pipe is a circular FIFO buffer.",
        source_id="b",
        document_id="document-b",
        author="Author B",
        page_start=4,
        page_end=4,
    )

    result = compare_evidence_records(left, right)

    assert result["relation"] == "REVIEW_POSSIBLE_DUPLICATE"
    assert result["provenance"]["same_source_id"] is False
    assert result["provenance"]["same_author"] is False
    assert result["independence_decision"] == "NOT_ADJUDICATED"


def test_analysis_returns_each_pair_and_keeps_human_review_boundary():
    records = [
        _record("chunk-a", "Identical content for pair comparison."),
        _record("chunk-b", "Identical content for pair comparison."),
        _record(
            "chunk-c",
            "Different passage describing a process scheduler.",
            document_id="document-c",
            source_id="source-c",
        ),
    ]

    result = analyze_evidence_relations(records)

    assert len(result["pairs"]) == 3
    assert result["pairs"][2]["relation"] == (
        "NO_STRONG_TEXT_DUPLICATE_SIGNAL"
    )
    assert result["independence_adjudication"] == "NOT_PERFORMED"
    assert result["qrel_actions"] == "NOT_PRODUCED"
    assert result["canonical_decision"] is None
    assert result["human_review_required"] is True


def test_invalid_records_and_thresholds_raise_errors():
    with pytest.raises(
        Gate2EvidenceRelationError,
        match="text must be non-empty",
    ):
        compare_evidence_records(_record("a", " "), _record("b", "text"))

    with pytest.raises(
        Gate2EvidenceRelationError,
        match="word token",
    ):
        analyze_evidence_relations([_record("punctuation", "!!!")])

    with pytest.raises(
        Gate2EvidenceRelationError,
        match="EvidenceRecord",
    ):
        analyze_evidence_relations([object()])

    too_many = [
        _record(f"chunk-{index}", "A passage.")
        for index in range(101)
    ]
    with pytest.raises(Gate2EvidenceRelationError, match="At most 100"):
        analyze_evidence_relations(too_many)

    with pytest.raises(
        Gate2EvidenceRelationError, match="minimum_text_similarity"
    ):
        analyze_evidence_relations([], minimum_text_similarity=float("nan"))

    with pytest.raises(
        Gate2EvidenceRelationError, match="maximum_simhash_distance"
    ):
        analyze_evidence_relations([], maximum_simhash_distance=True)

    record = _record("same-id", "text")
    with pytest.raises(Gate2EvidenceRelationError, match="unique"):
        analyze_evidence_relations([record, record])


def test_loader_reads_selected_chunks_read_only_in_requested_order(tmp_path):
    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY,
            author TEXT
        );
        CREATE TABLE chunks (
            id TEXT PRIMARY KEY,
            content TEXT NOT NULL,
            source_id TEXT NOT NULL,
            document_id TEXT NOT NULL,
            page_start INTEGER,
            page_end INTEGER
        );
        INSERT INTO sources VALUES ('source-a', 'Author A');
        INSERT INTO chunks VALUES (
            'chunk-a', 'First passage text.', 'source-a', 'document-a', 2, 2
        );
        INSERT INTO chunks VALUES (
            'chunk-b', 'Second passage text.', 'source-a', 'document-a', 3, 3
        );
        """
    )
    connection.commit()
    connection.close()

    records = load_evidence_records(database, ["chunk-b", "chunk-a"])

    assert [record.evidence_id for record in records] == [
        "chunk-b",
        "chunk-a",
    ]
    assert records[0].author == "Author A"
    assert records[0].page_start == 3
    with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as readonly:
        count = readonly.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    assert count == 2

    with pytest.raises(Gate2EvidenceRelationError, match="not found"):
        load_evidence_records(database, ["missing"])


def _adversarial_cases(split):
    fixture = json.loads(ADVERSARIAL_FIXTURE.read_text(encoding="utf-8"))
    return [
        case for case in fixture["cases"] if case["split"] == split
    ]


def _fixture_record(data):
    return EvidenceRecord(**data)


@pytest.mark.parametrize(
    "case",
    _adversarial_cases("development"),
    ids=lambda case: case["case_id"],
)
def test_adversarial_development_pairs_match_diagnostic_contract(case):
    result = compare_evidence_records(
        _fixture_record(case["left"]),
        _fixture_record(case["right"]),
    )

    assert result["relation"] == case["expected_relation_signal"]
    assert result["provenance"]["same_source_id"] is (
        case["same_source_expected"]
    )
    assert result["provenance"]["overlapping_page_range"] is (
        case["page_overlap_expected"]
    )
    assert (
        result["text_similarity_ratio"] >= 0.88
    ) is case["text_similarity_signal_expected"]
    if "token_set_similarity_expected_at_least" in case:
        assert result["token_set_similarity_ratio"] >= case[
            "token_set_similarity_expected_at_least"
        ]
    assert result["independence_decision"] == "NOT_ADJUDICATED"
    assert result["qrel_actions"] == "NOT_PRODUCED"
    assert result["canonical_decision"] is None
    assert result["human_review_required"] is True
    assert "semantic_relation" not in result
    assert not {
        "grade",
        "accepted",
        "included",
        "qrel_decision",
    }.intersection(result)


@pytest.mark.parametrize(
    "case",
    _adversarial_cases("holdout"),
    ids=lambda case: case["case_id"],
)
def test_adversarial_holdout_pairs_are_checked_without_semantic_outputs(case):
    result = compare_evidence_records(
        _fixture_record(case["left"]),
        _fixture_record(case["right"]),
    )

    assert result["relation"] == case["expected_relation_signal"]
    assert result["provenance"]["same_source_id"] is (
        case["same_source_expected"]
    )
    assert result["provenance"]["overlapping_page_range"] is (
        case["page_overlap_expected"]
    )
    assert (
        result["text_similarity_ratio"] >= 0.88
    ) is case["text_similarity_signal_expected"]
    assert result["independence_decision"] == "NOT_ADJUDICATED"
    assert result["qrel_actions"] == "NOT_PRODUCED"
    assert result["canonical_decision"] is None
    assert "semantic_relation" not in result


def test_adversarial_fixture_keeps_qrel_authority_outside_tool_contract():
    fixture = json.loads(ADVERSARIAL_FIXTURE.read_text(encoding="utf-8"))
    assert fixture["qrel_mutation_expected"] is False

    output = analyze_evidence_relations(
        [
            _fixture_record(fixture["cases"][0]["left"]),
            _fixture_record(fixture["cases"][0]["right"]),
        ]
    )

    assert output["qrel_actions"] == "NOT_PRODUCED"
    assert output["canonical_decision"] is None
    assert output["independence_adjudication"] == "NOT_PERFORMED"
    assert all(
        pair["qrel_actions"] == "NOT_PRODUCED" for pair in output["pairs"]
    )
