# Gate 2 — Revisión semántica propuesta de GS2-SYN-015…016

**Estado:** propuesta técnica; pendiente de aceptación del usuario.  
**Fecha:** 2026-09-28  
**Grupo:** `sintaxis_codigo` / `execve` / `retrieval_citation`.

## Dos formulaciones, dos exigencias

- `GS2-SYN-015` pregunta cómo opera `execve` desde la perspectiva POSIX/Linux.
- `GS2-SYN-016` pide parámetros exactos y posibles valores de retorno.

No se transfieren los grados de una variante a la otra: una descripción de
reemplazo de imagen puede apoyar la primera sin cubrir el contrato de
parámetros/retorno de la segunda.

## Fuentes potencialmente complementarias

- `Computer Security: Principles and Practice` (páginas 373, 377 y 620)
  aporta explicación de reemplazo de imagen, preparación de argumentos y
  entorno, e invocación del sistema. Está contextualizado en shellcode y
  auditoría, por lo que no equivale a una referencia POSIX completa.
- `Operating Systems: Internals and Design Principles` (página 120) lo
  identifica como llamada de proceso que ejecuta un programa. Es una fuente
  distinta y pertinente a nivel de clasificación, pero muy escueta.
- `Hacking Ético` (página 258) muestra una invocación con ruta, `argv` y
  `envp`, dentro de un ejemplo de rootkit. Se trata como contexto marginal,
  no como contrato general.

Así, distintas fuentes aportan información no idéntica, aunque con profundidad
desigual. Con el umbral de cualquier relevancia (grado ≥1), hay tres fuentes
para `SYN-015` y dos para `SYN-016`; con el umbral de evidencia sustantiva
(grado ≥2), queda una sola fuente para cada consulta. Los tres IDs de la
página 373 de un mismo libro son fragmentos solapados de una unidad de
evidencia, no tres corroboraciones. Tener diferentes `source_id` tampoco
demuestra independencia de autoría.

## Propuestas por query/qrel

| Query | Referencia | Grado propuesto | Lectura |
|---|---|---:|---|
| `SYN-015` | `chk_0aa9aa4cc0b2_373_1` | **2** | Reemplazo de imagen y preparación de argv/env/call path; útil, pero contexto shellcode y contrato POSIX incompleto. |
| `SYN-015` | `chk_76e248a62974_120_1` | **1** | Confirma de forma independiente que ejecuta un programa; no explica el mecanismo. |
| `SYN-015` | `hacking-etico-carlos-tori.pdf:p258:c0000` | **1** | Ejemplo concreto de invocación, pero contexto rootkit y sin explicación general. |
| `SYN-015` | `Computer_Security_Stallings_3rd_Ed.pdf:p373:c0006` | **1** | Fragmento parcial de argumentos/entorno, solapado con la página completa. |
| `SYN-015` | `Computer_Security_Stallings_3rd_Ed.pdf:p373:c0007` | **1** | Fragmento parcial del paso al sistema, solapado con la página completa. |
| `SYN-016` | `chk_0aa9aa4cc0b2_373_1` | **2** | Describe argumentos/entorno, pero no firma completa ni comportamiento ordinario de retorno/error. |
| `SYN-016` | `chk_76e248a62974_120_1` | **1** | Nombra su finalidad, sin parámetros ni retorno. |
| `SYN-016` | `chk_0aa9aa4cc0b2_620_1` | **1** | Explica carga de ejecutable/address space, no la firma ni los valores de retorno. |
| `SYN-016` | `chk_0aa9aa4cc0b2_380_1` | **0** | Mención pasajera en una lista de capacidades; sin semántica de API. |
| `SYN-016` | `Computer_Security_Stallings_3rd_Ed.pdf:p377:c0002` | **2** | Da detalles de valores marshaled para la llamada, pero en un ejemplo shellcode y sin contrato ordinario de retorno/error. |

## Estado decisional

Las propuestas de grado/retención son no canónicas. Las decisiones de consulta
siguen vacías; los diez qrels históricos siguen `PENDING`. No se modificaron
el registro explícito, los golden sets, los qrels ni la ACL; no se ejecutó
retrieval.

El [JSON detallado](./gate2_v2400_review_batch_syn_015_016_adjudication_2026-09-28.json)
contiene los fundamentos por referencia, la verificación de alcance y las
limitaciones.
