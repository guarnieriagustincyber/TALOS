"""Two-Stage Rerankers: Jina API Client with Transparent Local Fallback (Fase 7 / F2, F3).

Architecture:
- BaseReranker: Standard protocol for ranking candidates.
- DeterministicLocalReranker (F2): Exact coverage (40%), bigrams (30%), position (30%).
- JinaReranker (F3): Jina API client with strict 2.0s timeout, max 1 retry, and fail-safe local fallback.
"""

import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Protocol, Set, Tuple, Union
import httpx

from study_engine.contracts.retrieval import ScoredCandidate

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercase alphanumeric words."""
    if not text:
        return []
    return re.findall(r"\w+", text.lower())


def _word_bigrams(words: List[str]) -> List[str]:
    """Extract word-level bigrams."""
    if len(words) < 2:
        return []
    return [f"{words[i]}_{words[i+1]}" for i in range(len(words) - 1)]


def _calculate_position_score(query_terms: Set[str], text: str) -> float:
    """Calculate position score: terms appearing earlier in text yield higher scores."""
    if not query_terms or not text:
        return 0.0
    text_lower = text.lower()
    text_len = max(len(text_lower), 1)
    scores: List[float] = []

    for term in query_terms:
        idx = text_lower.find(term)
        if idx != -1:
            # Linear decay from 1.0 at pos 0 down to 0.1 at end of text
            pos_score = max(0.1, 1.0 - (idx / text_len))
            scores.append(pos_score)
        else:
            scores.append(0.0)

    return sum(scores) / len(query_terms)


def calculate_local_rerank_score(candidate: ScoredCandidate, query: str) -> float:
    """Deterministic local reranking scoring formula (F2).

    Weights:
    - Term coverage: 40%
    - Bigram density: 30%
    - Position score: 30%

    Returns score in [0.0, 1.0] rounded to 4 decimals.
    """
    query_words = _tokenize(query)
    chunk_words = _tokenize(candidate.content)

    query_terms = set(query_words)
    chunk_terms = set(chunk_words)

    if not query_terms:
        return 0.0

    # 1. Cobertura de términos (40% peso)
    coverage = len(query_terms & chunk_terms) / len(query_terms)

    # 2. Densidad de bigramas (30% peso)
    query_bigrams = set(_word_bigrams(query_words))
    chunk_bigrams = set(_word_bigrams(chunk_words))
    if query_bigrams:
        bigram_overlap = len(query_bigrams & chunk_bigrams) / len(query_bigrams)
    else:
        # Si la query no tiene bigramas (1 palabra), usar coverage
        bigram_overlap = coverage

    # 3. Posición (30% peso) - términos al inicio valen más
    position_score = _calculate_position_score(query_terms, candidate.content)

    final_score = (0.4 * coverage) + (0.3 * bigram_overlap) + (0.3 * position_score)
    return round(min(1.0, max(0.0, final_score)), 4)


class BaseReranker(Protocol):
    """Protocol for candidate rerankers."""

    def rerank(
        self,
        query: str,
        candidates: List[ScoredCandidate],
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Rerank candidates based on semantic relevance to query."""
        ...


