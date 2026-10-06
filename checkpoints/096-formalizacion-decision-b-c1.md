# CP096 — FORMALIZACIÓN DE DECISIÓN HUMANA B PARA C1 (GATE B)

## 1. Objetivo y límites

Este checkpoint formaliza el registro de la **Decisión Humana B** adoptada respecto al **Criterio 1 de Gate B (IDs, aliases y `curriculum_id` reconciliados)**, tras la auditoría adversarial que demostró que el estado `curriculum_id = 'fadena_v1'` pertenece a la base SQLite de desarrollo local y no al diseño canónico del producto.

Este registro es estrictamente documental y normativo:
* `TECHNICAL_CHANGES = 0` (no se modifica código de aplicación, seeders ni tests).
* `DATABASE_CHANGES = 0` (no se ejecuta ningún `UPDATE`, borrado ni migración sobre `data/web_state/knowledge_store.db`).
* No se declara `PASS` para C1; se fija su estado contractual en `PARTIAL_EXISTING_EVIDENCE` (`ASSURANCE_PENDING`).

---

## 2. Registro formal de la Decisión Humana B

```text
C1_CONTRACTUAL_STATUS = PARTIAL_EXISTING_EVIDENCE
C1_LOCAL_INSTALL_STATUS = BLOCKED_BY_RESIDUAL_DB_STATE
HUMAN_DECISION = B
NATURE = NO_BLOCKER / ASSURANCE_PENDING
```

### Significado e implicancias normativas de la Decisión B:

1. **`knowledge_store.db` no será modificado:**
   El archivo `data/web_state/knowledge_store.db` es un artefacto de desarrollo local, no versionado (ignorado por `.gitignore`), mutable y efímero. No se utilizará como artefacto normativo de release.
2. **Cero operaciones de mutación sobre la DB local:**
   No se ejecutará ningún comando SQL `UPDATE` manual ni se redactará script de migración sobre dicha base de datos en esta etapa.
3. **`fadena_v1` como estado residual observado:**
   El valor `fadena_v1` detectado en la inspección de CP077/CP078 queda clasificado formalmente como *estado residual de desarrollo previo*, producto de un seeding ejecutado con anterioridad a la incorporación del catálogo granular. No se interpreta como la identidad canónica del producto ni como un defecto arquitectónico del código.
4. **Certificación sobre provisioning limpio y reproducible:**
   La certificación final de Gate B para C1 deberá ejecutarse sobre un entorno de aprovisionamiento limpio, reproducible y determinista (`_seed_curriculum_tree` ejecutado contra catálogo versionado en una base virgen).

---

## 3. Separación estricta de planos

Para evitar futuras confusiones metodológicas, se formaliza la distinción entre los tres planos de análisis:

```text
+-----------------------------------------------------------------------------------+
| 1. PRODUCT_DESIGN (Canónico / Versionado)                                         |
|    - Catálogo: config/notebook_kc_catalog.json (mapeo 1:1 granular verificado).   |
|    - Identidad: config/notebook_identity_decisions.json ("alias_target": null).  |
|    - Seeder: app/curriculum_service.py (_seed_curriculum_tree).                   |
|    - Resolver: talos/core/prompt_resolver.py (fallback neutro TALOS_BASE_PROMPT). |
|    ESTADO: CORRECTO / 1:1 EXPLICITO                                              |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 2. LOCAL_INSTALLATION (Estado local / No versionado)                              |
|    - Archivo: data/web_state/knowledge_store.db (.gitignore L87/L96).             |
|    - Causa: Guarda idempotente `if not store.contains_notebook(...)` en seeder   |
|      preservó las filas sembradas con la versión temprana fadena_v1.              |
|    ESTADO: BLOCKED_BY_RESIDUAL_DB_STATE (circunscrito a ese archivo local)       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
| 3. RELEASE_VALIDATION (Criterio de Acreditación Gate B)                           |
|    - Procedimiento: Instanciación de SQLite virgen / en memoria.                  |
|    - Ejecución: _seed_curriculum_tree() sobre el catálogo del release.            |
|    - Verificación: Comprobación determinista de identidad 1:1 sin fadena_v1.     |
|    ESTADO: ASSURANCE_PENDING (pendiente de test de certificación reproducible)    |
+-----------------------------------------------------------------------------------+
```

