# Gate 2 — Revisión semántica propuesta de GS2-SYN-011…012

**Estado:** propuesta técnica; pendiente de aceptación explícita.  
**Fecha:** 2026-09-28  
**Grupo:** `sintaxis_codigo` / `fork` / `retrieval_citation`.

## Hallazgo principal: colisión léxica con “fork”

Las dos consultas preguntan por la llamada al sistema `fork` en programación
de procesos. Sin embargo, los qrels esperados para ambas incluyen pasajes del
problema de los filósofos comensales, donde *fork* significa cubierto. La
coincidencia de palabra no constituye relevancia semántica para el syscall.

- `GS2-SYN-011` pregunta cómo opera `fork` desde POSIX/Linux. La referencia de
  *Fluent Python* identifica `os.fork()` como API POSIX para lanzar un proceso
  hijo, pero no explica el comportamiento. Una tabla de llamadas de Linux
  solo enumera `fork`. Se proponen ambos como grado 1, no como evidencia
  sustantiva.
- `GS2-SYN-012` pide expresamente parámetros y valores de retorno. Sus cinco
  referencias describen mecanismos de sincronización de los filósofos y sus
  cubiertos; ninguna aporta la firma ni los valores de retorno de `fork(2)`.

## Propuestas por query/qrel

| Consulta | Referencia | Grado histórico | Propuesta | Justificación |
|---|---|---:|---:|---|
| `SYN-011` | `chk_76e248a62974_325_1` | 3 | **0** | Preguntas sobre deadlock y filósofos; cubiertos físicos, no syscall. |
| `SYN-011` | `luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf:p534:c0000` | 2 | **1** | Identifica `os.fork()` como API POSIX que lanza un hijo; no explica operación. |
| `SYN-011` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | **1** | Enumera `fork` entre llamadas Linux; no contiene semántica. |
| `SYN-011` | `chk_76e248a62974_304_1` | 1 | **0** | Monitor para asignar cubiertos en filósofos. |
| `SYN-011` | `chk_76e248a62974_302_1` | 1 | **0** | Semáforos y cubiertos físicos; no creación de procesos. |
| `SYN-012` | `chk_76e248a62974_304_1` | 3 | **0** | Pseudocódigo del monitor de filósofos; no parámetros ni retorno. |
| `SYN-012` | `chk_76e248a62974_302_1` | 2 | **0** | Solución con semáforos al problema de filósofos. |
| `SYN-012` | `chk_76e248a62974_303_1` | 1 | **0** | Continuación del ejemplo de filósofos y monitores. |
| `SYN-012` | `Operating Systems - Internals and Design Principles 7th.pdf:p303:c0002` | 1 | **0** | *Fork* alude explícitamente al cubierto izquierdo/derecho. |
| `SYN-012` | `Operating Systems - Internals and Design Principles 7th.pdf:p304:c0000` | 1 | **0** | Vector de disponibilidad de cubiertos; sin API de procesos. |

## Cobertura de facetas (diagnóstico, umbral ≥2)

Para `SYN-011`, la descomposición analítica distingue identificación
POSIX/Linux y explicación del comportamiento. Ninguna faceta tiene evidencia
con grado propuesto ≥2: nombrar el syscall no basta para explicar cómo opera.

Para `SYN-012`, las dos facetas explícitas son parámetros y valores de retorno.
Ambas quedan descubiertas: todos los candidatos son referencias al problema
de los filósofos. La cobertura solo resume estos juicios individuales; no
decide por sí sola la validez canónica de la consulta o sus qrels.

La diversidad de origen tampoco rescata la cobertura: `SYN-011` tiene tres
`source_id`, pero ninguno llega al umbral sustantivo; las cinco referencias
de `SYN-012` proceden del mismo libro y comparten el mismo desajuste semántico.

## Estado decisional y límites

Las diez propuestas son no canónicas. `canonical_query_decision` y
`canonical_qrel_decisions` permanecen `null`; los qrels históricos siguen
`PENDING`. No se buscó evidencia de reemplazo ni se alteraron el dataset,
qrels, registro explícito o ACL. La evaluación se limitó a leer los pasajes
asociados a estos diez qrels en SQLite read-only; no se ejecutó retrieval.

El [JSON detallado](./gate2_v2400_review_batch_syn_011_012_adjudication_2026-09-28.json)
conserva texto de query, grados, razones, facetas diagnósticas y límites por
referencia.
