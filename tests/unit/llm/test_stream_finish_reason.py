"""COMMIT 5 feat(stream): finish_reason observable al cierre.

- Gemini captura finish_reason de cada chunk SSE.
- CircuitBreakerBackend.stream lo propaga del backend usado.
- El pipeline loguea el finish_reason y emite evento "truncated" si es
  "length" (corte por max_tokens), sin cambiar timeouts ni max_tokens.
"""

import asyncio
from unittest.mock import MagicMock

from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.llm.circuit_breaker import CircuitBreakerBackend
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


class _StreamingBackendWithFinish:
    """Backend fake que streamea 2 tokens y fija finish_reason al cerrar (como Gemini)."""

    def __init__(self, finish_reason):
        self._finish = finish_reason
        self._last_finish_reason = None

    async def stream(self, **kwargs):
        yield "palabra-uno "
        yield "palabra-dos"
        self._last_finish_reason = self._finish


def _mk_backend(finish):
    return _StreamingBackendWithFinish(finish)


def _collect_events(pipeline, **kwargs):
    async def _run():
        return [ev async for ev in pipeline.generate_phased_response(**kwargs)]
    return asyncio.run(_run())


def _pipeline_with(backend):
    contract = PedagogicalContract(
        contract_id="c1",
        notebook_id="nb1",
        version="1",
        authoritative_sources=(),
        domain_scope=(),
        base_system_prompt="Sistema tutelar TALOS para pruebas de streaming.",
        response_phases=[
            ResponsePhase(phase_id="conceptual", max_tokens=50, phase_prompt_template="Q: {concept}"),
        ],
    )
    return StructuredResponsePipeline(contract=contract, llm_backend=backend, auditor=None)


def test_cb_stream_propaga_finish_reason_del_backend():
    primary = _mk_backend("length")
    cb = CircuitBreakerBackend(primary, _mk_backend("stop"))
    asyncio.run(_collect_tokens(cb))
    assert cb._last_finish_reason == "length"


def _collect_tokens(cb):
    async def _run():
        return [t async for t in cb.stream(system_prompt="s", user_prompt="u", max_tokens=10)]
    return _run()


def test_pipeline_emite_truncated_cuando_finish_reason_es_length():
    backend = _mk_backend("length")
    pipeline = _pipeline_with(backend)
    events = _collect_events(
        pipeline,
        user_query="describí listas",
        context_pack=None,
        requested_phase="conceptual",
    )
    kinds = [e.event_type for e in events]
    assert "truncated" in kinds


def test_pipeline_no_emite_truncated_con_stop():
    backend = _mk_backend("stop")
    pipeline = _pipeline_with(backend)
    events = _collect_events(
        pipeline,
        user_query="describí listas",
        context_pack=None,
        requested_phase="conceptual",
    )
    kinds = [e.event_type for e in events]
    assert "truncated" not in kinds
    assert "phase_complete" in kinds
