import json
from pathlib import Path

import pytest
from study_engine.pedagogy.fase0_seed import (
    TALOS_BASE_SYSTEM_PROMPT,
    NOTEBOOK_PROFILES,
    get_system_prompt_for_notebook,
    get_default_contract,
    FASE0_CONTRACT,
)
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    PhaseHistory,
)
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.persona_narrator import RIOPLATENSE_SYSTEM_PROMPT


def test_base_system_prompt_invariants():
    # Comportamiento
    assert "NUNCA saludes" in TALOS_BASE_SYSTEM_PROMPT
    assert "NUNCA halagues" in TALOS_BASE_SYSTEM_PROMPT
    assert "de forma vacía" in TALOS_BASE_SYSTEM_PROMPT
    assert "Sé DIRECTO" in TALOS_BASE_SYSTEM_PROMPT
    assert "pregunta" in TALOS_BASE_SYSTEM_PROMPT

    # Epistémico
    assert "cita [E#]" in TALOS_BASE_SYSTEM_PROMPT
    assert "No tengo evidencia en las fuentes autorizadas" in TALOS_BASE_SYSTEM_PROMPT
    assert "NO inventes contenido" in TALOS_BASE_SYSTEM_PROMPT

    # Format selection stays adaptive instead of imposing every template globally.
    assert "presentación clara y proporcional" in TALOS_BASE_SYSTEM_PROMPT
    assert (
        "no conviertas automáticamente una explicación en código"
        in TALOS_BASE_SYSTEM_PROMPT
    )

    # Extensión variable
    assert "máximo 200 palabras" in TALOS_BASE_SYSTEM_PROMPT
    assert "hasta 500 palabras" in TALOS_BASE_SYSTEM_PROMPT
    assert "x86-64" not in TALOS_BASE_SYSTEM_PROMPT
    assert "ABI System V" not in TALOS_BASE_SYSTEM_PROMPT
    assert "transistores/hardware" not in TALOS_BASE_SYSTEM_PROMPT


def test_solution_policy_distinguishes_guided_practice_from_protected_assessment():
    prompts = (TALOS_BASE_SYSTEM_PROMPT, RIOPLATENSE_SYSTEM_PROMPT)

    for prompt in prompts:
        assert "solución completa" in prompt.lower()
        assert "por defecto" in prompt.lower()
        assert "explícitamente" in prompt.lower()
        assert "evaluación protegida" in prompt.lower()
        assert "jamás" not in prompt.lower()


def test_notebook_specializations_all_five():
    expected_profiles = {
        "fase0-soc": (
            "Programación y Pensamiento Algorítmico",
            "roadmap_kasiu_v4_fase0",
            "traza o pseudocódigo",
        ),
        "fadena-lenguajes": (
            "Lenguajes de Programación",
            "fadena_lenguajes_2026",
            "pseudocódigo, C, programación",
        ),
        "fadena-so2": (
            "Sistemas Operativos II",
            "fadena_so2_2026",
            "estados, intercalaciones",
        ),
        "fadena-std": (
            "Sistema de Tratamiento de Datos",
            "fadena_std_2026",
            "no conviertas toda explicación en SQL",
        ),
        "fadena-teleco": (
            "Infraestructura de Telecomunicaciones",
            "fadena_teleco_2025",
            "Señales, capas",
        ),
    }

    assert {
        notebook_id: (profile.subject, profile.curriculum_id)
        for notebook_id, profile in NOTEBOOK_PROFILES.items()
    } == {
        notebook_id: (subject, curriculum_id)
        for notebook_id, (subject, curriculum_id, _) in expected_profiles.items()
    }

    prompts = {}
    for notebook_id, (subject, curriculum_id, hint) in expected_profiles.items():
        prompt = get_system_prompt_for_notebook(
            notebook_id,
            curriculum_id=curriculum_id,
        )
        prompts[notebook_id] = prompt
        assert "PERFIL CURRICULAR VALIDADO" in prompt
        assert f"Materia: {subject}" in prompt
        assert f"curriculum_id: {curriculum_id}" in prompt
        assert hint in prompt
        assert "x86-64" not in prompt
        assert "ABI System V" not in prompt

    assert "Tratamiento de Datos" not in prompts["fadena-teleco"]
    assert "Telecomunicaciones" not in prompts["fadena-std"]
    assert "programación orientada a objetos" not in prompts["fadena-so2"]


def test_profiles_match_versioned_curriculum_catalog():
    catalog_path = (
        Path(__file__).resolve().parents[2] / "config" / "notebook_kc_catalog.json"
    )
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert {
        notebook_id: profile.curriculum_id
        for notebook_id, profile in NOTEBOOK_PROFILES.items()
    } == {
        notebook_id: catalog[notebook_id]["curriculum_id"]
        for notebook_id in NOTEBOOK_PROFILES
    }
    assert "fadena-sye" not in NOTEBOOK_PROFILES


