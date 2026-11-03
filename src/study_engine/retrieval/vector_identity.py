"""Exact, versioned identity for embeddings used in vector comparisons."""

import json
from typing import Any, Optional

from study_engine.retrieval.embedding import (
    DeterministicHashEmbedder,
    LocalONNXEmbeddingProvider,
    MockEmbeddingProvider,
    QWEN_EMBEDDING_MODEL,
    SentenceTransformerEmbeddingProvider,
)


def vector_space_id(provider: Any) -> Optional[str]:
    """Return a canonical identity only when all space-defining inputs are known.

    Device, batch size and thread count do not define the embedding space.
    An arbitrary provider cannot be identified from its name and dimensions.
    """
    try:
        base = {
            "schema": 1,
            "provider": provider.provider_id,
            "model": provider.model_id,
            "dimensions": provider.dimensions,
        }
        if not base["provider"] or not base["model"] or base["dimensions"] <= 0:
            return None
        if type(provider) in (MockEmbeddingProvider, DeterministicHashEmbedder):
            base.update(
                implementation="sha256-v1",
                prefix="e5-v1" if provider._use_e5_prefix else "qwen-strip-v1",
                normalization="l2",
            )
        elif isinstance(provider, SentenceTransformerEmbeddingProvider):
            if provider._model_name != QWEN_EMBEDDING_MODEL or not provider._revision:
                return None
            base.update(
                revision=provider._revision,
                prefix="qwen-strip-v1",
                normalization="l2",
            )
        elif isinstance(provider, LocalONNXEmbeddingProvider):
            base.update(
                model_sha256=provider._asset_digests[0],
                tokenizer_sha256=provider._asset_digests[1],
                max_length=provider._max_length,
                prefix="e5-v1",
                pooling="attention-mask-mean-v1",
                normalization="l2",
            )
        else:
            return None
        return json.dumps(base, sort_keys=True, separators=(",", ":"))
    except (AttributeError, OSError, TypeError, ValueError):
        return None
