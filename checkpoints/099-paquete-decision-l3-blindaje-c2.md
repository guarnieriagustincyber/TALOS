# CP099 — PAQUETE DE DECISIÓN L3 Y BLINDAJE C2 (GATE B)

## 1. Identidad del documento y marco normativo

```text
CP = 099
GATE = B (Identidad y aislamiento curricular)
CRITERIA = C2 (Roles de fuente y ACL efectiva)
BASE_COMMIT = f81134fc2293916210d53c8065f3a0049e52b0b4
DATE = 2026-10-02
ROL = Auditor senior y preparador de decisión
METODOLOGÍA = OBSERVE → MEASURE → CORRELATE → CLASSIFY → DOCUMENT
ESTADO CONTRACTUAL = CP098 COMPLETADO / C1=PASS / C2=BLOCKED
```

### 1.1 Objetivo del checkpoint

CP098 estableció de manera empírica e irrefutable que el Criterio C2 se encuentra bloqueado por dos razones independientes:
1. **Déficit probatorio de autorización formal L3 (`0/99 L3 DEMONSTRATED`):** No existe un acto documental explícito de aprobación positiva para las relaciones fuente-cuaderno en el alcance de release.
2. **Vulnerabilidad técnica de frontera en ACL (`SECTION_EXPANSION_BYPASS = OBSERVED`):** `SectionExpander` expande fragmentos contiguos sin re-verificar `source_id IN (retrieval_source_ids)`, y la allowlist técnica admite en runtime 17 relaciones `SOC → FADENA` que carecen de concesión de política bajo D3-C.

La finalidad de **CP099** NO es implementar el código ni forjar decisiones humanas, sino **estructurar de forma rigurosa, completa y separable el paquete de decisiones humanas y especificaciones técnicas** necesario para que la persona responsable del producto desbloquee C2.

### 1.2 Separación estricta de planos metodológicos

Conforme a la directiva de auditoría, se establece la distinción taxativa de cuatro planos secuenciales:

