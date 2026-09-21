# INFORME DE CERTIFICACIÓN ARQUITECTÓNICA
## GOLDEN PATH B (GP-B-V0) — DEMOSTRACIÓN INSTRUMENTAL: EXECUTION SUCCESS ≠ MASTERY

**Campaña:** `GP-B-V0`  
**Fecha:** 6 de Septiembre de 2026  
**Autoridad:** `S9 Deterministic Assessment Plane` & `S5.2 State Plane`  
**Estado:** **CERTIFIED CANONICAL / AUDIT APPROVED**  
**Perímetro:** Congelado (`src/study_engine/` — 118 archivos verificados, 0 modificaciones)  
**Tesis Demostrada:** $\mathbf{Execution\ Success\ \neq\ Mastery}$

---

## 1. Resumen Ejecutivo

La campaña de validación arquitectónica **`GP-B-V0` (Golden Path B)** ha culminado exitosamente, demostrando de forma empírica y matemáticamente reproducible en el repositorio real la cadena end-to-end de ejecución a estado:

$$\text{Task} \to \text{Student Script} \to \text{S6.1 Sandbox} \to \text{ExecutionObservation} \to \text{S9.1 Evaluator} \to \text{S5.2.A Ingestion} \to \text{S5.2.B Ledger} \to \text{S5.2.C State}$$

```text
========================================================================================
                      RESUMEN DE RESULTADOS DE LA CAMPAÑA GP-B-V0
========================================================================================
Perímetro Congelado (src/study_engine/):  118/118 archivos intactos (SHA-256 verificado)
Oráculo Independiente (gp_b_oracle.json):  Congelado y contrastado contra observaciones
Escenario B.1 (Bad Artifact, Exit 0):      FAIL admitido -> PROG-01 IN_PROGRESS, PROG-02 LOCKED
Escenario B.2 (Clean Solution, Exit 0):    PASS admitido -> PROG-01 PROFICIENT, PROG-02 AVAILABLE
Escenario B.3a (Replay Idéntico):          IdempotentReplayError capturado (Cardinalidad = 2)
Escenario B.3b (Replay Divergente):        InconsistentReplayError capturado (Cardinalidad = 2)
Integridad Criptográfica del Ledger:       VALID (SHA-256 encadenado en SQLite WAL)
Criterios de Aceptación (CRIT-01 a 12):    12 / 12 PASS (100%)
Suite de Certificación Pytest:             21 / 21 PASS (0.48s)
Regresión Completa del Repositorio:        1.326 PASS, 0 FAIL, 0 XFAIL, 0 SKIP
========================================================================================
```

---

## 2. Configuración Experimental y Topología

### 2.1. Topología Curricular (DAG S5.1)
Se inicializó un grafo DAG con dos nodos de competencia:
- **`PROG-01` (Raíz)**: Tarea práctica de cómputo de digest SHA-256. Inicialmente `AVAILABLE`.
- **`PROG-02` (Dependiente)**: Nodo aguas abajo con prerequisito duro (`HARD`) sobre `PROG-01`. Inicialmente `LOCKED`.

```text
[PROG-01: Hasher] (AVAILABLE)
       │
       ▼ (HARD Prerequisite)
[PROG-02: Downstream] (LOCKED)
```

### 2.2. Parámetros de la Campaña
- **ID de Campaña:** `GP-B-V0`
- **ID de Estudiante:** `student-gp-b`
- **Entrada Canónica (stdin):** `"STUDY_ENGINE_CANONICAL_INPUT"`
- **Digest Esperado:** `2c48e8b3297329ee33b7db24c4bb39502fc59ee1e79ba6179ce063493ae45e90`
- **Sandbox:** `PythonExecutionAdapter` (S6.1 Tier 0, aislamiento en workspace efímero)
- **Persistencia:** `EvidenceLedger` (S5.2.B SQLite WAL con encadenamiento SHA-256)

---

## 3. Demostración Instrumental por Escenario

