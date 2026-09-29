# Gate 2 — Revisión semántica propuesta de GS2-SYN-026…028

**Estado:** propuesta técnica; pendiente de aceptación explícita.  
**Fecha:** 2026-09-28  
**Grupo:** `sintaxis_codigo` / `pthread_create` / `retrieval_citation`.

## Hallazgo principal

El pasaje de la página 218 es la evidencia sustantiva del lote: muestra una
invocación de `pthread_create`, describe que el tercer argumento es la rutina
de inicio, indica cero/no-cero para éxito/fallo y explica cuándo termina el
hilo. El chunk completo y su fragmento p218 son extracciones solapadas de una
misma página, no corroboración independiente.

Las otras referencias tienen cobertura más limitada:

- La página 606 explica que eCos puede implementar funciones POSIX como
  `pthread_create` mediante paquetes de compatibilidad, sin detallar la API.
- La página 760 solo enumera `pthread_create` como instrucción de una
  simulación.
- Las referencias de páginas 218 y 606 aparecen como chunks completos y como
  fragmentos de página; se calificaron individualmente, pero no se contaron
  como nuevas fuentes.

## Propuestas por query/qrel

| Consulta | Referencia | Grado histórico | Propuesta | Lectura |
|---|---|---:|---:|---|
| `SYN-026` | `chk_76e248a62974_606_1` | 3 | **1** | Contexto de compatibilidad eCos/POSIX; no explica sintaxis ni operación. |
| `SYN-026` | `chk_76e248a62974_760_1` | 2 | **1** | Mención en una lista de simulación. |
| `SYN-026` | `chk_76e248a62974_218_1` | 1 | **3** | Ejemplo directo con creación, argumentos, retorno y ciclo de la rutina. |
| `SYN-026` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 1 | **1** | Fragmento solapado del contexto eCos; sin detalle nuevo de API. |
| `SYN-026` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | **2** | Fragmento que explica rutina de inicio y retorno, pero con menos contexto que el chunk completo. |
| `SYN-027` | `chk_76e248a62974_606_1` | 3 | **1** | Identifica una capa de compatibilidad POSIX en eCos, no la operación solicitada. |
| `SYN-027` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 2 | **1** | Extracción de la misma explicación eCos; no es evidencia Linux específica. |
| `SYN-027` | `chk_76e248a62974_760_1` | 1 | **1** | Mención en la lista de instrucciones simuladas. |
| `SYN-027` | `chk_76e248a62974_218_1` | 1 | **2** | Explica creación, rutina y retorno, aunque no desarrolla detalles de implementación Linux. |
| `SYN-027` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | **2** | Apoya rutina/retorno; solapa con la explicación completa de p218. |
| `SYN-028` | `chk_76e248a62974_760_1` | 3 | **1** | La lista no aporta parámetros ni valores de retorno. |
| `SYN-028` | `chk_76e248a62974_606_1` | 2 | **1** | Contexto POSIX/eCos sin firma ni contrato de retorno. |
| `SYN-028` | `chk_76e248a62974_218_1` | 1 | **2** | Muestra los cuatro argumentos y cero/no-cero, pero no explica todos los parámetros ni enumera códigos de error. |
| `SYN-028` | `Operating Systems - Internals and Design Principles 7th.pdf:p606:c0003` | 1 | **1** | Fragmento eCos solapado; sin datos de parámetros/retorno. |
| `SYN-028` | `Operating Systems - Internals and Design Principles 7th.pdf:p218:c0001` | 1 | **2** | Explica el tercer argumento y retorno cero/no-cero; no detalla los cuatro parámetros. |

## Cobertura diagnóstica por facetas (umbral ≥2)

- **SYN-026:** la invocación y el comportamiento de creación/rutina quedan
  respaldados por el pasaje completo de p218.
- **SYN-027:** creación/rutina y convención de retorno tienen apoyo
  sustantivo en p218; esto no demuestra detalles de implementación Linux.
- **SYN-028:** la forma de llamada y la distinción éxito/fallo tienen apoyo
  parcial. El texto no da tipos/semántica de los cuatro parámetros ni
  valores de error enumerados; cobertura no equivale a exhaustividad.

La v0.1 de relaciones se usó solo para triage: por consulta produjo diez pares
con señal amplia de fuente compartida; dos pares por consulta corresponden a
las extracciones de la misma fuente/página 606 y 218. No produjo pares
`REVIEW_POSSIBLE_DUPLICATE`. Ninguna señal modificó los grados propuestos.

## Estado y límites

Las quince propuestas siguen no canónicas y cada query permanece
`PENDING_ADJUDICATION`. Todas las referencias están en la ACL activa, pero
eso no decide relevancia. Los cinco chunks por consulta pertenecen al mismo
libro/autor; las extracciones de páginas iguales no cuentan como
corroboración independiente.

No se modificaron golden set, qrels históricos, registro explícito o ACL; no
se buscó evidencia de reemplazo ni se ejecutó retrieval. El [JSON
detallado](./gate2_v2400_review_batch_syn_026_028_adjudication_2026-09-28.json)
registra el fundamento por query/qrel y el diagnóstico de relaciones.