```text
┌─────────────────────────────────────────────────────────────┐
│ 1. AUTORIZACIÓN HUMANA (Acto documental vinculante L3)      │
│    - Decisiones D1 (Release grants) y D2 (17 SOC→FADENA)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. POLÍTICA EFECTIVA (Modelo relacional normativo)          │
│    - Reglas de allowlist por cuaderno y política D3-C       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. IMPLEMENTACIÓN TÉCNICA (Hardening de código TALOS)       │
│    - Decisión D3 (Contrato técnico runtime)                 │
│    - Blindaje Defense in Depth en SectionExpander           │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. CERTIFICACIÓN (Ejecución reproducible de Gate B)         │
│    - Suite de regresión adversarial C2                      │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Invariantes operativas durante CP099

* `DATABASE_CHANGES = 0`: La base de datos de desarrollo `data/web_state/knowledge_store.db` se mantiene completamente intacta.
* `TECHNICAL_SOURCE_CHANGES = 0`: No se introduce ninguna modificación en el código fuente de TALOS, rutas FastAPI ni tests.
* `C1_STATUS = PASS / CLOSED`: La identidad curricular y reconciliación de aliases certificada en CP097 se mantiene como premisa cerrada e inmutable.

---

## 2. Diagnóstico de los dos bloqueadores independientes de C2

La auditoría adversarial CP098 demostró que la superación de C2 exige resolver dos planos desacoplados:

### 2.1 Bloqueador A: Provenance y Autorización L3 (`0/99 DEMONSTRATED`)

* **Definición contractual (CP083/CP084):** El estándar L3 requiere una decisión documental explícita, trazable y formal que consigne:
  1. Cuaderno/scope de release.
  2. Identidad unívoca de la fuente (identificador y SHA-256).
  3. Propósito académico o pedagógico autorizado.
  4. Autoridad/decisor competente con fecha.
  5. Efecto formal de autorización para el release.
* **Estado observado:** `0/99 L3 DEMONSTRATED` (84 con evidencia parcial de desarrollo y 15 sin evidencia documental previa).
* **Desacople de planos probatorios:**
  * **Asociación en SQLite (`notebook_sources`):** Registra enlaces técnicos preexistentes de ingestión, pero no equivale a una autorización institucional.
  * **Configuración de roles (`notebook_source_roles.json`):** Es una descripción analítica de fuentes, no un grant formal. Además, en runtime su efecto es `METADATA_ONLY` (no restringe ni filtra la recuperación).
  * **Existencia física de archivos PDF (`fuentes/<scope>/`):** Demuestra disponibilidad de bytes en disco (confirmada para 76 PDFs locales en CP087), pero no confiere autorización legal, académica ni de release.

### 2.2 Bloqueador B: Integridad técnica de ACL y bypass en `SectionExpander`

* **Hallazgo empírico de CP098 (`SECTION_EXPANSION_BYPASS = OBSERVED`):**
  * El endpoint de chat resuelve la allowlist en `chat.py` y filtra los resultados iniciales (`seed_results`).
  * Sin embargo, `SectionExpander.expand_results()` ejecuta una consulta por ventana:
    ```sql
    SELECT id, document_id, source_id, content, page_start, pos_index, section, token_count
    FROM chunks
    WHERE document_id = ? AND pos_index BETWEEN ? AND ?
    ORDER BY pos_index ASC;
    ```
  * Esta consulta carece de la cláusula `AND source_id IN (retrieval_source_ids)`.
  * Tampoco re-filtra en memoria los fragmentos obtenidos.
  * En documentos multi-fuente o con fronteras contiguas entre fuentes autorizadas y no autorizadas, fragmentos de fuentes fuera de la allowlist ingresan a `expanded_context_text` y se inyectan en el prompt del LLM.
* **Desalineación técnica de política (17 relaciones `SOC → FADENA`):**
  * La política D3-C adoptada en CP092 concedió la reutilización `FADENA → SOC` como complementaria, pero dejó `SOC → FADENA` como `POLICY_NOT_GRANTED`.
  * No obstante, en la base de datos y en `_authorized_sources_for_scope()`, estas 17 relaciones están asociadas en `notebook_sources`, por lo que el runtime las trata como `TECHNICALLY_ALLOWED`.

### 2.3 Independencia causal de ambos bloqueadores

```text
┌──────────────────────────────────────┬──────────────────────────────────────┐
│ Si se emite Autorización L3 (A)      │ ...pero no se blinda SectionExpander │
│                                      │ → C2 sigue BLOQUEADO por bypass ACL  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ Si se blinda SectionExpander (B)     │ ...pero no se emiten grants L3       │
│                                      │ → C2 sigue BLOQUEADO por provenance  │
└──────────────────────────────────────┴──────────────────────────────────────┘
```
Ambos bloqueadores deben resolverse de manera independiente y coordinada.

---

## 3. Matriz integral de auditoría de las 99 relaciones de release

A continuación se consolida la totalidad del universo de 99 relaciones persistidas en el scope de release (5 cuadernos), cruzando identidad lógica, evidencia física de archivos y SHA-256 (CP087), estado de política curricular (CP089/CP092), estado probatorio previo (CP085/CP086) y estado de autorización L3 (CP098):

### Cuaderno `fase0-soc` (26 relaciones)

| # | `source_id` | Documento físico | SHA-256 | Pertenencia | Rol declarado | Función curricular | Política D3-C | Soporte físico | Evid. previa | Estado L3 | Estado release propuesto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `src-guia-2025-c04f44ef` | GUIA_2025-en procesov2.pdf | `c04f44efcccf…` | `REUSED (home: teleco)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 2 | `src_0bc5d20dcc91895f` | Stallings.William.-.Sistemas.Operativos.5ed.pdf | `0bc5d20dcc91…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 3 | `src_0fc90b2695369475` | FADENA - SO2 - Unidad 3 - Semana 6 - 2026.pdf | `0fc90b269536…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 4 | `src_a9a056742dcf69ae` | FADENA - SO2 Unidad 2 - Semana 4 - 2026.pdf | `a9a056742dcf…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 5 | `src_bel_algoritmos_estructuras_python` | algoritmos-y-estructuras-de-datos-en-python-digital.pdf | `e98da4f1f537…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 6 | `src_d253687930308e41` | FADENA - SO2 Unidad 2 - Semana 5 - 2026.pdf | `d25368793030…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 7 | `src_e9682dece40b58ab` | FADENA SO II -  S5-A1 - 2026.pdf | `e9682dece40b…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 8 | `src_f009c4e75f5ca3f2` | FADENA SO II - S6-A1 - 2026 (OBLIGATORIA).pdf | `f009c4e75f5c…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 9 | `src_fadena_prog_arboles` | prog_arboles.pdf | `241af51b9e0b…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 10 | `src_fadena_prog_archivos` | prog_archivos.pdf | `ead0e969f47d…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 11 | `src_fadena_prog_lineales` | prog_lineales.pdf | `d03d7669e19a…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 12 | `src_fadena_prog_punteros` | prog_punteros.pdf | `4ece5c39d64e…` | `NATIVE` | `IMPLEMENTATION, REFERENCE` | `NOT_ESTABLISHED (D4)` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 13 | `src_fadena_so_concurrencia` | so_concurrencia.pdf | `4c38c87d686d…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 14 | `src_fadena_so_memoria` | so_memoria.pdf | `869c24589732…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 15 | `src_fadena_so_planificacion` | so_planificacion.pdf | `26cfba6fe469…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 16 | `src_fadena_so_procesos` | so_procesos.pdf | `4f9413043a5e…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 17 | `src_goodrich_dsa_python` | Data Structures and Algorithms in Python.pdf | `c96e808d96bf…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 18 | `src_joyanes_fundamentos` | Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf | `1217dd5e6038…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 19 | `src_kurose_computer_networking` | Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf | `7599e188b264…` | `REUSED (home: teleco)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 20 | `src_martin_clean_code` | Codigo limpio - Robert Cecil Martin.pdf | `92876e0f2bc2…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 21 | `src_ramalho_fluent_python` | luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf | `db97c77518c6…` | `NATIVE` | `—` | `COMPLEMENTARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 22 | `src_rosen_matematicas_discretas` | Matematicas_Discretas_Rosen_IA_16MB.pdf | `c8146cecbc5e…` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 23 | `src_spraul_think_like_a_programmer` | Think_Like_a_Programmer.pdf | `07e0f6d0fb24…` | `NATIVE` | `METHODOLOGICAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 24 | `src_stallings_computer_security` | Computer_Security_Stallings_3rd_Ed.pdf | `0aa9aa4cc0b2…` | `NATIVE` | `—` | `COMPLEMENTARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 25 | `src_stallings_os_internals_7ed` | Operating Systems - Internals and Design Principles 7th.pdf | `76e248a62974…` | `REUSED (home: so2)` | `—` | `COMPLEMENTARY` | `ALLOWED_FADENA_TO_SOC` | FOLDER_ABSENT (en fadena-so2) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 26 | `src_sweigart_automate_boring_stuff` | Automate the Boring Stuff with Python.pdf | `a5d156fbb378…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE (Nativa)` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |

### Cuaderno `fadena-lenguajes` (17 relaciones)

| # | `source_id` | Documento físico | SHA-256 | Pertenencia | Rol declarado | Función curricular | Política D3-C | Soporte físico | Evid. previa | Estado L3 | Estado release propuesto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 27 | `src_1149ca3399b6dd85` | Semana06 - Clase 01 - Parte 1.pdf | `1149ca3399b6…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 28 | `src_115f0bc876b44be8` | Clase3LP.pdf | `115f0bc876b4…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 29 | `src_7ba98d836c32fe4b` | Manual de referencia de C v1.1.docx.pdf | `7ba98d836c32…` | `NATIVE` | `REFERENCE` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 30 | `src_8ac0eed0a6121c6a` | Clase4LP.pdf | `8ac0eed0a612…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 31 | `src_fadena_leng_clase1` | Clase1.pdf | `349766430b88…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 32 | `src_fadena_leng_clase2` | Clase2.pdf | `ed5eab08cd52…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 33 | `src_fadena_prog_arboles` | prog_arboles.pdf | `241af51b9e0b…` | `REUSED (home: soc)` | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 34 | `src_fadena_prog_archivos` | prog_archivos.pdf | `ead0e969f47d…` | `REUSED (home: soc)` | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 35 | `src_fadena_prog_lineales` | prog_lineales.pdf | `d03d7669e19a…` | `REUSED (home: soc)` | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 36 | `src_fadena_prog_punteros` | prog_punteros.pdf | `4ece5c39d64e…` | `REUSED (home: soc)` | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 37 | `src_fdc4df20e0f9f99e` | Guia Practica 6.pdf | `fdc4df20e0f9…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 38 | `src_joyanes_fundamentos` | Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf | `1217dd5e6038…` | `REUSED (home: soc)` | `PRIMARY, METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 39 | `src_marzal_intro_programacion_c` | Introduccion-a-la-programacion-en-C.pdf | `dc44a8665f2b…` | `NATIVE` | `METHODOLOGICAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 40 | `src_spraul_think_like_a_programmer` | Think_Like_a_Programmer.pdf | `07e0f6d0fb24…` | `REUSED (home: soc)` | `METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 41 | `src_stallman_gnu_c_manual` | GNU-c-language-manual.pdf | `fa5f80f8da3c…` | `NATIVE` | `REFERENCE` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 42 | `src_sweigart_automate_boring_stuff` | Automate the Boring Stuff with Python.pdf | `a5d156fbb378…` | `REUSED (home: soc)` | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 43 | `src_urrutia_programacion_c_principiantes` | Programacion-c-principiantes-gorka-urrutia.pdf | `776399a65bec…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |

### Cuaderno `fadena-so2` (14 relaciones)

| # | `source_id` | Documento físico | SHA-256 | Pertenencia | Rol declarado | Función curricular | Política D3-C | Soporte físico | Evid. previa | Estado L3 | Estado release propuesto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 44 | `src_0bc5d20dcc91895f` | Stallings.William.-.Sistemas.Operativos.5ed.pdf | `0bc5d20dcc91…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `NOT_FOUND` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 45 | `src_0fc90b2695369475` | FADENA - SO2 - Unidad 3 - Semana 6 - 2026.pdf | `0fc90b269536…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 46 | `src_a9a056742dcf69ae` | FADENA - SO2 Unidad 2 - Semana 4 - 2026.pdf | `a9a056742dcf…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 47 | `src_d253687930308e41` | FADENA - SO2 Unidad 2 - Semana 5 - 2026.pdf | `d25368793030…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 48 | `src_e9682dece40b58ab` | FADENA SO II -  S5-A1 - 2026.pdf | `e9682dece40b…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 49 | `src_f009c4e75f5ca3f2` | FADENA SO II - S6-A1 - 2026 (OBLIGATORIA).pdf | `f009c4e75f5c…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 50 | `src_fadena_so2_clase1` | Clase1SOII.pdf | `a92d5b22837a…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 51 | `src_fadena_so2_clase2` | clase2SOII.pdf | `d3b4fecfde23…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 52 | `src_fadena_so_concurrencia` | so_concurrencia.pdf | `4c38c87d686d…` | `REUSED (home: soc)` | `PRIMARY, METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 53 | `src_fadena_so_memoria` | so_memoria.pdf | `869c24589732…` | `REUSED (home: soc)` | `COMPLEMENTARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 54 | `src_fadena_so_planificacion` | so_planificacion.pdf | `26cfba6fe469…` | `REUSED (home: soc)` | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 55 | `src_fadena_so_procesos` | so_procesos.pdf | `4f9413043a5e…` | `REUSED (home: soc)` | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 56 | `src_stallings_computer_security` | Computer_Security_Stallings_3rd_Ed.pdf | `0aa9aa4cc0b2…` | `REUSED (home: soc)` | `IMPLEMENTATION` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 57 | `src_stallings_os_internals_7ed` | Operating Systems - Internals and Design Principles 7th.pdf | `76e248a62974…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |

