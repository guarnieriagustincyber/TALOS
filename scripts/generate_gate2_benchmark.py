#!/usr/bin/env python3
"""Normalize Gate 2 benchmark records without mutating historical datasets."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_engine.contracts.gate2_oracle import Gate2Dataset, Gate2OracleType
from study_engine.diagnostics.gate2_proposals import generate_qrel_proposals
from study_engine.diagnostics.gate2_snapshots import (
    create_snapshots,
    verify_sources_unchanged,
)
from study_engine.storage.knowledge_store import KnowledgeStore


class Gate2GeneratorError(ValueError):
    """Raised when the generator cannot safely normalize or publish a dataset."""


def _load_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise Gate2GeneratorError(f"Cannot load JSON from {path}: {exc}") from exc


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as exc:
        raise Gate2GeneratorError(f"Cannot hash {path}: {exc}") from exc
    return f"sha256:{digest.hexdigest()}"


def _queries(payload: Mapping[str, Any], path: Path) -> list[dict[str, Any]]:
    records = payload.get("queries")
    if not isinstance(records, list):
        raise Gate2GeneratorError(f"{path} must contain a queries list")
    if not all(isinstance(record, dict) for record in records):
        raise Gate2GeneratorError(f"{path} contains a non-object query")
    return records


def _qrels(payload: Mapping[str, Any], path: Path) -> dict[str, dict[str, int]]:
    records = payload.get("qrels")
    if not isinstance(records, dict):
        raise Gate2GeneratorError(f"{path} must contain a qrels object")
    normalized: dict[str, dict[str, int]] = {}
    for query_id, values in records.items():
        if not isinstance(query_id, str) or not isinstance(values, dict):
            raise Gate2GeneratorError(f"Invalid qrels entry for {query_id!r}")
        if not all(
            isinstance(chunk_id, str) and isinstance(grade, int)
            for chunk_id, grade in values.items()
        ):
            raise Gate2GeneratorError(f"Invalid qrel values for {query_id!r}")
        normalized[query_id] = dict(values)
    return normalized


def _historical_index(
    records: list[dict[str, Any]], label: str
) -> dict[str, dict[str, Any]]:
    result = {}
    for record in records:
        query_id = record.get("query_id", record.get("id"))
        if not isinstance(query_id, str) or not query_id.strip():
            raise Gate2GeneratorError(f"{label} contains a query without query_id")
        if query_id in result:
            raise Gate2GeneratorError(
                f"{label} contains duplicate query ID {query_id!r}"
            )
        result[query_id] = record
    return result


def _decision_for(
    decisions: Mapping[str, Any], query_id: str
) -> Mapping[str, Any] | None:
    decision = decisions.get(query_id)
    if decision is None:
        return None
    if not isinstance(decision, Mapping):
        raise Gate2GeneratorError(f"Decision for {query_id!r} must be an object")
    return decision


def _classify(
    record: Mapping[str, Any],
    decision: Mapping[str, Any] | None,
    previous: Mapping[str, Any] | None,
) -> tuple[str, str]:
    if decision is None:
        return "blocked", Gate2OracleType.POSITIVE_IN_SCOPE.value
    oracle_type = decision.get("oracle_type")
    if oracle_type not in {item.value for item in Gate2OracleType}:
        raise Gate2GeneratorError(
            f"Query {record.get('query_id')!r} has invalid oracle_type {oracle_type!r}"
        )
    status = decision.get("status", "pending")
    if status not in {"pending", "approved", "rejected", "blocked"}:
        raise Gate2GeneratorError(f"Invalid decision status {status!r}")
    if oracle_type == Gate2OracleType.NEGATIVE_BY_SCOPE.value and not decision.get(
        "evidence"
    ):
        raise Gate2GeneratorError(
            f"Negative-by-scope query {record.get('query_id')!r} needs evidence"
        )
    return status, oracle_type


def normalize_dataset(
    dataset_payload: Mapping[str, Any],
    qrels_payload: Mapping[str, Any],
    decisions_payload: Mapping[str, Any],
    *,
    version: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    current_records = _queries(dataset_payload, Path("dataset input"))
    historical = _historical_index(current_records, "dataset input")
    previous_records = decisions_payload.get("previous_queries", [])
    if not isinstance(previous_records, list):
        raise Gate2GeneratorError("previous_queries must be a list when provided")
    previous = _historical_index(previous_records, "previous_queries")
    decisions = decisions_payload.get("decisions", {})
    if not isinstance(decisions, Mapping):
        raise Gate2GeneratorError("decisions must be an object")
    historical_qrels = _qrels(qrels_payload, Path("qrels input"))
    if set(historical_qrels) != set(historical):
        raise Gate2GeneratorError("Historical dataset and qrels IDs do not match")

    normalized_records: list[dict[str, Any]] = []
    normalized_qrels: dict[str, dict[str, int]] = {}
    decision_rows: list[dict[str, Any]] = []
    for query_id, record in historical.items():
        decision = _decision_for(decisions, query_id)
        prior = previous.get(query_id)
        status, oracle_type = _classify(record, decision, prior)
        scope = decision.get("scope") if decision else None
        if not isinstance(scope, str) or not scope.strip():
            status = "blocked"
            scope = ""
        previous_scope = (
            prior.get("notebook_scope", [None])[0]
            if prior and isinstance(prior.get("notebook_scope"), list)
            else None
        )
        if (
            previous_scope
            and scope
            and previous_scope != scope
            and not decision.get("scope_decision_id")
        ):
            raise Gate2GeneratorError(
                f"Query {query_id!r} changes scope without scope_decision_id"
            )
        qrels = historical_qrels[query_id]
        if (
            status != "approved"
            or oracle_type != Gate2OracleType.POSITIVE_IN_SCOPE.value
        ):
            qrels = {}
        requested_provenance = (
            decision.get("qrels_provenance", "historical") if decision else "pending"
        )
        if requested_provenance not in {
            "historical",
            "fixture",
            "retrieval_proposal",
            "human_verified",
            "pending",
        }:
            raise Gate2GeneratorError(
                f"Query {query_id!r} has invalid qrels_provenance "
                f"{requested_provenance!r}"
            )
        if requested_provenance == "human_verified":
            if (
                status != "approved"
                or not decision.get("reviewer")
                or not decision.get("evidence")
            ):
                raise Gate2GeneratorError(
                    f"Human-verified qrels for {query_id!r} need approved status, "
                    "reviewer and evidence"
                )
        qrels_provenance = requested_provenance if status == "approved" else "pending"
        normalized_records.append(
            {
                "query_id": query_id,
                "query": record.get("query", ""),
                "scope": scope,
                "oracle_type": oracle_type,
                "kc_ids": record.get("kc_ids", []),
                "topic_anchors": record.get("topic_anchors", []),
                "previous_scope": previous_scope,
                "scope_decision_id": (
                    decision.get("scope_decision_id") if decision else None
                ),
                "qrels_status": status,
                "qrels_provenance": qrels_provenance,
                "reviewer": decision.get("reviewer") if decision else None,
                "notes": decision.get("notes") if decision else "Decision required",
            }
        )
        normalized_qrels[query_id] = qrels
        decision_rows.append(
            {
                "query_id": query_id,
                "scope": scope,
                "previous_scope": previous_scope,
                "oracle_type": oracle_type,
                "status": status,
                "scope_decision_id": (
                    decision.get("scope_decision_id") if decision else None
                ),
                "evidence": decision.get("evidence", []) if decision else [],
                "reviewer": decision.get("reviewer") if decision else None,
            }
        )

    counts = Counter(row["oracle_type"] for row in normalized_records)
    scope_counts = Counter(row["scope"] for row in normalized_records if row["scope"])
    metadata = {
        "total_queries": len(normalized_records),
        "by_oracle_type": dict(sorted(counts.items())),
        "by_scope": dict(sorted(scope_counts.items())),
        "qrel_queries": sum(bool(values) for values in normalized_qrels.values()),
    }
    dataset = {
        "version": version,
        "queries": normalized_records,
        "metadata": {"counts": metadata},
    }
    qrels = {
        "version": version,
        "total_queries": len(normalized_qrels),
        "qrels": normalized_qrels,
    }
    decisions = {"version": version, "decisions": decision_rows}
    return dataset, qrels, decisions


def _write_outputs(
    output_dir: Path,
    version: str,
    dataset: Mapping[str, Any],
    qrels: Mapping[str, Any],
    decisions: Mapping[str, Any],
    manifest: Mapping[str, Any],
    observations: Mapping[str, Any] | None = None,
) -> None:
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        raise Gate2GeneratorError(f"Output directory already exists: {output_dir}")
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent)
    )
    try:
        files = {
            f"gate2_{version}.dataset.json": dataset,
            f"gate2_{version}.qrels.json": qrels,
            f"gate2_{version}.decisions.json": decisions,
            f"gate2_{version}.manifest.json": manifest,
        }
        if observations is not None:
            files[f"gate2_{version}.observations.json"] = observations
        for name, payload in files.items():
            (temporary / name).write_text(
                json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
                + "\n",
                encoding="utf-8",
            )
        temporary.rename(output_dir)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise


def generate_fixture(
    dataset_path: Path,
    qrels_path: Path,
    decisions_path: Path,
    output_dir: Path,
    version: str,
) -> Path:
    if version == "v2.401":
        raise Gate2GeneratorError("The historical v2.401 version cannot be overwritten")
    input_paths = [dataset_path, qrels_path, decisions_path]
    if any(not path.is_file() for path in input_paths):
        missing = next(path for path in input_paths if not path.is_file())
        raise Gate2GeneratorError(f"Input file does not exist: {missing}")
    historical_root = (ROOT / "data" / "eval").resolve()
    try:
        output_dir.resolve().relative_to(historical_root)
    except ValueError:
        pass
    else:
        raise Gate2GeneratorError(
            "Output must be outside data/eval so historical artifacts remain protected"
        )
    dataset, qrels, decisions = normalize_dataset(
        _load_json(dataset_path),
        _load_json(qrels_path),
        _load_json(decisions_path),
        version=version,
    )
    Gate2Dataset.model_validate(dataset)
    manifest = {
        "version": version,
        "mode": "fixture",
        "inputs": {str(path): _sha256(path) for path in input_paths},
        "retrieval": {"executed": False},
    }
    _write_outputs(output_dir, version, dataset, qrels, decisions, manifest)
    return output_dir


def generate_snapshot_proposal(
    dataset_path: Path,
    qrels_path: Path,
    decisions_path: Path,
    output_dir: Path,
    version: str,
    knowledge_db: Path,
    vector_db: Path,
    retriever=None,
    *,
    top_k: int = 5,
    retriever_factory=None,
) -> Path:
    """Normalize records and write unapproved proposals from disposable snapshots."""
    if version == "v2.401":
        raise Gate2GeneratorError("The historical v2.401 version cannot be overwritten")
    historical_root = (ROOT / "data" / "eval").resolve()
    try:
        output_dir.resolve().relative_to(historical_root)
    except ValueError:
        pass
    else:
        raise Gate2GeneratorError(
            "Output must be outside data/eval so historical artifacts remain protected"
        )
    dataset, _, decisions = normalize_dataset(
        _load_json(dataset_path),
        _load_json(qrels_path),
        _load_json(decisions_path),
        version=version,
    )
    contract_dataset = Gate2Dataset.model_validate(dataset)
    temporary, snapshot_manifest = create_snapshots(knowledge_db, vector_db)
    store = None
    try:
        if retriever_factory is not None:
            store, retriever = retriever_factory(
                Path(snapshot_manifest["snapshots"]["knowledge_db"]["path"])
            )
        if retriever is None:
            raise Gate2GeneratorError("A snapshot retriever is required")
        report = generate_qrel_proposals(
            contract_dataset,
            Path(snapshot_manifest["snapshots"]["knowledge_db"]["path"]),
            retriever,
            top_k=top_k,
        )
        verify_sources_unchanged(snapshot_manifest, knowledge_db, vector_db)
        manifest = {
            "version": version,
            "mode": "proposal",
            "retrieval": report["metadata"],
            "snapshots": snapshot_manifest,
        }
        proposal_qrels = {
            "version": version,
            "total_queries": len(report["qrels"]),
            "qrels": report["qrels"],
            "metadata": report["metadata"],
        }
        _write_outputs(
            output_dir,
            version,
            dataset,
            proposal_qrels,
            decisions,
            manifest,
            {
                "version": version,
                "observations": report["observations"],
                "candidate_proposals": report["candidate_proposals"],
            },
        )
        return output_dir
    finally:
        if store is not None:
            store.engine.close()
        temporary.cleanup()


def _snapshot_fts_retriever(knowledge_snapshot: Path):
    store = KnowledgeStore(knowledge_snapshot)

    def retrieve(query: str, notebook_id: str, source_ids: list[str], top_k: int):
        rows = store.fts_search(
            query,
            notebook_id=notebook_id,
            limit=top_k,
            source_ids=source_ids,
        )
        return [
            {
                "chunk_id": row.chunk_id,
                "source_id": row.source_id,
                "score": getattr(row, "score", 1.0),
            }
            for row in rows
        ]

    return store, retrieve


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode", choices=("fixture", "proposal", "generate"), required=True
    )
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--decisions", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--knowledge-db", type=Path)
    parser.add_argument("--vector-db", type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument(
        "--allow-retrieval",
        action="store_true",
        help="Explicitly allow sequential retrieval from disposable snapshots",
    )
    args = parser.parse_args(argv)
    if args.mode == "fixture":
        generate_fixture(
            args.dataset, args.qrels, args.decisions, args.output_dir, args.version
        )
    elif args.mode == "proposal":
        if not args.allow_retrieval:
            raise Gate2GeneratorError(
                "proposal mode requires --allow-retrieval; no retrieval runs by default"
            )
        if args.knowledge_db is None or args.vector_db is None:
            raise Gate2GeneratorError(
                "proposal mode requires --knowledge-db and --vector-db"
            )
        if not 1 <= args.top_k <= 5:
            raise Gate2GeneratorError("--top-k must be between 1 and 5")
        generate_snapshot_proposal(
            args.dataset,
            args.qrels,
            args.decisions,
            args.output_dir,
            args.version,
            args.knowledge_db,
            args.vector_db,
            top_k=args.top_k,
            retriever_factory=_snapshot_fts_retriever,
        )
    else:
        raise Gate2GeneratorError(
            "generate mode is reserved for a later approved benchmark run"
        )
    print(args.output_dir)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Gate2GeneratorError as exc:
        print(f"Gate 2 generator failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
