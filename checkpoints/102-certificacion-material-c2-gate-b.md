# CP102 — CERTIFICACIÓN MATERIAL C2 / GATE B

## 1. Identidad y marco de certificación

```text
CP = 102
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C2 (Roles de fuente y ACL efectiva)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor técnico certificador de Gate B
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → CLASSIFY → CERTIFY
ESTADO ANTERIOR = C2 = READY_FOR_CERTIFICATION (CP101)
DICTAMEN FINAL = C2 = PASS / CLOSED
```

### 1.1 Objetivo

Certificar o rechazar con evidencia primaria y reproducible si el Criterio 2 de Gate B — Roles de fuente y ACL efectiva — se encuentra materialmente satisfecho en TALOS tras el despliegue del blindaje CP101.

Se verifica de forma estricta que, bajo el contrato L3 normativo, no exista ninguna ruta en runtime capaz de introducir fragmentos o texto de fuentes no autorizadas en la cadena:
$$\text{selection} \longrightarrow \text{retrieval} \longrightarrow \text{expansion} \longrightarrow \text{evidence assembly} \longrightarrow \text{context compilation} \longrightarrow \text{prompt}$$

---

## 2. Invariantes de producción y entorno de prueba

La certificación se ejecutó en modalidad de **estricta solo-lectura** sobre el estado de producción. No se aplicaron modificaciones sobre la base de datos de desarrollo ni parches funcionales en el código fuente.

### 2.1 Estado bit-a-bit de la base de datos de desarrollo
```bash
sha256sum data/web_state/knowledge_store.db
# PRE:  fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
# POST: fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1

stat -c "MTIME=%Y (%y)" data/web_state/knowledge_store.db
# PRE:  1790366294 (2026-09-25 16:58:14.078984875 -0300)
# POST: 1790366294 (2026-09-25 16:58:14.078984875 -0300)
```
```text
DATABASE_CHANGES = 0
INTEGRITY_VERIFIED = PASS
```

### 2.2 Huellas criptográficas de artefactos normativos y código evaluado
| Artefacto / Archivo | SHA-256 | Rol |
| :--- | :--- | :--- |
| `config/l3_authorization_manifest.json` | `038b4cd0d958423451e3fb3e2542b78ed77007c609a79ac06578d06a0536a0e9` | Manifiesto normativo L3 |
| `src/study_engine/contracts/l3_manifest.py` | `7969418a44bc0125c495e891424af4e717f741c0aaecc309c1496243245bb149` | Contrato de resolución de frontera |
| `src/study_engine/retrieval/expansion.py` | `78f3e95a7274fc4025ded0638ca73b9692b8f6ee3df8d1c37aaecd54e55c376e` | SectionExpander retrieval |
| `src/study_engine/context/section_expander.py` | `4aae53350e77cb8272f96cf66bf5e68df15dcaf7731e9a9b9605780a38d79c3c` | SectionExpander context |
| `src/study_engine/web/routes/chat.py` | `68594d897dfecaff966252f1e2e1ea23d4f876491219dab9e97bc253757725ce` | Endpoints de chat y allowlist |
| `src/study_engine/pedagogy/evidence_assembler.py` | `1cced0f51a7b895765cdb2af62bcc725392493bd52a0bf79fa6015ee0f9b1f8a` | MultiSourceEvidenceAssembler |
| `src/study_engine/context/context_compiler.py` | `c6b70a962946c7f18fda44c7fb4fe29d18939f127e469390bb721b52dd368ff7` | ContextCompiler |
| `tests/adversarial/test_c2_l3_integral_shield.py` | `51ce173c72a9429e497de137dce1cd3e8e8ce09bccad602b2834b595df221cdf` | Suite de regresión adversarial |

---

## 3. Certificación de integridad del manifiesto normativo L3

Se evaluaron formalmente los 11 requisitos de integridad sobre `config/l3_authorization_manifest.json`:

| # | Requisito de Integridad | Verificación | Estado |
| :---: | :--- | :--- | :---: |
| 1 | Archivo presente en ruta esperada | `config/l3_authorization_manifest.json` existe | **PASS** |
| 2 | JSON estructuralmente válido | Parseo RFC 8259 sin errores | **PASS** |
| 3 | `manifest_version` presente | `"1.0.0"` | **PASS** |
| 4 | Gate correspondiente | `"GATE_B"` | **PASS** |
| 5 | Acto de autorización formal | `"ACT-TALOS-GATE-B-L3-20261002-81"` | **PASS** |
| 6 | Conteo exacto 81 / 1 / 17 | 81 `AUTHORIZED`, 1 `PENDING`, 17 `EXCLUDED` (Total = 99) | **PASS** |
| 7 | Cero pares duplicados | 99 pares `(notebook_id, source_id)` únicos | **PASS** |
| 8 | Ningún `PENDING` en autorizados | `PENDING ∩ get_l3_authorized_sources() = ∅` | **PASS** |
| 9 | Ningún `EXCLUDED` en autorizados | `EXCLUDED ∩ get_l3_authorized_sources() = ∅` | **PASS** |
| 10 | G4 no autorizado | `src_fadena_prog_punteros ∉ fase0-soc (L3)` | **PASS** |
| 11 | Las 17 relaciones D2-A no autorizadas | Ninguna relación SOC $\to$ FADENA presente en L3 | **PASS** |

---

## 4. Certificación de frontera efectiva sobre datos de producción

Se calculó la frontera de autorización efectiva sobre los cinco cuadernos normativos del release cruzando el estado físico de `data/web_state/knowledge_store.db` contra `config/l3_authorization_manifest.json`:

$$\text{effective\_sources}(\text{scope}) = \text{notebook\_sources}(\text{scope}) \cap \text{l3\_authorized\_sources}(\text{scope})$$

| Scope / Cuaderno | $\| \text{notebook\_sources} \|$ (DB) | $\| \text{L3\_authorized} \|$ (Manifest) | $\| \text{effective\_sources} \|$ (Runtime) | Diferencia DB $-$ L3 | Diferencia L3 $-$ DB | Identidad Demostrada ($\text{EFF} == \text{DB} \cap \text{L3}$) |
| :--- | :---: | :---: | :---: | :--- | :---: | :---: |
| `fase0-soc` | 26 | 25 | **25** | `['src_fadena_prog_punteros']` (G4) | $\emptyset$ | **DEMOSTRADA** |
| `fadena-lenguajes` | 17 | 10 | **10** | 7 fuentes SOC $\to$ FADENA (D2-A) | $\emptyset$ | **DEMOSTRADA** |
| `fadena-so2` | 14 | 9 | **9** | 5 fuentes SOC $\to$ FADENA (D2-A) | $\emptyset$ | **DEMOSTRADA** |
| `fadena-std` | 30 | 27 | **27** | 3 fuentes SOC $\to$ FADENA (D2-A) | $\emptyset$ | **DEMOSTRADA** |
| `fadena-teleco` | 12 | 10 | **10** | 2 fuentes SOC $\to$ FADENA (D2-A) | $\emptyset$ | **DEMOSTRADA** |
| **TOTALES** | **99** | **81** | **81** | **18 relaciones excluidas** | $\emptyset$ | **100% CONGRUENCIA** |

### Observaciones críticas:
1. Las 18 relaciones que no cuentan con concesión L3 positiva ($1\text{ PENDING} + 17\text{ EXCLUDED} = 18$) son filtradas de forma determinista y **jamás ingresan a `effective_sources`**.
2. No existen fuentes normativas huérfanas en el manifiesto ($\| \text{L3} - \text{DB} \| = 0$).
3. La frontera efectiva es idéntica a la intersección formal en el 100% de los scopes.

---

## 5. Auditoría material de rutas de evidencia

