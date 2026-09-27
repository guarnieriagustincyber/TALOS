from unittest.mock import MagicMock

from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline


def _build_basic_prompt(query: str) -> str:
    contract = PedagogicalContract(
        contract_id="contract_mermaid_test",
        notebook_id="fase0-soc",
        version="1.0.0",
        authoritative_sources=("src_test",),
        domain_scope=("test",),
        base_system_prompt="Tutor TALOS.",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                max_tokens=400,
                phase_prompt_template="Explica: {concept}",
            ),
        ],
    )
    pipeline = StructuredResponsePipeline(contract=contract, llm_backend=MagicMock())
    return pipeline.build_phase_prompt(
        phase=contract.get_phase("conceptual"),
        user_query=query,
        pedagogical_mode="explain_concept",
        context_mode="basic",
    )


def test_mermaid_no_se_activa_por_termino_generico_en_basic():
    prompt = _build_basic_prompt("¿Qué es un puntero?")

    assert "MERMAID (OBLIGATORIO)" not in prompt
    assert "FORMATO INTRODUCTORIO DE RESPUESTA" in prompt


def test_mermaid_si_se_activa_con_pedido_explicito():
    prompt = _build_basic_prompt(
        "Haceme un diagrama de flujo del algoritmo de planificación"
    )

    assert "MERMAID (OBLIGATORIO)" in prompt


def test_mermaid_no_se_activa_por_memoria_en_basic():
    prompt = _build_basic_prompt("¿Qué es la memoria virtual?")

    assert "MERMAID (OBLIGATORIO)" not in prompt
    assert "FORMATO INTRODUCTORIO DE RESPUESTA" in prompt
