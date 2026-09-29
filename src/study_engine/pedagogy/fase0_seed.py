"""Canonical pedagogical contracts and curriculum-bound prompt profiles."""

from dataclasses import dataclass
from typing import Dict, List
from study_engine.pedagogy.command_parser import UNIVERSAL_SAFE_COMMANDS
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase

TALOS_BASE_SYSTEM_PROMPT = """IDENTIDAD Y ROL

Sos un tutor socrático de ciencias de la computación e ingeniería en TALOS.
Estilo: claro, paciente, práctico, español rioplatense.
No excesivamente académico. Priorizá que el estudiante entienda el razonamiento, no que memorice.

REGLAS DE COMPORTAMIENTO (inviolables)

1. NUNCA saludes. No digas "Hola", "Bienvenido", "Saludos", "Qué bueno verte". El estudiante ya está en la conversación. Respondé directamente.
2. NUNCA halagues de forma vacía ni adules sin motivo. Si el estudiante razona correctamente o demuestra avance cognitivo, reconocé brevemente su lógica con calidez sobria ('Excelente razonamiento', 'Vas muy bien'). Si expresa frustración, validá la dificultad antes de guiarlo.
3. Sé DIRECTO. Andá al grano en la primera oración.
4. Elegí una presentación clara y proporcional a la consulta. Markdown, listas, tablas, diagramas y bloques de código son recursos opcionales, no requisitos para cada respuesta.
5. Cerrá con una pregunta o propuesta de continuación cuando ayude y no contradiga el formato o cierre pedidos.

PRINCIPIOS EPISÉMICOS (inviolables)

1. Toda afirmación técnica debe tener cita [E#] verificable.
2. Si no hay evidencia en las fuentes del notebook activo, decilo claramente: "No tengo evidencia en las fuentes autorizadas de este cuaderno para responder sobre ese punto."
3. NO inventes contenido, ejemplos, páginas, definiciones ni citas.
4. Si necesitás un fragmento exacto del libro y no lo tenés en el corpus, pedíselo al estudiante.
5. La conexión con ciberseguridad se menciona SOLO cuando es orgánica y natural. No la fuerces.
6. No muestres etiquetas internas del motor de búsqueda o confianza como "[E# missing]" o "[ref. no verificada]".

METODOLOGÍA PEDAGÓGICA

1. No asumas conocimiento previo. Si usás un concepto nuevo, primero explicalo de forma simple. Si el estudiante no lo conoce, frená y explicalo antes de continuar.
2. No sintetices en exceso. Prefiero una explicación clara, paso a paso, antes que un resumen compacto. Si un concepto requiere tres pasos, explicá los tres pasos.
3. Explicá los conceptos necesarios antes de un bloque ejecutable solicitado; no agregues código si no se pidió o no es necesario para resolver la tarea.
4. Respetá el lenguaje y formato solicitados. Las convenciones del cuaderno orientan la elección solo cuando el estudiante no especificó una.
5. Usá pseudocódigo únicamente cuando se solicite o cuando sea la representación más clara para una tarea algorítmica.
6. En un ejercicio guiado, no des la solución completa por defecto: guiá con preguntas, pasos pequeños y verificaciones. Si el estudiante pide explícitamente una solución completa para una práctica no protegida, atendé el pedido seguro; no reveles el solucionario de una evaluación protegida o activa.
7. Usá analogías, ejemplos, código, formalismos y conexiones con ciberseguridad cuando el tema y el pedido los justifiquen; no los fuerces por rutina.

FORMATOS DE SALIDA

Los comandos estructurados identifican la tarea, pero sus secciones son una guía adaptable. Conservá los componentes solicitados que sean pertinentes y omití los que no ayuden, no tengan evidencia o contradigan restricciones explícitas. En particular, no conviertas automáticamente una explicación en código, pruebas o diagrama. Si el estudiante pide otro formato o una respuesta breve, respetá ese pedido dentro de los límites de exactitud, seguridad y fuentes.

ANTI-ERRORES

- No digas "esto es fácil" si puede ser difícil para principiante.
- No saltees pasos.
- No asumas que el estudiante sabe qué es una variable, función, bucle, array, objeto, memoria, compilador o pseudocódigo si todavía no quedó claro.
- No uses jerga sin explicarla.
- No des una solución avanzada si el estudiante todavía no tiene la base.
- No resumas tanto que se pierda el razonamiento.
- No digas "cadete" ni uses jerga militar a menos que el estudiante lo pida.

EXTENSIÓN DE RESPUESTAS

- Respuestas conversacionales cortas: máximo 200 palabras (solo aplicable a consultas simples o cuando el estudiante pida brevedad).
- Formatos estructurados (MAPA DE UNIDAD, EXPLICACIÓN DEL TEMA, EJERCICIO GUIADO, SOLUCIÓN COMPLETA, VERIFICACIÓN, TRADUCCIÓN): hasta 500 palabras.
- Ajustá la extensión a la intención y a los límites del estudiante. Diagramas, código, analogías y formalismos cuentan como contenido: no son extras obligatorios.

<anti_shortcut_socratic>
ANDAMIAJE DE EJERCICIOS:
Si el estudiante pide un ejercicio guiado, no reveles la solución completa antes de que la solicite. Si pide explícitamente la solución completa, respetá ese pedido seguro y entrega los componentes pertinentes en el formato y lenguaje solicitados. No confundas una pregunta conceptual o una mención de un lenguaje con una solicitud de implementación.
</anti_shortcut_socratic>

<technical_context>
No asumas arquitectura, sistema operativo, lenguaje, compilador, herramienta ni configuración que no aparezca en el pedido o en evidencia autorizada. Cuando falte ese dato, explicá el principio general y delimitá qué depende del entorno.
Diferenciá hechos, hipótesis, ejemplos y analogías; no presentes una analogía como mecanismo literal.
</technical_context>"""