Se auditó minuciosamente cada punto de contacto y componente de formación de contexto en `src/`:

| Ruta de Evidencia | Recibe ACL efectiva | Consulta chunks directos | Filtra `source_id` | Fail-Closed | Estado |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Chat retrieval** (`chat.py`) | **SÍ** (`retrieval_source_ids`) | NO (usa `store.search` parametrizado) | **SÍ** (Filtro SQL + saneamiento memoria) | **SÍ** (Abstención física inmediata) | `PROTECTED` |
| **Retrieval expansion** (`expansion.py`) | **SÍ** (`allowed_source_ids`) | SÍ (vía SQL `chunks`) | **SÍ** (Filtro SQL `IN` + memoria Nivel 3) | **SÍ** (Retorna `([], "")` si ACL vacía) | `PROTECTED` |
| **Context section expander** (`section_expander.py`) | **SÍ** (`allowed_source_ids`) | SÍ (vía SQL `chunks`) | **SÍ** (Filtro SQL `IN` + memoria Nivel 3) | **SÍ** (Retorna `([], "")` si ACL vacía) | `PROTECTED` |
| **Evidence assembler** (`evidence_assembler.py`) | **SÍ** (Intersecta con L3) | SÍ (por `source_id` autorizado) | **SÍ** (Itera solo sobre `active_sources`) | **SÍ** (Retorna vacío si ACL vacía) | `PROTECTED` |
| **Offline backend** (`chat.py`) | **SÍ** (Resuelve `_source_ids_for_notebook`) | NO (usa `search_hybrid` parametrizado) | **SÍ** (Parametriza `source_ids=allowed_srcs`) | **SÍ** (Abstención explícita si vacía) | `PROTECTED` |
| **Context compiler** (`context_compiler.py`) | **SÍ** (`allowed_source_ids`) | NO (delega a expander) | **SÍ** (Filtra semillas previo a expander) | **SÍ** (Emite abstención física pre-LLM) | `PROTECTED` |
| **Allowlist helpers** (`_source_ids_for_notebook`) | **SÍ** (Intersecta con L3) | NO (consulta `notebook_sources`) | **SÍ** (Aplica manifiesto de jure) | **SÍ** (Retorna `set()` si no hay autorizadas) | `PROTECTED` |
| **Admin UI / Catalog** (`routes/notebook.py`) | N/A | NO (inspecciona catálogo) | N/A | N/A | `INFORMATIONAL_ONLY` |

---

## 6. Resultados de pruebas adversariales (Fixtures A–E)

Se ejecutó la suite adversarial `tests/adversarial/test_c2_l3_integral_shield.py` (6 tests en 0.54s) y verificaciones en vivo sobre la base de producción:

### Fixture A — Documento Multi-Source
* **Escenario:** Un único documento contiene Chunk 0 (`src_authorized`) y Chunk 1 (`src_unauthorized`).
* **Ejecución:** Expansión desde Chunk 0 solicitando autorización únicamente para `src_authorized`.
* **Resultado:**
  * Chunk 1 (`src_unauthorized`) fue completamente eliminado en `retrieval.expansion` y `context.section_expander`.
  * `0 chunks UNAUTHORIZED` presentes en `expanded_chunks`.
  * Ningún fragmento del texto prohibido (`LEAK_PAYLOAD`) ni metadata de la fuente no autorizada ingresó a `formatted_context`.
  * **Veredicto:** `SECTION_EXPANSION_BYPASS = NOT_OBSERVED (ELIMINATED)`.

### Fixture B — Aislamiento Cross-Notebook
* **Escenario:** Cuaderno A vinculado con Fuente A y cross-linkeado erróneamente en SQLite con Fuente B.
* **Ejecución:** Consulta sobre Cuaderno A bajo manifiesto L3 que otorga Fuente A a Cuaderno A y Fuente B a Cuaderno B.
* **Resultado:**
  * Fuente B fue descartada determinísticamente de la allowlist de Cuaderno A.
  * `0 chunks de B` recuperados o expandidos.
  * **Veredicto:** `CROSS_NOTEBOOK_BYPASS = NOT_OBSERVED`.

