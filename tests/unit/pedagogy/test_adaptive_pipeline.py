"""Unit tests for FASE S4: Adaptive Pipeline and Pedagogical Intent Routing."""

from unittest.mock import MagicMock
import pytest

from study_engine.pedagogy.structured_pipeline import (
    RESPONSE_MODES,
    classify_pedagogical_intent,
    resolve_response_intent,
    build_mode_specific_instruction,
    StructuredResponsePipeline,
)
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.student_context import (
    determine_pedagogical_context_mode,
    build_bkt_adaptation_directive,
)
from study_engine.llm.backends import ProviderCompletion
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


@pytest.mark.parametrize(
    ("query", "expected_mode"),
    [
        ("En una frase, ¿qué es un proceso?", "quick_answer"),
        ("Resumí todo lo aprendido en 5 líneas.", "quick_answer"),
        ("No lo resumas; explicá el mecanismo paso a paso.", "deep_dive"),
        ("Explicá en profundidad cómo funciona la planificación.", "deep_dive"),
        ("Mostrame un ejemplo en C de cómo se crea un proceso.", "give_example"),
        ("Sí, hagamos el ejercicio.", "explain_concept"),
        ("¿Qué es un proceso?", "explain_concept"),
    ],
)
def test_response_intent_selects_task_without_losing_explicit_constraints(query, expected_mode):
    intent = resolve_response_intent(query)
    assert intent.mode == expected_mode


def test_response_intent_preserves_explicit_length_and_suppresses_forced_follow_up():
    intent = resolve_response_intent("Resumí todo lo aprendido sobre procesos en 5 líneas.")

    assert intent.task == "sintetizar o responder brevemente"
    assert intent.max_lines == 5
    assert intent.max_sentences is None
    assert intent.exclude_follow_up is True

    instruction = intent.to_prompt_instruction()
    assert "no excedas 5 línea(s)" in instruction
    assert "No agregues una pregunta, ejercicio ni oferta de continuación" in instruction
    assert "Conservá exactitud técnica" in instruction


def test_response_intent_does_not_treat_negated_summary_as_synthesis():
    intent = resolve_response_intent("No lo resumas; explicá el mecanismo paso a paso.")
    another_negation = resolve_response_intent("No quiero un resumen; desarrollá la explicación.")

    assert intent.mode == "deep_dive"
    assert intent.depth == "deep"
    assert intent.max_lines is None
    assert "mecanismo paso a paso" in intent.include
    assert another_negation.mode == "explain_concept"


def test_deep_request_respects_explicit_five_line_limit():
    intent = resolve_response_intent("Explicá en profundidad el context switch en 5 líneas.")

    assert intent.mode == "deep_dive"
    assert intent.depth == "deep"
    assert intent.max_lines == 5
    assert intent.exclude_follow_up is True
    assert "no excedas 5 línea(s)" in intent.to_prompt_instruction()


def test_response_intent_keeps_requested_code_and_respects_code_exclusion():
    requested = resolve_response_intent("¿Me podés mostrar un ejemplo en C?")
    excluded = resolve_response_intent("Explicame fork() sin código.")

    assert requested.mode == "give_example"
    assert requested.code_language == "c"
    assert requested.exclude_code is False
    assert "podés incluir el bloque de código necesario" in requested.to_prompt_instruction()
    assert excluded.exclude_code is True


def test_response_intent_recognizes_exercise_acceptance():
    intent = resolve_response_intent("Sí, hagamos el ejercicio.")

    assert intent.task == "proponer o continuar un ejercicio guiado"
    assert "Conservá el tema del historial reciente" in intent.to_prompt_instruction()
    assert "esperá el intento sin revelar la solución completa" in intent.to_prompt_instruction()


