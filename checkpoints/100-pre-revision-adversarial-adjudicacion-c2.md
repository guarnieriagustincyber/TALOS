# CP100-PRE — REVISIÓN ADVERSARIAL DE ADJUDICACIÓN L3 Y POLÍTICA C2

## 1. Identidad y marco de la revisión

```text
CP = 100-PRE
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C2 (Roles de fuente y ACL efectiva)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor técnico senior y adversarial reviewer de Gate B
METODOLOGÍA = OBSERVE → CORRELATE → CLASSIFY → REPORT
ESTADO OPERATIVO = AUDITORÍA ADVERSARIAL PRE-DECISIÓN HUMANA
```

### 1.1 Objetivo

Ejecutar una revisión técnica adversarial estricta sobre el paquete de decisiones y especificaciones preparado en CP099 (D1, D2, D3), evaluando si la propuesta está suficientemente sustentada por la evidencia documental y de código preexistente antes de que el propietario del proyecto emita su adjudicación humana definitiva.

**Límites estrictos de ejecución:**
* NO implementar cambios de código (`src/` y `tests/` intactos).
* NO modificar la base de datos `data/web_state/knowledge_store.db`.
* NO alterar la política D3-C ni emitir grants L3.
* NO reemplazar ni forzar decisiones humanas normativas.
* Mantener `C1 = PASS / CLOSED` inmutable.

---

## 2. Evidencia documental y técnica revisada

La revisión se limitó estrictamente al cuerpo probatorio normativo y artefactos ya identificados en el proyecto:

1. **Checkpoints normativos:**
   * **CP074 (§5):** Definición contractual de Criterio 2 (Roles de fuente y ACL efectiva consistentes de extremo a extremo).
   * **CP083 / CP084:** Definición del estándar uniforme L3 (5 campos obligatorios: scope, source con versión/hash, propósito, decisor competente/fecha y efecto explícito).
   * **CP085 / CP086:** Inventario previo de 99 relaciones (`0/99 L3`, `84 PARTIAL`, `15 NOT_FOUND`).
   * **CP087:** Evidencia física de carpetas y SHA-256 (76 PDFs locales, 75 confirmados en home, 24 ausentes).
   * **CP088 / CP089:** Adjudicación curricular de 47 relaciones nativas directas (`NATIVE / PRIMARY`).
   * **CP091 / CP092:** Agrupamiento estructural (G1=19, G2=8, G3=24 [7 FADENA→SOC + 17 SOC→FADENA], G4=1) y aplicación de decisiones D1=A, D2=A, D3=C, D4 derivada.
   * **CP093:** Auditoría de necesidad de resolución de `curricular_function` para Gate B y delimitación de las 17 relaciones SOC→FADENA como `POLICY_NOT_GRANTED`.
   * **CP097:** Cierre formal reproducible de C1 (`C1 = PASS / CLOSED`).
   * **CP098:** Auditoría adversarial de C2 (`0/99 L3`, roles como `METADATA_ONLY`, bypass en `SectionExpander`, 17 SOC→FADENA técnicamente permitidas en runtime).
   * **CP099:** Paquete de decisión y especificación de blindaje Defense in Depth.
2. **Artefactos de código y configuración inspeccionados:**
   * `src/study_engine/web/routes/chat.py` (flujo de allowlist, retrieval, expansión y ensamblaje de contexto).
   * `src/study_engine/retrieval/expansion.py` / `section_expander.py` (mecanismo de expansión por ventana de chunks).
   * `src/study_engine/pedagogy/evidence_assembler.py` (`MultiSourceEvidenceAssembler`).
   * `src/study_engine/pedagogy/orchestrator.py` (`PedagogicalOrchestrator.explain_concept`).
   * `src/study_engine/pedagogy/structured_pipeline.py` (inyección en prompt de inferencia).
   * `config/notebook_source_roles.json` (declaraciones de roles descriptivos).

---

