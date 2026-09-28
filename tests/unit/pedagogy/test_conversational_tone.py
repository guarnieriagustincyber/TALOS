"""Unit tests for Pedagogical Tone and Empathetic Scaffolding (Roadmap v1.1 Fase 4).

Covers:
- T1: Invariant preservation (non-empty praise without flattery).
- T2: Frustration detectors (Argentine expressions + density fallback >= 2).
- T3: Student reasoning attempt detection (conditional/deductive hypotheses).
- T4: Metacognitive scaffolding integration (alta, baja, moderada).
- T5: Canonical 3-part response validation helper and pipeline prompt injection.
"""

import pytest

from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.fase0_seed import TALOS_BASE_SYSTEM_PROMPT, get_default_contract
from study_engine.pedagogy.prompts import (
    PedagogicalToneDirective,
    build_pedagogical_tone_directive,
    detect_student_frustration,
    detect_student_reasoning_attempt,
    validate_three_part_structure,
)
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import PhaseHistory, StructuredResponsePipeline


class TestFrustrationDetection:
    """Tests for student frustration, confusion, and blockage detection (T2)."""

    @pytest.mark.parametrize(
        "query",
        [
            "no entiendo nada de esto",
            "no cacho cómo funciona el stack",
            "no pesco la diferencia entre puntero y valor",
            "este tema me tiene podrido",
            "es un quilombo la paginación",
            "es un lío bárbaro entender el TLB",
            "estoy hasta las manos con los registros",
            "estoy bloqueado con el ejercicio",
            "no me sale la función recursiva",
            "no le encuentro la vuelta a los punteros dobles",
            "me explotó la cabeza con el segmentation fault",
            "me hice un lío con las banderas de condición",
        ],
    )
    def test_explicit_frustration_patterns(self, query: str) -> None:
        assert detect_student_frustration(query) is True

    def test_density_fallback_detection(self) -> None:
        # No single regex pattern, but 2+ negative/difficulty words
        query = "este ejercicio es muy dificil y complicado"
        assert detect_student_frustration(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "¿Qué es un puntero en C?",
            "Explicame la arquitectura x86",
            "¿Cuáles son los registros de propósito general?",
            "RESUMEN UNIDAD 3",
            "dame un ejemplo de bucle for",
        ],
    )
    def test_non_frustration_queries(self, query: str) -> None:
        assert detect_student_frustration(query) is False


class TestReasoningDetection:
    """Tests for student reasoning and active deduction detection (T3)."""

    @pytest.mark.parametrize(
        "query",
        [
            "si el puntero apunta a NULL entonces el kernel lanza SIGSEGV",
            "si incremento el puntero en 1 entonces avanza 4 bytes por ser int?",
            "por lo tanto el buffer no puede desbordar",
            "eso significa que la pila crece hacia direcciones menores de memoria",
            "o sea que el registro RAX almacena el valor de retorno",
            "entonces el compilador alineó la estructura a 8 bytes?",
            "entonces el registro rsp apunta al tope del marco de pila",
        ],
    )
    def test_active_reasoning_patterns(self, query: str) -> None:
        assert detect_student_reasoning_attempt(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "¿Será que esto funciona?",
            "¿Qué hace el registro RBP?",
            "No entiendo la diferencia",
            "¿Podrías darme un ejemplo?",
            "¿Por qué falla el programa?",
        ],
    )
    def test_non_reasoning_direct_questions(self, query: str) -> None:
        # Simple questions without conditional/deductive structure must NOT trigger reasoning praise
        assert detect_student_reasoning_attempt(query) is False


