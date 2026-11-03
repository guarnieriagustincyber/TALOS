"""H2-A (autorización propietaria 2026-10-21): admisibilidad de observaciones.

Regla aprobada por el propietario para esta intervención focal:

> Una observación solo puede modificar el estado académico de los
> conocimientos que un instrumento autorizado y verificable haya
> evaluado efectivamente.

Este módulo clasifica los resultados de los evaluadores EXISTENTES por su
contrato real (no por el nombre del grader ni por etiquetas como
EXACT_CORRECTOR) y decide si pueden producir efectos académicos
(BKT, dificultades, digest académico, recomendaciones de avance).

Estado vigente tras H2-A (contención; la promoción de un instrumento a
admisible es decisión pendiente del propietario — H9/EP-04):

- keyword_coverage (multi_kc): cobertura léxica de conceptos con alias.
  FEEDBACK ESTRUCTURAL; la presencia de palabras no acredita comprensión
  disciplinar (falso positivo reproducido: explicación conceptualmente
  falsa que contiene todos los alias — .m1_h2a/repro_before.json D3).
- bug_class (debugging): nombra la clase de bug por subcadena de alias,
  sin distinguir mención en negación ni comprobar el vector/parche que el
  propio prompt declara parte de la respuesta (D4). Contenida hasta
  disponer de identificación efectiva inequívoca.
- state_match (trace): predicción de estado final comparada por subcadena
  — acepta "x=10" para esperado "x=1" (D1) y aprueba vacuamente cuando
  todos los campos son simbólicos (D2). Contenida hasta corregir su
  semántica y demostrar comparación inequívoca (autorización H2-A §3).
- Multi-KC (cualquier tipo): resultado global sin atribución discriminante
  por criterio/KC; sin atribución suficiente no hay efectos académicos
  individuales (autorización H2-A §3).

FUERA de esta clasificación (instrumentos exactos que conservan sus
efectos autorizados): ejercicios certificados con clave verificable
(MultiChoiceGrader/ExactMatchGrader contra expected_answer certificada)
y pasos socráticos calificados; sus rutas no pasan por este módulo.

"No evaluable" NO es "incorrecto": la ausencia de observación admisible
no penaliza BKT, dificultades ni repasos (H2-A §3).
"""

from typing import List, NamedTuple, Optional


class GeneratedAdmission(NamedTuple):
    """Decisión de admisibilidad para los efectos académicos de una observación."""

    academic_effects: bool
    reason: str


# Contención por contrato real del oráculo (defectos reproducidos en ruta;
# ver .m1_h2a/repro_before.json).
_NON_ADMISSIBLE_REASONS = {
    "multi_kc": (
        "keyword_coverage: cobertura léxica estructural; la presencia de "
        "alias no acredita comprensión disciplinar"
    ),
    "debugging": (
        "bug_class: coincidencia de alias por subcadena sin identificación "
        "efectiva del mecanismo/vector/parche exigido por el prompt"
    ),
    "trace": (
        "state_match: comparación por subcadena no inequívoca (acepta "
        "valores distintos y aprueba sin criterios evaluables)"
    ),
}


def admit_generated_observation(
    *, kind: Optional[str], kc_ids: Optional[List[str]]
) -> GeneratedAdmission:
    """Clasifica una observación de ejercicio generado para efectos académicos.

    Fail-closed: todo tipo de oráculo conocido queda hoy NO admisible
    (feedback conservado); un tipo desconocido o la ausencia de atribución
    suficiente también producen ``academic_effects=False``.
    """
    reason = _NON_ADMISSIBLE_REASONS.get(kind or "")
    if reason is None:
        return GeneratedAdmission(
            False, f"tipo de oráculo desconocido o sin contrato admisible: {kind!r}"
        )
    kc_count = len(kc_ids or [])
    if kc_count > 1:
        reason = (
            f"{reason}; resultado global distribuido a {kc_count} KCs sin "
            "atribución discriminante por criterio"
        )
    elif kc_count == 0:
        reason = f"{reason}; sin KC atribuible"
    return GeneratedAdmission(False, reason)
