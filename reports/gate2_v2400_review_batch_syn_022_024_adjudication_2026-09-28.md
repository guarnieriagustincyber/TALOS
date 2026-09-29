# Gate 2 — Revisión semántica propuesta de GS2-SYN-022…024

**Estado:** propuesta técnica; pendiente de aceptación explícita.  
**Fecha:** 2026-09-28  
**Grupo:** `sintaxis_codigo` / `dup2` / `retrieval_citation`.

## Qué evidencia contienen realmente los qrels

Los cuatro chunks únicos provienen de dos páginas de Stallings:

- *Computer Security: Principles and Practice*, p. 301, enumera `dup2`
  entre llamadas Linux monitoreadas en un cuadro sobre detección de
  intrusiones.
- *Operating Systems: Internals and Design Principles*, p. 760, incluye
  `dup2` en la lista de instrucciones de una simulación educativa UNIX
  Fork-pipe.

Cada página aparece además en una extracción fragmentaria equivalente. Esos
pares de referencias repiten la misma mención: no son cuatro explicaciones ni
cuatro piezas independientes. Ninguno de los pasajes describe duplicación de
descriptores, sintaxis/argumentos o valores de retorno.

## Propuestas por query/qrel

| Consulta | Referencia | Grado histórico | Propuesta | Lectura |
|---|---|---:|---:|---|
| `SYN-022` | `chk_0aa9aa4cc0b2_301_1` | 3 | **1** | Identifica `dup2` como syscall Linux; el cuadro no da semántica. |
| `SYN-022` | `chk_76e248a62974_760_1` | 2 | **1** | Aparece como instrucción de una simulación, sin explicación. |
| `SYN-022` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | **1** | Fragmento solapado de la misma lista de simulación. |
| `SYN-022` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | **1** | Fragmento solapado de la tabla de syscalls. |
| `SYN-023` | `chk_0aa9aa4cc0b2_301_1` | 3 | **1** | Nombra la llamada, no su operación POSIX/Linux. |
| `SYN-023` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 2 | **1** | Solo confirma el nombre y solapa con el chunk completo. |
| `SYN-023` | `chk_76e248a62974_760_1` | 1 | **1** | Lista la llamada como instrucción simulada. |
| `SYN-023` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | **1** | Fragmento de la misma tabla/lista, sin corroboración explicativa. |
| `SYN-024` | `chk_0aa9aa4cc0b2_301_1` | 3 | **1** | No contiene parámetros ni retornos. |
| `SYN-024` | `chk_76e248a62974_760_1` | 2 | **1** | No contiene firma ni contrato de retorno. |
| `SYN-024` | `Operating Systems - Internals and Design Principles 7th.pdf:p760:c0000` | 1 | **1** | Repite la mención de la simulación; no añade detalles API. |
| `SYN-024` | `Computer_Security_Stallings_3rd_Ed.pdf:p301:c0000` | 1 | **1** | La lista de syscalls no informa parámetros ni retornos. |

Se conserva grado 1 en cada par porque el pasaje menciona efectivamente la
llamada y aporta contexto de identificación, pero no satisface la pregunta
completa. El mismo chunk se calificó independientemente contra cada
formulación: su pertinencia no se convierte por repetición en evidencia
sustantiva.

## Cobertura analítica de facetas (umbral ≥2)

- **SYN-022:** quedan descubiertas operación de `dup2` y sintaxis/contrato.
- **SYN-023:** quedan descubiertas operación POSIX/Linux y efecto sobre
  descriptores.
- **SYN-024:** quedan descubiertos parámetros exactos y valores de retorno.

La pertenencia a ACL y la identificación léxica de una llamada no cubren
ninguna de esas dimensiones al umbral sustantivo. El cálculo es un diagnóstico
de facetas; no decide canonicidad.

## Estado y límites

Las doce propuestas siguen no canónicas; las decisiones canónicas de consulta
y qrel quedan vacías. No se modificaron golden set, qrels históricos,
registro explícito ni ACL. La revisión leyó solo los cuatro chunks asociados
en SQLite read-only, sin buscar evidencia de reemplazo ni ejecutar retrieval.

El [JSON detallado](./gate2_v2400_review_batch_syn_022_024_adjudication_2026-09-28.json)
registra propuestas independientes por query/qrel, facetas y límites.
