"""Regression coverage for F4 adaptive response-format handling."""

from unittest.mock import MagicMock

import pytest

from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.socratic_guard import SocraticGuard
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    extract_requested_structural_components,
    resolve_response_intent,
)


def test_conceptual_question_about_c_code_does_not_request_c_implementation():
    query = "¿Qué es el código en C?"

    intent = resolve_response_intent(query)
    directives = extract_requested_structural_components(
        query, notebook_id="fadena-lenguajes"
    )

    assert intent.code_language is None
    assert intent.output_format is None
    assert "c_code" not in directives


def test_explicit_no_code_overrides_language_mentions_and_test_keywords():
    query = "Explicame qué es código en C, sin código ni tests"

    intent = resolve_response_intent(query)
    directives = extract_requested_structural_components(
        query, notebook_id="fadena-lenguajes"
    )

    assert intent.exclude_code is True
    assert intent.code_language is None
    assert not {"c_code", "python_code", "sql_code", "pytest"} & directives.keys()


def test_explicit_c_implementation_request_keeps_requested_deliverables():
    query = "Implementá un buffer circular con código en C y tests"

    intent = resolve_response_intent(query)
    directives = extract_requested_structural_components(
        query, notebook_id="fadena-lenguajes"
    )

    assert intent.code_language == "c"
    assert directives["c_code"]
    assert directives["pytest"]


def test_pseudocode_directive_uses_supported_text_fence():
    directives = extract_requested_structural_components(
        "Mostrame el pseudocódigo de la búsqueda"
    )

    assert "```text" in directives["pseudocode"]
    assert "```pseudocode" not in directives["pseudocode"]
    assert "pseudocircle" not in directives["pseudocode"]


def test_pseudocode_request_remains_allowed_when_executable_code_is_excluded():
    query = "Mostrame el pseudocódigo, pero sin código ejecutable"

    intent = resolve_response_intent(query)
    directives = extract_requested_structural_components(query)

    assert intent.exclude_code is True
    assert intent.output_format == "pseudocode"
    assert "pseudocode" in directives
    assert not {"c_code", "python_code", "sql_code", "pytest"} & directives.keys()


def test_format_mentions_in_conceptual_questions_do_not_force_deliverables():
    pseudocode_question = "¿Qué significa pseudocódigo?"
    diagram_question = "¿Qué es un diagrama de flujo?"

    assert resolve_response_intent(pseudocode_question).output_format is None
    assert "pseudocode" not in extract_requested_structural_components(pseudocode_question)
    assert resolve_response_intent(diagram_question).output_format is None
    assert "mermaid" not in extract_requested_structural_components(diagram_question)


def test_mermaid_is_injected_only_when_diagram_output_is_requested():
    directives = extract_requested_structural_components(
        "Diseñá el validador e incluí un diagrama de flujo en Mermaid"
    )

    assert "graph TD" in directives["mermaid"]


def test_no_code_contract_cannot_be_overridden_by_guard_pattern():
    guard = SocraticGuard(contract=FASE0_CONTRACT)
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicación conceptual de {concept}.",
        max_tokens=1000,
        code_allowed=False,
    )

    result = guard.validate_token(
        "```c\nint main(void) { return 0; }\n```",
        phase,
        "Explicame qué es código en C, sin código",
        allow_user_override=False,
    )

    assert result.allowed is False
    assert result.blocked_reason == "CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE"


def test_no_code_guard_does_not_block_incidental_py_substrings():
    guard = SocraticGuard(contract=FASE0_CONTRACT)
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicación conceptual de {concept}.",
        max_tokens=1000,
        code_allowed=False,
    )

    result = guard.validate_token(
        "La criptografía estudia mecanismos para proteger información.",
        phase,
        "¿Qué es criptografía?",
        allow_user_override=False,
    )

    assert result.allowed is True


def test_no_code_guard_allows_text_pseudocode_but_rejects_unknown_fence_labels():
    guard = SocraticGuard(contract=FASE0_CONTRACT)
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicación conceptual de {concept}.",
        max_tokens=1000,
        code_allowed=False,
    )

    pseudocode = guard.validate_text(
        "```text\nSI entrada es válida ENTONCES\n    devolver verdadero\n```",
        phase,
        "Mostrame pseudocódigo sin código ejecutable",
        allow_user_override=False,
    )
    guard.reset()
    unknown_label = guard.validate_text(
        "```pseudocircle\nSI entrada es válida ENTONCES\n```",
        phase,
        "Mostrame pseudocódigo sin código ejecutable",
        allow_user_override=False,
    )

    assert pseudocode.allowed is True
    assert unknown_label.allowed is False
    assert unknown_label.blocked_reason == "UNSUPPORTED_CODE_FENCE_LABEL"


