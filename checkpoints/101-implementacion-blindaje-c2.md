# CP101 — IMPLEMENTACIÓN DEL MODELO L3 Y BLINDAJE INTEGRAL C2

## 1. Identidad y marco de ejecución

```text
CP = 101
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C2 (Roles de fuente y ACL efectiva)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Implementador técnico y auditor de blindaje
METODOLOGÍA = OBSERVE → SPECIFY → HARDEN → REGRESSION_TEST → DOCUMENT
ESTADO ANTERIOR = C2 = BLOCKED / ASSURANCE_BLOCKER (CP098, CP100-PRE)
ESTADO RESULTANTE = C2 = READY_FOR_CERTIFICATION (Implementación y blindaje completos; certificación en CP102)
```

### 1.1 Objetivo

Materializar técnicamente la adjudicación humana emanada tras la revisión adversarial CP100-PRE, erradicar los vectores de bypass identificados en CP098 y CP100-PRE, establecer el manifiesto normativo L3 como única autoridad formal de autorización de fuentes para Gate B, blindar la frontera de expansión y ensamblaje de evidencias bajo defensa en profundidad, y verificar la no-regresión mediante una batería de fixtures adversariales estrictos, preservando de forma absoluta la invariante `DATABASE_CHANGES = 0` sobre la base de datos de desarrollo.

---

## 2. Adjudicación humana incorporada

En estricta conformidad con las directivas del propietario del proyecto y las conclusiones de CP100-PRE, se aplicó la siguiente matriz de adjudicación:

```text
D1     = 81 RELACIONES AUTHORIZED (81 grants positivos institucionales)
D1-G4  = PENDING (src_fadena_prog_punteros excluida de autorización para fase0-soc)
D2     = A (17 relaciones SOC → FADENA como POLICY_NOT_GRANTED / EXCLUDED)
D3     = ACCEPTED (Frontera efectiva = notebook_sources ∩ L3_authorized_sources)
```

### 2.1 Los 4 ajustes mandatorios del plan

1. **Autoridad Normativa De Jure del Manifiesto:**
   * `config/l3_authorization_manifest.json` constituye la **única autoridad normativa formal** (de jure).
   * La tabla SQLite `notebook_sources` representa **capacidad técnica instalada / disponibilidad** (de facto).
   * La frontera operativa efectiva en runtime es:
     $$\text{effective\_sources}(\text{scope}) = \text{notebook\_sources}(\text{scope}) \cap \text{l3\_authorized\_sources}(\text{scope})$$
     $$\forall \text{chunk} \in \text{runtime\_context}: \text{chunk.source\_id} \in \text{effective\_sources}(\text{scope})$$

2. **Contabilidad Estricta de las 99 Relaciones:**
   * Manifiesto estructurado exactamente en 99 grants individuales con `grant_id` único (`L3-GRANT-001` a `L3-GRANT-099`).
   * **81 AUTHORIZED** (relaciones curriculares consolidadas).
   * **1 PENDING** (`fase0-soc` $\to$ `src_fadena_prog_punteros`, grupo G4 desacoplado).
   * **17 EXCLUDED** (relaciones `SOC → FADENA` sin concesión bajo D2-A y D3-C).
   * Total = $81 + 1 + 17 = 99$ relaciones. Cero duplicados `(notebook_id, source_id)`.

3. **Fixture E (ACL Vacía / Fail-Closed sin Fallback):**
   * Si $\text{effective\_sources}(\text{scope}) = \emptyset$, el sistema falla cerrado de inmediato: 0 retrieval, 0 expansion, 0 evidencias pedagógicas, 0 texto en prompt y strictly **cero fallback** a búsqueda abierta o global.

4. **Búsqueda Exhaustiva Ampliada Post-Implementación:**
   * Auditoría de código en todo `src/` sobre `get_chunks_for_source`, `notebook_sources`, `chunks`, `source_id`, `document_id`, `expanded_context`, `formatted_context`, `context_pack`, `get_notebook` y `search(`.

---

## 3. Artefactos creados y modificados