@pytest.mark.parametrize("notebook_id", ["fadena-std-extra", "mi-fadena-so", ""])
def test_unknown_and_legacy_like_ids_are_neutral(notebook_id):
    prompt = get_system_prompt_for_notebook(
        notebook_id,
        curriculum_id="fadena_std_2026",
    )

    assert prompt == TALOS_BASE_SYSTEM_PROMPT
    if notebook_id:
        contract = get_default_contract(notebook_id)
        assert contract.required_analogies == []
        assert all(
            "transistor" not in phase.phase_prompt_template.lower()
            and "en Python" not in phase.phase_prompt_template
            for phase in contract.response_phases
        )


def test_curriculum_mismatch_falls_back_to_neutral_contract():
    prompt = get_system_prompt_for_notebook(
        "fadena-std",
        curriculum_id="fadena_v1",
    )

    assert prompt == TALOS_BASE_SYSTEM_PROMPT
    assert (
        get_system_prompt_for_notebook("fadena-std", curriculum_id="fadena_std_2026")
        != TALOS_BASE_SYSTEM_PROMPT
    )
    assert (
        get_system_prompt_for_notebook("fadena-std", curriculum_id="fadena_v1")
        == TALOS_BASE_SYSTEM_PROMPT
    )


def test_all_notebook_contracts_have_universal_safe_commands():
    notebooks = [
        "fase0-soc",
        "fadena-lenguajes",
        "fadena-so2",
        "fadena-std",
        "fadena-teleco",
    ]
    for nb in notebooks:
        contract = get_default_contract(nb)
        assert contract.required_analogies == []
        assert "DAME UN EJERCICIO" in contract.safe_words
        assert "DAME LA SOLUCIÓN COMPLETA" in contract.safe_words
        assert "RESUMEN UNIDAD" in contract.safe_words
        assert "NO ENTENDÍ" in contract.safe_words
        assert ":solve" in contract.safe_words


def test_pipeline_build_phase_prompt_with_structured_command():
    contract = get_default_contract("fadena-lenguajes")
    pipeline = StructuredResponsePipeline(
        contract=contract, llm_backend=None, phase_history=PhaseHistory()
    )
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Tema: {user_query}",
        max_tokens=600,
    )

    prompt = pipeline.build_phase_prompt(phase, "RESUMEN UNIDAD 1")
    assert "=== COMANDO ESTRUCTURADO DETECTADO: RESUMEN_UNIDAD ===" in prompt
    assert "**MAPA DE UNIDAD**" in prompt
    assert "hasta 500 palabras permitidas" in prompt


def test_pipeline_build_phase_prompt_with_conversational_query():
    contract = get_default_contract("fadena-lenguajes")
    pipeline = StructuredResponsePipeline(
        contract=contract, llm_backend=None, phase_history=PhaseHistory()
    )
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Tema: {user_query}",
        max_tokens=600,
    )

    prompt = pipeline.build_phase_prompt(phase, "¿Qué es una variable?")
    assert "COMANDO ESTRUCTURADO DETECTADO" not in prompt
    assert "hasta 400 palabras" in prompt


@pytest.fixture
def isolated_offline_container(web_state_test_copy, monkeypatch):
    from study_engine.web import dependencies
    from study_engine.web.dependencies import AppContainer
    from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

    repo_root = Path(__file__).resolve().parents[2]
    monkeypatch.setattr(AppContainer, "_load_dotenv", lambda self: None)
    container = AppContainer(
        repo_root=repo_root,
        working_dir=web_state_test_copy,
        use_mock=True,
    )
    container.llm_backend = OfflinePedagogicalBackend()
    monkeypatch.setattr(dependencies, "_container", container)
    return container


def test_offline_structured_command_without_sufficient_evidence_abstains_before_backend(
    isolated_offline_container,
):
    import json
    from fastapi.testclient import TestClient
    from study_engine.web.app import app

    client = TestClient(app)

    res = client.post(
        "/api/chat/query",
        json={
            "notebook_id": "fadena-lenguajes",
            "query": "RESUMEN UNIDAD 1",
            "session_id": "test-offline-session",
        },
    )
    assert res.status_code == 200
    lines = [l for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    assert [event["event_type"] for event in events] == [
        "evidence_manifest",
        "abstention",
    ]
    assert events[0]["payload"]["abstained"] is True
    assert events[0]["payload"]["trust_status"] == "RELATED_INSUFFICIENT"
    assert events[1]["payload"]["abstention_code"] == "QUERY_OUT_OF_SCOPE"


def test_offline_out_of_corpus_abstains_honestly(isolated_offline_container):
    import json
    from fastapi.testclient import TestClient
    from study_engine.web.app import app

    client = TestClient(app)

    res = client.post(
        "/api/chat/query",
        json={
            "notebook_id": "fadena-lenguajes",
            "query": "¿Qué dice Stallman sobre machine learning?",
            "session_id": "test-offline-session-2",
        },
    )
    assert res.status_code == 200
    lines = [l for l in res.text.split("\n") if l.startswith("data: ")]
    events = [json.loads(l[6:]) for l in lines]
    tokens = "".join(
        [e["payload"]["token"] for e in events if e["event_type"] == "phase_token"]
    )
    assert "No dispongo de evidencia documental autorizada" in tokens
