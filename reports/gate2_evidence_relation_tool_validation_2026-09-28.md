# Gate 2 Diagnostic Layer v0.1 — Validación en micro-lotes

**Estado:** validación diagnóstica completada; no canoniza ni modifica qrels.  
**Fecha:** 2026-09-28  
**Implementación:** [`gate2_evidence_relations.py`](../src/study_engine/diagnostics/gate2_evidence_relations.py)

## Método

Se ejecutó la herramienta sobre IDs de evidencia explícitos de cuatro lotes
ya revisados. La base se leyó en `mode=ro`; se usaron los valores por defecto
de `text_similarity >= 0.88` y distancia SimHash `<= 16`. El límite es 100
evidencias por lote y las comparaciones se hicieron por consulta, por lo que
los pares de variantes relacionadas se cuentan nuevamente.

| Micro-lote | Comparaciones por consulta | `REVIEW_SHARED_PROVENANCE` | Sin señal fuerte | Posible near-duplicate | Pares misma página/fuente |
|---|---:|---:|---:|---:|---:|
| SYN-014 | 10 | 6 | 4 | 0 | 0 |
| SYN-015/016 | 20 | 9 | 11 | 0 | 3 |
| SYN-022/024 | 18 | 6 | 12 | 0 | 6 |
| SYN-018/020 | 30 | 9 | 21 | 0 | 0 |
| **Total** | **78** | **30** | **48** | **0** | **9** |

## Lectura de los resultados

- **SYN-014:** el pasaje de Tori y el de Stallings, que aportan dimensiones
  complementarias desde fuentes/autores distintos, no reciben señal de
  procedencia compartida ni de near-duplicate. Los pares internos de Stallings
  sí muestran procedencia común. Eso no niega complementariedad ni prueba
  independencia epistemológica.
- **SYN-015:** el chunk completo de la página 373 y sus dos fragmentos
  producen tres señales de misma fuente/página. Sus ratios textuales son
  `0.2201`, `0.2376` y `0.4585`; por tanto, no cruzan el umbral de near-duplicate.
  La señal útil aquí fue la proveniencia.
- **SYN-022/024:** cada consulta detecta los dos pares de extracciones de la
  misma fuente y página. Los IDs internos de documento difieren, pero la fuente
  y el rango de páginas coinciden; este caso motivó comprobar la página dentro
  de la fuente, sin exigir igualdad de `document_id`.
- **SYN-018/020:** la herramienta señala que tres pasajes vienen de la misma
  fuente en cada variante. No los marca como near-duplicates ni decide si son
  redundantes semánticamente; Kurose queda sin señal textual/proveniencia
  compartida con los textos de IPC.

No hubo pares reales que superaran simultáneamente las señales textuales
configuradas. Eso no equivale a demostrar que no existan duplicados: en los
casos conocidos de extracción solapada, la detección efectiva vino de la
proveniencia, no del umbral de similitud.

## Contrato y límites

La salida nunca promueve, degrada, excluye ni canoniza qrels y no produce
acciones de qrel. No adjudica relevancia, independencia, complementariedad ni
suficiencia. `REVIEW_SHARED_PROVENANCE` es deliberadamente amplio: compartir
`source_id` basta para pedir revisión aun en páginas distantes. Los valores de
similitud son umbrales diagnósticos iniciales, no cortes calibrados para
decisiones. Cuatro micro-lotes no proporcionan métricas de precisión/recall
para todo el corpus.

Golden set v2.400, qrels y knowledge store conservaron sus hashes. No se
ejecutó retrieval ni se cambiaron decisiones históricas.

El [JSON reproducible](./gate2_evidence_relation_tool_validation_2026-09-28.json)
registra los IDs de consulta, agregados, pares representativos y hashes.
