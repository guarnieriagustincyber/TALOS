#!/usr/bin/env python3
"""Prepare a review-only Gate 2 decision template without opening databases."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


class Gate2PreflightError(ValueError):
    """Raised when historical benchmark inputs cannot be reconciled safely."""


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Gate2PreflightError(f"Cannot read JSON {path}: {exc}") from exc


def _hash(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest}"


def prepare_decision_template(
    dataset_path: Path, qrels_path: Path, output_path: Path
) -> Path:
    dataset = _load(dataset_path)
    qrels = _load(qrels_path)
    queries = dataset.get("queries")
    qrel_map = qrels.get("qrels")
    if not isinstance(queries, list) or not isinstance(qrel_map, dict):
        raise Gate2PreflightError("Dataset queries and qrels.qrels are required")

    query_ids = []
    decisions = {}
    for record in queries:
        if not isinstance(record, dict) or not isinstance(record.get("query_id"), str):
            raise Gate2PreflightError("Every historical query needs a string query_id")
        query_id = record["query_id"]
        if query_id in query_ids:
            raise Gate2PreflightError(f"Duplicate query ID: {query_id}")
        query_ids.append(query_id)
        decisions[query_id] = {
            "scope": None,
            "oracle_type": None,
            "status": "blocked",
            "scope_decision_id": None,
            "evidence": [],
            "reviewer": None,
            "notes": "Requires curricular review; not approved for retrieval.",
        }

    qrel_ids = set(qrel_map)
    missing = sorted(set(query_ids) - qrel_ids)
    unknown = sorted(qrel_ids - set(query_ids))
    if missing or unknown:
        raise Gate2PreflightError(
            f"Dataset/qrels IDs do not match; missing={missing}, unknown={unknown}"
        )

    output = {
        "purpose": "Gate 2 review-only decision template",
        "status": "blocked_pending_curricular_review",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_hashes": {
            "dataset": _hash(dataset_path),
            "qrels": _hash(qrels_path),
        },
        "previous_queries": queries,
        "decisions": decisions,
        "coverage": {
            "total_queries": len(query_ids),
            "qrels_entries": len(qrel_ids),
            "missing_qrels": missing,
            "unknown_qrels": unknown,
        },
        "instructions": [
            "Assign exactly one approved scope and oracle_type per query.",
            "Use negative_by_scope only with explicit curricular evidence.",
            "Do not mark positive_in_scope approved until qrels are regenerated under that ACL.",
            "Keep ambiguous queries blocked.",
        ],
    }
    if output_path.exists():
        raise Gate2PreflightError(f"Output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(output, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(prepare_decision_template(args.dataset, args.qrels, args.output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Gate2PreflightError as exc:
        print(f"Gate 2 preflight failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
