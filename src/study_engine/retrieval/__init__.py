"""Retrieval subsystem for Study Engine."""

from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.benchmark_builder import build_benchmark_corpus
from study_engine.retrieval.dense import (

    DenseRetrievalError,
    DenseRetriever,
)
from study_engine.retrieval.embedding import (
    DeterministicHashEmbedder,
    E5PrefixFormatter,
    EmbeddingDimensionMismatchError,
    EmbeddingProvider,
    LocalONNXEmbeddingProvider,
    MockEmbeddingProvider,
    QwenPrefixFormatter,
    SentenceTransformerEmbeddingProvider,
)
from study_engine.retrieval.evaluator import (
    CategoryMetrics,
    EvaluationReport,
    OracleEvaluator,
    QueryEvaluationResult,
)
from study_engine.retrieval.fusion import (
    FusedCandidate,
    FusionStrategy,
    ReciprocalRankFusion,
)
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.oracle import (
    OracleIntegrityError,
    OracleValidationError,
    validate_oracle_dataset,
)
from study_engine.retrieval.query_rewriter import QueryRewriter
from study_engine.retrieval.service import RetrievalService
from study_engine.retrieval.vector_store import (
    SQLiteVectorStore,
    VectorRecord,
    VectorStore,
)

__all__ = [
    "BaseRetriever",
    "QueryRewriter",

    "CategoryMetrics",
    "DenseRetrievalError",
    "DenseRetriever",
    "DeterministicHashEmbedder",
    "E5PrefixFormatter",
    "EmbeddingDimensionMismatchError",
    "EmbeddingProvider",
    "EvaluationReport",
    "FusedCandidate",
    "FusionStrategy",
    "HybridRetriever",
    "LexicalRetriever",
    "LocalONNXEmbeddingProvider",
    "MockEmbeddingProvider",
    "OracleEvaluator",
    "OracleIntegrityError",
    "OracleValidationError",
    "QueryEvaluationResult",
    "QwenPrefixFormatter",
    "ReciprocalRankFusion",
    "RetrievalService",
    "SentenceTransformerEmbeddingProvider",
    "SQLiteVectorStore",

    "VectorRecord",
    "VectorStore",
    "build_benchmark_corpus",
    "index_notebook_chunks",
    "validate_oracle_dataset",
]
