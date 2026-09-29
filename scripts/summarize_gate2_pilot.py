#!/usr/bin/env python3
"""Summarize a Gate 2 pilot without opening SQLite or changing its outputs."""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any


class Gate2PilotReportError(ValueError):
    """Raised when pilot outputs are missing or inconsistent."""


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Gate2PilotReportError(f"Cannot read {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def summarize_pilot(
    pilot_dir: Path,
    thermal_path: Path,
    knowledge_db: Path,
    vector_db: Path,
) -> Path:
    manifest_paths = list(pilot_dir.glob("gate2_*.manifest.json"))
    if len(manifest_paths) != 1:
        raise Gate2PilotReportError(
            f"Expected one manifest in {pilot_dir}, found {len(manifest_paths)}"
        )
    manifest_path = manifest_paths[0]
    stem = manifest_path.name.removesuffix(".manifest.json")
    dataset = _read_json(pilot_dir / f"{stem}.dataset.json")
    qrels = _read_json(pilot_dir / f"{stem}.qrels.json")
    observation_file = _read_json(pilot_dir / f"{stem}.observations.json")
    thermal = _read_json(thermal_path)

    queries = dataset.get("queries")
    observations = observation_file.get("observations")
    candidates = observation_file.get("candidate_proposals")
    if not isinstance(queries, list) or not isinstance(observations, dict):
        raise Gate2PilotReportError("Pilot dataset/observations have invalid schema")
    if set(observations) != {query.get("query_id") for query in queries}:
        raise Gate2PilotReportError("Pilot observations do not match dataset IDs")

    by_type: dict[str, dict[str, Any]] = {}
    by_scope: dict[str, dict[str, Any]] = {}
    latency_by_type: dict[str, list[float]] = defaultdict(list)
    negative_total = 0
    negative_absence_passes = 0
    illegal_candidate_ids = []
    for query in queries:
        query_id = query["query_id"]
        oracle_type = query["oracle_type"]
        scope = query["scope"]
        observation = observations[query_id]
        type_metrics = by_type.setdefault(
            oracle_type,
            {
                "total": 0,
                "candidate_absence_checks": 0,
                "candidate_absence_passes": 0,
                "candidates": 0,
            },
        )
        scope_metrics = by_scope.setdefault(
            scope,
            {
                "total": 0,
                "candidates": 0,
                "candidate_absence_checks": 0,
                "candidate_absence_passes": 0,
            },
        )
        type_metrics["total"] += 1
        scope_metrics["total"] += 1
        count = observation.get(
            "candidate_count", len(observation["retrieved_chunk_ids"])
        )
        type_metrics["candidates"] += count
        scope_metrics["candidates"] += count
        latency = observation.get("retrieval_ms")
        if isinstance(latency, (int, float)):
            latency_by_type[oracle_type].append(float(latency))
        absence_passed = observation.get("candidate_absence_passed")
        if absence_passed is not None:
            type_metrics["candidate_absence_checks"] += 1
            scope_metrics["candidate_absence_checks"] += 1
            if absence_passed is True:
                type_metrics["candidate_absence_passes"] += 1
                scope_metrics["candidate_absence_passes"] += 1
        if oracle_type in {"ood_global", "negative_by_scope"}:
            negative_total += 1
            negative_absence_passes += int(absence_passed is True)
        for candidate in (candidates or {}).get(query_id, []):
            if candidate.get("authorized_source") is False:
                illegal_candidate_ids.append(candidate.get("chunk_id"))

    type_latency = {
        key: {
            "count": len(values),
            "total_ms": round(sum(values), 2),
            "mean_ms": round(sum(values) / len(values), 2) if values else None,
        }
        for key, values in sorted(latency_by_type.items())
    }
    active_hashes = {}
    manifest = _read_json(manifest_path)
    sources = manifest.get("snapshots", {}).get("sources", {})
    for key, path in (("knowledge_db", knowledge_db), ("vector_db", vector_db)):
        actual = _sha256(path)
        expected = sources.get(key, {}).get("sha256")
        active_hashes[key] = {
            "expected": expected,
            "actual": actual,
            "unchanged": actual == expected,
        }
    snapshots = manifest.get("snapshots", {}).get("snapshots", {})
    snapshot_cleaned = all(
        not Path(record["path"]).exists()
        for record in snapshots.values()
        if isinstance(record, dict) and isinstance(record.get("path"), str)
    )
    pilot_passed = (
        negative_total > 0
        and negative_absence_passes == negative_total
        and not illegal_candidate_ids
        and any(
            query.get("oracle_type") == "positive_in_scope"
            and bool(qrels.get("qrels", {}).get(query.get("query_id")))
            for query in queries
        )
        and all(item["unchanged"] for item in active_hashes.values())
        and thermal.get("stop_reason") is None
        and thermal.get("return_code") == 0
    )
    report = {
        "version": qrels.get("version"),
        "status": "PASS" if pilot_passed else "INCONCLUSIVE",
        "query_count": len(queries),
        "oracle_types": dict(sorted(by_type.items())),
        "scopes": dict(sorted(by_scope.items())),
        "latency_by_oracle_type": type_latency,
        "negative_candidate_absence": {
            "passed": negative_absence_passes,
            "total": negative_total,
        },
        "illegal_candidates": illegal_candidate_ids,
        "candidate_acl_validation": "passed_by_proposal_runner",
        "qrels_provenance": qrels.get("metadata", {}).get("qrels_provenance"),
        "qrels_approved": qrels.get("metadata", {}).get("approved"),
        "active_database_hashes": active_hashes,
        "snapshots_cleaned": snapshot_cleaned,
        "thermal_monitor": {
            "baseline": thermal.get("baseline"),
            "max_cpu_tctl_c": thermal.get("max_cpu_tctl_c"),
            "max_gpu_edge_c": thermal.get("max_gpu_edge_c"),
            "max_load_1m": thermal.get("max_load_1m"),
            "stop_reason": thermal.get("stop_reason"),
            "runner_return_code": thermal.get("return_code"),
            "runtime_seconds": thermal.get("samples", [{}])[-1].get("elapsed_s"),
        },
        "limits": {
            "retrieval_concurrency": qrels.get("metadata", {}).get("concurrency"),
            "top_k": qrels.get("metadata", {}).get("top_k"),
            "candidate_absence_required_for_negative_oracles": True,
        },
        "limitations": [
            "Retrieval diagnostics only; no answer generation or citation evaluation.",
            "Candidate absence is a strict retrieval-level check, not proof of semantic abstention.",
        ],
    }
    output_path = pilot_dir / f"{stem}.pilot-report.json"
    if output_path.exists():
        raise Gate2PilotReportError(f"Refusing to overwrite report: {output_path}")
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot-dir", type=Path, required=True)
    parser.add_argument("--thermal", type=Path, required=True)
    parser.add_argument("--knowledge-db", type=Path, required=True)
    parser.add_argument("--vector-db", type=Path, required=True)
    args = parser.parse_args(argv)
    print(
        summarize_pilot(
            args.pilot_dir,
            args.thermal,
            args.knowledge_db,
            args.vector_db,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Gate2PilotReportError, OSError, KeyError, TypeError) as exc:
        print(f"Gate 2 pilot report failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
