"""Focal F1 tests: markdown-aware structural vs factual classification.

Verifies that purely presentational elements (labels, dividers, code) are
distinguished from knowledge-communicating claims, and that headings, lists and
code blocks that *do* assert something keep the full grounding requirement.
"""

from study_engine.audit.claim_extractor import ClaimExtractor
from study_engine.audit.contracts import ClaimType


def _single(text):
    claims = ClaimExtractor().extract_claims(text)
    assert len(claims) == 1, [c.claim_type for c in claims]
    return claims[0]


def test_heading_label_is_structural():
    claim = _single("## Introducción")
    assert claim.claim_type == ClaimType.STRUCTURAL
    assert claim.cited_tags == ()


def test_noun_phrase_heading_is_structural():
    for heading in ("## Uso de memoria", "## Definición", "## Funcionamiento"):
        assert _single(heading).claim_type == ClaimType.STRUCTURAL


def test_heading_with_assertion_is_factual():
    assert _single("## El scheduler desaloja el proceso").claim_type == ClaimType.FACTUAL


def test_bullet_label_is_structural_but_assertion_is_factual():
    label = _single("- Uso de memoria")
    assertion = _single("- El kernel libera la página tras el uso")
    assert label.claim_type == ClaimType.STRUCTURAL
    assert assertion.claim_type == ClaimType.FACTUAL


def test_verbless_bullets_that_assert_are_factual():
    """Verbless phrases still assert when they carry quantifier/modal/evaluative markers."""
    for text in (
        "- Mayor eficiencia",
        "- Resultados siempre correctos",
        "- Clave primaria obligatoriamente numérica",
        "- Latencia mínima",
        "- Alta disponibilidad",
    ):
        claim = _single(text)
        assert claim.claim_type == ClaimType.FACTUAL, text


def test_verbless_headings_that_assert_are_factual():
    for text in (
        "## Mayor eficiencia",
        "## Resultados siempre correctos",
        "## Clave primaria obligatoriamente numérica",
    ):
        assert _single(text).claim_type == ClaimType.FACTUAL, text


def test_presentational_headings_remain_structural():
    for text in (
        "## Introducción",
        "## Uso de memoria",
        "## Ventajas",
        "## Limitaciones",
        "## Funcionamiento",
        "## Más información",
    ):
        assert _single(text).claim_type == ClaimType.STRUCTURAL, text


def test_evidence_insufficiency_is_a_meta_claim_not_factual():
    for text in (
        "La evidencia proporcionada no menciona ni define el término quantum.",
        "El contexto es insuficiente para responder esa parte.",
        "No hay evidencia suficiente sobre el tema.",
        "No se proporciona información sobre la latencia.",
    ):
        assert _single(text).claim_type == ClaimType.CONVERSATIONAL, text


def test_evidence_disclaimer_cannot_smuggle_a_contrastive_claim():
    text = "La evidencia no menciona el quantum, pero el quantum siempre es 10 ms."
    assert _single(text).claim_type == ClaimType.FACTUAL


def test_evidence_disclaimer_cannot_smuggle_a_consequential_claim():
    text = "La evidencia no menciona el quantum, por lo tanto el quantum es 10 ms."
    assert _single(text).claim_type == ClaimType.FACTUAL


def test_evidence_statement_that_asserts_content_is_factual():
    text = "La evidencia proporcionada muestra que el planificador usa quantum."
    assert _single(text).claim_type == ClaimType.FACTUAL


def test_cited_bullet_is_factual():
    claim = _single("- Se solicita memoria en tiempo de ejecución [E1, E2]")
    assert claim.claim_type == ClaimType.FACTUAL
    assert claim.cited_tags == ("E1", "E2")


def test_fenced_code_lines_without_assertion_are_structural():
    text = "```c\nint x = 5;\n#include <stdio.h>\nreturn x;\n# COMPLETAR LÓGICA\n```"
    claims = ClaimExtractor().extract_claims(text)
    factual = [c for c in claims if c.claim_type == ClaimType.FACTUAL]
    assert factual == []


def test_code_comment_assertion_is_factual():
    text = "```c\n// Round Robin asigna un quantum fijo\n```"
    claims = ClaimExtractor().extract_claims(text)
    factual = [c for c in claims if c.claim_type == ClaimType.FACTUAL]
    assert len(factual) == 1
    assert "Round Robin" in factual[0].claim_text


def test_code_string_assertion_is_factual():
    text = '```c\nprintf("El scheduler desaloja el proceso");\n```'
    claims = ClaimExtractor().extract_claims(text)
    factual = [c for c in claims if c.claim_type == ClaimType.FACTUAL]
    assert len(factual) == 1


def test_todo_and_directive_comments_are_structural():
    text = "```c\n# COMPLETAR LÓGICA DE INTERCAMBIO\n#include <stdio.h>\n```"
    claims = ClaimExtractor().extract_claims(text)
    assert all(c.claim_type == ClaimType.STRUCTURAL for c in claims)


def test_verbless_code_comment_assertion_is_factual():
    text = "```c\n// Mayor eficiencia operativa\n```"
    claims = ClaimExtractor().extract_claims(text)
    factual = [c for c in claims if c.claim_type == ClaimType.FACTUAL]
    assert len(factual) == 1


def test_hr_and_table_separator_are_structural():
    text = "---\n| --- | --- |"
    claims = ClaimExtractor().extract_claims(text)
    assert len(claims) == 2
    assert all(c.claim_type == ClaimType.STRUCTURAL for c in claims)


def test_prose_semantics_unchanged():
    """Existing prose behaviour must not regress (>=2 words -> FACTUAL)."""
    text = (
        "Hola a todos. "
        "Round Robin asigna un quantum de CPU [E1]. "
        "¿Qué ocurre si el quantum expira?"
    )
    claims = ClaimExtractor().extract_claims(text)
    assert [c.claim_type for c in claims] == [
        ClaimType.CONVERSATIONAL,
        ClaimType.FACTUAL,
        ClaimType.QUESTION,
    ]
    assert claims[1].cited_tags == ("E1",)