### Cuaderno `fadena-std` (30 relaciones)

| # | `source_id` | Documento físico | SHA-256 | Pertenencia | Rol declarado | Función curricular | Política D3-C | Soporte físico | Evid. previa | Estado L3 | Estado release propuesto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 58 | `src_032c52bff94a0743` | 6- Ejercicios recursividad.pdf | `032c52bff94a…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 59 | `src_0960283d5cef8dee` | 2 - Álgebra Relacional y Cálculo Relacional - Presentación.pdf | `0960283d5cef…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 60 | `src_3102eb1e89e2229e` | 5- Ejercicios estructuras de datos.pdf | `3102eb1e89e2…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 61 | `src_3e2e8abda5f55c17` | 1 - Fundamentos del Modelo Relacional.pdf | `3e2e8abda5f5…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 62 | `src_52ff5ff3e07c1da5` | 2 - Álgebra Relacional y Cálculo Relacional - Ejercicios.pdf | `52ff5ff3e07c…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 63 | `src_53ef2a7243ae3f63` | 2 - Álgebra Relacional y Cálculo Relacional.pdf | `53ef2a7243ae…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 64 | `src_56cfdbe35123c49e` | 7 - SQL Básico - Alternativas Entorno Interactivo.pdf | `56cfdbe35123…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 65 | `src_6dbdc8e943261fa7` | 2 - Normalización de Bases de Datos - Ejercicios.pdf | `6dbdc8e94326…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 66 | `src_755be6c147ddc5dd` | 1 - SQL Básico - Presentación.pdf | `755be6c147dd…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 67 | `src_7822bc3cef85c783` | 1 - Diseño de Bases de Datos Relacionales.pdf | `7822bc3cef85…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 68 | `src_7ec00a3365f208e6` | 4 - SQL Básico - Ejercicios.pdf | `7ec00a3365f2…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 69 | `src_9946be0e7d11161a` | 2 - Normalización de Bases de Datos.pdf | `9946be0e7d11…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 70 | `src_9e866bf082e52dd7` | 1 - Fundamentos del Modelo Relacional - Ejercicios.pdf | `9e866bf082e5…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 71 | `src_a01b9809f37fb47b` | 1 - Diseño de Bases de Datos Relacionales - Ejercicios.pdf | `a01b9809f37f…` | `NATIVE` | `IMPLEMENTATION` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 72 | `src_cf46d8f0e018b09e` | 1 - Diseño de Bases de Datos Relacionales - Presentación.pdf | `cf46d8f0e018…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 73 | `src_coronel_database_systems_11ed` | database-systems-design-implementation-and-management.pdf | `4990c35d1608…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 74 | `src_d7ff8399759d387a` | 1 - Estructuras de Datos.pdf | `d7ff8399759d…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 75 | `src_d946d1a5a3c32144` | 1 - Fundamentos del Modelo Relacional - Presentación.pdf | `d946d1a5a3c3…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 76 | `src_date_intro_sistemas_bd_7ed` | Introducción a los Sistemas de Bases de Datos, 7ma Edición, C. J. Date.pdf | `da02ac37e324…` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 77 | `src_de275591245abbd3` | 2 - Normalización de Bases de Datos - Presentación.pdf | `de275591245a…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 78 | `src_elmasri_navathe_sistemas_bd` | Fundamentos-de-Sistemas-de-Bases-de-Datos.pdf | `bed831d843c0…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 79 | `src_f3352475bc0cd360` | 6 - SQL Básico - Soluciones Ejercicios.pdf | `f3352475bc0c…` | `NATIVE` | `—` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 80 | `src_f93b8a264e20359c` | 3 - SQL Básico.pdf | `f93b8a264e20…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 81 | `src_fadena_prog_archivos` | prog_archivos.pdf | `ead0e969f47d…` | `REUSED (home: soc)` | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 82 | `src_fadena_std_unidad1` | UNIDAD1STD.pdf | `d22e633943c6…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 83 | `src_marques_bases_de_datos` | MercedesMarqués (2011) Bases de datos,1era Edición.pdf | `6a44b761bfdc…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 84 | `src_ramakrishnan_gehrke_dbms` | Raghu-Ramakrishnan-Johannes-Gehrke-Database-Management-Systems-McGraw-Hill-Education-2018.pdf | `808ae432589d…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 85 | `src_ramalho_fluent_python` | luciano-ramalho-fluent-python_-clear-concise-and-effective-programming-oreilly-media-2022.pdf | `db97c77518c6…` | `REUSED (home: soc)` | `IMPLEMENTATION` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 86 | `src_rosen_matematicas_discretas` | Matematicas_Discretas_Rosen_IA_16MB.pdf | `c8146cecbc5e…` | `REUSED (home: soc)` | `—` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 87 | `src_silberschatz_fundamentos_bd` | Fundamentos de bases de datos .pdf | `5e567f9df7f3…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |

