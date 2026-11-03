"""Unit tests M1-02: selección determinista de oración verbatim en
concept_builder (calidad pedagógica del packet + preservación de identidad).

Contrato:
- La oración seleccionada es SUBSTRING del fragmento normalizado
  (hyphen-join + colapso de whitespace): identidad de contenido intacta.
- Rechazo determinista de ruido tipográfico: running head con número de
  página, arte de portada en mayúsculas, cortes en "(Fig.".
- Ranking por cobertura de términos del objetivo del KC.
- Sin candidato aceptable → "" (el builder recurre al template; el audit
  decide fail-closed). Jamás se emite texto no-verbatim o sin tag.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.pedagogy.concept_builder import (
    _is_noise_line,
    _normalize_chunk_text,
    _objective_terms,
    _select_verbatim_sentence,
)

OBJ_PUNTEROS = "Tramo 5: Aritmética de Punteros y Memoria Dinámica"

# Fragmento REAL (transcripción literal de working3, Joyanes p481 c0000):
# running head con "451", corte silábico "doblemen-\nte", "(Fig." y
# la oración pedagógicamente útil dentro del chunk.
CHUNK_JOYANES_481 = (
    "Estructuras dinámicas lineales de datos (pilas, colas y listas enlazadas)   451\n"
    "que apuntan hacia adelante y hacia atrás (Fig. 12.9). Como cada elemento tiene dos punteros, una lista doblemen-\n"
    "te enlazada ocupa más espacio en memoria que una lista simplemente enlazada para una misma cantidad de infor-\n"
    "mación.\n"
    "La lista necesita dos punteros CABECERA y FIN2 que apuntan hacia el primero y último nodo."
)

# Fragmento REAL (Think Like a Programmer p101 c0000): arte de portada
# "CODE/EAT/SLEEP" + intro en inglés.
CHUNK_TLAP_101 = (
    "CODE\nEAT\nSLEEP\nSOLVING PROBLEMS\nWITH POINTERS AND\nDYNAMIC MEMORY\n"
    "In this chapter, we will learn to solve problems using pointers and dynamic memory "
    "allocation, which will allow us to write flexible programs that can accommodate data "
    "sizes that are unknown until the program runs."
)

# Running head "… 91" (Think Like a Programmer p91) + contenido real.
CHUNK_TLAP_91 = (
    "Solving Problems with Pointers and Dynamic Memory   91\n"
    "Solving Pointer Problems By this point, you are probably ready for some problems, "
    "so let us look at how we can use pointers and dynamic memory allocation to solve them."
)


def test_hyphen_join_and_noise_lines_are_normalized():
    normalized = _normalize_chunk_text(CHUNK_JOYANES_481)
    assert "doblemente enlazada" in normalized  # hyphen-join
    assert "451" not in normalized  # running head (línea con número de página) fuera
    assert "que apuntan hacia adelante" in normalized  # contenido real conservado


def test_cover_art_and_running_head_lines_marked_noise():
    assert _is_noise_line("CODE")
    assert _is_noise_line("EAT")
    assert _is_noise_line("WITH POINTERS AND")
    assert _is_noise_line("Estructuras dinámicas lineales de datos (pilas, colas) 451")
    assert not _is_noise_line("Como cada elemento tiene dos punteros.")
    assert not _is_noise_line("La lista necesita dos punteros CABECERA y FIN2.")


def test_selection_avoids_running_head_and_fig_cutoff():
    """La oración elegida NO es el fragmento del running head ni el corte de "(Fig."."""
    selected = _select_verbatim_sentence(CHUNK_JOYANES_481, OBJ_PUNTEROS)
    assert selected
    assert selected.startswith("Como cada elemento")
    assert "(Fig." not in selected
    assert "451" not in selected


def test_selection_preserves_verbatim_identity():
    """Substring-exacto del fragmento normalizado (hyphen-join no reescribe palabras)."""
    selected = _select_verbatim_sentence(CHUNK_JOYANES_481, OBJ_PUNTEROS)
    normalized = _normalize_chunk_text(CHUNK_JOYANES_481)
    assert selected in normalized
    # Identidad NLI: sentence == substring del contenido del chunk citado.
    assert "doblemente enlazada" in selected  # palabra re-ensamblada del corte "doblemen-\nte"


def test_selection_survives_cover_art_prefix():
    selected = _select_verbatim_sentence(CHUNK_TLAP_101, OBJ_PUNTEROS)
    assert selected
    assert "CODE" not in selected.split(",")[0]
    assert "pointers and dynamic memory" in selected.lower()


def test_selection_skips_running_head_page_number():
    selected = _select_verbatim_sentence(CHUNK_TLAP_91, OBJ_PUNTEROS)
    assert selected
    assert "91" not in selected
    # El running head con "91" queda fuera; la oración elegida es el contenido
    # real bajo el encabezado.
    assert selected.strip().startswith("Solving Pointer Problems")
    assert "pointers and dynamic memory allocation" in selected.lower()


def test_ranking_prefers_higher_term_coverage():
    """La oración con más cobertura del objetivo gana, no la primera del chunk."""
    chunk = (
        "Encabezado de pagina decorativa 12\n"
        "El curso introduce varios temas generales de programación que no se relacionan "
        "directamente con el objetivo del tramo actual.\n"
        "En lenguaje C, la aritmética de punteros escala el desplazamiento por el tamaño del "
        "tipo apuntado, y la memoria del arreglo se addressa de forma lineal."
    )
    selected = _select_verbatim_sentence(chunk, OBJ_PUNTEROS)
    assert "aritmética de punteros" in selected


def test_junk_only_chunk_returns_empty_string():
    """Sin oración aceptable → '': el builder recurre al template (fail-closed)."""
    assert _select_verbatim_sentence("451\n441\n12\n", OBJ_PUNTEROS) == ""
    assert _select_verbatim_sentence("", OBJ_PUNTEROS) == ""
    assert _select_verbatim_sentence(None, OBJ_PUNTEROS) == ""


def test_objective_terms_extraction_is_deterministic():
    terms = _objective_terms(OBJ_PUNTEROS)
    assert terms == ["aritmética", "punteros", "memoria", "dinámica"]
    assert _objective_terms("") == []
    assert _objective_terms(None) == []


def test_no_regression_when_chunk_has_no_noise():
    """Chunk limpio: la oración elegida sigue siendo un substring verbatim
    completo y el ranking elige la más cubierta por el objetivo."""
    chunk = (
        "Un puntero es una variable que contiene la dirección de memoria de otro objeto. "
        "La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado."
    )
    selected = _select_verbatim_sentence(chunk, OBJ_PUNTEROS)
    # "aritmética de punteros" (2 términos del objetivo) gana a "puntero" (1).
    assert selected == (
        "La aritmética de punteros escala el desplazamiento por el tamaño del tipo apuntado."
    )
    assert selected in _normalize_chunk_text(chunk)


def test_build_proposal_emits_tagged_verbatim_sentences():
    """Integración del builder: oraciones taggadas [E#] verbatim del fragmento."""
    from study_engine.contracts.evidence_engine import CitationRecord
    from study_engine.pedagogy.concept_builder import ConceptPacketBuilder

    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-joyanes-481",
        document_id="doc-joyanes",
        source_id="src-joyanes",
        source_title="Fundamentos de programación",
        content_hash="0" * 64,
    )
    packet = ConceptPacketBuilder().build_proposal(
        notebook_id="fase0-soc",
        kc_id="aritmetica_punteros",
        objective=OBJ_PUNTEROS,
        evidence_by_role={"PRIMARY": [rec], "METHODOLOGICAL": [], "FORMAL": [], "IMPLEMENTATION": []},
        all_citations=[rec],
        content_by_citation={"E1": CHUNK_JOYANES_481},
    )
    assert packet.core_concept.startswith("[E1] Como cada elemento tiene dos punteros")
    assert "451" not in packet.core_concept
    # El texto auditado conserva identidad: la oración sigue siendo substring
    # del fragmento citado (normalizado).
    assert "Como cada elemento tiene dos punteros" in _normalize_chunk_text(CHUNK_JOYANES_481)


