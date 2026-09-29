import pytest

from study_engine.contracts.gate2_oracle import Gate2Dataset, Gate2OracleType
from study_engine.retrieval.gate2_oracle import (
    Gate2ContractError,
    evaluate_gate2_observations,
    validate_gate2_contract,
)


@pytest.fixture
def gate2_fixture():
    dataset = Gate2Dataset.model_validate(
        {
            "version": "gate2-fixture-1",
            "queries": [
                {
                    "query_id": "positive",
                    "scope": "scope-a",
                    "query": "¿Qué es un puntero?",
                    "oracle_type": "positive_in_scope",
                },
                {
                    "query_id": "ood",
                    "scope": "scope-a",
                    "query": "¿Cuál es la capital de Australia?",
                    "oracle_type": "ood_global",
                },
                {
                    "query_id": "negative",
                    "scope": "scope-a",
                    "query": "¿Cómo funciona el scheduling SJF?",
                    "oracle_type": "negative_by_scope",
                },
            ],
        }
    )
    return dataset, {"chunk-a": "source-a"}, {"scope-a": {"source-a"}}


def test_validates_three_oracles_and_derives_counts(gate2_fixture):
    dataset, chunks, acl = gate2_fixture
    counts = validate_gate2_contract(
        dataset,
        {"positive": {"chunk-a": 2}, "ood": {}, "negative": {}},
        chunks,
        acl,
    )

    assert counts == {
        "total_queries": 3,
        "by_oracle_type": {
            "negative_by_scope": 1,
            "ood_global": 1,
            "positive_in_scope": 1,
        },
        "by_scope": {"scope-a": 3},
        "qrel_queries": 1,
    }


@pytest.mark.parametrize(
    ("query_id", "qrels", "message"),
    [
        ("positive", {}, "must have non-empty qrels"),
        ("ood", {"chunk-a": 1}, "must not have positive qrels"),
        ("negative", {"chunk-a": 1}, "must not have positive qrels"),
    ],
)
def test_rejects_invalid_qrel_shape(gate2_fixture, query_id, qrels, message):
    dataset, chunks, acl = gate2_fixture
    all_qrels = {"positive": {"chunk-a": 2}, "ood": {}, "negative": {}}
    all_qrels[query_id] = qrels

    with pytest.raises(Gate2ContractError, match=message):
        validate_gate2_contract(dataset, all_qrels, chunks, acl)


def test_rejects_missing_qrels_chunk_and_acl_leakage(gate2_fixture):
    dataset, chunks, acl = gate2_fixture
    with pytest.raises(Gate2ContractError, match="Missing qrels"):
        validate_gate2_contract(
            dataset, {"positive": {"chunk-a": 2}, "ood": {}}, chunks, acl
        )

    with pytest.raises(Gate2ContractError, match="missing chunk"):
        validate_gate2_contract(
            dataset,
            {"positive": {"missing": 2}, "ood": {}, "negative": {}},
            chunks,
            acl,
        )

    with pytest.raises(Gate2ContractError, match="outside ACL"):
        validate_gate2_contract(
            dataset,
            {"positive": {"chunk-a": 2}, "ood": {}, "negative": {}},
            {"chunk-a": "source-b"},
            acl,
        )


def test_positive_empty_response_is_not_approval(gate2_fixture):
    dataset, _, _ = gate2_fixture
    report = evaluate_gate2_observations(
        dataset,
        {
            "positive": {"retrieved_chunk_ids": [], "citation_ids": []},
            "ood": {"retrieved_chunk_ids": [], "citation_ids": []},
            "negative": {"retrieved_chunk_ids": [], "citation_ids": []},
        },
    )

    assert report["results"]["positive"]["passed"] is False
    assert report["results"]["ood"]["passed"] is True
    assert report["results"]["negative"]["passed"] is True


def test_negative_and_ood_require_empty_chunks_and_citations(gate2_fixture):
    dataset, _, _ = gate2_fixture
    report = evaluate_gate2_observations(
        dataset,
        {
            "positive": {"retrieved_chunk_ids": ["chunk-a"], "citation_ids": ["chunk-a"]},
            "ood": {"retrieved_chunk_ids": ["chunk-a"], "citation_ids": []},
            "negative": {"retrieved_chunk_ids": [], "citation_ids": ["chunk-a"]},
        },
    )

    assert report["by_oracle_type"][Gate2OracleType.POSITIVE_IN_SCOPE.value] == {
        "total": 1,
        "passed": 1,
    }
    assert report["results"]["ood"]["passed"] is False
    assert report["results"]["negative"]["passed"] is False


def test_scope_change_requires_registered_decision():
    with pytest.raises(ValueError, match="without a decision"):
        Gate2Dataset.model_validate(
            {
                "version": "gate2-fixture-1",
                "queries": [
                    {
                        "query_id": "changed",
                        "scope": "scope-b",
                        "previous_scope": "scope-a",
                        "query": "tema",
                        "oracle_type": "positive_in_scope",
                    }
                ],
            }
        )