### Cuaderno `fadena-teleco` (12 relaciones)

| # | `source_id` | Documento físico | SHA-256 | Pertenencia | Rol declarado | Función curricular | Política D3-C | Soporte físico | Evid. previa | Estado L3 | Estado release propuesto |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 88 | `src-guia-2025-c04f44ef` | GUIA_2025-en procesov2.pdf | `c04f44efcccf…` | `REUSED (home: soc)` | `METHODOLOGICAL` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 89 | `src_001b27137cf6680c` | Unidad 4 2026.pptx.pdf | `001b27137cf6…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 90 | `src_11195af8e0f2ef40` | Unidad 5 2026.pptx.pdf | `11195af8e0f2…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 91 | `src_2f1a5843cd1693ba` | Unidad 2 2026.pptx.pdf | `2f1a5843cd16…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 92 | `src_castro_fusario_comunicaciones_redes` | Comunicaciones_y_redes.pdf | `1a4caaa17e62…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 93 | `src_comer_internetworking_tcpip_v1` | Douglas E. Comer - Internetworking with TCP_IP Volume One. 1-Addison-Wesley (2013).pdf | `f04fee214066…` | `NATIVE` | `FORMAL` | `NOT_ESTABLISHED` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 94 | `src_corletti_seguridad_redes` | seguridad-en-redes.pdf | `3caa27ac33ca…` | `NATIVE` | `COMPLEMENTARY` | `COMPLEMENTARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 95 | `src_da10b53f20f2a647` | Unidad 3 2026.pptx.pdf | `da10b53f20f2…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 96 | `src_fadena_teleco_unidad1` | Unidad 1 - Infraestructura.pdf | `f7d3f8520381…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 97 | `src_kurose_computer_networking` | Computer Networking A Top-Down Approach (James W. Kurose, Keith W. Ross).pdf | `7599e188b264…` | `NATIVE` | `PRIMARY, METHODOLOGICAL` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 98 | `src_stallings_computer_security` | Computer_Security_Stallings_3rd_Ed.pdf | `0aa9aa4cc0b2…` | `REUSED (home: soc)` | `PRIMARY` | `UNRESOLVED` | `POLICY_NOT_GRANTED` | FOLDER_ABSENT (en fase0-soc) | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |
| 99 | `src_stallings_comunicaciones_redes_7ed` | Stallings - Comunicaciones y Redes de Computadores - 7ma edición.pdf | `b6b9613417b6…` | `NATIVE` | `PRIMARY` | `PRIMARY` | `NOT_APPLICABLE` | FOLDER_CONFIRMED | `PARTIAL` | `L3_NOT_DEMONSTRATED` | `PENDING_HUMAN_DECISION` |

