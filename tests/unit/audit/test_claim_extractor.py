"""Unit tests for ClaimExtractor in Subsystem S4.4."""

from study_engine.audit.claim_extractor import ClaimExtractor
from study_engine.audit.contracts import ClaimType


def test_claim_extractor_empty_and_whitespace():
    """Verify empty or whitespace strings return an empty tuple of claims."""
    extractor = ClaimExtractor()
    assert extractor.extract_claims("") == ()
    assert extractor.extract_claims("   \n\t  ") == ()


def test_claim_extractor_sentence_segmentation_and_citations():
    """Verify sentence segmentation with multiple citations and types."""
    extractor = ClaimExtractor()

    text = (
        "Hola a todos. "
        "Round Robin asigna un quantum de CPU [E1]. "
        "Sin embargo, CFS utiliza un árbol rojo-negro [E2] [E3]. "
        "¿Qué ocurre si el quantum expira?"
    )
    claims = extractor.extract_claims(text)
    assert len(claims) == 4

    # 1. Conversational greeting
    assert claims[0].claim_index == 0
    assert "Hola a todos" in claims[0].claim_text
    assert claims[0].claim_type == ClaimType.CONVERSATIONAL
    assert claims[0].cited_tags == ()

    # 2. Factual claim citing E1
    assert claims[1].claim_index == 1
    assert "Round Robin" in claims[1].claim_text
    assert claims[1].claim_type == ClaimType.FACTUAL
    assert claims[1].cited_tags == ("E1",)

    # 3. Factual claim citing E2 and E3
    assert claims[2].claim_index == 2
    assert "CFS" in claims[2].claim_text
    assert claims[2].claim_type == ClaimType.FACTUAL
    assert claims[2].cited_tags == ("E2", "E3")

    # 4. Question
    assert claims[3].claim_index == 3
    assert "¿Qué ocurre" in claims[3].claim_text
    assert claims[3].claim_type == ClaimType.QUESTION
    assert claims[3].cited_tags == ()


def test_claim_extractor_pedagogical_framing():
    """Verify pedagogical introductory statements are classified correctly."""
    extractor = ClaimExtractor()
    text = (
        "Vamos a analizar el problema paso a paso. "
        "El scheduler desaloja el proceso cuando el quantum expira [E1]."
    )
    claims = extractor.extract_claims(text)
    assert len(claims) == 2
    assert claims[0].claim_type == ClaimType.PEDAGOGICAL
    assert claims[0].cited_tags == ()
    assert claims[1].claim_type == ClaimType.FACTUAL
    assert claims[1].cited_tags == ("E1",)


def test_claim_extractor_comma_separated_citations_and_lead_in():
    """Verify multi-citations in single brackets and colon list lead-ins."""
    extractor = ClaimExtractor()
    text = (
        "El uso de estructuras se debe a las siguientes razones:\n"
        "* Se solicita memoria en tiempo de ejecución [E1, E2]."
    )
    claims = extractor.extract_claims(text)
    assert len(claims) == 2
    assert claims[0].claim_type == ClaimType.PEDAGOGICAL
    assert claims[0].cited_tags == ()
    assert claims[1].claim_type == ClaimType.FACTUAL
    assert claims[1].cited_tags == ("E1", "E2")
