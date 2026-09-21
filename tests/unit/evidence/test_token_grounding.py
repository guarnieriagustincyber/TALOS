"""Unit tests for TokenGroundingEngine (Phase E2.4)."""

from pathlib import Path
import pytest

from study_engine.evidence.claim_extractor import ClaimCriticality, ClaimType, ExtractedClaim
from study_engine.evidence.token_grounding import (
    ClaimGroundingResult,
    GroundingStatus,
    TokenGroundingEngine,
)

DICT_PATH = Path("data/benchmark/bilingual_dict_v1.json")


def test_grounding_factual_supported_same_language():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    claim = ExtractedClaim(
        claim_id="CLM-001",
        text="El bloque de control de proceso almacena los registros y el contador de programa.",
        claim_type=ClaimType.FACTUAL_TEXTUAL,
        criticality=ClaimCriticality.CRITICAL,
    )
    evidence = [
        {"id": "chunk-1", "content": "El bloque de control de proceso (PCB) almacena el estado de CPU, registros y contador de programa."}
    ]
    res = engine.ground_claim(claim, evidence)
    assert res.status == GroundingStatus.SUPPORTED
    assert res.grounding_score >= 0.55
    assert "chunk-1" in res.matched_chunk_ids


def test_grounding_cross_lingual_es_to_en():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    # Spanish claim mentioning "hilo" and "sección crítica"
    claim = ExtractedClaim(
        claim_id="CLM-002",
        text="Un semáforo binario restringe el acceso de un hilo a la sección crítica.",
        claim_type=ClaimType.FACTUAL_TEXTUAL,
        criticality=ClaimCriticality.CRITICAL,
    )
    # English textbook excerpt
    evidence = [
        {"id": "chunk-stallings", "content": "A binary semaphore allows only one thread to execute in its critical section at a time."}
    ]
    res = engine.ground_claim(claim, evidence)
    assert res.status == GroundingStatus.SUPPORTED
    assert res.grounding_score >= 0.50
    # Should have matched cross-lingual terms
    matched_claim_terms = [m[0] for m in res.matched_terms]
    assert any("semáforo" in t or "semaforo" in t or "sección" in t or "hilo" in t for t in matched_claim_terms)


def test_grounding_contradiction():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    claim = ExtractedClaim(
        claim_id="CLM-003",
        text="En la paginación tradicional los marcos tienen tamaños dinámicos y variables según el proceso.",
        claim_type=ClaimType.FACTUAL_TEXTUAL,
        criticality=ClaimCriticality.CRITICAL,
    )
    evidence = [
        {"id": "chunk-mem", "content": "La memoria física se divide en marcos de tamaño fijo llamados page frames."}
    ]
    res = engine.ground_claim(claim, evidence)
    assert res.status == GroundingStatus.CONTRADICTION
    assert res.grounding_score == 0.0


def test_grounding_pedagogical_analogy_h1():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    # Pedagogical analogy has NO literal tokens in technical evidence
    claim = ExtractedClaim(
        claim_id="CLM-004",
        text="Podemos imaginar la memoria RAM como una hilera de casilleros postales numerados.",
        claim_type=ClaimType.PEDAGOGICAL,
        criticality=ClaimCriticality.NON_CRITICAL,
        is_pedagogical_analogy=True,
    )
    evidence = [
        {"id": "chunk-joyanes", "content": "La memoria principal RAM almacena bytes direccionables mediante celdas con dirección numérica."}
    ]
    res = engine.ground_claim(claim, evidence)
    # Under H1, should NOT fail token grounding; evaluated only for non-contradiction
    assert res.status == GroundingStatus.SUPPORTED
    assert res.is_pedagogical_analogy is True


def test_grounding_conversational_h1():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    claim = ExtractedClaim(
        claim_id="CLM-005",
        text="¡Hola! Espero que tengas un gran día.",
        claim_type=ClaimType.CONVERSATIONAL,
        criticality=ClaimCriticality.NON_CRITICAL,
    )
    evidence = []
    res = engine.ground_claim(claim, evidence)
    assert res.status == GroundingStatus.EXEMPT


def test_grounding_formal_complexity_h1():
    engine = TokenGroundingEngine(bilingual_dict_path=DICT_PATH)
    claim = ExtractedClaim(
        claim_id="CLM-006",
        text="La búsqueda binaria tiene complejidad O(log n)",
        claim_type=ClaimType.FORMAL_COMPLEXITY,
        criticality=ClaimCriticality.CRITICAL,
        formal_parameters={"algorithm": "binary_search", "complexity": "O(log n)"},
    )
    evidence = []
    res = engine.ground_claim(claim, evidence)
    assert res.status == GroundingStatus.SUPPORTED
    assert res.grounding_score == 1.0
