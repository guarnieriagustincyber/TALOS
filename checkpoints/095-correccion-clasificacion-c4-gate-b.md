# CP095 — RECTIFICACIÓN FORMAL DE CLASIFICACIÓN DE C4 (GATE B)

## 1. Objetivo y límites

Este checkpoint registra formalmente la corrección de la clasificación del **Criterio 4 de Gate B (aislamiento multi-currículo / ausencia de contaminación cross-curriculum)**, preservando la trazabilidad histórica de CP093 y CP094 sin alterar retroactivamente sus textos originales.

Esta rectificación es estrictamente documental y de clasificación normativa.
No modifica código, base de datos, `notebook_sources`, roles, configuración, prompts, corpus ni modelos. No emite un veredicto de `PASS` para C4, no afirma que el aislamiento ya esté demostrado y no resuelve la autorización pendiente de C2.

---

## 2. Cadena de trazabilidad histórica

```text
CP074 §5:
  C4 definido como REQUIRED_FOR_PRODUCT.
  Condición de cierre: suite/matriz versionada con rutas positivas y negativas por materia sin observar contenido, profile o ACL del scope vecino.

CP075 §3:
  C4 clasificado como PARTIAL_EXISTING_EVIDENCE.
  Mecanismos de aislamiento probados en unit tests/fixtures; pendiente la ejecución integrada sobre el release.

CP093 §6:
  Sobreclasificación de C4 como BLOCKED (ASSURANCE_BLOCKER).
  Razonamiento: 17 relaciones técnicas SOC → FADENA en notebook_sources carecen de política positiva concedida bajo D3-C.

Auditoría crítica posterior:
  Detección de salto lógico: confunde la legitimidad/autorización de la allowlist (C2)
  con una falla de aislamiento o contaminación demostrada (C4).

CP095 (este checkpoint):
  Rectificación formal:
  C4 = PARTIAL_EXISTING_EVIDENCE
  NATURE = NO_BLOCKER / ASSURANCE_PENDING
```

---

## 3. Fundamentación normativa del desacoplamiento C2 vs. C4

La auditoría independiente determinó que catalogar `C4 = BLOCKED` a partir de las 17 relaciones `SOC → FADENA` constituía la introducción de una condición adicional que el contrato de Gate B no exige:

1. **Perímetro de C2 (Autorización y roles/ACL):**
   * Evalúa la consistencia de los roles de fuente y la allowlist técnica (`notebook_sources`) frente a las fuentes autorizadas bajo el umbral L3.
   * La falta de cobertura positiva de la política D3-C para las 17 relaciones `SOC → FADENA` es un problema de legitimidad de la allowlist que pertenece **estricta y exclusivamente a C2**.

2. **Perímetro de C4 (Aislamiento arquitectónico y runtime):**
   * Evalúa si los mecanismos de aislamiento del software (storage, retrieval, context pack, memoria de sesión, prompt) confinan la ejecución a la allowlist asignada al cuaderno consultado, impidiendo fugas provenientes de cuadernos vecinos no asociados.
   * El hecho de que una fuente esté asociada en `notebook_sources` para un cuaderno FADENA implica que, para el motor de ejecución, dicha fuente forma parte del scope configurado; su recuperación no representa una fuga arquitectónica ni una rotura de aislamiento del software.

3. **Invariante documental del repositorio (canon anti-conflación):**
   El repositorio estableció reiteradamente que la presencia técnica de una fuente compartida no debe equipararse a contaminación:
   * **CP077 §10:** *"Una fuente declarada o compartida no se interpreta como contaminación sin probar su ruta."*
   * **CP079 §6:** *"No se reinterpretan estos casos como contaminación demostrada."*
   * **CP083 §8:** *"La presencia compartida de una fuente en varios scopes no demuestra contaminación ni autoriza/rechaza ninguno de ellos."*
   * **CP087 §7:** *"Las fuentes compartidas no se consideran automáticamente contaminación..."*

4. **Conclusión de la distinción:**
   > **C4 no está bloqueado por las 17 relaciones SOC → FADENA; C2 continúa bloqueado por la cuestión de autorización de esas relaciones.**

---

## 4. Evidencia operacional pendiente de C4

El estado de C4 permanece en **`PARTIAL_EXISTING_EVIDENCE`** porque la condición objetiva de cierre establecida en CP074 §5 y CP075 §3 sigue pendiente de ejecución material:

```text
Condición pendiente para C4:
  1. Suite/matriz integrada versionada para los 5 currículos del release scope.
  2. Verificación de rutas positivas y negativas por materia.
  3. Comprobación en el límite de prompt/retrieval de que no se observa contenido,
     perfil ni ACL del scope vecino.
```

No se declara `PASS` ni se asume aislamiento demostrado: el estado es puramente **`ASSURANCE_PENDING`**, sin constituir un bloqueo estructural (`NO_BLOCKER`).

---

## 5. Resumen maestro formal vigente de Gate B (C1–C5)

Tras la rectificación de CP095, el estado formal de los cinco criterios de Gate B queda consolidado como sigue:

| Criterio Gate B | Estado vigente | Naturaleza del estado | Evidencia faltante para cierre |
|---|---|---|---|
| **C1 — IDs, aliases y `curriculum_id`** | **`BLOCKED`** | `PRODUCT_BLOCKER` / `ASSURANCE_BLOCKER` | Reconciliación declarativa de IDs/aliases y resolución de `fadena_v1` en DB SQLite. |
| **C2 — Roles de fuente y ACL efectiva** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Actos de autorización demostrada L3 (0/99) y alineación de allowlist con D3-C. |
| **C3 — Selección de prompt/perfil** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Test integrado request → resolver → prompt para los 5 currículos declarados. |
| **C4 — Aislamiento multi-currículo** | **`PARTIAL_EXISTING_EVIDENCE`** | `NO_BLOCKER` / `ASSURANCE_PENDING` | Suite/matriz versionada de no-contaminación (rutas positivas y negativas). |
| **C5 — Autoridad de `fadena-std`** | **`BLOCKED`** | `ASSURANCE_BLOCKER` | Documento de programa académico oficial verificable o decisión de exclusión. |

---

## 6. Cierre

```text
CP094_STATUS = ACCEPTED_HISTORICAL_HANDOFF
CP095_STATUS = COMPLETE_RECTIFICATION
C4_RECTIFIED_STATUS = PARTIAL_EXISTING_EVIDENCE
C4_RECTIFIED_NATURE = NO_BLOCKER / ASSURANCE_PENDING
GATE_B_FORMAL_BLOCKERS = [C1, C2, C5]
GATE_B_PENDING_ASSURANCE = [C3, C4]
TECHNICAL_STATE_MODIFIED = NO
```