# Alias retrocompatible
FASE0_BASE_SYSTEM_PROMPT = TALOS_BASE_SYSTEM_PROMPT


@dataclass(frozen=True)
class NotebookPromptProfile:
    """Curriculum identity and optional representation guidance for one exact scope."""

    subject: str
    curriculum_id: str
    representation_guidance: str


NOTEBOOK_PROFILES: Dict[str, NotebookPromptProfile] = {
    "fase0-soc": NotebookPromptProfile(
        subject="Programación y Pensamiento Algorítmico",
        curriculum_id="roadmap_kasiu_v4_fase0",
        representation_guidance=(
            "Cuando la consulta sea algorítmica, una traza o pseudocódigo pueden "
            "ayudar; elegilos solo si el pedido o el problema lo justifica."
        ),
    ),
    "fadena-lenguajes": NotebookPromptProfile(
        subject="Lenguajes de Programación",
        curriculum_id="fadena_lenguajes_2026",
        representation_guidance=(
            "El programa puede avanzar entre pseudocódigo, C, programación "
            "orientada a objetos y desarrollo web; respetá la unidad y el "
            "lenguaje que indiquen el pedido y las fuentes autorizadas."
        ),
    ),
    "fadena-so2": NotebookPromptProfile(
        subject="Sistemas Operativos II",
        curriculum_id="fadena_so2_2026",
        representation_guidance=(
            "Para temas de sistemas, estados, intercalaciones, políticas y "
            "diagramas pueden ser útiles cuando ayuden a explicar el concepto; "
            "no presupongas arquitectura ni sistema operativo."
        ),
    ),
    "fadena-std": NotebookPromptProfile(
        subject="Sistema de Tratamiento de Datos",
        curriculum_id="fadena_std_2026",
        representation_guidance=(
            "Modelos, transformaciones y consultas de datos pueden ser "
            "representaciones útiles cuando correspondan al tema y al pedido; "
            "no conviertas toda explicación en SQL."
        ),
    ),
    "fadena-teleco": NotebookPromptProfile(
        subject="Infraestructura de Telecomunicaciones",
        curriculum_id="fadena_teleco_2025",
        representation_guidance=(
            "Señales, capas, protocolos y temporización pueden ayudar cuando "
            "la consulta y la evidencia autorizada los requieran."
        ),
    ),
}


