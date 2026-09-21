"""Dedicated chunk embedding indexing service for S3.4."""

from typing import List
from study_engine.contracts.catalog import NotebookNotFoundError
from study_engine.contracts.chunk import Chunk

from study_engine.retrieval.embedding import (
    EmbeddingDimensionMismatchError,
    EmbeddingProvider,
)
from study_engine.retrieval.vector_store import (
    SQLiteVectorStore,
    VectorRecord,
)
from study_engine.storage.knowledge_store import KnowledgeStore


def index_notebook_chunks(
    store: KnowledgeStore,
    vector_store: SQLiteVectorStore,
    embedding_provider: EmbeddingProvider,
    notebook_id: str,
) -> int:
    """Extract, embed, and persist all chunks for a notebook."""
    if not store.contains_notebook(notebook_id):
        raise NotebookNotFoundError(notebook_id)

    # 1. Gather all chunks linked to this notebook
    sources = store.list_notebook_sources(notebook_id)
    chunks_to_index: List[Chunk] = []

    for src in sources:
        docs = store.list_documents(source_id=src.source_id)
        for doc in docs:
            doc_chunks = store.list_chunks_by_document(doc.id)
            chunks_to_index.extend(doc_chunks)

    if not chunks_to_index:
        return 0

    # 2. Generate embeddings in passage mode
    texts = [c.content for c in chunks_to_index]
    vectors = embedding_provider.embed_passages(texts)

    if len(vectors) != len(chunks_to_index):
        raise ValueError(
            f"Provider returned {len(vectors)} vectors for "
            f"{len(chunks_to_index)} chunks."
        )

    # 3. Build VectorRecords with full model identity
    records: List[VectorRecord] = []
    dim = embedding_provider.dimensions
    prov_id = embedding_provider.provider_id
    mod_id = embedding_provider.model_id

    for chunk, vec in zip(chunks_to_index, vectors):
        if len(vec) != dim:
            raise EmbeddingDimensionMismatchError(
                f"Expected {dim} dimensions, got {len(vec)}."
            )
        records.append(
            VectorRecord(
                chunk_id=chunk.id,
                notebook_id=notebook_id,
                source_id=chunk.source_id,
                provider_id=prov_id,
                model_id=mod_id,
                dimensions=dim,
                vector=vec,
            )
        )

    # 4. Save to vector store
    return vector_store.save_records(records)
