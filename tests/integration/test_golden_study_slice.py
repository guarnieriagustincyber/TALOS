"""Golden End-to-End Study Tests for TALOS Vertical Slice (5 Notebooks).

Verifies the complete deterministic study loop across all 5 notebooks:
1. fase0-soc -> KC: aritmetica_punteros
2. fadena-lenguajes -> KC: leng_pseudocodigo_estructurado
3. fadena-so2 -> KC: so2_gestion_procesos_pcb
4. fadena-std -> KC: std_modelo_relacional_er
5. fadena-teleco -> KC: teleco_transmision_datos

Checks tested:
- Backend KC eligibility validation
- Retrieval and role segmentation (PRIMARY, METHODOLOGICAL, etc.)
- Concept synthesis proposal & S4.4 approval (or ABSTAINED fallback)
- Presentation of verified QUALIFIABLE exercise
- Deterministic grading
- Idempotent observation registration
- BKT update P(L)
"""

import pytest
from fastapi.testclient import TestClient

from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


@pytest.fixture
def client() -> TestClient:
    app = create_app()
    container = AppContainer(use_mock=True)
    set_container(container)
    return TestClient(app)


GOLDEN_CASES = [
    {
        "notebook_id": "fase0-soc",
        "kc_id": "aritmetica_punteros",
        "answer": "1012",
        "expected_correct": True,
    },
    {
        "notebook_id": "fadena-lenguajes",
        "kc_id": "leng_pseudocodigo_estructurado",
        "answer": "C",
        "expected_correct": True,
    },
    {
        "notebook_id": "fadena-so2",
        "kc_id": "so2_gestion_procesos_pcb",
        "answer": "PCB",
        "expected_correct": True,
    },
    {
        "notebook_id": "fadena-std",
        "kc_id": "std_modelo_relacional_er",
        "answer": "tupla",
        "expected_correct": True,
    },
    {
        "notebook_id": "fadena-teleco",
        "kc_id": "teleco_transmision_datos",
        "answer": "C",
        "expected_correct": True,
    },
]


@pytest.mark.parametrize("case", GOLDEN_CASES)
def test_golden_study_loop(client: TestClient, case: dict) -> None:
    nb_id = case["notebook_id"]
    kc_id = case["kc_id"]

    # 1. Start episode
    start_resp = client.post(
        "/api/pedagogy/episode/start",
        json={"notebook_id": nb_id, "kc_id": kc_id},
    )
    assert start_resp.status_code == 200, start_resp.text
    ep_data = start_resp.json()
    ep_id = ep_data["episode_id"]
    assert ep_data["phase"] == "EXPLAINING"

    # 2. Request Concept Explanation
    concept_resp = client.get(f"/api/pedagogy/episode/{ep_id}/concept")
    assert concept_resp.status_code == 200
    c_data = concept_resp.json()
    assert c_data["status"] in ("PRESENTABLE", "ABSTAINED")

    # 3. Request Next Intervention (QUALIFIABLE exercise)
    next_resp = client.get(f"/api/pedagogy/episode/{ep_id}/next")
    assert next_resp.status_code == 200
    interv_data = next_resp.json()
    assert interv_data["intervention_type"] == "EXERCISE"
    step_id = interv_data["step_id"]
    exercise = interv_data["exercise"]
    assert exercise["verification_status"] == "QUALIFIABLE"

    # 4. Respond to exercise (Deterministic grading & BKT)
    respond_resp = client.post(
        f"/api/pedagogy/episode/{ep_id}/respond",
        json={"step_id": step_id, "response_text": case["answer"]},
    )
    assert respond_resp.status_code == 200
    r_data = respond_resp.json()
    assert r_data["is_correct"] is case["expected_correct"]
    assert r_data["bkt_update"]["p_L"] > 0.1
    assert r_data["was_idempotent_replay"] is False

    # 5. Idempotent Retry: repeating the same step_id must NOT increment attempts
    repeat_resp = client.post(
        f"/api/pedagogy/episode/{ep_id}/respond",
        json={"step_id": step_id, "response_text": case["answer"]},
    )
    assert repeat_resp.status_code == 200
    rep_data = repeat_resp.json()
    assert rep_data["was_idempotent_replay"] is True
    assert rep_data["bkt_update"]["attempts"] == r_data["bkt_update"]["attempts"]


def test_negative_unknown_kc_rejected(client: TestClient) -> None:
    resp = client.post(
        "/api/pedagogy/episode/start",
        json={"notebook_id": "fase0-soc", "kc_id": "kc_fantasma_inexistente"},
    )
    assert resp.status_code == 400
    assert "no pertenece" in resp.json()["detail"]


def test_negative_cross_notebook_kc_rejected(client: TestClient) -> None:
    # Attempting to start SO2 KC in fase0-soc must fail-closed
    resp = client.post(
        "/api/pedagogy/episode/start",
        json={"notebook_id": "fase0-soc", "kc_id": "so2_gestion_procesos_pcb"},
    )
    assert resp.status_code == 400
