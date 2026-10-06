# CP097 — CERTIFICACIÓN REPRODUCIBLE DE C1 (GATE B)

## 1. Identidad de la auditoría

```text
CP = 097
CRITERIO = C1 (IDs canónicos, aliases y curriculum_id reconciliados)
GATE = Gate B (Identidad y aislamiento curricular)
FECHA = 2026-10-02
COMMIT / TREE = f81134fc2293916210d53c8065f3a0049e52b0b4
ROL = Auditor técnico ejecutor (OBSERVE → MEASURE → CORRELATE → CLASSIFY → DOCUMENT)
```

---

## 2. Marco contractual y normativo

* **CP074 §5:** Define las condiciones objetivas de cierre para C1:
  > *"IDs canónicos, aliases y `curriculum_id` reconciliados declarativamente para cada currículo incluido en el release. La matriz aprobada lista identidad canónica y alias permitidos; cada caso positivo resuelve el currículo esperado y cada ID desconocido toma fallback neutral, sin herencia accidental."*
* **CP096:** Formaliza la Decisión Humana B:
  > *`data/web_state/knowledge_store.db` es clasificado como estado local/efímero/residual de desarrollo y permanece sin modificar. La certificación de Gate B se ejecuta sobre provisioning limpio y reproducible.*
  > *Fija la matriz canónica vinculante de 5 currículos, `aliases = []` estricto y fallback neutro `TALOS_BASE_SYSTEM_PROMPT`.*

---

## 3. Entorno de ejecución y artefactos

```text
RUNTIME = CPython 3.12.3
OS = Linux (Kernel 6.8.0-52-generic x86_64)
STORAGE_TEMPORAL_1 = SQLite in-memory (:memory:)
STORAGE_TEMPORAL_2 = SQLite archivo temporal aislado (/tmp/tmpdku7qzdj.db)
CATALOGO_PATH = config/notebook_kc_catalog.json
CATALOGO_SHA256 = 4d0e1449c62a944717d7a723508553e45b2c1193ddfc057e3b7479e3638bc1af
IDENTITY_DECISIONS_PATH = config/notebook_identity_decisions.json
IDENTITY_DECISIONS_SHA256 = 9b893468de3fba05c3b676603afb93894cd4f218ad33955bf38c3d3678e0504c
HARNESS_EJECUCION = /home/agustin/.gemini/antigravity/brain/31012c01-9fec-4c0a-9023-331ef1196c87/scratch/certify_c1.py
```

---

## 4. Verificación del mecanismo real de provisioning

La auditoría ejecutó el mecanismo real del código fuente sin duplicar su lógica:
* **Módulo:** `src/study_engine/web/dependencies.py`
* **Función:** `AppContainer._seed_curriculum_tree(store, registry)`
* **Lógica de carga:** `_load_notebook_curriculum_ids(catalog_path)` lee directamente el mapeo canónico versionado desde `config/notebook_kc_catalog.json`.
* **Estado inicial del almacenamiento:**
  ```sql
  SELECT COUNT(*) FROM notebooks; -- Retorna: 0
  ```
  `INITIAL_NOTEBOOK_COUNT = 0` (almacenamiento estrictamente virgen).
* **Ejecución del seed:** Invocación de `_seed_curriculum_tree` con `KnowledgeStore(":memory:")` inicializado.
* **Estado posterior al seed:**
  ```sql
  SELECT COUNT(*) FROM notebooks; -- Retorna: 5
  ```
  `POST_SEED_NOTEBOOK_COUNT = 5`.

---

## 5. Verificación de identidad generada en almacenamiento virgen

Consulta SQL directa sobre la tabla `notebooks` del almacenamiento limpio tras la ejecución del provisioning:

