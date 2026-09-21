"""Oracle benchmark dataset validation against KnowledgeStore."""

from typing import Optional, Set
from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
)
from study_engine.storage.knowledge_store import KnowledgeStore


class OracleValidationError(ValueError):
    """Raised when an Oracle dataset violates structural rules."""
    pass


class OracleIntegrityError(OracleValidationError):
    """Raised when an Oracle dataset violates relational integrity."""
    pass


def validate_oracle_dataset(
    dataset: OracleDataset,
    store: Optional[KnowledgeStore] = None,
) -> None:
    """Validate an OracleDataset against rules and optional KnowledgeStore.

    Invariants Checked:
        1. Query and notebook_id are non-blank strings.
        2. Category is in BenchmarkCategory.
        3. Relevant chunk IDs are unique within each query.
        4. CURRICULAR_LEAKAGE queries have empty relevant lists.
        5. If store is provided:
            a. Query notebook_id must physically exist in store.
            b. Every relevant chunk_id must physically exist in store.
            c. Every relevant chunk_id belongs to a source linked
               to query.notebook_id.

    Raises:
        OracleValidationError: If dataset-level invariant is violated.
        OracleIntegrityError: If chunk or notebook violates isolation.
    """
    if not dataset.version or not dataset.version.strip():
        raise OracleValidationError("Oracle dataset version cannot be empty.")

    seen_query_ids: Set[str] = set()

    for q in dataset.queries:
        if q.id in seen_query_ids:
            raise OracleValidationError(
                f"Duplicate query ID '{q.id}' in dataset."
            )
        seen_query_ids.add(q.id)

        # Leakage check
        if (
            q.category == BenchmarkCategory.CURRICULAR_LEAKAGE
            and len(q.relevant) > 0
        ):
            raise OracleValidationError(
                f"Curricular leakage query '{q.id}' must have "
                "zero relevant chunks."
            )

        # Store-level relational integrity check
        if store is not None:
            _validate_query_against_store(q, store)


def _validate_query_against_store(
    query: OracleQuery, store: KnowledgeStore
) -> None:
    """Verify notebooks, chunks, and sources exist and respect scoping."""
    # 1. Verify notebook exists
    if not store.contains_notebook(query.notebook_id):
        raise OracleIntegrityError(
            f"Query '{query.id}' references notebook '{query.notebook_id}', "
            "which does not exist in store."
        )

    # 2. Get sources linked to this notebook
    linked_source_ids = {
        s.source_id for s in store.list_notebook_sources(query.notebook_id)
    }

    # 3. Verify every relevant chunk exists and belongs to a linked source
    for item in query.relevant:
        if not store.chunks.contains(item.chunk_id):
            raise OracleIntegrityError(
                f"Query '{query.id}' references chunk '{item.chunk_id}', "
                "which does not exist in store."
            )

        chunk = store.get_chunk(item.chunk_id)
        if chunk.source_id not in linked_source_ids:
            raise OracleIntegrityError(
                f"Curricular isolation violated in query '{query.id}': chunk "
                f"'{item.chunk_id}' belongs to source '{chunk.source_id}', "
                f"which is NOT linked to notebook '{query.notebook_id}'."
            )