class TestToneDirectiveBuilder:
    """Tests for pedagogical tone directive generation and metacognitive integration (T4)."""

    def test_frustration_directive_injection(self) -> None:
        directive = build_pedagogical_tone_directive("no entiendo nada, me tiene podrido este tema")
        assert "EMPATÍA ANTE DIFICULTAD" in directive
        assert "USO CUIDADOSO DE ANALOGÍAS" in directive
        assert "solo si aclara el mecanismo" in directive
        assert "RIGOR EPISTÉMICO MANDATORIO" in directive
        assert "CONTEXTO Y ALCANCE DE AFIRMACIONES TÉCNICAS" in directive

    def test_reasoning_directive_injection(self) -> None:
        directive = build_pedagogical_tone_directive(
            "si el puntero apunta a NULL entonces el programa crashea con SIGSEGV"
        )
        assert "RECONOCIMIENTO Y CALIDEZ" in directive
        assert "Excelente razonamiento" in directive
        assert "RIGOR EPISTÉMICO MANDATORIO" in directive

    def test_metacognitive_high_dependency(self) -> None:
        profile = {"classification": "alta"}
        directive = build_pedagogical_tone_directive("¿cómo resuelvo esto?", metacognitive_profile=profile)
        assert "ALTA DEPENDENCIA" in directive
        assert "no reveles la solución directa" in directive

    def test_metacognitive_autonomous_student(self) -> None:
        profile = {"classification": "baja"}
        directive = build_pedagogical_tone_directive("¿cómo resuelvo esto?", metacognitive_profile=profile)
        assert "ESTUDIANTE AUTÓNOMO" in directive
        assert "desafiante" in directive

    def test_epistemic_rigor_always_present(self) -> None:
        directive = build_pedagogical_tone_directive("¿qué es una variable?")
        assert "RIGOR EPISTÉMICO MANDATORIO" in directive
        assert "[E#]" in directive


class TestThreePartStructureValidator:
    """Tests for response structure validation helper (T5)."""

    def test_valid_three_part_response(self) -> None:
        valid_response = (
            "Excelente razonamiento sobre el comportamiento del puntero en la memoria.\n\n"
            "Un puntero en lenguaje C almacena la dirección de memoria de una variable [E1]. "
            "Cuando se desreferencia con el operador '*', se accede directamente al contenido "
            "alojado en dicha celda de memoria física [E2].\n\n"
            "¿Qué ocurriría en la memoria si modificamos el valor apuntado sin reasignar la dirección?"
        )
        assert validate_three_part_structure(valid_response) is True

    def test_invalid_missing_socratic_question(self) -> None:
        no_question = (
            "Vas muy bien encaminado con la deducción.\n\n"
            "El puntero almacena la dirección de memoria según K&R [E1]."
        )
        assert validate_three_part_structure(no_question) is False

    def test_invalid_missing_citation(self) -> None:
        no_citation = (
            "Muy bien pensado.\n\n"
            "El puntero contiene una dirección de memoria y permite indirección directa.\n\n"
            "¿Tiene sentido esta distinción?"
        )
        assert validate_three_part_structure(no_citation) is False

    def test_invalid_single_paragraph(self) -> None:
        single_p = "Excelente deducción: el puntero guarda la dirección [E1]. ¿Tiene sentido?"
        assert validate_three_part_structure(single_p) is False


class TestPipelinePromptToneInjection:
    """Tests for pipeline build_phase_prompt integration with tone directives."""

    def test_pipeline_injects_frustration_and_warmth_rules(self) -> None:
        contract = get_default_contract("fadena-lenguajes")
        pipeline = StructuredResponsePipeline(contract=contract, llm_backend=None, phase_history=PhaseHistory())
        phase = ResponsePhase(phase_id="conceptual", phase_prompt_template="Tema: {user_query}", max_tokens=600)

        # 1. Frustration query
        prompt_frustrated = pipeline.build_phase_prompt(phase, "no cacho nada, me tiene podrido este tema")
        assert "NUNCA halagues de forma vacía" in prompt_frustrated
        assert "EMPATÍA ANTE DIFICULTAD" in prompt_frustrated
        assert "USO CUIDADOSO DE ANALOGÍAS" in prompt_frustrated
        assert "no la presentes como mecanismo literal" in prompt_frustrated.lower()

        # 2. Structured deduction query
        prompt_reasoning = pipeline.build_phase_prompt(
            phase, "si el puntero apunta a NULL entonces el kernel lanza SIGSEGV"
        )
        assert "NUNCA halagues de forma vacía" in prompt_reasoning
        assert "RECONOCIMIENTO Y CALIDEZ" in prompt_reasoning
        assert "Excelente razonamiento" in prompt_reasoning

        # 3. Metacognitive high dependency passed
        prompt_meta = pipeline.build_phase_prompt(
            phase, "¿qué es un puntero?", metacognitive_profile={"classification": "alta"}
        )
        assert "ALTA DEPENDENCIA" in prompt_meta