---

## 4. Agrupación estructurada del universo para decisión humana

Para permitir una resolución ordenada y minimizar la complejidad de adjudicación, las 99 relaciones se clasifican en los siguientes 5 grupos estructurales:

| Grupo | Descripción estructural | Cantidad | Estado de soporte | Situación técnica en runtime |
|---|---|---:|---|---|
| **CP089 Adjudicadas** | Relaciones con coincidencia exacta en su carpeta nativa, sin rol conflictivo (`PRIMARY` o `—`), adjudicadas en CP089 como `NATIVE / PRIMARY`. | 47 | Soporte físico nativo confirmado (`FOLDER_CONFIRMED`). | Técnicamente permitidas en `notebook_sources`. |
| **G1 — Roles Semánticos** | Relaciones con coincidencia nativa física en carpeta, pero con roles declarados descriptivos (`IMPLEMENTATION`, `REFERENCE`, `METHODOLOGICAL`, `FORMAL`). Clasificadas bajo D1-A como `NATIVE`, con función curricular no establecida (`NOT_ESTABLISHED`). | 19 | Soporte físico nativo confirmado (`FOLDER_CONFIRMED`). | Técnicamente permitidas en `notebook_sources`. |
| **G2 — Nativas Complementarias** | Relaciones con soporte físico nativo en carpeta y rol declarado `COMPLEMENTARY`. Resueltas bajo D2-A como `NATIVE / COMPLEMENTARY`. | 8 | Soporte físico nativo confirmado (`FOLDER_CONFIRMED`). | Técnicamente permitidas en `notebook_sources`. |
| **G3-A — Reutilización FADENA → SOC** | Relaciones con home en `fadena-so2` reutilizadas en `fase0-soc`. Autorizadas formalmente bajo la política D3-C como `REUSED / COMPLEMENTARY`. | 7 | Soporte físico presente en `fadena-so2` (`FOLDER_ABSENT` en `fase0-soc`). | Técnicamente permitidas en `notebook_sources`. |
| **G3-B — Reutilización SOC → FADENA** | Relaciones con home en `fase0-soc` asociadas a cuadernos FADENA (`lenguajes`, `so2`, `std`, `teleco`). Fuera de cobertura de D3-C (`POLICY_NOT_GRANTED`), sin función asignada. | 17 | Soporte físico en `fase0-soc` (`FOLDER_ABSENT` en cuadernos FADENA). | Técnicamente permitidas en `notebook_sources` (discrepancia con política). |
| **G4 — Bundle Punteros** | Relación `fase0-soc` → `src_fadena_prog_punteros` con roles coexistentes `IMPLEMENTATION, REFERENCE`. Resuelta bajo D4/D1-A como `NATIVE`, función no establecida. | 1 | Soporte físico nativo confirmado (`FOLDER_CONFIRMED`). | Técnicamente permitida en `notebook_sources`. |
| **TOTAL** | **Universo íntegro del release scope** | **99** | **75 confirmadas / 24 ausentes** | **99 permitidas en `notebook_sources`** |

