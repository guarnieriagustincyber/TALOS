"""Métricas de Recuperación para la Fase 4-eval de TALOS v1.1.

Implementa:
- MRR@k (Mean Reciprocal Rank)
- nDCG@k graduado con descuento logarítmico (Normalized Discounted Cumulative Gain)
- Recall@k
- Precision@k
"""

import math
from typing import Dict, Sequence


def compute_mrr(retrieved_ids: Sequence[str], qrels: Dict[str, int], k: int = 5) -> float:
    """Calcula el Reciprocal Rank del primer chunk relevante en el top-k.
    
    Criterio: relevancia >= 1.
    """
    if not retrieved_ids or not qrels:
        return 0.0

    for rank, chunk_id in enumerate(retrieved_ids[:k], start=1):
        if qrels.get(chunk_id, 0) >= 1:
            return 1.0 / rank
    return 0.0


def compute_ndcg(retrieved_ids: Sequence[str], qrels: Dict[str, int], k: int = 5) -> float:
    """Calcula el nDCG@k con relevancia graduada (0 a 3).
    
    DCG = sum((2^rel - 1) / log2(rank + 1))
    """
    if not qrels:
        return 0.0

    # DCG observado
    dcg = 0.0
    for rank, chunk_id in enumerate(retrieved_ids[:k], start=1):
        rel = qrels.get(chunk_id, 0)
        if rel > 0:
            dcg += (math.pow(2, rel) - 1.0) / math.log2(rank + 1)

    # Ideal DCG (ordenando todos los qrels disponibles de mayor a menor)
    ideal_rels = sorted(qrels.values(), reverse=True)[:k]
    idcg = 0.0
    for rank, rel in enumerate(ideal_rels, start=1):
        if rel > 0:
            idcg += (math.pow(2, rel) - 1.0) / math.log2(rank + 1)

    if idcg == 0.0:
        return 0.0

    return min(1.0, dcg / idcg)


def compute_recall(retrieved_ids: Sequence[str], qrels: Dict[str, int], k: int = 5) -> float:
    """Calcula la fracción de chunks relevantes recuperados en top-k sobre el total relevante."""
    if not qrels:
        return 0.0

    relevant_in_qrels = [cid for cid, rel in qrels.items() if rel >= 1]
    if not relevant_in_qrels:
        return 0.0

    retrieved_top_k = set(retrieved_ids[:k])
    hits = sum(1 for cid in relevant_in_qrels if cid in retrieved_top_k)
    return hits / min(len(relevant_in_qrels), k)


def compute_precision(retrieved_ids: Sequence[str], qrels: Dict[str, int], k: int = 5) -> float:
    """Calcula la fracción de chunks en top-k que son relevantes."""
    if k <= 0:
        return 0.0
    actual_k = min(len(retrieved_ids), k)
    if actual_k == 0:
        return 0.0

    hits = sum(1 for cid in retrieved_ids[:actual_k] if qrels.get(cid, 0) >= 1)
    return hits / actual_k