@pytest.mark.parametrize(
    ("query", "expected_task"),
    [
        ("¿Qué es un proceso?", "responder la consulta"),
        ("Explicá en profundidad cómo se planifica un proceso.", "explicar en profundidad"),
        ("Resumí los estados de un proceso en 3 líneas.", "sintetizar o responder brevemente"),
        ("DAME LA SOLUCIÓN COMPLETA del ejercicio.", "entregar solución completa solicitada"),
        ("Pasame la solución completa del ejercicio.", "entregar solución completa solicitada"),
        ("Dame el código completo terminado del ejercicio.", "entregar solución completa solicitada"),
        ("Revisá mi respuesta: un proceso es un programa en ejecución.", "revisar un intento o corregir una respuesta"),
        ("No entendí cómo decide el scheduler; explicámelo de otra manera.", "reexplicar con otro enfoque"),
        ("¿Qué tema conviene estudiar ahora a partir de esto?", "recomendar el siguiente paso"),
        ("Armemos un laboratorio conceptual de DNS.", "diseñar un laboratorio conceptual"),
    ],
)
def test_response_intent_resolves_distinct_pedagogical_tasks(query, expected_task):
    assert resolve_response_intent(query).task == expected_task


@pytest.mark.parametrize(
    "attempt",
    [
        "Un proceso es un programa en ejecución.",
        "Un proceso tiene recursos propios, aunque varios procesos pueden compartir archivos.",
        "Un proceso y un programa son lo mismo.",
        "",
    ],
)
def test_feedback_strategy_uses_available_attempt_and_asks_when_missing(attempt):
    contract = PedagogicalContract(
        contract_id="contract_feedback_strategy_test",
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
    with_attempt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Revisá mi respuesta.",
        recent_turns=[{"role": "user", "content": attempt}],
    )
    without_attempt = pipeline.build_phase_prompt(phase=phase, user_query="Revisá mi intento.")

    assert "Usá solo el intento disponible" in with_attempt
    assert "el primer error concreto" in with_attempt
    assert "No inventes un intento" in without_attempt
    assert "pedile que comparta su respuesta" in without_attempt
    if attempt:
        assert attempt in with_attempt


@pytest.mark.parametrize(
    ("query", "expected_instruction"),
    [
        ("¿Qué es un proceso en sistemas operativos?", "Contestá primero la pregunta"),
        ("Explicá en profundidad el aislamiento de procesos.", "Desarrollá capas pertinentes"),
        ("Resumí el aislamiento de procesos en 3 líneas.", "Conservá el hecho central"),
        ("Sí, hagamos el ejercicio.", "Proponé una consigna clara"),
        ("DAME LA SOLUCIÓN COMPLETA del ejercicio.", "Entregá la solución completa solicitada"),
        ("Pasame la solución completa del ejercicio.", "Entregá la solución completa solicitada"),
        ("Dame el código completo terminado del ejercicio.", "Entregá la solución completa solicitada"),
        ("No entendí cómo decide el scheduler; explicámelo de otra manera.", "cambiá realmente"),
        ("¿Qué tema conviene estudiar ahora a partir de esto?", "No afirmes dominio"),
        ("Armemos un laboratorio conceptual de DNS.", "No ejecutes acciones reales"),
    ],
)
def test_assembled_prompt_includes_task_specific_adaptive_strategy(query, expected_instruction):
    contract = PedagogicalContract(
        contract_id="contract_mode_strategy_test",
        notebook_id="fase0-soc",
        version="1.0.0",
        authoritative_sources=("src_test",),
        domain_scope=("test",),
        base_system_prompt="Tutor TALOS.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                max_tokens=400,
                phase_prompt_template="Explica: {concept}\nCerrá con una pregunta socrática.",
            ),
        ],
    )
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=MagicMock())
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query=query,
    )

    assert "ESTRATEGIA PEDAGÓGICA PARA ESTA TAREA" in prompt
    assert expected_instruction in prompt
    assert prompt.rfind("ESTRATEGIA PEDAGÓGICA PARA ESTA TAREA") > prompt.rfind(
        "Cerrá con una pregunta socrática"
    )


