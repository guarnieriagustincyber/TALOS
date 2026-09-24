"""Embedding provider protocol and implementations for S3.4 Dense Retrieval."""

import hashlib
import math
from pathlib import Path
from typing import Any, List, Optional, Protocol, Union, runtime_checkable


class EmbeddingDimensionMismatchError(ValueError):
    """Raised when vector dimensions do not match provider configuration."""
    pass


class QwenPrefixFormatter:
    """Formatter adhering to Qwen3-Embedding instruction schema.

    Unlike E5, Qwen3 does not require rigid asymmetric 'query: ' or 'passage: ' prefixes.
    Queries and passages are stripped cleanly.
    """

    @staticmethod
    def format_query(text: str) -> str:
        """Clean user query for Qwen3 retrieval."""
        return text.strip()

    @staticmethod
    def format_passage(text: str) -> str:
        """Clean passage text for Qwen3 embedding."""
        return text.strip()


class E5PrefixFormatter:
    """Formatter adhering to the multilingual-e5 instruction schema."""

    @staticmethod
    def format_query(text: str) -> str:
        """Prefix user query with 'query: ' as required by E5."""
        clean = text.strip()
        return f"query: {clean}"

    @staticmethod
    def format_passage(text: str) -> str:
        """Prefix corpus chunk with 'passage: ' as required by E5."""
        clean = text.strip()
        return f"passage: {clean}"


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol defining the embedding generation contract."""

    @property
    def provider_id(self) -> str:
        """Unique identifier of the embedding provider."""
        ...

    @property
    def model_id(self) -> str:
        """Specific model name and version."""
        ...

    @property
    def dimensions(self) -> int:
        """Vector dimensionality."""
        ...

    @property
    def is_test_mock(self) -> bool:
        """True if this provider is for tests and not a real semantic model."""
        ...

    def embed_query(self, query: str) -> List[float]:
        """Embed a search query, applying appropriate query formatting."""
        ...

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        """Embed corpus passages, applying appropriate document formatting."""
        ...


class MockEmbeddingProvider:
    """Deterministic hash-based embedding provider strictly for tests."""

    def __init__(
        self,
        dimensions: int = 2560,
        provider_id: str = "mock",
        model_id: str = "mock-sha256-v1",
        use_e5_prefix: bool = False,
    ) -> None:
        if dimensions <= 0:
            raise ValueError("Dimensions must be positive.")
        self._dimensions = dimensions
        self._provider_id = provider_id
        self._model_id = model_id
        self._use_e5_prefix = use_e5_prefix

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def is_test_mock(self) -> bool:
        return True

    def _hash_to_vector(self, text: str) -> List[float]:
        """Generate a deterministic unit vector from text using SHA-256."""
        vec: List[float] = []
        seed = text.encode("utf-8")
        step = 0
        while len(vec) < self._dimensions:
            h = hashlib.sha256(seed + step.to_bytes(4, "big")).digest()
            for b in h:
                if len(vec) >= self._dimensions:
                    break
                # Center around 0.0: [-1.0, 1.0]
                vec.append((b - 128.0) / 128.0)
            step += 1

        # L2-normalize
        norm = math.sqrt(sum(x * x for x in vec))
        return [x / norm for x in vec]

    def embed_query(self, query: str) -> List[float]:
        if self._use_e5_prefix:
            formatted = E5PrefixFormatter.format_query(query)
        else:
            formatted = QwenPrefixFormatter.format_query(query)
        return self._hash_to_vector(formatted)

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        results: List[List[float]] = []
        for text in texts:
            if self._use_e5_prefix:
                formatted = E5PrefixFormatter.format_passage(text)
            else:
                formatted = QwenPrefixFormatter.format_passage(text)
            results.append(self._hash_to_vector(formatted))
        return results


class DeterministicHashEmbedder(MockEmbeddingProvider):
    """Deterministic hash-based embedding provider with fixed dimensions (default 128) using SHA-256."""

    def __init__(
        self,
        dimensions: int = 128,
        provider_id: str = "deterministic_hash",
        model_id: str = "sha256-128d-v1",
    ) -> None:
        super().__init__(
            dimensions=dimensions,
            provider_id=provider_id,
            model_id=model_id,
        )


class SentenceTransformerEmbeddingProvider:
    """Embedding provider executing sentence-transformers (e.g. Qwen/Qwen3-Embedding-8B) with normalize_embeddings=True."""

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-Embedding-4B",
        dimensions: int = 2560,
        device: Union[str, None] = None,
        batch_size: int = 128,
        provider_id: str = "sentence_transformers",
    ) -> None:
        self._model_name = model_name_or_path
        self._dimensions = dimensions
        self._device = device
        self._batch_size = batch_size
        self._provider_id = provider_id
        self._model: Any = None

    def _ensure_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "SentenceTransformerEmbeddingProvider requires 'sentence_transformers'. "
                    "Install via pip: pip install sentence-transformers"
                ) from e
            self._model = SentenceTransformer(
                self._model_name,
                device=self._device,
                trust_remote_code=True,
            )
        return self._model

    @property
    def provider_id(self) -> str:
        return self._provider_id

    @property
    def model_id(self) -> str:
        return self._model_name

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def is_test_mock(self) -> bool:
        return False

    def embed_query(self, query: str) -> List[float]:
        model = self._ensure_model()
        cleaned = QwenPrefixFormatter.format_query(query)
        embedding = model.encode(
            cleaned,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        vec = embedding.tolist() if hasattr(embedding, "tolist") else list(embedding)
        return vec  # type: ignore[no-any-return]

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        model = self._ensure_model()
        cleaned = [QwenPrefixFormatter.format_passage(t) for t in texts]
        embeddings = model.encode(
            cleaned,
            batch_size=self._batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist() if hasattr(embeddings, "tolist") else [list(e) for e in embeddings]  # type: ignore[no-any-return]


class LocalONNXEmbeddingProvider:
    """Local ONNX embedding provider executing multilingual-e5-small on CPU."""

    def __init__(
        self,
        model_path: Union[
            str, Path
        ] = "models/multilingual-e5-small/onnx/model.onnx",
        tokenizer_path: Union[
            str, Path
        ] = "models/multilingual-e5-small/onnx/tokenizer.json",
        dimensions: int = 384,
        max_length: int = 512,
        num_threads: int = 4,
    ) -> None:
        self._model_path = Path(model_path)
        self._tokenizer_path = Path(tokenizer_path)
        self._dimensions = dimensions
        self._max_length = max_length
        self._num_threads = num_threads

        if not self._model_path.exists():
            raise FileNotFoundError(
                f"ONNX model file not found: {self._model_path}"
            )
        if not self._tokenizer_path.exists():
            raise FileNotFoundError(
                f"Tokenizer file not found: {self._tokenizer_path}"
            )

        try:
            import numpy as np
            import onnxruntime as ort  # type: ignore[import-untyped]
            from tokenizers import Tokenizer
        except ImportError as e:
            raise ImportError(

                "LocalONNXEmbeddingProvider requires 'numpy', "
                "'onnxruntime', and 'tokenizers'. Install them via pip."
            ) from e

        self._np = np
        self._tokenizer = Tokenizer.from_file(str(self._tokenizer_path))
        self._tokenizer.enable_truncation(max_length=self._max_length)
        self._tokenizer.enable_padding(
            pad_id=0, pad_token="<pad>", length=None
        )

        opts = ort.SessionOptions()
        opts.intra_op_num_threads = self._num_threads
        opts.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(self._model_path),
            sess_options=opts,
            providers=["CPUExecutionProvider"],
        )

    @property
    def provider_id(self) -> str:
        return "local_onnx"

    @property
    def model_id(self) -> str:
        return "multilingual-e5-small"

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def is_test_mock(self) -> bool:
        return False

    def _infer(self, formatted_texts: List[str]) -> List[List[float]]:
        if not formatted_texts:
            return []

        encodings = self._tokenizer.encode_batch(formatted_texts)
        input_ids = self._np.array(
            [e.ids for e in encodings], dtype=self._np.int64
        )
        attention_mask = self._np.array(
            [e.attention_mask for e in encodings], dtype=self._np.int64
        )
        token_type_ids = self._np.array(
            [e.type_ids for e in encodings], dtype=self._np.int64
        )

        outputs = self._session.run(
            None,
            {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
                "token_type_ids": token_type_ids,
            },
        )
        last_hidden_state = outputs[0]  # (batch, seq_len, 384)

        # Average pooling with attention mask
        mask_expanded = self._np.expand_dims(
            attention_mask, -1
        ).astype(self._np.float32)
        sum_embeddings = self._np.sum(
            last_hidden_state * mask_expanded, axis=1
        )
        sum_mask = self._np.clip(
            mask_expanded.sum(axis=1), a_min=1e-9, a_max=None
        )
        embeddings = sum_embeddings / sum_mask

        # L2-normalize
        norms = self._np.linalg.norm(embeddings, axis=1, keepdims=True)
        normalized = embeddings / self._np.clip(norms, a_min=1e-9, a_max=None)
        return normalized.tolist()  # type: ignore[no-any-return]

    def embed_query(self, query: str) -> List[float]:
        formatted = E5PrefixFormatter.format_query(query)
        res = self._infer([formatted])
        return res[0]

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        formatted = [E5PrefixFormatter.format_passage(t) for t in texts]
        return self._infer(formatted)