| `id` (`notebook_id`) | `curriculum_id` generado | `folder_id` | `name` / `subject` | Resultado |
|---|---|---|---|---|
| `fase0-soc` | `roadmap_kasiu_v4_fase0` | `roadmap_fase0` | Roadmap KASIU TECH v4 - Fase 0 / Programación y Pensamiento Algorítmico | **CORRECTO** |
| `fadena-lenguajes` | `fadena_lenguajes_2026` | `fadena_1ano_2cuat` | Lenguajes de Programación - FADENA 2026 / Lenguajes de Programación | **CORRECTO** |
| `fadena-so2` | `fadena_so2_2026` | `fadena_1ano_2cuat` | Sistemas Operativos II - FADENA 2026 / Sistemas Operativos | **CORRECTO** |
| `fadena-std` | `fadena_std_2026` | `fadena_1ano_2cuat` | Sistema de Tratamiento de Datos - FADENA 2026 / Tratamiento de Datos y Bases de Datos | **CORRECTO** |
| `fadena-teleco` | `fadena_teleco_2025` | `fadena_1ano_2cuat` | Infraestructura de Telecomunicaciones - FADENA 2025 / Telecomunicaciones y Redes | **CORRECTO** |

### Métricas de identidad observadas:
* **Identidades del release presentes:** 5 / 5 (100%).
* **`curriculum_id` correctos:** 5 / 5 (100%).
* **Ocurrencias de `fadena_v1` en almacenamiento virgen:** 0.
* **IDs inesperados:** 0.
* **Duplicados:** 0.
* **Valores NULL inesperados:** 0.
* **Aliases implícitos:** 0.
* **Ambigüedades:** 0.

---

## 6. Pruebas positivas del resolver real

Se ejecutó el resolver curricular del producto (`get_system_prompt_for_notebook` en `src/study_engine/pedagogy/fase0_seed.py`) y la interfaz de persistencia (`store.get_pedagogical_contract(notebook_id)`) para cada una de las cinco identidades canónicas:

| `notebook_id` | `curriculum_id` | Perfil obtenido (`subject`) | Fallback usado | Marcador de perfil validado | Concordancia contract prompt | Resultado |
|---|---|---|---|---|---|---|
| `fase0-soc` | `roadmap_kasiu_v4_fase0` | Programación y Pensamiento Algorítmico | `False` | Presente (`=== PERFIL CURRICULAR VALIDADO ===`) | Coincidencia 100% | **PASS** |
| `fadena-lenguajes` | `fadena_lenguajes_2026` | Lenguajes de Programación | `False` | Presente (`=== PERFIL CURRICULAR VALIDADO ===`) | Coincidencia 100% | **PASS** |
| `fadena-so2` | `fadena_so2_2026` | Sistemas Operativos II | `False` | Presente (`=== PERFIL CURRICULAR VALIDADO ===`) | Coincidencia 100% | **PASS** |
| `fadena-std` | `fadena_std_2026` | Sistema de Tratamiento de Datos | `False` | Presente (`=== PERFIL CURRICULAR VALIDADO ===`) | Coincidencia 100% | **PASS** |
| `fadena-teleco` | `fadena_teleco_2025` | Infraestructura de Telecomunicaciones | `False` | Presente (`=== PERFIL CURRICULAR VALIDADO ===`) | Coincidencia 100% | **PASS** |

**Resultado positivo:** 5 / 5 PASS. Cada caso resuelve exclusivamente a su perfil especializado validado.

---

## 7. Pruebas negativas del resolver real

Se ejecutaron de forma sistemática 39 casos negativos para verificar que ninguna entrada inválida, ambigua o desalineada adopte indebidamente un currículo ajeno ni active un perfil especializado:

### Subtest N1 — Currículo desconocido / inexistente (5 casos)
Se invocó cada uno de los 5 cuadernos válidos con `curriculum_id = 'curriculum_fantasma_xyz'`:
* Los 5 casos devolvieron exactamente `TALOS_BASE_SYSTEM_PROMPT` (fallback neutro).
* **Resultado N1:** 5 / 5 PASS.

