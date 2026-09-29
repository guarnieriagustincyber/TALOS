"""Human-review signals for duplicate-like Gate 2 evidence passages."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
import hashlib
from itertools import islice
import math
import re
import sqlite3
from pathlib import Path
from typing import Any

try:
    from rapidfuzz import fuzz
except ImportError as exc:
    raise ImportError(
        "Install the optional Gate 2 diagnostic dependency with "
        "`pip install -e '.[gate2-diagnostics]'`"
    ) from exc


class Gate2EvidenceRelationError(ValueError):
    """Raised when evidence metadata or similarity thresholds are invalid."""


@dataclass(frozen=True)
class EvidenceRecord:
    """Text and provenance needed to compare two evidence candidates."""

    evidence_id: str
    text: str
    source_id: str
    document_id: str
    author: str | None = None
    page_start: int | None = None
    page_end: int | None = None


_TOKEN_PATTERN = re.compile(r"\w+", flags=re.UNICODE)
MAX_EVIDENCE_RECORDS = 100


def _normalized_tokens(text: str) -> list[str]:
    return _TOKEN_PATTERN.findall(text.casefold())


def _simhash(tokens: list[str], *, bits: int = 64) -> int:
    if not tokens:
        return 0
    shingles = [
        " ".join(tokens[index:index + 3])
        for index in range(max(1, len(tokens) - 2))
    ]
    weights = [0] * bits
    for shingle in shingles:
        digest = hashlib.blake2b(
            shingle.encode("utf-8"), digest_size=8
        ).digest()
        value = int.from_bytes(digest, "big")
        for bit in range(bits):
            weights[bit] += 1 if value & (1 << bit) else -1
    return sum(1 << bit for bit, weight in enumerate(weights) if weight >= 0)


def _validate_record(record: EvidenceRecord) -> None:
    if not isinstance(record, EvidenceRecord):
        raise Gate2EvidenceRelationError(
            "records must be EvidenceRecord instances"
        )
    for field_name in ("evidence_id", "source_id", "document_id"):
        value = getattr(record, field_name)
        if not isinstance(value, str) or not value.strip():
            raise Gate2EvidenceRelationError(
                f"{field_name} must be a non-empty string"
            )
    if not isinstance(record.text, str):
        raise Gate2EvidenceRelationError("text must be a string")
    if not record.text.strip():
        raise Gate2EvidenceRelationError("text must be non-empty")
    if not _normalized_tokens(record.text):
        raise Gate2EvidenceRelationError(
            "text must contain at least one word token"
        )
    if record.author is not None and not isinstance(record.author, str):
        raise Gate2EvidenceRelationError("author must be a string or None")
    for field_name in ("page_start", "page_end"):
        value = getattr(record, field_name)
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, int) or value < 0
        ):
            raise Gate2EvidenceRelationError(
                f"{field_name} must be a non-negative integer or None"
            )
    if (
        record.page_start is not None
        and record.page_end is not None
        and record.page_end < record.page_start
    ):
        raise Gate2EvidenceRelationError("page_end cannot precede page_start")


def compare_evidence_records(
    left: EvidenceRecord,
    right: EvidenceRecord,
    *,
    minimum_text_similarity: float = 0.88,
    maximum_simhash_distance: int = 16,
) -> dict[str, Any]:
    """Return duplicate-like signals without deciding evidence independence.

    Similarity and provenance are review cues only. Neither a high score nor
    shared provenance proves that two passages are epistemically identical.
    """
    _validate_record(left)
    _validate_record(right)
    if left.evidence_id == right.evidence_id:
        raise Gate2EvidenceRelationError(
            "evidence records must have distinct IDs"
        )
    _validate_thresholds(minimum_text_similarity, maximum_simhash_distance)

    left_tokens = _normalized_tokens(left.text)
    right_tokens = _normalized_tokens(right.text)
    left_text = " ".join(left_tokens)
    right_text = " ".join(right_tokens)
    ratio = (
        fuzz.ratio(left_text, right_text) / 100
        if left_text or right_text
        else 1.0
    )
    token_set_ratio = (
        fuzz.token_set_ratio(left_text, right_text) / 100
        if left_text or right_text
        else 1.0
    )
    simhash_distance = (
        _simhash(left_tokens) ^ _simhash(right_tokens)
    ).bit_count()

    same_source = left.source_id == right.source_id
    same_document = left.document_id == right.document_id
    same_page = (
        left.page_start is not None
        and left.page_end is not None
        and right.page_start is not None
        and right.page_end is not None
        and left.page_start <= right.page_end
        and right.page_start <= left.page_end
        and same_source
    )
    exact_text_match = left_text == right_text
    near_duplicate_signal = (
        exact_text_match
        or (
            ratio >= minimum_text_similarity
            and simhash_distance <= maximum_simhash_distance
        )
    )

    reasons = []
    if same_source:
        reasons.append("same_source_id")
    if same_document:
        reasons.append("same_document")
    if same_page:
        reasons.append("overlapping_page_range")
    if exact_text_match:
        reasons.append("normalized_text_match")
    if ratio >= minimum_text_similarity:
        reasons.append("high_text_similarity")
    if simhash_distance <= maximum_simhash_distance:
        reasons.append("low_simhash_distance")

    relation = (
        "REVIEW_POSSIBLE_DUPLICATE"
        if near_duplicate_signal
        else (
            "REVIEW_SHARED_PROVENANCE"
            if same_source or same_document or same_page
            else "NO_STRONG_TEXT_DUPLICATE_SIGNAL"
        )
    )
    return {
        "evidence_ids": [left.evidence_id, right.evidence_id],
        "relation": relation,
        "text_similarity_ratio": round(ratio, 4),
        "token_set_similarity_ratio": round(token_set_ratio, 4),
        "simhash_distance": simhash_distance,
        "provenance": {
            "same_source_id": same_source,
            "same_document": same_document,
            "overlapping_page_range": same_page,
            "same_author": (
                left.author is not None
                and right.author is not None
                and left.author.casefold() == right.author.casefold()
            ),
        },
        "reasons": reasons,
        "independence_decision": "NOT_ADJUDICATED",
        "qrel_actions": "NOT_PRODUCED",
        "canonical_decision": None,
        "human_review_required": True,
    }


def _validate_thresholds(
    minimum_text_similarity: float,
    maximum_simhash_distance: int,
) -> None:
    if (
        isinstance(minimum_text_similarity, bool)
        or not isinstance(minimum_text_similarity, (int, float))
        or not math.isfinite(minimum_text_similarity)
        or not 0 <= minimum_text_similarity <= 1
    ):
        raise Gate2EvidenceRelationError(
            "minimum_text_similarity must be between 0 and 1"
        )
    if (
        isinstance(maximum_simhash_distance, bool)
        or not isinstance(maximum_simhash_distance, int)
        or not 0 <= maximum_simhash_distance <= 64
    ):
        raise Gate2EvidenceRelationError(
            "maximum_simhash_distance must be an integer from 0 to 64"
        )


def load_evidence_records(
    database_path: Path,
    evidence_ids: Iterable[str],
) -> list[EvidenceRecord]:
    """Load chunk text and provenance from SQLite in read-only mode."""
    requested_ids = list(islice(evidence_ids, MAX_EVIDENCE_RECORDS + 1))
    if len(requested_ids) > MAX_EVIDENCE_RECORDS:
        raise Gate2EvidenceRelationError(
            f"At most {MAX_EVIDENCE_RECORDS} evidence IDs can be loaded "
            "per diagnostic batch"
        )
    if any(
        not isinstance(evidence_id, str) or not evidence_id
        for evidence_id in requested_ids
    ):
        raise Gate2EvidenceRelationError(
            "evidence_ids must contain non-empty strings"
        )
    ids = list(dict.fromkeys(requested_ids))
    if not ids:
        return []

    uri = f"file:{Path(database_path).resolve().as_posix()}?mode=ro"
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(uri, uri=True)
        connection.row_factory = sqlite3.Row
        placeholders = ",".join("?" for _ in ids)
        rows = connection.execute(
            f"""
            SELECT
                chunks.id AS evidence_id,
                chunks.content AS text,
                chunks.source_id AS source_id,
                chunks.document_id AS document_id,
                sources.author AS author,
                chunks.page_start AS page_start,
                chunks.page_end AS page_end
            FROM chunks
            JOIN sources ON sources.source_id = chunks.source_id
            WHERE chunks.id IN ({placeholders})
            """,
            ids,
        ).fetchall()
    except sqlite3.Error as exc:
        raise Gate2EvidenceRelationError(
            f"Cannot read evidence from {database_path}: {exc}"
        ) from exc
    finally:
        if connection is not None:
            connection.close()

    records = {
        row["evidence_id"]: EvidenceRecord(
            evidence_id=row["evidence_id"],
            text=row["text"],
            source_id=row["source_id"],
            document_id=row["document_id"],
            author=row["author"],
            page_start=row["page_start"],
            page_end=row["page_end"],
        )
        for row in rows
    }
    missing = [
        evidence_id for evidence_id in ids if evidence_id not in records
    ]
    if missing:
        raise Gate2EvidenceRelationError(
            f"Evidence IDs not found in knowledge store: {missing}"
        )
    return [records[evidence_id] for evidence_id in ids]


def analyze_evidence_relations(
    records: Iterable[EvidenceRecord],
    *,
    minimum_text_similarity: float = 0.88,
    maximum_simhash_distance: int = 16,
) -> dict[str, Any]:
    """Compare unique pairs while preserving a human-review boundary."""
    _validate_thresholds(minimum_text_similarity, maximum_simhash_distance)
    evidence = list(islice(records, MAX_EVIDENCE_RECORDS + 1))
    if len(evidence) > MAX_EVIDENCE_RECORDS:
        raise Gate2EvidenceRelationError(
            f"At most {MAX_EVIDENCE_RECORDS} evidence records can be "
            "analyzed per diagnostic batch"
        )
    for record in evidence:
        _validate_record(record)
    ids = [record.evidence_id for record in evidence]
    if len(ids) != len(set(ids)):
        raise Gate2EvidenceRelationError("evidence IDs must be unique")

    pairs = []
    for left_index, left in enumerate(evidence):
        for right in evidence[left_index + 1:]:
            pairs.append(
                compare_evidence_records(
                    left,
                    right,
                    minimum_text_similarity=minimum_text_similarity,
                    maximum_simhash_distance=maximum_simhash_distance,
                )
            )
    return {
        "evidence_ids": ids,
        "pairs": pairs,
        "qrel_actions": "NOT_PRODUCED",
        "independence_adjudication": "NOT_PERFORMED",
        "canonical_decision": None,
        "human_review_required": True,
    }
