"""Deterministic Content Parser and Backfill (Slice 6.0.5, Punto 1 & Tarea 3).

Parses ingested chunks into exact-identity curricular content units (exercises and sections)
and tags solution chunks deterministically without using any LLM.

Invariants:
- Strictly rule-based header and regex extraction.
- Ambiguity or overlapping headers -> status = ContentStatus.NEEDS_REVIEW. Never guess.
- Idempotent backfill with explicit cache invalidation.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType

logger = logging.getLogger(__name__)

# Regular expressions for guides and exercises
_RE_GUIDE_HEADER = re.compile(
    r"(?:TRABAJO\s+PR[AÁ]CTICO|GU[IÍ]A|TP)\s*(?:Nro\.?|Nº|N°)?\s*(\d+)",
    re.IGNORECASE,
)
_RE_EXERCISE_HEADER = re.compile(
    r"(?:^|\n)\s*(?:Ejercicio|Problema|Actividad)\s*([0-9]+[a-zA-Z]?(?:\.[0-9]+)?)\b[:.]?\s*(.*?)(?=\n\s*(?:Ejercicio|Problema|Actividad|\d+\.)|\Z)",
    re.IGNORECASE | re.DOTALL,
)
_RE_NUMBERED_ITEM = re.compile(
    r"(?:^|\n)\s*([0-9]{1,3})\.\s+([A-ZÁÉÍÓÚ][^\n]{10,})",
    re.DOTALL,
)

# Regular expressions for sections
_RE_SECTION_HEADER = re.compile(
    r"(?:^|\n)\s*(?:Secci[oó]n|Sec|Cap[ií]tulo|Cap)?\s*([0-9]+(?:\.[0-9]+)+)\.?\s+([A-ZÁÉÍÓÚ][^\n]+)",
)

# Solution indicators
_RE_SOLUTION_INDICATOR = re.compile(
    r"(?:^|\n)\s*(?:Soluci[oó]n|Resoluci[oó]n|Respuestas?|Solucionario)[:\s-]",
    re.IGNORECASE,
)


def _clean_source_prefix(source_id: str) -> str:
    """Derive a human-readable prefix from source_id."""
    clean = source_id.lower().replace("-", "_").replace("src_", "").replace("src_", "")
    if clean.startswith("src_"):
        clean = clean[4:]
    if clean.startswith("src-"):
        clean = clean[4:]
    return clean.split("_")[0] if "_" in clean else clean


def parse_content_items(chunks: List[Any], source_id: str) -> List[ContentItem]:
    """Deterministically extract ContentItem records from a list of chunks.

    Args:
        chunks: List of chunk objects or rows with id, content, pos_index, page_start, etc.
        source_id: The source identifier.

    Returns:
        List of parsed ContentItem instances.
    """
    if not chunks:
        return []

    items: List[ContentItem] = []
    source_prefix = _clean_source_prefix(source_id)

    # Sort chunks by pos_index or page_start
    sorted_chunks = sorted(
        chunks,
        key=lambda c: (
            getattr(c, "pos_index", 0) if getattr(c, "pos_index", None) is not None else 0,
            getattr(c, "page_start", 0) if getattr(c, "page_start", None) is not None else 0,
        ),
    )

    current_guide_num: Optional[str] = None
    is_guide_source = "guia" in source_id.lower() or "tp" in source_id.lower() or "practica" in source_id.lower()

    # Track currently open exercise item
    active_exercise: Optional[ContentItem] = None
    active_section: Optional[ContentItem] = None

    for chunk in sorted_chunks:
        c_id = getattr(chunk, "id", "") or str(chunk)
        content = getattr(chunk, "content", "") or ""
        chapter = getattr(chunk, "chapter", "") or ""
        section = getattr(chunk, "section", "") or ""

        # Check if chunk contains a guide header (e.g. TRABAJO PRACTICO Nro. 1)
        guide_match = _RE_GUIDE_HEADER.search(content)
        if guide_match:
            current_guide_num = guide_match.group(1)

        # Check for solution marker
        is_solution = bool(_RE_SOLUTION_INDICATOR.search(content)) or (
            "solucion" in section.lower() or "respuestas" in section.lower()
        )

        # --- A. Exercise Parsing ---
        if is_guide_source or current_guide_num or "ejercicio" in content.lower():
            # Check for explicit "Ejercicio X" headers
            ex_matches = list(_RE_EXERCISE_HEADER.finditer(content))
            if ex_matches:
                for match in ex_matches:
                    ex_num = match.group(1)
                    statement_snippet = match.group(2).strip()[:300]
                    guide_key = f"guia_{current_guide_num}" if current_guide_num else source_prefix
                    content_id = f"{guide_key}:ej_{ex_num}"

                    # Ambiguity check: if guide_num is unknown in a guide source, mark needs_review
                    status = ContentStatus.OK if current_guide_num or not is_guide_source else ContentStatus.NEEDS_REVIEW

                    active_exercise = ContentItem(
                        content_id=content_id,
                        source_id=source_id,
                        unit_type=UnitType.EXERCISE,
                        statement_text=statement_snippet or f"Ejercicio {ex_num}",
                        chunk_ids=[c_id],
                        solution_chunk_ids=[c_id] if is_solution else [],
                        status=status,
                        metadata={
                            "exercise_num": ex_num,
                            "guide_num": current_guide_num,
                            "page_start": getattr(chunk, "page_start", 1),
                        },
                    )
                    items.append(active_exercise)
                continue

            # Numbered list items in guides: "1. Suponga que..."
            if current_guide_num and not ex_matches:
                num_matches = list(_RE_NUMBERED_ITEM.finditer(content))
                if num_matches and len(num_matches) <= 3:  # Only if clean list item, not a table
                    for match in num_matches:
                        num = match.group(1)
                        snippet = match.group(2).strip()[:300]
                        content_id = f"guia_{current_guide_num}:ej_{num}"

                        active_exercise = ContentItem(
                            content_id=content_id,
                            source_id=source_id,
                            unit_type=UnitType.EXERCISE,
                            statement_text=snippet,
                            chunk_ids=[c_id],
                            solution_chunk_ids=[c_id] if is_solution else [],
                            status=ContentStatus.OK,
                            metadata={
                                "exercise_num": num,
                                "guide_num": current_guide_num,
                                "page_start": getattr(chunk, "page_start", 1),
                            },
                        )
                        items.append(active_exercise)
                    continue

        # If chunk is a solution for the current open exercise
        if is_solution and active_exercise:
            if c_id not in active_exercise.chunk_ids:
                active_exercise.chunk_ids.append(c_id)
            if active_exercise.solution_chunk_ids is None:
                active_exercise.solution_chunk_ids = []
            if c_id not in active_exercise.solution_chunk_ids:
                active_exercise.solution_chunk_ids.append(c_id)
            continue

        # --- B. Section Parsing ---
        sec_matches = list(_RE_SECTION_HEADER.finditer(content))
        if sec_matches:
            for match in sec_matches:
                sec_num = match.group(1)
                sec_title = match.group(2).strip()[:150]
                content_id = f"{source_prefix}:sec_{sec_num}"

                active_section = ContentItem(
                    content_id=content_id,
                    source_id=source_id,
                    unit_type=UnitType.SECTION,
                    statement_text=sec_title,
                    chunk_ids=[c_id],
                    solution_chunk_ids=[c_id] if is_solution else [],
                    status=ContentStatus.OK,
                    metadata={
                        "section_num": sec_num,
                        "section_title": sec_title,
                        "page_start": getattr(chunk, "page_start", 1),
                    },
                )
                items.append(active_section)
            continue

    # Deduplicate items by content_id, merging chunk_ids and solution_chunk_ids
    deduped: Dict[str, ContentItem] = {}
    for item in items:
        if item.content_id not in deduped:
            deduped[item.content_id] = item
        else:
            existing = deduped[item.content_id]
            for cid in item.chunk_ids:
                if cid not in existing.chunk_ids:
                    existing.chunk_ids.append(cid)
            if item.solution_chunk_ids:
                if existing.solution_chunk_ids is None:
                    existing.solution_chunk_ids = []
                for scid in item.solution_chunk_ids:
                    if scid not in existing.solution_chunk_ids:
                        existing.solution_chunk_ids.append(scid)
            # If any occurrence had needs_review, preserve needs_review
            if item.status == ContentStatus.NEEDS_REVIEW:
                existing.status = ContentStatus.NEEDS_REVIEW

    return list(deduped.values())


def backfill_content_registry(store: Any, force: bool = False) -> Dict[str, Any]:
    """Populates content_registry from existing chunks in the store idempotently.

    Args:
        store: KnowledgeStore instance.
        force: If True, clears existing registry entries before parsing.

    Returns:
        Summary statistics dictionary.
    """
    from study_engine.storage.content_registry import ContentRegistryRepository

    repo = ContentRegistryRepository(store.engine)

    if force:
        with store.engine.transaction() as conn:
            conn.execute("DELETE FROM content_registry;")
        repo.invalidate_solution_cache()

    # Fetch all chunks grouped by source_id
    with store.engine.transaction() as conn:
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT source_id FROM chunks;")
        source_ids = [row[0] for row in cur.fetchall()]

    stats: Dict[str, Any] = {
        "total_items": 0,
        "by_unit_type": {"exercise": 0, "section": 0},
        "by_status": {"ok": 0, "needs_review": 0},
        "by_source": {},
    }

    for src_id in source_ids:
        chunk_repo = getattr(store, "chunks", None) or getattr(getattr(store, "repositories", None), "chunks", None)
        if chunk_repo and hasattr(chunk_repo, "list_by_source"):
            chunks = chunk_repo.list_by_source(src_id)
        else:
            chunks = []
        parsed_items = parse_content_items(chunks, src_id)

        src_stats = {"total": len(parsed_items), "ok": 0, "needs_review": 0}

        for item in parsed_items:
            repo.save(item)
            stats["total_items"] += 1
            stats["by_unit_type"][item.unit_type.value] += 1
            stats["by_status"][item.status.value] += 1
            src_stats[item.status.value] += 1

        stats["by_source"][src_id] = src_stats

    # Invalidate repository solution chunk cache after backfill batch
    repo.invalidate_solution_cache()

    logger.info(
        "[CONTENT REGISTRY BACKFILL] Total indexed: %d (ok: %d, needs_review: %d)",
        stats["total_items"],
        stats["by_status"]["ok"],
        stats["by_status"]["needs_review"],
    )
    return stats
