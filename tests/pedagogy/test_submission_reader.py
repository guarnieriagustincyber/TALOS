"""Unit tests for SubmissionReader and domain exercise auditors."""

from pathlib import Path
import pytest

from study_engine.pedagogy.auditors import (
    FADENAExerciseAuditor,
    ProgrammingExerciseAuditor,
    SOExerciseAuditor,
    TelecomExerciseAuditor,
    get_auditor_for_notebook,
)
from study_engine.pedagogy.submission_reader import SubmissionReader, StudentSubmission


def test_submission_reader_parses_programming_template(tmp_path: Path) -> None:
    doc = """# Ejercicio: es_octeto_valido

## Enunciado
Validar si un entero está entre 0 y 255.

## Contrato Formal
PRE: octeto es un entero
POST: retorna True si 0 <= octeto <= 255, False en caso contrario

## Diagrama de Flujo
```mermaid
flowchart TD
    A[Inicio] --> B{0 <= octeto <= 255?}
    B -->|Sí| C[True]
    B -->|No| D[False]
```

## Pseudocódigo
```
FUNCIÓN es_octeto_valido(octeto)
    SI octeto < 0 O octeto > 255 ENTONCES
        RETORNAR Falso
    FIN SI
    RETORNAR Verdadero
FIN FUNCIÓN
```

## Código Python
```python
def es_octeto_valido(octeto: int) -> bool:
    \"\"\"Valida si un número está en el rango [0, 255].\"\"\"
    return 0 <= octeto <= 255
```

## Tests
```python
assert es_octeto_valido(0) == True
assert es_octeto_valido(255) == True
assert es_octeto_valido(256) == False
assert es_octeto_valido(-1) == False
```
"""
    file_path = tmp_path / "ej_07_es_octeto_valido.md"
    file_path.write_text(doc, encoding="utf-8")

    reader = SubmissionReader()
    sub = reader.parse(file_path)

    assert sub.exercise_id == "ej_07_es_octeto_valido"
    assert sub.title == "es_octeto_valido"
    assert sub.has_section("enunciado")
    assert sub.has_section("contrato_formal")
    assert sub.has_section("diagrama_de_flujo")
    assert sub.has_section("pseudocodigo")
    assert sub.has_section("codigo_python")
    assert sub.has_section("tests")

    code = sub.get_code_block("python", index=0)
    assert "def es_octeto_valido" in code

    tests = sub.get_code_block("python", index=1)
    assert "assert es_octeto_valido(0)" in tests

    # Run programming auditor
    auditor = ProgrammingExerciseAuditor()
    report = auditor.audit(sub)

    assert report.passed is True
    assert report.score >= 80.0
    check_names = {c.name: c.passed for c in report.checks}
    assert check_names["syntax"] is True
    assert check_names["contract"] is True
    assert check_names["diagram"] is True
    assert check_names["pseudocode"] is True
    assert check_names["tests"] is True
    assert check_names["type_hints"] is True


def test_programming_auditor_fails_on_syntax_error(tmp_path: Path) -> None:
    doc = """# Ejercicio: roto

## Enunciado
Test syntax error.

## Código Python
```python
def broken_fn(:
    return 42
```
"""
    file_path = tmp_path / "broken.md"
    file_path.write_text(doc, encoding="utf-8")

    reader = SubmissionReader()
    sub = reader.parse(file_path)

    auditor = ProgrammingExerciseAuditor()
    report = auditor.audit(sub)

    assert report.passed is False
    syntax_check = next(c for c in report.checks if c.name == "syntax")
    assert syntax_check.passed is False
    assert "Error de sintaxis" in syntax_check.feedback