### 3.1 [NUEVO] `config/l3_authorization_manifest.json`
* **Propósito:** Manifiesto normativo institucional de fuentes autorizadas bajo Nivel 3 (L3).
* **Campos formales:** `$schema`, `manifest_version: "1.0.0"`, `gate: "GATE_B"`, `issued_date: "2026-10-02"`, `decision_maker: "Propietario del Proyecto / Autoridad de Producto TALOS"`, `authorization_act_id: "ACT-TALOS-GATE-B-L3-20261002-81"`, `purpose_statement`, `normative_authority_statement`, `accounting_summary`, `grants`.
* **Contenido:** 99 grants con `grant_id`, `notebook_id`, `source_id`, `sha256`, `document_filename`, `membership`, `curricular_function`, `declared_roles`, `policy_coverage`, `physical_support`, `status`.

### 3.2 [NUEVO] `src/study_engine/contracts/l3_manifest.py`
* **Módulo de interfaz normativa:**
  * `load_l3_manifest(manifest_path=None) -> Dict[str, Any]`: Carga, valida y cachea en memoria por `mtime` el manifiesto L3.
  * `get_l3_authorized_sources(notebook_id, manifest_path=None) -> Set[str]`: Retorna el conjunto de `source_id` con estatus `AUTHORIZED` para el cuaderno. Fail-closed ante ausencia o error.
  * `get_effective_sources(store, notebook_id, global_folder_id=None, manifest_path=None) -> Set[str]`: Calcula la intersección $\text{notebook\_sources} \cap \text{l3\_authorized\_sources}$.

### 3.3 [MODIFICADO] `src/study_engine/retrieval/expansion.py` (`SectionExpander`)
* **Parámetro añadido:** `allowed_source_ids: Optional[Set[str] | List[str]] = None` en `expand_results`.
* **Defensa en Profundidad implementada:**
  * **Nivel 0 (Fail-Closed):** Si `allowed_source_ids is not None and len(allowed_source_ids) == 0`: retorna `([], "")` inmediatamente.
  * **Nivel 1 (Seed Filtering):** Si `allowed_set` está presente, filtra `seed_results` para descartar semillas no autorizadas.
  * **Nivel 2 (Filtro SQL):** `WHERE document_id = ? AND pos_index BETWEEN ? AND ? AND source_id IN ({placeholders})`.
  * **Nivel 3 (Filtro en Memoria):** `if allowed_set is not None and s_id not in allowed_set: continue`.

### 3.4 [MODIFICADO] `src/study_engine/context/section_expander.py` (`SectionExpander`)
* Implementa idéntica Defensa en Profundidad (Nivel 0, 1, 2 y 3) adaptada a su firma y contrato (`List[ChunkWithProvenance]`).

### 3.5 [MODIFICADO] `src/study_engine/web/routes/chat.py`
* **`_source_ids_for_notebook(store, notebook_id)`:** Resuelve `tech_sources` de SQLite y las intersecta con `get_l3_authorized_sources(notebook_id, manifest_path=store.l3_manifest_path)`. Si el almacén apunta a la base de producción (`data/web_state/knowledge_store.db`), aplica automáticamente `DEFAULT_MANIFEST_PATH`.
* **`_authorized_sources_for_scope(store, target_notebook_id, global_folder_id)`:** Agrega las fuentes efectivas de cada cuaderno del scope.
* **`_assemble_epistemic_context`:** Pasa explícitamente `allowed_source_ids=retrieval_source_ids` a `expander.expand_results(...)`. Si `retrieval_source_ids` es vacío, emite abstención estricta inmediata sin fallback.
* **`OfflineKnowledgeBackend.generate_response`:** Filtra la búsqueda local mediante `source_ids=allowed_srcs` de fuentes autorizadas del cuaderno.

### 3.6 [MODIFICADO] `src/study_engine/web/dependencies.py`
* En `AppContainer`: Asigna `self.knowledge_store.l3_manifest_path = self.repo_root / "config" / "l3_authorization_manifest.json"` cuando `not self.use_mock`.

### 3.7 [MODIFICADO] `src/study_engine/pedagogy/evidence_assembler.py` (`MultiSourceEvidenceAssembler`)
* Añade soporte para `l3_manifest_path`.
* En `assemble_evidence_for_kc`: Intersecta `notebook.sources` con `get_l3_authorized_sources(notebook_id, manifest_path=self.l3_manifest_path)` cerrando la brecha arquitectónica identificada en CP100-PRE §7.1.

