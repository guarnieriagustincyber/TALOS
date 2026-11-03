"""Unit tests M1-02: reutilización del ConceptResponse APROBADO por episode_id
en la ruta de diálogo (continuidad sin regenerar/re-auditar concepto verificar
byte-idéntico).

Fail-closed garantizado:
- ABSTAINED / sin packet NUNCA se cachea.
- Un fallo de explain_concept no se cachea y degrada a packet=None.
- Un episode_id distinto no hereda la respuesta de otro episodio.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO)); sys.path.insert(0, str(REPO / "src"))

import pytest

from study_engine.web.routes import dialogue as dialogue_router


class FakeConceptResponse:
    def __init__(self, status: str, packet=None):
        self.status = status
        self.packet = packet
        self.audit_verdict = "APPROVED" if status == "PRESENTABLE" else "REJECTED_UNSUPPORTED"


class FakePacket:
    """El packet porta su procedencia (reporte S4.4 + hashes) dentro del objeto."""


class FakeOrch:
    def __init__(self):
        self.calls = 0
        self._next = None

    def set_next(self, resp):
        self._next = resp

    def explain_concept(self, episode_id: str):
        self.calls += 1
        if isinstance(self._next, Exception):
            raise self._next
        return self._next


@pytest.fixture(autouse=True)
def clean_cache():
    dialogue_router._EPISODE_CONCEPT_RESPONSES.clear()
    yield
    dialogue_router._EPISODE_CONCEPT_RESPONSES.clear()


def test_presentable_response_is_cached_and_reused_without_new_call():
    orch = FakeOrch()
    orch.set_next(FakeConceptResponse("PRESENTABLE", packet=FakePacket()))
    ep = "ep_a"

    first = dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert orch.calls == 1
    dialogue_router._load_or_reuse_concept_response(orch, ep)  # segundo turno
    dialogue_router._load_or_reuse_concept_response(orch, ep)  # tercer turno
    assert orch.calls == 1  # NINGUNA re-propuesta
    assert first.packet is not None
    assert first.status == "PRESENTABLE"


def test_abstained_response_is_never_cached():
    orch = FakeOrch()
    orch.set_next(FakeConceptResponse("ABSTAINED", packet=None))
    ep = "ep_b"

    r1 = dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert r1 is not None and r1.status == "ABSTAINED" and r1.packet is None
    dialogue_router._load_or_reuse_concept_response(orch, ep)
    dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert orch.calls == 3  # siempre recomputa (fail-closed)


def test_explain_concept_failure_is_not_cached_and_degrades_to_none():
    orch = FakeOrch()
    orch.set_next(RuntimeError("provider down"))
    ep = "ep_c"
    r1 = dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert r1 is None
    r2 = dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert r2 is None
    assert orch.calls == 2
    assert ep not in dialogue_router._EPISODE_CONCEPT_RESPONSES


def test_different_episodes_do_not_share_cache():
    orch = FakeOrch()
    orch.set_next(FakeConceptResponse("PRESENTABLE", packet=FakePacket()))
    dialogue_router._load_or_reuse_concept_response(orch, "ep_x")
    dialogue_router._load_or_reuse_concept_response(orch, "ep_y")
    assert orch.calls == 2  # cada episodio consulta su propia identidad


def test_recompute_replaces_cache_after_tuning_from_fail_to_ok():
    orch = FakeOrch()
    orch.set_next(FakeConceptResponse("ABSTAINED", packet=None))
    ep = "ep_d"
    dialogue_router._load_or_reuse_concept_response(orch, ep)
    orch.set_next(FakeConceptResponse("PRESENTABLE", packet=FakePacket()))
    r2 = dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert r2.status == "PRESENTABLE"
    # ahora aprobado -> entra a la cache
    dialogue_router._load_or_reuse_concept_response(orch, ep)
    assert orch.calls == 2