### Fixture C — Política D2-A (17 Relaciones SOC $\to$ FADENA)
* **Escenario:** Las 17 relaciones `SOC → FADENA` residen en `notebook_sources` de la base de datos de producción.
* **Ejecución:** Consulta de allowlist, retrieval y ensamblador de evidencia para `fadena-lenguajes`, `fadena-so2`, `fadena-std` y `fadena-teleco`.
* **Resultado:**
  * En los 17 casos: `notebook_sources = PRESENTE`, `l3_authorized_sources = AUSENTE`, `effective_sources = AUSENTE`.
  * Retrieval = 0 hits; Expansion = 0 fragmentos; Evidence Assembly = 0 citas; Prompt Contribution = 0 caracteres.
  * **Veredicto:** La presencia residual en SQLite carece de efecto autorizante.

### Fixture D — Decisión G4 Pending (`src_fadena_prog_punteros`)
* **Escenario:** `src_fadena_prog_punteros` está asociada a `fase0-soc` en `notebook_sources`.
* **Ejecución:** Validación de estatus en manifiesto y resolución de evidencia en `fase0-soc`.
* **Resultado:**
  * `manifest status = PENDING`.
  * `L3 authorization = False`.
  * `effective_sources = False`.
  * Retrieval = 0; Expansion = 0; Evidence Assembly = 0; Prompt Contribution = 0.
  * **Veredicto:** G4 permanece neutralizada y no produce evidencia efectiva.

### Fixture E — ACL Efectiva Vacía (Fail-Closed sin Fallback)
* **Escenario:** Un cuaderno posee fuentes técnicas en SQLite (`notebook_sources ≠ ∅`), pero 0 fuentes autorizadas en L3 (`l3_authorized_sources = ∅`).
* **Ejecución:** Pipeline completo de chat, SectionExpander y MultiSourceEvidenceAssembler.
* **Resultado:**
  * `SectionExpander.expand_results` $\to$ retorna `([], "")`.
  * `MultiSourceEvidenceAssembler.assemble_evidence_for_kc` $\to$ retorna `{role: []}, []`.
  * `_assemble_epistemic_context` $\to$ retorna `abstained=True`, `formatted_context=""`, `citations=[]`, `chunks=[]`.
  * Prompt contribution = 0.
  * Cero fallback a búsqueda libre o global.
  * **Veredicto:** `FAIL_CLOSED_VERIFIED = PASS`.

---

## 7. Búsqueda exhaustiva de bypass residual

Se auditó estáticamente el código fuente de `src/` sobre los 16 términos de control:
* `notebook_sources` $\to$ Intersectado con L3 en todas las rutas de runtime.
* `source_id` / `document_id` $\to$ Provenance estricto y claves foráneas de catálogo.
* `chunks` $\to$ Acceso protegido mediante filtros SQL `IN (effective_sources)`.
* `get_chunks_for_source` $\to$ Limitado exclusivamente a fuentes validadas en L3.
* `get_notebook` $\to$ Metadatos de catálogo e introspección; sin fuga de fragmentos.
* `store.search` / `search(` $\to$ Parametrizados con `source_ids=retrieval_source_ids`.
* `expanded_context` / `formatted_context` $\to$ Formateados exclusivamente a partir de fragmentos sobrevivientes a la cuádruple barrera Defense in Depth.
* `context_pack` $\to$ Contrato tipado con pre-LLM physical abstention gate ante listas vacías.
* `OfflineKnowledgeBackend` $\to$ Blindado con `allowed_srcs`.
* `SectionExpander` $\to$ Filtrado en SQL y memoria.
* `MultiSourceEvidenceAssembler` $\to$ Filtrado contra manifiesto L3.

