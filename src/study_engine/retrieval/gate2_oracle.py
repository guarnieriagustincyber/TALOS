"""Lightweight, retrieval-free validation and scoring for Gate 2 oracles."""

from collections import Counter
from typing import Any, Dict, Mapping, Set

from study_engine.contracts.gate2_oracle import (
    Gate2Dataset,
    Gate2OracleType,
)


class Gate2ContractError(ValueError):
    """Raised when a Gate 2 dataset or observation violates its contract."""


def validate_gate2_contract(
    dataset: Gate2Dataset,
    qrels: Mapping[str, Mapping[str, int]],
    fixture_chunks: Mapping[str, str],
    acl_by_scope: Mapping[str, Set[str]],
) -> Dict[str, Any]:
    """Validate qrels against a small chunk fixture and return derived counts.

    ``fixture_chunks`` maps chunk IDs to source IDs. No production database or
    retrieval component is accessed by this function.
    """
    query_by_id = {query.query_id: query for query in dataset.queries}
    query_ids = set(query_by_id)
    qrel_ids = set(qrels)
    missing_qrels = sorted(query_ids - qrel_ids)
    unknown_qrels = sorted(qrel_ids - query_ids)
    if missing_qrels:
        raise Gate2ContractError(
            f"Missing qrels for query IDs: {', '.join(missing_qrels)}"
        )
    if unknown_qrels:
        raise Gate2ContractError(
            f"Qrels reference unknown query IDs: {', '.join(unknown_qrels)}"
        )

    counts: Counter[str] = Counter()
    scope_counts: Counter[str] = Counter()
    for query in dataset.queries:
        if query.scope not in acl_by_scope:
            raise Gate2ContractError(
                f"Query {query.query_id!r} uses an unknown ACL scope "
                f"{query.scope!r}"
            )
        records = qrels[query.query_id]
        if not isinstance(records, Mapping):
            raise Gate2ContractError(f"Qrels for {query.query_id!r} must be an object")
        if query.oracle_type == Gate2OracleType.POSITIVE_IN_SCOPE:
            if not records:
                raise Gate2ContractError(
                    f"Positive query {query.query_id!r} must have non-empty qrels"
                )
        elif records:
            raise Gate2ContractError(
                f"{query.oracle_type.value} query {query.query_id!r} "
                "must not have positive qrels"
            )

        authorized_sources = acl_by_scope[query.scope]
        for chunk_id in records:
            if chunk_id not in fixture_chunks:
                raise Gate2ContractError(
                    f"Query {query.query_id!r} references missing chunk {chunk_id!r}"
                )
            if fixture_chunks[chunk_id] not in authorized_sources:
                raise Gate2ContractError(
                    f"Chunk {chunk_id!r} for query {query.query_id!r} is outside "
                    f"ACL scope {query.scope!r}"
                )
        counts[query.oracle_type.value] += 1
        scope_counts[query.scope] += 1

    declared_counts = dataset.metadata.get("counts")
    derived_counts = {
        "total_queries": len(dataset.queries),
        "by_oracle_type": dict(sorted(counts.items())),
        "by_scope": dict(sorted(scope_counts.items())),
        "qrel_queries": sum(bool(qrels[query_id]) for query_id in query_ids),
    }
    if declared_counts is not None and declared_counts != derived_counts:
        raise Gate2ContractError(
            "Dataset metadata counts do not match records; derive counts "
            "from the final dataset"
        )
    return derived_counts


def evaluate_gate2_observations(
    dataset: Gate2Dataset,
    observations: Mapping[str, Mapping[str, list[str]]],
) -> Dict[str, Any]:
    """Score simulated retrieval observations without running retrieval.

    Every observation must contain ``retrieved_chunk_ids`` and ``citation_ids``.
    Positive queries fail on an empty response; both negative classes pass only
    when no chunks and no citations are returned.
    """
    query_by_id = {query.query_id: query for query in dataset.queries}
    unknown = sorted(set(observations) - set(query_by_id))
    if unknown:
        raise Gate2ContractError(
            f"Observations reference unknown query IDs: {', '.join(unknown)}"
        )
    results: Dict[str, Dict[str, Any]] = {}
    by_type: Counter[str] = Counter()
    for query in dataset.queries:
        observation = observations.get(
            query.query_id, {"retrieved_chunk_ids": [], "citation_ids": []}
        )
        retrieved = observation.get("retrieved_chunk_ids")
        citations = observation.get("citation_ids")
        if not isinstance(retrieved, list) or not isinstance(citations, list):
            raise Gate2ContractError(
                f"Observation for {query.query_id!r} must contain list fields"
            )
        if query.oracle_type == Gate2OracleType.POSITIVE_IN_SCOPE:
            passed = bool(retrieved) and bool(citations)
        else:
            passed = not retrieved and not citations
        results[query.query_id] = {
            "oracle_type": query.oracle_type.value,
            "passed": passed,
            "retrieved_count": len(retrieved),
            "citation_count": len(citations),
        }
        by_type[query.oracle_type.value] += int(passed)

    totals = Counter(query.oracle_type.value for query in dataset.queries)
    return {
        "total_queries": len(dataset.queries),
        "passed_queries": sum(
            result["passed"] for result in results.values()
        ),
        "by_oracle_type": {
            oracle_type: {
                "total": totals[oracle_type],
                "passed": by_type[oracle_type],
            }
            for oracle_type in sorted(totals)
        },
        "results": results,
    }
