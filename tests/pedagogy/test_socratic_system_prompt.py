import pytest
from study_engine.pedagogy.fase0_seed import (
    TALOS_BASE_SYSTEM_PROMPT,
    get_system_prompt_for_notebook,
    get_default_contract,
    FASE0_CONTRACT,
)
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline, PhaseHistory
from study_engine.pedagogy.response_phase import ResponsePhase


def test_base_system_prompt_invariants():
    # Comportamiento
    assert 'NUNCA saludes' in TALOS_BASE_SYSTEM_PROMPT
    assert 'NUNCA halagues' in TALOS_BASE_SYSTEM_PROMPT
    assert 'de forma vacía' in TALOS_BASE_SYSTEM_PROMPT
    assert 'Sé DIRECTO' in TALOS_BASE_SYSTEM_PROMPT
    assert 'pregunta socrática' in TALOS_BASE_SYSTEM_PROMPT

    # Epistémico
    assert 'cita [E#]' in TALOS_BASE_SYSTEM_PROMPT
    assert 'No tengo evidencia en las fuentes autorizadas' in TALOS_BASE_SYSTEM_PROMPT
    assert 'NO inventes contenido' in TALOS_BASE_SYSTEM_PROMPT

    # Formatos de salida
    assert '**MAPA DE UNIDAD**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**EXPLICACIÓN DEL TEMA**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**EJERCICIO GUIADO**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**SOLUCIÓN COMPLETA**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**VERIFICACIÓN**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**TRADUCCIÓN**' in TALOS_BASE_SYSTEM_PROMPT
    assert '**EXPLICACIÓN DESDE CERO**' in TALOS_BASE_SYSTEM_PROMPT
    assert 'CAMBIO DE ENFOQUE' in TALOS_BASE_SYSTEM_PROMPT or 'NO ENTENDÍ' in TALOS_BASE_SYSTEM_PROMPT

    # Extensión variable
    assert 'máximo 200 palabras' in TALOS_BASE_SYSTEM_PROMPT
    assert 'hasta 500 palabras' in TALOS_BASE_SYSTEM_PROMPT


def test_notebook_specializations_all_five():
    # 1. fase0-soc
    p_f0 = get_system_prompt_for_notebook('fase0-soc')
    assert 'Joyanes' in p_f0
    assert 'Spraul' in p_f0
    assert 'Hammack' in p_f0
    assert 'Rosen' not in p_f0

    # 2. fadena-lenguajes
    p_leng = get_system_prompt_for_notebook('fadena-lenguajes')
    assert '10 unidades' in p_leng
    assert 'pseudocódigo → C → POO → Web/PHP' in p_leng
    assert 'Urrutia Landa' in p_leng
    assert 'Marzal Varó' in p_leng
    assert 'Stallman GNU C' in p_leng

    # 3. fadena-so2
    p_so2 = get_system_prompt_for_notebook('fadena-so2')
    assert 'Drapañoti' in p_so2
    assert '6 unidades' in p_so2
    assert 'Stallings 7ed' in p_so2
    assert 'Tanenbaum SO Modernos' in p_so2

    # 4. fadena-std
    p_std = get_system_prompt_for_notebook('fadena-std')
    assert 'Pereira' in p_std
    assert '7 módulos' in p_std
    assert 'Coronel & Morris' in p_std
    assert 'Silberschatz BD' in p_std

    # 5. fadena-teleco
    p_tel = get_system_prompt_for_notebook('fadena-teleco')
    assert 'Fusario' in p_tel
    assert '12 unidades' in p_tel
    assert 'Stallings Redes 7ed' in p_tel
    assert 'Comer TCP/IP' in p_tel


def test_all_notebook_contracts_have_universal_safe_commands():
    notebooks = ['fase0-soc', 'fadena-lenguajes', 'fadena-so2', 'fadena-std', 'fadena-teleco']
    for nb in notebooks:
        contract = get_default_contract(nb)
        assert 'DAME UN EJERCICIO' in contract.safe_words
        assert 'DAME LA SOLUCIÓN COMPLETA' in contract.safe_words
        assert 'RESUMEN UNIDAD' in contract.safe_words
        assert 'NO ENTENDÍ' in contract.safe_words
        assert ':solve' in contract.safe_words


def test_pipeline_build_phase_prompt_with_structured_command():
    contract = get_default_contract('fadena-lenguajes')
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=None, phase_history=PhaseHistory())
    phase = ResponsePhase(phase_id='conceptual', phase_prompt_template='Tema: {user_query}', max_tokens=600)

    prompt = pipeline.build_phase_prompt(phase, 'RESUMEN UNIDAD 1')
    assert '=== COMANDO ESTRUCTURADO DETECTADO: RESUMEN_UNIDAD ===' in prompt
    assert '**MAPA DE UNIDAD**' in prompt
    assert 'hasta 500 palabras permitidas' in prompt


def test_pipeline_build_phase_prompt_with_conversational_query():
    contract = get_default_contract('fadena-lenguajes')
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=None, phase_history=PhaseHistory())
    phase = ResponsePhase(phase_id='conceptual', phase_prompt_template='Tema: {user_query}', max_tokens=600)

    prompt = pipeline.build_phase_prompt(phase, '¿Qué es una variable?')
    assert 'COMANDO ESTRUCTURADO DETECTADO' not in prompt
    assert 'hasta 400 palabras' in prompt


def test_offline_structured_command_abstains_honestly():
    import json
    from fastapi.testclient import TestClient
    from study_engine.web.app import app
    from study_engine.web.dependencies import get_container
    from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

    cont = get_container()
    cont.llm_backend = OfflinePedagogicalBackend()
    client = TestClient(app)

    res = client.post('/api/chat/query', json={
        'notebook_id': 'fadena-lenguajes',
        'query': 'RESUMEN UNIDAD 1',
        'session_id': 'test-offline-session'
    })
    assert res.status_code == 200
    lines = [l for l in res.text.split('\n') if l.startswith('data: ')]
    events = [json.loads(l[6:]) for l in lines]
    tokens = ''.join([e['payload']['token'] for e in events if e['event_type'] == 'phase_token'])
    assert 'No puedo generar una respuesta estructurada sin el motor de IA activo' in tokens


def test_offline_out_of_corpus_abstains_honestly():
    import json
    from fastapi.testclient import TestClient
    from study_engine.web.app import app
    from study_engine.web.dependencies import get_container
    from study_engine.llm.offline_oracle import OfflinePedagogicalBackend

    cont = get_container()
    cont.llm_backend = OfflinePedagogicalBackend()
    client = TestClient(app)

    res = client.post('/api/chat/query', json={
        'notebook_id': 'fadena-lenguajes',
        'query': '¿Qué dice Stallman sobre machine learning?',
        'session_id': 'test-offline-session-2'
    })
    assert res.status_code == 200
    lines = [l for l in res.text.split('\n') if l.startswith('data: ')]
    events = [json.loads(l[6:]) for l in lines]
    tokens = ''.join([e['payload']['token'] for e in events if e['event_type'] == 'phase_token'])
    assert 'No dispongo de evidencia documental autorizada' in tokens

