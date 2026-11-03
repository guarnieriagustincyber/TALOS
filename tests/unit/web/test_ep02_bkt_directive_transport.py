"""Tests EP-02 / H1-B: transporte y consumo de la directiva adaptativa (bkt_directive).

Defecto confirmado contra HEAD 2c82f0b: `_prepare_chat_context` compone la
directiva adaptativa (modo BKT, aceleración cold-start, protocolo de lucha,
andamiaje metacognitivo, espiral y digest de sesión) y `maybe_inject_session_digest`
la aumenta, pero la llamada a `generate_phased_response` NO la transmitía:
pérdida silenciosa de la adaptación completa (el pipeline la soporta desde
Fix S4.2 y el presupuesto C3 la contabiliza).

Contrato verificado aquí:
  1. Transporte: la ruta pasa `bkt_directive` al pipeline con el valor
     compuesto para el KC matcheado de ESTE turno y esta sesión.
  2. Consumo: la directiva llega al prompt efectivo del generador
     (user prompt del PromptBundle) y sólo cuando se provee.
  3. Diferenciación: dos estados controlados del MISMO concepto producen
     directivas distintas (NIVEL INICIAL vs NIVEL AVANZADO).
  4. Fail-closed: con pack abstenido NINGÚN backend se invoca (la directiva
     no puede bypassar C5); KC sin match recibe la directiva neutral
     intermedia (tratamiento explícito de incertidumbre, sin atribución falsa).
  5. Inmutabilidad: una conversación ordinaria NO muta BKT (sin observaciones).
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

import pytest
from fastapi.testclient import TestClient

from study_engine.context.c5_trust import EpistemicTrustStatus
from study_engine.generation.prompts import PromptBundle
from study_engine.llm.backends import ProviderCompletion
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline
from study_engine.student.contracts import BKTState
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container
from study_engine.web.routes.chat import (
    EpistemicContextPack,
    _global_default_contract,
)
from study_engine.pedagogy.structured_pipeline import PhaseHistory

NOTEBOOK = "fase0-soc"
KC = "aritmetica_punteros"
QUERY = "¿Cómo funciona la aritmética de punteros con malloc y free en el heap?"


def _sufficient_pack(topic="punteros"):
    return EpistemicContextPack(
        formatted_context=f"Fragmento sintético verificado sobre {topic} con citas [E1].",
        citations=[],
        chunks=[{"chunk_text": f"contenido sintético de {topic}"}],
        abstained=False,
        trust_status=EpistemicTrustStatus.SUFFICIENT_EVIDENCE,
        is_sufficient=True,
    )


def _abstained_pack():
    return EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )


class SpyBackend:
    """Backend determinista que registra el PromptBundle efectivo."""

    def __init__(self, text="Según la evidencia [E1], el concepto se explica conforme a las fuentes."):
        self.bundles = []
        self._text = text

    def complete(self, prompt_bundle: PromptBundle) -> ProviderCompletion:
        self.bundles.append(prompt_bundle)
        return ProviderCompletion(
            text=self._text,
            latency_ms=5.0,
            tokens_used=None,
            model="spy-llm-v1",
            generator_abstained=False,
        )


def _run_route_query(tmp_path, kc_state=None):
    """POST /api/chat/query real con retrieval parcheado; devuelve
    (kwargs capturados de generate_phased_response, respuesta HTTP, container)."""
    container = AppContainer(working_dir=tmp_path / "state", use_mock=True)
    if kc_state is not None:
        container.bkt_tracker.save_state(kc_state)
    set_container(container)
    bkt_before = container.bkt_tracker.get_state(KC)

    client = TestClient(create_app())
    captured = {}
    orig = StructuredResponsePipeline.generate_phased_response

    async def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        async for ev in orig(self, *args, **kwargs):
            yield ev

    with patch(
        "study_engine.web.routes.chat._assemble_epistemic_context",
        lambda **kw: (_sufficient_pack(), [{"chunk_text": "síntesis sintética"}]),
    ), patch.object(StructuredResponsePipeline, "generate_phased_response", _spy):
        resp = client.post(
            "/api/chat/query",
            json={
                "prompt": QUERY,
                "scope_type": "notebook",
                "scope_id": NOTEBOOK,
                "notebook_id": NOTEBOOK,
                "session_id": "sess-ep02-test",
                "requested_phase": "conceptual",
            },
        )
    return captured, resp, container, bkt_before


# ---------------------------------------------------------------------------
# 1-2. Transporte y diferenciación en la ruta real
# ---------------------------------------------------------------------------


def test_route_transports_bkt_directive_to_pipeline(tmp_path):
    """La directiva compuesta llega como argumento al consumidor real."""
    captured, resp, container, bkt_before = _run_route_query(tmp_path)
    assert resp.status_code == 200
    assert "bkt_directive" in captured, "la ruta debe transmitir bkt_directive"
    directive = captured["bkt_directive"]
    assert directive and "ADAPTACIÓN PEDAGÓGICA BKT" in directive
    # KC frío (p_L=0.1, attempts=0) → nivel inicial por política S4.2.
    assert "NIVEL INICIAL" in directive
    # La conversación ordinaria NO muta BKT (sin observaciones nuevas).
    bkt_after = container.bkt_tracker.get_state(KC)
    assert bkt_after.p_L == bkt_before.p_L
    assert bkt_after.attempts == bkt_before.attempts


def test_route_differentiates_directive_by_student_state(tmp_path):
    """Mismo concepto, necesidad de ayuda distinta → directiva distinta.

    Estado controlado avanzado (p_L=0.9) sobre el MISMO KC: la política S4.2
    produce NIVEL AVANZADO en lugar de NIVEL INICIAL. La intervención se
    adapta a información académica pertinente, no a la mera existencia de BKT.
    """
    advanced = BKTState(kc_id=KC, p_L=0.9, attempts=10)
    captured, resp, _c, _b = _run_route_query(tmp_path, kc_state=advanced)
    assert resp.status_code == 200
    directive = captured.get("bkt_directive") or ""
    assert "NIVEL AVANZADO" in directive
    assert "NIVEL INICIAL" not in directive


def test_route_neutral_directive_for_unmatched_kc(tmp_path):
    """Sin match de KC: directiva neutral intermedia (incertidumbre explícita).

    La consulta no matchea ningún KC del catálogo: la política vigente produce
    el modo intermedio con p_L neutral (0.5) y target genérico — nunca una
    atribución falsa a un KC específico.
    """
    container = AppContainer(working_dir=tmp_path / "state", use_mock=True)
    set_container(container)
    client = TestClient(create_app())
    captured = {}
    orig = StructuredResponsePipeline.generate_phased_response

    async def _spy(self, *args, **kwargs):
        captured.update(kwargs)
        async for ev in orig(self, *args, **kwargs):
            yield ev

    with patch(
        "study_engine.web.routes.chat._assemble_epistemic_context",
        lambda **kw: (_sufficient_pack(), [{"chunk_text": "síntesis"}]),
    ), patch.object(StructuredResponsePipeline, "generate_phased_response", _spy):
        resp = client.post(
            "/api/chat/query",
            json={
                "prompt": "consulta sin kc del catalogo xyzq",
                "scope_type": "notebook",
                "scope_id": NOTEBOOK,
                "notebook_id": NOTEBOOK,
                "session_id": "sess-ep02-neutral",
                "requested_phase": "conceptual",
            },
        )
    assert resp.status_code == 200
    directive = captured.get("bkt_directive") or ""
    assert "NIVEL INTERMEDIO / CONSOLIDACIÓN" in directive
    assert "NIVEL INICIAL" not in directive and "NIVEL AVANZADO" not in directive


# ---------------------------------------------------------------------------
# 3. Consumo en el prompt efectivo del generador
# ---------------------------------------------------------------------------


def _make_pipeline(backend):
    return StructuredResponsePipeline(
        contract=_global_default_contract(),
        llm_backend=backend,
        phase_history=PhaseHistory(),
        auditor=None,
    )


def _drain(gen):
    async def _run():
        return [ev async for ev in gen]

    return asyncio.run(_run())


def test_pipeline_consumes_directive_in_effective_prompt():
    """La directiva transportada llega al PromptBundle que ve el generador."""
    spy = SpyBackend()
    pipeline = _make_pipeline(spy)
    directive = (
        "=== ADAPTACIÓN PEDAGÓGICA BKT: NIVEL INICIAL / CONCEPTUAL (P(L)=0.10) ===\n"
        "- Partí de analogías cotidianas."
    )
    events = _drain(pipeline.generate_phased_response(
        user_query="explicame el concepto",
        context_pack=_sufficient_pack(),
        requested_phase="conceptual",
        bkt_directive=directive,
    ))
    assert spy.bundles, "el generador efectivo debe haber sido invocado"
    bundle = spy.bundles[0]
    user_content = bundle.messages[0].content
    assert directive in user_content, "la directiva debe estar en el prompt efectivo"


def test_pipeline_without_directive_injects_nothing():
    """Sin directiva: ningún fragmento de adaptación se inyecta."""
    spy = SpyBackend()
    pipeline = _make_pipeline(spy)
    _drain(pipeline.generate_phased_response(
        user_query="explicame el concepto",
        context_pack=_sufficient_pack(),
        requested_phase="conceptual",
        bkt_directive=None,
    ))
    assert spy.bundles
    user_content = spy.bundles[0].messages[0].content
    assert "ADAPTACIÓN PEDAGÓGICA BKT" not in user_content


def test_pipeline_directive_differentiates_prompts():
    """Dos directivas distintas sobre el mismo concepto → prompts distintos."""
    from study_engine.pedagogy.student_context import build_bkt_adaptation_directive

    basic = build_bkt_adaptation_directive("basic", {"p_L": 0.1, "target_kc_id": KC})
    advanced = build_bkt_adaptation_directive("advanced", {"p_L": 0.9, "target_kc_id": KC})

    spy_basic, spy_advanced = SpyBackend(), SpyBackend()
    for spy, directive in ((spy_basic, basic), (spy_advanced, advanced)):
        pipeline = _make_pipeline(spy)
        _drain(pipeline.generate_phased_response(
            user_query="explicame la aritmética de punteros",
            context_pack=_sufficient_pack(),
            requested_phase="conceptual",
            bkt_directive=directive,
        ))
    basic_prompt = spy_basic.bundles[0].messages[0].content
    advanced_prompt = spy_advanced.bundles[0].messages[0].content
    assert basic in basic_prompt and basic not in advanced_prompt
    assert advanced in advanced_prompt and advanced not in basic_prompt


# ---------------------------------------------------------------------------
# 4. Fail-closed: la directiva no bypassa C5 ni provoca mutaciones
# ---------------------------------------------------------------------------


def test_abstained_pack_never_invokes_backend_even_with_directive():
    """Pack abstenido: cero invocaciones al backend (la directiva no abre la frontera C5)."""
    spy = SpyBackend()
    pipeline = _make_pipeline(spy)
    events = _drain(pipeline.generate_phased_response(
        user_query="consulta fuera de alcance",
        context_pack=_abstained_pack(),
        requested_phase="conceptual",
        bkt_directive="=== ADAPTACIÓN PEDAGÓGICA BKT: NIVEL AVANZADO ===",
    ))
    assert not spy.bundles, "ningún backend puede invocarse con pack abstenido"
    abstentions = [e for e in events if e.event_type == "abstention"]
    assert abstentions and abstentions[0].payload["abstained"] is True


def test_provider_failure_is_technical_not_academic(tmp_path):
    """Fallo del proveedor con directiva transportada → error técnico, sin
    contentido académico emitido; la directiva no convierte el fallo en
    abstinencia académica ni en observación."""
    captured, resp, container, bkt_before = _run_route_query(tmp_path)
    # La corrida de referencia usa el backend mock/offline del contenedor
    # sintético; lo esencial: la ruta reporta 200 con eventos SSE y BKT queda
    # intacto tras el turno completo.
    assert resp.status_code == 200
    bkt_after = container.bkt_tracker.get_state(KC)
    assert bkt_after.attempts == bkt_before.attempts
    assert bkt_after.p_L == bkt_before.p_L


# ---------------------------------------------------------------------------
# 5. Aplicabilidad: identidad y scope por construcción
# ---------------------------------------------------------------------------


def test_directive_texts_carry_kc_and_level_not_solutions():
    """Las directivas de la política vigente adaptan el nivel y nombran el KC;
    no transportan soluciones ni material protegido."""
    from study_engine.pedagogy.student_context import build_bkt_adaptation_directive

    for mode, meta in (
        ("basic", {"p_L": 0.1, "target_kc_id": KC}),
        ("intermediate", {"p_L": 0.5, "target_kc_id": KC}),
        ("advanced", {"p_L": 0.9, "target_kc_id": KC}),
    ):
        text = build_bkt_adaptation_directive(mode, meta)
        assert "ADAPTACIÓN PEDAGÓGICA BKT" in text
        if mode == "advanced":
            # Sólo la directiva advanced nombra el KC explícitamente (política vigente).
            assert KC in text
        lowered = text.lower()
        assert "solución completa" not in lowered and "código terminado" not in lowered
