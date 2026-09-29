import json
from pathlib import Path

import pytest

from study_engine.diagnostics.gate2_facet_coverage import (
    Gate2FacetCoverageError,
    evaluate_facet_coverage,
)

FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "gate2_syn_014_facet_coverage.json"
)
CMP_011_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "gate2_cmp_011_facet_coverage.json"
)


def _fixture(path=FIXTURE):
    return json.loads(path.read_text(encoding="utf-8"))


def _coverage(fixture):
    evidence_grades = {
        row["evidence_id"]: row["proposed_grade"]
        for row in fixture["evidence"]
    }
    return evaluate_facet_coverage(
        fixture["query"]["required_facets"],
        evidence_grades,
        minimum_grade=fixture["query"][
            "minimum_relevance_grade_for_facet_coverage"
        ],
    )


def test_syn_014_fixture_covers_each_required_facet_with_proposed_evidence():
    fixture = _fixture()
    result = _coverage(fixture)
    evidence_by_id = {
        row["evidence_id"]: row for row in fixture["evidence"]
    }

    assert result["all_facets_covered"] is True
    assert result["uncovered_facets"] == []
    for facet in fixture["query"]["required_facets"]:
        assert set(facet["evidence_ids"]).issubset(
            set(facet["expected_chunks"])
        )
    covered_evidence = {
        row["facet_id"]: row["eligible_evidence_ids"]
        for row in result["facets"]
    }
    assert covered_evidence == {
        "invocation_syntax": ["hacking-etico-carlos-tori.pdf:p258:c0000"],
        "core_behavior": [
            "chk_0aa9aa4cc0b2_373_1",
            "chk_0aa9aa4cc0b2_620_1",
        ],
    }
    primary_ids = {
        evidence_id
        for facet in fixture["query"]["required_facets"]
        for evidence_id in facet["evidence_ids"]
    }
    assert {
        evidence_by_id[evidence_id]["source_id"] for evidence_id in primary_ids
    } == {"src_tori_hacking_etico", "src_stallings_computer_security"}
    assert {
        evidence_by_id[evidence_id]["author"] for evidence_id in primary_ids
    } == {"Carlos Tori", "William Stallings"}
    assert (
        evidence_by_id["chk_0aa9aa4cc0b2_373_1"]["source_id"]
        == evidence_by_id["chk_0aa9aa4cc0b2_620_1"]["source_id"]
    )
    assert fixture["set_assessment"]["facet_coverage_proposal"] == (
        "SUFFICIENT_FOR_QUERY_STATED_CORE_FACETS"
    )
    assert fixture["set_assessment"]["canonical_query_decision"] is None
    assert fixture["set_assessment"]["canonical_qrel_decisions"] is None
    assert fixture["set_assessment"]["user_acceptance"] == "PENDING"


def test_uncovered_required_facet_blocks_facet_coverage():
    fixture = _fixture()
    grades = {
        row["evidence_id"]: row["proposed_grade"]
        for row in fixture["evidence"]
    }
    grades["hacking-etico-carlos-tori.pdf:p258:c0000"] = 1

    result = evaluate_facet_coverage(
        fixture["query"]["required_facets"],
        grades,
        minimum_grade=2,
    )

    assert result["all_facets_covered"] is False
    assert result["uncovered_facets"] == ["invocation_syntax"]


def test_cmp_011_fixture_covers_semaphore_but_not_mutex_ownership():
    fixture = _fixture(CMP_011_FIXTURE)
    evidence_grades = {
        row["evidence_id"]: row["adjudicated_grade"]
        for row in fixture["evidence"]
    }

    result = evaluate_facet_coverage(
        fixture["query"]["required_facets"],
        evidence_grades,
        minimum_grade=fixture["query"][
            "minimum_relevance_grade_for_facet_coverage"
        ],
    )

    assert result["all_facets_covered"] is False
    assert result["uncovered_facets"] == ["mutex_thread_ownership"]
    assert {
        row["facet_id"]: row["eligible_evidence_ids"]
        for row in result["facets"]
    } == {
        "mutex_thread_ownership": [],
        "counting_semaphore_operations": ["chk_db97c77518c6_821_1"],
    }
    assert fixture["set_assessment"]["distinct_source_ids"] == 1
    assert fixture["set_assessment"]["sufficient_for_full_query"] is False
    assert fixture["set_assessment"]["fixture_creates_new_decisions"] is False


def test_facet_coverage_uses_only_generic_facet_and_grade_inputs():
    result = evaluate_facet_coverage(
        [
            {"facet_id": "alpha", "evidence_ids": ["item-a"]},
            {"facet_id": "beta", "evidence_ids": ["item-b", "item-c"]},
        ],
        {"item-a": 2, "item-b": 1, "item-c": 0},
        minimum_grade=2,
    )

    assert result == {
        "minimum_grade": 2,
        "facets": [
            {
                "facet_id": "alpha",
                "eligible_evidence_ids": ["item-a"],
                "covered": True,
            },
            {
                "facet_id": "beta",
                "eligible_evidence_ids": [],
                "covered": False,
            },
        ],
        "uncovered_facets": ["beta"],
        "all_facets_covered": False,
    }


def test_unknown_evidence_reference_is_an_explicit_error():
    fixture = _fixture()
    facets = fixture["query"]["required_facets"]
    facets[0]["evidence_ids"] = ["unknown-evidence"]

    with pytest.raises(Gate2FacetCoverageError, match="unknown evidence"):
        _coverage(fixture)


def test_invalid_grades_and_duplicate_facets_are_rejected():
    with pytest.raises(Gate2FacetCoverageError, match="integer from 0 to 3"):
        evaluate_facet_coverage([], {"chunk-a": 4})

    with pytest.raises(Gate2FacetCoverageError, match="Duplicate facet_id"):
        evaluate_facet_coverage(
            [
                {"facet_id": "same", "evidence_ids": ["chunk-a"]},
                {"facet_id": "same", "evidence_ids": ["chunk-a"]},
            ],
            {"chunk-a": 2},
        )
