"""Unit tests for LexicalGuard in Subsystem S4.4."""

from study_engine.audit.contracts import (
    ClaimType,
    LexicalAnomalyStatus,
)
from study_engine.audit.lexical_guard import LexicalGuard


def test_lexical_guard_normal_overlap_no_anomaly():
    """Verify well-grounded claim with shared terminology flags NO_ANOMALY."""
    guard = LexicalGuard()
    chunk = (
        "El algoritmo Round Robin asigna un quantum fijo de tiempo a cada "
        "proceso en la cola de listos."
    )
    claim = "Round Robin asigna un quantum fijo a cada proceso."

    diag = guard.diagnose(claim_text=claim, evidence_text=chunk)
    assert diag.status == LexicalAnomalyStatus.NO_ANOMALY
    assert diag.token_overlap_ratio > 0.5
    assert diag.technical_entities_missing == ()


def test_lexical_guard_missing_technical_entity_anomaly():
    """Verify claim introducing code calls not in chunk flags anomaly."""
    guard = LexicalGuard()
    chunk = (
        "La memoria se gestiona mediante segmentos paginados en "
        "memoria física."
    )

    claim = "Para reservar memoria, el proceso ejecuta malloc() y sys_brk()."

    diag = guard.diagnose(claim_text=claim, evidence_text=chunk)
    assert diag.status == LexicalAnomalyStatus.LEXICAL_ANOMALY
    assert "malloc()" in diag.technical_entities_missing
    assert "sys_brk" in diag.technical_entities_missing


def test_lexical_guard_hex_numeric_anomaly():
    """Verify claim introducing fabricated hex addresses flags anomaly."""
    guard = LexicalGuard()
    chunk = "El vector de interrupciones se ubica en las direcciones bajas."

    claim = "La rutina de atención se ejecuta en la dirección 0x8080ff."

    diag = guard.diagnose(claim_text=claim, evidence_text=chunk)
    assert diag.status == LexicalAnomalyStatus.LEXICAL_ANOMALY
    assert "0x8080ff" in diag.technical_entities_missing


def test_lexical_guard_short_inconclusive():
    """Verify very short claims are marked INCONCLUSIVE."""
    guard = LexicalGuard()
    chunk = "Contenido amplio sobre sistemas operativos y gestión de archivos."
    claim = "Es correcto."

    diag = guard.diagnose(claim_text=claim, evidence_text=chunk)
    assert diag.status == LexicalAnomalyStatus.INCONCLUSIVE


def test_lexical_guard_conversational_no_anomaly():
    """Verify conversational sentences do not trigger lexical anomaly."""
    guard = LexicalGuard()
    chunk = "Contenido técnico sobre schedulers."
    claim = "¿Hola, cómo estás?"

    diag = guard.diagnose(
        claim_text=claim,
        evidence_text=chunk,
        claim_type=ClaimType.CONVERSATIONAL,
    )
    assert diag.status == LexicalAnomalyStatus.NO_ANOMALY
