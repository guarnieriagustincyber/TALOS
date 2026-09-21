"""Test suite for ContextCompiler and EvidenceSet (Ola 5, Fase 5.4, E25, E30, INV-W5-1).

5 tests requeridos:
1. test_evidence_set_types           -> DIRECT/SYNTHESIS/DERIVED/UNSUPPORTED
2. test_s44_rejects_only_unsupported -> S4.4 acepta DIRECT, SYNTHESIS y DERIVED, rechaza solo UNSUPPORTED
3. test_abstention_gate_physical     -> 0 chunks = no llama al LLM (abstained=True, INV-W5-1)
4. test_cache_prefix_stable          -> prefijo idéntico entre turnos consecutivos
5. test_briefing_after_corpus        -> briefing posicionado después del corpus (E27)
"""

from study_engine.context.context_compiler import ContextCompiler
from study_engine.context.evidence_set import EvidenceSet, EvidenceType
from study_engine.contracts.generation import GenerationParameters
from study_engine.contracts.search import SearchResult
from study_engine.generation.prompts import PromptRole
from study_engine.pedagogy.prompt_assembler import CanonicalPromptAssembler


def test_evidence_set_types() -> None:
    """1. Test that all 4 EvidenceType classifications are properly represented and queryable."""
    ev_set = EvidenceSet()
    ev_set.add_claim("El puntero almacena una dirección física", EvidenceType.DIRECT, ("chk_1",))
    ev_set.add_claim("La paginación con semáforos previene condiciones de carrera en buffer compartido", EvidenceType.SYNTHESIS, ("chk_1", "chk_2"))
    ev_set.add_claim("Por lo tanto, la complejidad de acceso es O(1)", EvidenceType.DERIVED, ("chk_1",))
    ev_set.add_claim("El kernel de Windows 95 usaba microkernel puro", EvidenceType.UNSUPPORTED, ())

    assert len(ev_set.claims) == 4
    unsupported = ev_set.unsupported_claims
    assert len(unsupported) == 1
    assert unsupported[0].claim_text == "El kernel de Windows 95 usaba microkernel puro"


def test_s44_rejects_only_unsupported() -> None:
    """2. Invariant E30: S4.4 audit validates DIRECT, SYNTHESIS, and DERIVED; rejects only UNSUPPORTED."""
    valid_set = EvidenceSet()
    valid_set.add_claim("Afirmación directa textual", EvidenceType.DIRECT, ("c1",))
    valid_set.add_claim("Síntesis legítima de 2 fuentes", EvidenceType.SYNTHESIS, ("c1", "c2"))
    valid_set.add_claim("Deducción lógica formal derivada", EvidenceType.DERIVED, ("c1",))

    # All claims are legitimate epistemic types -> APPROVED
    assert valid_set.is_audited_approved() is True

    # Introducing an UNSUPPORTED claim -> REJECTED
    valid_set.add_claim("Afirmación inventada sin sustento", EvidenceType.UNSUPPORTED)
    assert valid_set.is_audited_approved() is False


def test_abstention_gate_physical() -> None:
    """3. Invariant INV-W5-1 / E25: 0 chunks triggers physical pre-LLM abstention gate (0 network calls)."""
    compiler = ContextCompiler()
    # 0 seed results
    pack = compiler.build_context_pack(query="¿Cómo funciona el scheduler de Minix?", seed_results=[])

    assert pack.abstained is True
    assert pack.abstention_reason == "NO_EVIDENCES_IN_ACTIVE_SOURCES"
    assert len(pack.retrieved_evidence) == 0
    assert pack.has_evidence is False


def test_cache_prefix_stable() -> None:
    """4. Invariant E22: Static prefix (System + Corpus) remains byte-for-byte stable across turns."""
    assembler = CanonicalPromptAssembler(
        notebook_id="nb-so-course",
        base_system_prompt="Eres un tutor socrático riguroso de Sistemas Operativos.",
    )
    corpus = "[CHUNK 1 | Pág 10 | Tanenbaum]\nLos procesos se comunican mediante IPC."

    # Turn 1
    bundle_1 = assembler.assemble(
        user_query="¿Qué es IPC?",
        corpus_pack=corpus,
        session_briefing="El alumno repasó hilos ayer.",
        chat_history=[],
    )

    # Turn 2: different chat history, different query, different dynamic briefing
    bundle_2 = assembler.assemble(
        user_query="¿Y cómo difiere de memoria compartida?",
        corpus_pack=corpus,
        session_briefing="El alumno domina IPC por mensajes.",
        chat_history=[
            {"role": "user", "content": "¿Qué es IPC?"},
            {"role": "assistant", "content": "IPC refiere a comunicación interprocesos..."},
        ],
    )

    # Prefix hash of System + Corpus must be 100% identical for Gemini prompt caching
    assert bundle_1.prefix_hash is not None
    assert bundle_1.prefix_hash == bundle_2.prefix_hash
    # System prompt is byte-for-byte identical (Cacheable static prefix)
    assert bundle_1.system_prompt == bundle_2.system_prompt


def test_briefing_after_corpus() -> None:
    """5. Invariant E27: Session Briefing is placed strictly AFTER the static corpus pack."""
    assembler = CanonicalPromptAssembler(
        notebook_id="nb-c-prog",
        base_system_prompt="Base tutor prompt.",
    )
    corpus = "[CHUNK 0 | Pág 1 | K&R]\nint a = 5;"
    briefing = "ALUMNO_DIFICULTAD_PUNTEROS_PREVIA"

    bundle = assembler.assemble(
        user_query="Explicame int a",
        corpus_pack=corpus,
        session_briefing=briefing,
    )

    # System prompt holds the cacheable prefix
    assert corpus in bundle.system_prompt
    # Crucial E27 check: Briefing must NOT be inside the cacheable system prompt!
    assert briefing not in bundle.system_prompt

    # Briefing must appear in subsequent non-cacheable messages
    dynamic_text = "\n".join(m.content for m in bundle.messages)
    assert briefing in dynamic_text