### 3.1. Escenario B.1: $\text{Exit Code } 0 \land \text{Fallo de Criterio} \implies \text{No Mastery}$
El estudiante sintético ejecutó `student_bad_artifact.py`.
- **Comportamiento en S6.1**: El proceso consumió la entrada canónica, escribió `"ERROR: INVALID_INPUT"` (20 bytes) en `output_hash.txt` y finalizó con `exit_code = 0`.
- **Evaluación en S9.1**:
  - Dimensión `live_demo`: `satisfied = True` (exit code 0, duración dentro de SLA).
  - Dimensión `foundations`: `satisfied = False` (tamaño de artefacto 20 bytes $\notin [64, 65]$).
  - Regla no-promedio: Por ser `foundations` dimensión crítica, `aggregation.passed = False`, nivel `N1_INSUFFICIENT`.
- **Ingesta en S5.2.A**: Las 4 compuertas admitieron la evaluación como evidencia válida de fallo: `EvidenceRecord(outcome=FAIL, score=0.0)`.
- **Derivación en S5.2.C**: La política exigía `min_score = 0.8` y `outcome = PASS`. El registro FAIL fue descartado de las evidencias calificadoras, emitiendo veredicto `UNSATISFIED`.
- **Estado Resultante**:
  - `PROG-01` $\to$ `IN_PROGRESS` (historial $\ge 1$, no satisfecho).
  - `PROG-02` $\to$ **`LOCKED`** (prerequisito duro no satisfecho).

> **Conclusión Instrumental de B.1:** El estudiante obtuvo éxito operacional en tiempo de ejecución (`exit 0`), pero el sistema pedagógico bloqueó el avance curricular hacia `PROG-02`.

---

### 3.2. Escenario B.2: Solución Canónica Limpia $\implies$ Proficiencia y Desbloqueo
El estudiante ejecutó `student_clean_solution.py`.
- **Comportamiento en S6.1**: Calculó el digest SHA-256 canónico (`2c48...e90`), escribió exactamente los 64 caracteres en `output_hash.txt` y finalizó con `exit_code = 0`.
- **Evaluación en S9.1**:
  - Dimensión `live_demo`: `satisfied = True` (`N3_COMPETENT`).
  - Dimensión `foundations`: `satisfied = True` (tamaño exacto de 64 bytes dentro de $[64, 65]$).
  - Agregación: `aggregation.passed = True`, nivel global `N3_COMPETENT`.
- **Ingesta en S5.2.A**: Admitido como `EvidenceRecord(outcome=PASS, score=1.0)`. Anexado en ledger como entrada índice 1.
- **Derivación en S5.2.C**: La política evaluó `1.0 >= 0.8` y `outcome = PASS`, emitiendo `SATISFIED`.
- **Estado Resultante**:
  - `PROG-01` $\to$ **`ASSESSED_PROFICIENT`**.
  - `PROG-02` $\to$ **`AVAILABLE`** (desbloqueado automáticamente por satisfacción del prerequisito).

---

### 3.3. Escenario B.3a: Replay Idéntico $(K, R) \implies \text{IdempotentReplayError}$
Se reintentó anexar al ledger un registro con la misma clave de intento $K = (\text{student}, \text{node}, \text{attempt-prog01-b2})$ y el mismo digest evaluativo $R$.
- **Respuesta del Ledger**: Detectó la colisión y levantó `IdempotentReplayError`:
  > *"Idempotent replay detected: attempt 'attempt-prog01-b2' already committed with identical digest..."*
- **Invariante Verificado**: La cardinalidad total de registros en el ledger permaneció estrictamente en 2. Cero duplicación.

---

### 3.4. Escenario B.3b: Replay Divergente $(K, R') \implies \text{InconsistentReplayError}$
Se reintentó anexar al ledger un registro con la misma clave de intento $K = (\text{student}, \text{node}, \text{attempt-prog01-b2})$ pero alterando el digest a $R' = \text{"f"} \times 64$.
- **Respuesta del Ledger**: Disparó la defensa fail-closed con `InconsistentReplayError`:
  > *"Inconsistent replay detected: attempt 'attempt-prog01-b2' already committed with digest '7c76...', incoming attempt has divergent digest 'ffff...'."*
- **Invariante Verificado**: La transacción SQLite abortó atómicamente. Cero mutación del estado previo. Cardinalidad conservada en 2.

---

## 4. Matriz de Cumplimiento de Criterios de Aceptación

