"""Unit tests for FASE S4: Adaptive Pipeline and Pedagogical Intent Routing."""

from unittest.mock import MagicMock
import pytest

from study_engine.pedagogy.structured_pipeline import (
    RESPONSE_MODES,
    classify_pedagogical_intent,
    build_mode_specific_instruction,
    StructuredResponsePipeline,
)
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.student_context import (
    determine_pedagogical_context_mode,
    build_bkt_adaptation_directive,
)
from study_engine.student.contracts import BKTState
from study_engine.web.routes.chat import OfflineKnowledgeBackend
from study_engine.contracts.search import SearchResult


def test_intent_router_classification():
    """Verify that user queries are mapped to appropriate RESPONSE_MODES (Fix S4.1)."""
    # 1. Compare
    assert classify_pedagogical_intent("Compara arrays contiguos vs listas enlazadas en memoria") == "compare"
    assert classify_pedagogical_intent("¿Cuál es la diferencia entre TCP y UDP?") == "compare"
    assert classify_pedagogical_intent("Hacé un cuadro comparativo entre mutex y semáforos") == "compare"

    # 2. Give example
    assert classify_pedagogical_intent("Dame un ejemplo de código en C para abrir un socket") == "give_example"
    assert classify_pedagogical_intent("Mostrame un ejemplo práctico de cláusula de guarda") == "give_example"
    assert classify_pedagogical_intent("¿Cómo se implementa un bucle while?") == "give_example"

    # 3. Simplify
    assert classify_pedagogical_intent("Explicamelo simple como para un niño de 5 años") == "simplify"
    assert classify_pedagogical_intent("Explicación muy simple y sin tecnicismos de la memoria RAM") == "simplify"
    assert classify_pedagogical_intent("Feynman simple sobre punteros") == "simplify"

    # 4. Evaluate code / Forensic audit
    assert classify_pedagogical_intent("Revisa este código y evalúa posibles desbordamientos de buffer") == "evaluate_code"
    assert classify_pedagogical_intent("¿Está bien este código en C? ```int *p = NULL; *p = 5;```") == "evaluate_code"
    assert classify_pedagogical_intent("Auditar la siguiente solución en Python que intenta validar una dirección IPv4. El código contiene varios bugs sutiles:") == "evaluate_code"
    assert classify_pedagogical_intent("Audita este código y señala las fallas de seguridad") == "evaluate_code"

    # 5. Deep dive
    assert classify_pedagogical_intent("Hacé un análisis exhaustivo y en profundidad del algoritmo") == "deep_dive"
    assert classify_pedagogical_intent("Deep dive técnico con todos los detalles de la tabla de páginas") == "deep_dive"

    # 6. Quick answer
    assert classify_pedagogical_intent("En una frase, decime la definición rápida de atomicidad") == "quick_answer"
    assert classify_pedagogical_intent("Brevemente, respuesta rápida sobre si RAM es volátil") == "quick_answer"

    # 7. Resolve misconception / Duda conceptual o conflicto epistémico
    assert classify_pedagogical_intent(
        "No entiendo por qué decís que '010.0.0.1' es un error o un peligro. En matemáticas 010 es igual a 10."
    ) == "resolve_misconception"
    assert classify_pedagogical_intent(
        "¿Por qué el código debería rechazarlo si el valor numérico sigue siendo 10 y está entre 0 y 255?"
    ) == "resolve_misconception"
    assert classify_pedagogical_intent(
        "¿Por qué es un error si en matemáticas un cero a la izquierda no cambia el valor?"
    ) == "resolve_misconception"

    # 8. Default explain concept
    assert classify_pedagogical_intent("¿Qué es un proceso en el sistema operativo?") == "explain_concept"
    assert classify_pedagogical_intent("¿Por qué necesitamos el registro program counter?") == "explain_concept"