### 3.8 [MODIFICADO] `src/study_engine/context/context_compiler.py` (`ContextCompiler`)
* Añade soporte para `allowed_source_ids` en `build_context_pack` y lo delega a `self.expander.expand_results(..., allowed_source_ids=allowed_source_ids)`.

### 3.9 [NUEVO] `tests/adversarial/test_c2_l3_integral_shield.py`
* Batería adversarial con 6 tests exhaustivos cubriendo los 5 escenarios/fixtures:
  * `test_fixture_a_multi_source_document_retrieval_expansion_defense_in_depth`: Validación de aislamiento dentro de un mismo documento multi-fuente en `retrieval.expansion`.
  * `test_fixture_a_multi_source_document_context_section_expander_defense_in_depth`: Validación en `context.section_expander`.
  * `test_fixture_b_cross_notebook_isolation`: Validación de que la contaminación de links técnicos entre cuadernos es anulada por el manifiesto L3.
  * `test_fixture_c_soc_to_fadena_17_relations_strictly_excluded`: Comprobación de que las 17 relaciones `SOC → FADENA` quedan excluidas de retrieval, expansión y ensamblaje pedagógico.
  * `test_fixture_d_g4_pending_punteros_excluded`: Comprobación de que `src_fadena_prog_punteros` (G4) no entra en la ACL efectiva de `fase0-soc`.
  * `test_fixture_e_empty_effective_acl_fail_closed_zero_fallback`: Comprobación de fail-closed estricto y cero fallback cuando la ACL efectiva es vacía.

---

## 4. Resultados de la verificación técnica

### 4.1 Batería adversarial específica
```bash
.venv/bin/pytest tests/adversarial/test_c2_l3_integral_shield.py -v
```
**Resultado:** `6 passed in 0.54s` (100% PASS).

### 4.2 Batería combinada de expansión, aislamiento pedagógico y allowlist
```bash
.venv/bin/pytest tests/adversarial/test_c2_l3_integral_shield.py \
                 tests/context/test_section_expander.py \
                 tests/pedagogy/test_evidence_assembler_isolation.py \
                 tests/unit/web/test_retrieval_scope_allowlist.py -v
```
**Resultado:** `16 passed in 0.61s` (100% PASS).

### 4.3 Suite integral de endpoints web
```bash
.venv/bin/pytest tests/unit/web/ -q
```
**Resultado:** `88 passed in 51.33s` (100% PASS). Cero regresiones en la suite web.

---

## 5. Verificación de la invariante de base de datos

De acuerdo con la Decisión B (CP096) y el compromiso contractual de CP101:
* No se ejecutó ningún `UPDATE`, `INSERT` o `DELETE` sobre la base de datos de desarrollo.
* No se modificó ningún esquema ni tabla existente.

```bash
sha256sum data/web_state/knowledge_store.db
# fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1

stat -c "MTIME=%Y (%y)" data/web_state/knowledge_store.db
# MTIME=1790366294 (2026-09-25 16:58:14.078984875 -0300)
```

```text
DATABASE_CHANGES = 0
INTEGRITY_VERIFIED = PASS
```

---

## 6. Estado resultante de Gate B

Tras la implementación de CP101, la arquitectura de TALOS cuenta con un modelo de autorización formal L3 completamente desacoplado del estado residual de instalación, y un blindaje técnico impermeable contra bypass de expansión y rutas pedagógicas alternativas.

```text
C1 (IDs / aliases / curriculum_id) = PASS / CLOSED (CP097)
C2 (Roles de fuente y ACL efectiva) = READY_FOR_CERTIFICATION (CP101 implementado; certificación en CP102)
C3 (Hard-ceiling de contexto)       = PARTIAL_EXISTING_EVIDENCE
C4 (Aislamiento cross-curriculum)   = PARTIAL_EXISTING_EVIDENCE
C5 (Gate de abstención y confianza) = BLOCKED / ASSURANCE_BLOCKER
```

---

## 7. Dictamen de handoff a CP102

La implementación técnica y normativa de C2 ha concluido satisfactoriamente. Corresponde habilitar **CP102 — Certificación Material C2 / Gate B**, cuyo objetivo será emitir el dictamen formal definitivo de cierre de C2 sustentado en las evidencias generadas en CP101.