---

## 5. Paquete de decisiones humanas mínimas requeridas

Para levantar el bloqueo de C2, la persona responsable del producto debe adoptar tres decisiones estructuradas:

### 5.1 Decisión D1 — Paquete de Autorización L3 de Release

* **Contexto:** 82 relaciones poseen soporte nativo o cobertura bajo la política D3-C (47 adjudicadas + 19 G1 + 8 G2 + 7 G3-A + 1 G4 = 82 relaciones).
* **Pregunta de decisión:** ¿Se aprueba formalmente el paquete de estas 82 relaciones (o el conjunto resultante tras D2) como fuentes oficiales autorizadas para el release de TALOS Gate B?
* **Alternativas:**
  * **D1-A (Aprobación en Bloque):** Conceder formalmente el grant L3 a las 82 relaciones candidatas firmes bajo el propósito general *"Inclusión como material bibliográfico autorizado en el release pedagógico de TALOS Gate B"*.
  * **D1-B (Aprobación Selectiva por Cuaderno):** Emitir la autorización cuaderno por cuaderno, ratificando la lista granularmente.
  * **D1-C (Rechazo / Pospuesto):** Requerir auditoría académica externa antes de otorgar cualquier grant formal.
* **Efecto normativo:** La opción D1-A o D1-B generará el artefacto vinculante `config/l3_authorization_manifest.json` con metadatos de firma, fecha y autoridad responsable.

### 5.2 Decisión D2 — Resolución de las 17 relaciones SOC → FADENA

