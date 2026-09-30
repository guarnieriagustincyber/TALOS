#!/usr/bin/env python3
"""Validate adversarial, synthetic backend-selection contract fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "tests/fixtures/backend_selection"

ChunkKey = tuple[str, str]


def build_pool(
    backend_a: Iterable[ChunkKey],
    backend_b: Iterable[ChunkKey],
    lexical: Iterable[ChunkKey],
    authorized_scopes: set[str],
    top_n: int,
    top_m: int,
) -> dict[ChunkKey, tuple[str, ...]]:
    if top_n < 0 or top_m < 0:
        raise ValueError("pool cutoffs must not be negative")
    candidates: dict[ChunkKey, set[str]] = {}
    for source, values, limit in (
        ("backend_a", backend_a, top_n),
        ("backend_b", backend_b, top_n),
        ("lexical", lexical, top_m),
    ):
        values = list(values)
        if any(notebook_id not in authorized_scopes for notebook_id, _ in values):
            raise ValueError(f"{source} returned a candidate outside authorized scope")
        source_unique = []
        source_seen: set[ChunkKey] = set()
        for key in values:
            if key not in source_seen:
                source_unique.append(key)
                source_seen.add(key)
        for notebook_id, chunk_id in source_unique[:limit]:
            if notebook_id not in authorized_scopes:
                raise ValueError(f"candidate outside authorized scope: {notebook_id}")
            candidates.setdefault((notebook_id, chunk_id), set()).add(source)
    return {
        key: tuple(sorted(candidates[key]))
        for key in sorted(candidates)
    }


def validate_judgments(
    judgments: list[dict],
    authorized_scopes: set[str],
    corpus_keys: set[ChunkKey],
    ood: bool,
) -> None:
    seen: set[ChunkKey] = set()
    for judgment in judgments:
        key = (judgment["notebook_id"], judgment["chunk_id"])
        if key[0] not in authorized_scopes:
            raise ValueError(f"qrel outside authorized scope: {key}")
        if key not in corpus_keys:
            raise ValueError(f"qrel points outside corpus: {key}")
        if key in seen:
            raise ValueError(f"duplicate qrel: {key}")
        seen.add(key)
        grade = judgment["grade"]
        if type(grade) is not int or grade not in {0, 1, 2, 3}:
            raise ValueError(f"invalid relevance grade: {grade!r}")
        if ood and grade > 0:
            raise ValueError("OOD query cannot have positive ranking qrels")


def evaluate_ranking(
    ranking: list[ChunkKey],
    query_scope: set[str],
    judgments: list[dict],
    judgment_status: str,
    k: int,
    pool: set[ChunkKey],
) -> dict:
    if k < 1:
        raise ValueError("k must be positive")
    if judgment_status == "INCONSISTENT":
        return {"status": "INVALID_BENCHMARK", "reason": "INCONSISTENT_QRELS"}
    if judgment_status != "EXHAUSTIVELY_JUDGED":
        return {"status": "INCONCLUSIVE", "reason": "QRELS_NOT_EXHAUSTIVE"}
    seen: set[ChunkKey] = set()
    deduplicated: list[ChunkKey] = []
    for key in ranking:
        if key[0] not in query_scope:
            return {"status": "INVALID_BENCHMARK", "reason": "SCOPE_VIOLATION"}
        if key not in pool:
            return {"status": "INCONCLUSIVE", "reason": "UNJUDGED_RESULT"}
        if key not in seen:
            seen.add(key)
            deduplicated.append(key)
    relevant = {
        (item["notebook_id"], item["chunk_id"])
        for item in judgments
        if item["grade"] >= 2 and item["notebook_id"] in query_scope
    }
    if not relevant:
        return {"status": "INCONCLUSIVE", "reason": "NO_POSITIVE_QRELS"}
    top = deduplicated[:k]
    recovered = len(set(top) & relevant)
    return {
        "status": "COMPARABLE",
        "recall_at_k": recovered / len(relevant),
        "precision_at_k": recovered / k,
        "recall_denominator": len(relevant),
        "ranking_count": len(top),
    }


def evaluate_ood(abstention_expected: bool, citation_count: int) -> dict:
    if citation_count < 0:
        raise ValueError("citation count must not be negative")
    abstained = citation_count == 0
    return {
        "status": "OOD_EVALUATED_SEPARATELY",
        "correct_abstention": abstention_expected == abstained,
        "false_citations": citation_count if abstention_expected else 0,
    }


def resource_summary(
    baseline_rss_mib: float,
    backend_total_rss_mib: float,
    ram_limit_mib: float | None,
    cpu_seconds_per_query: float,
    cpu_limit_seconds_per_query: float | None,
) -> dict:
    if min(baseline_rss_mib, backend_total_rss_mib, cpu_seconds_per_query) < 0:
        raise ValueError("resource measurements must not be negative")
    return {
        "rss_baseline_mib": baseline_rss_mib,
        "rss_total_backend_mib": backend_total_rss_mib,
        "rss_delta_backend_mib": backend_total_rss_mib - baseline_rss_mib,
        "ram_status": (
            "UNASSESSED"
            if ram_limit_mib is None
            else (
                "PASS"
                if backend_total_rss_mib <= ram_limit_mib
                else "FAIL"
            )
        ),
        "cpu_seconds_per_query": cpu_seconds_per_query,
        "cpu_status": (
            "UNASSESSED"
            if cpu_limit_seconds_per_query is None
            else (
                "PASS"
                if cpu_seconds_per_query <= cpu_limit_seconds_per_query
                else "FAIL"
            )
        ),
    }


def validate_fixtures() -> int:
    cases = json.loads(
        (FIXTURE_DIR / "adversarial_cases.json").read_text(encoding="utf-8")
    )
    queries = json.loads(
        (FIXTURE_DIR / "miniature_queries.json").read_text(encoding="utf-8")
    )
    qrels = json.loads(
        (FIXTURE_DIR / "miniature_qrels.json").read_text(encoding="utf-8")
    )
    if not all(
        item.get("synthetic_only") is True
        for item in (cases, queries, qrels)
    ):
        raise ValueError("all adversarial inputs must be synthetic")
    expected_cases = {
        "query_without_positive",
        "ood_query",
        "multi_scope_query",
        "candidate_outside_pool",
        "duplicate_pool_candidates",
        "partial_judgment",
        "unknown_not_zero",
        "wrong_scope_result",
        "ranking_shorter_than_k",
        "unpooled_result_at_evaluation",
        "lexical_pool_duplicates_and_short_source",
        "recall_denominator_per_query",
        "rss_baseline_and_delta",
        "cpu_without_threshold",
        "inconsistent_qrels",
    }
    if {item["name"] for item in cases["cases"]} != expected_cases:
        raise ValueError("adversarial case inventory does not match contract")

    corpus_keys = {
        (item["notebook_id"], item["chunk_id"])
        for item in queries["corpus"]
    }
    query_map = {item["query_id"]: item for item in queries["queries"]}
    qrel_map = qrels["qrels"]
    if set(query_map) != set(qrel_map):
        raise ValueError("query and qrel IDs must match exactly")
    if len(query_map) != len(queries["queries"]):
        raise ValueError("query IDs must be unique")
    if len(corpus_keys) != len(queries["corpus"]):
        raise ValueError("scoped corpus keys must be unique")

    for query_id, query in query_map.items():
        state = query["judgment_status"]
        if state not in qrels["judgment_states"]:
            raise ValueError(f"{query_id}: invalid judgment status {state}")
        entry = qrel_map[query_id]
        if entry["status"] != state:
            raise ValueError(f"{query_id}: query/qrel judgment states differ")
        try:
            validate_judgments(
                entry["judgments"],
                set(query["notebook_scope"]),
                corpus_keys,
                query["category"] == "ood",
            )
        except ValueError:
            if state != "INCONSISTENT":
                raise
        else:
            if state == "INCONSISTENT":
                raise AssertionError(
                    f"{query_id}: fixture marked inconsistent but validates"
                )
        if entry["pool_size"] < len(entry["judgments"]):
            raise ValueError(f"{query_id}: judgments exceed candidate pool size")
        if (
            state == "EXHAUSTIVELY_JUDGED"
            and entry["pool_size"] != len(entry["judgments"])
        ):
            raise ValueError(f"{query_id}: exhaustive pool has unjudged candidates")
        if state == "UNJUDGED" and entry["judgments"]:
            raise ValueError(f"{query_id}: UNJUDGED query contains judgments")
        if (
            state == "PARTIALLY_JUDGED"
            and entry["pool_size"] <= len(entry["judgments"])
        ):
            raise ValueError(f"{query_id}: partial pool has no unjudged candidates")

    pool = build_pool(
        [
            ("synthetic-os", "SYN-CHUNK-001"),
            ("synthetic-os", "SYN-CHUNK-001"),
            ("synthetic-os", "SYN-CHUNK-002"),
            ("synthetic-os", "SYN-CHUNK-004"),
        ],
        [("synthetic-os", "SYN-CHUNK-001")],
        [
            ("synthetic-os", "SYN-CHUNK-001"),
            ("synthetic-os", "SYN-CHUNK-001"),
            ("synthetic-os", "SYN-CHUNK-003"),
        ],
        {"synthetic-os"},
        top_n=2,
        top_m=2,
    )
    assert pool == {
        ("synthetic-os", "SYN-CHUNK-001"): ("backend_a", "backend_b", "lexical"),
        ("synthetic-os", "SYN-CHUNK-002"): ("backend_a",),
        ("synthetic-os", "SYN-CHUNK-003"): ("lexical",),
    }
    try:
        build_pool(
            [],
            [],
            [("synthetic-code", "SYN-CHUNK-006")],
            {"synthetic-os"},
            top_n=2,
            top_m=2,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("lexical candidate outside scope must fail closed")

    multi = qrel_map["SYN-MULTISCOPE-001"]["judgments"]
    multi_result = evaluate_ranking(
        [("synthetic-os", "SYN-CHUNK-007")],
        {"synthetic-os", "synthetic-code"},
        multi,
        "EXHAUSTIVELY_JUDGED",
        1,
        {
            ("synthetic-os", "SYN-CHUNK-007"),
            ("synthetic-code", "SYN-CHUNK-008"),
        },
    )
    assert multi_result["recall_denominator"] == 2
    assert multi_result["recall_at_k"] == 0.5
    assert multi_result["precision_at_k"] == 1.0

    short = evaluate_ranking(
        [("synthetic-os", "SYN-CHUNK-001")],
        {"synthetic-os"},
        qrel_map["SYN-CONCEPT-001"]["judgments"],
        "EXHAUSTIVELY_JUDGED",
        3,
        {
            ("synthetic-os", "SYN-CHUNK-001"),
            ("synthetic-os", "SYN-CHUNK-002"),
        },
    )
    assert short["precision_at_k"] == 1 / 3
    assert short["recall_denominator"] == 2

    incomplete = evaluate_ranking(
        [],
        {"synthetic-os"},
        qrel_map["SYN-UNKNOWN-001"]["judgments"],
        "UNJUDGED",
        5,
        set(),
    )
    partial = evaluate_ranking(
        [],
        {"synthetic-os"},
        qrel_map["SYN-PARTIAL-001"]["judgments"],
        "PARTIALLY_JUDGED",
        5,
        {("synthetic-os", "SYN-CHUNK-007")},
    )
    inconsistent = evaluate_ranking(
        [],
        {"synthetic-os"},
        qrel_map["SYN-INCONSISTENT-001"]["judgments"],
        "INCONSISTENT",
        5,
        set(),
    )
    assert incomplete == {"status": "INCONCLUSIVE", "reason": "QRELS_NOT_EXHAUSTIVE"}
    assert partial == incomplete
    assert inconsistent["status"] == "INVALID_BENCHMARK"
    no_positive = evaluate_ranking(
        [],
        {"synthetic-os"},
        qrel_map["SYN-OOD-001"]["judgments"],
        "EXHAUSTIVELY_JUDGED",
        5,
        set(),
    )
    assert no_positive == {"status": "INCONCLUSIVE", "reason": "NO_POSITIVE_QRELS"}
    assert qrel_map["SYN-OOD-001"]["ood_policy"] == {
        "positive_qrels_allowed": False,
        "evaluate_abstention_separately": True,
    }
    assert evaluate_ood(True, 0) == {
        "status": "OOD_EVALUATED_SEPARATELY",
        "correct_abstention": True,
        "false_citations": 0,
    }
    assert evaluate_ood(True, 1)["correct_abstention"] is False

    out_of_pool = evaluate_ranking(
        [("synthetic-os", "SYN-CHUNK-004")],
        {"synthetic-os"},
        qrel_map["SYN-CONCEPT-001"]["judgments"],
        "EXHAUSTIVELY_JUDGED",
        1,
        {("synthetic-os", "SYN-CHUNK-001")},
    )
    wrong_scope = evaluate_ranking(
        [("synthetic-code", "SYN-CHUNK-006")],
        {"synthetic-os"},
        qrel_map["SYN-CONCEPT-001"]["judgments"],
        "EXHAUSTIVELY_JUDGED",
        1,
        {("synthetic-code", "SYN-CHUNK-006")},
    )
    assert out_of_pool == {"status": "INCONCLUSIVE", "reason": "UNJUDGED_RESULT"}
    assert wrong_scope == {
        "status": "INVALID_BENCHMARK",
        "reason": "SCOPE_VIOLATION",
    }

    resources = resource_summary(850, 1150, None, 0.03, None)
    assert resources["rss_delta_backend_mib"] == 300
    assert resources["ram_status"] == "UNASSESSED"
    assert resources["cpu_status"] == "UNASSESSED"
    return len(cases["cases"])


if __name__ == "__main__":
    count = validate_fixtures()
    print(f"PASS adversarial backend-selection fixtures: {count} declared cases")
