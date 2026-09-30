# Initial Qrels Candidate Source — Read-only Audit

**Resultado:** `SOURCE_INSUFFICIENT`<br>
**Gate operativo:** `BLOCKED_SOURCE_UNSELECTED`<br>
**Actividad:** inspección documental y de metadatos existentes; read-only.<br>
**Retrieval, embeddings, modelos o generación de pares nuevos:** no ejecutados.

## Conclusión ejecutiva

No se encontró en los artefactos existentes una fuente de pares
query→chunk que demuestre procedencia independiente de Qwen, E5 **y** del canal
lexical que se compararía como baseline, con cobertura suficiente para los
qrels iniciales.

Sí existen asociaciones anteriores y juicios humanos puntuales. Sin embargo:

1. Las 165 referencias positivas v2.400 en 48 consultas son qrels históricos;
   Gate 2 documenta que los grados originales 3/2/1 reflejaban posiciones de
   retrieval, no relevancia semántica adjudicada.
2. Revisar manualmente un candidato heredado puede validar o corregir su label,
   pero no cambia la procedencia de cómo se seleccionó el candidato.
3. Un subconjunto nuevo de candidatos se encontró con búsquedas FTS y anclas
   lexicales curadas. Es una fuente distinta del ranking denso, pero comparte el
   canal lexical y no cumple el requisito estricto de independencia del
   baseline; además la cobertura es puntual.
4. Las fixtures de backend son sintéticas. Los scopes, KCs y relaciones
   notebook-source no enlazan por sí solos una consulta con un chunk juzgado.

## Fuentes revisadas

| Artefacto | Qué aporta | Procedencia / límite |
|---|---|---|
| [`golden_set_v2_400.json`](../data/eval/golden_set_v2_400.json) y [`golden_set_v2_400.qrels.json`](../data/eval/qrels/golden_set_v2_400.qrels.json) | 400 consultas y 165 referencias positivas heredadas | `expected.relevant_chunks` concuerda con qrels; documentación de Gate 2 indica que las notas heredadas se generaron por posición de retrieval |
| [`gate2_v2400_coverage_inventory_2026-09-28.json`](../reports/gate2_v2400_coverage_inventory_2026-09-28.json) y [`gate2_v2400_query_adjudication_queue_2026-09-28.json`](../reports/gate2_v2400_query_adjudication_queue_2026-09-28.json) | Presencia, ACL y estado de revisión de referencias históricas | Reorganizan referencias heredadas; no constituyen un pool independiente |
| [`gate2_v2400_explicit_decision_register_2026-09-28.json`](../reports/gate2_v2400_explicit_decision_register_2026-09-28.json) | Decisiones humanas explícitas puntuales | La mayoría son keep/exclude de candidatos ya presentes en qrels heredados |
| [`gate2_v2.402-pilot1.manifest.json`](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.manifest.json) | Provenance operacional del piloto previo | Declara `retrieval_executed=true`, `top_k=1` y `qrels_provenance=retrieval_proposal`; no es independiente |
| [`gate2_v2.402-pilot1.qrel-membership-proposal.json`](../reports/gate2_pilot_v2_402_pilot1/gate2_v2.402-pilot1.qrel-membership-proposal.json) | Juicios semánticos de un solo revisor, aceptados por el usuario | El propio artefacto declara revisión única y procedencia provisional; no borra el origen por retrieval |
| [`gate2_v2.402-positive-segments-selection-review.json`](../reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-selection-review.json) y [`gate2_v2.402-positive-segments-user-adjudication.json`](../reports/gate2_positive_segments_v2_402/gate2_v2.402-positive-segments-user-adjudication.json) | Revisión y aprobación de candidatos de dos consultas | Selección basada en v2.400/qrels, aunque no se ejecutó nuevo retrieval |
| [`gate2_scope_evidence_audit_2026-09-28.md`](../reports/gate2_scope_evidence_audit_2026-09-28.md) y [`gate2_scope_candidate_adjudication_2026-09-28.json`](../reports/gate2_scope_candidate_adjudication_2026-09-28.json) | Cinco pares investigados en scopes bloqueados; uno fue aceptado como qrel nuevo | El informe declara búsquedas locales FTS con anclas lexicales; cobertura puntual y correlacionada con el baseline lexical |
| [`miniature_queries.json`](../tests/fixtures/backend_selection/miniature_queries.json) y [`miniature_qrels.json`](../tests/fixtures/backend_selection/miniature_qrels.json) | Validación sintética del formato | No son evidencia real del corpus |

El nuevo qrel puntual aceptado es
`GS2-CMP-011` → `chk_db97c77518c6_821_1`, grado 2. El informe de auditoría
indica que se encontró al inspeccionar candidatos obtenidos por FTS; cuatro de
los cinco candidatos del lote quedaron excluidos y este único par tampoco
aporta una fuente amplia independiente del canal lexical.

## Clasificación final

| Posible fuente | ¿Independiente de Qwen/E5? | ¿Independiente del baseline lexical? | ¿Suficiente para qrels iniciales? |
|---|---|---|---|
| Qrels históricos por retrieval | No | No demostrado | No |
| Adjudicaciones humanas sobre candidatos heredados | El juicio puede ser independiente; la selección no | No demostrado | No |
| Búsquedas FTS/anclas lexicales curadas | Sí respecto del ranking denso | No | No |
| Scope/KC/fuente bibliográfica sin chunk explícito | No aplica | No aplica | No |
| Fixtures sintéticas | No aplica | No aplica | No |
| Selección humana independiente desde corpus curricular | Potencialmente | Potencialmente | No existe protocolo/evidencia ya registrada |

## Decisión y límite de autorización

El resultado del gate es `SOURCE_INSUFFICIENT`; el estado se mantiene
`BLOCKED_SOURCE_UNSELECTED`. No se importan qrels históricos ni se amplían los
paquetes existentes.

Si se quiere continuar sin una fuente independiente, la siguiente opción es
pedir autorización separada para una actividad de candidate generation ciega
exclusivamente para formar el pool, sin métricas ni decisión de backend. Esa
autorización no está concedida por la luz verde a adjudicación humana. Hasta
entonces no se generan candidatos, no se ejecutan modelos, no se instalan
dependencias y no se alteran índices o producción.
