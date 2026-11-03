"""Focal C5 checks for academic questions and their negative controls."""

from study_engine.context.c5_trust import (
    EpistemicTrustStatus,
    evaluate_conversational_rescue_compatibility,
    evaluate_epistemic_trust,
    extract_critical_query_terms,
)


def test_requirements_question_accepts_documented_nominal_forms():
    query = "¿Qué información se recoge antes de diseñar el esquema conceptual de una base de datos?"
    supported = evaluate_epistemic_trust(query, [{
        "chunk_text": "La recopilación de requisitos precede al diseño del esquema conceptual de la base de datos.",
        "relevance_score": 0.9,
    }])
    assert supported.status == EpistemicTrustStatus.SUFFICIENT_EVIDENCE
    assert supported.is_sufficient and not supported.abstained
    unrelated = evaluate_epistemic_trust(query, [{
        "chunk_text": "Diseño visual de una pantalla.", "relevance_score": 0.9,
    }])
    assert unrelated.abstained


def test_false_order_premise_requires_explicit_counterevidence():
    query = "Como las tuplas de una relación tienen orden garantizado, ¿cuál aparece siempre primero?"
    supported_refutation = evaluate_epistemic_trust(query, [{
        "chunk_text": "Las tuplas de una relación son teóricamente desordenadas: el modelo no impone ningún orden.",
        "relevance_score": 0.9,
    }])
    assert supported_refutation.status == EpistemicTrustStatus.SUFFICIENT_EVIDENCE
    assert supported_refutation.is_sufficient and not supported_refutation.abstained
    merely_related = evaluate_epistemic_trust(query, [{
        "chunk_text": "Una relación contiene tuplas y atributos con nombres.", "relevance_score": 0.9,
    }])
    assert merely_related.status == EpistemicTrustStatus.RELATED_INSUFFICIENT
    assert merely_related.abstained


def test_missing_index_detail_and_missing_benchmark_remain_blocked():
    index_query = "Un equipo empieza por elegir índices antes de entrevistar usuarios. ¿Qué paso del proceso de diseño está adelantando y qué debería obtener primero?"
    missing_index = evaluate_epistemic_trust(index_query, [{
        "chunk_text": "Primero se recopilan requisitos de usuarios para el diseño conceptual.",
        "relevance_score": 0.9,
    }])
    assert missing_index.status == EpistemicTrustStatus.RELATED_INSUFFICIENT
    assert missing_index.abstained

    benchmark_query = "Según estas páginas, ¿cuál es el rendimiento en milisegundos de un índice B+ para un millón de tuplas?"
    no_evidence = evaluate_epistemic_trust(benchmark_query, [])
    assert no_evidence.status == EpistemicTrustStatus.NO_EVIDENCE
    assert no_evidence.abstained


def test_accented_pedagogical_frame_word_does_not_block_grounded_exercise():
    query = (
        "Ejercicio: después de la recopilación de requisitos, ¿cuál es el siguiente paso: "
        "diseño conceptual, lógico o físico?"
    )
    assert "despu" not in extract_critical_query_terms(query)
    evidence = [{
        "chunk_text": (
            "Tras la recopilación de requisitos, el siguiente paso es el diseño conceptual. "
            "Después se realiza el diseño lógico y finalmente el diseño físico."
        ),
        "relevance_score": 0.9,
    }]
    result = evaluate_epistemic_trust(query, evidence)
    assert result.status == EpistemicTrustStatus.SUFFICIENT_EVIDENCE


def test_comparison_operator_and_stage_phase_paraphrase_do_not_block_multisource_evidence():
    query = "Compará la independencia física de datos con las etapas de diseño lógico y físico."
    terms = extract_critical_query_terms(query)
    assert "compara" not in terms
    evidence = [
        {
            "chunk_text": (
                "La independencia de datos física liberó a las aplicaciones de conocer "
                "los detalles del almacenamiento y mejoró su resistencia a cambios."
            ),
            "relevance_score": 0.95,
        },
        {
            "chunk_text": (
                "El primer paso es la recopilación de requisitos y el análisis. "
                "Las fases del diseño son conceptual, lógico y físico."
            ),
            "relevance_score": 0.95,
        },
    ]
    result = evaluate_epistemic_trust(query, evidence)
    assert result.status == EpistemicTrustStatus.SUFFICIENT_EVIDENCE
    assert not result.abstained


def test_uncovered_benchmark_question_cannot_reuse_previous_design_context():
    class PreviousPack:
        formatted_context = (
            "Independencia de datos física: las aplicaciones no conocen el almacenamiento físico. "
            "Las fases de diseño lógico y físico especifican el modelo y las características físicas."
        )

    previous_chunks = [{"chunk_text": PreviousPack.formatted_context}]
    reusable, reason = evaluate_conversational_rescue_compatibility(
        new_query="¿Cuánto tarda exactamente en milisegundos una consulta en este DBMS?",
        previous_context_pack=PreviousPack(),
        previous_chunks=previous_chunks,
    )
    assert not reusable
    assert "Incompatibilidad temática total" in reason or "rescate parcial denegado" in reason.lower()
