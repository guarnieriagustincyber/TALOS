"""Unit and Contract Tests for SymbolGuard (Sprint v1.2 / Fase 5).

Verifies the 3 Golden Rules from Dirección Técnica:
1. Activation strictly on 'Canonicity Assertion' (inhibited on student code/debugging).
2. Local O(1) Static Whitelist for ISO C, POSIX, and x86-64 registers.
3. Student Morphology & Hesitation Tolerance.
4. Enmienda E-FTS5: Safe Document Frequency check without underscore tokenizer hazards.
5. Performance gate: < 1ms per query.
"""

import time
import pytest

from study_engine.retrieval.symbol_guard import SymbolGuard, SymbolGuardDecision
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture(scope="module")
def store(knowledge_store_test_copy):
    if knowledge_store_test_copy is not None:
        return KnowledgeStore(knowledge_store_test_copy)
    return None


@pytest.fixture(scope="module")
def guard(store):
    return SymbolGuard(store=store)


def test_symbol_guard_detects_apocryphal_function(guard, store):
    """GS2-OOD-046: Non-standard function asserting C stdlib must fail-closed."""
    query = "¿Qué biblioteca estándar de C contiene la función free_all_memory_at_once()?"
    decision = guard.evaluate(query, store=store)
    assert decision.should_abstain is True
    assert decision.reason == "NON_STANDARD_CANONICAL_FUNCTION"
    assert decision.symbol == "free_all_memory_at_once"
    assert decision.canonicity_asserted is True
    assert decision.is_student_debugging is False


def test_symbol_guard_detects_apocryphal_register(guard, store):
    """GS2-OOD-032: Fake register asserting x86-64 Linux kernel must fail-closed."""
    query = "¿Qué registro x86-64 utiliza el kernel Linux para el quantum_accumulator_register?"
    decision = guard.evaluate(query, store=store)
    assert decision.should_abstain is True
    assert decision.reason == "APOCRYPHAL_CANONICAL_REGISTER"
    assert decision.symbol == "quantum_accumulator_register"
    assert decision.canonicity_asserted is True
    assert decision.is_student_debugging is False


def test_symbol_guard_allows_student_debugging_code(guard, store):
    """Regla 1 (Inhibición): Student code debugging must NEVER be vetoed."""
    student_queries = [
        "¿Por qué mi función free_all_memory() da segmentation fault?",
        "En mi código de C, ¿por qué mi función crear_nodo_arbol() da segfault?",
        "¿Cómo implemento quantum_accumulator en mi TAD?",
        "¿Por qué mi función liberar_matriz() da double free al ejecutar free(matriz[i])?",
        "En mi práctica de punteros, ¿por qué mi_vector_redimensionar() pierde datos?",
    ]
    for q in student_queries:
        decision = guard.evaluate(q, store=store)
        assert decision.should_abstain is False, f"Spurious veto on student query: {q}"
        assert decision.is_student_debugging is True
        assert decision.reason == "STUDENT_DEBUGGING_CONTEXT"


def test_symbol_guard_allows_canonical_whitelisted_symbols(guard, store):
    """Regla 2: Valid ISO C functions and x86-64 registers must pass cleanly."""
    valid_queries = [
        "¿Qué biblioteca estándar de C contiene la función malloc()?",
        "¿Qué biblioteca estándar de C contiene la función printf()?",
        "¿Qué registro x86-64 se utiliza para el puntero de pila rsp?",
        "¿Qué registro de la cpu se utiliza para el acumulador rax?",
        "¿Cómo opera la syscall POSIX fork() para crear procesos?",
    ]
    for q in valid_queries:
        decision = guard.evaluate(q, store=store)
        assert decision.should_abstain is False, f"Valid canonical symbol rejected: {q}"
        assert decision.canonicity_asserted is True


def test_symbol_guard_allows_composite_canonical_symbols(guard, store):
    """Regla 2: Composite comparisons of valid symbols (e.g. brk_sbrk, reg_rsp) must not be vetoed."""
    composite_queries = [
        "Desde la perspectiva del estándar POSIX, compare brk_sbrk para asignación de memoria",
        "En la arquitectura x86-64, ¿cómo interactúa el puntero de pila reg_rsp con reg_rbp?",
        "¿Cómo se implementa el control de flujo con setjmp_longjmp según el estándar C?",
        "¿Cuál es la diferencia entre select_poll_epoll en llamadas al sistema POSIX?",
    ]
    for q in composite_queries:
        decision = guard.evaluate(q, store=store)
        assert decision.should_abstain is False, f"Composite canonical query rejected: {q}"



def test_symbol_guard_hesitation_normalization(guard, store):
    """Regla 3: Hesitation prefixes must be stripped without masking the apocryphal symbol."""
    queries = [
        "Creo que la función free_all_memory_at_once() pertenece a la biblioteca estándar de C, ¿es así?",
        "¿Existe la función apócrifa fake_c_alloc() en ANSI C?",
    ]
    for q in queries:
        decision = guard.evaluate(q, store=store)
        assert decision.should_abstain is True
        assert decision.reason == "NON_STANDARD_CANONICAL_FUNCTION"


def test_symbol_guard_enmienda_e_fts5_safe_df_check(guard, store):
    """Enmienda E-FTS5: Underscores in identifiers must not cause tokenizer errors."""
    if store is None:
        pytest.skip("KnowledgeStore not available")

    # Non-existent snake_case identifier asserting canonicity
    query = "¿Qué registro del kernel Linux se llama hyper_thread_quantum_accumulator_v2?"
    decision = guard.evaluate(query, store=store)
    assert decision.should_abstain is True
    assert decision.symbol == "hyper_thread_quantum_accumulator_v2"


def test_symbol_guard_sub_millisecond_performance(guard):
    """Performance Gate: Whitelist lookup and evaluation must take < 1ms per query."""
    query = "¿Qué biblioteca estándar de C contiene la función free_all_memory_at_once()?"
    t0 = time.perf_counter()
    iterations = 200
    for _ in range(iterations):
        guard.evaluate(query, store=None)
    t1 = time.perf_counter()
    avg_ms = ((t1 - t0) / iterations) * 1000.0
    assert avg_ms < 1.0, f"SymbolGuard evaluation too slow: {avg_ms:.4f} ms per query"
