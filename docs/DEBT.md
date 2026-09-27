# Deuda técnica de TALOS v1.0 (post-cierre)

## Tests con fallos en una corrida completa

La única corrida completa ejecutada durante el sprint terminó con código 1. Pytest registró 10 tests fallidos entre 2.650 node IDs. Cuatro de esos tests se ejecutaron después de forma individual y pasaron; los otros seis no se reejecutaron individualmente. Por lo tanto, los resultados sugieren fallos intermitentes en algunos casos, pero no demuestran que los diez sean flaky ni identifican la causa.

Tests que pasaron al repetirse individualmente:
- `tests/security/test_long_context_invariants.py::test_active_sources_filtering_restricts_retrieval_and_abtains_if_empty`
- `tests/security/test_long_context_invariants.py::test_physical_pre_llm_abstention_gate_on_zero_chunks`
- `tests/unit/pedagogy/memory/test_extractor.py::test_heuristic_misconception_extraction`
- `tests/unit/pedagogy/memory/test_extractor.py::test_heuristic_preference_extraction`

Tests restantes de la corrida completa, pendientes de diagnóstico individual:
- `tests/adversarial/contracts/test_ingestion_adversarial.py::test_source_manifest_rejects_invalid_byte_size[1024]`
- `tests/adversarial/tutor/test_router_security.py::test_group_c_injection_action_rejected` (dos casos parametrizados)
- `tests/contract/test_package_contract.py`
- `tests/security/test_data_sanitizer.py`
- `tests/unit/student/test_meta_declaration_survives_gate.py::test_meta_declaration_abstains_but_persists_preference`

Los cuatro casos que pasaron individualmente no importan ni usan directamente la política `classify_readiness`, el endpoint de catálogo de `ingestion.py` ni `ReadinessProbe`. Aun así, para establecer si son fallos preexistentes habría que compararlos con la misma revisión base; no se hizo esa comparación en este sprint.

**Prioridad:** media. Investigar aislamiento/estado compartido y repetir los casos no diagnosticados antes de clasificarlos como deuda flaky confirmada.

## Refactorización de módulos grandes

- `structured_pipeline.py` (1273 líneas): evaluar separación por fases.
- `orchestrator.py` (1477 líneas): evaluar extracción de servicios.
- `chat.py` (1034 líneas): evaluar extracción de preparación de prompt y auditoría.

**Prioridad:** baja; considerar si el costo de mantenimiento aumenta.

## Documentación pendiente

- Revisar el README y actualizar el mapa del proyecto.
- Marcar como históricos los documentos de hitos ya concluidos.
- Revisar si `health.py` debe publicar resultados recientes en lugar de un contador fijo.

**Prioridad:** baja; no bloquea la funcionalidad actual.

## Decisión de diseño: gate de relevancia

El gate de relevancia de `RetrievalService` permite el paso de candidatos densos con score bajo siempre que exista al menos un candidato con soporte léxico en el mismo batch. Esto prioriza el recall (no perder contexto potencialmente útil) sobre la precisión estricta, asumiendo que la síntesis filtra ruido. El comportamiento está cubierto por `tests/unit/retrieval/test_relevance_gate_policy.py`; cambiarlo requiere revisar esa política y medir el impacto en recall y precisión.