def test_no_code_request_removes_generated_code_and_pytest_prompt_directives():
    pipeline = StructuredResponsePipeline(
        contract=FASE0_CONTRACT, llm_backend=MagicMock()
    )
    phase = FASE0_CONTRACT.get_phase("conceptual")
    query = "Explicame qué es código en C, sin código ni tests"

    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query)

    assert "CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO)" not in prompt
    assert "BATERÍA DE PRUEBAS AUTOMATIZADAS CON PYTEST (OBLIGATORIA)" not in prompt


def test_no_code_constraint_wins_over_code_review_prompt_rewrite():
    pipeline = StructuredResponsePipeline(
        contract=FASE0_CONTRACT, llm_backend=MagicMock()
    )
    phase = FASE0_CONTRACT.get_phase("conceptual")

    prompt = pipeline.build_phase_prompt(
        phase=phase,
        user_query="Revisá mi código C y explicá el error sin incluir código",
    )

    assert "DADO QUE EL ESTUDIANTE SOLICITÓ AUDITORÍA" not in prompt
    assert "CÓDIGO C ESTÁNDAR Y DEFENSIVO (OBLIGATORIO)" not in prompt


def test_complete_solution_request_preserves_explicit_no_code_constraint():
    pipeline = StructuredResponsePipeline(
        contract=FASE0_CONTRACT, llm_backend=MagicMock()
    )
    query = "Dame la solución completa, pero sin incluir código"

    prompt = pipeline.build_phase_prompt(
        phase=FASE0_CONTRACT.get_phase("conceptual"),
        user_query=query,
    )
    intent = resolve_response_intent(query)

    assert intent.task == "entregar solución completa solicitada"
    assert intent.exclude_code is True
    assert "PROTOCOLO ANTI-ATAJO ACTIVADO" not in prompt
    assert "El estudiante excluyó el código ejecutable" in prompt


@pytest.mark.anyio
async def test_no_code_stream_blocks_code_even_when_query_mentions_language():
    pipeline = StructuredResponsePipeline(
        contract=FASE0_CONTRACT, llm_backend=MagicMock()
    )

    async def stream_tokens(**_kwargs):
        for token in ("Explicación conceptual. ", "```", "c\n", "int main(void) {}"):
            yield token

    pipeline._stream_tokens = stream_tokens
    events = [
        event
        async for event in pipeline.generate_phased_response(
            user_query="Explicame qué es código en C, sin código",
            requested_phase="conceptual",
        )
    ]

    assert next(e for e in events if e.event_type == "phase_start").payload["code_allowed"] is False
    assert any(e.event_type == "guard_blocked" for e in events)
    emitted = "".join(
        e.payload.get("token", "")
        for e in events
        if e.event_type == "phase_token"
    )
    assert "int main" not in emitted
    assert "```" not in emitted


@pytest.mark.anyio
async def test_explicit_solve_command_still_authorizes_complete_solution():
    pipeline = StructuredResponsePipeline(
        contract=FASE0_CONTRACT, llm_backend=MagicMock()
    )

    async def stream_tokens(**_kwargs):
        yield "Solución completa."

    pipeline._stream_tokens = stream_tokens
    events = [
        event
        async for event in pipeline.generate_phased_response(
            user_query=":solve",
            requested_phase="conceptual",
        )
    ]

    assert next(e for e in events if e.event_type == "phase_start").payload["code_allowed"] is True


@pytest.mark.anyio
async def test_explicit_language_blocks_wrong_fence_and_allows_requested_fence():
    async def run_response(response):
        pipeline = StructuredResponsePipeline(
            contract=FASE0_CONTRACT, llm_backend=MagicMock()
        )

        async def stream_tokens(**_kwargs):
            yield response

        pipeline._stream_tokens = stream_tokens
        return [
            event
            async for event in pipeline.generate_phased_response(
                user_query="Mostrame un ejemplo en C",
                requested_phase="conceptual",
            )
        ]

    wrong_language_events = await run_response("```python\nprint('no')\n```")
    right_language_events = await run_response("```c\nint main(void) { return 0; }\n```")

    assert any(
        event.event_type == "guard_blocked"
        and event.payload["reason"] == "REQUESTED_CODE_LANGUAGE_MISMATCH"
        for event in wrong_language_events
    )
    assert not any(
        "print('no')" in event.payload.get("token", "")
        for event in wrong_language_events
        if event.event_type == "phase_token"
    )
    assert not any(event.event_type == "guard_blocked" for event in right_language_events)
    assert "```c" in "".join(
        event.payload.get("token", "")
        for event in right_language_events
        if event.event_type == "phase_token"
    )
