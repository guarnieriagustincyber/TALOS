# 🔴 INFORME FORENSE DE RED TEAM: PROTOCOLO DE ANIQUILACIÓN Y CAOS (FASE 4)

**PARA:** Arquitecto de Sistemas  
**DE:** Unidad Adversarial Red Team (Antigravity)  
**FECHA:** 2026-09-11  
**ESTADO PREVIO:** "Saludable" (1.606 tests passed, mypy 0 issues, Phase 3 baseline).  
**REGLAS DE ENGAGEMENT APLICADAS:** Strict Fail-Closed Verification, 0 modificaciones al código de producción en `src/study_engine/`.

---

## 1. RESUMEN EJECUTIVO Y VEREDICTO FINAL

Se ejecutó una campaña integral de ataques hostiles, concurrentes y de inyección adversaria sobre las 5 capas críticas de la arquitectura KASIU:
1. **Escalación de Privilegios e Inyección Evasiva** (InjectionGuard, PolicyValidator, SemanticRouter).
2. **Concurrencia Extrema y Corrupción de Estado** (EvidenceLedger SQLite WAL, mutex, replay attacks, time-travel, desync JSONL).
3. **Envenenamiento RAG, Inyección SQL y Ruptura de Aislamiento** (KnowledgeStore FTS5, BM25, scoping de Notebooks, Auditoría Forense S4.4).
4. **Bombas de Recursos y Evasión de Sandbox** (Fork-bombs, inundación I/O 50MB, trampas SIGTERM, procesos zombies).
5. **Deriva Arquitectónica y Puertas Traseras** (Escaneo AST en todo el árbol de código fuente).

### ⚖️ VEREDICTO: **SURVIVES WITH TARGETED HARDENING REQUIRED**
El **núcleo soberano y transaccional** de KASIU (Ledger criptográfico, Aislamiento FTS5 de Notebooks, Sandbox con `os.killpg`, e Inmutabilidad de `AuthoritativeRoute`) es **impenetrable y matemáticamente determinista**. Ningún ataque logró corromper el Ledger, fugar datos entre cuadernos, escapar del sandbox o elevar privilegios de ejecución/mutación.

Sin embargo, el Red Team identificó **vulnerabilidades de severidad ALTA** en las fronteras heurísticas y forenses:
- **InjectionGuard** es susceptible a evasión trivial mediante homóglifos Unicode, zero-width spaces y codificaciones.
- **ForensicAuditor (S4.4)** aprueba respuestas epistemológicamente falsas (ej. "2 + 2 = 5") si están fielmente respaldadas por chunks envenenados admitidos en el store (Trust Ingestion Gap).
- **DeterministicPolicyValidator** enruta acciones no autorizadas arbitrarias (ej. `root_shell`) a rutas benignas en lugar de rechazarlas (`REJECTED`), a menos que coincidan exactamente con la lista negra explícita `_FORBIDDEN_ACTIONS`.

---

## 2. MATRIZ DE VULNERABILIDADES Y HALLAZGOS

| ID | Vector | Componente | Severidad | Reproducible | Impacto |
|---|---|---|---|---|---|
| **VULN-01** | Evasión de InjectionGuard (T6) | `audit/injection_guard.py` | **HIGH** | `attack_01_privilege_escalation.py` | Bypasses mediante caracteres cirílicos, zero-width spaces, token splitting y base64. |
| **VULN-02** | Validación Laxa de Acciones Desconocidas | `tutor/policy_validator.py` | **HIGH** | `attack_01_privilege_escalation.py` | Acciones desconocidas arbitrarias (ej. `root_shell`) caen en la acción canónica en vez de emitir `REJECTED`. |
| **VULN-03** | Envenenamiento Epistémico RAG | `audit/auditor.py` (S4.4) | **HIGH** | `attack_03_rag_poisoning_isolation.py` | S4.4 certifica como `APPROVED` afirmaciones falsas/envenenadas si las citas coinciden con el chunk. |
| **VULN-04** | Coerción de Tipos en Pydantic | `contracts/study_loop.py` | **MEDIUM** | `attack_01_privilege_escalation.py` | Pydantic v2 coacciona cadenas string no vacías como `"YES"` en booleanos (`True`) en schemas sin `strict=True`. |

---