def test_explicit_complete_solution_is_not_replaced_by_anti_shortcut_policy():
    contract = PedagogicalContract(
        contract_id="contract_explicit_solution_test",
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
    for query in (
        "DAME LA SOLUCIÓN COMPLETA del ejercicio.",
        "Pasame la solución completa del ejercicio.",
        "Dame el código completo terminado del ejercicio.",
    ):
        prompt = pipeline.build_phase_prompt(
            phase=contract.get_phase("conceptual"),
            user_query=query,
        )

        assert "SOLUCIÓN COMPLETA SOLICITADA" in prompt
        assert "PROTOCOLO ANTI-ATAJO ACTIVADO" not in prompt
        assert "No reveles la solución completa" not in prompt


def test_generation_sends_adaptive_task_policy_to_mocked_backend():
    import asyncio

    async def _run():
        class PromptCaptureBackend:
            def __init__(self):
                self.prompt_bundles = []

            def complete(self, prompt_bundle):
                self.prompt_bundles.append(prompt_bundle)
                return ProviderCompletion(
                    text="Respuesta determinista.",
                    latency_ms=1.0,
                    model="prompt-capture",
                )

        contract = PedagogicalContract(
            contract_id="contract_task_strategy_generation_test",
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
        backend = PromptCaptureBackend()
        pipeline = StructuredResponsePipeline(contract=contract, llm_backend=backend)

        cases = (
            (
                "DAME LA SOLUCIÓN COMPLETA del ejercicio.",
                [],
                "SOLUCIÓN COMPLETA SOLICITADA",
            ),
            (
                "Revisá mi respuesta.",
                [{"role": "user", "content": "Un proceso es un programa en ejecución."}],
                "revisar un intento o corregir una respuesta",
            ),
            (
                "¿Qué tema conviene estudiar ahora?",
                [{"role": "assistant", "content": "Estuvimos repasando procesos e hilos."}],
                "No afirmes dominio",
            ),
            (
                "¿Qué tema me recomendás estudiar ahora?",
                [],
                "pedí una aclaración breve",
            ),
        )
        for query, recent_turns, expected_prompt_text in cases:
            events = [
                event
                async for event in pipeline.generate_phased_response(
                    user_query=query,
                    requested_phase="conceptual",
                    recent_turns=recent_turns,
                )
            ]
            assert any(event.event_type == "phase_complete" for event in events)

            user_prompt = backend.prompt_bundles[-1].messages[0].content
            assert expected_prompt_text in user_prompt
            if "SOLUCIÓN COMPLETA" in query:
                phase_start = next(event for event in events if event.event_type == "phase_start")
                assert phase_start.payload["code_allowed"] is True
                assert "PROTOCOLO ANTI-ATAJO ACTIVADO" not in user_prompt

    asyncio.run(_run())


@pytest.mark.parametrize(
    "query",
    [
        "¿Qué es una dirección IPv4?",
        "¿Qué es un proceso?",
        "Explicá el contexto histórico de Heartbleed.",
        "¿Qué condiciones hicieron posible CVE-2021-29921?",
        "Explicá por qué una analogía de direcciones puede ser limitada.",
    ],
)
def test_prompt_adds_contextual_rigor_without_inventing_sources_or_security_links(query):
    contract = PedagogicalContract(
        contract_id="contract_contextual_rigor_test",
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
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query=query,
    )

    assert "CONTEXTO Y ALCANCE DE AFIRMACIONES TÉCNICAS" in prompt
    assert "No supongas sistema operativo, arquitectura, ABI, compilador, versión ni configuración" in prompt
    assert "No inventes citas, versiones ni fuentes consultadas" in prompt
    assert "No fuerces una conexión con ciberseguridad" in prompt
    assert "Explicá el límite de la analogía" in prompt
    assert "No presentes un CVE o caso histórico como universal" in prompt


def test_known_environment_is_preserved_and_not_overridden_by_default_assumptions():
    from study_engine.web.routes.chat import EpistemicContextPack

    contract = PedagogicalContract(
        contract_id="contract_known_environment_test",
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
    context_pack = EpistemicContextPack(
        formatted_context="[E1] El ejemplo de esta consulta usa Linux x86-64.",
        citations=[],
        chunks=[],
    )
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=MagicMock())
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query="¿Qué hace este syscall?",
        context_pack=context_pack,
    )

    assert "[E1] El ejemplo de esta consulta usa Linux x86-64." in prompt
    assert "Si el contexto sí especifica el entorno, circunscribí la afirmación a ese entorno" in prompt
    assert "No supongas sistema operativo, arquitectura, ABI, compilador, versión ni configuración" in prompt


def test_generic_ipv4_explanation_does_not_force_an_unverified_cve_mapping():
    contract = PedagogicalContract(
        contract_id="contract_unverified_historical_case_test",
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
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query="¿Qué es una dirección IPv4?",
    )

    assert "CVE-2021-29921" not in prompt
    assert "ANCLAJE A THREAT INTEL" not in prompt
    assert "No presentes un CVE o caso histórico como universal" in prompt


def test_concept_strategy_is_not_programming_specific_or_forced_to_use_analogies():
    contract = PedagogicalContract(
        contract_id="contract_cross_subject_strategy_test",
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

    for query in ("¿Qué es un proceso?", "¿Qué es DNS?"):
        prompt = pipeline.build_phase_prompt(
            phase=contract.get_phase("conceptual"),
            user_query=query,
        )
        strategy = prompt.rsplit("ESTRATEGIA PEDAGÓGICA PARA ESTA TAREA", 1)[1]
        assert "analogía solo si aporta" in strategy
        assert "no fuerces python" in strategy.lower()


def test_response_intent_suppresses_socratic_close_when_requested():
    intent = resolve_response_intent("Definilo en una frase y no hagas una pregunta.")

    assert intent.max_sentences == 1
    assert intent.exclude_follow_up is True


def test_response_intent_preserves_explicit_table_format():
    intent = resolve_response_intent("Compará procesos e hilos en una tabla.")

    assert intent.mode == "compare"
    assert intent.output_format == "table"
    assert "Formato solicitado: table" in intent.to_prompt_instruction()


def test_response_contract_is_appended_after_conflicting_phase_instructions():
    contract = PedagogicalContract(
        contract_id="contract_response_intent_test",
        notebook_id="fase0-soc",
        version="1.0.0",
        authoritative_sources=("src_test",),
        domain_scope=("test",),
        base_system_prompt="Tutor TALOS.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                max_tokens=400,
                phase_prompt_template="Explica: {concept}\nCerrá con una pregunta socrática.",
            ),
        ],
    )
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=MagicMock())
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query="En una frase, ¿qué es un proceso?",
    )

    assert prompt.index("Cerrá con una pregunta socrática") < prompt.index("CONTRATO RESUELTO PARA ESTE TURNO")
    contract_block = prompt.split("=== CONTRATO RESUELTO PARA ESTE TURNO ===", 1)[1]
    assert "no excedas 1 frase(s)" in contract_block
    assert "No agregues una pregunta" in contract_block


