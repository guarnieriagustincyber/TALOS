"""COMMIT 4 fix(citations): validación de formato de IDs de cita.

Bug visto en pruebas manuales: el LLM emite placeholders vacíos o nulos
("[E#]", "[E# 0]") y el validador original (`\\[E(\\d+)\\]`) no los capturaba:
leakeaban al frontend como ruido.

Contrato:
- IDs vacíos ([E], [E#]) o <1 ([E0], [E# 0]) → inválidos + log de anomalía.
- IDs numéricos válidos fuera del pack → inválidos (comportamiento previo).
- IDs válidos → intocados. Idempotencia preservada.
"""

import logging

from study_engine.pedagogy.citation_validator import CitationValidator

CHUNKS = [
    {"id": "E1", "citation_id": "E1", "chunk_text": "a"},
    {"id": "E2", "citation_id": "E2", "chunk_text": "b"},
]


def test_citas_malformadas_se_rechazan(caplog):
    v = CitationValidator()
    text = "Según [E#] y también [E0] y [E# 0], el concepto vale [E2]."
    with caplog.at_level(logging.WARNING):
        corrected, invalid = v.validate_and_rewrite(text, CHUNKS)
    assert "[E#]" not in corrected and "[E0]" not in corrected and "[E# 0]" not in corrected
    assert corrected.count("[ref. no verificada]") == 3
    assert "[E2]" in corrected
    assert set(invalid) == {"[E#]", "[E0]", "[E# 0]"}
    assert any("malformada" in rec.message for rec in caplog.records)


def test_citas_invalidas_numericas_siguen_rechazadas():
    v = CitationValidator()
    corrected, invalid = v.validate_and_rewrite("ver [E99] y [E1]", CHUNKS)
    assert "[ref. no verificada]" in corrected
    assert "[E1]" in corrected
    assert invalid == ["[E99]"]


def test_audit_only_detecta_malformadas(caplog):
    v = CitationValidator()
    with caplog.at_level(logging.WARNING):
        valid, invalid = v.audit_only("nada: [E#] y [E1]", CHUNKS)
    assert valid == ["[E1]"]
    assert invalid == ["[E#]"]
    assert any("malformada" in rec.message for rec in caplog.records)


def test_texto_sin_citas_intacto_e_idempotente():
    v = CitationValidator()
    text = "Respuesta sin referencias."
    corrected, invalid = v.validate_and_rewrite(text, CHUNKS)
    assert corrected == text and invalid == []