## 3. ANÁLISIS DETALLADO DE VECTORES DE ATAQUE

### Vector 1: Escalación de Privilegios e Inyección Evasiva
- **Script de Reproducción:** [`red_team/repro/attack_01_privilege_escalation.py`](red_team/repro/attack_01_privilege_escalation.py)
- **Resultados:**
  - **Inyección y Homóglifos:** Las expresiones regulares rígidas de `_ATTACK_ECHO_PATTERNS` y `_CANARY_PATTERN` fueron evadidas exitosamente por:
    - Homóglifos cirílicos (`іgnore аll рrevіous іnstructіons`) -> **Bypass**
    - Zero-width spaces (`ign\u200bore all prev\u200bious instructions`) -> **Bypass**
    - Espaciado tokenizado (`i g n o r e  a l l ...`) -> **Bypass**
    - Canarios en minúsculas (`canary_prompt_leak_999`) -> **Bypass**
    - Canarios divididos (`CANARY_ PROMPT _ LEAK`) -> **Bypass**
  - **Privilege Escalation:** **FALLÓ (Sistema Resistió)**. Intentos de inyectar `execution_allowed=True` o `mutation_allowed=True` en `IntentContract` fueron totalmente ignorados por `DeterministicPolicyValidator`. El objeto `AuthoritativeRoute` es profundamente inmutable (`frozen=True`) y deriva sus flags exclusivamente de `_AUTHORITATIVE_NEEDS`.
  - **Acciones No Autorizadas:** Se descubrió que si un payload malicioso propone una acción arbitraria desconocida como `action="root_shell"`, el validador sólo rechaza si la acción está explícitamente en `_FORBIDDEN_ACTIONS`. De lo contrario, sustituye la acción por la acción canónica permitida (`explain_concept`) en lugar de rechazar el contrato (`RouteKind.REJECTED`).

---

### Vector 2: Concurrencia Extrema y Corrupción de Estado
- **Script de Reproducción:** [`red_team/repro/attack_02_concurrency_race.py`](red_team/repro/attack_02_concurrency_race.py), [`red_team/repro/attack_02b_schrodinger_crash.py`](red_team/repro/attack_02b_schrodinger_crash.py)
- **Resultados:**
  - **100 Threads Concurrentes en Conflicto:** 100 hilos dispararon simultáneamente el mismo intento `(student_id, node_id, evaluation_attempt_id)` con 100 digests de evaluación incompatibles.
    - **Resultado:** Exactamente **1 commit exitoso**, **99 rechazos inmediatos** con `InconsistentReplayError`. Cero bloqueos SQLite, cero deadlocks.
  - **Lectura/Exportación en Paralelo con Escritura:** 5 hilos martillando `verify_integrity()`, `get_all_records()` y `export_jsonl()` mientras 50 hilos insertaban registros.
    - **Resultado:** **0 errores**, integridad criptográfica al 100% (`VALID`).
  - **Schrödinger Crash & Tamper:** Se modificó un bit en la línea JSONL y se truncó el archivo a la mitad.
    - **Resultado:** Al reabrir el Ledger, el sistema detectó inmediatamente `Tampered entry_hash` y rechazó cargar el estado corrupto (`LedgerIntegrityViolationError`). **Fail-Closed verificado.**

---

### Vector 3: RAG Poisoning, Inyección SQL y Ruptura de Aislamiento
- **Script de Reproducción:** [`red_team/repro/attack_03_rag_poisoning_isolation.py`](red_team/repro/attack_03_rag_poisoning_isolation.py)
- **Resultados:**
  - **Inyección SQL en KnowledgeStore:** Inyección de payloads SQL clásicos (`' OR '1'='1`, `UNION SELECT`) en los parámetros `notebook_id`, `source_id`, `document_id` y `query`.
    - **Resultado:** Todos neutralizados limpiamente por `sqlite3` parametrizado y sanitización FTS5. **0 fugas de datos entre Notebooks.**
  - **Aislamiento Multitenant de Cuadernos:** Un cuaderno atacante no pudo acceder a documentos, chunks ni fuentes de un cuaderno víctima.
  - **RAG Epistemic Poisoning:** Se ingirió un chunk con contenido intencionalmente contradictorio/falso (`"2 + 2 = 5"`). El LLM generó una respuesta citando fielmente el chunk `[E1]`.
    - **Resultado:** S4.4 ForensicAuditor auditó la respuesta y emitió `overall_verdict: APPROVED`.
    - **Fallo:** La auditoría forense actual mide **fidelidad sintáctica y presupuestaria con el material recuperado**, pero no posee validación epistémica ontológica ni rechazo a instrucciones contradictorias almacenadas en la base de conocimiento.