def test_exercise_acceptance_uses_recent_topic_and_does_not_reveal_solution():
    contract = PedagogicalContract(
        contract_id="contract_exercise_continuation_test",
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
    prompt = pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query="Sí, hagamos el ejercicio.",
        recent_turns=[{"role": "assistant", "content": "¿Querés practicar qué es un proceso?"}],
    )

    assert "EJERCICIO GUIADO" in prompt
    assert "mantener el mismo tema" in prompt
    assert "No reveles la solución completa salvo que la solicite" in prompt
    assert "¿Querés practicar qué es un proceso?" in prompt


def test_build_phase_prompt_respects_explicit_code_and_no_code_requests():
    contract = PedagogicalContract(
        contract_id="contract_code_constraints_test",
        notebook_id="fadena-so2",
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

    code_prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="¿Me podés mostrar un ejemplo en C de cómo se crea un proceso?",
    )
    no_code_prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Explicame fork() sin código.",
    )

    assert "CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO)" in code_prompt
    assert "PROTOCOLO ANTI-ATAJO ACTIVADO" not in code_prompt
    assert "El estudiante pidió explícitamente un ejemplo en c" in code_prompt
    assert "CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO)" not in no_code_prompt
    assert "El estudiante excluyó el código ejecutable" in no_code_prompt


