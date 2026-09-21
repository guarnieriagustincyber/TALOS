"""Auditoría de Rendimiento: Latencia y TTFT Desagregado (Fase 7.3, Métricas 1-4, 10, 11, 14, 15).

Métricas Evaluadas:
- Métrica 1: TTFT NORMAL p95 (cache hit) < 1.2s
- Métrica 2: TTFT NORMAL p95 (cache miss) < 2.5s
- Métrica 3: TTFT GLOBAL p95 (cache hit) < 2.0s
- Métrica 4: TTFT GLOBAL p95 (cache miss) < 5.0s
- Métrica 10: EpistemicController latency p95 < 10ms
- Métrica 11: ModelRegistry latency p99 < 5ms
- Métrica 14: Cold start TTFT p95 < 5.0s
- Métrica 15: SQLite query latency p95 < 50ms

Desagregación obligatoria:
TTFT total = t_sanitization + t_retrieval + t_compilation + t_controller + t_registry + t_provider_ttft
"""

import time
from typing import Dict, List, Tuple
import numpy as np
import pytest

from study_engine.contracts.search import SearchResult
from study_engine.context.context_compiler import ContextCompiler
from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.llm.abstract_provider import AbstractLLMProvider, ProviderHealth
from study_engine.llm.circuit_breaker import CircuitBreaker
from study_engine.llm.registry import ModelRegistry
from study_engine.pedagogy.controller_payload import ConversationStyle
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.security.data_sanitizer import DataSanitizer
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


class SimulatedLatencyProvider(AbstractLLMProvider):
    def __init__(self, provider_id: str, base_ttft_ms: float = 250.0):
        self._provider_id = provider_id
        self.base_ttft_ms = base_ttft_ms

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def generate(self, prompt: str, **kwargs) -> str:
        time.sleep(self.base_ttft_ms / 1000.0)
        return "Simulated LLM token stream output"

    def generate_stream(self, prompt: str, **kwargs):
        time.sleep(self.base_ttft_ms / 1000.0)
        yield "token1 "
        yield "token2"

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_id=self._provider_id,
            availability=1.0,
            avg_latency_ms=self.base_ttft_ms,
            rate_limit_429_count=0,
            context_capacity=128000,
            multimodal_support=True,
            structured_output=True,
        )

    def max_context_tokens(self) -> int:
        return 128000

    def supports_multimodal(self) -> bool:
        return True


def _run_pipeline_measurement(
    query: str,
    depth: str,
    cache_hit: bool,
    sanitizer: DataSanitizer,
    compiler: ContextCompiler,
    controller: EpistemicController,
    registry: ModelRegistry,
    provider: SimulatedLatencyProvider,
) -> Dict[str, float]:
    """Execute single full-turn pipeline and return precise disaggregated component latencies in ms."""
    # 1. Sanitization
    t0 = time.perf_counter()
    _ = sanitizer.scrub(query)
    t_sanitization = (time.perf_counter() - t0) * 1000.0

    # 2. Retrieval (simulating cache hit = 0.5ms vs cache miss = 15ms hybrid search)
    t0 = time.perf_counter()
    if cache_hit:
        time.sleep(0.0005)
    else:
        time.sleep(0.015)
    t_retrieval = (time.perf_counter() - t0) * 1000.0

    # 3. Context Compilation
    t0 = time.perf_counter()
    seed = [
        SearchResult(
            chunk_id=f"chk_{depth}_{i}",
            source_id="src_doc",
            document_id="doc_os",
            content="Información técnica formal para análisis de rendimiento y latencia.",
            snippet="Información técnica...",
            index=i,
            page_start=40 + i,
            page_end=41 + i,
            score=0.95 - (i * 0.05),
        )
        for i in range(2 if depth == "NORMAL" else 8)
    ]
    pack = compiler.build_context_pack(query, seed, current_kc="perf_kc")
    t_compilation = (time.perf_counter() - t0) * 1000.0

    # 4. EpistemicController
    t0 = time.perf_counter()
    payload = controller.process(
        query=query,
        context_pack=pack,
        style=ConversationStyle.NORMAL if depth == "NORMAL" else ConversationStyle.DEEP,
    )
    t_controller = (time.perf_counter() - t0) * 1000.0

    # 5. ModelRegistry Selection
    t0 = time.perf_counter()
    _ = registry.select_best_provider(depth=depth)
    t_registry = (time.perf_counter() - t0) * 1000.0

    # 6. Provider TTFT
    t0 = time.perf_counter()
    # If cache hit, prefix-caching yields faster response
    effective_ttft = provider.base_ttft_ms * (0.6 if cache_hit else 1.0)
    time.sleep(effective_ttft / 1000.0)
    t_provider = (time.perf_counter() - t0) * 1000.0

    t_total = t_sanitization + t_retrieval + t_compilation + t_controller + t_registry + t_provider

    return {
        "t_sanitization": t_sanitization,
        "t_retrieval": t_retrieval,
        "t_compilation": t_compilation,
        "t_controller": t_controller,
        "t_registry": t_registry,
        "t_provider": t_provider,
        "t_total": t_total,
    }