## 3. Análisis adversarial de Decisión D1 (Paquete L3 de 82 relaciones)

### 3.1 Planteo de la propuesta en CP099

CP099 propuso consolidar en el paquete de autorización L3 a 82 relaciones candidatas con respaldo nativo o cobertura bajo D3-C:
* 47 relaciones adjudicadas en CP089 (`NATIVE / PRIMARY`).
* 19 relaciones de G1 (Nativas con roles descriptivos bajo D1-A).
* 8 relaciones de G2 (Nativas complementarias bajo D2-A).
* 7 relaciones de G3-A (Reutilización FADENA → SOC bajo D3-C).
* 1 relación de G4 (`fase0-soc` → `src_fadena_prog_punteros`).

Total: **82 relaciones**.

### 3.2 Evaluación probatoria de la evidencia

* **Para las 81 relaciones (47 + 19 + 8 + 7):**
  * La evidencia física y documental es exhaustiva y coherente.
  * Para las 74 nativas (47 + 19 + 8), el soporte físico en carpeta (`fuentes/<scope>/`) es exacto por SHA-256 (`FOLDER_CONFIRMED`).
  * Para las 7 relaciones FADENA → SOC (G3-A), la política D3-C las concedió explícitamente como complementarias y su soporte físico está demostrado en `fuentes/fadena-so2/`.
  * La autorización L3 como material bibliográfico de release es un acto legítimo de gobernanza institucional que no introduce saltos lógicos respecto de su materialidad probada.

---

## 4. Análisis específico y adversarial de G4 (`src_fadena_prog_punteros`)

### 4.1 Estado probatorio de G4

* **Relación:** `fase0-soc` → `src_fadena_prog_punteros`.
* **Archivo físico:** `fuentes/fase0-soc/prog_punteros.pdf`.
* **SHA-256:** `4ece5c39d64ee055b6ff45eb7e49aa0b0e51381e4bcfcb4470bc5e5d36c1e951` (`FOLDER_CONFIRMED` en Fase 0).
* **Roles declarados:** `["IMPLEMENTATION", "REFERENCE"]` (coexistencia de dos dimensiones descriptivas).
* **Trayectoria documental:**
  * CP089: Clasificada como `UNRESOLVED` por ambigüedad entre roles múltiples y función curricular.
  * CP091: Agrupada como G4 (`CONFLICTING_EVIDENCE`, 1 relación).
  * CP092: D4 derivada de D1-A reconoció pertenencia `NATIVE`, preservó ambos roles, pero dejó `curricular_function = NOT_ESTABLISHED`.
  * CP093: Determinó que para Gate B no es necesario forzar `curricular_function` en relaciones nativas.
  * CP099 (§6): El esquema JSON propuesto para el manifiesto L3 exige taxativamente:
    ```json
    "curricular_function": { "type": "string", "enum": ["PRIMARY", "COMPLEMENTARY"] }
    ```

### 4.2 La pregunta crítica de adjudicación

> *¿La evidencia actualmente disponible permite que una autorización L3 positiva para G4 sea emitida sin inferir una función curricular que todavía no está demostrada?*

### 4.3 Evaluación de alternativas para G4

1. **Alternativa A (Incluir G4 directamente en el paquete de 82):**
   * *Sustento a favor:* Su presencia física nativa en `fuentes/fase0-soc/` está demostrada al 100% por SHA-256. Es indudablemente material propio de Fase 0.
   * *Objeción adversarial:* Si el manifiesto L3 requiere obligatoriamente declarar `"PRIMARY"` o `"COMPLEMENTARY"`, incluirla en bloque forzaría al auditor a inventar una función curricular no demostrada en la cátedra, violando la regla metodológica de no inferencia.