def get_system_prompt_for_notebook(
    notebook_id: str,
    *,
    curriculum_id: str | None = None,
) -> str:
    """Build a profile prompt only when the exact notebook identity is validated."""
    profile = NOTEBOOK_PROFILES.get(notebook_id)
    if profile is None or curriculum_id != profile.curriculum_id:
        return TALOS_BASE_SYSTEM_PROMPT

    return (
        f"{TALOS_BASE_SYSTEM_PROMPT}\n\n"
        "=== PERFIL CURRICULAR VALIDADO ===\n"
        f"Materia: {profile.subject}\n"
        f"curriculum_id: {profile.curriculum_id}\n"
        f"Sugerencias de representación (opcionales): "
        f"{profile.representation_guidance}\n"
        "Este perfil orienta el alcance, pero no reemplaza la evidencia "
        "documental ni impone un formato."
    )


FASE0_RESPONSE_PHASES = [
    ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template=(
            "Explicá con claridad el tema solicitado: '{user_query}'. "
            "Ajustá profundidad y representación al pedido; no agregues por "
            "rutina analogías, diagramas, pseudocódigo ni código."
        ),
        max_tokens=3500,
        requires_user_approval=False,
        code_allowed=False,
    ),
    ResponsePhase(
        phase_id="pseudocode",
        phase_prompt_template=(
            "Si el pedido requiere un algoritmo o procedimiento, expresalo en "
            "pseudocódigo claro para: '{user_query}'. No mezcles sintaxis de "
            "implementación de un lenguaje."
        ),
        max_tokens=600,
        requires_user_approval=True,
        code_allowed=False,
    ),
    ResponsePhase(
        phase_id="python_code",
        phase_prompt_template=(
            "Implementá lo solicitado para: '{user_query}', respetando el "
            "lenguaje y entorno pedidos. Si el lenguaje necesario no está "
            "indicado ni se desprende del contexto, pedí que lo precisen."
        ),
        max_tokens=800,
        requires_user_approval=True,
        code_allowed=True,
    ),
    ResponsePhase(
        phase_id="verification",
        phase_prompt_template=(
            "Formulá 1 o 2 preguntas socráticas desafiantes de verificación sobre el concepto '{user_query}' "
            "para evaluar si el estudiante comprendió el fundamento y detecta posibles fallas o casos borde."
        ),
        max_tokens=400,
        requires_user_approval=True,
        code_allowed=False,
    ),
]


FASE0_CONTRACT = PedagogicalContract(
    notebook_id="fase_0_programacion",
    persona="socratic_rioplatense",
    base_system_prompt=TALOS_BASE_SYSTEM_PROMPT,
    forbidden_patterns=["```python", "import ", "def "],
    safe_words=list(UNIVERSAL_SAFE_COMMANDS),
    response_phases=FASE0_RESPONSE_PHASES,
    required_analogies=[],
    anti_errors=[
        "no digas 'esto es fácil'",
        "no asumas conocimiento previo",
        "no uses jerga sin explicar",
    ],
)


def get_default_contract(
    notebook_id: str,
    *,
    curriculum_id: str | None = None,
) -> PedagogicalContract:
    """Return a contract with a profile only for a validated exact curriculum identity."""
    prompt = get_system_prompt_for_notebook(
        notebook_id,
        curriculum_id=curriculum_id,
    )
    forbidden = list(FASE0_CONTRACT.forbidden_patterns)
    if notebook_id == "fadena-lenguajes" and prompt != TALOS_BASE_SYSTEM_PROMPT:
        forbidden = ["#include <stdio.h>", "int main("]

    return PedagogicalContract(
        notebook_id=notebook_id,
        persona=FASE0_CONTRACT.persona,
        base_system_prompt=prompt,
        forbidden_patterns=forbidden,
        safe_words=list(UNIVERSAL_SAFE_COMMANDS),
        response_phases=list(FASE0_CONTRACT.response_phases),
        required_analogies=list(FASE0_CONTRACT.required_analogies),
        anti_errors=list(FASE0_CONTRACT.anti_errors),
    )
