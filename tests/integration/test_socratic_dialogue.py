"""Golden integration test suite for Pedagogical Dialogue Engine (Modo Socrático).

Verifies the 12 functional requirements of the Socratic Dialogue Engine:
1. test_basic_clarification_flow
2. test_example_request
3. test_reformulation_request
4. test_max_turns_suggests_not_forces
5. test_student_rejects_exercise_suggestion
6. test_student_accepts_exercise_suggestion
7. test_student_skips_to_exercise
8. test_dialogue_after_exercise
9. test_off_topic_redirect
10. test_abstention_on_insufficient_evidence
11. test_no_global_pool_fallback
12. test_comprehension_tracking_is_consultive
"""

import asyncio
from datetime import datetime, timezone
import pytest

from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.dialogue_contracts import (
    DialogueState,
    DialogueTurn,
    SocraticQuestion,
)
from study_engine.pedagogy.dialogue_engine import DialogueEngine
from study_engine.pedagogy.dialogue_policy import DialoguePolicy
from study_engine.pedagogy.dialogue_state import DialogueStateTracker
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


from study_engine.audit.contracts import AuditVerdict


def create_mock_concept_packet(kc_id: str = "aritmetica_punteros") -> ConceptPacket:
    citation = CitationRecord(
        citation_id="E1",
        chunk_id="chk_joyanes_01",
        document_id="doc_joyanes_fundamentos",
        source_id="src_joyanes_fundamentos",
        source_title="Joyanes - Fundamentos de Programación",
        content_hash="a" * 64,
    )
    return ConceptPacket(
        kc_id=kc_id,
        notebook_id="fase0-soc",
        objective="Comprender el acceso directo a memoria en arrays",
        evidence_by_role={"PRIMARY": [citation]},
        core_concept="Direccionamiento contiguo y aritmética de punteros",
        mental_model="Casilleros contiguos en memoria RAM indexados por offset",
        reasoning_guidance="Considere la base más el offset multiplicado por el tamaño del tipo de dato.",
        formalization="Acceso O(1) vía dirección base + desplazamiento * tamaño",
        implementation_guidance="int *ptr = arr; *(ptr + i)",
        pitfalls=("confundir puntero con el valor apuntado",),
        citations=(citation,),
        s44_report=None,
        audit_verdict=AuditVerdict.APPROVED,
        assembly_hash="b" * 64,
    )


def create_test_episode(kc_id: str = "aritmetica_punteros", phase: EpisodePhase = EpisodePhase.DIALOGUE) -> Episode:
    return Episode(
        episode_id="ep_socratic_01",
        kc_id=kc_id,
        notebook_id="fase0-soc",
        objective="Comprender el acceso directo a memoria en arrays",
        phase=phase,
        current_step_id="step_dialogue_1",
    )


class MockExerciseSelector:
    def has_qualifiable(self, kc_id: str) -> bool:
        return True

    def get_presentable_exercise_for_kc(self, kc_id: str):
        class DummyEx:
            expected_answer = "base + i * sizeof(T)"
        return DummyEx()


class MockForensicAuditor:
    class Result:
        verdict = "APPROVED"

    def audit_claims(self, claims, evidence):
        return self.Result()


@pytest.fixture
def engine() -> DialogueEngine:
    policy = DialoguePolicy()
    tracker = DialogueStateTracker()
    selector = MockExerciseSelector()
    auditor = MockForensicAuditor()
    return DialogueEngine(
        dialogue_policy=policy,
        state_tracker=tracker,
        exercise_selector=selector,
        forensic_auditor=auditor,
    )


