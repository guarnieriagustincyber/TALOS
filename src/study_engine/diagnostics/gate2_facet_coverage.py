"""Facet-coverage summaries for query-scoped Gate 2 evidence reviews."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


class Gate2FacetCoverageError(ValueError):
    """Raised when a facet review references malformed or unknown evidence."""


def evaluate_facet_coverage(
    required_facets: Sequence[Mapping[str, object]],
    evidence_grades: Mapping[str, int],
    *,
    minimum_grade: int = 2,
) -> dict[str, Any]:
    """Summarize whether each query facet has sufficiently relevant evidence.

    This is a coverage calculation only. It does not adjudicate source
    independence, complementarity, query intent, or canonical sufficiency.
    """
    if isinstance(minimum_grade, bool) or not isinstance(minimum_grade, int):
        raise Gate2FacetCoverageError(
            "minimum_grade must be an integer from 0 to 3"
        )
    if not 0 <= minimum_grade <= 3:
        raise Gate2FacetCoverageError(
            "minimum_grade must be an integer from 0 to 3"
        )
    for evidence_id, grade in evidence_grades.items():
        if not isinstance(evidence_id, str) or not evidence_id:
            raise Gate2FacetCoverageError(
                "evidence IDs must be non-empty strings"
            )
        if (
            isinstance(grade, bool)
            or not isinstance(grade, int)
            or not 0 <= grade <= 3
        ):
            raise Gate2FacetCoverageError(
                f"Evidence grade for {evidence_id!r} must be an integer "
                "from 0 to 3"
            )

    seen_facets: set[str] = set()
    rows: list[dict[str, Any]] = []
    for facet in required_facets:
        facet_id = facet.get("facet_id")
        evidence_ids = facet.get("evidence_ids")
        if not isinstance(facet_id, str) or not facet_id:
            raise Gate2FacetCoverageError(
                "Each facet requires a non-empty facet_id"
            )
        if facet_id in seen_facets:
            raise Gate2FacetCoverageError(f"Duplicate facet_id: {facet_id!r}")
        seen_facets.add(facet_id)
        if not isinstance(evidence_ids, list) or not all(
            isinstance(evidence_id, str) and evidence_id
            for evidence_id in evidence_ids
        ):
            raise Gate2FacetCoverageError(
                f"Facet {facet_id!r} evidence_ids must be a list of "
                "non-empty strings"
            )
        unknown = [
            evidence_id
            for evidence_id in evidence_ids
            if evidence_id not in evidence_grades
        ]
        if unknown:
            raise Gate2FacetCoverageError(
                f"Facet {facet_id!r} references unknown evidence: {unknown}"
            )
        eligible = [
            evidence_id
            for evidence_id in evidence_ids
            if evidence_grades[evidence_id] >= minimum_grade
        ]
        rows.append(
            {
                "facet_id": facet_id,
                "eligible_evidence_ids": eligible,
                "covered": bool(eligible),
            }
        )

    uncovered = [row["facet_id"] for row in rows if not row["covered"]]
    return {
        "minimum_grade": minimum_grade,
        "facets": rows,
        "uncovered_facets": uncovered,
        "all_facets_covered": bool(rows) and not uncovered,
    }
