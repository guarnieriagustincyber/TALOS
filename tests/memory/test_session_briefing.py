"""Test suite for Session Memory & Context Replay (Ola 6, Fase 6.3).

7 tests requeridos:
1. test_briefing_includes_weak_kcs      -> menciona KCs con P(L) < 0.50
2. test_briefing_includes_hints         -> menciona pistas pedidas
3. test_briefing_includes_due_reviews   -> menciona repasos SM-2
4. test_briefing_includes_last_topic    -> menciona el último tema
5. test_briefing_after_corpus           -> no invalida caché del libro (E27)
6. test_state_object_compresses_history -> 100 turnos -> state de ~3-8K tokens
7. test_cross_session_continuity        -> sesión N+1 conoce contexto de N y respeta aislamiento
"""

from datetime import datetime, timezone
import pytest

from study_engine.memory.conversation_state import ConversationStateObject
from study_engine.memory.session_briefing import SessionBriefingGenerator, WeakKCInfo
from study_engine.memory.session_history import SessionHistory, SessionRecord
from study_engine.pedagogy.prompt_assembler import CanonicalPromptAssembler
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_briefing_includes_weak_kcs() -> None:
    """1. Generator identifies weak KCs (P(L) < 0.50) from BKT and mentions them."""
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="memoria_virtual", p_L=0.35, attempts=3))
    storage.save_bkt_state(BKTState(kc_id="punteros_basicos", p_L=0.85, attempts=6))

    history = SessionHistory(":memory:")
    history.record_session(
        SessionRecord(
            session_id="s1",
            notebook_id="fadena-sistemas",
            topic="Gestión de Memoria",
            next_topic="Paginación",
        )
    )

    generator = SessionBriefingGenerator(
        student_storage=storage,
        session_history=history,
    )

    briefing = generator.generate_briefing(
        student_id="agustin",
        notebook_id="fadena-sistemas",
        student_name="Agustín",
    )

    assert "memoria virtual" in briefing
    assert "0.35" in briefing
    assert "todavía débil" in briefing
    # Strong KC must NOT be flagged as weak
    assert "punteros_basicos" not in briefing


def test_briefing_includes_hints() -> None:
    """2. Generator reflects hints requested in previous exercises."""
    history = SessionHistory(":memory:")
    history.record_session(
        SessionRecord(
            session_id="s_hints",
            notebook_id="fadena-sistemas",
            topic="Llamadas al Sistema",
            next_topic="Señales",
            hints_requested=3,
        )
    )

    generator = SessionBriefingGenerator(
        session_history=history,
        hint_ledger=3,
    )

    briefing = generator.generate_briefing(
        student_id="agustin",
        notebook_id="fadena-sistemas",
    )

    assert "3 pistas" in briefing


def test_briefing_includes_due_reviews() -> None:
    """3. Generator alerts student about pending SM-2 spaced repetition reviews."""
    history = SessionHistory(":memory:")
    history.record_session(
        SessionRecord(
            session_id="s_sm2",
            notebook_id="fadena-sistemas",
            topic="Planificación de Procesos",
            next_topic="Hilos y Concurrencia",
        )
    )

    generator = SessionBriefingGenerator(
        session_history=history,
        sm2_scheduler=["anchor_round_robin", "anchor_quantum"],
    )

    briefing = generator.generate_briefing(
        student_id="agustin",
        notebook_id="fadena-sistemas",
    )

    assert "2 repasos pendientes" in briefing


def test_briefing_includes_last_topic() -> None:
    """4. Generator starts briefing referencing the student's previous topic."""
    history = SessionHistory(":memory:")
    history.record_session(
        SessionRecord(
            session_id="s_prev",
            notebook_id="fadena-sistemas",
            topic="Estructura del Kernel",
            next_topic="Módulos Dinámicos",
        )
    )

    generator = SessionBriefingGenerator(
        session_history=history,
    )

    briefing = generator.generate_briefing(
        student_id="agustin",
        notebook_id="fadena-sistemas",
        student_name="Agustín",
    )

    assert "Agustín, la última vez estuviste trabajando en Estructura del Kernel." in briefing
    assert "Módulos Dinámicos" in briefing