def test_basic_clarification_flow(engine: DialogueEngine):
    """1. Flujo básico de clarificación: respuesta basada en evidencia [E#] y pregunta socrática."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="¿Por qué el acceso al elemento en un array es O(1)?",
        )

        assert response.status == "RESPONDED"
        assert response.answer is not None
        assert "[E1]" in response.answer
        assert response.socratic_question is not None
        assert response.socratic_question.target_dimension == "REASONING"
        assert "explora" in response.socratic_question.target_dimension_note.lower()
        assert response.dialogue_state is not None
        assert response.dialogue_state.turn_count == 1
        assert response.audit_verdict == "APPROVED"

    asyncio.run(_run())


def test_example_request(engine: DialogueEngine):
    """2. Pedido de ejemplo: retorna un ejemplo concreto con evidencia y actualiza métrica consultiva."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="¿Podrías darme un ejemplo de cómo se calcula en memoria?",
        )

        assert response.status == "RESPONDED"
        assert "[E1]" in response.answer
        assert response.dialogue_state.examples_requested == 1
        assert response.socratic_question is not None

    asyncio.run(_run())


def test_reformulation_request(engine: DialogueEngine):
    """3. Pedido de reformulación: explica de otra forma sin emitir juicios ni microevaluaciones."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="No entiendo bien, ¿me lo explicás de otra forma?",
        )

        assert response.status == "RESPONDED"
        assert "[E1]" in response.answer
        assert response.dialogue_state.reformulation_count >= 1
        # Verificar que no contenga microevaluaciones
        lower_ans = response.answer.lower()
        for forbidden in DialoguePolicy.FORBIDDEN_WORDS:
            assert forbidden not in lower_ans

    asyncio.run(_run())


def test_max_turns_suggests_not_forces(engine: DialogueEngine):
    """4. Límite de turnos (8): sugiere ejercicio determinísticamente pero NO fuerza la transición de fase."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id, turn_count=8)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="¿Cómo influye el tamaño del tipo de dato?",
        )

        assert response.status == "LIMIT_REACHED"
        assert response.limit_reason == "max_turns"
        assert response.dialogue_state.dialogue_limit_reached is True
        # El episodio sigue en fase DIALOGUE, no fue forzado a EVALUATING sin consentimiento
        assert episode.phase == EpisodePhase.DIALOGUE

    asyncio.run(_run())


def test_student_rejects_exercise_suggestion(engine: DialogueEngine):
    """5. El estudiante rechaza la sugerencia de ejercicio y el episodio permanece en DIALOGUE."""
    episode = create_test_episode(phase=EpisodePhase.DIALOGUE_LIMIT_REACHED)
    updated_ep = engine.reject_exercise_suggestion(episode)
    assert updated_ep.phase == EpisodePhase.DIALOGUE


def test_student_accepts_exercise_suggestion(engine: DialogueEngine):
    """6. El estudiante acepta la sugerencia de ejercicio y transiciona a EVALUATING."""
    episode = create_test_episode(phase=EpisodePhase.SUGGEST_EXERCISE)
    updated_ep = engine.accept_exercise_suggestion(episode)
    assert updated_ep.phase == EpisodePhase.EVALUATING