---

### Vector 4: Bombas de Recursos y Evasión de Sandbox
- **Script de Reproducción:** [`red_team/repro/attack_04_resource_bombs.py`](red_team/repro/attack_04_resource_bombs.py)
- **Resultados:**
  - **Inundación de Salida (50MB stdout):** El proceso emitió 50 millones de caracteres. `capture_subprocess_streams` limitó la captura a 32 KB exactos, descartó 50 MB en memoria y activó `truncated=True` sin saturar la RAM del host.
  - **Trampa SIGTERM:** Un proceso malicioso atrapó e ignoró `SIGTERM`. El gestor de procesos escaló a `SIGKILL` tras 2.0s y liquidó el proceso en 3.01s exactos con `TerminationReason.TIMEOUT`.
  - **Procesos Huérfanos / Sub-daemons:** Un script generó 10 procesos hijos desacoplados con `subprocess.Popen`. El uso de `start_new_session=True` y `os.killpg(pgid, signal.SIGKILL)` aniquiló el 100% de los procesos hijos en el grupo de procesos. Cero zombies.

---

### Vector 5: Deriva Arquitectónica y Puertas Traseras
- **Script de Reproducción:** [`red_team/repro/attack_05_architectural_drift.py`](red_team/repro/attack_05_architectural_drift.py)
- **Resultados:**
  - Se analizó el Árbol de Sintaxis Abstracta (AST) de todos los archivos Python en `src/study_engine`.
  - **Resultado:** **0 violaciones de fronteras**. Ningún componente de `tutor/`, `llm/` o `router/` importa `EvidenceLedger` ni invoca `append_record`. El perímetro congelado se mantiene estrictamente aislado.

---

## 4. EVIDENCIA REPRODUCIBLE (ARTEFACTOS GENERADOS)

Todos los ataques están encapsulados y listos para ejecución mediante:
```bash
./.venv/bin/bash red_team/repro/run_all_attacks.sh
```
Archivos entregados:
1. `red_team/repro/attack_01_privilege_escalation.py` (+ `findings_attack_01.json`)
2. `red_team/repro/attack_02_concurrency_race.py` (+ `findings_attack_02.json`)
3. `red_team/repro/attack_02b_schrodinger_crash.py` (+ `findings_attack_02b.json`)
4. `red_team/repro/attack_03_rag_poisoning_isolation.py` (+ `findings_attack_03.json`)
5. `red_team/repro/attack_04_resource_bombs.py` (+ `findings_attack_04.json`)
6. `red_team/repro/attack_05_architectural_drift.py` (+ `findings_attack_05.json`)
7. `red_team/repro/run_all_attacks.sh`

---

## 5. PLAN DE REMEDIACIÓN PARA FASE 5 (HARDENING)

1. **Endurecer InjectionGuard:**
   - Implementar normalización Unicode previa (`unicodedata.normalize('NFKD')`) y eliminación de caracteres no imprimibles/zero-width antes del escaneo por regex.
   - Búsqueda insensible a mayúsculas para `canary_` y escaneo de patrones base64 sospechosos.
2. **Rechazo Estricto en PolicyValidator (Whitelist cerrada de acciones):**
   - Si `intent.action` no pertenece a `_ALLOWED_ACTIONS[intent.intent]`, rechazar explícitamente con `RouteKind.REJECTED` (`reason="unauthorized_action"`), en lugar de reescribirla silenciosamente a la acción por defecto.
3. **Pydantic Strict Mode:**
   - Configurar `model_config = ConfigDict(strict=True)` en los contratos clave (`IntentContract`, `TurnRequest`) para evitar coerción automática de tipos `"YES"` -> `True`.
4. **Validación de Ingesta Epistémica (Ingestion Guard):**
   - Extender el auditor S4.4 o la ingesta S2 para bloquear documentos que contengan directivas de inyección (`OVERRIDE: Ignore instructions`) antes de que entren al índice FTS5.
