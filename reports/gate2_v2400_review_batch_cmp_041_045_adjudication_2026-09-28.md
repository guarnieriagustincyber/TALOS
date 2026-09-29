# Gate 2 — Revisión semántica propuesta de GS2-CMP-041…045

**Estado:** propuesta técnica; pendiente de aceptación del usuario.  
**Fecha:** 2026-09-28  
**Evidencia:** lectura completa de las cinco consultas y del chunk
`chk_d3b4fecfde23_17_1`, desde SQLite read-only.

## Contenido observado

El pasaje aporta contexto sobre mayor sobrecarga de KLT asociada al cambio de
modo, nombra Windows/Linux en el contexto parcial que precede al chunk, resume
beneficios del enfoque combinado ULT/KLT y menciona Solaris y TRIX. No presenta
una comparación completa de ULT y KLT puros.

También existe una salvedad de notación: las consultas contrastan un modelo de
hilos de usuario 1:N con uno 1:1 soportado por kernel, mientras que el tramo
posterior del chunk describe algunas relaciones hilo:proceso usando etiquetas
distintas. Este pasaje no basta para normalizar esas taxonomías.

## Evaluación independiente por query/qrel

| Consulta | Dimensión adicional o central | Grado propuesto | Fundamento |
|---|---|---:|---|
| `GS2-CMP-041` | Ventajas/desventajas de los dos modelos y su mapeo | 1 | Aporta sobrecarga KLT y contexto híbrido, pero no desarrolla ambos modelos puros ni resuelve la notación. |
| `GS2-CMP-042` | Contraste analítico de los modelos | 1 | Hay observaciones aisladas, no el análisis comparativo solicitado. |
| `GS2-CMP-043` | Rendimiento **y seguridad** | 1 | La sobrecarga toca parcialmente rendimiento; no hay análisis de seguridad ni comparación completa. |
| `GS2-CMP-044` | Disyuntivas arquitectónicas | 1 | Menciona configuraciones y ventajas híbridas, pero no establece las disyuntivas entre ambos modelos puros. |
| `GS2-CMP-045` | Ejemplos concretos de sistemas reales | 1 | Se nombran sistemas, pero no se vinculan con una comparación concreta y completa de los modelos pedidos. |

El grado 1 indica contexto marginal útil, no relevancia suficiente para
sostener por sí solo la respuesta. Aunque todos los pares reciben la misma
propuesta, cada fundamento corresponde a la dimensión particular de su query;
no se copió una adjudicación común por compartir `chunk_id`.

## Diversidad del top-5

La nota histórica exige chunks de al menos dos capítulos o fuentes distintas
en el top-5. Se trata aquí como una condición del conjunto de resultados o del
ranking, separada de la relevancia semántica de esta referencia individual.
No cambia los grados propuestos ni permite concluir que el qrel sea inválido.

## Estado decisional

Para los cinco pares se propone `EXCLUDE_FROM_POSITIVE_QRELS` con grado 1,
pero `canonical_qrel_decision`, `accepted_grade` y la decisión canónica de
consulta permanecen vacíos. Los qrels siguen en estado pendiente hasta que el
usuario acepte o corrija estas propuestas. No se modificaron el registro de
decisiones, los golden sets, los qrels históricos ni la ACL; no se ejecutó
retrieval.

El detalle por par, las limitaciones y la trazabilidad están en
[el JSON de revisión](./gate2_v2400_review_batch_cmp_041_045_adjudication_2026-09-28.json).