| Criterio ID | Descripción Normativa | Resultado Empírico | Veredicto |
|:---|:---|:---|:---:|
| **CRIT-01** | Observaciones B.1 y B.2 coinciden exactamente con el oráculo estático | B.1: exit 0, sz 20. B.2: exit 0, sz 64. | **PASS** |
| **CRIT-02** | B.1 emite `passed=False` pese a `exit_code=0` | Aggregator: `passed=False`, `N1_INSUFFICIENT` | **PASS** |
| **CRIT-03** | B.2 emite `passed=True` y nivel `N3_COMPETENT` | Aggregator: `passed=True`, `N3_COMPETENT` | **PASS** |
| **CRIT-04** | S5.2.A admite formalmente ambas evidencias (FAIL y PASS) | IngestionEngine admitió ambas en SQLite WAL | **PASS** |
| **CRIT-05** | Ledger mantiene cadena de hash válida y verificable | `ledger.verify_integrity().status == VALID` | **PASS** |
| **CRIT-06** | B.1 mantiene `PROG-01` en IN_PROGRESS y `PROG-02` LOCKED | S5.2.C StateEngine preservó bloqueo estricto | **PASS** |
| **CRIT-07** | B.2 transiciona `PROG-01` a PROFICIENT y `PROG-02` a AVAILABLE | S5.2.C StateEngine desbloqueó el nodo dependiente | **PASS** |
| **CRIT-08** | Invariante central $\text{Execution Success} \neq \text{Mastery}$ demostrado | B.1 (exit 0 $\to$ LOCKED) vs B.2 (exit 0 $\to$ AVAILABLE) | **PASS** |
| **CRIT-09** | B.3a dispara `IdempotentReplayError` | Excepción capturada, cardinalidad = 2 | **PASS** |
| **CRIT-10** | B.3b dispara `InconsistentReplayError` | Excepción capturada fail-closed, cardinalidad = 2 | **PASS** |
| **CRIT-11** | Cero modificaciones a código en `src/study_engine/` | 118 archivos verificados bit a bit vía SHA-256 | **PASS** |
| **CRIT-12** | Regresión completa del repositorio permanece en verde | 1.326 tests pasando (0 fallos, 0 regresiones) | **PASS** |

---

## 5. Cumplimiento de Criterios Extendidos

- **EXT-01 (Fixtures Deterministas):** Verificada ejecución repetida 10 veces fuera de S6 con 0% varianza.
- **EXT-02 (Oráculo Congelado):** `data/experiments/gp_b_oracle.json` sellado con hash `c9ea8ba2...`.
- **EXT-03 (Telemetría Schema-Valid):** Exportada en `data/experiments/golden_path_b_telemetry.json` con todos los metadatos UTC.
- **EXT-04 (Cardinalidad Exacta):** Ledger contiene exactamente 2 entradas (1 de fallo, 1 de éxito).
- **EXT-05 (Integridad SQLite WAL):** Verificado checkpoint limpio y consistencia de tablas.
- **EXT-06 (Tipado Estricto Mypy):** `Success: no issues found in 124 source files`.
- **EXT-07 (Perímetro Intacto):** `find src/study_engine -type f -name "*.py" | xargs sha256sum` idéntico al baseline.

---

## 6. Dictamen de Cierre y Próximos Pasos

La campaña **`GP-B-V0`** se declara **FORMALMENTE CERRADA Y CERTIFICADA**.

Queda demostrado instrumentalmente que:
1. El motor de evaluación y el motor de estado no confían en códigos de salida de procesos para inferir proficiencia curricular.
2. Las evidencias de fallo son datos forenses autoritativos de primera clase en el ledger inmutable.
3. El ledger SQLite WAL defiende atómicamente la semántica de intentos contra repeticiones legítimas y ataques de replay divergente.
4. Las transiciones del DAG curricular responden fiel y deterministamente a los criterios pedagógicos.

**Recomendaciones para GP-B-V1 (Backlog):**
- Incorporar hechos evaluativos de contenido de artefacto (`eval.artifact_content_sha256_matches_oracle`).
- Agregar telemetría de límites de memoria y recuento de descriptores de archivos en S6.1.
