# CHECKPOINT 126 — MINIMAL ISOLATION FIX

**Fecha:** 2026-10-05  
**Fase:** CP126 — Minimal Isolation Fix  
**Estado:** COMPLETE — PASS  
**Subdominio:** Infraestructura de Almacenamiento / Aislamiento de Tests / Integridad Forense  
**Autoridad:** Directiva CP126 / Antigravity Agent  
**Referencia Normativa:**
- `reports/e2e_study_loop/CP125_FORENSIC_ISOLATION_AUDIT.md`
- `checkpoints/125-forensic-isolation-audit.md`
- `reports/e2e_study_loop/CP126_MINIMAL_ISOLATION_FIX.md`

---

## 1. RESUMEN EJECUTIVO

CP126 resolvió la vulnerabilidad de aislamiento descubierta en CP124-R1 y analizada en profundidad durante CP125 (`TEST_ISOLATION_ERROR`), que provocaba escrituras involuntarias de SQLite WAL en `data/web_state/vector_store.db` durante la inicialización de tests y el arranque de la API web.

La corrección se ejecutó con estricta adherencia a la frontera mínima y sin tocar datos de producción:

1. **`SQLiteVectorStore`:** Se implementó modo `read_only=True` por defecto, conectando mediante SQLite URI `mode=ro` (sin `nolock=1`), omitiendo `PRAGMA journal_mode = WAL`, omitiendo `_initialize_schema()`, validando fail-closed la existencia de `chunk_embeddings`, y elevando `ReadOnlyVectorStoreError` en cualquier intento de mutación.
2. **`AppContainer`:** Se eliminó el fallback silencioso a `data/web_state` cuando `working_dir` no se provee: en modo `use_mock=True` utiliza un directorio efímero sintético (`talos_mock_state_`), y bajo `pytest` falla cerrado ante cualquier omisión de ruta explícita.
3. **Warmup de Retrieval:** Se implementó el toggle `TALOS_ENABLE_WARMUP` / `settings.enable_retrieval_warmup` y se suprime automáticamente la ejecución del hilo asíncrono de warmup en entornos de test o con contenedor mock.
4. **`KnowledgeStore.vector_search`:** Resuelve explícitamente el almacén de vectores con `read_only=True`, sin ejecutar DDL ni crear bases de datos en runtime.
5. **Caminos de Escritura:** Se auditaron y clasificaron todos los constructores de `SQLiteVectorStore`, haciendo explícito `read_only=False` únicamente en procesos administrativos y fixtures de prueba temporales (`tmp_path`).

---

## 2. CERTIFICACIÓN DE PRUEBAS DE AISLAMIENTO

Se implementaron 8 pruebas dedicadas en `tests/isolation/test_vector_store_isolation.py`:
- `test_iso_01_read_only_default_preserves_db_state`: **PASS**
- `test_iso_02_appcontainer_mock_uses_synthetic_dir`: **PASS**
- `test_iso_03_create_app_warmup_suppressed_in_test_env`: **PASS**
- `test_iso_04_vector_search_resolves_readonly`: **PASS**
- `test_iso_05_readonly_mutations_fail_closed`: **PASS**
- `test_iso_06_admin_write_mode_allowed_on_isolated_db`: **PASS**
- `test_iso_07_existing_schema_read_without_init`: **PASS**
- `test_iso_08_forensic_no_mutation_end_to_end`: **PASS**

Total aislamiento: **8/8 PASS (100%)**

---

## 3. REGRESIÓN INTEGRAL Y DESGLOSE DE TESTS

- **Tests de Aislamiento:** 8/8 PASS
- **Tests de Regresión:** 155/155 PASS
  - Unitarios de Almacenamiento Vectorial: 26/26 PASS
  - Contratos y Adversariales de Retrieval: 69/69 PASS
  - E2E Study Loop (CP124): 9/9 PASS
  - Adversariales Gate B (C2, C3, C5): 51/51 PASS
- **Conteo Total Certificado:** 163 / 163 PASS (8 isolation + 155 regression, 0 fallos, 0 regresiones)

---

## 4. INTEGRIDAD FÍSICA DE PRODUCCIÓN

Las bases de datos permanecieron estrictamente inmutables durante toda la ejecución de CP126:

- `data/web_state/vector_store.db`:
  - SHA256: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4` (IDÉNTICO)
  - SIZE: 1,369,837,568 bytes (IDÉNTICO)
  - MTIME: `2026-10-05T02:18:06.927626+00:00` (IDÉNTICO)
- `data/web_state/knowledge_store.db`:
  - SHA256: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (IDÉNTICO)
  - SIZE: 303,194,112 bytes (IDÉNTICO)
  - MTIME: `2026-09-25T19:58:14.078985+00:00` (IDÉNTICO)
- `data/web_state/student_state.db`:
  - SHA256: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d` (IDÉNTICO)
  - SIZE: 172,032 bytes (IDÉNTICO)
  - MTIME: `2026-10-02T21:19:52.412403+00:00` (IDÉNTICO)

---

## 5. ESTADO DEL RELEASE Y SIGUIENTE PASO

El bloqueo de release V1 queda levantado:
```text
V1_RELEASE_BLOCKED = FALSE
```

El siguiente paso es exclusivamente el **cierre formal de V1 / Release Integrity & Documentation Sync**. No se autoriza el inicio anticipado de V1.5.