* **Contexto:** 17 relaciones cross-curriculum (`fase0-soc` → FADENA) carecen de soporte bajo la política D3-C (`POLICY_NOT_GRANTED`) y su PDF físico reside en `fuentes/fase0-soc/`. No obstante, están asociadas en la tabla `notebook_sources` de desarrollo.
* **Opciones disponibles para la autoridad de producto:**
  * **Opción D2-A (Recomendada / Máximo aislamiento curricular):**
    * **Decisión:** Excluir las 17 relaciones del release scope de FADENA.
    * **Justificación:** Los cuadernos de FADENA (`lenguajes`, `so2`, `std`, `teleco`) deben sostenerse exclusivamente sobre su propio material curricular nativo. Esto elimina la dependencia cruzada y simplifica el gobierno documental.
    * **Impacto técnico:** En la base de datos o en la allowlist operativa de provisioning, las 17 relaciones no se incluyen en `notebook_sources` para los cuadernos FADENA.
  * **Opción D2-B (Ampliación de Política D3-C a Bidireccional):**
    * **Decisión:** Ampliar formalmente la política curricular de reutilización, reconociendo que los cuadernos FADENA pueden utilizar fuentes de Fase 0 (SOC) con rol `COMPLEMENTARY`.
    * **Justificación:** Se considera pedagógicamente enriquecedor que los estudiantes de FADENA puedan consultar apuntes o textos introductorios de programación.
    * **Impacto técnico:** Se incorporan las 17 relaciones al manifiesto L3 con estatus `AUTHORIZED_REUSED_COMPLEMENTARY` y se conservan en la allowlist técnica.
  * **Opción D2-C (Tratamiento Selectivo):**
    * **Decisión:** Autorizar únicamente las relaciones relevantes para una materia (ej. material de programación en C para `fadena-lenguajes`) y excluir el resto.

### 5.3 Decisión D3 — Contrato de Exigibilidad Técnica de Runtime

* **Principio vinculante:** La allowlist técnica de retrieval y contexto DEBE derivarse estrictamente de las relaciones que cuenten con autorización L3 formal en el manifiesto de release.
* **Requisito no funcional normativo:** En runtime, ninguna fuente cuyo `source_id` no pertenezca a la intersección `(notebook_sources ∩ l3_authorization_manifest)` podrá ser recuperada ni expandida hacia el prompt del modelo.

---

## 6. Esquema del Manifiesto de Autorización L3 (`config/l3_authorization_manifest.json`)

Para materializar las decisiones D1 y D2 sin ambigüedades, se define el siguiente esquema de datos auditable en formato JSON:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "TALOS L3 Authorization Manifest",
  "type": "object",
  "required": [
    "manifest_version",
    "gate",
    "issued_date",
    "decision_maker",
    "decision_maker_role",
    "authorization_act_id",
    "purpose_statement",
    "grants"
  ],
  "properties": {
    "manifest_version": { "type": "string", "example": "1.0.0" },
    "gate": { "type": "string", "enum": ["GATE_B"] },
    "issued_date": { "type": "string", "format": "date", "example": "2026-10-02" },
    "decision_maker": { "type": "string", "example": "Nombre o Identificador del Responsable" },
    "decision_maker_role": { "type": "string", "example": "Product Owner / Autoridad Curricular" },
    "authorization_act_id": { "type": "string", "example": "ACT-TALOS-GATE-B-L3-20261002" },
    "purpose_statement": { "type": "string" },
    "grants": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "grant_id",
          "notebook_id",
          "source_id",
          "sha256",
          "document_filename",
          "membership",
          "curricular_function",
          "status"
        ],
        "properties": {
          "grant_id": { "type": "string" },
          "notebook_id": { "type": "string" },
          "source_id": { "type": "string" },
          "sha256": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
          "document_filename": { "type": "string" },
          "membership": { "type": "string", "enum": ["NATIVE", "REUSED"] },
          "curricular_function": { "type": "string", "enum": ["PRIMARY", "COMPLEMENTARY"] },
          "status": { "type": "string", "enum": ["AUTHORIZED", "EXCLUDED"] }
        }
      }
    }
  }
}
```

### 6.1 Plantilla de Grant (Ejemplo representativo con placeholders)

```json
{
  "grant_id": "GRANT-SOC-JOY-001",
  "notebook_id": "fase0-soc",
  "source_id": "src_joyanes_fundamentos",
  "sha256": "1217dd5e6038f150f454198b9645b7f4b89929ff88ba3744ca2c446082f4fb47",
  "document_filename": "Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf",
  "membership": "NATIVE",
  "curricular_function": "PRIMARY",
  "status": "AUTHORIZED"
}
```

---

## 7. Especificación técnica para el blindaje de `SectionExpander`

### 7.1 Diagnóstico de la vulnerabilidad en código

En `src/study_engine/retrieval/section_expander.py`:
```python
def expand_results(self, seed_results: list[SearchResult], window_size: int = 1) -> list[Chunk]:
    ...
    # Consulta actual sin restricción de source_id:
    cursor = self._db.execute(
        """
        SELECT id, document_id, source_id, content, page_start, pos_index, section, token_count
        FROM chunks
        WHERE document_id = ? AND pos_index BETWEEN ? AND ?
        ORDER BY pos_index ASC;
        """,
        (doc_id, start_pos, end_pos)
    )