2. **Alternativa B (Excluir G4 del paquete L3 y dejarla en `PENDING_FUNCTION_RESOLUTION`):**
   * *Sustento a favor:* Preserva la pureza metodológica. El paquete D1 se reduce a **81 relaciones** totalmente consolidadas y libres de cualquier indeterminación funcional.
   * *Objeción adversarial:* Posterga la autorización de una fuente central del programa de programación en C (punteros), privando potencialmente a los alumnos de Fase 0 de ese contenido hasta una decisión futura.
3. **Alternativa C (Decisión humana singular y explícita para G4):**
   * *Sustento a favor:* Permite que el propietario del proyecto, en ejercicio exclusivo de su autoridad de diseño curricular, adjudique explícitamente la función de G4 (por ejemplo, declarando: *"Autorizo `src_fadena_prog_punteros` para Fase 0 con función `PRIMARY` [o `COMPLEMENTARY`]"*) o adaptando el esquema L3 para permitir `"curricular_function": "NOT_ESTABLISHED"`.
   * *Conclusión adversarial:* **La evidencia existente NO permite incluir automáticamente a G4 en D1 sin esa intervención humana explícita.**

---

## 5. Análisis adversarial de Decisión D2 (Las 17 relaciones SOC → FADENA)

### 5.1 Antecedente normativo (CP092 y CP093)

En CP092, la decisión D3-C estableció:
* `FADENA → SOC = ALLOWED_BY_CP092_FADENA_TO_SOC` (reutilización complementaria concedida).
* `SOC → FADENA = POLICY_NOT_GRANTED` (fuera de la cobertura de la política concedida).

En CP093, se constató que `POLICY_NOT_GRANTED` no es un rechazo normativo ni revocación, pero constituye la ausencia de una habilitación positiva.

### 5.2 Estado en CP098 y CP099

* En CP098 se comprobó que, a pesar de estar `POLICY_NOT_GRANTED`, estas 17 relaciones aparecen asociadas en la tabla SQLite `notebook_sources` de desarrollo y son tratadas como `TECHNICALLY_ALLOWED` por `_authorized_sources_for_scope()` en `chat.py`.
* **Distinción metodológica esencial:**
  ```text
  TECHNICALLY_ALLOWED (Estado residual en DB de desarrollo)
          ≠
  POLICY_AUTHORIZED (Concesión normativa de política de release)
  ```
  La persistencia técnica previa en SQLite NO confiere legitimidad normativa.

### 5.3 Coherencia de la propuesta D2-A

* **Propuesta D2-A:** Mantener formalmente las 17 relaciones fuera del release scope de los 4 cuadernos FADENA (`lenguajes`, `so2`, `std`, `teleco`).
* **Sustento probatorio y normativo:**
  1. Es plenamente coherente con la política D3-C de CP092.
  2. Es plenamente coherente con la evidencia física de CP087: los PDFs residen en `fuentes/fase0-soc/` y están físicamente ausentes (`FOLDER_ABSENT`) de las carpetas de los cuadernos FADENA.
  3. Cumple el mandato de máximo aislamiento curricular de Gate B (C4).
  4. CP098 y CP099 no contienen ninguna evidencia nueva que justifique extender D3-C hacia FADENA.
* **Veredicto adversarial:** La evidencia existente respalda de manera concluyente que la opción natural y coherente con las decisiones previas es **D2-A**. Si el propietario deseara incluirlas, requeriría una reforma sustantiva de la política curricular (Opción D2-B), no sustentada en el archivo actual.

---

## 6. Análisis adversarial de Decisión D3 (Contrato técnico de autorización)

### 6.1 Formulación del contrato propuesto en CP099

```text
effective_sources(scope) = notebook_sources(scope) ∩ L3_authorized_sources(scope)

∀ chunk ∈ retrieved_or_expanded_context:
    chunk.source_id ∈ effective_sources(scope)
```

### 6.2 Coherencia con el blindaje de `SectionExpander`

* El blindaje propuesto en CP099 mediante **Defensa en Profundidad**:
  1. Filtro SQL: `AND source_id IN (?)` pasando `effective_sources(scope)`.
  2. Doble candado en memoria: `if chunk.source_id not in effective_sources(scope): continue`.
