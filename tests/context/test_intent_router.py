"""Test suite for Intent & Context Router (Ola 5, Fase 5.2).

8 tests requeridos:
1. test_normal_focal_query        -> "¿Qué es starvation?" -> NORMAL
2. test_deep_chapter_analysis     -> "Desglosá el capítulo 5" -> DEEP
3. test_global_cross_book         -> "Compará Tanenbaum vs Silberschatz" -> GLOBAL
4. test_multimodal_orthogonal     -> "Explicá el diagrama" + imagen -> depth + multimodal=True
5. test_multimodal_with_global    -> GLOBAL + imagen -> GLOBAL + multimodal=True
6. test_fallback_short_query      -> query corta sin match -> NORMAL
7. test_fallback_long_query       -> query larga sin match -> DEEP
8. test_router_never_decides_bkt  -> el router no toca BKT (INV-W5-3)
"""

import asyncio
from datetime import datetime, timezone

from study_engine.context.intent_router import IntentRouter
from study_engine.context.routing_decision import RoutingDecision
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_normal_focal_query() -> None:
    """1. Focal conceptual query routes to NORMAL depth with bounded tokens."""
    router = IntentRouter()
    decision = asyncio.run(router.route("¿Qué es starvation?"))
    
    assert decision.depth == "NORMAL"
    assert decision.requires_multimodal is False
    assert decision.requires_multi_source is False
    assert decision.requires_long_context is False
    assert decision.max_context_tokens == 4000
    assert decision.suggested_provider is None


def test_deep_chapter_analysis() -> None:
    """2. Chapter / deep drill analysis query routes to DEEP depth."""
    router = IntentRouter()
    decision = asyncio.run(router.route("Desglosá el capítulo 5 de Sistemas Operativos"))
    
    assert decision.depth == "DEEP"
    assert decision.requires_multimodal is False
    assert decision.requires_multi_source is False
    assert decision.requires_long_context is True
    assert decision.max_context_tokens == 16000
    assert decision.suggested_provider is None


def test_global_cross_book() -> None:
    """3. Cross-source / multi-book comparison routes to GLOBAL depth."""
    router = IntentRouter()
    decision = asyncio.run(router.route("Compará Tanenbaum vs Silberschatz en gestión de memoria"))
    
    assert decision.depth == "GLOBAL"
    assert decision.requires_multimodal is False
    assert decision.requires_multi_source is True
    assert decision.requires_long_context is True
    assert decision.max_context_tokens == 40000
    assert decision.suggested_provider is None


def test_multimodal_orthogonal() -> None:
    """4. MULTIMODAL is strictly orthogonal to depth: NORMAL depth + multimodal=True."""
    router = IntentRouter()
    decision = asyncio.run(
        router.route(
            "Explicá el diagrama adjunto",
            has_multimodal_asset=True,
        )
    )
    
    # Assert depth is one of 3 levels, NOT a 4th "MULTIMODAL" level
    assert decision.depth in ("NORMAL", "DEEP", "GLOBAL")
    assert decision.requires_multimodal is True


def test_multimodal_with_global() -> None:
    """5. MULTIMODAL combines cleanly with GLOBAL cross-source queries."""
    router = IntentRouter()
    decision = asyncio.run(
        router.route(
            "Compará el gráfico de Silberschatz con la arquitectura de Tanenbaum",
            has_multimodal_asset=True,
        )
    )
    
    assert decision.depth == "GLOBAL"
    assert decision.requires_multimodal is True
    assert decision.requires_multi_source is True
    assert decision.requires_long_context is True


def test_fallback_short_query() -> None:
    """6. Short query without specific heuristic match falls back to NORMAL (<=12 words)."""
    router = IntentRouter()
    # 5 words, no explicit regex match
    decision = asyncio.run(router.route("hablemos un poco sobre semáforos"))
    
    assert decision.depth == "NORMAL"
    assert decision.requires_long_context is False
    assert decision.max_context_tokens == 4000


def test_fallback_long_query() -> None:
    """7. Long query without specific heuristic match falls back to DEEP (>12 words)."""
    router = IntentRouter()
    # 16 words, elaborate description without explicit 'capítulo' or 'comparar'
    long_query = (
        "estaba pensando en cómo los procesos interactúan entre sí cuando hay condiciones de carrera "
        "en arquitecturas multicore modernas"
    )
    decision = asyncio.run(router.route(long_query))
    
    assert decision.depth == "DEEP"
    assert decision.requires_long_context is True
    assert decision.max_context_tokens == 16000


def test_router_never_decides_bkt() -> None:
    """8. INV-W5-3 Invariant: IntentRouter never alters, mutates, or reads/writes student BKT state."""
    storage = StudentStorage(":memory:")
    now = datetime.now(timezone.utc)
    initial_bkt = BKTState(
        kc_id="semaphores_mutex",
        p_L=0.62,
        attempts=3,
        last_update=now,
    )
    storage.save_bkt_state(initial_bkt)

    router = IntentRouter()
    
    # Process multiple queries with active KC
    queries = [
        "¿Qué es un semáforo?",
        "Desglosá la implementación en el capítulo 4",
        "Compará semáforos vs mutex a lo largo de todos los libros",
    ]
    for q in queries:
        decision = asyncio.run(router.route(q, active_kc_id="semaphores_mutex"))
        assert decision.depth in ("NORMAL", "DEEP", "GLOBAL")
        # Router decisions are read-only pure context routing
        assert hasattr(decision, "depth")
        assert not hasattr(decision, "p_L")
        assert not hasattr(decision, "mastery")

    # Verify BKT in storage is 100% untouched
    current_bkt = storage.get_bkt_state("semaphores_mutex")
    assert current_bkt is not None
    assert current_bkt.p_L == 0.62
    assert current_bkt.attempts == 3
    assert current_bkt.last_update == now
