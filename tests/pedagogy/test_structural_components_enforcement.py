"""Unit tests for deterministic structural deliverable extraction and enforcement (Phase 7.5)."""

import pytest
from unittest.mock import MagicMock

from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.socratic_guard import SocraticGuard
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    extract_requested_structural_components,
)


def test_extract_requested_structural_components_all():
    query = (
        "diseñar un algoritmo que valide si una cadena dada es una dirección IPv4 válida (ej. '192.168.1.1'). "
        "Requisitos: contrato formal PRE/POST, diagrama de flujo en Mermaid, pseudocódigo estructurado y código Python con tests"
    )
    directives = extract_requested_structural_components(query)

    assert "mermaid" in directives
    assert "pytest" in directives
    assert "python_code" in directives
    assert "contracts" in directives
    assert "pseudocode" in directives

    assert "DIAGRAMA DE FLUJO EN MERMAID" in directives["mermaid"]
    assert "BATERÍA DE PRUEBAS AUTOMATIZADAS CON PYTEST" in directives["pytest"]
    assert "CÓDIGO PYTHON EJECUTABLE Y TIPADO" in directives["python_code"]
    assert "CONTRATOS FORMALES PRE / POST" in directives["contracts"]
    assert "PSEUDOCÓDIGO ESTRUCTURADO" in directives["pseudocode"]


def test_build_phase_prompt_injects_mandatory_structural_block():
    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=MagicMock())
    phase = FASE0_CONTRACT.get_phase("conceptual")

    query = (
        "diseñar un algoritmo que valide si una cadena dada es una dirección IPv4 válida. "
        "Requisitos: contrato formal PRE/POST, diagrama de flujo en Mermaid, pseudocódigo estructurado y código Python con tests"
    )
    prompt = pipeline.build_phase_prompt(phase=phase, user_query=query)

    assert "=== COMPONENTES ESTRUCTURALES EXPRESAMENTE SOLICITADOS POR EL ESTUDIANTE (OBLIGATORIOS) ===" in prompt
    assert "DIAGRAMA DE FLUJO EN MERMAID" in prompt
    assert "BATERÍA DE PRUEBAS AUTOMATIZADAS CON PYTEST" in prompt
    assert "CÓDIGO PYTHON EJECUTABLE Y TIPADO" in prompt
    assert "CONTRATOS FORMALES PRE / POST" in prompt
    assert "PSEUDOCÓDIGO ESTRUCTURADO" in prompt
    assert "NO incluyas código fuente ejecutable en Python o C." not in prompt
    assert "diagramas de flujo obligatorios en ```mermaid" in prompt


def test_socratic_guard_allows_code_when_explicitly_requested():
    guard = SocraticGuard(contract=FASE0_CONTRACT)
    phase = FASE0_CONTRACT.get_phase("conceptual")

    query = "Requisitos: código Python con tests"
    assert guard.check_user_override(query) is True

    res = guard.validate_token("```python\ndef validar_ipv4(ip: str) -> bool:\n", phase, query)
    assert res.allowed is True
    assert "def validar_ipv4" in res.emitted_token


def test_socratic_guard_blocks_code_for_standard_conceptual_query():
    guard = SocraticGuard(contract=FASE0_CONTRACT)
    phase = FASE0_CONTRACT.get_phase("conceptual")

    query = "¿Cómo funciona la pila de ejecución y el stack frame?"
    assert guard.check_user_override(query) is False

    res = guard.validate_token("```python\ndef stack(): pass", phase, query)
    assert res.allowed is False
    assert res.blocked_reason == "CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE"


@pytest.mark.anyio
async def test_generate_phased_response_boosts_tokens_and_authorizes_code():
    mock_backend = MagicMock()
    mock_backend.complete.return_value = MagicMock(text="```python\ndef test(): pass\n```")
    pipeline = StructuredResponsePipeline(contract=FASE0_CONTRACT, llm_backend=mock_backend)

    query = "validar IPv4 con código Python con tests y diagrama en Mermaid"
    events = []
    async for ev in pipeline.generate_phased_response(user_query=query, requested_phase="conceptual"):
        events.append(ev)

    start_event = next(e for e in events if e.event_type == "phase_start")
    assert start_event.payload["code_allowed"] is True
    assert start_event.payload["max_tokens"] >= 2500

def test_extract_requested_structural_components_c_and_sql():
    # Test C request
    c_query = "implementar un buffer circular con código en C y tests"
    c_directives = extract_requested_structural_components(c_query, notebook_id="fadena-lenguajes")
    assert "c_code" in c_directives
    assert "CÓDIGO C ESTÁNDAR Y DEFENSIVO" in c_directives["c_code"]

    # Test SQL request
    sql_query = "diseñar el esquema y consulta SQL parametrizada para usuarios"
    sql_directives = extract_requested_structural_components(sql_query, notebook_id="fadena-std")
    assert "sql_code" in sql_directives
    assert "CONSULTA O ESQUEMA SQL" in sql_directives["sql_code"]
