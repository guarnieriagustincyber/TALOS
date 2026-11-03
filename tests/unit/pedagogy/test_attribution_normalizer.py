"""M1-04b: contrato del normalizador determinista de atribuciones genéricas.

Autorización propietaria M1-04b: transformación acotada aplicada a la
respuesta candidata ANTES del ClaimExtractor y de S4.4.

Propiedades verificadas:
  1. Positivas (bytes del corpus real M1-04): la envoltura se elimina,
     discurso/proposición/tags/signos preservados byte-a-byte.
  2. Negativas: negación, modal/futuro, pregunta, comillas literales,
     oración sin tag y proposición vacía NO se transforman (fail-closed).
  3. Equivalencia: ClaimExtractor antes/después conserva tipo de claim,
     cited_tags y los bytes de la proposición técnica.
  4. La transformación NO convierte una afirmación no sustentada en
     aparentemente válida: la proposición permanece idéntica ante S4.4.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from study_engine.audit.claim_extractor import ClaimExtractor, ClaimType
from study_engine.pedagogy.attribution_normalizer import (
    normalize_attribution_frames,
)

# Bytes reales preservados del corpus M1-04 (baseline_repro.json / dumps).
# Forma H_FRAMING_APPROVED (053524Z#c2): ENTAILED histórico.
_H_APPROVED = (
    "Sin embargo, las fuentes sí establecen que un array, o arreglo, es una "
    "secuencia de posiciones de la memoria central a las que se puede acceder "
    "directamente, que contiene datos del mismo tipo y pueden ser "
    "seleccionados individualmente mediante el uso de subíndices [E1]."
)
# Forma H_FRAMING_REJECTED (051652Z#c2): NOT_ENTAILED histórico (rationale:
# "no menciona que las 'fuentes autorizadas' establezcan dicha definición").
_H_REJECTED = (
    "Las fuentes autorizadas establecen que un array, o arreglo, es una "
    "secuencia de posiciones de la memoria central a las que se puede acceder "
    "directamente, que contiene datos del mismo tipo y que pueden ser "
    "seleccionados individualmente mediante el uso de subíndices [E1]."
)


def _norm(text):
    return normalize_attribution_frames(text)


def test_positivo_corpus_h_approved():
    out, regs = _norm(_H_APPROVED)
    assert len(regs) == 1
    # discurso preservado; envoltura eliminada; proposición y tag intactos
    assert out == (
        "Sin embargo, Un array, o arreglo, es una "
        "secuencia de posiciones de la memoria central a las que se puede acceder "
        "directamente, que contiene datos del mismo tipo y pueden ser "
        "seleccionados individualmente mediante el uso de subíndices [E1]."
    )
    assert regs[0].removed == "las fuentes sí establecen que"


def test_positivo_corpus_h_rejected():
    out, regs = _norm(_H_REJECTED)
    assert len(regs) == 1
    assert regs[0].removed == "Las fuentes autorizadas establecen que"
    # la proposición técnica queda byte-a-byte (capitalización inicial de
    # oración es el único cambio de presentación)
    assert "Un array, o arreglo, es una secuencia de posiciones de la memoria central" in out
    assert "[E1]." in out


def test_positivo_tag_leading_040132Z():
    """Bytes reales M1-03 040132Z: tag delante de la envoltura."""
    claim = (
        "[E1] Las fuentes autorizadas definen que un array o arreglo es una "
        "secuencia de posiciones de la memoria central a las que se puede "
        "acceder directamente, que contienen datos del mismo tipo y pueden "
        "ser seleccionados individualmente mediante el uso de subíndices."
    )
    out, regs = _norm(claim)
    assert len(regs) == 1
    assert regs[0].removed == "Las fuentes autorizadas definen que"
    # tag intacto al inicio; envoltura eliminada; proposición byte-idéntica
    assert out.startswith("[E1] Un array o arreglo es una secuencia")
    assert out.endswith("mediante el uso de subíndices.")
    # el extractor mantiene el mapeo claim<->tag (condición 3)
    ex = ClaimExtractor().extract_claims(out)
    fact = [c for c in ex if c.claim_type == ClaimType.FACTUAL and c.cited_tags]
    assert len(fact) == 1 and fact[0].cited_tags == ("E1",)


def test_negacion_modal_pregunta_comillas_sin_tag_no_transforman():
    cases = [
        "las fuentes no mencionan que malloc inicialice la memoria [E1].",
        "Las fuentes podrían establecer que el heap crece hacia abajo [E1].",
        "las fuentes definirán que un array es una secuencia [E1].",
        "¿Las fuentes establecen que un array es una secuencia [E1]?",
        'La referencia «Un array es una secuencia» es clara [E1].',
        "Sin evidencia disponible, no afirmo que malloc tenga ese comportamiento.",
        "las fuentes establecen que",
        "",
    ]
    for text in cases:
        out, regs = _norm(text)
        assert out == text, f"cambio prohibido sobre: {text[:60]!r}"
        assert regs == []


def test_idempotencia_y_pasaje_transparente():
    # texto sin marco: identidad byte-a-byte
    plain = "Un array, o arreglo, es una secuencia de posiciones de la memoria central [E1]."
    out, regs = _norm(plain)
    assert out == plain and regs == []
    # normalizar dos veces no cambia nada más
    out1, r1 = _norm(_H_REJECTED)
    out2, r2 = _norm(out1)
    assert out2 == out1 and r2 == []


def test_equivalencia_claim_extractor_antes_despues():
    """El extractor ve el mismo tipo, mismos tags y la proposición técnica."""
    ex = ClaimExtractor()
    before = ex.extract_claims(_H_REJECTED)
    after_text, _ = _norm(_H_REJECTED)
    after = ex.extract_claims(after_text)
    fact_b = [c for c in before if c.claim_type == ClaimType.FACTUAL and c.cited_tags]
    fact_a = [c for c in after if c.claim_type == ClaimType.FACTUAL and c.cited_tags]
    assert len(fact_b) == len(fact_a) == 1
    # mismos tags exactos
    assert fact_b[0].cited_tags == fact_a[0].cited_tags == ("E1",)
    # la proposición técnica es idéntica en ambos claims (sólo cambia la
    # envoltura de atribución y la capitalización inicial de presentación)
    core_b = fact_b[0].claim_text.replace(
        "Las fuentes autorizadas establecen que un array",
        "Un array", 1,
    )
    assert fact_a[0].claim_text == core_b


def test_transformacion_no_crea_aparente_validez():
    """Proposición NO sustentada permanece idéntica: S4.4 la verá igual."""
    bad = (
        "Las fuentes autorizadas establecen que malloc libera automáticamente "
        "toda la memoria asignada al finalizar el programa [E1]."
    )
    out, regs = _norm(bad)
    assert len(regs) == 1
    # la proposición técnica sigue estando ahí, verbatim, para el juez NLI
    assert "Malloc libera automáticamente toda la memoria asignada" in out
    assert "[E1]." in out


def test_multiples_oraciones_transforma_solo_las_que_aplican():
    text = (
        "No tengo evidencia para confirmar la reserva implícita [E2].\n\n"
        + _H_APPROVED
        + "\n\n¿Querés que veamos la operación con subíndices?"
    )
    out, regs = _norm(text)
    assert len(regs) == 1
    assert "No tengo evidencia para confirmar la reserva implícita [E2]." in out
    assert "Sin embargo, Un array" in out
    assert "¿Querés que veamos" in out
