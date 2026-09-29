#!/usr/bin/env python3
"""Audit topical support for Gate 2 pilot candidates without retrieval."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import sys
import unicodedata
from typing import Any


class Gate2CandidateAuditError(ValueError):
    """Raised when pilot candidate evidence cannot be audited safely."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Gate2CandidateAuditError(f"Cannot read {path}: {exc}") from exc


def _normalized_tokens(text: str) -> list[str]:
    normalized = unicodedata.normalize("NFD", text.lower())
    normalized = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return re.findall(r"[a-z0-9]+", normalized)


def _anchor_matches(content: str, anchors: list[str]) -> list[str]:
    content_tokens = _normalized_tokens(content)
    matches = []
    for anchor in anchors:
        anchor_tokens = _normalized_tokens(anchor)
        if not anchor_tokens:
            continue
        width = len(anchor_tokens)
        if any(
            content_tokens[index : index + width] == anchor_tokens
            for index in range(len(content_tokens) - width + 1)
        ):
            matches.append(anchor)
    return matches


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _fetch_chunks(
    connection: sqlite3.Connection,
    chunk_ids: list[str],
    notebook_id: str,
) -> dict[str, dict[str, Any]]:
    results = {}
    for chunk_id in chunk_ids:
        row = connection.execute(
            "SELECT c.id, c.source_id, c.content, s.title, "
            "EXISTS(SELECT 1 FROM notebook_sources ns "
            "WHERE ns.notebook_id = ? AND ns.source_id = c.source_id) "
            "FROM chunks c LEFT JOIN sources s ON s.source_id = c.source_id "
            "WHERE c.id = ?",
            (notebook_id, chunk_id),
        ).fetchone()
        if row:
            results[chunk_id] = {
                "chunk_id": row[0],
                "source_id": row[1],
                "content": row[2],
                "source_title": row[3],
                "authorized": bool(row[4]),
            }
    return results


def audit_candidates(
    dataset_path: Path,
    observations_path: Path,
    knowledge_db: Path,
    historical_qrels_path: Path | None = None,
) -> dict[str, Any]:
    dataset = _read_json(dataset_path)
    observation_payload = _read_json(observations_path)
    queries = dataset.get("queries")
    observations = observation_payload.get("observations")
    candidates_by_query = observation_payload.get("candidate_proposals")
    if not isinstance(queries, list) or not isinstance(observations, dict):
        raise Gate2CandidateAuditError("Invalid dataset or observations schema")
    if not isinstance(candidates_by_query, dict):
        raise Gate2CandidateAuditError("Candidate proposal map is missing")
    historical_qrels = {}
    if historical_qrels_path:
        historical_payload = _read_json(historical_qrels_path)
        historical_qrels = historical_payload.get("qrels")
        if not isinstance(historical_qrels, dict):
            raise Gate2CandidateAuditError(
                "Historical qrels must contain a qrels object"
            )

    connection = sqlite3.connect(
        f"file:{Path(knowledge_db).resolve()}?mode=ro", uri=True
    )
    connection.row_factory = sqlite3.Row
    try:
        rows = []
        for query in queries:
            query_id = query["query_id"]
            scope = query["scope"]
            anchors = query.get("topic_anchors", [])
            if not isinstance(anchors, list) or not all(
                isinstance(anchor, str) and anchor.strip() for anchor in anchors
            ):
                raise Gate2CandidateAuditError(
                    f"Invalid topic anchors for query {query_id!r}"
                )
            observation = observations.get(query_id)
            if not isinstance(observation, dict):
                raise Gate2CandidateAuditError(
                    f"Missing observation for query {query_id!r}"
                )
            candidate_ids = observation.get("retrieved_chunk_ids", [])
            chunks = _fetch_chunks(connection, candidate_ids, scope)
            candidate_rows = []
            for chunk_id in candidate_ids:
                chunk = chunks.get(chunk_id)
                if chunk is None:
                    candidate_rows.append(
                        {
                            "chunk_id": chunk_id,
                            "exists": False,
                            "authorized": False,
                            "topic_anchor_matches": [],
                            "topic_supported": False,
                        }
                    )
                    continue
                matches = _anchor_matches(chunk["content"], anchors)
                candidate_rows.append(
                    {
                        "chunk_id": chunk_id,
                        "source_id": chunk["source_id"],
                        "source_title": chunk["source_title"],
                        "exists": True,
                        "authorized": chunk["authorized"],
                        "topic_anchor_matches": matches,
                        "topic_supported": bool(matches),
                        "content_sha256": hashlib.sha256(
                            chunk["content"].encode("utf-8")
                        ).hexdigest(),
                    }
                )

            historical_rows = []
            for chunk_id, grade in historical_qrels.get(query_id, {}).items():
                historical_chunk = _fetch_chunks(connection, [chunk_id], scope).get(
                    chunk_id
                )
                matches = (
                    _anchor_matches(historical_chunk["content"], anchors)
                    if historical_chunk
                    else []
                )
                historical_rows.append(
                    {
                        "chunk_id": chunk_id,
                        "historical_grade": grade,
                        "exists": historical_chunk is not None,
                        "authorized": (
                            historical_chunk["authorized"]
                            if historical_chunk
                            else False
                        ),
                        "source_id": (
                            historical_chunk["source_id"] if historical_chunk else None
                        ),
                        "source_title": (
                            historical_chunk["source_title"]
                            if historical_chunk
                            else None
                        ),
                        "topic_anchor_matches": matches,
                        "topic_supported": bool(matches),
                        "adjudication_recommendation": (
                            "review_keep_as_topic_supported"
                            if matches
                            else "review_remove_as_unrelated_qrel"
                        ),
                    }
                )
            rows.append(
                {
                    "query_id": query_id,
                    "oracle_type": query["oracle_type"],
                    "scope": scope,
                    "topic_anchors": anchors,
                    "retrieved_candidate_count": len(candidate_rows),
                    "topic_supported_candidate_count": sum(
                        row["topic_supported"] for row in candidate_rows
                    ),
                    "irrelevant_candidate_count": sum(
                        not row["topic_supported"] for row in candidate_rows
                    ),
                    "unauthorized_candidate_count": sum(
                        row.get("exists") and not row["authorized"]
                        for row in candidate_rows
                    ),
                    "retrieved_candidates": candidate_rows,
                    "historical_qrels": historical_rows,
                }
            )
    except sqlite3.Error as exc:
        raise Gate2CandidateAuditError(
            f"Cannot inspect the knowledge database read-only: {exc}"
        ) from exc
    finally:
        connection.close()

    return {
        "dataset_version": dataset.get("golden_set_version", dataset.get("version")),
        "knowledge_db_sha256": _hash(knowledge_db),
        "method": "curated exact-token phrase anchors; no retrieval executed",
        "queries": rows,
        "limitations": [
            "Anchor matching is a transparent lexical audit, not semantic relevance adjudication.",
            "Recommendations are advisory and do not rewrite historical qrels.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--observations", type=Path, required=True)
    parser.add_argument("--knowledge-db", type=Path, required=True)
    parser.add_argument("--historical-qrels", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise Gate2CandidateAuditError(f"Output already exists: {args.output}")
    report = audit_candidates(
        args.dataset,
        args.observations,
        args.knowledge_db,
        args.historical_qrels,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Gate2CandidateAuditError, OSError, KeyError, TypeError) as exc:
        print(f"Gate 2 candidate audit failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
