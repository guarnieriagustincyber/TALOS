from types import SimpleNamespace

from study_engine.pedagogy.solution_protection import (
    contains_protected_solution,
    is_protected_assessment,
)


def test_only_server_marked_active_assessments_are_protected():
    active = SimpleNamespace(
        metadata={"assessment": {"protected": True, "status": "active"}}
    )
    inactive = SimpleNamespace(
        metadata={"assessment": {"protected": True, "status": "draft"}}
    )
    unprotected = SimpleNamespace(
        metadata={"assessment": {"protected": False, "status": "active"}}
    )
    no_metadata = SimpleNamespace(metadata={})

    assert is_protected_assessment(active)
    assert not is_protected_assessment(inactive)
    assert not is_protected_assessment(unprotected)
    assert not is_protected_assessment(no_metadata)


def test_solution_leak_detector_catches_full_answers_and_verbatim_fragments():
    solution = "struct Queue { Stack* first; Stack* second; }; void enqueue(int value);"

    assert contains_protected_solution(
        "The answer is struct Queue { Stack* first; Stack* second; }; void enqueue(int value);",
        [solution],
    )
    assert contains_protected_solution(
        "Implementás struct Queue { Stack* first; Stack* second; }; and then continue.",
        [solution],
    )


def test_solution_leak_detector_allows_conceptual_guidance_and_short_generic_terms():
    assert not contains_protected_solution(
        "Pensá qué información necesitás conservar entre una operación y la siguiente.",
        ["base + i * sizeof(int)"],
    )
    assert not contains_protected_solution(
        "Usá una estructura para guardar el estado necesario.",
        ["struct Queue"],
    )
    assert contains_protected_solution("B", ["B"])


def test_protected_assessment_instruction_is_added_to_generation_system_prompt():
    import asyncio

    from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
    from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline

    captured = {}

    class Backend:
        async def stream(self, **kwargs):
            yield "Conceptual guidance."

    pipeline = StructuredResponsePipeline(FASE0_CONTRACT, object())

    async def capture_system_prompt(**kwargs):
        captured.update(kwargs)
        yield "Conceptual guidance."

    pipeline._stream_tokens = capture_system_prompt

    async def collect():
        return [
            event
            async for event in pipeline.generate_phased_response(
                user_query="Dame una pista conceptual.",
                requested_phase="conceptual",
                protected_assessment=True,
            )
        ]

    events = asyncio.run(collect())
    assert "EVALUACIÓN ACTIVA PROTEGIDA" in captured["system_prompt"]
    assert any(event.event_type == "phase_complete" for event in events)
