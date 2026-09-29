# Gate 2 — Revisión semántica propuesta de GS2-FUN-111…115

**Estado:** propuesta técnica; pendiente de aceptación del usuario.  
**Fecha:** 2026-09-28  
**Grupo:** `fundamentos` / `aritmetica_punteros` / `retrieval_citation`.

## Evidencia leída

Se leyeron completas las cinco consultas y las tres referencias en SQLite
read-only. Las tres referencias existen y sus fuentes están asociadas al scope
actual `NB-SEC-01-C-PTR`.

- `chk_dc44a8665f2b_243_1` explica que sumar/restar un entero a un puntero usa
  unidades del tamaño del tipo base, con contexto de `int` de 4 bytes, y
  advierte que el mal uso puede provocar accesos inválidos.
- `chk_dc44a8665f2b_102_1` explica el cálculo dirección inicial + índice ×
  tamaño del elemento, con el ejemplo de `2 × 4` bytes para `int`.
- `Introduccion-a-la-programacion-en-C.pdf:p243:c0003` es una extracción OCR
  corta, truncada y dañada de la misma página 243 que el primer chunk. No es
  una segunda fuente ni aporta cobertura independiente.

## Propuestas independientes por consulta y referencia

| Consulta | `…243_1` (regla en unidades del tipo) | `…102_1` (índice × tamaño) | `…p243:c0003` (OCR duplicado) |
|---|---:|---:|---:|
| `GS2-FUN-111` — desplazamiento en bytes | **3** — responde directamente la regla de escalado | **3** — cálculo directo con ejemplo en bytes | **1** — pertinente pero truncado/dañado |
| `GS2-FUN-112` — explicación formal | **2** — regla correcta en prosa, sin fórmula general explícita | **2** — mecanismo con ejemplo, no generalizado formalmente | **1** — no permite sostener la explicación formal |
| `GS2-FUN-113` — bibliografía canónica de SO | **2** — explica el concepto, pero la fuente identificada es de introducción a C | **2** — mismo límite de fuente y ejemplo específico | **1** — dañado y no resuelve el requisito de fuente |
| `GS2-FUN-114` — mecanismo y fundamentos en detalle | **2** — mecanismo sustancial, sin desarrollo general completo | **2** — dirección y tamaño del elemento, limitado al ejemplo `int` | **1** — truncado y sin detalle fiable |
| `GS2-FUN-115` — implicancias en diseño de sistemas | **2** — regla más advertencia de acceso incorrecto, sin implicancias amplias | **1** — cálculo útil, pero sin la dimensión de diseño | **1** — marginal y duplicado |

La duplicación de página 243 se puntúa por par query/qrel, pero no se cuenta
como evidencia independiente. La expectativa de una cita canónica es una
condición del oráculo y no altera por sí sola la relevancia semántica de cada
chunk.

## Estado de autoridad

Los grados y las decisiones `KEEP_AS_RELEVANT_PROPOSAL` /
`EXCLUDE_FROM_POSITIVE_QRELS` son propuestas, no decisiones aceptadas. En los
cinco casos `canonical_query_decision` permanece vacío y cada qrel espera
aceptación; los qrels históricos siguen `PENDING`. No se modificaron el
registro explícito, el dataset, los qrels ni la ACL y no se ejecutó retrieval.

El
[JSON detallado](./gate2_v2400_review_batch_fun_111_115_adjudication_2026-09-28.json)
incluye el fundamento individual de los 15 pares y las limitaciones.
