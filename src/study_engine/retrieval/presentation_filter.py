"""Presentation Filter and Anti-Leakage Guard (Slice 6.0.5, Punto 2).

Enforces strict anti-leakage invariant:
Solution chunks (identified by content_registry.solution_chunk_ids) must NEVER be
presented to a student during search, context assembly, chat streaming, or statement display.

Acts as:
1. Universal layer applied inside ContentRegistryRepository chunk accessors.
2. Second defensive layer inside chat.py context and evidence assembly.
"""

from __future__ import annotations

import logging
from typing import Any, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


def _extract_chunk_id(chunk: Any) -> str:
    """Extract string identifier from a Chunk, SearchResult, ChunkWithProvenance, or dict."""
    if isinstance(chunk, str):
        return chunk
    if isinstance(chunk, dict):
        return str(chunk.get("id") or chunk.get("chunk_id") or "")
    return str(getattr(chunk, "chunk_id", None) or getattr(chunk, "id", None) or "")


def filter_presentation(
    chunks: List[Any],
    registry_or_solution_ids: Union[Any, Set[str]],
) -> Tuple[List[Any], bool]:
    """Filters out any chunk tagged as a solution chunk.

    Args:
        chunks: List of chunk instances (Chunk, SearchResult, ChunkWithProvenance, etc.).
        registry_or_solution_ids: ContentRegistryRepository instance or Set[str] of solution chunk IDs.

    Returns:
        Tuple[List[Any], bool]:
            - Cleaned list of non-solution chunks.
            - Boolean flag indicating whether one or more solution chunks were intercepted and removed.
    """
    if not chunks:
        return [], False

    if isinstance(registry_or_solution_ids, set):
        solution_ids = registry_or_solution_ids
    elif hasattr(registry_or_solution_ids, "get_solution_chunk_ids"):
        solution_ids = registry_or_solution_ids.get_solution_chunk_ids()
    else:
        solution_ids = set()

    if not solution_ids:
        return list(chunks), False

    clean_chunks: List[Any] = []
    removed_any = False

    for c in chunks:
        cid = _extract_chunk_id(c)
        if cid and cid in solution_ids:
            logger.info("[ANTI-LEAKAGE] Intercepted solution chunk %s from presentation context", cid)
            removed_any = True
        else:
            clean_chunks.append(c)

    return clean_chunks, removed_any


def filter_chunk_ids(
    chunk_ids: List[str],
    registry_or_solution_ids: Union[Any, Set[str]],
) -> Tuple[List[str], bool]:
    """Filters a list of chunk ID strings directly."""
    return filter_presentation(chunk_ids, registry_or_solution_ids)