---

## 4. Matriz canónica de identidad curricular del release

Conforme a la condición objetiva de cierre establecida en CP074 §5 para C1 (*"Matriz completa de los 5 currículos publicada en checkpoint o config con verificación en tests"*), se publica la matriz canónica y vinculante para el release scope de TALOS:

| Cuaderno (`notebook_id`) | `curriculum_id` Canónico | Aliases Aceptados | Fallback de Resolución (sin match) |
|---|---|---|---|
| `fase0-soc` | `roadmap_kasiu_v4_fase0` | `[]` (ninguno) | `TALOS_BASE_SYSTEM_PROMPT` |
| `fadena-lenguajes` | `fadena_lenguajes_2026` | `[]` (ninguno) | `TALOS_BASE_SYSTEM_PROMPT` |
| `fadena-so2` | `fadena_so2_2026` | `[]` (ninguno) | `TALOS_BASE_SYSTEM_PROMPT` |
| `fadena-std` | `fadena_std_2026` | `[]` (ninguno) | `TALOS_BASE_SYSTEM_PROMPT` |
| `fadena-teleco` | `fadena_teleco_2025` | `[]` (ninguno) | `TALOS_BASE_SYSTEM_PROMPT` |

### Reglas de identidad de la matriz:

1. **Política de aliases (`aliases = []`):**
   En este release no existen aliases válidos, tolerados ni heredados. Cualquier identificador distinto del `notebook_id` canónico es considerado no reconocido.
2. **Política de fallback neutro:**
   Ante un identificador de materia o currículo inexistente o desalineado, el sistema nunca debe cruzar ni fallar silenciosamente hacia otro de los cuatro currículos restantes; su resolución decae exclusivamente al prompt base neutro no especializado (`TALOS_BASE_SYSTEM_PROMPT`).

---

## 5. Evidencia pendiente para el cierre de C1 (Hacia `PASS`)

Para que el criterio C1 sea certificado con veredicto `PASS`, se requerirá:

1. Ejecución de un test automatizado de aprovisionamiento reproducible que inicialice un almacén virgen (o en memoria) invocando `_seed_curriculum_tree()`.
2. Aserción en dicho test de que los 5 cuadernos tienen exactamente sus correspondientes `curriculum_id` canónicos según la matriz precedente.
3. Aserción de que ningún registro en la base limpia contiene `fadena_v1`.
4. Aserción del comportamiento estricto de aliases vacíos y fallback neutro.

Hasta tanto se ejecute y documente dicha verificación automatizada en el marco de Gate B, el estado permanece como **`PARTIAL_EXISTING_EVIDENCE`**.

---

## 6. Resumen maestro formal vigente de Gate B (C1–C5)

Consolidando las resoluciones de CP095 (rectificación C4) y CP096 (formalización Decisión B para C1), el mapa de criterios de Gate B se estructura objetivamente de la siguiente manera:

| Criterio Gate B | Estado vigente | Naturaleza del estado | Evidencia faltante para cierre |
|---|---|---|---|
| **C1 — IDs, aliases y `curriculum_id`** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Test de certificación de provisioning limpio reproducible para los 5 scopes. |
| **C2 — Roles de fuente y ACL efectiva** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Actos de autorización demostrada L3 (0/99) y alineación de allowlist con D3-C. |
| **C3 — Selección de prompt/perfil** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Test integrado request → resolver → prompt para los 5 currículos declarados. |
| **C4 — Aislamiento multi-currículo** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Suite/matriz versionada de no-contaminación (rutas positivas y negativas). |
| **C5 — Autoridad de `fadena-std`** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Documento de programa académico oficial verificable o decisión de exclusión. |

---

## 7. Cierre

```text
CP096_STATUS = COMPLETE_DECISION_B_REGISTRATION
C1_CONTRACTUAL_STATUS = PARTIAL_EXISTING_EVIDENCE
C1_LOCAL_INSTALL_STATUS = BLOCKED_BY_RESIDUAL_DB_STATE
HUMAN_DECISION = B
GATE_B_FORMAL_BLOCKERS = [C2, C5]
GATE_B_PENDING_ASSURANCE = [C1, C3, C4]
TECHNICAL_STATE_MODIFIED = NO
DATABASE_STATE_MODIFIED = NO
```
