"""Unit tests for GreedyMarginalSelector with token density gain."""

import pytest

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.greedy_selector import GreedyMarginalSelector
from study_engine.retrieval.stage_aware_decomposer import AtomicFacet


def make_candidate(
    cid: str,
    source: str,
    content: str,
    score: float,
    rank: int = 1,
) -> ScoredCandidate:
    return ScoredCandidate(
        chunk_id=cid,
        document_id=f"doc-{source}",
        source_id=source,
        notebook_id="NB-1",
        rank=rank,
        score=score,
        content=content,
        lexical_score=score,
        dense_score=score,
        retrieval_method="hybrid",
        page_start=1,
        page_end=1,
        pos_index=0,
        metadata={},
    )


def test_greedy_selection_submodular_diminishing_gain():
    selector = GreedyMarginalSelector(max_chunks=5, tau_pool=0.40, tau_admit=0.70)
    cands = [
        make_candidate("c1", "joyanes_fundamentos", "Las fases de resolución de problemas son análisis, diseño y codificación del algoritmo.", 0.85),
        make_candidate("c2", "joyanes_fundamentos", "El análisis del algoritmo identifica las entradas y salidas requeridas.", 0.82),
        make_candidate("c3", "goodrich_dsa_python", "La verificación de tipos en tiempo de ejecución asegura la integridad de los datos.", 0.80),
        make_candidate("c4", "spraul_think_like_a_programmer", "Dividir un problema en sub-problemas más pequeños simplifica el diseño algorítmico.", 0.75),
    ]

    facets = [
        AtomicFacet(facet_id="f-1", text="análisis del problema algorítmico"),
        AtomicFacet(facet_id="f-2", text="verificación de tipos de datos"),
    ]

    result = selector.select(
        candidates=cands,
        global_query="¿Cómo resolver problemas algorítmicos y verificar tipos?",
        facets=facets,
    )

    assert len(result.selected_chunks) >= 2
    assert result.overall_coverage > 0.60
    assert result.facet_coverage["f-global"] > 0.0


def test_source_diversity_quota():
    selector = GreedyMarginalSelector(max_chunks=5, max_per_source=2, tau_pool=0.40, tau_admit=0.60)
    # 4 candidates from joyanes, 1 from ramalho
    cands = [
        make_candidate(f"j{i}", "joyanes_fundamentos", f"Explicación técnica de algoritmos joyanes parte {i}.", 0.90 - (i * 0.01))
        for i in range(4)
    ] + [
        make_candidate("r1", "ramalho_fluent_python", "Estructuras de datos dinámicas en memoria.", 0.78)
    ]

    result = selector.select(
        candidates=cands,
        global_query="algoritmos y estructuras de datos",
    )

    joyanes_selected = [c for c in result.selected_chunks if c.source_id == "joyanes_fundamentos"]
    assert len(joyanes_selected) <= 2
    assert any(c.source_id == "ramalho_fluent_python" for c in result.selected_chunks)


def test_separation_tau_pool_and_tau_admit():
    selector = GreedyMarginalSelector(tau_pool=0.40, tau_admit=0.70)
    cands = [
        make_candidate("c_low", "src1", "Texto con score debajo de pool", 0.35),
        make_candidate("c_mid", "src2", "Texto con score en pool pero debajo de admit", 0.55),
        make_candidate("c_high", "src3", "Texto excelente con score alto para admisión", 0.88),
    ]

    result = selector.select(
        candidates=cands,
        global_query="consulta de prueba",
    )

    # c_low shouldn't even be in pool diagnostics
    assert result.diagnostics["pool_size"] == 2
    # only c_high passes tau_admit=0.70
    assert len(result.selected_chunks) == 1
    assert result.selected_chunks[0].chunk_id == "c_high"


def test_contradiction_freeze_rule():
    selector = GreedyMarginalSelector(
        tau_pool=0.40,
        tau_admit=0.70,
        max_chunks=5,
    )
    # Joyanes vs Ramalho on in-situ parameter mutability
    cand_joyanes = make_candidate(
        "j1",
        "joyanes_fundamentos",
        "En paso por referencia formal, la variable entera en memoria es modificada directamente en el marco del llamador.",
        0.88,
    )
    cand_ramalho = make_candidate(
        "r1",
        "ramalho_fluent_python",
        "En Python los enteros son estrictamente inmutables; el paso de argumentos es por asignación de objetos (call by sharing).",
        0.86,
    )
    cand_extra = make_candidate(
        "extra",
        "spraul_think_like_a_programmer",
        "Un puntero almacena una dirección física de memoria RAM.",
        0.75,
    )

    result = selector.select(
        candidates=[cand_joyanes, cand_ramalho, cand_extra],
        global_query="¿Puede una función modificar una variable entera in situ?",
        known_contradiction_pairs=[("joyanes_fundamentos", "ramalho_fluent_python")],
    )

    assert result.contradiction_detected is True
    assert result.contradiction_pair == ("joyanes_fundamentos", "ramalho_fluent_python")
    selected_sources = {c.source_id for c in result.selected_chunks}
    assert "joyanes_fundamentos" in selected_sources
    assert "ramalho_fluent_python" in selected_sources
