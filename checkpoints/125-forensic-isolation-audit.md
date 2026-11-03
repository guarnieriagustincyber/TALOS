# CHECKPOINT 125 — AUDITORÍA DE AISLAMIENTO FORENSE Y RECUPERACIÓN SEGURA DEL VECTOR STORE

**Checkpoint:** `checkpoints/125-forensic-isolation-audit.md`  
**Directiva:** `CP125 — FORENSIC ISOLATION AUDIT`  
**Subdominio:** V1 / Retrieval & Storage / Aislamiento Forense  
**Tipo:** Auditoría forense de solo lectura, análisis estático de call-graph y plan de corrección mínima  
**Estado:** AUDITORÍA COMPLETADA — NO IMPLEMENTAR  
**Fecha:** 2026-10-04  

---

## 1. ESTADO DE GOBERNANZA Y MÉTRICAS

```text
CP125_FORENSIC_AUDIT = COMPLETE
ROOT_CAUSE_IDENTIFIED = TRUE
PRODUCTION_DB_WRITE_PATH_IDENTIFIED = TRUE

VECTOR_CONTENT_INTEGRITY = PASS
VECTOR_FILE_INTEGRITY = FAIL
TEST_ISOLATION_DEFECT_CONFIRMED = TRUE

RECOVERY_REQUIRED = FALSE
MINIMAL_FIX_DEFINED = TRUE
IMPLEMENTATION = NOT_STARTED

PRODUCTION_DB_MODIFIED_DURING_CP125 = FALSE
V1_RELEASE_BLOCKED = TRUE
```

---

## 2. RESUMEN EJECUTIVO

En cumplimiento estricto del mandato de **CP125**, se llevó a cabo una auditoría forense integral de solo lectura (`mode=ro`) sobre el subsistema de almacenamiento vectorial de TALOS V1, estableciendo con certeza matemática y documental la causa raíz del `TEST_ISOLATION_ERROR` reportado en CP124-R1.

Se concluyó que:
1. **El contenido de `vector_store.db` está 100% íntegro:** Los 287.075 vectores correspondientes a los 7 cuadernos y a los dos modelos (`Qwen3-Embedding-0.6B` de 1024d con 287.069 registros y `sha256-128d-v1` con 6 registros) coinciden de manera exacta con el baseline histórico certificado en el Checkpoint 104 y Checkpoint 112. No hubo pérdida ni alteración de datos de embeddings (`VECTOR_CONTENT_INTEGRITY = PASS`).
2. **La causa raíz del cambio de hash radica en el acoplamiento RW de `SQLiteVectorStore`:** El constructor `SQLiteVectorStore.__init__` carece de modo de solo lectura. Toda instanciación ejecuta `sqlite3.connect` en modo lectura-escritura, `PRAGMA journal_mode = WAL;`, DDL (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`) y `commit()`.
3. **El camino de propagación en tests y exploración proviene de `AppContainer` y `create_app()`:**  
   * `AppContainer(use_mock=True)` no redirige `working_dir` a memoria o rutas temporales si no se le especifica; por defecto adopta `data/web_state/` e inicializa el pipeline real conectando a `vector_store.db`.
   * `create_app()` lanza en su hook `startup` un hilo secundario asíncrono (`_schedule_retrieval_warmup`) que ejecuta `vector_search("warmup")`, el cual a su vez busca en rutas de producción prefijadas e instancia `SQLiteVectorStore` en modo lectura-escritura.

---

## 3. ENTREGABLE PRINCIPAL

Se generó el informe técnico detallado:
[`reports/e2e_study_loop/CP125_FORENSIC_ISOLATION_AUDIT.md`](../reports/e2e_study_loop/CP125_FORENSIC_ISOLATION_AUDIT.md)

El informe documenta:
1. Inventario forense de archivos (`knowledge_store.db`, `vector_store.db`, `student_state.db`, archivos WAL y SHM).
2. Consulta de pragmas internos y distribución de vectores.
3. Call-graph estático completo que explica cómo las operaciones de lectura desencadenan mutaciones de cabecera en SQLite.
4. Matriz de clasificación de componentes (RO vs RW).
5. Evaluación de las 5 opciones de corrección arquitectónica.
6. Propuesta de corrección mínima recomendada para la fase **CP126**.

---

## 4. CONDICIÓN DE INTEGRIDAD FÍSICA EN CP125

Durante la totalidad de CP125 se respetaron rigurosamente las reglas de no-modificación:
* Modificaciones de código en producción: 0 líneas (`src/` intacto).
* Modificaciones de bases de datos: 0 bytes (`DATABASE_CHANGES = 0`).
* Hashes verificados al cierre:
  - `data/web_state/knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
  - `data/web_state/vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4`
  - `data/web_state/student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d`
  - `data/student_state.db`: `66e090f6f55dd20a91423c93b7d21a8800fdf12474738df689b2862bb4de8dd4`
* `PRODUCTION_DB_MODIFIED_DURING_CP125 = FALSE`.
* `V1_RELEASE_BLOCKED = TRUE` (Permanece bloqueado hasta la implementación y certificación de CP126).
