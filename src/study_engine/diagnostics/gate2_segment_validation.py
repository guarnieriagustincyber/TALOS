"""Read-only structural and ACL validation for segmented Gate 2 datasets."""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
import sqlite3
from typing import Any

from study_engine.contracts.gate2_oracle import Gate2Dataset
from study_engine.retrieval.gate2_oracle import (
    Gate2ContractError,
    validate_gate2_contract,
)


class Gate2SegmentValidationError(ValueError):
    """Raised when a Gate 2 segment cannot be validated safely."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Gate2SegmentValidationError(f"Cannot read {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise Gate2SegmentValidationError(f"Cannot hash {path}: {exc}") from exc
    return f"sha256:{digest.hexdigest()}"


def _read_acl_and_chunks(
    database: Path, scopes: set[str], chunk_ids: set[str]
) -> tuple[dict[str, set[str]], dict[str, str]]:
    if not database.is_file():
        raise Gate2SegmentValidationError(
            f"Knowledge database does not exist: {database}"
        )
    connection = sqlite3.connect(f"file:{database.resolve()}?mode=ro", uri=True)
    try:
        acl: dict[str, set[str]] = {}
        for scope in sorted(scopes):
            acl[scope] = {
                row[0]
                for row in connection.execute(
                    "SELECT source_id FROM notebook_sources WHERE notebook_id = ?",
                    (scope,),
                )
            }

        chunk_sources: dict[str, str] = {}
        chunk_id_list = sorted(chunk_ids)
        for offset in range(0, len(chunk_id_list), 500):
            batch = chunk_id_list[offset : offset + 500]
            placeholders = ",".join("?" for _ in batch)
            rows = connection.execute(
                f"SELECT id, source_id FROM chunks WHERE id IN ({placeholders})",
                batch,
            )
            chunk_sources.update({row[0]: row[1] for row in rows})
        return acl, chunk_sources
    except sqlite3.Error as exc:
        raise Gate2SegmentValidationError(
            f"Cannot validate ACL/chunks in read-only mode: {exc}"
        ) from exc
    finally:
        connection.close()


def validate_gate2_segments(
    dataset_path: Path,
    qrels_path: Path,
    knowledge_db: Path,
) -> dict[str, Any]:
    """Validate the dataset and report counts grouped by oracle and scope.

    Only qrel-referenced chunk IDs and ACL rows for represented scopes are read.
    No retrieval, embedding, generation, or database writes are performed.
    """
    dataset_payload = _read_json(dataset_path)
    qrels_payload = _read_json(qrels_path)
    raw_queries = dataset_payload.get("queries")
    qrels = qrels_payload.get("qrels")
    version = dataset_payload.get("version", dataset_payload.get("golden_set_version"))
    if not isinstance(raw_queries, list) or not isinstance(qrels, dict):
        raise Gate2SegmentValidationError(
            "Dataset must contain queries and qrels file must contain a qrels object"
        )
    if not isinstance(version, str) or not version.strip():
        raise Gate2SegmentValidationError("Dataset version is missing")
    try:
        dataset = Gate2Dataset.model_validate(
            {
                "version": version,
                "queries": raw_queries,
                "metadata": dataset_payload.get("metadata", {}),
            }
        )
    except Exception as exc:
        raise Gate2SegmentValidationError(f"Invalid Gate 2 dataset: {exc}") from exc

    chunk_ids: set[str] = set()
    for query_id, records in qrels.items():
        if not isinstance(query_id, str) or not isinstance(records, dict):
            raise Gate2SegmentValidationError(f"Invalid qrels record {query_id!r}")
        for chunk_id, grade in records.items():
            if not isinstance(chunk_id, str) or not isinstance(grade, int):
                raise Gate2SegmentValidationError(
                    f"Invalid qrel value for {query_id!r}: {chunk_id!r}={grade!r}"
                )
            if not 1 <= grade <= 3:
                raise Gate2SegmentValidationError(
                    f"Qrel grade for {query_id!r}/{chunk_id!r} must be between 1 and 3"
                )
            chunk_ids.add(chunk_id)

    scopes = {query.scope for query in dataset.queries}
    acl, chunk_sources = _read_acl_and_chunks(knowledge_db, scopes, chunk_ids)
    try:
        counts = validate_gate2_contract(dataset, qrels, chunk_sources, acl)
    except Gate2ContractError as exc:
        raise Gate2SegmentValidationError(str(exc)) from exc

    queries_by_segment: dict[tuple[str, str], list[Any]] = defaultdict(list)
    pending_queries = []
    for query in dataset.queries:
        queries_by_segment[(query.scope, query.oracle_type.value)].append(query)
        if query.qrels_status != "approved":
            pending_queries.append(query.query_id)
        if (
            query.oracle_type.value == "positive_in_scope"
            and qrels[query.query_id]
            and query.qrels_provenance != "human_verified"
        ):
            pending_queries.append(query.query_id)

    segments = []
    for (scope, oracle_type), queries in sorted(queries_by_segment.items()):
        segment_qrel_count = 0
        grade_counts: Counter[str] = Counter()
        provenance_counts: Counter[str] = Counter()
        for query in queries:
            query_qrels = qrels[query.query_id]
            segment_qrel_count += len(query_qrels)
            grade_counts.update(str(grade) for grade in query_qrels.values())
            provenance_counts.update([query.qrels_provenance])
        segments.append(
            {
                "scope": scope,
                "oracle_type": oracle_type,
                "query_count": len(queries),
                "query_ids": sorted(query.query_id for query in queries),
                "queries_with_qrels": sum(bool(qrels[q.query_id]) for q in queries),
                "qrel_chunk_count": segment_qrel_count,
                "qrel_grade_counts": dict(sorted(grade_counts.items())),
                "qrels_provenance_counts": dict(sorted(provenance_counts.items())),
            }
        )

    return {
        "version": version,
        "status": "passed",
        "mode": "offline_structural_acl_validation",
        "retrieval_executed": False,
        "release_eligible": not pending_queries,
        "pending_adjudication_query_ids": sorted(set(pending_queries)),
        "sources": {
            "dataset_sha256": _sha256(dataset_path),
            "qrels_sha256": _sha256(qrels_path),
            "knowledge_db_sha256": _sha256(knowledge_db),
        },
        "counts": counts,
        "segments": segments,
        "limitations": [
            "This validates structure and persisted ACL membership only; it does not assess semantic relevance, ranking, abstention, latency, or retrieval quality.",
            "Only chunks referenced by qrels are looked up; no corpus-wide retrieval or scan is run.",
        ],
    }
