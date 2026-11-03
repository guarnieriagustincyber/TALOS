# Contexto para Auditoría Profunda de TALOS

## Estado actual
- Rama: main
- Tag: v1.0.0
- Commits locales por delante de origin/main: 100 (sin push de main)

## Arquitectura del sistema
TALOS es un tutor adaptativo local con las siguientes capas:

1. **Ingestion Layer** (batch externo vía Colab)
   - PDFs → chunks → embeddings → vector_store.db
   - Chapter summaries → FTS5 index
   - Entry point: scripts/generate_hierarchical_index.py

2. **Retrieval Layer** (online)
   - Hybrid search: FTS5 (BM25) + dense vectors
   - GranularityRouter: elige chunks vs chapter summaries
   - QueryRewriter: resuelve deixis y follow-ups
   - ConversationState: mantiene contexto epistémico

3. **Pedagogical Layer** (online)
   - BKT tracker: actualiza p_L por KC
   - determine_pedagogical_context_mode: basic/intermediate/advanced
   - structured_pipeline: ensambla prompts con directivas pedagógicas
   - Gate introductorio: basic + explain_concept → analogías, sin diagramas salvo pedido explícito

4. **Synthesis Layer** (online)
   - LLM call con streaming SSE
   - Citation verifier
   - ForensicAuditor: valida rigor epistémico

## Perímetro congelado (NO TOCAR)
- src/study_engine/state/
- src/study_engine/execution/
- src/study_engine/assessment/
- src/study_engine/audit/auditor.py (hash: cf5b9062f95de7f635738b5c4f0bea074c2fbcfada5c2eccc53cb06e3f277b57)

## Problemas ya resueltos en este sprint
1. cold_start_mode: intermediate → basic (para KC sin historial)
2. Aliases en notebook_kc_catalog.json para matching introductorio
3. Reglas de formato condicionadas a context_mode (basic = introductorio)
4. Límite de tokens por modo: 800 (basic) / 3500 (resto)
5. Test assertion actualizada para prerequisite_reinforcement

## Deuda técnica documentada
Ver docs/DEBT.md. Los fallos allí enumerados requieren diagnóstico: no deben asumirse como flaky confirmado. La última corrida completa antes de actualizar la aserción registró 5 fallos listados en DEBT.md y uno adicional en test_chat_content_registry, cuya aserción fue actualizada después.

## Tu misión
Auditar profundamente las capas de Retrieval y Pedagogical buscando:
1. Falsos cableados (flujos que parecen conectados pero no lo están)
2. Contradicciones semánticas en prompts
3. Problemas de performance (cuellos de botella, queries N+1)
4. Condiciones de carrera en estado compartido
5. Deuda técnica oculta (TODOs, código muerto, imports sin usar)
6. Edge cases no cubiertos (queries vacías, KCs sin chunks, etc.)

## Formato de reporte
Por cada hallazgo:
- Archivo y línea exacta
- Descripción del problema
- Impacto estimado (crítico/alto/medio/bajo)
- Evidencia (código relevante)
- Sugerencia de fix (opcional)