def test_build_phase_prompt_adapts_to_response_modes():
    """Verify that build_phase_prompt adjusts formatting, word count, and socratic requirements."""
    contract = PedagogicalContract(
        contract_id="contract_test",
        notebook_id="fase0-soc",
        version="1.0.0",
        authoritative_sources=("src_test",),
        domain_scope=("test",),
        base_system_prompt="Tutor TALOS.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                max_tokens=400,
                phase_prompt_template="Explica: {concept}",
            ),
        ],
    )
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=MagicMock())
    phase = contract.get_phase("conceptual")

    # Mode: Compare -> Table format, 300 words, socratic
    prompt_compare = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Compara memoria contigua vs listas",
        pedagogical_mode="compare",
    )
    assert "COMPARACIÓN ESTRUCTURADA (FORMATO TABLA)" in prompt_compare
    assert "Extensión pedagógica objetivo: hasta 300 palabras" in prompt_compare
    assert "pregunta socrática" in prompt_compare

    # Mode: Give example -> Code format, 500 words, no forced socratic
    prompt_example = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Dame un ejemplo de socket en C",
        pedagogical_mode="give_example",
    )
    assert "EJEMPLO PRÁCTICO (FORMATO CÓDIGO IDIOMÁTICO)" in prompt_example
    assert "Extensión pedagógica objetivo: hasta 500 palabras" in prompt_example
    assert "sin pregunta socrática forzada" in prompt_example

    # Mode: Simplify -> 1 layer, 200 words, no forced socratic
    prompt_simplify = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Explicamelo simple",
        pedagogical_mode="simplify",
    )
    assert "SÍNTESIS SIMPLIFICADA (ESTILO FEYNMAN ACCESIBLE)" in prompt_simplify
    assert "Extensión pedagógica objetivo: hasta 200 palabras" in prompt_simplify

    # Mode: Quick answer -> 100 words, concise
    prompt_quick = pipeline.build_phase_prompt(
        phase=phase,
        user_query="En una frase qué es RAM",
        pedagogical_mode="quick_answer",
    )
    assert "RESPUESTA RÁPIDA Y CONCISA" in prompt_quick
    assert "Extensión pedagógica objetivo: hasta 100 palabras" in prompt_quick

    # Mode: Evaluate code / Forensic audit -> 2500 words, bug-by-bug forensic protocol
    prompt_audit = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Auditar la siguiente solución en Python para validar IPv4",
        pedagogical_mode="evaluate_code",
    )
    assert "AUDITORÍA FORENSE DE CÓDIGO Y CIBERDEFENSA" in prompt_audit
    assert "Auditoría Técnica y Análisis de Bugs (Diagnóstico Forense Específico)" in prompt_audit
    assert "REGLA DE ORO DE SEGURIDAD EN PYTHON" in prompt_audit
    assert "es_digito_ascii" in prompt_audit
    assert "CVE-2021-29921" in prompt_audit

    # Mode: Resolve misconception -> 1500 words, epistemic scaffolding
    prompt_misconception = pipeline.build_phase_prompt(
        phase=phase,
        user_query="No entiendo por qué 010.0.0.1 es un error si en matemáticas 010 es 10",
        pedagogical_mode="resolve_misconception",
    )
    assert "RESOLUCIÓN DE CONFLICTO EPISTÉMICO Y ANDAMIAJE SOCRÁTICO" in prompt_misconception
    assert "Validación Cognitiva y Desarme de la Frustración" in prompt_misconception
    assert "Regla de Oro: Modelar el Mecanismo, No Metáforas Vacías" in prompt_misconception
    assert "Parser Differential / CVE-2021-29921" in prompt_misconception
    assert "Extensión pedagógica objetivo: hasta 1500 palabras" in prompt_misconception


def test_bkt_influences_pedagogical_context_mode():
    """Verify that BKT mastery levels dictate basic, intermediate, and advanced modes (Fix S4.2)."""
    tracker = MagicMock()
    catalog = {
        "fase0-soc": {
            "kcs": [
                {"kc_id": "kc_advanced", "prerequisites": []},
                {"kc_id": "kc_basic", "prerequisites": []},
                {"kc_id": "kc_intermediate", "prerequisites": []},
            ]
        }
    }

    # Case 1: P(L) = 0.92 -> Advanced (evaluado, attempts > 0)
    tracker.get_state.side_effect = lambda kc: BKTState(
        kc_id=kc,
        p_L=0.92 if kc == "kc_advanced" else (0.15 if kc == "kc_basic" else 0.65),
        attempts=1,
    )

    mode_adv, meta_adv = determine_pedagogical_context_mode(
        target_kc_id="kc_advanced",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="fase0-soc",
    )
    assert mode_adv == "advanced"
    assert meta_adv["p_L"] == 0.92
    dir_adv = build_bkt_adaptation_directive(mode_adv, meta_adv)
    assert "NIVEL AVANZADO / MAESTRÍA" in dir_adv
    assert "NUNCA expliques definiciones elementales" in dir_adv

    # Case 2: P(L) = 0.15 -> Basic (evaluado, attempts > 0)
    mode_basic, meta_basic = determine_pedagogical_context_mode(
        target_kc_id="kc_basic",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="fase0-soc",
    )
    assert mode_basic == "basic"
    assert meta_basic["p_L"] == 0.15
    dir_basic = build_bkt_adaptation_directive(mode_basic, meta_basic)
    assert "NIVEL INICIAL / CONCEPTUAL" in dir_basic
    assert "Partí obligatoriamente de analogías cotidianas" in dir_basic

    # Case 3: P(L) = 0.65 -> Intermediate (evaluado, attempts > 0)
    mode_inter, meta_inter = determine_pedagogical_context_mode(
        target_kc_id="kc_intermediate",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="fase0-soc",
    )
    assert mode_inter == "intermediate"
    dir_inter = build_bkt_adaptation_directive(mode_inter, meta_inter)
    assert "NIVEL INTERMEDIO / CONSOLIDACIÓN" in dir_inter

    # Case 4: KC identificado sin historial usa el cold-start pedagógico configurado.
    tracker.get_state.side_effect = lambda kc: BKTState(
        kc_id=kc,
        p_L=0.10,
        attempts=0,
    )
    mode_cold, meta_cold = determine_pedagogical_context_mode(
        target_kc_id="kc_basic",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="fase0-soc",
    )
    assert mode_cold == "basic"
    assert meta_cold["attempts"] == 0
    assert meta_cold["cold_start_mode"] == "basic"


