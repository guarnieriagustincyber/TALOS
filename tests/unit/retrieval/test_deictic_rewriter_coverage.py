from study_engine.retrieval.query_rewriter import QueryRewriter


def test_rewriter_extrae_semaforo():
    rewritten = QueryRewriter().rewrite_contextual(
        "¿cómo funciona eso?",
        recent_turns=[
            {
                "role": "assistant",
                "content": "El semáforo coordina el acceso concurrente a la sección crítica.",
            },
        ],
    )

    assert "semáforo" in rewritten.lower() or "semaforo" in rewritten.lower()


def test_rewriter_mantiene_terminos_existentes():
    rewritten = QueryRewriter().rewrite_contextual(
        "¿cómo funciona eso?",
        recent_turns=[
            {
                "role": "assistant",
                "content": "Los punteros guardan una dirección de memoria.",
            },
        ],
    )

    assert "puntero" in rewritten.lower()