### Subtest N2 — Combinaciones cross-curriculum (20 casos)
Se invocó cada cuaderno con los 4 `curriculum_id` canónicos pertenecientes a las otras materias del release:
* Los 20 casos devolvieron exactamente `TALOS_BASE_SYSTEM_PROMPT`.
* Cero resolución cruzada observada.
* **Resultado N2:** 20 / 20 PASS.

### Subtest N3 — Identificador residual legacy `fadena_v1` (5 casos)
Se invocó cada cuaderno con el valor residual `curriculum_id = 'fadena_v1'`:
* Los 5 casos devolvieron exactamente `TALOS_BASE_SYSTEM_PROMPT`.
* Demuestra que el resolver rechaza activamente el valor residual de la base local y no le otorga ningún perfil especializado.
* **Resultado N3:** 5 / 5 PASS.

### Subtest N4 — Aliases no autorizados e identificadores informales (9 casos)
Se probaron identificadores de compatibilidad legacy, nombres abreviados y alias potenciales:
* `fadena-so` + `fadena_so2_2026` → `TALOS_BASE_SYSTEM_PROMPT`
* `fadena-prog` + `fadena_lenguajes_2026` → `TALOS_BASE_SYSTEM_PROMPT`
* `fase0` + `roadmap_kasiu_v4_fase0` → `TALOS_BASE_SYSTEM_PROMPT`
* `lenguajes` + `fadena_lenguajes_2026` → `TALOS_BASE_SYSTEM_PROMPT`
* `so2` + `fadena_so2_2026` → `TALOS_BASE_SYSTEM_PROMPT`
* `std` + `fadena_std_2026` → `TALOS_BASE_SYSTEM_PROMPT`
* `teleco` + `fadena_teleco_2025` → `TALOS_BASE_SYSTEM_PROMPT`
* `NB-CYBERSECURITY-V1` + `fadena_v1` → `TALOS_BASE_SYSTEM_PROMPT`
* `NB-CYBERSECURITY-V1` + `cybersecurity_v1` → `TALOS_BASE_SYSTEM_PROMPT`
* **Resultado N4:** 9 / 9 PASS (política estricta `aliases = []` demostrada en runtime).

---

## 8. Matriz completa 5 × 5 de resolución cruzada

Se evaluaron exhaustivamente las 25 combinaciones posibles entre los 5 cuadernos y los 5 currículos del release:

```text
                                         Columnas: curriculum_id
                   C1 (roadmap)   C2 (lenguajes)   C3 (so2)   C4 (std)   C5 (teleco)
fase0-soc                ✓              N             N          N            N
fadena-lenguajes         N              ✓             N          N            N
fadena-so2               N              N             ✓          N            N
fadena-std               N              N             N          ✓            N
fadena-teleco            N              N             N          N            ✓
```

* **Leyenda:**
  * `✓` = Perfil curricular validado específico obtenido (diagonal).
  * `N` = Fallback neutro no especializado (`TALOS_BASE_SYSTEM_PROMPT`) obtenido (fuera de diagonal).
* **Métricas de la matriz:**
  * Diagonal: 5 / 5 `✓` (100%).
  * Fuera de diagonal: 20 / 20 `N` (100%).
  * **Casos de resolución cruzada (cross-resolution): EXACTAMENTE 0.**

---

## 9. Pruebas de aislamiento e invariancia

1. **Invariancia al orden de inserción:**
   Se aprovisionó un store virgen independiente sembrando los cuadernos en orden inverso. Los 5 cuadernos conservaron exactamente sus mismos IDs canónicos y `curriculum_id`.
2. **Idempotencia de aprovisionamiento:**
   Se ejecutó un segundo ciclo de seed sobre el almacén ya provisto. El conteo de cuadernos permaneció en exactamente 5, sin duplicación de filas ni alteración de `curriculum_id`.
3. **Reproducibilidad en almacenamiento SQLite de archivo físico:**
   Se instanció un archivo temporal en disco (`/tmp/tmpdku7qzdj.db`) y se ejecutó la suite completa. El comportamiento fue idéntico al del modo en memoria.

