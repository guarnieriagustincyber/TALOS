import pytest
from study_engine.tutor.question_type import QuestionType, detect_question_type

@pytest.mark.integration
def test_detect_question_type_greeting():
    assert detect_question_type("Hola, buen día!") == QuestionType.GREETING

@pytest.mark.integration
def test_detect_question_type_curricular():
    assert detect_question_type("¿Qué tema sigue después de redes?") == QuestionType.CURRICULAR

@pytest.mark.integration
def test_detect_question_type_technical():
    assert detect_question_type("Explícame qué es un puntero en C.") == QuestionType.TECHNICAL

@pytest.mark.integration
def test_detect_question_type_meta():
    assert detect_question_type("¿Quién te creó?") == QuestionType.META