def test_generation_phase_code_permission_obeys_explicit_request_constraints():
    async def _run():
        contract = PedagogicalContract(
            contract_id="contract_code_permission_test",
            notebook_id="fadena-so2",
            version="1.0.0",
            authoritative_sources=("src_test",),
            domain_scope=("test",),
            base_system_prompt="Tutor TALOS.",
            response_phases=[
                ResponsePhase(
                    phase_id="conceptual",
                    max_tokens=400,
                    phase_prompt_template="Explica: {concept}",
                    code_allowed=True,
                ),
            ],
        )
        class PromptCaptureBackend:
            def __init__(self):
                self.prompt_bundles = []

            def complete(self, prompt_bundle):
                self.prompt_bundles.append(prompt_bundle)
                return ProviderCompletion(
                    text="Respuesta de prueba.",
                    latency_ms=1.0,
                    model="prompt-capture",
                )

        backend = PromptCaptureBackend()
        pipeline = StructuredResponsePipeline(contract=contract, llm_backend=backend)
        cases = (
            ("¿Me podés mostrar un ejemplo en C?", True),
            ("Explicame fork() sin código.", False),
        )
        for index, (query, expected_code_permission) in enumerate(cases):
            events = [
                event
                async for event in pipeline.generate_phased_response(
                    user_query=query,
                    requested_phase="conceptual",
                )
            ]
            phase_start = next(event for event in events if event.event_type == "phase_start")
            assert phase_start.payload["code_allowed"] is expected_code_permission
            system_prompt = backend.prompt_bundles[index].system_prompt
            assert "CONTRATO RESUELTO PARA ESTE TURNO" in system_prompt
            if not expected_code_permission:
                assert "El estudiante excluyó el código ejecutable" in system_prompt
            else:
                assert "El estudiante pidió explícitamente un ejemplo en c" in system_prompt

    import asyncio

    asyncio.run(_run())


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

    # Code review is contextual and does not force unrelated CVEs or implementation details.
    prompt_audit = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Auditar la siguiente solución en Python para validar IPv4",
        pedagogical_mode="evaluate_code",
    )
    assert "REVISIÓN DE CÓDIGO Y ANÁLISIS TÉCNICO" in prompt_audit
    assert "No inventes vulnerabilidades, impacto de seguridad, arquitectura ni CVE" in prompt_audit
    assert "CVE-2021-29921" not in prompt_audit
    assert "No supongas sistema operativo, arquitectura, ABI, compilador, versión ni configuración" in prompt_audit

    # Misconception repair is context-specific instead of hard-coding one unrelated example.
    prompt_misconception = pipeline.build_phase_prompt(
        phase=phase,
        user_query="No entiendo por qué 010.0.0.1 es un error si en matemáticas 010 es 10",
        pedagogical_mode="resolve_misconception",
    )
    assert "REPARACIÓN DE CONCEPTO" in prompt_misconception
    assert "resolver una concepción errónea" in prompt_misconception
    assert "dónde deja de aplicar" in prompt_misconception


def test_basic_explain_concept_uses_introductory_output_rules():
    contract = PedagogicalContract(
        contract_id="contract_basic_test",
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

    basic_prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="¿Qué es un proceso en sistemas operativos?",
        pedagogical_mode="explain_concept",
        context_mode="basic",
    )
    assert "FORMATO INTRODUCTORIO DE RESPUESTA" in basic_prompt
    assert "Máximo 300 palabras" in basic_prompt
    assert "pregunta de comprensión básica" in basic_prompt
    assert "Nivel máquina" not in basic_prompt
    assert "diagramas limpios" not in basic_prompt

    intermediate_prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="¿Qué es un proceso en sistemas operativos?",
        pedagogical_mode="explain_concept",
        context_mode="intermediate",
    )
    assert "Nivel máquina" in intermediate_prompt


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
            return BKTState(kc_id=kc_id, p_L=0.25, attempts=2)
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
    authorized_source_ids = {
        "src_tanenbaum_os_modernos",
        "src_silberschatz_so",
        "src_stallings_os_internals",
    }
    mock_conn = MagicMock()
    mock_conn.cursor.return_value.fetchall.return_value = [
        (source_id,) for source_id in sorted(authorized_source_ids)
    ]
    mock_store.engine.db_path = ":memory:"
    mock_store.engine.transaction.return_value.__enter__.return_value = mock_conn

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

    def search_authorized_chunks(
        query,
        *,
        notebook_id,
        limit,
        source_ids,
    ):
        assert notebook_id == "fadena-so2"
        assert limit == 5
        assert set(source_ids) == authorized_source_ids
        return [
            chunk for chunk in mock_chunks if chunk.source_id in source_ids
        ][:limit]

    mock_store.search_hybrid.side_effect = search_authorized_chunks

    backend = OfflineKnowledgeBackend(knowledge_store=mock_store)
    response_text = backend.generate_response(query="planificación de procesos", notebook_id="fadena-so2")

    mock_store.search_hybrid.assert_called_once()
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