def test_so_auditor_evaluates_state_diagram_and_transitions(tmp_path: Path) -> None:
    doc = """# Ejercicio: estados_proceso

## Enunciado
Modelo de 5 estados de procesos.

## Diagrama de Estados
```mermaid
stateDiagram-v2
    [*] --> New
    New --> Ready: Admitido
    Ready --> Running: Despachado
    Running --> Ready: Preemptado
    Running --> Waiting: Bloqueado por I/O
    Waiting --> Ready: I/O listo
    Running --> Terminated: Exit
    Terminated --> [*]
```

## Explicación de Transiciones
New a Ready cuando el proceso es admitido.
Ready a Running cuando el scheduler despacha la CPU.
Running a Waiting cuando se bloquea en syscall.
Waiting a Ready cuando finaliza la I/O.
Running a Terminated al finalizar la tarea.

## Análisis Crítico
El modelo clásico de 5 estados asume una visión uniprocesador. En sistemas simétricos multiprocesador (SMP) modernos, varios hilos pueden estar en Running al mismo tiempo, requiriendo sincronización y colas por núcleo.
"""
    file_path = tmp_path / "so_test.md"
    file_path.write_text(doc, encoding="utf-8")

    reader = SubmissionReader()
    sub = reader.parse(file_path)

    auditor = SOExerciseAuditor()
    report = auditor.audit(sub)

    assert report.passed is True
    assert report.score >= 75.0


def test_telecom_auditor_evaluates_link_budget(tmp_path: Path) -> None:
    doc = """# Ejercicio: calculo_atenuacion

## Enunciado
Cálculo de enlace óptico de 10 km.

## Fórmulas
```
Atenuacion_total = (alfa * d) + (perdida_conectores * n)
Margen = Ptx - Prx - Atenuacion_total
```

## Cálculos
```
Distancia = 10.0 km
Fibra = 0.2 dB/km * 10 km = 2.0 dB
Conectores = 0.5 dB * 2 = 1.0 dB
Atenuación total = 3.0 dB
Ptx = 2.0 dBm
Prx = -24.0 dBm
Margen = 2.0 - (-24.0) - 3.0 = 23.0 dB
```

## Resultado
Atenuación total: 3.0 dB, margen de potencia resultante: 23.0 dB.

## Análisis
Margen de 23 dB resulta holgado y viable para un estándar FTTH comercial en planta externa.
"""
    file_path = tmp_path / "teleco_test.md"
    file_path.write_text(doc, encoding="utf-8")

    reader = SubmissionReader()
    sub = reader.parse(file_path)

    auditor = TelecomExerciseAuditor()
    report = auditor.audit(sub)

    assert report.passed is True
    assert report.score >= 75.0


def test_fadena_auditor_evaluates_bobbio_essay(tmp_path: Path) -> None:
    doc = """# Ejercicio: analisis_bobbio

## Enunciado
Gobierno de leyes versus gobierno de hombres en Bobbio.

## Tesis Central
Bobbio sostiene que el Estado de derecho se caracteriza por la supremacía indispensable de la ley sobre la voluntad arbitraria de los gobernantes, sometiendo al poder político a normas generales y preexistentes.

## Argumentos

### 1. Legalidad como límite al poder
El poder político se ejerce dentro de las normas jurídicas positivas.

### 2. Generalidad de la norma
Las leyes son abstractas y universales para garantizar igualdad formal ante la ley.

### 3. Publicidad y previsibilidad
Las leyes públicas garantizan seguridad jurídica a los ciudadanos.

## Crítica y Contrapunto
Schmitt plantea que la decisión soberana en estado de excepción trasciende la norma formal, mientras que Bobbio sostiene que incluso la emergencia debe regularse jurídicamente.

## Conclusión
La distinción bobbiana sigue siendo el pilar fundamental para evaluar la calidad democrática del Estado moderno frente al arbitrio del poder político.

## Citas
- Bobbio, Norberto (1995). Estado, gobierno y sociedad, Cap. 2.
- Constitución de la Nación Argentina, Art. 19.
"""
    file_path = tmp_path / "fadena_test.md"
    file_path.write_text(doc, encoding="utf-8")

    reader = SubmissionReader()
    sub = reader.parse(file_path)

    auditor = FADENAExerciseAuditor()
    report = auditor.audit(sub)

    assert report.passed is True
    assert report.score >= 80.0
