"""M1-04: contrato de generación sin atribución meta en oraciones citadas.

Propiedad: el CITATION_PROTOCOL_BLOCK y el prompt base ordenan afirmar los
hechos directamente y prohíben el marco de atribución a las fuentes
("Las fuentes autorizadas definen que..." dentro de una oración con tag).
La auditoría NLI rechaza ese marco como UNSUPPORTED_GENERALIZATION porque
el fragmento citado contiene el hecho técnico, no la atribución meta.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from study_engine.context.c3_budget import estimate_payload_tokens
from study_engine.pedagogy.fase0_seed import TALOS_BASE_SYSTEM_PROMPT
from study_engine.pedagogy.structured_pipeline import CITATION_PROTOCOL_BLOCK


def test_protocolo_prohibe_atribucion_meta_en_oracion_citada():
    assert "no la atribuyas a las fuentes" in CITATION_PROTOCOL_BLOCK
    # contraejemplo literal que causó los rechazos c2 (M1-03)
    assert "Mal: '[E1] Las fuentes autorizadas definen que malloc...'" in (
        CITATION_PROTOCOL_BLOCK
    )
    # ejemplo correcto
    assert "Bien: '[E1] malloc devuelve...'" in CITATION_PROTOCOL_BLOCK


def test_protocolo_mantiene_instrucciones_nucleo():
    # tag-LEADING y oración independiente de ausencia (contratos M1-03)
    assert "AL INICIO de cada oración factual" in CITATION_PROTOCOL_BLOCK
    assert "oración SEPARADA y SIN tags" in CITATION_PROTOCOL_BLOCK
    assert "PROTOCOLO DE CITAS OBLIGATORIO" in CITATION_PROTOCOL_BLOCK


def test_prompt_base_afirma_hecho_directo():
    assert "afirmarse como hecho directo" in TALOS_BASE_SYSTEM_PROMPT
    assert "('Las fuentes definen que...')" in TALOS_BASE_SYSTEM_PROMPT
    # plantilla de abstención intacta (test_socratic_system_prompt cubre substring;
    # aquí se verifica que la regla 2 completa no fue alterada)
    assert (
        'decilo claramente: "No tengo evidencia en las fuentes autorizadas de '
        'este cuaderno para responder sobre ese punto."'
    ) in TALOS_BASE_SYSTEM_PROMPT


def test_protocolo_no_infla_presupuesto_c3():
    # correlato de contrato: el bloque debe permanecer compacto; la corrección
    # M1-04 costó +4 tokens sobre la versión M1-03 (369 → 373)
    assert estimate_payload_tokens("", CITATION_PROTOCOL_BLOCK) <= 380


_EV = (
    "[E1] Fuente: FADeNA - Metodologia (Pág: 22):\n"
    '"Un array, o arreglo en Latinoamérica, es una secuencia de posiciones de '
    "la memoria central a las que se puede acceder directamente, que contiene "
    "datos del mismo tipo y que pueden ser seleccionados individualmente "
    'mediante el uso de subíndices. Además se encuentran almacenados en la '
    'memoria principal."\n'
    '[E2] Fuente: K&R (Pág: 77):\n'
    '"sizeof calcula el tamaño en bytes de un objeto del tipo especificado."'
)


def test_preformulado_encierra_hecho_directo_de_pieza_mas_afin():
    from study_engine.pedagogy.structured_pipeline import _direct_assertion_lines

    q = (
        "Expliqué qué es el comportamiento indefinido al acceder fuera de "
        "los límites de un arreglo en C."
    )
    q = q.replace("Expliqué", "Explicá")
    out = _direct_assertion_lines(_EV, q)
    assert out.startswith("=== MODELO DE ENUNCIADO DIRECTO CON CITA")
    assert "[E1] Un array, o arreglo en Latinoamérica, es una secuencia" in out
    # control positivo del chunk ajeno a la consulta: elección determinista
    q2 = "¿Cómo funciona la aritmética de punteros y por qué p+1 avanza sizeof(T) bytes?"
    out2 = _direct_assertion_lines(_EV, q2)
    assert "[E2] sizeof calcula el tamaño" in out2


def test_preformulado_sin_evidencia_o_sin_candidato_devuelve_vacio():
    from study_engine.pedagogy.structured_pipeline import _direct_assertion_lines

    assert _direct_assertion_lines("", "consulta") == ""
    assert _direct_assertion_lines("[Programa Oficial]: unidades", "consulta") == ""


def test_preformulado_no_duplica_encabezado_de_fuente():
    from study_engine.pedagogy.structured_pipeline import _direct_assertion_lines

    out = _direct_assertion_lines(_EV, "Explicá comportamiento indefinido con arreglos")
    assert "FADeNA - Metodologia" not in out  # el encabezado no entra al modelo
    assert out.count("[E") == 1  # exactamente una oración con un tag