**Resultado:** Cero accesos directos desprotegidos. Cero vectores de fuga residuales.

---

## 8. Verificación de no-regresión en suites existentes

Se ejecutó la batería de tests consolidada:
```bash
.venv/bin/pytest tests/adversarial/test_c2_l3_integral_shield.py \
                 tests/context/test_section_expander.py \
                 tests/pedagogy/test_evidence_assembler_isolation.py \
                 tests/unit/web/test_retrieval_scope_allowlist.py \
                 tests/unit/web/test_global_scope.py \
                 tests/unit/web/test_intent_gate.py \
                 tests/unit/web/test_chat_content_registry.py -v
```
**Resultado:** `33 passed, 15 warnings in 13.13s` (100% PASS).

Suite completa de endpoints web:
```bash
.venv/bin/pytest tests/unit/web/ -q
# 88 passed in 51.33s (0 regresiones)
```

---

## 9. Verificación de los 11 criterios de PASS material (§14)

| # | Criterio de Certificación | Evidencia Primaria Demostrada | Resultado |
| :---: | :--- | :--- | :---: |
| 1 | Manifiesto 81/1/17 íntegro | Auditado en §3; 99 relaciones únicas, sin duplicados ni corrupción | **CUMPLE** |
| 2 | `effective_sources` como intersección real | Demostrado en §4 sobre los 5 scopes en base de producción | **CUMPLE** |
| 3 | Ninguna fuente `PENDING` produce evidencia | Demostrado en §6 (Fixture D) y en prueba en vivo de `fase0-soc` | **CUMPLE** |
| 4 | Ninguna fuente `EXCLUDED` produce evidencia | Demostrado en §6 (Fixture C) y en prueba en vivo de FADENA | **CUMPLE** |
| 5 | Ningún bypass cross-notebook | Demostrado en §6 (Fixture B) | **CUMPLE** |
| 6 | Ningún bypass multi-source/document | Demostrado en §6 (Fixture A) para ambas implementaciones de expander | **CUMPLE** |
| 7 | Rutas de evidencia respetan L3 | Demostrado en tabla de rutas de §5 | **CUMPLE** |
| 8 | ACL vacía produce fail-closed completo | Demostrado en §6 (Fixture E); 0 retrieval, 0 expansion, 0 fallback | **CUMPLE** |
| 9 | Cero accesos directos no protegidos | Demostrado en auditoría estática de 16 términos en §7 | **CUMPLE** |
| 10 | DB de producción bit-a-bit estable | Demostrado en §2.1; SHA-256 y MTIME pre/post idénticos | **CUMPLE** |
| 11 | Cero regresiones en suites previas | Demostrado en §8 (33/33 tests focalizados, 88/88 tests web) | **CUMPLE** |

---

## 10. Dictamen definitivo

Habiéndose cumplido simultáneamente y con evidencia material reproducible los once (11) criterios de certificación sin ninguna excepción, ambigüedad ni presunción:

```text
================================================================================
DICTAMEN FORMAL DE GATE B — CRITERIO 2:
C2 = PASS / CLOSED
================================================================================
```

---

## 11. Estado consolidado de Gate B

```text
C1 (IDs / aliases / curriculum_id) = PASS / CLOSED (CP097)
C2 (Roles de fuente y ACL efectiva) = PASS / CLOSED (CP102)
C3 (Hard-ceiling de contexto)       = PARTIAL_EXISTING_EVIDENCE
C4 (Aislamiento cross-curriculum)   = PARTIAL_EXISTING_EVIDENCE
C5 (Gate de abstención y confianza) = BLOCKED / ASSURANCE_BLOCKER
```

Gate B registra dos criterios cerrados con certificación material formal (`C1` y `C2`). Los bloqueadores de assurance restantes para alcanzar Product Complete se concentran en C5 (y la formalización de assurance de C3 y C4).
