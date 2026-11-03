"""M1-04b: normalización determinista de atribuciones genéricas.

Autorización propietaria (M1-04b) acotada: transformación aplicada a la
respuesta candidata ANTES del ClaimExtractor y de S4.4, sobre el mismo texto
que luego se audita y se presenta al estudiante (idénticos por construcción:
el pipeline ya emite el contenido pedagógico sólo tras el veredicto).

Defecto que corrige: el generador envuelve hechos técnicos verbatim en un
marco meta "las fuentes definen/establecen/mencionan que...". El fragmento
citado contiene el hecho técnico, no la atribución meta, por lo que el juez
NLI (temperature=0, estable ante bytes idénticos — ver
.m1_04b/judge_variance_results.json) marca NOT_ENTAILED con el rationale
"no menciona que las 'fuentes autorizadas' establezcan dicha definición".

Contrato:
  - El texto auditado == el texto presentado (por diseño del pipeline).
  - El texto original se preserva aparte para trazabilidad; nunca sustituye
    al texto auditado.
  - Sólo transformación permitida: eliminar la envoltura de atribución
    genérica ("<sujeto-fuente> <verbo declarativo> que ") en oraciones
    factuales con tag [E#], preservando byte-a-byte discurso ("Sin
    embargo," etc.), proposición, tags, signos y separadores.
  - NO modifica negaciones, cantidades, modalidad, condiciones,
    comparaciones, citas literales ni el alcance. Ante ambigüedad: NO
    transforma (fail-closed conservador).
  - No forma parte de S4.4; no altera el juez NLI; no agrega hechos; no
    regenera contenido.
"""

import re
from typing import List, NamedTuple, Tuple


# Sujetos-fuente genéricos (el núcleo que SÍ se elimina).
_CORE = r"(?:las\s+fuentes?|la\s+evidencia|el\s+material|los\s+autores|el\s+documento|los\s+documentos)"
_COMPLEMENTOS = (
    r"(?:\s+(?:autorizad[oa]s?|disponibl(?:e|es)|de\s+este\s+cuaderno|"
    r"del\s+cuaderno|del\s+notebook|de\s+este\s+notebook|del\s+módulo|"
    r"del\s+tema|del\s+corpus))*?"
)
# Entre sujeto y verbo sólo pasan estos conectores (lista blanca cerrada;
# un "no", modal o futuro fuera de lista impide el match => sin transformar).
_CONECTORES = r"(?:\s+(?:s[íi]|tambi[ée]n))*?"
# Verbos declarativos 3ª persona (indicativo; sin negación/modal/futuro).
_VERBOS = (
    r"defin(?:e|en)|establec(?:e|en)|mencion(?:a|an)|afirm(?:a|an)|"
    r"indic(?:a|an)|refier(?:e|en)|se[ñn]al(?:a|an)|rese[ñn]a(?:n)?|"
    r"describ(?:e|en)"
)
_DISCURSO = r"(?:(?:Sin\s+embargo|No\s+obstante|Ahora\s+bien|De\s+hecho|En\s+efecto),\s*)?"

# Inicio de oración: arranque del texto o separador tras puntuación/salto.
# El separador se captura y re-emite (preservación byte 1:1).
_BOUNDARY = r"(?P<pre>\A|(?<=[.!?…\n])\s+)"
# Tags [E#] leading OPCIONALES entre el límite y el discurso (protocolo de
# citas: tag al inicio de la oración; se preservan íntegros).
_TAGS0 = r"(?P<tags0>(?:\s*\[\s*[Ee]\s*\d+\s*\]\s*)?)"

# Patrón del marco transformable. La proposición va de \" que \" hasta el
# final de la oración (sin cruzar puntuación ni saltos).
_FRAME_RE = re.compile(
    rf"{_BOUNDARY}{_TAGS0}"
    rf"(?P<discurso>{_DISCURSO})"
    rf"(?P<nucleo>{_CORE}{_COMPLEMENTOS}{_CONECTORES}\s+"
    rf"(?P<verbo>{_VERBOS})\s+que\s+)"
    r"(?P<proposicion>[^.!?…\n]+)",
    re.IGNORECASE,
)

_TAG_RE = re.compile(r"\[[Ee]\s*\d+\]")
_QUOTE_CHARS = ("«", "»", '"', '"', "‹", "›")


class AttributionTransform(NamedTuple):
    """Registro de trazabilidad de una transformación aplicada."""

    before: str
    after: str
    removed: str  # bytes eliminados (discurso NO; sujeto-fuente + verbo + "que")


def normalize_attribution_frames(text: str) -> Tuple[str, List[AttributionTransform]]:
    """Elimina marcos de atribución genérica en oraciones factuales con tag.

    Devuelve (texto_normalizado, registros). El texto cambia SOLO por
    eliminación de la envoltura; discurso, proposición, tags [E#], signos y
    separadores se preservan byte-a-byte. Sin matches válidos => texto
    idéntico de vuelta (idempotencia trivial).
    """
    if not text or not _TAG_RE.search(text) or " que " not in text.lower():
        return text, []

    transforms: List[AttributionTransform] = []

    def _repl(m: "re.Match[str]") -> str:
        discurso = m.group("discurso") or ""
        tags0 = m.group("tags0") or ""
        prop = m.group("proposicion").strip()
        # Condiciones conservadoras por match:
        if (
            not prop
            or not (_TAG_RE.search(prop) or tags0.strip())  # factuales con tag [E#]
            or any(ch in prop for ch in _QUOTE_CHARS)  # citas literales intactas
        ):
            return m.group(0)
        # capitalización de arranque de oración (sólo el primer carácter;
        # la proposición técnica permanece intacta en lo demás)
        after = f"{discurso}{prop}"
        if prop and not prop.startswith("["):
            after = f"{discurso}{prop[0].upper()}{prop[1:]}"
        transforms.append(
            AttributionTransform(
                before=m.group(0).strip(),
                after=after,
                removed=m.group("nucleo").strip(),
            )
        )
        return f"{m.group('pre')}{tags0}{after}"

    try:
        normalized = _FRAME_RE.sub(_repl, text)
    except Exception:
        # fail-closed: sin transformación ante cualquier anomalía
        return text, []
    return normalized, transforms
