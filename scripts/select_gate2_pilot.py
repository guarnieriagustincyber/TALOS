#!/usr/bin/env python3
"""Select auditable Gate 2 pilot candidates without approving scope decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


def _hash(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def select_candidates(dataset_path: Path, qrels_path: Path, output_path: Path) -> Path:
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    qrels = json.loads(qrels_path.read_text(encoding="utf-8"))["qrels"]
    queries = dataset["queries"]
    positives = [
        query
        for query in queries
        if query.get("category") != "ood_trampas"
        and query.get("notebook_scope")
        and qrels.get(query["query_id"])
    ]
    ood = [
        query
        for query in queries
        if query.get("category") == "ood_trampas"
        and not qrels.get(query["query_id"])
    ]
    negative_candidates = [
        query
        for query in queries
        if query.get("category") != "ood_trampas"
        and query.get("expected", {}).get("abstention") is True
        and not qrels.get(query["query_id"])
    ]
    if not positives or not ood:
        raise ValueError("Historical inputs lack a positive or OOD candidate")
    selected_positive = positives[0]
    selected_ood = ood[0]
    selected_negative = negative_candidates[0] if negative_candidates else None
    report: dict[str, Any] = {
        "status": "blocked_pending_negative_scope_review",
        "source_hashes": {
            "dataset": _hash(dataset_path),
            "qrels": _hash(qrels_path),
        },
        "candidates": {
            "positive_in_scope": {
                "query_id": selected_positive["query_id"],
                "scope": selected_positive["notebook_scope"][0],
                "qrel_count": len(qrels[selected_positive["query_id"]]),
                "selection_basis": "historical non-OOD query with non-empty qrels",
            },
            "ood_global": {
                "query_id": selected_ood["query_id"],
                "scope": selected_ood["notebook_scope"][0],
                "qrel_count": 0,
                "selection_basis": "historical ood_trampas query with empty qrels",
            },
            "negative_by_scope": {
                "query_id": selected_negative["query_id"]
                if selected_negative
                else None,
                "scope": selected_negative["notebook_scope"][0]
                if selected_negative
                else None,
                "qrel_count": 0,
                "selection_basis": (
                    "candidate only; historical abstention is insufficient "
                    "evidence for negative_by_scope"
                ),
                "approved": False,
                "blocker": (
                    "Confirm that the topic exists outside the declared ACL "
                    "before assigning negative_by_scope"
                ),
            },
        },
        "pilot_authorized": False,
        "required_before_retrieval": [
            "Approve a curricular decision for the positive query.",
            "Approve the OOD oracle explicitly.",
            "Confirm the negative-by-scope topic outside the ACL.",
            "Use --allow-retrieval --top-k 1 only after all three decisions.",
        ],
    }
    if output_path.exists():
        raise ValueError(f"Output already exists: {output_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    print(select_candidates(args.dataset, args.qrels, args.output))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Gate 2 pilot selection failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
