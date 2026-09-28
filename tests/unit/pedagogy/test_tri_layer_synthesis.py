"""Tests for Tri-Layer Dialectical Synthesis and Configurable Notebook Author Roles."""

from study_engine.pedagogy.structured_pipeline import (
    AUTHOR_ROLES_BY_NOTEBOOK,
    classify_sources_by_role,
    build_tri_layer_instruction,
)
from study_engine.web.routes.chat import OfflineKnowledgeBackend, EpistemicContextPack


def test_author_roles_configured_for_all_five_subjects():
    assert "fadena-so2" in AUTHOR_ROLES_BY_NOTEBOOK
    assert "fadena-lenguajes" in AUTHOR_ROLES_BY_NOTEBOOK
    assert "fadena-std" in AUTHOR_ROLES_BY_NOTEBOOK
    assert "fadena-teleco" in AUTHOR_ROLES_BY_NOTEBOOK
    assert "fase0-soc" in AUTHOR_ROLES_BY_NOTEBOOK

    # Verify SO2 roles
    so2 = AUTHOR_ROLES_BY_NOTEBOOK["fadena-so2"]
    assert any("tanenbaum" in x for x in so2["pedagogical"])
    assert any("silberschatz" in x for x in so2["formal"])
    assert any("stallings" in x for x in so2["technical"])

    # Verify Lenguajes roles
    leng = AUTHOR_ROLES_BY_NOTEBOOK["fadena-lenguajes"]
    assert any("joyanes" in x for x in leng["pedagogical"])
    assert any("urrutia" in x for x in leng["formal"])
    assert any("stallman" in x for x in leng["technical"])

    # Verify STD roles
    std = AUTHOR_ROLES_BY_NOTEBOOK["fadena-std"]
    assert any("coronel" in x for x in std["pedagogical"])
    assert any("date" in x for x in std["formal"])
    assert any("elmasri" in x for x in std["technical"])

    # Verify Teleco roles
    tel = AUTHOR_ROLES_BY_NOTEBOOK["fadena-teleco"]
    assert any("kurose" in x for x in tel["pedagogical"])
    assert any("comer" in x for x in tel["formal"])
    assert any("stallings" in x for x in tel["technical"])


def test_classify_sources_by_role_so2():
    chunks = [
        {"source_id": "src_tanenbaum_os_modernos", "source_title": "Tanenbaum - Sistemas Operativos"},
        {"source_id": "src_silberschatz_so", "source_title": "Silberschatz - Conceptos de SO"},
        {"source_id": "src_stallings_os_internals_7ed", "source_title": "Stallings - OS Internals"},
    ]
    pack = EpistemicContextPack(formatted_context="", citations=[], chunks=chunks)
    classified = classify_sources_by_role(pack, "fadena-so2")

    assert len(classified["pedagogical"]) == 1
    assert "Tanenbaum" in classified["pedagogical"][0]
    assert len(classified["formal"]) == 1
    assert "Silberschatz" in classified["formal"][0]
    assert len(classified["technical"]) == 1
    assert "Stallings" in classified["technical"][0]


def test_build_tri_layer_instruction_keeps_explanatory_layers_optional():
    chunks = [
        {"source_id": "src_joyanes_fundamentos", "source_title": "Joyanes Aguilar"},
        {"source_id": "src_urrutia_programacion_c_principiantes", "source_title": "Urrutia Landa"},
    ]
    pack = EpistemicContextPack(formatted_context="", citations=[], chunks=chunks)
    instruction = build_tri_layer_instruction(pack, "fadena-lenguajes")

    assert "Intuición o analogía" in instruction
    assert "Mecanismo o formalismo" in instruction
    assert "Implementación o nivel de máquina" in instruction
    assert "no conviertas esta lista en tres secciones obligatorias" in instruction
    assert "solo si es útil" in instruction
    assert "Richard Feynman" not in instruction
    assert "CIERRE SOCRÁTICO OBLIGATORIO" not in instruction


def test_offline_knowledge_backend_tri_layer_and_socratic_questions():
    backend = OfflineKnowledgeBackend()
    queries = [
        "¿Cómo funciona una variable?",
        "¿Qué son las estructuras de control if y while?",
        "¿Cómo se define una función modular?",
        "¿Qué es el handshake de TCP?",
        "¿Cómo se calcula la latencia AMAT de caché?",
        "Consulta general no listada",
    ]

    for q in queries:
        res = backend(q)
        text = res.text
        assert "Capa 1: Intuición" in text or "Intuición" in text, f"Falta Capa 1 en: {q}"
        assert "Capa 2: Mecanismo" in text or "Mecanismo" in text, f"Falta Capa 2 en: {q}"
        assert "Capa 3: Nivel de Máquina" in text or "Máquina" in text, f"Falta Capa 3 en: {q}"
        assert "Desafío Socrático:" in text, f"Falta cierre socrático obligatorio en: {q}"


def test_extract_technical_checklist_and_security_evidence_instruction():
    """Verify technical checklist extraction and evidence-bounded security context."""
    from study_engine.pedagogy.structured_pipeline import (
        extract_technical_checklist,
        build_security_evidence_instruction,
        StructuredResponsePipeline,
    )
    from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT

    query = "¿Qué registros o banderas (FLAGS: Zero Flag, Carry Flag) se ven afectados en un short-circuit?"
    entities = extract_technical_checklist(query)
    assert "Zero Flag" in entities
    assert "Carry Flag" in entities

    security_instruction = build_security_evidence_instruction(query)
    assert security_instruction == ""

    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=None)
    phase = FASE0_CONTRACT.get_phase("conceptual")
    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query)

    assert "LISTA DE VERIFICACIÓN DE COBERTURA TÉCNICA OBLIGATORIA" in prompt
    assert "'Zero Flag'" in prompt
    assert "'Carry Flag'" in prompt
    assert "ANCLAJE A THREAT INTEL" not in prompt
    assert "CRITERIOS DE EVIDENCIA PARA AFIRMACIONES DE SEGURIDAD" not in prompt
    assert "Heartbleed" not in prompt
    assert "Tarea resuelta: responder la consulta." in prompt
    assert "Feynman de Barrio" not in prompt
