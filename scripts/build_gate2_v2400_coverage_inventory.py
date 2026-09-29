#!/usr/bin/env python3
"""Build a read-only, per-query and per-qrel v2.400 coverage inventory."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]

QUERY_STATUSES = {
    "APPROVED_POSITIVE",
    "APPROVED_NEGATIVE",
    "APPROVED_OOD",
    "PARTIALLY_VALID",
    "PENDING_ADJUDICATION",
    "BLOCKED_SEMANTIC",
    "BLOCKED_SCOPE",
    "INVALID_HISTORICAL_QREL",
    "NO_VALID_QREL",
}
QREL_DECISIONS = {"KEEP", "EXCLUDE"}
SEMANTIC_STATUSES = {"CONFIRMED", "PARTIAL", "INVALID_SEMANTIC"}


class InventoryError(ValueError):
    """Raised when historical inputs cannot be inventoried safely."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InventoryError(f"Cannot read JSON from {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise InventoryError(f"Cannot hash {path}: {exc}") from exc
    return f"sha256:{digest.hexdigest()}"


def _query_scope(record: Mapping[str, Any]) -> str:
    scopes = record.get("notebook_scope")
    if not isinstance(scopes, list) or len(scopes) != 1:
        raise InventoryError(
            f"Query {record.get('query_id')!r} must have exactly one historical scope"
        )
    scope = scopes[0]
    if not isinstance(scope, str) or not scope.strip():
        raise InventoryError(
            f"Query {record.get('query_id')!r} has an invalid historical scope"
        )
    return scope.strip()


def _index_queries(records: Any, label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(records, list):
        raise InventoryError(f"{label} must contain a queries list")
    indexed: dict[str, dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise InventoryError(f"{label} contains a non-object query")
        query_id = record.get("query_id")
        if not isinstance(query_id, str) or not query_id.strip():
            raise InventoryError(f"{label} contains a query without query_id")
        if query_id in indexed:
            raise InventoryError(f"{label} contains duplicate query ID {query_id!r}")
        indexed[query_id] = record
    return indexed


def _index_qrels(payload: Mapping[str, Any]) -> dict[str, dict[str, int]]:
    qrels = payload.get("qrels")
    if not isinstance(qrels, dict):
        raise InventoryError("Qrels input must contain a qrels object")
    indexed: dict[str, dict[str, int]] = {}
    for query_id, entries in qrels.items():
        if not isinstance(query_id, str) or not isinstance(entries, dict):
            raise InventoryError(f"Invalid qrels record for {query_id!r}")
        for chunk_id, grade in entries.items():
            if (
                not isinstance(chunk_id, str)
                or not chunk_id.strip()
                or not isinstance(grade, int)
                or isinstance(grade, bool)
            ):
                raise InventoryError(f"Invalid qrel value for {query_id!r}")
        indexed[query_id] = dict(entries)
    return indexed


def _index_qrel_decisions(
    register: Mapping[str, Any], query_ids: set[str]
) -> dict[tuple[str, str], dict[str, Any]]:
    records = register.get("qrel_decisions", [])
    if not isinstance(records, list):
        raise InventoryError("Decision register qrel_decisions must be a list")
    result: dict[tuple[str, str], dict[str, Any]] = {}
    for row in records:
        if not isinstance(row, dict):
            raise InventoryError("Decision register contains a non-object qrel decision")
        query_id = row.get("query_id")
        chunk_id = row.get("chunk_id")
        if (
            not isinstance(query_id, str)
            or not isinstance(chunk_id, str)
            or not chunk_id.strip()
        ):
            raise InventoryError("Decision register contains an invalid qrel key")
        key = (query_id, chunk_id)
        if query_id not in query_ids:
            raise InventoryError(f"Decision references an unknown qrel query: {key!r}")
        if key in result:
            raise InventoryError(f"Duplicate qrel decision for {key!r}")
        if row.get("decision") not in QREL_DECISIONS:
            raise InventoryError(f"Invalid qrel decision for {key!r}")
        if row.get("semantic_status") not in SEMANTIC_STATUSES:
            raise InventoryError(f"Invalid semantic status for {key!r}")
        if not isinstance(row.get("reason"), str) or not row["reason"].strip():
            raise InventoryError(f"Qrel decision for {key!r} needs a reason")
        if not isinstance(row.get("evidence_source"), str):
            raise InventoryError(f"Qrel decision for {key!r} needs evidence_source")
        result[key] = row
    return result


def _read_scope_and_chunk_membership(
    database: Path, scopes: set[str], chunk_ids: set[str]
) -> tuple[dict[str, set[str]], dict[str, str]]:
    if not database.is_file():
        raise InventoryError(f"Knowledge database does not exist: {database}")
    connection = sqlite3.connect(
        f"file:{database.resolve()}?mode=ro", uri=True
    )
    try:
        acl = {
            scope: {
                row[0]
                for row in connection.execute(
                    "SELECT source_id FROM notebook_sources WHERE notebook_id = ?",
                    (scope,),
                )
            }
            for scope in sorted(scopes)
        }
        chunk_sources: dict[str, str] = {}
        ordered_ids = sorted(chunk_ids)
        for offset in range(0, len(ordered_ids), 400):
            batch = ordered_ids[offset : offset + 400]
            placeholders = ",".join("?" for _ in batch)
            rows = connection.execute(
                f"SELECT id, source_id FROM chunks WHERE id IN ({placeholders})",
                batch,
            )
            chunk_sources.update({row[0]: row[1] for row in rows})
        return acl, chunk_sources
    except sqlite3.Error as exc:
        raise InventoryError(
            f"Cannot inspect scope ACL and qrel chunk membership read-only: {exc}"
        ) from exc
    finally:
        connection.close()


def _qrel_inventory_row(
    *,
    query_id: str,
    scope: str,
    chunk_id: str,
    grade: int,
    decision: Mapping[str, Any] | None,
    acl_sources: set[str],
    chunk_sources: Mapping[str, str],
) -> dict[str, Any]:
    source_id = chunk_sources.get(chunk_id)
    if source_id is None:
        acl_status = "NOT_FOUND"
        chunk_status = "MISSING"
        semantic_status = (
            decision.get("semantic_status", "PENDING") if decision else "PENDING"
        )
        qrel_status = "INVALID"
        action = "HOLD"
        reason = (
            decision.get("reason", "Qrel chunk ID does not exist in the current store.")
            if decision
            else "Qrel chunk ID does not exist in the current store."
        )
    elif source_id not in acl_sources:
        acl_status = "OUTSIDE_ACL"
        chunk_status = "OUTSIDE_ACL"
        semantic_status = (
            decision.get("semantic_status", "PENDING") if decision else "PENDING"
        )
        qrel_status = "INVALID"
        action = "HOLD"
        reason = (
            decision.get(
                "reason",
                "Chunk source is not authorized by the v2.400 scope in the current ACL.",
            )
            if decision
            else "Chunk source is not authorized by the v2.400 scope in the current ACL."
        )
    elif decision is None:
        acl_status = "IN_SCOPE"
        chunk_status = "PENDING_ADJUDICATION"
        semantic_status = "PENDING"
        qrel_status = "PENDING"
        action = "PENDING"
        reason = "No explicit semantic adjudication exists for this query/chunk pair."
    elif decision["decision"] == "EXCLUDE":
        acl_status = "IN_SCOPE"
        chunk_status = "INVALID_SEMANTIC"
        semantic_status = decision["semantic_status"]
        qrel_status = "INVALID"
        action = "EXCLUDE"
        reason = decision["reason"]
    else:
        acl_status = "IN_SCOPE"
        semantic_status = decision["semantic_status"]
        chunk_status = "VALID" if semantic_status == "CONFIRMED" else "PARTIAL"
        qrel_status = "VALID" if semantic_status == "CONFIRMED" else "PARTIAL"
        action = "KEEP"
        reason = decision["reason"]

    result = {
        "query_id": query_id,
        "scope": scope,
        "chunk_id": chunk_id,
        "qrel_grade": grade,
        "qrel_status": qrel_status,
        "chunk_status": chunk_status,
        "acl_status": acl_status,
        "semantic_status": semantic_status,
        "decision": action,
        "reason": reason,
        "evidence_source": (
            decision.get("evidence_source") if decision else "pending_adjudication"
        ),
        "source_id": source_id,
    }
    if decision and "approved_grade" in decision:
        result["adjudicated_grade"] = decision["approved_grade"]
    return result


def _query_status(
    *,
    query_id: str,
    category: str,
    oracle_type: str,
    qrel_rows: list[Mapping[str, Any]],
    explicit_decision: Mapping[str, Any] | None,
) -> tuple[str, str, str | None]:
    if explicit_decision:
        explicit_status = explicit_decision.get("query_status")
        if explicit_status not in {"APPROVED_OOD", "BLOCKED_SEMANTIC", "BLOCKED_SCOPE"}:
            raise InventoryError(
                f"Invalid explicit query status for {query_id!r}: {explicit_status!r}"
            )
        return (
            explicit_status,
            explicit_decision["reason"],
            explicit_decision.get("evidence_source"),
        )

    if oracle_type == "abstention_oracle" and category != "ood_trampas":
        return (
            "PENDING_ADJUDICATION",
            "Historical abstention assertion is outside the OOD category; its intended meaning (scope-negative, global OOD, or another oracle) has not been adjudicated.",
            "data/eval/golden_set_v2_400.json",
        )
    if not qrel_rows:
        if category == "ood_trampas":
            return (
                "PENDING_ADJUDICATION",
                "Historical OOD intent has no explicit approved query-level adjudication.",
                "data/eval/golden_set_v2_400.json",
            )
        return (
            "NO_VALID_QREL",
            "No historical qrel references exist; a positive retrieval query is not approved without adjudicated evidence.",
            "data/eval/qrels/golden_set_v2_400.qrels.json",
        )

    if any(row["acl_status"] == "OUTSIDE_ACL" for row in qrel_rows):
        return (
            "BLOCKED_SCOPE",
            "At least one historical qrel source is outside this query's current persisted ACL; no scope reassignment or qrel mutation is implied.",
            "data/eval/golden_set_v2_400.json; data/web_state/knowledge_store.db",
        )
    if any(row["chunk_status"] == "MISSING" for row in qrel_rows):
        return (
            "INVALID_HISTORICAL_QREL",
            "At least one historical qrel chunk ID is absent from the current knowledge store.",
            "data/eval/qrels/golden_set_v2_400.qrels.json; data/web_state/knowledge_store.db",
        )
    if any(row["decision"] == "HOLD" for row in qrel_rows):
        return (
            "BLOCKED_SCOPE",
            "At least one qrel reference is missing or outside the current scope ACL.",
            "data/web_state/knowledge_store.db",
        )
    if all(row["decision"] == "EXCLUDE" for row in qrel_rows):
        return (
            "INVALID_HISTORICAL_QREL",
            "Every historical qrel reference has an explicit semantic exclusion.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    if any(row["decision"] == "KEEP" for row in qrel_rows) and any(
        row["decision"] in {"EXCLUDE", "PENDING"} for row in qrel_rows
    ):
        return (
            "PARTIALLY_VALID",
            "At least one qrel is explicitly retained while other references are excluded or still pending; only retained references are eligible.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    if any(row["decision"] == "PENDING" for row in qrel_rows):
        return (
            "PENDING_ADJUDICATION",
            "At least one historical qrel reference has no explicit semantic decision.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    if any(row["decision"] == "EXCLUDE" for row in qrel_rows):
        return (
            "PARTIALLY_VALID",
            "At least one qrel is explicitly retained and at least one is explicitly excluded; only retained references are eligible.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    if all(row["semantic_status"] == "CONFIRMED" for row in qrel_rows):
        return (
            "APPROVED_POSITIVE",
            "All historical qrel references are explicitly retained as confirmed evidence.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    if any(row["decision"] == "KEEP" for row in qrel_rows):
        return (
            "PARTIALLY_VALID",
            "Historical qrels contain explicitly retained partial evidence; the query may lack coverage of all requested dimensions.",
            "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
        )
    return (
        "PENDING_ADJUDICATION",
        "Historical qrels have not been semantically adjudicated.",
        "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
    )


def _aggregate_qrel_status(qrel_rows: list[Mapping[str, Any]]) -> str:
    if not qrel_rows:
        return "ABSENT"
    statuses = {row["qrel_status"] for row in qrel_rows}
    known_statuses = statuses - {"PENDING"}
    if not known_statuses:
        return "PENDING"
    if "PENDING" in statuses:
        return (
            "PARTIAL"
            if known_statuses & {"VALID", "PARTIAL"}
            else "PENDING"
        )
    if statuses & {"VALID", "PARTIAL"} and "INVALID" in statuses:
        return "PARTIAL"
    if "INVALID" in statuses:
        return "INVALID"
    if "PARTIAL" in statuses:
        return "PARTIAL"
    return "VALID"


def build_inventory(
    dataset_payload: Mapping[str, Any],
    qrels_payload: Mapping[str, Any],
    decision_register: Mapping[str, Any],
    *,
    v2401_dataset_payload: Mapping[str, Any],
    v2401_qrels_payload: Mapping[str, Any],
    dataset_sha256: str,
    qrels_sha256: str,
    knowledge_db: Path,
    knowledge_db_sha256: str,
    v2401_dataset_sha256: str,
    v2401_qrels_sha256: str,
) -> dict[str, Any]:
    if dataset_payload.get("golden_set_version") != "v2.400":
        raise InventoryError("Canonical input dataset must be golden_set_version v2.400")
    queries = _index_queries(dataset_payload.get("queries"), "v2.400 dataset")
    qrels = _index_qrels(qrels_payload)
    if set(queries) != set(qrels):
        raise InventoryError("v2.400 query IDs and qrels query IDs do not match")

    explicit_qrel_decisions = _index_qrel_decisions(
        decision_register, set(queries)
    )
    unknown_decisions = set(explicit_qrel_decisions) - {
        (query_id, chunk_id)
        for query_id, entries in qrels.items()
        for chunk_id in entries
    }
    if unknown_decisions:
        raise InventoryError(
            "Decision register contains non-historical qrel pairs: "
            f"{sorted(unknown_decisions)!r}"
        )

    query_decisions = decision_register.get("query_decisions", {})
    if not isinstance(query_decisions, Mapping):
        raise InventoryError("Decision register query_decisions must be an object")
    unknown_query_decisions = set(query_decisions) - set(queries)
    if unknown_query_decisions:
        raise InventoryError(
            f"Decision register contains unknown query IDs: {sorted(unknown_query_decisions)!r}"
        )

    v2401_queries = _index_queries(
        v2401_dataset_payload.get("queries"), "v2.401 audit dataset"
    )
    v2401_qrels = _index_qrels(v2401_qrels_payload)
    if set(v2401_queries) != set(v2401_qrels):
        raise InventoryError("v2.401 audit query IDs and qrels IDs do not match")

    changed_scope_ids = {
        query_id
        for query_id in set(queries) & set(v2401_queries)
        if _query_scope(queries[query_id]) != _query_scope(v2401_queries[query_id])
    }
    scopes = {_query_scope(row) for row in queries.values()} | {
        _query_scope(row) for row in v2401_queries.values()
    }
    chunk_ids = {
        chunk_id for entries in qrels.values() for chunk_id in entries
    }
    changed_v2401_qrel_ids = {
        chunk_id
        for query_id in changed_scope_ids
        for chunk_id in v2401_qrels[query_id]
    }
    chunk_ids.update(changed_v2401_qrel_ids)
    acl, chunk_sources = _read_scope_and_chunk_membership(
        knowledge_db, scopes, chunk_ids
    )

    query_rows: list[dict[str, Any]] = []
    qrel_rows: list[dict[str, Any]] = []
    for query_id, record in queries.items():
        scope = _query_scope(record)
        category = record.get("category", "")
        oracle_type = record.get("oracle_type", "")
        expected = record.get("expected", {})
        if not isinstance(expected, dict):
            raise InventoryError(f"Query {query_id!r} has invalid expected metadata")

        current_qrel_rows = [
            _qrel_inventory_row(
                query_id=query_id,
                scope=scope,
                chunk_id=chunk_id,
                grade=grade,
                decision=explicit_qrel_decisions.get((query_id, chunk_id)),
                acl_sources=acl.get(scope, set()),
                chunk_sources=chunk_sources,
            )
            for chunk_id, grade in qrels[query_id].items()
        ]
        query_decision = query_decisions.get(query_id)
        if query_decision is not None and not isinstance(query_decision, Mapping):
            raise InventoryError(f"Query decision for {query_id!r} must be an object")
        status, reason, query_evidence = _query_status(
            query_id=query_id,
            category=category,
            oracle_type=oracle_type,
            qrel_rows=current_qrel_rows,
            explicit_decision=query_decision,
        )
        if status not in QUERY_STATUSES:
            raise InventoryError(f"Unsupported query status {status!r}")

        scope_integrity = (
            "VIOLATION_DETECTED"
            if query_id in changed_scope_ids
            else "NO_QUERY_LEVEL_VIOLATION_DETECTED"
        )
        scope_action = "NONE"
        if scope_action != "NONE":
            raise InventoryError(
                f"Scope decision for {scope!r} attempts a destructive action"
            )

        if oracle_type == "abstention_oracle" and category == "ood_trampas":
            intent = "Global abstention / OOD"
        elif oracle_type == "abstention_oracle":
            intent = "Historical abstention assertion outside the OOD category"
        elif oracle_type == "retrieval_citation":
            intent = "In-scope retrieval and citation"
        else:
            intent = f"Historical oracle: {oracle_type or 'unspecified'}"

        query_rows.append(
            {
                "query_id": query_id,
                "scope": scope,
                "intent": intent,
                "category": category,
                "oracle_type": oracle_type,
                "query": record.get("query", ""),
                "kc_ids": record.get("kc_ids", []),
                "tags": record.get("tags", []),
                "expected_abstention": expected.get("abstention"),
                "historical_qrel_count": len(current_qrel_rows),
                "historical_qrel_status": _aggregate_qrel_status(current_qrel_rows),
                "pending_qrel_reference_count": sum(
                    row["qrel_status"] == "PENDING" for row in current_qrel_rows
                ),
                "query_status": status,
                "reason": reason,
                "evidence_source": query_evidence,
                "historical_scope_integrity": scope_integrity,
                "scope_integrity_action": scope_action,
                "v2401_scope_changed": query_id in changed_scope_ids,
                "v2401_scope": (
                    _query_scope(v2401_queries[query_id])
                    if query_id in v2401_queries
                    else None
                ),
                "qrel_chunk_ids": [row["chunk_id"] for row in current_qrel_rows],
            }
        )
        qrel_rows.extend(current_qrel_rows)

    query_status_counts = Counter(row["query_status"] for row in query_rows)
    qrel_status_counts = Counter(row["qrel_status"] for row in qrel_rows)
    chunk_status_counts = Counter(row["chunk_status"] for row in qrel_rows)
    acl_status_counts = Counter(row["acl_status"] for row in qrel_rows)
    query_qrel_status_counts = Counter(
        row["historical_qrel_status"] for row in query_rows
    )
    kept_qrel_rows_by_query: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in qrel_rows:
        if row["decision"] == "KEEP":
            kept_qrel_rows_by_query[row["query_id"]].append(row)
    query_ids_by_scope: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in query_rows:
        query_ids_by_scope[row["scope"]].append(row)
    scope_summaries = []
    imported_to_scope_counts = Counter(
        _query_scope(v2401_queries[query_id])
        for query_id in changed_scope_ids
    )
    imported_query_ids_by_scope: dict[str, list[str]] = defaultdict(list)
    for query_id in changed_scope_ids:
        imported_query_ids_by_scope[_query_scope(v2401_queries[query_id])].append(
            query_id
        )
    for scope in sorted(set(query_ids_by_scope) | set(imported_to_scope_counts)):
        rows = query_ids_by_scope.get(scope, [])
        scoped_qrels = [row for row in qrel_rows if row["scope"] == scope]
        changed_rows = [row for row in rows if row["v2401_scope_changed"]]
        imported_count = imported_to_scope_counts[scope]
        scope_summaries.append(
            {
                "scope": scope,
                "query_count": len(rows),
                "qrel_reference_count": len(scoped_qrels),
                "qrel_status_counts": dict(
                    sorted(Counter(row["qrel_status"] for row in scoped_qrels).items())
                ),
                "query_status_counts": dict(
                    sorted(Counter(row["query_status"] for row in rows).items())
                ),
                "acl_associated_source_count": len(acl.get(scope, set())),
                "v2401_scope_changed_query_count": len(changed_rows),
                "v2401_imported_query_count": imported_count,
                "v2401_changed_query_qrel_count": sum(
                    len(v2401_qrels[row["query_id"]]) for row in changed_rows
                ),
                "v2401_imported_query_qrel_count": sum(
                    len(v2401_qrels[query_id])
                    for query_id in imported_query_ids_by_scope[scope]
                ),
                "historical_scope_integrity": (
                    "VIOLATION_DETECTED"
                    if changed_rows or imported_count
                    else "NO_VIOLATION_DETECTED"
                ),
                "action": "NONE",
            }
        )

    audit_qrel_reference_count = 0
    audit_qrel_outside_previous_scope_count = 0
    audit_qrel_missing_count = 0
    for query_id in sorted(changed_scope_ids):
        old_scope = _query_scope(queries[query_id])
        for chunk_id in v2401_qrels[query_id]:
            audit_qrel_reference_count += 1
            source_id = chunk_sources.get(chunk_id)
            if source_id is None:
                audit_qrel_missing_count += 1
            elif source_id not in acl.get(old_scope, set()):
                audit_qrel_outside_previous_scope_count += 1

    register = decision_register.get("audit_reference", {})
    if not isinstance(register, Mapping):
        raise InventoryError("audit_reference must be an object")
    if (
        register.get("version") != "v2.401"
        or register.get("canonical_for_repair") is not False
        or register.get("historical_evidence") is not True
        or register.get("action") != "NONE"
    ):
        raise InventoryError(
            "v2.401 must be marked historical evidence only, with no repair action"
        )

    return {
        "schema_version": "gate2-v2400-coverage-inventory-v1",
        "generated_at": "2026-09-28",
        "canonical_source": {
            "version": "v2.400",
            "dataset_path": "data/eval/golden_set_v2_400.json",
            "qrels_path": "data/eval/qrels/golden_set_v2_400.qrels.json",
            "dataset_sha256": dataset_sha256,
            "qrels_sha256": qrels_sha256,
        },
        "read_only_validation": {
            "knowledge_db_path": str(knowledge_db),
            "knowledge_db_sha256": knowledge_db_sha256,
            "retrieval_executed": False,
            "embeddings_executed": False,
            "reranking_executed": False,
            "generation_executed": False,
            "database_writes": False,
        },
        "audit_reference": {
            "version": "v2.401",
            "canonical_for_repair": False,
            "historical_evidence": True,
            "dataset_sha256": v2401_dataset_sha256,
            "qrels_sha256": v2401_qrels_sha256,
            "scope_qrel_finding": register.get("scope_qrel_finding"),
            "canonical_v2400_scope_changed_query_count": len(changed_scope_ids),
            "changed_scope_qrel_reference_count": audit_qrel_reference_count,
            "changed_scope_qrels_outside_corresponding_v2400_acl": audit_qrel_outside_previous_scope_count,
            "changed_scope_qrels_missing": audit_qrel_missing_count,
            "action": "NONE",
        },
        "scope_integrity_findings": {
            scope: {
                "historical_scope_integrity": values.get(
                    "historical_scope_integrity", "NO_DECISION"
                ),
                "action": values.get("action", "NONE"),
                "reason": values.get("reason"),
                "evidence_source": values.get("evidence_source"),
            }
            for scope, values in sorted(
                decision_register.get("scope_decisions", {}).items()
            )
        },
        "counts": {
            "query_count": len(query_rows),
            "query_status_counts": {
                status: query_status_counts[status] for status in sorted(QUERY_STATUSES)
            },
            "query_historical_qrel_status_counts": {
                status: query_qrel_status_counts[status]
                for status in ("ABSENT", "INVALID", "PARTIAL", "PENDING", "VALID")
            },
            "scope_count": len(scope_summaries),
            "qrel_reference_count": len(qrel_rows),
            "qrel_status_counts": {
                status: qrel_status_counts[status]
                for status in ("INVALID", "PARTIAL", "PENDING", "VALID")
            },
            "chunk_status_counts": {
                status: chunk_status_counts[status]
                for status in (
                    "INVALID_SEMANTIC",
                    "MISSING",
                    "OUTSIDE_ACL",
                    "PARTIAL",
                    "PENDING_ADJUDICATION",
                    "VALID",
                )
            },
            "acl_status_counts": {
                status: acl_status_counts[status]
                for status in ("IN_SCOPE", "NOT_FOUND", "OUTSIDE_ACL")
            },
            "queries_with_confirmed_qrel_count": sum(
                any(row["semantic_status"] == "CONFIRMED" for row in rows)
                for rows in kept_qrel_rows_by_query.values()
            ),
            "queries_with_partial_qrel_count": sum(
                any(row["semantic_status"] == "PARTIAL" for row in rows)
                for rows in kept_qrel_rows_by_query.values()
            ),
            "qrel_references_missing": chunk_status_counts["MISSING"],
            "qrel_references_outside_acl": chunk_status_counts["OUTSIDE_ACL"],
            "qrel_references_pending_semantic_adjudication": chunk_status_counts[
                "PENDING_ADJUDICATION"
            ],
            "v2401_changed_scope_query_count": len(changed_scope_ids),
            "v2401_changed_scope_qrel_reference_count": audit_qrel_reference_count,
            "v2401_changed_scope_qrels_outside_v2400_acl": audit_qrel_outside_previous_scope_count,
            "v2401_changed_scope_qrels_missing": audit_qrel_missing_count,
        },
        "scope_summaries": scope_summaries,
        "queries": query_rows,
        "qrel_references": qrel_rows,
        "limitations": [
            "A current persisted ACL membership check does not reconstruct a historical ACL and does not establish semantic relevance.",
            "Only explicit decisions in the decision register are treated as semantic adjudications; unreviewed references remain pending.",
            "The inventory is not a benchmark repair, does not change historical files or ACL, and makes no retrieval-quality or end-to-end abstention claim.",
            "v2.401 is included solely as audit evidence and is not canonical for repair.",
        ],
    }


def render_markdown(inventory: Mapping[str, Any]) -> str:
    counts = inventory["counts"]
    lines = [
        "# Gate 2 — Inventario de cobertura y validez de v2.400",
        "",
        f"**Fecha:** {inventory['generated_at']}  ",
        "**Modo:** read-only; sin retrieval, embeddings, reranking, generación ni escrituras SQLite.  ",
        "**Fuente canónica:** v2.400. v2.401 se conserva solo como evidencia de auditoría.",
        "",
        "## Resumen",
        "",
        f"- Consultas inventariadas: **{counts['query_count']}**",
        f"- Scopes: **{counts['scope_count']}**",
        f"- Referencias qrel: **{counts['qrel_reference_count']}**",
        f"- Qrels no encontrados: **{counts['qrel_references_missing']}**",
        f"- Qrels fuera de ACL actual del scope v2.400: **{counts['qrel_references_outside_acl']}**",
        f"- Qrels pendientes de adjudicación semántica: **{counts['qrel_references_pending_semantic_adjudication']}**",
        f"- Consultas con al menos un qrel conservado y confirmado: **{counts['queries_with_confirmed_qrel_count']}**",
        f"- Consultas con al menos un qrel conservado como evidencia parcial: **{counts['queries_with_partial_qrel_count']}**",
        "",
        "### Estado de consultas",
        "",
        "| Estado | Consultas |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{status}` | {count} |"
        for status, count in inventory["counts"]["query_status_counts"].items()
    )
    lines.extend(
        [
            "",
            "### Estado agregado de qrels por consulta",
            "",
            "| Estado | Consultas |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{status}` | {count} |"
        for status, count in inventory["counts"][
            "query_historical_qrel_status_counts"
        ].items()
    )
    lines.extend(
        [
            "",
            "### Estado de referencias qrel",
            "",
            "| Estado qrel | Referencias |",
            "|---|---:|",
        ]
    )
    qrel_status_counts = inventory["counts"]["qrel_status_counts"]
    chunk_status_counts = inventory["counts"]["chunk_status_counts"]
    for status, count in qrel_status_counts.items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "| Estado de chunk / ACL | Referencias |",
            "|---|---:|",
        ]
    )
    for status, count in chunk_status_counts.items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "| Estado ACL | Referencias |",
            "|---|---:|",
        ]
    )
    for status, count in inventory["counts"]["acl_status_counts"].items():
        lines.append(f"| `{status}` | {count} |")
    lines.extend(
        [
            "",
            "## Resumen por scope",
            "",
            "| Scope | Consultas v2.400 | Qrels v2.400 | Estados de consulta | Estados qrel | Cambios v2.401 salientes / entrantes | Qrels v2.401 entrantes | Integridad histórica | Acción |",
            "|---|---:|---:|---|---|---:|---|---|---|",
        ]
    )
    for row in inventory["scope_summaries"]:
        query_states = ", ".join(
            f"{key}: {value}" for key, value in row["query_status_counts"].items()
        )
        qrel_states = ", ".join(
            f"{key}: {value}" for key, value in row["qrel_status_counts"].items()
        )
        lines.append(
            f"| `{row['scope']}` | {row['query_count']} | "
            f"{row['qrel_reference_count']} | {query_states or '—'} | "
            f"{qrel_states or '—'} | "
            f"{row['v2401_scope_changed_query_count']} / "
            f"{row['v2401_imported_query_count']} | "
            f"{row['v2401_imported_query_qrel_count']} | "
            f"`{row['historical_scope_integrity']}` | "
            f"`{row['action']}` |"
        )
    lines.extend(
        [
            "",
            "## Referencia de auditoría v2.401",
            "",
            f"- Canonical para reparación: **{inventory['audit_reference']['canonical_for_repair']}**",
            f"- Evidencia histórica: **{inventory['audit_reference']['historical_evidence']}**",
            f"- Cambios de scope al comparar con v2.400: **{inventory['audit_reference']['canonical_v2400_scope_changed_query_count']} consultas**",
            f"- Referencias qrel de esas consultas: **{inventory['audit_reference']['changed_scope_qrel_reference_count']}**",
            f"- Fuera de la ACL del scope correspondiente en v2.400: **{inventory['audit_reference']['changed_scope_qrels_outside_corresponding_v2400_acl']}**",
            f"- Referencias faltantes: **{inventory['audit_reference']['changed_scope_qrels_missing']}**",
            "- Acción: **NONE** (hallazgo de integridad; no reasignar scopes ni eliminar qrels automáticamente).",
            "",
            "## Inventario de las 400 consultas",
            "",
            "La tabla incluye todas las consultas v2.400. El JSON contiene los "
            "campos completos y el detalle independiente de cada chunk qrel.",
            "",
            "| Query ID | Scope | Categoría / intención | Oráculo histórico | Qrels | Estado | Justificación resumida |",
            "|---|---|---|---|---:|---|---|",
        ]
    )
    for row in inventory["queries"]:
        reason = row["reason"].replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{row['query_id']}` | `{row['scope']}` | "
            f"{row['category']} / {row['intent']} | `{row['oracle_type']}` | "
            f"{row['historical_qrel_count']} | `{row['query_status']}` | {reason} |"
        )
    lines.extend(
        [
            "",
            "## Decisiones por referencia qrel",
            "",
            "| Query ID | Scope | Chunk ID | Grado histórico | Estado | ACL | Semántica | Decisión | Fuente |",
            "|---|---|---|---:|---|---|---|---|---|",
        ]
    )
    for row in inventory["qrel_references"]:
        lines.append(
            f"| `{row['query_id']}` | `{row['scope']}` | `{row['chunk_id']}` | "
            f"{row['qrel_grade']} | `{row['qrel_status']}` | "
            f"`{row['acl_status']}` | `{row['semantic_status']}` | "
            f"`{row['decision']}` | `{row['evidence_source']}` |"
        )
    lines.extend(
        [
            "",
            "## Política de interpretación",
            "",
            "- Cada consulta tiene un estado principal; cada referencia qrel tiene "
            "su propio estado, decisión y motivo.",
            "- Una membresía ACL válida no implica validez semántica.",
            "- Estados de query y de qrel se calculan por separado; una query puede "
            "ser parcialmente válida aunque una referencia esté excluida.",
            "- `VIOLATION_DETECTED` solo registra una inconsistencia histórica; "
            "la acción es `NONE`, sin reasignación ni eliminación automática.",
            "- Los qrels no adjudicados quedan `PENDING_ADJUDICATION`; no se "
            "completan juicios por inferencia.",
            "- v2.401 tiene `canonical_for_repair=false` y "
            "`historical_evidence=true`.",
            "",
            "## Hashes congelados",
            "",
            f"- v2.400 dataset: `{inventory['canonical_source']['dataset_sha256']}`",
            f"- v2.400 qrels: `{inventory['canonical_source']['qrels_sha256']}`",
            f"- v2.401 dataset (referencia): `{inventory['audit_reference']['dataset_sha256']}`",
            f"- v2.401 qrels (referencia): `{inventory['audit_reference']['qrels_sha256']}`",
            f"- knowledge store: `{inventory['read_only_validation']['knowledge_db_sha256']}`",
            "",
            "El JSON adyacente es la fuente estructurada de verdad; este Markdown "
            "es una vista auditable derivada.",
            "",
        ]
    )
    return "\n".join(lines)


def generate_inventory(
    *,
    dataset_path: Path,
    qrels_path: Path,
    v2401_dataset_path: Path,
    v2401_qrels_path: Path,
    decision_register_path: Path,
    knowledge_db_path: Path,
    output_json: Path,
    output_markdown: Path,
    overwrite_existing: bool = False,
) -> dict[str, Any]:
    outputs = (output_json, output_markdown)
    resolved_outputs = {path.resolve() for path in outputs}
    if len(resolved_outputs) != len(outputs):
        raise InventoryError("JSON and Markdown outputs must be different paths")
    input_paths = (
        dataset_path,
        qrels_path,
        v2401_dataset_path,
        v2401_qrels_path,
        decision_register_path,
        knowledge_db_path,
    )
    resolved_inputs = {path.resolve() for path in input_paths}
    if resolved_outputs & resolved_inputs:
        raise InventoryError("Inventory outputs must not replace any input or database")
    existing = [path for path in outputs if path.exists()]
    if existing and not overwrite_existing:
        raise InventoryError(f"Refusing to overwrite output: {existing[0]}")
    missing = next((path for path in input_paths if not path.is_file()), None)
    if missing:
        raise InventoryError(f"Input file does not exist: {missing}")

    inventory = build_inventory(
        _read_json(dataset_path),
        _read_json(qrels_path),
        _read_json(decision_register_path),
        v2401_dataset_payload=_read_json(v2401_dataset_path),
        v2401_qrels_payload=_read_json(v2401_qrels_path),
        dataset_sha256=_sha256(dataset_path),
        qrels_sha256=_sha256(qrels_path),
        knowledge_db=knowledge_db_path,
        knowledge_db_sha256=_sha256(knowledge_db_path),
        v2401_dataset_sha256=_sha256(v2401_dataset_path),
        v2401_qrels_sha256=_sha256(v2401_qrels_path),
    )
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    json_written = False
    try:
        output_json.write_text(
            json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        json_written = True
        output_markdown.write_text(
            render_markdown(inventory), encoding="utf-8"
        )
    except OSError as exc:
        if json_written:
            output_json.unlink(missing_ok=True)
        raise InventoryError(f"Cannot write inventory outputs: {exc}") from exc
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset",
        type=Path,
        default=ROOT / "data/eval/golden_set_v2_400.json",
    )
    parser.add_argument(
        "--qrels",
        type=Path,
        default=ROOT / "data/eval/qrels/golden_set_v2_400.qrels.json",
    )
    parser.add_argument(
        "--v2401-dataset",
        type=Path,
        default=ROOT / "data/eval/golden_set_v2_401.json",
    )
    parser.add_argument(
        "--v2401-qrels",
        type=Path,
        default=ROOT / "data/eval/qrels/golden_set_v2_401.qrels.json",
    )
    parser.add_argument(
        "--decision-register",
        type=Path,
        default=ROOT
        / "reports/gate2_v2400_explicit_decision_register_2026-09-28.json",
    )
    parser.add_argument(
        "--knowledge-db",
        type=Path,
        default=ROOT / "data/web_state/knowledge_store.db",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT / "reports/gate2_v2400_coverage_inventory_2026-09-28.json",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=ROOT / "reports/gate2_v2400_coverage_inventory_2026-09-28.md",
    )
    parser.add_argument(
        "--overwrite-existing",
        action="store_true",
        help="Replace the two explicitly selected output files",
    )
    args = parser.parse_args(argv)
    inventory = generate_inventory(
        dataset_path=args.dataset,
        qrels_path=args.qrels,
        v2401_dataset_path=args.v2401_dataset,
        v2401_qrels_path=args.v2401_qrels,
        decision_register_path=args.decision_register,
        knowledge_db_path=args.knowledge_db,
        output_json=args.output_json,
        output_markdown=args.output_markdown,
        overwrite_existing=args.overwrite_existing,
    )
    print(
        f"Generated {args.output_json} and {args.output_markdown}: "
        f"{inventory['counts']['query_count']} queries, "
        f"{inventory['counts']['qrel_reference_count']} qrel references, "
        f"read-only validation."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except InventoryError as exc:
        print(f"Gate 2 inventory failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
