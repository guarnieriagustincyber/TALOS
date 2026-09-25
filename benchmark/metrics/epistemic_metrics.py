"""Métricas Epistémicas y de Aislamiento para Fase 4-eval.

Implementa:
- Verificación Fail-Closed (100% abstención ante OOD)
- Verificación de Aislamiento de Cuaderno (Notebook Scoping & Anti-Leakage)
- Precisión de Citas Canónicas
"""

from typing import Sequence, Set


def verify_fail_closed_abstention(is_ood: bool, abstained: bool, emitted_citations: Sequence[str]) -> bool:
    """Valida la política ADR-008: si una consulta es OOD, DEBE abstenerse y NO emitir citas."""
    if is_ood:
        # Falla si emitió citas o si no se abstuvo formalmente
        if len(emitted_citations) > 0:
            return False
        return abstained
    return True


def verify_notebook_scoping(
    retrieved_sources: Sequence[str],
    authorized_sources: Set[str],
) -> bool:
    """Verifica que ningún chunk recuperado pertenezca a fuentes no autorizadas para el cuaderno."""
    if not retrieved_sources:
        return True
    for src in retrieved_sources:
        if src not in authorized_sources:
            return False
    return True


def compute_evidence_precision(
    emitted_citations: Sequence[str],
    authorized_chunks: Set[str],
) -> float:
    """Calcula la fracción de citas emitidas que existen en el context pack autorizado."""
    if not emitted_citations:
        return 1.0
    valid_citations = sum(1 for c in emitted_citations if c in authorized_chunks)
    return valid_citations / len(emitted_citations)