* **Veredicto adversarial sobre `SectionExpander`:** El diseño especificado es matemáticamente suficiente e imposibilita que un fragmento fuera de la allowlist ingrese a `expanded_chunks` o `expanded_context_text`.

---

## 7. Rutas de enforcement revisadas: Descubrimiento de brechas en código

La revisión adversarial auditó de extremo a extremo el flujo de datos para determinar si existen otras rutas en el código de TALOS que puedan incorporar fragmentos fuera de `effective_sources(scope)`.

### 7.1 Hallazgo crítico: `MultiSourceEvidenceAssembler` (Ruta pedagógica alternativa)

* **Ubicación:** `src/study_engine/pedagogy/evidence_assembler.py` (líneas 79-98).
* **Invocación:** Es invocado por `PedagogicalOrchestrator.explain_concept()` en:
  * `src/study_engine/web/routes/pedagogy.py` (endpoint `/api/pedagogy/concept-response/{episode_id}`).
  * `src/study_engine/session/study_session_orchestrator.py` (orquestación de sesiones).
* **Mecanismo observado:**
  ```python
  notebook = self.knowledge_store.get_notebook(notebook_id)
  authorized_sources = set(notebook.sources)
  active_sources = [
      source_id for source_id in nb_roles if source_id in authorized_sources
  ]
  for src_id in active_sources:
      chunks = self.knowledge_store.get_chunks_for_source(src_id)
  ```
* **Vulnerabilidad adversarial identificada:**
  `MultiSourceEvidenceAssembler` consulta directamente `notebook.sources` (tabla SQLite `notebook_sources`) y `notebook_source_roles.json`. **No implementa la intersección con `l3_authorization_manifest.json`**.
  Si la tabla SQLite `notebook_sources` conserva relaciones no autorizadas (como las 17 relaciones SOC → FADENA), esta ruta pedagógica recuperará y empaquetará fragmentos no autorizados para el orquestador pedagógico.
* **Impacto:** Para que el contrato D3 sea verdaderamente inviolable, **debe regir también sobre `MultiSourceEvidenceAssembler`**, no únicamente sobre `chat.py` y `SectionExpander`.

### 7.2 Riesgo secundario: Reutilización conversacional en `_LAST_EPISTEMIC_PACK`

* **Ubicación:** `src/study_engine/web/routes/chat.py` (líneas 1867-1875).
* **Mecanismo:** En consultas conversacionales de seguimiento (followup/deícticas), si el retrieval devuelve 0 fragmentos nuevos, se recupera el pack previo:
  ```python
  last_pack_tuple = _LAST_EPISTEMIC_PACK.get(epistemic_key)
  ```
* **Evaluación:** Dado que la clave `epistemic_key` contiene el `target_notebook_id` y el `session_id`, el aislamiento entre cuadernos se preserva en runtime. No obstante, si se modificaran dinámicamente las allowlists en caliente sin invalidar la caché de sesión, fragmentos de un estado previo podrían persistir durante la misma sesión.

### 7.3 Ruta de fallback global en `chat.py`

* **Ubicación:** `src/study_engine/web/routes/chat.py` (líneas 1163-1169).
* **Mecanismo:** `if not search_results and not target_notebook_id: store.search(...)`.
* **Evaluación:** Si `target_notebook_id` no está especificado o es `GLOBAL_SCOPE_ID`, el retrieval debe acotarse a la unión estricta de las fuentes autorizadas de todos los cuadernos del release scope, sin admitir fuentes huérfanas o no autorizadas del store.

---

## 8. Nuevos riesgos identificados