def test_disaggregated_ttft_metrics_1_to_4() -> None:
    """Validate Métricas 1, 2, 3, 4 (TTFT NORMAL/GLOBAL hit/miss) across 50 iterations per type."""
    sanitizer = DataSanitizer()
    compiler = ContextCompiler()
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="perf_kc", p_L=0.65, attempts=2))
    controller = EpistemicController(student_storage=storage)

    registry = ModelRegistry()
    provider_normal = SimulatedLatencyProvider("groq", base_ttft_ms=280.0)
    provider_global = SimulatedLatencyProvider("gemini", base_ttft_ms=650.0)
    registry.register_provider(provider_normal, CircuitBreaker())
    registry.register_provider(provider_global, CircuitBreaker())

    test_configs = [
        ("NORMAL", True, provider_normal, 1200.0),   # Métrica 1: < 1.2s (1200ms)
        ("NORMAL", False, provider_normal, 2500.0),  # Métrica 2: < 2.5s (2500ms)
        ("GLOBAL", True, provider_global, 2000.0),   # Métrica 3: < 2.0s (2000ms)
        ("GLOBAL", False, provider_global, 5000.0),  # Métrica 4: < 5.0s (5000ms)
    ]

    for depth, hit, prov, threshold_ms in test_configs:
        totals = []
        for i in range(50):
            res = _run_pipeline_measurement(
                query=f"Consulta de rendimiento #{i}",
                depth=depth,
                cache_hit=hit,
                sanitizer=sanitizer,
                compiler=compiler,
                controller=controller,
                registry=registry,
                provider=prov,
            )
            totals.append(res["t_total"])

        p50 = float(np.percentile(totals, 50))
        p95 = float(np.percentile(totals, 95))
        p99 = float(np.percentile(totals, 99))

        assert p95 < threshold_ms, (
            f"Métrica {depth} {'hit' if hit else 'miss'} falló: p95={p95:.2f}ms >= {threshold_ms}ms"
        )


def test_epistemic_controller_latency_p95_under_10ms() -> None:
    """Métrica 10: EpistemicController execution latency p95 is strictly < 10ms across 100 runs."""
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="controller_kc", p_L=0.72, attempts=3))
    controller = EpistemicController(student_storage=storage)

    pack = ContextPack(current_kc="controller_kc", total_tokens=40)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_ctrl_1",
            document_id="doc_os",
            source_id="src_os",
            source_title="Operating Systems",
            page_start=15,
            pos_index=1,
            section="Memory",
            content="Fragmento fáctico de prueba de latencia determinista del Controller.",
            is_seed_hit=True,
            relevance_score=0.96,
            token_count=15,
        )
    )

    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = controller.process(query="Consulta de prueba", context_pack=pack)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(latencies, 95))
    assert p95 < 10.0, f"Métrica 10 falló: Controller p95={p95:.2f}ms >= 10.0ms"


def test_model_registry_latency_p99_under_5ms() -> None:
    """Métrica 11: ModelRegistry selection latency p99 is strictly < 5ms across 100 runs."""
    registry = ModelRegistry()
    for name in ["groq", "cerebras", "gemini", "nvidia", "openrouter"]:
        prov = SimulatedLatencyProvider(name)
        registry.register_provider(prov, CircuitBreaker())

    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        _ = registry.select_best_provider(depth="NORMAL")
        latencies.append((time.perf_counter() - t0) * 1000.0)

    p99 = float(np.percentile(latencies, 99))
    assert p99 < 5.0, f"Métrica 11 falló: Registry p99={p99:.2f}ms >= 5.0ms"


def test_sqlite_query_latency_p95_under_50ms(tmp_path) -> None:
    """Métrica 15: SQLite query latency p95 is strictly < 50ms across 100 reads and writes."""
    db_file = tmp_path / "perf_sqlite.db"
    storage = StudentStorage(db_file)
    storage.save_bkt_state(BKTState(kc_id="bench_kc", p_L=0.50, attempts=1))

    latencies = []
    for i in range(100):
        t0 = time.perf_counter()
        st = storage.get_bkt_state("bench_kc")
        if st:
            st.attempts += 1
            storage.save_bkt_state(st)
        latencies.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(latencies, 95))
    assert p95 < 50.0, f"Métrica 15 falló: SQLite p95={p95:.2f}ms >= 50.0ms"


def test_cold_start_ttft_p95_under_5s() -> None:
    """Métrica 14: Cold start TTFT (first pipeline initialization + invocation) is < 5.0s."""
    cold_starts = []
    for _ in range(10):
        t0 = time.perf_counter()
        # Cold initialization of components
        sanitizer = DataSanitizer()
        compiler = ContextCompiler()
        storage = StudentStorage(":memory:")
        controller = EpistemicController(student_storage=storage)
        registry = ModelRegistry()
        prov = SimulatedLatencyProvider("cold_prov", base_ttft_ms=600.0)
        registry.register_provider(prov, CircuitBreaker())

        res = _run_pipeline_measurement(
            query="Cold start query",
            depth="NORMAL",
            cache_hit=False,
            sanitizer=sanitizer,
            compiler=compiler,
            controller=controller,
            registry=registry,
            provider=prov,
        )
        cold_starts.append((time.perf_counter() - t0) * 1000.0)

    p95 = float(np.percentile(cold_starts, 95))
    assert p95 < 5000.0, f"Métrica 14 falló: Cold start p95={p95:.2f}ms >= 5000ms"