---

## 10. Integridad de la base de datos de desarrollo (`knowledge_store.db`)

Para dar cumplimiento estricto a la directiva de no tocar el archivo no versionado `data/web_state/knowledge_store.db`, se midió su estado criptográfico antes y después de toda la ejecución de CP097:

```text
PRE_HASH  = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
POST_HASH = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1
PRE_MTIME = 1790366294.078985 (2026-09-25 16:58:14.078985 -0300)
POST_MTIME = 1790366294.078985 (2026-09-25 16:58:14.078985 -0300)

DATABASE_MUTATIONS = 0 (INTACTA)
```

---

## 11. Estado Git e invariantes técnicos

```bash
git diff --check   # Retorna 0 (limpio)
git status --short # Cero modificaciones en código fuente de producción o tests
```

* `TECHNICAL_SOURCE_CHANGES = 0` (el harness de prueba se ejecutó desde el scratchpad del auditor sin alterar el árbol Git de la aplicación).
* `DATABASE_CHANGES = 0`.

---

## 12. Clasificación formal de C1

Con base en la evidencia material reproducible obtenida:

```text
C1_CONTRACTUAL_STATUS = PASS
C1_LOCAL_INSTALL_STATUS = OBSERVED_RESIDUAL_PRESERVED_BY_DECISION_B
C1_CERTIFICATION = PASS
NATURE = CLOSED
```

### Justificación de cierre:
1. El mecanismo real del producto (`_seed_curriculum_tree` + `config/notebook_kc_catalog.json`) aprovisiona deterministamente las 5 identidades canónicas requeridas sobre almacenamiento limpio.
2. No existe presencia de `fadena_v1` en el aprovisionamiento limpio.
3. El resolver real discrimina al 100% los 5 currículos en sus combinaciones positivas.
4. Las 20 combinaciones cruzadas, los 5 intentos con currículos inexistentes, los 5 intentos con `fadena_v1` y los 9 intentos con aliases no autorizados decaen de forma estricta y segura a `TALOS_BASE_SYSTEM_PROMPT`.
5. Se verificó cero contaminación, cero colisión y cero mutación del estado local.

---

## 13. Resumen maestro formal vigente de Gate B (C1–C5 post-CP097)

Tras el cierre definitivo de C1 en CP097, el mapa de criterios de Gate B queda estructurado así:

| Criterio Gate B | Estado vigente | Naturaleza del estado | Evidencia faltante para cierre |
|---|---|---|---|
| **C1 — IDs, aliases y `curriculum_id`** | **`PASS`** | `CLOSED` | **Criterio cerrado definitivamente en CP097.** |
| **C2 — Roles de fuente y ACL efectiva** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Actos de autorización demostrada L3 (0/99) y alineación de allowlist con D3-C. |
| **C3 — Selección de prompt/perfil** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Test integrado request → resolver → prompt para los 5 currículos declarados. |
| **C4 — Aislamiento multi-currículo** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Suite/matriz versionada de no-contaminación (rutas positivas y negativas). |
| **C5 — Autoridad de `fadena-std`** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Documento de programa académico oficial verificable o decisión de exclusión. |

```text
GATE_B_FORMAL_BLOCKERS = [C2, C5]
GATE_B_PENDING_ASSURANCE = [C3, C4]
GATE_B_CLOSED_CRITERIA = [C1]
```

---

## 14. Regla de continuidad y próximo paso

Conforme a la regla de cierre de CP097 §19–§20:
* C1 queda formalmente cerrado y **no debe volver a abrirse durante Gate B**.
* El siguiente paso operativo es directamente:
  ```text
  CP098 — Auditoría adversarial C2
  ```
  focalizada en:
  * `SOURCE_ROLE_ACL`
  * Autorización L3 de fuentes
  * Selección de fuentes
  * Retrieval allowlist
  * Provenance de autorización documental