def test_briefing_after_corpus() -> None:
    """5. Invariant E27: Briefing is injected AFTER Corpus Pack to preserve 32K+ cache prefix."""
    assembler = CanonicalPromptAssembler(
        notebook_id="fadena-sistemas",
        base_system_prompt="Sos TALOS, profesor universitario.",
    )

    corpus_pack = (
        "[CHUNK 1 | Pág 100 | Silberschatz] La memoria virtual separa la memoria lógica del usuario de la memoria física.\n"
        "[CHUNK 2 | Pág 101 | Silberschatz] La tabla de páginas mapea páginas virtuales a marcos físicos."
    )

    # Sesión 1 con briefing A
    bundle1 = assembler.assemble(
        user_query="¿Qué es una página?",
        corpus_pack=corpus_pack,
        session_briefing="Agustín, la última vez estuviste trabajando en Memoria Principal.",
    )

    # Sesión 2 con briefing B completamente diferente
    bundle2 = assembler.assemble(
        user_query="¿Qué es una página?",
        corpus_pack=corpus_pack,
        session_briefing="Agustín, la última vez estuviste trabajando en Paginación Jerárquica.",
    )

    # Invariant E27: Static prefix and prefix_hash MUST remain 100% byte-for-byte identical!
    assert bundle1.system_prompt == bundle2.system_prompt
    assert bundle1.prefix_hash == bundle2.prefix_hash

    # The briefing MUST be located in the dynamic messages (position [3]), NOT inside system_prompt
    assert "Memoria Principal" not in bundle1.system_prompt
    assert "Paginación Jerárquica" not in bundle2.system_prompt

    # Verify briefing is present in the assistant operational context message
    assert "Memoria Principal" in bundle1.messages[0].content
    assert "Paginación Jerárquica" in bundle2.messages[0].content


def test_state_object_compresses_history() -> None:
    """6. ConversationStateObject compresses 100 turns into ~3-8K tokens structured state."""
    # Simulate 100 turns of dialogue with technical discussion
    turns = []
    topics = ["punteros", "memoria virtual", "paginacion", "tlb", "fallo de pagina", "segmentacion"]
    for i in range(100):
        topic = topics[i % len(topics)]
        if i % 2 == 0:
            turns.append({
                "role": "user",
                "content": f"Turno {i+1}: ¿Cómo se relaciona {topic} con la arquitectura? Tuve un error al calcular la dirección base.",
            })
        else:
            turns.append({
                "role": "assistant",
                "content": f"Turno {i+1}: Fijate que {topic} interactúa mapeando la tabla física según los registros del procesador.",
            })

    # Uncompressed raw text would be huge (~25-50K words)
    state = ConversationStateObject.compress_history(
        turns=turns,
        goal="Dominar el subsistema de memoria en sistemas operativos",
    )

    # Verify structured properties
    assert state.goal == "Dominar el subsistema de memoria en sistemas operativos"
    assert len(state.active_kcs) > 0
    assert len(state.recent_errors) > 0
    assert len(state.open_questions) > 0
    assert "Turnos" in state.conversation_summary

    # Verify compression to target range ~3-8K tokens
    assert 3000 <= state.token_estimate <= 8000
    assert state.token_estimate < 10000

    # Verify prompt serialization
    prompt_ctx = state.to_prompt_context()
    assert "ESTADO CONVERSACIONAL Y COGNITIVO" in prompt_ctx
    assert state.goal in prompt_ctx


def test_cross_session_continuity() -> None:
    """7. Cross-session continuity: Session N+1 recalls Session N, with per-notebook isolation."""
    history = SessionHistory(":memory:")

    # Record session in Notebook A
    history.record_session(
        SessionRecord(
            session_id="sess_nbA_1",
            notebook_id="notebook_A",
            student_id="agustin",
            topic="Árboles Binarios Balanceados",
            next_topic="Árboles Red-Black",
            hints_requested=2,
        )
    )

    # Record session in Notebook B
    history.record_session(
        SessionRecord(
            session_id="sess_nbB_1",
            notebook_id="notebook_B",
            student_id="agustin",
            topic="Concurrencia con Semáforos",
            next_topic="Monitores y Locks",
            hints_requested=0,
        )
    )

    generator = SessionBriefingGenerator(session_history=history)

    # Briefing for Notebook A
    briefing_A = generator.generate_briefing(student_id="agustin", notebook_id="notebook_A")
    assert "Árboles Binarios Balanceados" in briefing_A
    assert "Árboles Red-Black" in briefing_A
    # Notebook A must NOT see Notebook B topic (Isolation)
    assert "Concurrencia" not in briefing_A
    assert "Semáforos" not in briefing_A

    # Briefing for Notebook B
    briefing_B = generator.generate_briefing(student_id="agustin", notebook_id="notebook_B")
    assert "Concurrencia con Semáforos" in briefing_B
    assert "Monitores y Locks" in briefing_B
    # Notebook B must NOT see Notebook A topic
    assert "Árboles" not in briefing_B

    # Invariant INV-W6-2 check: Verify BKT state was NOT mutated
    storage = StudentStorage(":memory:")
    storage.save_bkt_state(BKTState(kc_id="arboles_avl", p_L=0.45, attempts=2))
    p_L_before = storage.get_bkt_state("arboles_avl").p_L

    gen_bkt = SessionBriefingGenerator(
        student_storage=storage,
        session_history=history,
    )
    _ = gen_bkt.generate_briefing(student_id="agustin", notebook_id="notebook_A")

    p_L_after = storage.get_bkt_state("arboles_avl").p_L
    assert p_L_before == p_L_after == 0.45