def test_prerequisite_reinforcement_triggers_when_unmet():
    """Verify that unfulfilled prerequisites (P(L) < 0.50) override level and trigger reinforcement (Fix S4.2)."""
    tracker = MagicMock()
    catalog = {
        "fase0-soc": {
            "kcs": [
                {"kc_id": "kc_target", "prerequisites": ["kc_prereq_1", "kc_prereq_2"]},
            ]
        }
    }

    # Target has P(L) = 0.85 (advanced), but prereq_1 has P(L) = 0.25 (< 0.50)
    def mock_get_state(kc_id):
        if kc_id == "kc_target":
            return BKTState(kc_id=kc_id, p_L=0.85)
        elif kc_id == "kc_prereq_1":
            return BKTState(kc_id=kc_id, p_L=0.25)
        elif kc_id == "kc_prereq_2":
            return BKTState(kc_id=kc_id, p_L=0.90)
        return BKTState(kc_id=kc_id, p_L=0.1)

    tracker.get_state.side_effect = mock_get_state

    mode, meta = determine_pedagogical_context_mode(
        target_kc_id="kc_target",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="fase0-soc",
    )

    assert mode == "prerequisite_reinforcement"
    assert len(meta["unmet_prerequisites"]) == 1
    assert meta["unmet_prerequisites"][0][0] == "kc_prereq_1"
    assert meta["unmet_prerequisites"][0][1] == 0.25

    directive = build_bkt_adaptation_directive(mode, meta)
    assert "REFUERZO DE PRERREQUISITOS FALTANTES" in directive
    assert "kc_prereq_1 (P(L)=0.25)" in directive
    assert "andamiaje conceptual que conecte y refuerce" in directive


def test_offline_knowledge_backend_pure_retrieval():
    """Verify that OfflineKnowledgeBackend retrieves real corpus chunks and formats by role (Fix S4.3)."""
    mock_store = MagicMock()

    # Create mock search results representing pedagogical, formal, and technical sources
    mock_chunks = [
        SearchResult(
            chunk_id="chk_01",
            document_id="doc_01",
            source_id="src_tanenbaum_os_modernos",
            score=0.95,
            snippet="El núcleo del sistema operativo asigna la CPU a través del planificador.",
            content="El núcleo del sistema operativo asigna la CPU a través del planificador.",
            index=0,
            page_start=120,
            page_end=121,
        ),
        SearchResult(
            chunk_id="chk_02",
            document_id="doc_02",
            source_id="src_silberschatz_so",
            score=0.88,
            snippet="Formalmente, el estado de un proceso se modela mediante el autómata de 5 estados.",
            content="Formalmente, el estado de un proceso se modela mediante el autómata de 5 estados.",
            index=1,
            page_start=95,
            page_end=96,
        ),
        SearchResult(
            chunk_id="chk_03",
            document_id="doc_03",
            source_id="src_stallings_os_internals",
            score=0.82,
            snippet="A nivel de hardware, el cambio de contexto guarda los registros en el PCB.",
            content="A nivel de hardware, el cambio de contexto guarda los registros en el PCB.",
            index=2,
            page_start=140,
            page_end=141,
        ),
    ]

    mock_store.search_hybrid.return_value = mock_chunks

    backend = OfflineKnowledgeBackend(knowledge_store=mock_store)
    response_text = backend.generate_response(query="planificación de procesos", notebook_id="fadena-so2")

    # Verificaciones
    assert "### 1. Intuición Conceptual y Analogía" in response_text
    assert "src_tanenbaum_os_modernos" in response_text
    assert "p. 120" in response_text

    assert "### 2. Mecanismo y Formalismo Riguroso" in response_text
    assert "src_silberschatz_so" in response_text
    assert "p. 95" in response_text

    assert "### 3. Nivel de Máquina e Implementación Práctica" in response_text
    assert "src_stallings_os_internals" in response_text
    assert "p. 140" in response_text

    assert "**Desafío Socrático:**" in response_text
    assert "planificación de procesos" in response_text