class DeterministicLocalReranker:
    """Pure, deterministic local reranker using token overlap, bigrams, and position (F2)."""

    def rerank(
        self,
        query: str,
        candidates: List[ScoredCandidate],
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Rerank candidates using exact local scoring formula without network calls."""
        if not candidates:
            return []

        scored_cands: List[Tuple[float, int, ScoredCandidate]] = []
        for orig_idx, cand in enumerate(candidates):
            score = calculate_local_rerank_score(cand, query)
            new_meta = dict(cand.metadata)
            new_meta["reranker"] = "local_fallback"
            new_meta["local_rerank_score"] = score
            updated = cand.model_copy(
                update={
                    "score": score,
                    "metadata": new_meta,
                }
            )
            # Tuple: (-score, orig_idx, candidate) for stable sort
            scored_cands.append((-score, orig_idx, updated))

        scored_cands.sort(key=lambda t: (t[0], t[1]))

        result: List[ScoredCandidate] = []
        for new_rank, (_, _, cand) in enumerate(scored_cands[:top_k], start=1):
            result.append(cand.model_copy(update={"rank": new_rank}))

        return result


class JinaReranker:
    """Neural Reranker via Jina API with strict timeout, retries, and local fallback (F3)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "jina-reranker-v2-base-multilingual",
        timeout: float = 2.0,
        max_retries: int = 1,
        endpoint: str = "https://api.jina.ai/v1/rerank",
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.endpoint = endpoint
        self.fallback = DeterministicLocalReranker()

    def rerank(
        self,
        query: str,
        candidates: List[ScoredCandidate],
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Rerank candidates using Jina API if key is available, else fallback cleanly."""
        if not candidates:
            return []

        if not self.api_key:
            logger.debug("JINA_API_KEY no configurada; aplicando DeterministicLocalReranker fallback.")
            return self.fallback.rerank(query, candidates, top_k=top_k)

        # F3: Intento con timeout estricto de 2.0s y max_retries=1
        for attempt in range(self.max_retries + 1):
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                payload = {
                    "model": self.model,
                    "query": query,
                    "documents": [c.content for c in candidates],
                    "top_n": min(top_k, len(candidates)),
                }

                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(self.endpoint, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()

                results = data.get("results", [])
                if not results:
                    logger.warning("Jina rerank returned empty results; falling back.")
                    return self.fallback.rerank(query, candidates, top_k=top_k)

                reranked_items: List[ScoredCandidate] = []
                for new_rank, item in enumerate(results, start=1):
                    doc_idx = item["index"]
                    rel_score = float(item["relevance_score"])
                    orig_cand = candidates[doc_idx]

                    new_meta = dict(orig_cand.metadata)
                    new_meta["reranker"] = "jina"
                    new_meta["reranker_score"] = rel_score

                    updated = orig_cand.model_copy(
                        update={
                            "rank": new_rank,
                            "score": round(rel_score, 4),
                            "metadata": new_meta,
                        }
                    )
                    reranked_items.append(updated)

                return reranked_items[:top_k]

            except (httpx.TimeoutException, httpx.RequestError, httpx.HTTPStatusError, Exception) as e:
                logger.warning(
                    "Jina reranker failed (attempt %d/%d, error=%s: %s); falling back to local.",
                    attempt + 1,
                    self.max_retries + 1,
                    type(e).__name__,
                    e,
                )
                if attempt == self.max_retries:
                    break

        return self.fallback.rerank(query, candidates, top_k=top_k)


class LocalONNXReranker:
    """Local Neural Cross-Encoder Reranker using ONNX Runtime (CPU) with fail-safe fallback.

    Scores (query, passage) pairs with full cross-attention. Outputs calibrated
    relevance probabilities in [0.0, 1.0] using sigmoid activation over logits.
    """

    def __init__(
        self,
        model_path: Union[str, Path] = "models/reranker/model.onnx",
        tokenizer_path: Union[str, Path] = "models/reranker/tokenizer.json",
        max_length: int = 512,
        num_threads: int = 4,
        fallback: Optional[BaseReranker] = None,
    ) -> None:
        self.model_path = Path(model_path)
        self.tokenizer_path = Path(tokenizer_path)
        self.max_length = max_length
        self.num_threads = num_threads
        self.fallback = fallback or DeterministicLocalReranker()
        self._session: Any = None
        self._tokenizer: Any = None
        self._initialized = False

    def _initialize(self) -> bool:
        if self._initialized:
            return self._session is not None
        self._initialized = True

        if not self.model_path.exists() or not self.tokenizer_path.exists():
            logger.info(
                "Local ONNX reranker model/tokenizer not found at %s. Falling back to DeterministicLocalReranker.",
                self.model_path,
            )
            return False

        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer

            self._np = np
            self._tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
            self._tokenizer.enable_truncation(max_length=self.max_length)
            self._tokenizer.enable_padding(pad_id=0, pad_token="[PAD]", length=None)

            opts = ort.SessionOptions()
            opts.intra_op_num_threads = self.num_threads
            opts.inter_op_num_threads = 1
            opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
            self._session = ort.InferenceSession(
                str(self.model_path),
                sess_options=opts,
                providers=["CPUExecutionProvider"],
            )
            logger.info("LocalONNXReranker initialized successfully from %s", self.model_path)
            return True
        except Exception as e:
            logger.warning("Failed to initialize LocalONNXReranker session: %s. Using fallback.", e)
            return False

    def rerank(
        self,
        query: str,
        candidates: List[ScoredCandidate],
        top_k: int = 5,
    ) -> List[ScoredCandidate]:
        """Rerank candidates using local neural cross-encoder with ONNX Runtime."""
        if not candidates:
            return []

        if not self._initialize():
            return self.fallback.rerank(query, candidates, top_k=top_k)

        try:
            np = self._np
            pairs = [(query, c.content) for c in candidates]
            encodings = self._tokenizer.encode_batch(pairs)

            input_ids = np.array([e.ids for e in encodings], dtype=np.int64)
            attention_mask = np.array([e.attention_mask for e in encodings], dtype=np.int64)

            inputs = {
                "input_ids": input_ids,
                "attention_mask": attention_mask,
            }

            model_input_names = [inp.name for inp in self._session.get_inputs()]
            if "token_type_ids" in model_input_names:
                token_type_ids = np.array([e.type_ids for e in encodings], dtype=np.int64)
                inputs["token_type_ids"] = token_type_ids

            outputs = self._session.run(None, inputs)
            logits = outputs[0]

            if hasattr(logits, "ndim") and logits.ndim > 1:
                logits = logits.squeeze(-1)

            scores = 1.0 / (1.0 + np.exp(-logits.astype(np.float64)))
            if not hasattr(scores, "__iter__") or (hasattr(scores, "ndim") and scores.ndim == 0):
                scores = [float(scores)]

            scored_cands: List[Tuple[float, int, ScoredCandidate]] = []
            for orig_idx, (cand, score) in enumerate(zip(candidates, scores)):
                sc = round(float(score), 4)
                new_meta = dict(cand.metadata)
                new_meta["reranker"] = "local_onnx"
                new_meta["reranker_score"] = sc
                updated = cand.model_copy(
                    update={
                        "score": sc,
                        "metadata": new_meta,
                    }
                )
                scored_cands.append((-sc, orig_idx, updated))

            scored_cands.sort(key=lambda t: (t[0], t[1]))

            result: List[ScoredCandidate] = []
            for new_rank, (_, _, cand) in enumerate(scored_cands[:top_k], start=1):
                result.append(cand.model_copy(update={"rank": new_rank}))

            return result

        except Exception as e:
            logger.warning("LocalONNXReranker inference error: %s. Using fallback.", e)
            return self.fallback.rerank(query, candidates, top_k=top_k)