def test_build_proposal_never_emits_ungrounded_templates():
    """M1-02 (hallazgo live Tramo 1): sin oración verbatim admisible NO se
    emite template taggeado (core ni mental_model). Un template ('según la
    literatura canónica...', 'casilleros contiguos...') afirma soporte que no
    existe en la evidencia y el NLI lo rechaza — la abstención honesta es
    anterior (el orchestrator abstiene con core vacío)."""
    from study_engine.contracts.evidence_engine import CitationRecord
    from study_engine.pedagogy.concept_builder import ConceptPacketBuilder

    rec = CitationRecord(
        citation_id="E1",
        chunk_id="chk-junk",
        document_id="doc-junk",
        source_id="src-junk",
        source_title="Fuente con junk",
        content_hash="0" * 64,
    )
    junk = "451\n441\n12\n"
    packet = ConceptPacketBuilder().build_proposal(
        notebook_id="fase0-soc",
        kc_id="aritmetica_punteros",
        objective=OBJ_PUNTEROS,
        evidence_by_role={"PRIMARY": [rec], "METHODOLOGICAL": [], "FORMAL": [], "IMPLEMENTATION": []},
        all_citations=[rec],
        content_by_citation={"E1": junk},
    )
    assert packet.core_concept.strip() == ""  # sin template taggeado
    assert packet.mental_model.strip() == ""  # sin template 'casilleros'
    # La guidance KC-específica de punteros tampoco se emite sin grounded-ness.
    assert packet.reasoning_guidance.strip() == ""


def test_build_proposal_reasoning_guidance_not_kc_locked():
    """La guidance del builder ya no es el texto fijo de punteros: con una
    fuente METHODOLOGICAL con oración verbatim, guidance sigue vacía (no
    auditable) y el modelo mental porta la oración grounded."""
    from study_engine.contracts.evidence_engine import CitationRecord
    from study_engine.pedagogy.concept_builder import ConceptPacketBuilder

    primary = CitationRecord(
        citation_id="E1",
        chunk_id="chk-p",
        document_id="doc-p",
        source_id="src-p",
        source_title="Primaria",
        content_hash="0" * 64,
    )
    method = CitationRecord(
        citation_id="E2",
        chunk_id="chk-m",
        document_id="doc-m",
        source_id="src-m",
        source_title="Metodológica",
        content_hash="0" * 64,
    )
    packet = ConceptPacketBuilder().build_proposal(
        notebook_id="fase0-soc",
        kc_id="aritmetica_punteros",
        objective=OBJ_PUNTEROS,
        evidence_by_role={"PRIMARY": [primary], "METHODOLOGICAL": [method]},
        all_citations=[primary, method],
        content_by_citation={
            "E1": CHUNK_JOYANES_481,
            "E2": "Un modelo útil consiste en imaginar la memoria como una calle de casas numeradas correlativamente.",
        },
    )
    assert packet.mental_model.startswith("[E2] ")
    assert packet.reasoning_guidance == ""
