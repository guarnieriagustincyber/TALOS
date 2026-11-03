"""M1-04b E2E: el pipeline audita y presenta EXACTAMENTE el texto normalizado.

Con un LLM simulado que genera framing de atribución ("las fuentes sí
establecen que...") sobre texto con tag, se verifica que:
  1. El auditor recibe el texto NORMALIZADO (envoltura eliminada).
  2. Lo publicado por SSE (tokens concatenados) == lo auditado (byte-igual).
  3. El evento audit_verdict lleva el conteo de transformaciones.
  4. El texto ORIGINAL nunca se publica en la corriente.
"""

import asyncio

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline

_FRAMING = (
    "Sin embargo, las fuentes sí establecen que un array es una secuencia de "
    "posiciones de la memoria central [E1]."
)
_ORIGINAL_FRAMING = _FRAMING
_NORMALIZED = (
    "Sin embargo, Un array es una secuencia de posiciones de la memoria "
    "central [E1]."
)


class _FakeLLM:
    async def stream(self, **kwargs):
        yield _FRAMING


def _pipeline(token_text: str) -> StructuredResponsePipeline:
    contract = PedagogicalContract(
        notebook_id="test-notebook",
        base_system_prompt="Tutor de prueba con reglas pedagógicas.",
        forbidden_patterns=["<blocked-code>"],
        safe_words=[],
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Explicá {concept}.",
                max_tokens=200,
            )
        ],
    )
    return StructuredResponsePipeline(
        contract=contract, llm_backend=_FakeLLM(), auditor=object()
    )


def _report(kwargs, captured: dict, **overrides) -> ForensicAuditReport:
    captured["generated_text"] = kwargs.get("generated_text")
    fields = {
        "audit_id": "audit-norm-e2e",
        "request_id": kwargs["request_id"],
        "notebook_id": kwargs["notebook_id"],
        "prompt_hash": kwargs["prompt_hash"],
        "overall_verdict": AuditVerdict.APPROVED,
        "audit_latency_ms": 5.0,
        "auditor_backend": "synthetic-auditor",
    }
    fields.update(overrides)
    return ForensicAuditReport(**fields)


def _collect(pipeline: StructuredResponsePipeline, captured: dict) -> list:
    import study_engine.audit.generation_adapter as adapter

    orig = adapter.audit_generation_payload

    def spy(auditor, **kwargs):
        return _report(kwargs, captured, nli_executed=False, nli_calls=0)

    adapter.audit_generation_payload = spy

    try:
        async def run():
            return [
                event
                async for event in pipeline.generate_phased_response(
                    user_query="Explicá el concepto",
                    requested_phase="conceptual",
                )
            ]

        return asyncio.run(run())
    finally:
        adapter.audit_generation_payload = orig


def test_pipeline_audita_y_publica_texto_normalizado():
    captured: dict = {}
    events = _collect(_pipeline(_FRAMING), captured)

    auditor_texto = captured["generated_text"]
    # (1) el auditor recibió el texto normalizado (sin envoltura)
    assert "las fuentes" not in auditor_texto.lower()
    assert "Un array es una secuencia" in auditor_texto

    # (2) publicado por SSE == auditado (byte-igual)
    released = "".join(
        (ev.payload.get("token") or "")
        for ev in events
        if ev.event_type == "phase_token"
    )
    assert released == auditor_texto

    # (3) métrica de transformaciones en el evento audit_verdict
    verdict = next(ev for ev in events if ev.event_type == "audit_verdict")
    assert verdict.payload["metrics"]["text_normalization_transforms"] == 1
    assert verdict.payload["verdict"] == "APPROVED"

    # (4) el texto original con envoltura nunca se publica
    assert "las fuentes" not in released.lower()


def test_pipeline_sin_framing_no_transforma():
    clean = "Un array es una secuencia de posiciones de la memoria central [E1]."

    class _CleanLLM:
        async def stream(self, **kwargs):
            yield clean

    contract = PedagogicalContract(
        notebook_id="test-notebook",
        base_system_prompt="Tutor de prueba con reglas pedagógicas.",
        forbidden_patterns=["<blocked-code>"],
        safe_words=[],
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Explicá {concept}.",
                max_tokens=200,
            )
        ],
    )
    pipeline = StructuredResponsePipeline(
        contract=contract, llm_backend=_CleanLLM(), auditor=object()
    )
    captured: dict = {}
    events = _collect(pipeline, captured)
    auditor_texto = captured["generated_text"]
    assert auditor_texto == clean  # identidad: sin normalización
    verdict = next(ev for ev in events if ev.event_type == "audit_verdict")
    assert verdict.payload["metrics"]["text_normalization_transforms"] == 0
    released = "".join(
        (ev.payload.get("token") or "")
        for ev in events
        if ev.event_type == "phase_token"
    )
    assert released == clean