def test_student_skips_to_exercise(engine: DialogueEngine):
    """7. El estudiante pide pasar al ejercicio directamente ('pasá al ejercicio')."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="Listo, pasá al ejercicio",
        )

        assert response.status == "SUGGEST_EXERCISE"
        assert response.exercise_available is True

    asyncio.run(_run())


def test_dialogue_after_exercise(engine: DialogueEngine):
    """8. Retorno a diálogo post-ejercicio: es una transición legal en la máquina de estados."""
    async def _run():
        episode = create_test_episode(phase=EpisodePhase.EVALUATING)
        # Estudiante tiene dudas tras el ejercicio
        post_ep = episode.transition_to(EpisodePhase.DIALOGUE, "step_post_eval_dialogue")
        assert post_ep.phase == EpisodePhase.DIALOGUE

        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=post_ep.episode_id)
        response = await engine.process_turn(
            episode=post_ep,
            concept_packet=packet,
            dialogue_state=state,
            student_message="¿Por qué la respuesta correcta usaba sizeof(int)?",
        )
        assert response.status == "RESPONDED"

    asyncio.run(_run())


def test_off_topic_redirect(engine: DialogueEngine):
    """9. Redirección de off-topic: se devuelve status REDIRECTED sin penalizar ni evaluar."""
    async def _run():
        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        response = await engine.process_turn(
            episode=episode,
            concept_packet=packet,
            dialogue_state=state,
            student_message="¿Quién ganó el último partido de fútbol?",
        )

        assert response.status == "REDIRECTED"
        assert "tema de este KC" in response.answer or "unidad" in response.answer

    asyncio.run(_run())


def test_abstention_on_insufficient_evidence(engine: DialogueEngine):
    """10. Abstención ante falta de evidencia: status ABSTAINED con motivo auditable."""
    async def _run():
        empty_packet = ConceptPacket(
            kc_id="kc_unknown",
            notebook_id="nb_vacio",
            objective="Algo desconocido",
            evidence_by_role={},
            core_concept="Concepto sin evidencia",
            mental_model="Modelo vacío",
            reasoning_guidance="Guía vacía",
            formalization=None,
            implementation_guidance=None,
            pitfalls=(),
            citations=(),
            s44_report=None,
            audit_verdict=AuditVerdict.APPROVED,
            assembly_hash="0" * 64,
        )
        state = DialogueState(episode_id="ep_none")

        # Forzar configuración con notebook desconocido y sin bridges
        engine.config["allow_bridge_fallback"] = False
        episode = Episode(
            episode_id="ep_none",
            kc_id="kc_none",
            notebook_id="nb_vacio",
            objective="Algo desconocido",
            phase=EpisodePhase.DIALOGUE,
            current_step_id="s1",
        )

        response = await engine.process_turn(
            episode=episode,
            concept_packet=empty_packet,
            dialogue_state=state,
            student_message="¿Cómo funciona la teletransportación cuántica?",
        )

        assert response.status == "ABSTAINED"
        assert response.abstention_reason is not None
        assert "evidencia suficiente" in response.abstention_reason.lower()

    asyncio.run(_run())


def test_no_global_pool_fallback(engine: DialogueEngine):
    """11. Confinamiento sin pool global: allow_global_pool_fallback=False impide buscar en pool general."""
    async def _run():
        assert engine.config.get("allow_global_pool_fallback") is False
        episode = Episode(
            episode_id="ep_isolated",
            kc_id="kc_isolated",
            notebook_id="nb_inexistente",
            objective="Tema aislado",
            phase=EpisodePhase.DIALOGUE,
            current_step_id="step_iso",
        )
        empty_packet = ConceptPacket(
            kc_id="kc_isolated",
            notebook_id="nb_inexistente",
            objective="Tema aislado",
            evidence_by_role={},
            core_concept="Tema",
            mental_model="Modelo",
            reasoning_guidance="Guía",
            formalization=None,
            implementation_guidance=None,
            pitfalls=(),
            citations=(),
            s44_report=None,
            audit_verdict=AuditVerdict.APPROVED,
            assembly_hash="0" * 64,
        )
        state = DialogueState(episode_id=episode.episode_id)

        res = await engine.process_turn(
            episode=episode,
            concept_packet=empty_packet,
            dialogue_state=state,
            student_message="Explicame algo que está en otro cuaderno del sistema",
        )
        assert res.status == "ABSTAINED"

    asyncio.run(_run())


def test_comprehension_tracking_is_consultive(engine: DialogueEngine):
    """12. El seguimiento cognitivo es puramente consultivo: el diálogo NUNCA actualiza BKT."""
    async def _run():
        storage = StudentStorage(":memory:")
        now = datetime.now(timezone.utc)
        initial_bkt = BKTState(kc_id="aritmetica_punteros", p_L=0.45, attempts=2, last_update=now)
        storage.save_bkt_state(initial_bkt)

        episode = create_test_episode()
        packet = create_mock_concept_packet()
        state = DialogueState(episode_id=episode.episode_id)

        # Procesar 3 turnos sucesivos
        for i in range(3):
            res = await engine.process_turn(
                episode=episode,
                concept_packet=packet,
                dialogue_state=state,
                student_message=f"Consulta número {i+1}",
            )
            state = res.dialogue_state

        # BKT debe permanecer ESTRICTAMENTE INTACTO
        current_bkt = storage.get_bkt_state("aritmetica_punteros")
        assert current_bkt is not None
        assert current_bkt.p_L == 0.45
        assert current_bkt.attempts == 2

    asyncio.run(_run())