```

### 7.2 Análisis comparativo de alternativas de solución

| Alternativa | Descripción técnica | Ventajas | Desventajas | Veredicto |
|---|---|---|---|---|
| **Opción A: Filtro SQL puro** | Agregar `AND source_id IN (?)` en la consulta SQL pasando `allowed_source_ids`. | El filtrado ocurre en el motor de base de datos; menor transferencia de datos en memoria. | Si la lista de fuentes es extremadamente grande, puede acercarse a límites de variables de SQLite; requiere propagar `allowed_source_ids` al método. | Viable pero insuficiente por sí sola ante desajustes. |
| **Opción B: Post-filtro en Python puro** | Conservar la consulta SQL y filtrar en Python: `[c for c in expanded if c.source_id in allowed_source_ids]`. | Muy simple de implementar; inmune a límites de sintaxis SQL. | Puede traer de la base de datos registros no autorizados a memoria antes de descartarlos. | Viable como filtro defensivo. |
| **Opción C: Defensa en Profundidad (Defense in Depth)** | **Combinar Opción A y Opción B**: Restringir la consulta SQL por `source_id IN (...)` Y re-verificar en memoria antes de empaquetar el contexto. | **Garantía absoluta de no-bypass**: Imposibilita la filtración incluso ante fallas de parámetro o inconsistencias relacionales en SQLite. | Ninguna significativa (sobrecarga de milisegundos despreciable en conjuntos locales). | **RECOMENDADA / ADOPTADA COMO ESPECIFICACIÓN** |

### 7.3 Especificación del cambio (Contrato técnico propuesto)

1. **Firma del método:**
   ```python
   def expand_results(
       self,
       seed_results: list[SearchResult],
       allowed_source_ids: list[str] | set[str] | None = None,
       window_size: int = 1
   ) -> tuple[list[Chunk], str]:
   ```
2. **Lógica SQL:**
   * Si `allowed_source_ids` es provisto, construir placeholders `AND source_id IN (?, ?, ...)` y ligar los parámetros.
   * Si `allowed_source_ids` es vacío (`set()`), retornar inmediatamente `([], "")`.
3. **Lógica en memoria (Doble candado):**
   * Antes de agregar un chunk a `expanded_chunks`:
     ```python
     if allowed_source_ids is not None and chunk.source_id not in allowed_source_ids:
         continue
     ```
4. **Propagación en `chat.py`:**
   * En `chat.py`, la invocación de `expander.expand_results` pasará explícitamente `allowed_source_ids=retrieval_source_ids`.

### 7.4 Especificación de fixtures de regresión para certificación C2

Para certificar que el blindaje es efectivo, se implementará la suite de pruebas con los siguientes dos casos adversariales:

1. **Fixture 1 (`test_section_expander_multi_source_document_boundary`):**
   * Crear un documento sintético `doc_shared` que contenga:
     * Chunk 1 (`pos_index=1`, `source_id='src_authorized'`)
     * Chunk 2 (`pos_index=2`, `source_id='src_unauthorized'`)
   * Ejecutar `expand_results` con `seed_results=[Chunk 1]` y `allowed_source_ids=['src_authorized']`.
   * **Criterio de éxito (PASS):** El resultado expandido contiene únicamente el Chunk 1. El Chunk 2 queda 100% excluido de la lista de chunks y del texto contextual expandido.
2. **Fixture 2 (`test_section_expander_cross_notebook_isolation`):**
   * Cuaderno A (`allowed_sources=['src_a']`) y Cuaderno B (`allowed_sources=['src_b']`).
   * Chunks contiguos pertenecientes a `src_b` en el mismo documento.
   * Ejecutar expansión en el contexto de Cuaderno A.
   * **Criterio de éxito (PASS):** Cero fragmentos de `src_b` son retornados.

---

## 8. Verificación de integridad de entorno

```text
DATABASE_PATH = data/web_state/knowledge_store.db
DATABASE_CHANGES = 0
INTEGRITY = PRESERVED (Sin modificaciones)

TECHNICAL_SOURCE_CHANGES = 0
GIT_TREE = UNTOUCHED (Código fuente, tests y rutas limpios)
```

---

## 9. Próximos pasos operativos

Una vez adoptadas formalmente las decisiones humanas por la persona responsable:
1. **Paso 1 (Adjudicación Humana):** La autoridad formal consigna su decisión sobre D1, D2 y D3.
2. **Paso 2 (Emisión del Manifiesto L3):** Generar y versionar `config/l3_authorization_manifest.json`.
3. **Paso 3 (Implementación del Blindaje en `SectionExpander`):** Aplicar la especificación técnica de Defensa en Profundidad en `section_expander.py` y `chat.py`.
4. **Paso 4 (Certificación C2):** Ejecutar el harness adversarial de certificación de C2 para transicionar formalmente su estado a `PASS / CLOSED`.

---
