#!/usr/bin/env python3
"""Build blinded, non-decisional human review packets for backend selection."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import secrets
import sqlite3
import sys
import uuid
from typing import Any, Iterable, Mapping

ROOT = Path(__file__).resolve().parents[1]
PACKET_SCHEMA = "backend-selection-adjudication-packet-v1"


class PacketError(ValueError):
    """Raised when inputs cannot safely produce a blinded review packet."""


def _canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _hash_rows(rows: Iterable[Iterable[Any]]) -> tuple[str, int]:
    digest = hashlib.sha256()
    count = 0
    for row in rows:
        encoded = _canonical_json(list(row))
        digest.update(len(encoded).to_bytes(8, "big"))
        digest.update(encoded)
        count += 1
    return digest.hexdigest(), count


def _validate_inputs(
    dataset: Mapping[str, Any], qrels_file: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, int]]]:
    queries = dataset.get("queries")
    qrels = qrels_file.get("qrels")
    if not isinstance(queries, list) or not isinstance(qrels, dict):
        raise PacketError("Dataset and qrels must contain queries and qrels")

    query_ids: set[str] = set()
    normalized_queries = []
    for query in queries:
        if not isinstance(query, dict):
            raise PacketError("Dataset contains a non-object query")
        query_id = query.get("query_id")
        text = query.get("query")
        scopes = query.get("notebook_scope")
        if (
            not isinstance(query_id, str)
            or not query_id
            or query_id in query_ids
            or not isinstance(text, str)
            or not text.strip()
            or not isinstance(scopes, list)
            or not scopes
            or any(not isinstance(scope, str) or not scope for scope in scopes)
            or len(set(scopes)) != len(scopes)
        ):
            raise PacketError("Dataset has invalid or duplicate query identity/scope")
        query_ids.add(query_id)
        normalized_queries.append(query)

    if set(qrels) != query_ids:
        raise PacketError("Qrels query IDs do not exactly match the dataset")
    normalized_qrels: dict[str, dict[str, int]] = {}
    for query_id, labels in qrels.items():
        if not isinstance(labels, dict):
            raise PacketError(f"Invalid qrels mapping for {query_id!r}")
        normalized_qrels[query_id] = {}
        for chunk_id, grade in labels.items():
            if (
                not isinstance(chunk_id, str)
                or not chunk_id
                or type(grade) is not int
                or grade not in (1, 2, 3)
            ):
                raise PacketError(f"Invalid historical qrel for {query_id!r}")
            normalized_qrels[query_id][chunk_id] = grade
    return normalized_queries, normalized_qrels


def _scope_snapshot(
    connection: sqlite3.Connection, scope: str
) -> dict[str, Any]:
    source_rows = connection.execute(
        """
        SELECT s.source_id, s.sha256, s.manifest_json, s.source_json, s.title,
               s.author, s.type, s.language, s.role, s.priority, s.subject,
               s.course, s.phase, s.chapter, s.section, s.page, s.created_at,
               s.metadata
        FROM notebook_sources AS ns
        JOIN sources AS s ON s.source_id = ns.source_id
        WHERE ns.notebook_id = ?
        ORDER BY s.source_id
        """,
        (scope,),
    )
    source_hash, source_count = _hash_rows(source_rows)

    chunk_rows = connection.execute(
        """
        SELECT c.id, c.document_id, c.source_id, c.content, c.page_start,
               c.page_end, c.chapter, c.section, c.token_count, c.pos_index,
               c.metadata, c.parent_chapter_id
        FROM notebook_sources AS ns
        JOIN chunks AS c ON c.source_id = ns.source_id
        WHERE ns.notebook_id = ?
        ORDER BY c.source_id, c.pos_index, c.id
        """,
        (scope,),
    )
    chunk_hash, chunk_count = _hash_rows(chunk_rows)
    if source_count == 0 or chunk_count == 0:
        raise PacketError(f"Scope {scope!r} has no persisted sources or chunks")
    return {
        "source_count": source_count,
        "source_rows_sha256": source_hash,
        "chunk_count": chunk_count,
        "chunk_rows_sha256": chunk_hash,
    }


def build_bundle(
    dataset: Mapping[str, Any],
    qrels_file: Mapping[str, Any],
    connection: sqlite3.Connection,
    dataset_sha256: str,
    qrels_sha256: str,
) -> dict[str, Any]:
    queries, qrels = _validate_inputs(dataset, qrels_file)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")

    query_counts: Counter[str] = Counter()
    category_counts: Counter[str] = Counter()
    scope_queries: dict[str, set[str]] = {}
    query_by_id = {query["query_id"]: query for query in queries}
    for query in queries:
        for scope in query["notebook_scope"]:
            query_counts[scope] += 1
            scope_queries.setdefault(scope, set()).add(query["query_id"])
        category = query.get("category")
        if isinstance(category, str):
            category_counts[category] += 1

    scope_snapshots = {
        scope: _scope_snapshot(connection, scope) for scope in sorted(scope_queries)
    }
    qrel_reference_count = 0
    qrel_query_count = 0
    for query_id, labels in qrels.items():
        query = query_by_id[query_id]
        if labels:
            qrel_query_count += 1
        allowed_scopes = query["notebook_scope"]
        for chunk_id in labels:
            qrel_reference_count += 1
            placeholders = ",".join("?" for _ in allowed_scopes)
            row = connection.execute(
                f"""
                SELECT 1 FROM chunks AS c
                JOIN notebook_sources AS ns ON ns.source_id = c.source_id
                WHERE c.id = ? AND ns.notebook_id IN ({placeholders})
                LIMIT 1
                """,
                (chunk_id, *allowed_scopes),
            ).fetchone()
            if row is None:
                raise PacketError(
                    f"Historical qrel {query_id!r}/{chunk_id!r} is missing "
                    "or outside the current persisted scope"
                )
    connection.rollback()

    corpus_snapshot = {
        "scope_snapshots": scope_snapshots,
        "scope_acl_source": (
            "Current notebook_sources membership only; this does not reconstruct "
            "a historical ACL."
        ),
    }
    corpus_snapshot_sha256 = hashlib.sha256(
        _canonical_json(corpus_snapshot)
    ).hexdigest()

    cases_by_reviewer: dict[str, list[dict[str, Any]]] = {}
    reconciliation: dict[str, dict[str, str]] = {}
    for reviewer in ("reviewer_a", "reviewer_b"):
        cases = []
        reviewer_map: dict[str, str] = {}
        for query in queries:
            case_id = uuid.uuid4().hex
            reviewer_map[case_id] = query["query_id"]
            cases.append(
                {
                    "case_id": case_id,
                    "query": query["query"],
                    "authorized_scopes": sorted(query["notebook_scope"]),
                    "query_disposition": "UNDECIDED",
                    "pair_judgments": [],
                    "scope_exhaustively_reviewed": False,
                    "judgment_status": "UNJUDGED",
                    "reviewer_notes": "",
                }
            )
        secrets.SystemRandom().shuffle(cases)
        cases_by_reviewer[reviewer] = cases
        reconciliation[reviewer] = reviewer_map

    return {
        "schema_version": PACKET_SCHEMA,
        "source": {
            "dataset_version": dataset.get(
                "golden_set_version", dataset.get("version")
            ),
            "dataset_sha256": dataset_sha256,
            "qrels_version": qrels_file.get("version"),
            "qrels_sha256": qrels_sha256,
        },
        "counts": {
            "query_count": len(queries),
            "queries_with_legacy_qrels": qrel_query_count,
            "queries_without_legacy_qrels": len(queries) - qrel_query_count,
            "legacy_qrel_reference_count": qrel_reference_count,
            "query_count_by_scope": dict(sorted(query_counts.items())),
            "query_count_by_legacy_category": dict(sorted(category_counts.items())),
        },
        "corpus_snapshot": {
            "sha256": corpus_snapshot_sha256,
            **corpus_snapshot,
        },
        "review_policy": {
            "reviewers": ["reviewer_a", "reviewer_b"],
            "independent_reviews": True,
            "historical_qrels_are_not_disclosed": True,
            "historical_categories_tags_and_oracles_are_not_disclosed": True,
            "empty_pair_judgments_mean_unjudged_not_nonrelevant": True,
            "required_pair_grade_range": [0, 1, 2, 3],
            "required_query_dispositions": [
                "POSITIVE_IN_SCOPE",
                "OOD_GLOBAL",
                "NEGATIVE_WITHIN_SCOPE",
                "AMBIGUOUS",
            ],
            "production_or_runtime_modified": False,
            "embedding_or_retrieval_backend_executed": False,
        },
        "reviewer_packets": cases_by_reviewer,
        "restricted_reconciliation_map": reconciliation,
    }


def _write_bundle(bundle: Mapping[str, Any], output_dir: Path) -> None:
    if output_dir.exists():
        raise PacketError(f"Refusing to overwrite existing output: {output_dir}")
    output_dir.mkdir(parents=True)

    packet_hashes: dict[str, str] = {}
    for reviewer, cases in bundle["reviewer_packets"].items():
        packet = {
            "schema_version": PACKET_SCHEMA,
            "reviewer_alias": reviewer,
            "source": {
                "adjudication_batch": "backend-selection-v1",
            },
            "corpus_snapshot_sha256": bundle["corpus_snapshot"]["sha256"],
            "instructions": {
                "do_not_consult_historical_qrels_or_backend_outputs": True,
                "empty_pair_judgments_are_not_negative_labels": True,
                "judge_only_within_authorized_scopes": True,
                "record_chunk_content_evidence_and_rationale": True,
                "do_not_share_decisions_with_the_other_reviewer": True,
            },
            "cases": cases,
        }
        path = output_dir / f"{reviewer}.json"
        encoded = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
        path.write_text(encoded, encoding="utf-8")
        packet_hashes[reviewer] = _sha256_file(path)

    restricted = {
        "warning": "RESTRICTED: do not distribute with reviewer packets.",
        "mapping": bundle["restricted_reconciliation_map"],
    }
    restricted_path = output_dir / "restricted_reconciliation_map.json"
    restricted_path.write_text(
        json.dumps(restricted, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report = {
        "schema_version": "backend-selection-adjudication-evidence-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": bundle["source"],
        "counts": bundle["counts"],
        "corpus_snapshot": bundle["corpus_snapshot"],
        "review_policy": bundle["review_policy"],
        "reviewer_packet_sha256": packet_hashes,
        "restricted_reconciliation_map_sha256": _sha256_file(restricted_path),
        "status": "READY_FOR_HUMAN_ADJUDICATION",
        "limitations": [
            "The corpus fingerprint describes current persisted source/chunk rows, not a historical ACL.",
            "Historical qrels are quarantined from reviewers and are not adopted as ground truth.",
            "Human judgments and exhaustive pool closure remain outstanding.",
            "No embeddings, retrieval backends, dependencies, indexes, or production runtime were changed or executed.",
        ],
    }
    (output_dir / "evidence_manifest.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


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
        "--database",
        type=Path,
        default=ROOT / "data/web_state/knowledge_store.db",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "reports/backend_selection_adjudication_v1",
    )
    args = parser.parse_args(argv)

    try:
        dataset_bytes = args.dataset.read_bytes()
        qrels_bytes = args.qrels.read_bytes()
        dataset = json.loads(dataset_bytes)
        qrels_file = json.loads(qrels_bytes)
        database_uri = f"file:{args.database.resolve()}?mode=ro"
        connection = sqlite3.connect(database_uri, uri=True)
        try:
            bundle = build_bundle(
                dataset,
                qrels_file,
                connection,
                hashlib.sha256(dataset_bytes).hexdigest(),
                hashlib.sha256(qrels_bytes).hexdigest(),
            )
        finally:
            connection.close()
        _write_bundle(bundle, args.output_dir)
    except (OSError, sqlite3.Error, json.JSONDecodeError, PacketError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(json.dumps(bundle["counts"], ensure_ascii=False, indent=2))
    print(f"Packet bundle: {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