1. **Riesgo de Cobertura Parcial de ACL (Scope de Enforcement):** Limitar el blindaje técnico exclusivamente a `SectionExpander` dejaría desprotegido a `MultiSourceEvidenceAssembler` y al endpoint de pedagogía.
2. **Riesgo de Inconsistencia de Esquema en Manifiesto L3:** El esquema JSON propuesto en CP099 obliga a declarar `"curricular_function": "PRIMARY" | "COMPLEMENTARY"`. Si se intenta emitir el manifiesto para las 82 relaciones sin modificar el esquema o sin adjudicar G4, el validador JSON fallará o forzará una asignación arbitraria.

---

## 9. Elementos que permanecen sin resolver

1. **La función curricular de G4 (`src_fadena_prog_punteros`):** Sigue como `NOT_ESTABLISHED`. Requiere que el decisor humano la defina o que se admita explícitamente ese estado en el manifiesto.
2. **El estado de las 17 relaciones SOC → FADENA en la DB de desarrollo:** Aunque normativamente se decida D2-A (excluirlas), en `data/web_state/knowledge_store.db` seguirán asociadas en la tabla `notebook_sources` (clasificada en CP096 como estado local residual no modificado). El runtime requerirá que el contrato D3 filtre activamente esas 17 relaciones.

---

## 10. Recomendación técnica separada de la decisión normativa

Como auditor técnico independiente, se formulan las siguientes recomendaciones estrictamente técnicas, dejando la decisión normativa al propietario:

1. **Recomendación sobre D1 (Ajuste a 81 + 1):**
   * Aprobar en el paquete masivo D1 a las **81 relaciones** consolidadas (47 CP089 + 19 G1 + 8 G2 + 7 G3-A).
   * Tratar a **G4** mediante una decisión humana singular: adjudicarle función `COMPLEMENTARY` (o `PRIMARY`), o mantenerla en `PENDING_FUNCTION_RESOLUTION` sin trabar el cierre del resto.
2. **Recomendación sobre D2:**
   * Ratificar **D2-A**: Excluir formalmente las 17 relaciones SOC → FADENA del release scope de FADENA.
3. **Recomendación sobre D3 (Ampliación del contrato):**
   * Extender formalmente el contrato de enforcement técnico para que aplique tanto a `chat.py` / `SectionExpander` como a `MultiSourceEvidenceAssembler` (`evidence_assembler.py`).

---

## 11. Dictamen final de la revisión adversarial

Conforme a los hallazgos:
1. G4 no puede integrarse sin más en el enum `"PRIMARY" | "COMPLEMENTARY"` de CP099 sin decisión humana singular o ajuste de esquema.
2. Se descubrió una ruta adicional (`MultiSourceEvidenceAssembler`) que requiere ser incorporada formalmente en la especificación de D3.

El resultado técnico obligatorio es:

```text
CP100_PRE_RESULT = REVIEW_REQUIRES_ADJUSTMENT

DATABASE_CHANGES = 0
TECHNICAL_SOURCE_CHANGES = 0
POLICY_CHANGES = 0
L3_GRANTS_ISSUED = 0
```

---

## 12. Salida ejecutiva

| Decisión | Propuesta actual | Evidencia suficiente | Estado |
|---|---|---|---|
| **D1** | 82 relaciones (incluyendo G4) | **Parcial (81 Sí / G4 No)** | `REQUIRES_ADJUSTMENT` (Separar G4 o adjudicar su función) |
| **G4** | Incluir en D1 / Separar | **Sí (Soporte físico Sí / Función No)** | `REQUIRES_SEPARATE_HUMAN_DECISION` |
| **D2** | Mantener 17 SOC→FADENA fuera (D2-A) | **Sí** | `CONFIRMED_BY_EVIDENCE` |
| **D3** | L3 ∩ allowlist como frontera | **Sí (Requiere ampliar a `evidence_assembler`)** | `CONFIRMED_WITH_EXPANDED_SCOPE` |

```text
HUMAN_ADJUDICATION_READY = YES (con paquete estructurado en D1[81] + D1_G4 + D2 + D3_AMPLIADO)
```

---
