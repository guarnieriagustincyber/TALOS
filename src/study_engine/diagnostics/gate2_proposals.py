"""Sequential, snapshot-only qrel proposal generation for Gate 2."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
import math
from pathlib import Path
import resource
import sqlite3
import time
from typing import Any

from study_engine.contracts.gate2_oracle import Gate2Dataset, Gate2OracleType
from study_engine.diagnostics.gate2_snapshots import (
    Gate2SnapshotError,
    authorized_source_ids,
)


class Gate2ProposalError(ValueError):
    """Raised when a retrieval proposal violates snapshot or ACL invariants."""


Retriever = Callable[[str, str, list[str], int], Iterable[Any]]


def _candidate_value(candidate: Any, name: str) -> Any:
    if isinstance(candidate, Mapping):
        return candidate.get(name)
    return getattr(candidate, name, None)


def _chunk_sources(knowledge_snapshot: Path, chunk_ids: list[str]) -> dict[str, str]:
    if not chunk_ids:
        return {}
    connection = sqlite3.connect(
        f"file:{Path(knowledge_snapshot).resolve()}?mode=ro", uri=True
    )
    try:
        placeholders = ",".join("?" for _ in chunk_ids)
        rows = connection.execute(
            f"SELECT id, source_id FROM chunks WHERE id IN ({placeholders})",
            chunk_ids,
        ).fetchall()
    except sqlite3.Error as exc:
        raise Gate2ProposalError(
            f"Cannot inspect chunks in snapshot {knowledge_snapshot}: {exc}"
        ) from exc
    finally:
        connection.close()
    return {row[0]: row[1] for row in rows}


def generate_qrel_proposals(
    dataset: Gate2Dataset,
    knowledge_snapshot: Path,
    retriever: Retriever,
    *,
    top_k: int = 5,
) -> dict[str, Any]:
    """Generate unapproved qrel proposals using only a knowledge snapshot.

    The retriever is injected so tests can use deterministic fixtures. It must
    receive the query, notebook scope, authorized source IDs and bounded
    ``top_k``. Approved negative oracle classes are queried for diagnostics,
    but their candidates are never written to qrels.
    """
    if not 1 <= top_k <= 5:
        raise Gate2ProposalError("Gate 2 proposal top_k must be between 1 and 5")

    proposals: dict[str, dict[str, int]] = {}
    observations: dict[str, dict[str, Any]] = {}
    candidate_proposals: dict[str, list[dict[str, Any]]] = {}
    for query in dataset.queries:
        if not query.scope:
            raise Gate2ProposalError(f"Query {query.query_id!r} has no snapshot scope")
        if query.qrels_status != "approved":
            proposals[query.query_id] = {}
            observations[query.query_id] = {
                "retrieved_chunk_ids": [],
                "citation_ids": [],
                "oracle_type": query.oracle_type.value,
                "status": "decision_pending",
                "expected_no_candidates": query.oracle_type
                != Gate2OracleType.POSITIVE_IN_SCOPE,
                "candidate_absence_passed": None,
            }
            candidate_proposals[query.query_id] = []
            continue
        try:
            source_ids = authorized_source_ids(knowledge_snapshot, query.scope)
        except Gate2SnapshotError as exc:
            raise Gate2ProposalError(str(exc)) from exc
        if not source_ids:
            raise Gate2ProposalError(
                f"Query {query.query_id!r} has no authorized sources"
            )

        started = time.perf_counter()
        candidates = list(retriever(query.query, query.scope, source_ids, top_k))
        elapsed_ms = (time.perf_counter() - started) * 1000
        if len(candidates) > top_k:
            raise Gate2ProposalError(
                f"Retriever returned {len(candidates)} candidates for {query.query_id!r}; "
                f"expected at most {top_k}"
            )
        chunk_ids = []
        candidate_rows: list[dict[str, Any]] = []
        for candidate in candidates:
            chunk_id = _candidate_value(candidate, "chunk_id")
            source_id = _candidate_value(candidate, "source_id")
            score = _candidate_value(candidate, "score")
            if not isinstance(chunk_id, str) or not chunk_id:
                raise Gate2ProposalError(
                    f"Retriever returned an invalid chunk for {query.query_id!r}"
                )
            if chunk_id in chunk_ids:
                raise Gate2ProposalError(
                    f"Retriever returned duplicate chunk {chunk_id!r}"
                )
            if source_id not in source_ids:
                raise Gate2ProposalError(
                    f"Retriever returned chunk {chunk_id!r} outside scope {query.scope!r}"
                )
            if not isinstance(score, (int, float)) or score != score:
                raise Gate2ProposalError(
                    f"Retriever returned invalid score for chunk {chunk_id!r}"
                )
            if isinstance(score, bool) or not math.isfinite(float(score)):
                raise Gate2ProposalError(
                    f"Retriever returned invalid score for chunk {chunk_id!r}"
                )
            chunk_ids.append(chunk_id)
            candidate_rows.append(
                {
                    "chunk_id": chunk_id,
                    "source_id": source_id,
                    "rank": len(candidate_rows) + 1,
                    "retrieval_score": float(score),
                    "authorized_source": True,
                    "proposed_grade": 1,
                    "grade_status": "pending_human_review",
                }
            )

        existing_sources = _chunk_sources(knowledge_snapshot, chunk_ids)
        missing = sorted(set(chunk_ids) - set(existing_sources))
        if missing:
            raise Gate2ProposalError(
                f"Retriever returned missing chunks: {', '.join(missing)}"
            )
        illegal = {
            chunk_id: source_id
            for chunk_id, source_id in existing_sources.items()
            if source_id not in source_ids
        }
        if illegal:
            raise Gate2ProposalError(f"Snapshot chunk sources violate ACL: {illegal}")
        scores = {row["chunk_id"]: 1 for row in candidate_rows}
        positive = query.oracle_type == Gate2OracleType.POSITIVE_IN_SCOPE
        proposals[query.query_id] = scores if positive else {}
        candidate_proposals[query.query_id] = candidate_rows
        no_candidate_expected = not positive
        observations[query.query_id] = {
            "retrieved_chunk_ids": chunk_ids,
            "citation_ids": [],
            "oracle_type": query.oracle_type.value,
            "status": (
                "retrieval_proposal"
                if positive
                else (
                    "scope_isolation_check"
                    if query.oracle_type == Gate2OracleType.NEGATIVE_BY_SCOPE
                    else "global_ood_check"
                )
            ),
            "expected_no_candidates": no_candidate_expected,
            "candidate_absence_passed": (
                not chunk_ids if no_candidate_expected else None
            ),
            "candidate_count": len(chunk_ids),
            "retrieval_ms": round(elapsed_ms, 2),
        }

    return {
        "qrels": proposals,
        "observations": observations,
        "candidate_proposals": candidate_proposals,
        "metadata": {
            "retrieval_executed": True,
            "concurrency": 1,
            "top_k": top_k,
            "qrels_provenance": "retrieval_proposal",
            "approved": False,
            "negative_oracle_checks_executed": True,
            "citation_evaluation": False,
            "process_cpu_user_seconds": round(
                resource.getrusage(resource.RUSAGE_SELF).ru_utime, 3
            ),
            "process_cpu_system_seconds": round(
                resource.getrusage(resource.RUSAGE_SELF).ru_stime, 3
            ),
            "process_peak_rss_mb": round(
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1
            ),
        },
    }
