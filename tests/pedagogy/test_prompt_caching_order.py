"""Tests for Canonical Prompt Prefix and Cache Invariance (Ola 5, E22, E27)."""

from study_engine.pedagogy.prompt_assembler import CanonicalPromptAssembler


def test_prefix_hash_invariance_across_varying_history_and_briefing() -> None:
    """Verify that changing history and dynamic session briefing does NOT alter the static corpus prefix (E22, E27)."""
    assembler = CanonicalPromptAssembler(
        notebook_id="fadena-lenguajes",
        base_system_prompt="Sos TALOS, tutor socrático soberano en ciencias de la computación.",
    )

    corpus_pack = (
        "[CHUNK 1 | Pág 45 | Urrutia Landa] Un puntero es una variable que almacena la dirección de memoria...\n"
        "[CHUNK 2 | Pág 46 | Urrutia Landa] La desreferenciación mediante el operador * accede al valor apuntado..."
    )

    # Turn 1: Initial conversation turn, empty history, briefing A
    bundle_turn1 = assembler.assemble(
        user_query="¿Qué es un puntero?",
        corpus_pack=corpus_pack,
        dynamic_instructions="MODO CONVERSACIONAL NATURAL",
        session_briefing="Sesión inicial del alumno.",
        chat_history=[],
    )

    # Turn 2: Follow-up turn, populated history, completely different briefing B
    bundle_turn2 = assembler.assemble(
        user_query="¿Y cómo se usa el operador &?",
        corpus_pack=corpus_pack,
        dynamic_instructions="MODO EXPLICACIÓN TÉCNICA FORMAL",
        session_briefing="La última vez te trabaste con la dirección de memoria en stack.",
        chat_history=[
            {"role": "user", "content": "¿Qué es un puntero?"},
            {"role": "assistant", "content": "Un puntero guarda la dirección de memoria de una variable."},
        ],
    )

    # Invariant: system_prompt MUST be 100% byte-for-byte identical between turn 1 and turn 2!
    assert bundle_turn1.system_prompt == bundle_turn2.system_prompt
    assert getattr(bundle_turn1, "prefix_hash") == getattr(bundle_turn2, "prefix_hash")

    # Verify that the static system prompt contains the notebook and corpus pack
    assert "fadena-lenguajes" in bundle_turn1.system_prompt
    assert "[CHUNK 1 | Pág 45 | Urrutia Landa]" in bundle_turn1.system_prompt

    # Invariant E27: The briefing and dynamic directives must NOT be in system_prompt, but in the dynamic messages
    assert "Sesión inicial del alumno" not in bundle_turn1.system_prompt
    assert "La última vez te trabaste" not in bundle_turn2.system_prompt

    # Verify messages structure in turn 2
    msg_roles = [m.role.value for m in bundle_turn2.messages]
    assert msg_roles[0] == "assistant"  # Dynamic block injected as assistant guidance
    assert "La última vez te trabaste" in bundle_turn2.messages[0].content
    assert msg_roles[-1] == "user"
    assert bundle_turn2.messages[-1].content == "¿Y cómo se usa el operador &?"
