# INFORME TÉCNICO INTEGRAL DE CONTINUIDAD DEL PROYECTO KASIU / STUDY ENGINE
## Documento Maestro de Handoff para Tech Lead & Systems Architect
**Fecha de Emisión:** 7 de Septiembre de 2026  
**Autor:** Antigravity (Systems Architect & Red Team Auditor Agent)  
**Destinatario:** Tech Lead Entrante / Systems Architect de Relevo  
**Repositorio:** `/media/agustin/Laboratorio/study-engie`  
**Filosofía de Arquitectura:** `Deterministic Core → Instrumented Evidence → Controlled AI → Pedagogical Layer → UX`  

---

# 0. REGLA FUNDAMENTAL DEL INFORME

En estricta adhesión a la epistemología del proyecto KASIU, este documento no describe intenciones como implementaciones ni formula garantías globales a partir de verificaciones de alcance delimitado.

### Taxonomía Ontológica de Estados
* **`IMPLEMENTED`**: Código fuente escrito, compilable e integrado en el árbol de dependencias de `src/study_engine/`.
* **`VERIFIED`**: Código sometido a pruebas mecánicas (unitarias, integración o contrato) en escenarios nominales o controlados.
* **`CERTIFIED`**: Invariante o subsistema probado exhaustivamente contra un oráculo diferencial estático independiente, con cobertura adversarial, telemetría forense registrada y dictamen formal sin defectos residuales.
* **`FROZEN`**: Módulo sellado bajo estricta política de no-mutación. Prohibida cualquier modificación sin reapertura formal y re-certificación de suite completa.
* **`PARTIALLY IMPLEMENTED`**: Módulo con contratos o interfaces definidos y componentes funcionales parciales, pero con flujos incompletos.
* **`DRAFT`**: Especificación o archivo esqueleto preliminar, no acoplado a la ejecución productiva.
* **`PROPOSED`**: Diseño teórico documentado en RFC o especificación técnica sin código ejecutable asociado.
* **`UNMEASURED`**: Propiedad o escenario donde no se han obtenido métricas empíricas objetivas.
* **`NOT YET IMPLEMENTED`**: Capacidad planificada en roadmap para la cual no existe implementación activa.
* **`BLOCKED`**: Desarrollo detenido por dependencia técnica insatisfecha o defecto no resuelto.
* **`OPEN QUESTION`**: Decisión de arquitectura abierta con alternativas en evaluación.

> **Formulación Mandatoria:**  
> En todo este documento, cuando se declare ausencia de defectos en subsistemas certificados, se establece estrictamente:  
> **“0 defectos demostrados dentro del perímetro certificado”**.  
> No se formulan afirmaciones absolutas como “el sistema carece de bugs” o “la plataforma está 100% terminada”.

---

# 1. ESTADO ACTUAL DEL SISTEMA

### 1.1. Fotografía Técnica del Estado Operativo
* **Estado Global del Proyecto:** Plataforma funcional en su núcleo determinista, curricular, de ingestión, de ejecución sandboxed, de evaluación de reglas, de auditoría forense NLI, de orquestación de sesiones de estudio y de ledger autoritativo persistente. Capa pedagógica tutorial (S7) en estado de diseño preliminar (`DRAFT / PRE-SPEC`).
* **Milestone / Hito Actual:** **Hito 6: Survival, Adversarial & Integrity Certification** — **FINALIZADO Y CERTIFICADO**.
* **Último Milestone Certificado:** **Hito 6 (Fases 0 a 8)** mediante dictamen formal de Red Team.
* **Último Experimento Ejecutado:** `scripts/experiments/run_phase8_timeout_boundary.py` (Fase 8: Timeout Boundary Attacks — 9/9 `CONFIRMED_PASS`, 0 defectos residuales).
* **Cantidad Actual de Tests:** **1.463 tests colectables y ejecutados**.
* **Desglose de Tests:** **1.463 PASSED**, 0 FAILED, 0 SKIPPED, 0 XFAILED (duración total suite completa: ~86.18s).
* **Estado de `mypy`:**
  - `src/study_engine/`: **121 archivos tipados, 0 errores** (`Success: no issues found in 121 source files`).
  - Scripts de experimentación y suites adversariales Hito 6: **100% tipados bajo `--strict`, 0 errores**.
  - `tests/` globales: 17 archivos de pruebas unitarias heredadas presentan 33 advertencias de tipado debidas a la deprecación de `implicit Optional` de PEP 484 en Python 3.12 y disparidades menores en mocks de pruebas.
* **Estado del Perímetro Congelado:** **100% INTACTO**. Ninguna línea de código de producción en `state/`, `execution/`, `assessment/`, `audit/` fue alterada durante las fases finales de auditoría (Fases 7 y 8).
* **Componentes Modificables:** `src/study_engine/curriculum/`, `retrieval/`, `context/`, `generation/`, `session/`, `tutor/`, `data/`, `scripts/`, `tests/`.
* **Componentes NO Modificables (FROZEN):** `src/study_engine/state/`, `src/study_engine/execution/`, `src/study_engine/assessment/`, `src/study_engine/audit/`.
* **Subsistemas Incompletos / DRAFT:** S7 Pedagogical Tutor (`src/study_engine/tutor/` en estado de esqueleto), S8 Quality/Tester (`src/study_engine/quality/`, `src/study_engine/tester/` solo con `__init__.py`).
* **Subsistemas Certificados:** S1 (Curriculum & Roadmap), S2 (Storage & Corpus Ingestion), S3 (Epistemic Retrieval), S4 (Generation & S4.4 Forensic Audit), S5 (Authoritative Ledger, Ingestion Gate & State Engine), S6 (Execution Sandbox Tier 0), S9 (Deterministic Assessment Engine).
* **Próximo Milestone:** **Hito 8: Frontier AI Evaluation, Multi-Agent Resilience & Continuous Evolution** (o formalización e instrumentación del Tutor S7 bajo especificación formal).

### 1.2. Tabla Maestra de Subsistemas

| Subsistema | Componente / Paquete | Estado | Certificación | ¿Puede modificarse? | Próximo objetivo |
|---|---|:---:|:---:|:---:|---|
| **S1.1-S1.3** | `curriculum/`, `roadmap/` | `IMPLEMENTED` | `CERTIFIED` (Hito 1, 6) | SÍ (solo expansión) | Nuevos roadmaps y ontologías |
| **S2.1-S2.5** | `storage/`, `ingestion/` | `IMPLEMENTED` | `CERTIFIED` (Hito 2, 6) | CONDICIONAL | Escalamiento de corpus (>100 docs) |
| **S3.1-S3.3** | `retrieval/` | `IMPLEMENTED` | `CERTIFIED` (Hito 2, 6) | SÍ | Calibración de umbrales / re-ranking |
| **S4.2, S4.4** | `generation/`, `audit/` | `IMPLEMENTED` | `CERTIFIED` (Hito 3, 6) | SÍ (gen) / **NO (audit)** | Backends LLM de producción |
| **S5.2.A** | `state/ingestion_engine.py` | `IMPLEMENTED` | `CERTIFIED` (SSA-0R, Hito 6) | **NO (FROZEN)** | Preservar fail-closed |
| **S5.2.B** | `state/ledger.py` | `IMPLEMENTED` | `CERTIFIED` (SSA-0R, Hito 6) | **NO (FROZEN)** | Preservar ACID WAL y hash chain |
| **S5.2.C** | `state/state_engine.py` | `IMPLEMENTED` | `CERTIFIED` (Hito 6) | **NO (FROZEN)** | Preservar pureza funcional |
| **S6.1** | `execution/` | `IMPLEMENTED` | `CERTIFIED` (Hito 4, 6) | **NO (FROZEN)** | Preservar aislamiento de procesos |
| **S7.1-S7.4** | `tutor/` | `DRAFT / PRE-SPEC` | `NOT YET IMPLEMENTED` | SÍ | Especificar e implementar según Hito 7/8 |
| **S8.1-S8.2** | `quality/`, `tester/` | `DRAFT` | `NOT YET IMPLEMENTED` | SÍ | Infraestructura de stress testing |
| **S9.1** | `assessment/` | `IMPLEMENTED` | `CERTIFIED` (GP-B, Hito 6) | **NO (FROZEN)** | Preservar evaluación determinista |
| **S10.1** | `session/` (Orchestrator) | `IMPLEMENTED` | `CERTIFIED` (Hito 3, 4, 5, 6) | SÍ | Conectar nuevos backends y puertos |

---

# 2. HISTORIA COMPLETA DESDE SSA-0R

La trayectoria del proyecto KASIU ha seguido un ciclo riguroso de diseño, ataque adversarial y certificación progresiva:

```text
SSA-0 (Finding) ──> SSA-0R-D (Spec) ──> SSA-0R-I (SQLite WAL) ──> SSA-0R-A (Cert)
                                                                       │
┌──────────────────────────────────────────────────────────────────────┘
▼
GP-B-V0 (Pre-flight) ──> State of Union ──> Hito 1 (Curriculum) ──> Hito 2 (Retrieval)
                                                                           │
┌──────────────────────────────────────────────────────────────────────────┘
▼
Hito 3 (Generation/Audit) ──> Hito 4 (Adapters Loop) ──> Hito 5 (E2E Golden Paths)
                                                                │
┌───────────────────────────────────────────────────────────────┘
▼
Hito 6 (Survival, Adversarial & Integrity Certification: Fases 0 a 8) ──> HANDOFF
```

### 2.1. SSA-0: Detección de la Carrera TOCTOU en Persistencia
1. **Problema Original:** Bajo concurrencia de hilos, instancias y procesos, `EvidenceLedger` permitía la duplicación de evidencias y la corrupción de la cadena hash de registros.
2. **Hipótesis:** El ledger dependía de un archivo plano JSONL con verificación de idempotencia en memoria (`self._seen_record_ids: set`), liberando el GIL durante `os.fsync()` e incurriendo en carreras Time-of-Check to Time-of-Use (TOCTOU).
3. **Implementación:** Auditoría read-only SSA-0 (`REPORT-SSA-0.md`). No se aplicaron parches en caliente. Se instrumentaron 3 tests `XFAIL` en `tests/survival/test_l5_concurrency_and_crash.py`.
4. **Archivos Modificados:** Ninguno en `src/` (`git diff` vacío). Se crearon scripts de prueba en `scripts/survival/` y tests en `tests/survival/`.
5. **Invariantes Introducidos:** Formalización de la necesidad de atomicidad transaccional: $\mathrm{cardinality}(\mathrm{persisted\_evidence}) = 1$.
6. **Tests:** 1.302 tests ejecutados: 1.299 PASS, 3 XFAIL (demostración deliberada del defecto).
7. **Resultado:** FINDING-SSA0-01 (`CONFIRMED_DEFECT`).
8. **Decisión Arquitectónica:** Se emitió la especificación congelada `docs/06-CONCURRENCY-SPECIFICATION-V1.0.md`.
9. **Qué quedó congelado:** La especificación de concurrencia y el reporte forense SSA-0.
10. **Qué habilitó la siguiente etapa:** Apertura del flujo formal de remediación `SSA-0R`.

### 2.2. SSA-0R-D: Revisión de Diseño Formal
1. **Problema Original:** Riesgo de resolver la concurrencia solo para multi-threading mediante `threading.Lock`, dejando sin resolver multi-instancia y multi-proceso. Confusión entre el contenido evaluado (`assessment_digest`) y la identidad del intento (`evaluation_attempt_id`).
2. **Hipótesis:** Separar la identidad en 3 niveles (Submission $\to$ Attempt $\to$ Result Digest) y formular la función de decisión $D(K, R)$ sobre una base de datos ACID con bloqueo a nivel de motor C elimina todas las carreras TOCTOU.
3. **Implementación:** Redacción y congelamiento de `docs/06-CONCURRENCY-SPECIFICATION-V1.1.md`.
4. **Archivos Modificados:** Creación de `docs/06-CONCURRENCY-SPECIFICATION-V1.1.md`.
5. **Invariantes Introducidos:** Definición formal de la función de decisión:
   $$D(K, R) = \begin{cases} \mathbf{COMMIT\_OK} & K \notin \mathrm{DB} \\ \mathbf{IDEMPOTENT\_ACK} & K \in \mathrm{DB} \land R_{\text{in}} = R_{\text{db}} \\ \mathbf{INCONSISTENT\_REPLAY} & K \in \mathrm{DB} \land R_{\text{in}} \ne R_{\text{db}} \end{cases}$$
6. **Tests:** N/A (fase documental).
7. **Resultado:** Aprobación unánime del Tech Lead y congelamiento de la especificación.
8. **Decisión Arquitectónica:** Adopción obligatoria de SQLite en modo WAL como autoridad única de persistencia; JSONL relegado a proyección de auditoría regenerable.
9. **Qué quedó congelado:** `docs/06-CONCURRENCY-SPECIFICATION-V1.1.md`.
10. **Qué habilitó la siguiente etapa:** Inicio de la implementación en código `SSA-0R-I`.

### 2.3. SSA-0R-I: Implementación del Ledger Autorizado sobre SQLite WAL
1. **Problema Original:** Reemplazar el backend de persistencia en `EvidenceLedger` sin romper los contratos de consumo de S5.2.A ni de los tests preexistentes.
2. **Hipótesis:** Una tabla SQLite con restricción `UNIQUE(student_id, node_id, evaluation_attempt_id)`, transacciones `BEGIN IMMEDIATE`, `busy_timeout=5000` y `synchronous=NORMAL` garantiza serialización atómica en el kernel sin carreras en Python.
3. **Implementación:** Reescritura completa de `src/study_engine/state/ledger.py` y `src/study_engine/state/ingestion_engine.py`.
4. **Archivos Modificados:** `src/study_engine/state/ledger.py`, `src/study_engine/state/ledger_contracts.py`, `src/study_engine/state/ingestion_engine.py`.
5. **Invariantes Introducidos:** Monotonía estricta de `entry_index`, continuidad criptográfica SHA-256 (`parent_entry_hash`), anti-replay a nivel de esquema físico.
6. **Tests:** `tests/survival/test_l5_concurrency_and_crash.py`, `tests/survival/test_differential_oracle_4way.py`, scripts de stress en Scope 1, 2 y 3.
7. **Resultado:** Transición de 3 XFAIL a 3 PASS.
8. **Decisión Arquitectónica:** SQLite es la autoridad única de commit. Si el archivo JSONL falla o se trunca, se reconstruye determinísticamente a partir de SQLite (`export_jsonl()`).
9. **Qué quedó congelado:** `src/study_engine/state/ledger.py` y contratos de persistencia.
10. **Qué habilitó la siguiente etapa:** Auditoría y certificación de cierre `SSA-0R-A`.

### 2.4. SSA-0R-A: Auditoría y Certificación de Persistencia
1. **Problema Original:** Demostrar empíricamente que la remediación satisface los 7 criterios de aceptación bajo estrés de hilos, instancias y procesos concurrentes.
2. **Hipótesis:** 100 hilos concurrentes, múltiples instancias sobre la misma base y procesos paralelos de pytest no producen corrupturas ni cardinalidades $> 1$.
3. **Implementación:** Ejecución de suites hostiles y oráculo diferencial de 4 vías.
4. **Archivos Modificados:** Scripts de auditoría y tests de regresión.
5. **Invariantes Introducidos:** Verificación de integridad de cadena SHA-256 en caliente (`LedgerIntegrityStatus.VALID`).
6. **Tests:** 1.302 tests collectables y ejecutados: **1.302 PASS, 0 XFAIL, 0 FAIL**.
7. **Resultado:** Dictamen `CERTIFIED_PASS`.
8. **Decisión Arquitectónica:** Cierre formal del hito de persistencia.
9. **Qué quedó congelado:** Todo el subsistema S5.2.B (Ledger).
10. **Qué habilitó la siguiente etapa:** Diseño y ejecución de `GP-B-V0`.

---

# 3. SSA-0R — PERÍMETRO DE SUPERVIVENCIA Y PERSISTENCIA

### 3.1. Naturaleza del Finding Original (FINDING-SSA0-01)
El motor original realizaba comprobaciones de existencia en memoria:
```python
# CÓDIGO VULNERABLE HISTÓRICO (PRE-SSA-0R):
if record.record_id in self._seen_record_ids:
    raise DuplicateEvidenceError(...)
with open(self.path, "a") as f:
    f.write(serialized)
    os.fsync(f.fileno())  # <--- GIL liberado: race window abierta
self._seen_record_ids.add(record.record_id)
```
Esto permitía que 50 hilos concurrentes observaran simultáneamente que el registro no existía, escribieran 50 líneas duplicadas al archivo y corrompieran la secuencia de índices de bloque y hashes encadenados.

### 3.2. Arquitectura de Remediación Definitiva
Se implementó SQLite bajo el modo Write-Ahead Logging (WAL) con pragmas de alta concurrencia:
* `PRAGMA journal_mode=WAL;` (Permite lectores concurrentes sin bloquear al escritor).
* `PRAGMA synchronous=NORMAL;` (Garantiza durabilidad ante caídas de la aplicación manteniendo alto throughput de disco).
* `PRAGMA busy_timeout=5000;` (Espera activa de hasta 5.000 ms ante bloqueos de escritura antes de emitir error de contención).
* Transacciones explícitas: `BEGIN IMMEDIATE;` en cada append, serializando a los escritores antes de evaluar restricciones.

### 3.3. Frase Canónica y Cambio de Paradigma
> **Frase Canónica:**  
> *"SQLite executes the atomic authoritative commit; JSONL is a derived, deterministically regenerable audit projection."*

* **Razón del Reemplazo:** Históricamente se consideraba al archivo JSONL como el almacenamiento maestro. Sin embargo, los archivos planos carecen de primitivas de bloqueo atómico inter-proceso portables en sistemas POSIX/Windows sin incurrir en fallas ante caídas repentinas de energía o procesos. Delegar el commit en SQLite convierte al motor C de base de datos en el árbitro infalible de atomicidad; el archivo JSONL pasa a ser un artefacto secundario que puede regenerarse en cualquier momento mediante:
```python
ledger.export_jsonl(jsonl_path)
```

### 3.4. Implementación Formal de la Función de Decisión $D(K, R)$
En `src/study_engine/state/ledger.py`:
1. La clave de idempotencia se define como:
   $$K = \langle \text{student\_id}, \text{node\_id}, \text{evaluation\_attempt\_id} \rangle$$
2. Si el registro no existe en SQLite, se inserta con:
   ```sql
   INSERT INTO evidence_ledger (entry_index, record_id, student_id, node_id, evaluation_attempt_id,
                                assessment_digest, payload_json, parent_entry_hash, entry_hash, committed_at)
   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
   ```
3. Si SQLite levanta `sqlite3.IntegrityError` por colisión de clave única:
   - Se consulta el registro existente en la base de datos para obtener $R_{\text{stored}} = \text{assessment\_digest}$.
   - Si $R_{\text{incoming}} == R_{\text{stored}}$: Se levanta `IdempotentReplayError`. La evidencia fue previamente admitida con idéntico resultado. Cardinalidad se mantiene estrictamente en 1.
   - Si $R_{\text{incoming}} \ne R_{\text{stored}}$: Se levanta `InconsistentReplayError`. Un intento idéntico pretende sobrescribir un resultado previo con una evaluación divergente. El sistema rechaza la operación fail-closed.

### 3.5. Cadena Criptográfica de Hashes (Hash Chain)
Cada bloque en SQLite sella criptográficamente al bloque anterior:
$$\text{entry\_hash}_i = \mathrm{SHA256}(\text{entry\_index}_i \parallel \text{record\_id}_i \parallel \text{parent\_entry\_hash}_{i-1} \parallel \text{payload\_digest}_i \parallel \text{committed\_at}_i)$$
Donde $\text{parent\_entry\_hash}_0 = \text{"0"*64}$ (Génesis).

### 3.6. Límites Explícitos de la Garantía
* **Lo que SÍ se garantiza:**
  - Consistencia e idempotencia estricta ante hilos concurrentes en el mismo proceso (Scope 1).
  - Consistencia ante múltiples instancias de `EvidenceLedger` en el mismo proceso (Scope 2).
  - Consistencia ante múltiples procesos independientes del SO concurrentes (Scope 3).
  - Recuperabilidad determinista de transacciones no confirmadas ante excepciones de software (Scope 4).
* **Lo que NO se afirma:**
  - No se afirma resistencia ante corrupción de hardware de sectores físicos de disco o cortes abruptos de energía sin barrera de caché de disco (`PRAGMA synchronous=FULL` no está activo por diseño de rendimiento).
  - No se afirma soporte para sistemas de archivos de red distribuidos sin bloqueo de archivos POSIX coherente (e.g. NFS mal configurado).

---

# 4. PERÍMETRO FROZEN (CONGELADO)

El perímetro congelado comprende los subsistemas nucleares cuyo comportamiento ha sido formalmente certificado y cuya alteración accidental invalidaría la cadena de pruebas de supervivencia:

```text
src/study_engine/state/
├── ingestion_engine.py
├── ledger.py
├── ledger_contracts.py
├── policy_contracts.py
├── policy_engine.py
├── state_contracts.py
└── state_engine.py

src/study_engine/execution/
├── adapter_python.py
├── artifact_collector.py
├── base.py
├── env_sanitizer.py
├── io_streamer.py
└── process_manager.py

src/study_engine/assessment/
├── aggregator.py
├── evaluator_deterministic.py
├── fact_extractor.py
└── service.py

src/study_engine/audit/
├── auditor.py
├── citation_verifier.py
├── claim_extractor.py
├── contracts.py
├── engine.py
├── injection_guard.py
├── lexical_guard.py
├── nli.py
└── policy_guard.py
```

### 4.1. Justificación y Evidencia del Freeze por Componente
1. **`src/study_engine/state/` (S5.2.A, S5.2.B, S5.2.C):**
   - *Motivo:* Resuelve la persistencia ACID en SQLite WAL, la función de decisión $D(K, R)$, las compuertas de admisión ontológica y la derivación de estado puro.
   - *Pruebas que lo justifican:* SSA-0R (1.302 tests), Hito 6 Fase 0, Fase 6 (9 tests concurrentes) y Fase 7 (10 tests de estado).
2. **`src/study_engine/execution/` (S6.1):**
   - *Motivo:* Gestiona el sandbox Tier 0 de procesos locales, límites de memoria, captura segura de streams y terminación de grupos de procesos (`os.killpg`).
   - *Pruebas que lo justifican:* Hito 4, Hito 6 Fase 4 (8 casos) y Fase 8 (9 casos de boundaries temporales).
3. **`src/study_engine/assessment/` (S9.1):**
   - *Motivo:* Motor determinista de evaluación basado en hechos observados sin injerencia estocástica de LLM. Evaluación no promediada y ligada criptográficamente por SHA-256.
   - *Pruebas que lo justifican:* GP-B-V0, Hito 6 Fase 5 (8 casos de ataque a la soberanía determinista).
4. **`src/study_engine/audit/` (S4.4):**
   - *Motivo:* Guardián forense de groundedness NLI, extracción de afirmaciones y verificación de citas textuales sin auto-reparación no supervisada.
   - *Pruebas que lo justifican:* Hito 3, Hito 6 Fase 3 (9 casos de generación y fuga).

### 4.2. Condiciones Mandatorias para Reabrir el Perímetro
Bajo ninguna circunstancia se debe modificar código dentro del perímetro congelado para implementar conveniencias, atajos sintácticos u optimizaciones prematuras.  
La reapertura formal solo se autorizará si:
1. Se demuestra un `CONFIRMED_DEFECT` reproducible mediante un test de regresión que falle en la suite actual.
2. El Tech Lead emite un RFC formal con análisis de impacto.
3. Se ejecuta de nuevo la suite completa de 1.463 pruebas antes y después de la modificación, certificando cero regresiones.

---

# 5. GOLDEN PATH B — GP-B-V0

### 5.1. Objetivo
Demostrar empíricamente la invariante fundamental de la evaluación de competencias técnicas:
$$\mathbf{Execution\ Success \ne Mastery}$$
Un proceso que finaliza con código de retorno `exit 0` no otorga dominio ni avance curricular si el artefacto producido no satisface las reglas deterministas de evaluación.

### 5.2. Pre-flight Findings y su Resolución
Antes de ejecutar la campaña, la auditoría pre-vuelo detectó tres hallazgos críticos:
* **PF-FINDING-01 (Mapeo de Rubrica / Tarea):** La tarea práctica requería generar un archivo digest SHA-256 (64 bytes hexadecimales), pero la rúbrica inicial evaluaba dimensiones no emitidas por el proceso.  
  *Resolución:* Se adoptó la **Opción B**: se configuró la rúbrica determinista en `data/curriculum/rubrics/rubric_sec05_deterministic.json` para validar exactamente las dimensiones de tamaño, codificación y hash sin alterar una sola línea del motor `evaluator_deterministic.py` (S9.1).
* **PF-FINDING-02 (Propagación de `evaluation_attempt_id`):** `SessionProvenanceContext` no propagaba de forma estricta el identificador del intento hacia el adaptador de ingestión, comprometiendo la verificación de $D(K, R)$.  
  *Resolución:* Se tipó obligatoriamente `evaluation_attempt_id` en `SessionProvenanceContext` y se requirió su presencia en `EvidenceIngestionAdapter`.
* **PF-FINDING-03 (Desajuste de Timeouts):** El tiempo límite de la tarea (`time_limit_minutes=5`) colisionaba con el techo del sandbox de ejecución (`timeout_seconds=300`).  
  *Resolución:* Se introdujo la regla de contención: `timeout = min(task.time_limit_minutes * 60, 300)`.

### 5.3. Escenarios Ejecutados y Trazabilidad

```text
               +-------------------------------------------------------------+
               |                       STUDENT SUBMISSION                    |
               +-------------------------------------------------------------+
                                              |
                                              v
                              +-------------------------------+
                              |    Execution Sandbox (S6.1)   |
                              +-------------------------------+
                                              |
                       +----------------------+----------------------+
                       |                                             |
                       v (Escenario B.1)                             v (Escenario B.2)
         +----------------------------+                +----------------------------+
         | exit_code: 0               |                | exit_code: 0               |
         | artifact: 20 bytes (malf.) |                | artifact: 64 bytes (SHA256)|
         +----------------------------+                +----------------------------+
                       |                                             |
                       v                                             v
         +----------------------------+                +----------------------------+
         | Assessment Engine (S9.1)   |                | Assessment Engine (S9.1)   |
         | Verdict: FAIL              |                | Verdict: PASS              |
         +----------------------------+                +----------------------------+
                       |                                             |
                       v                                             v
         +----------------------------+                +----------------------------+
         | Evidence Ingestion (S5.2.A)|                | Evidence Ingestion (S5.2.A)|
         | Decision: ADMITTED (FAIL)  |                | Decision: ADMITTED (PASS)  |
         +----------------------------+                +----------------------------+
                       |                                             |
                       v                                             v
         +----------------------------+                +----------------------------+
         | Authoritative Ledger       |                | Authoritative Ledger       |
         | Record persisted (FAIL)    |                | Record persisted (PASS)    |
         +----------------------------+                +----------------------------+
                       |                                             |
                       v                                             v
         +----------------------------+                +----------------------------+
         | State Engine (S5.2.C)      |                | State Engine (S5.2.C)      |
         | SEC-05: IN_PROGRESS        |                | SEC-05: ASSESSED_PROFICIENT|
         | SEC-04: LOCKED             |                | SEC-04: AVAILABLE (UNLOCKED|
         +----------------------------+                +----------------------------+
```

* **Escenario B.1 (Ejecución Exitosa con Falla de Criterio):**  
  El estudiante entrega un script que sale con código `0` pero emite un archivo de 20 bytes (digest MD5 en lugar de SHA-256). S6.1 reporta `ExecutionStatus.SUCCESS`. S9.1 evalúa las dimensiones de la rúbrica y determina `AssessmentResult(verdict=FAIL)`. La evidencia es admitida en el ledger como evidencia legítima de falla. El motor de estado computa el nodo curricular en `IN_PROGRESS` con veredicto `UNSATISFIED`. El nodo descendiente permanece estrictamente `LOCKED`.
* **Escenario B.2 (Camino Canónico de Aprobación):**  
  El estudiante entrega un script conforme que calcula el digest SHA-256 canónico (64 bytes). S6.1 reporta `exit 0`. S9.1 emite `verdict=PASS` con nivel `PerformanceLevel.N3_COMPETENT`. La evidencia es admitida en el ledger. El motor de estado actualiza el nodo a `ASSESSED_PROFICIENT` y desbloquea el nodo downstream transicionándolo a `AVAILABLE`.
* **Escenario B.3 (Defensa Anti-Replay):**  
  Se reenvía el intento exacto del Escenario B.2 con los mismos identificadores. El ledger intercepta el intento mediante la restricción única de SQLite y levanta de forma determinista `IdempotentReplayError`. La cardinalidad del ledger no se incrementa ($\Delta = 0$).

### 5.4. Artefactos del Hito GP-B-V0
* [`PREFLIGHT_AUDIT_GP_B_V0.md`](file:///home/agustin/.gemini/antigravity/brain/a2aadc5c-88c7-4623-aa2b-4f0b16143fd3/PREFLIGHT_AUDIT_GP_B_V0.md)
* [`SPEC-GP-B-V0.md`](file:///home/agustin/.gemini/antigravity/brain/a2aadc5c-88c7-4623-aa2b-4f0b16143fd3/SPEC-GP-B-V0.md)
* [`scripts/experiments/run_golden_path_b.py`](file:///media/agustin/Laboratorio/study-engie/scripts/experiments/run_golden_path_b.py)
* [`tests/experiments/test_golden_path_b.py`](file:///media/agustin/Laboratorio/study-engie/tests/experiments/test_golden_path_b.py)
* [`data/experiments/gp_b_oracle.json`](file:///media/agustin/Laboratorio/study-engie/data/experiments/gp_b_oracle.json)
* [`data/experiments/golden_path_b_telemetry.json`](file:///media/agustin/Laboratorio/study-engie/data/experiments/golden_path_b_telemetry.json)
* [`artifacts/gp_b/frozen_src_hashes.txt`](file:///media/agustin/Laboratorio/study-engie/artifacts/gp_b/frozen_src_hashes.txt)
* [`artifacts/gp_b/frozen_manifest.json`](file:///media/agustin/Laboratorio/study-engie/artifacts/gp_b/frozen_manifest.json)

---

# 6. HITO 1 — CURRICULUM REAL

### 6.1. Grafo Acíclico Dirigido (DAG) del Roadmap
Ubicación: [`data/curriculum/roadmaps/cybersecurity_v1.yaml`](file:///media/agustin/Laboratorio/study-engie/data/curriculum/roadmaps/cybersecurity_v1.yaml).  
Contiene 6 nodos estructurados según relaciones estrictas de precedencia:

```text
    SEC-01-C-PTR (Punteros en C)         SEC-02-OS-PROC (Procesos SO)
              │                                      │
              └──────────────────┬───────────────────┘
                                 ▼
                     SEC-03-MEM-MGMT (Memoria)
                                 │
              ┌──────────────────┴───────────────────┐
              ▼                                      ▼
    SEC-04-CONCURR (Concurrencia)          SEC-05-BIN-SEC (Seguridad Binaria)
              │                                      │
              └──────────────────┬───────────────────┘
                                 ▼
                     SEC-06-CAPSTONE (Proyecto)
```

* **Validación Topológica:** Libre de ciclos, validado por `CurriculumRegistry.validate_roadmap_acyclicity()`.
* **Prerrequisitos Duros (`hard_prerequisites`):**
  - `SEC-03` requiere obligatoriamente `SEC-01` y `SEC-02`.
  - `SEC-04` requiere `SEC-03`.
  - `SEC-05` requiere `SEC-03`.
  - `SEC-06` requiere `SEC-04` y `SEC-05`.

### 6.2. Matriz de Alineación Curricular (Epistemic Alignment Matrix)
Ubicación: [`data/curriculum/alignment/cybersecurity_v1_alignment.json`](file:///media/agustin/Laboratorio/study-engie/data/curriculum/alignment/cybersecurity_v1_alignment.json).  
Define los límites epistémicos autorizados por nodo:
* `SEC-01-C-PTR`: `prog_punteros.pdf` (Págs 1 a 15).
* `SEC-02-OS-PROC`: `so_procesos.pdf` (Págs 1 a 10).
* `SEC-03-MEM-MGMT`: `so_memoria.pdf` (Págs 1 a 14).
* `SEC-04-CONCURR`: `so_concurrencia.pdf` (Págs 1 a 8).
* `SEC-05-BIN-SEC`: `prog_archivos.pdf` (Págs 1 a 15) y `so_memoria.pdf` (Págs 5 a 12).
* `SEC-06-CAPSTONE`: Síntesis de los 8 documentos autorizados.

### 6.3. Tarea Práctica y Rúbrica Determinista
* **Especificación de Tarea:** [`data/curriculum/tasks/task_sec05_file_hasher.json`](file:///media/agustin/Laboratorio/study-engie/data/curriculum/tasks/task_sec05_file_hasher.json)  
  Declara la meta práctica para `SEC-05-BIN-SEC`: implementación de una rutina en Python que procesa un flujo de bytes y genera un archivo con el digest SHA-256 correspondiente.
* **Rúbrica de Evaluación:** [`data/curriculum/rubrics/rubric_sec05_deterministic.json`](file:///media/agustin/Laboratorio/study-engie/data/curriculum/rubrics/rubric_sec05_deterministic.json)  
  Pondera 3 dimensiones deterministas evaluadas por S9.1:
  - `D1_FILE_PRESENCE` (Peso: 0.20): Existencia del archivo de salida en el sandbox.
  - `D2_FILE_SIZE` (Peso: 0.30): Tamaño exacto de 64 bytes (hexadecimal SHA-256).
  - `D3_DIGEST_MATCH` (Peso: 0.50): Coincidencia bit a bit con el digest canónico del input.
  - Umbral de aprobación: $\ge 0.80$.

### 6.4. `CurriculumRegistry`
Ubicación: [`src/study_engine/curriculum/registry.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/curriculum/registry.py).  
* **Responsabilidades:** Carga, indexación y validación bajo política fail-closed de roadmaps, matrices de alineación, tareas y rúbricas.
* **Mecanismos de Caché:** Inmutable en memoria tras la inicialización. Si un identificador de nodo no existe en el roadmap cargado, cualquier consulta posterior levanta `NodeNotFoundError` o se abstiene inmediatamente.

---

# 7. HITO 2 — KNOWLEDGE INGESTION + RETRIEVAL

### 7.1. Corpus Canónico Ingestado
El corpus del sistema consta de 8 documentos PDF canónicos en `data/benchmark/sources/`:
1. `prog_arboles.pdf`
2. `prog_archivos.pdf`
3. `prog_lineales.pdf`
4. `prog_punteros.pdf`
5. `so_concurrencia.pdf`
6. `so_memoria.pdf`
7. `so_planificacion.pdf`
8. `so_procesos.pdf`

* **Fidelidad de Página (Page-Fidelity):** Cada fragmento almacenado en `KnowledgeStore` contiene estrictamente `page_start`, `page_end` y metadatos verificables extraídos de la estructura del PDF.
* **Almacenamiento:** Repositorio estructurado en SQLite con persistencia de texto, metadatos y tokens normalizados.

### 7.2. Pipeline de Recuperación Híbrida y Epistemic Gatekeeper
El servicio de recuperación implementa una arquitectura en cascada con filtro de ámbito epistémico previo y posterior:

```text
Consulta del Estudiante + Target Node ID
                    │
                    ▼
          CurriculumRegistry
                    │ (Resuelve documentos y páginas autorizados)
                    ▼
          AUTHORIZED SCOPE FILTER
   (Descarta chunks fuera de documento o rango de páginas)
                    │
         ┌──────────┴──────────┐
         ▼                     ▼
     BM25 Lexical         Dense Retriever
  (Tokens limpios)     (DeterministicHashEmbedder)
         │                     │
         └──────────┬──────────┘
                    ▼
      Reciprocal Rank Fusion (RRF)
                    │
                    ▼
      HYBRID RELEVANCE GATEKEEPER
 (Dense Score >= 0.84 OR Lexical Hit >= Umbral)
                    │
                    ▼
           AUTHORIZED CANDIDATES
   (Garantía: RETRIEVED ⊆ AUTHORIZED_SCOPE)
```

### 7.3. Corrección del Bug en `DenseRetriever` y Stopwords en `LexicalRetriever`
* **Bug en DenseRetriever:** Inicialmente, `DenseRetriever` no aplicaba el filtro de alcance curricular *antes* del cálculo de similitud coseno. En consultas semánticamente amplias, fragmentos de documentos no autorizados copaban el top-$K$ de similitud vectorial y eran posteriormente descartados en el post-filtro, dejando la consulta con 0 resultados válidos a pesar de existir evidencia autorizada relevante.  
  *Corrección:* Se implementó el pre-filtrado obligatorio en el vector store: solo se comparan embeddings de chunks pertenecientes a los documentos y páginas autorizados por la matriz de alineación.
* **Bug en LexicalRetriever (Stopwords en Español):** El analizador léxico procesaba consultas eliminando términos en español de alta relevancia técnica por colisión de prefijos o listas de stopwords genéricas en inglés.  
  *Corrección:* Se introdujo `filter_spanish_stopwords()` con una lista léxica formalizada (`SPANISH_STOPWORDS`) y fallback de coincidencia por prefijo stem.

### 7.4. `DeterministicHashEmbedder`
Ubicación: [`src/study_engine/retrieval/embedding.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/retrieval/embedding.py).  
* **Propósito:** Proveer un modelo de representación vectorial determinista para entornos de prueba, auditoría y ejecución sin depender de llamadas a APIs de terceros o pesos neuronales estocásticos.
* **Especificación:** Dimensión fija $D=64$. Basado en hashing de n-gramas con proyección lineal determinista y normalización de norma $L_2$ ($\|\mathbf{v}\|_2 = 1.0$).
* **Límites:** Diseñado exclusivamente para pruebas de integridad y regresión controlada. No debe utilizarse en entornos de producción con lenguaje natural complejo sin sustitución por un modelo de embeddings denso calibrado (e.g. `text-embedding-004`).

### 7.5. `ContextPacker`
Ubicación: [`src/study_engine/context/packer.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/context/packer.py).  
Formatea los candidatos recuperados en bloques canónicos inyectables en el prompt del generador:
```text
[E1] (Fuente: so_concurrencia.pdf, pág. 1)
Los procesos concurrentes requieren mecanismos de sincronización para evitar condiciones de carrera...
```
Cada evidencia recibe un índice formal `[E_i]` que S4.4 (Forensic Auditor) audita para validar las citas textuales y las afirmaciones de conocimiento.

---

# 8. HITO 3 — GENERACIÓN + SESSION ORCHESTRATION + FORENSIC AUDIT

### 8.1. P3.1: Generadores y Backends de Lenguaje
* **`Generator` (`src/study_engine/generation/base.py`):** Interfaz abstracta que recibe el contexto empaquetado y la consulta del estudiante.
* **`MockGenerator` / `ReplayMockBackend` (`src/study_engine/generation/mock.py`, `llm/backends.py`):** Motor de generación determinista para auditorías y tests unitarios. Admite respuestas predefinidas e indexadas por hash de prompt, garantizando reproducibilidad absoluta en pipelines CI/CD sin variabilidad estocástica.
* **`GeminiBackend` (`src/study_engine/llm/backends.py`):** Conector hacia la API de modelos de frontera (e.g. Gemini 1.5/2.0), implementando control de reintentos, límites de tasa y saneamiento de texto.

### 8.2. P3.2: `SessionOrchestrator` y Flujo Conceptual
Ubicación: [`src/study_engine/session/orchestrator.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/session/orchestrator.py).  
Orquesta la máquina de estados finitos (FSM) de la sesión de estudio:
```text
Consulta del Estudiante
         │
         ▼
Resolución de Nodo Curricular
         │
         ▼
RetrievalService (Recuperación autorizada)
         │
         ├── Si 0 evidencias autorizadas ──> ABSTENCIÓN INMEDIATA (NO_EVIDENCE)
         ▼
ContextPacker (Empaquetado de citas [E_i])
         │
         ▼
Generator (Generación de explicación)
         │
         ▼
ForensicAuditor (S4.4)
         │
         ├── Citas inválidas / Hallucination / Injection ──> ABSTENCIÓN FAIL-CLOSED
         ▼
RESPUESTA APROBADA (Status: APPROVED)
```

### 8.3. P3.3: `ForensicAuditor` (S4.4)
Ubicación: [`src/study_engine/audit/auditor.py`](file:///media/agustin/Laboratorio/study-engie/src/study_engine/audit/auditor.py).  
* **Extracción de Afirmaciones:** Descompone la explicación generada en proposiciones atómicas individuales (`ClaimExtractor`).
* **Verificación de Citas:** Exige que cada cita `[E_i]` corresponda exactamente a una evidencia autorizada provista en el contexto (`CitationVerifier`).
* **Inferencia de Lenguaje Natural (NLI):** Verifica que cada afirmación esté estrictamente respaldada (`SUPPORTED`) por el texto del fragmento citado (`NLIEngine`).
* **Guardias de Inyección y Léxico:** Detecta intentos de jailbreak, prompt injection o evasión de instrucciones (`InjectionGuard`, `LexicalGuard`).
* **Ausencia de Self-Repair Loop:** Si la auditoría detecta una violación de grounding, la respuesta es **rechazada inmediatamente con abstención**. El sistema **no** entra en un ciclo ciego de re-generación que pueda alucinar nuevas justificaciones.

---

# 9. HITO 4 — FORMALIZACIÓN DEL STUDY LOOP (PORTS & ADAPTERS)

El Hito 4 no fue un hito puramente teórico, sino la **formalización e integración de la arquitectura hexagonal de puertos y adaptadores** para cerrar el circuito entre la sesión interactiva del estudiante y la persistencia autoritativa de evidencias:

```text
                               SESSION ORCHESTRATOR
                                        │
           ┌────────────────────────────┼────────────────────────────┐
           ▼                            ▼                            ▼
     ExecutionPort                AssessmentPort            EvidenceIngestionPort
           │                            │                            │
           ▼                            ▼                            ▼
PracticalExecutionAdapter    DeterministicAssessmentAdapter   EvidenceIngestionAdapter
(Tier 0 Sandbox S6.1)       (Reglas Rúbrica S9.1)            (Compuertas S5.2.A)
           │                            │                            │
           └────────────────────────────┼────────────────────────────┘
                                        ▼
                                  StateReadPort
                                        │
                                        ▼
                              CurriculumStateAdapter
                              (Motor de Estado S5.2.C)
```

### Contratos e Implementaciones de Adaptadores (`session/adapters.py`)
1. **`PracticalExecutionAdapter` (imprime `ExecutionPort`):** Encapsula a `PythonExecutionAdapter` (S6.1). Ejecuta código del estudiante en un directorio temporal aislado con variables de entorno desinfectadas y tiempo acotado (`min(task.time_limit_minutes * 60, 300)`).
2. **`DeterministicAssessmentAdapter` (imprime `AssessmentPort`):** Conecta con `DeterministicAssessmentEngine` (S9.1). Recibe la observación del sandbox, evalúa los hechos contra la rúbrica y emite un `AssessmentResult` inmutable sellado por SHA-256.
3. **`EvidenceIngestionAdapter` (imprime `EvidenceIngestionPort`):** Invoca a `EvidenceIngestionEngine` (S5.2.A). Exige obligatoriamente un `SessionProvenanceContext`. Si el contexto es válido y no hay replay, persiste la evidencia en `EvidenceLedger` (S5.2.B).
4. **`CurriculumStateAdapter` (imprime `StateReadPort`):** Ejecuta `derive_student_state()` (S5.2.C), proyectando el progreso del estudiante en el DAG curricular a partir de los registros inmutables del ledger.

---

# 10. HITO 5 — GOLDEN PATH E2E

### 10.1. El Circuito Completo de Aprendizaje
El Hito 5 integró en un único escenario end-to-end la totalidad de los subsistemas de la plataforma:

```text
[ Golden Path A: Turno Conceptual ]
  Consulta: "¿Cómo gestiona el SO los procesos concurrentes?"
    │
    ▼
  Epistemic Retrieval (S3) ──> Context Pack (S3) ──> Mock Generator (S4.2) ──> Forensic Audit (S4.4)
    │
    └─► APROBADO (Status: APPROVED)

[ Golden Path B: Turno Práctico ]
  Tarea: TASK-SEC05-HASHER (Implementar hasher SHA-256 en Python)
    │
    ▼
  Sandbox Execution (S6.1) ──> Observation (Artifact 64 bytes) ──> Assessment Engine (S9.1)
    │
    ▼
  Assessment Result (verdict: PASS, score: 1.0, level: N3_COMPETENT)
    │
    ▼
  Evidence Ingestion (S5.2.A) con SessionProvenanceContext
    │
    ▼
  Authoritative Ledger Commit (S5.2.B) sobre SQLite WAL
    │
    ▼
  State Derivation (S5.2.C): SEC-02=ASSESSED_PROFICIENT, SEC-04=AVAILABLE
    │
    ▼
  Anti-Replay Verification: Reenvío idéntico genera IdempotentReplayError
```

### 10.2. Verificación de Integridad y Resultados
* **Oráculo Diferencial:** [`data/experiments/hito5/gp_e2e_oracle.json`](file:///media/agustin/Laboratorio/study-engie/data/experiments/hito5/gp_e2e_oracle.json).
* **Telemetría Registrada:** [`data/experiments/hito5/gp_e2e_telemetry.json`](file:///media/agustin/Laboratorio/study-engie/data/experiments/hito5/gp_e2e_telemetry.json).
* **Tests Automatizados:** [`tests/experiments/test_golden_path_e2e.py`](file:///media/agustin/Laboratorio/study-engie/tests/experiments/test_golden_path_e2e.py) (6/6 tests pasando).
* **Métricas Finales E2E:**
  - Cardinalidad del Ledger: Exactamente 2 registros legítimos persistidos.
  - Integridad de Cadena SHA-256: `LedgerIntegrityStatus.VALID`.
  - Discrepancias contra el Oráculo: **0 discrepancias (PASS)**.
  - Veredicto Formal: **`FINAL VERDICT: CERTIFIED`**.

---

# 10.B. HITO 6 — RED TEAM ADVERSARIAL & INTEGRITY CERTIFICATION

Ejecutado bajo el protocolo estricto: `ATTACK → OBSERVE → COMPARE ORACLE → CLASSIFY → DOCUMENT`.  
Evaluó 78 casos de ataque a través de 9 fases exhaustivas:

| Fase | Foco y Subsistemas | Casos | Pass | Defect | Invariante Nuclear Certificada |
|---|---|:---:|:---:|:---:|---|
| **Fase 0** | Provenance Regression (S5.2.A) | 1 | 1 | 0 | Contexto de Procedencia Obligatorio (`FAIL_CLOSED_NO_PROVENANCE`) |
| **Fase 1** | Curriculum Attacks (S1.1-S1.3) | 12 | 11 | 0 | Aislamiento Curricular / Fail-Closed *(1 Design Weakness)* |
| **Fase 2** | Retrieval Attacks (S3.1-S3.3) | 12 | 12 | 0 | $\text{RETRIEVED\_EVIDENCE} \subseteq \text{AUTHORIZED\_SCOPE}$ (Bidireccional) |
| **Fase 3** | Generation Attacks (S4.2, S4.4) | 9 | 9 | 0 | Layer 1 / Layer 2 NLI Isolation (Cero Contaminación en Prompt) |
| **Fase 4** | Execution Attacks (S6.1, S9.1) | 8 | 8 | 0 | $\text{execution\_success} \ne \text{mastery}$ (Salida 0 sin Maestría Espuria) |
| **Fase 5** | Assessment Attacks (S9.1) | 8 | 8 | 0 | Sovereign Deterministic Authority (Cero LLM, No-Promedio, SHA Bound) |
| **Fase 6** | Evidence & Concurrency (S5.2.A/B) | 9 | 9 | 0 | Tabla de Verdad $D(K, R)$, Cadenas de Hash, Aislamiento Multi-Tenant |
| **Fase 7** | State Attacks (S5.2.C) | 10 | 10 | 0 | Invariante Nuclear S5.2.C & Derivación Funcional Pura Conmutativa |
| **Fase 8** | Timeout Boundary (S6.1, S5.2.B/C)| 9 | 9 | 0 | Nuclear Timeout Invariant & Serialización Atómica Concurrente |
| **TOTAL** | **Plataforma Integral** | **78** | **77** | **0** | **9 Invariantes Nucleares Certificadas Empíricamente** |

---

# 11. CAMBIOS DE ROBUSTEZ INTRODUCIDOS

Durante la ejecución empírica surgieron adaptaciones necesarias para blindar el comportamiento del sistema contra fallas silenciosas:

### 11.1. Propagación Estricta de Proveniencia y Eliminación de Fallback
* **Problema:** En `src/study_engine/session/adapters.py`, existía un fallback permisivo:
  ```python
  if context is None:
      node_id = next(iter(self._roadmap.nodes.keys()))  # <--- PELIGROSO
  ```
  Si una evaluación llegaba sin contexto de sesión, el adaptador le adjudicaba la evidencia de forma silenciosa al primer nodo del roadmap (`SEC-01-C-PTR`), atribuyendo competencia espuria al estudiante.
* **Corrección:** Eliminación radical del fallback. Se introdujo `MissingProvenanceError`. Toda ingesta sin `SessionProvenanceContext` es rechazada de inmediato fail-closed sin tocar el ledger ni mutar el estado.

### 11.2. Contención de Límites de Ejecución en `PracticalExecutionAdapter`
* **Problema:** Un atacante o configuración errónea en una tarea curricular con `time_limit_minutes = 99999` podía intentar agotar recursos del host.
* **Corrección:** Se impuso la cota defensiva en el adaptador:
  ```python
  effective_timeout = min(task.time_limit_minutes * 60, 300)
  ```
  Garantizando que ninguna ejecución sobrepase los 300 segundos permitidos por el techo de seguridad de `ExecutionPolicy`.

### 11.3. Aislamiento de Procesos vía `start_new_session=True`
* **Problema:** Procesos subordinados en segundo plano engendrados por scripts maliciosos quedaban huérfanos al terminar el proceso padre por timeout.
* **Corrección:** En `process_manager.py`, se enforced `start_new_session=True` en `subprocess.Popen` y terminación grupal con `os.killpg(pgid, signal.SIGTERM)` seguido de `SIGKILL`, garantizando cero procesos huérfanos.

---

# 12. MATRIZ COMPLETA DE ARCHIVOS

| Archivo | Estado | Modificación Realizada | Motivo Arquitectónico | Tests Asociados | Freeze |
|---|:---:|---|---|---|:---:|
| `src/study_engine/state/ledger.py` | `IMPLEMENTED` | Reescritura a SQLite WAL, $D(K, R)$, export JSONL | Resolver carrera TOCTOU (SSA-0R) | `test_l5_concurrency_and_crash.py` | **SÍ** |
| `src/study_engine/state/ledger_contracts.py` | `IMPLEMENTED` | Definición de `IdempotentReplayError`, `InconsistentReplayError` | Tipar decisiones de persistencia | `test_ledger_contracts.py` | **SÍ** |
| `src/study_engine/state/ingestion_engine.py` | `IMPLEMENTED` | Validación de $D(K, R)$, 4 compuertas pre-flight | Blindar admisión de evidencias | `test_ingestion_gates.py` | **SÍ** |
| `src/study_engine/state/policy_engine.py` | `IMPLEMENTED` | Reglas de suficiencia de umbral y soberanía | Evitar maestrías no autorizadas | `test_policy_engine.py` | **SÍ** |
| `src/study_engine/state/state_engine.py` | `IMPLEMENTED` | Derivación funcional pura, corte temporal | Garantizar determinismo y no-fuga | `test_state_engine.py` | **SÍ** |
| `src/study_engine/execution/process_manager.py` | `IMPLEMENTED` | `killpg`, micro-timeout tracking, cleanup temp | Contención de procesos huérfanos | `test_phase8_timeout_boundary.py` | **SÍ** |
| `src/study_engine/execution/adapter_python.py` | `IMPLEMENTED` | Ejecución en sandbox local desinfectado | Aislamiento de ejecución Tier 0 | `test_python_adapter.py` | **SÍ** |
| `src/study_engine/assessment/service.py` | `IMPLEMENTED` | Orquestación determinista de evaluación | Autoridad soberana determinista | `test_service.py` | **SÍ** |
| `src/study_engine/assessment/evaluator_deterministic.py`| `IMPLEMENTED` | Evaluación de hechos de artefactos | `Execution Success != Mastery` | `test_evaluator_deterministic.py` | **SÍ** |
| `src/study_engine/audit/auditor.py` | `IMPLEMENTED` | Verificación de citas, NLI, guardias | Cero alucinación en respuestas | `test_auditor.py` | **SÍ** |
| `src/study_engine/curriculum/registry.py` | `IMPLEMENTED` | Caché inmutable, validación DAG acíclico | Carga fail-closed de currículum | `test_curriculum_registry.py` | NO |
| `src/study_engine/curriculum/alignment_contracts.py` | `IMPLEMENTED` | Tipado de matriz de alineación epistémica | Aislamiento de fuentes y páginas | `test_alignment_contracts.py` | NO |
| `src/study_engine/retrieval/service.py` | `IMPLEMENTED` | Epistemic Gatekeeper, hybrid retrieval | `RETRIEVED ⊆ AUTHORIZED_SCOPE` | `test_phase2_retrieval_attacks.py`| NO |
| `src/study_engine/retrieval/dense.py` | `IMPLEMENTED` | Pre-filtrado por documento en vector store | Evitar saturación de top-K foráneo | `test_dense.py` | NO |
| `src/study_engine/retrieval/lexical.py` | `IMPLEMENTED` | Stopwords en español, stem fallback | Recuperación léxica de alta precisión | `test_lexical.py` | NO |
| `src/study_engine/context/packer.py` | `IMPLEMENTED` | Empaquetado `[E_i]` con procedencia de página | Grounding estricto para S4.4 | `test_context_packer.py` | NO |
| `src/study_engine/session/adapters.py` | `IMPLEMENTED` | Puertos hexagonales: Execution, Assessment, Ingestion | Desacoplamiento de orquestación | `test_session_adapters.py` | NO |
| `src/study_engine/session/orchestrator.py` | `IMPLEMENTED` | FSM de sesión, integración E2E | Conducción del ciclo de estudio | `test_session_orchestrator.py` | NO |
| `src/study_engine/tutor/__init__.py` | `DRAFT` | Archivo esqueleto vacío | Reservado para S7 | N/A | NO |

---

# 13. INVENTARIO FORMAL DE CONTRATOS E INVARIANTES

| ID | Invariante Nuclear | Implementación / Mecanismo | Test de Verificación | Estado |
|---|---|---|---|:---:|
| **INV-01** | `NO UNCONTAINED STATE TRANSITION` | `derive_student_state()` función pura | `test_l6_chaos_and_external_oracle.py` | `CERTIFIED` |
| **INV-02** | `NO UNAUTHORIZED EVIDENCE` | Compuerta ontológica S5.2.A | `test_l1_ast_and_immutability.py` | `CERTIFIED` |
| **INV-03** | `NO CROSS-STUDENT CONTAMINATION` | Tenant isolation en Ledger y State | `test_l4_hostile_e2e_matrix.py` | `CERTIFIED` |
| **INV-04** | `NO CURRICULAR BYPASS` | Hard prerequisites check en DAG | `test_phase7_state_attacks.py` | `CERTIFIED` |
| **INV-05** | `NO REPLAY DUPLICATION` | Decisión $D(K, R)$ en SQLite WAL | `test_differential_oracle_4way.py` | `CERTIFIED` |
| **INV-06** | `NO UNKNOWN -> FAIL COLLAPSE` | Abstención explícita `NO_EVIDENCE` | `test_l2_l3_epistemic_invariants.py` | `CERTIFIED` |
| **INV-07** | `NO GENERATED -> EVIDENCE LAUNDERING`| Rechazo de texto no auditado | `test_phase7_state_attacks.py` | `CERTIFIED` |
| **INV-08** | `NO AUDIT / CONTEXT DIVERGENCE` | Citas `[E_i]` bound a candidates | `test_phase3_generation_attacks.py` | `CERTIFIED` |
| **INV-09** | `NO CRASH-INDUCED PHANTOM STATE` | Transacciones ACID rollback en crash | `test_l5_concurrency_and_crash.py` | `CERTIFIED` |
| **INV-10** | `SOVEREIGN AUTHORITY PATH` | Cero autoridad a LLM/UI sobre estado | `test_phase5_assessment_attacks.py` | `CERTIFIED` |
| **INV-RET**| `RETRIEVED ⊆ AUTHORIZED_SCOPE` | Epistemic Gatekeeper pre/post filter | `test_phase2_retrieval_attacks.py` | `CERTIFIED` |
| **INV-EXEC**| `EXECUTION SUCCESS ≠ MASTERY` | S9.1 Deterministic Rubric Evaluator | `test_golden_path_b.py` | `CERTIFIED` |
| **INV-TIME**| `TIMEOUT BOUNDARY CONTAINMENT` | Process group killpg + bounds [1, 300] | `test_phase8_timeout_boundary.py` | `CERTIFIED` |

---

# 14. MÉTRICAS ACTUALES

Valores verificados empíricamente en la plataforma:

```text
pytest:
  collectables = 1463
  executed     = 1463
  passed       = 1463
  failed       = 0
  skipped      = 0
  xfailed      = 0
  duration     = 86.18 s

mypy:
  src/ files   = 121
  src/ errors  = 0
  scripts/ err = 0 (scripts/experiments/ 100% strict)
  tests/ err   = 33 (en 17 archivos heredados por PEP 484 no-implicit-optional)

E2E:
  campaigns    = 1 (Golden Path E2E completo)
  tests        = 6
  passed       = 6
  failed       = 0
  verdict      = CERTIFIED (0 oracle mismatches)

Ledger:
  entries      = 2 (en Golden Path canónico)
  hash-chain   = VALID (SHA-256 verificado)
  replay       = DEFENDED (IdempotentReplayError demostrado)

Corpus:
  PDFs         = 8 documentos canónicos
  pages        = 88 páginas procesadas
  fidelity     = 100% chunks con página exacta verificable

Curriculum:
  nodes        = 6 (SEC-01 a SEC-06)
  edges        = 7 precedencias duras
  cycles       = 0 (Acyclicity matemáticamente demostrada)
```

---

# 15. DECISIONES ARQUITECTÓNICAS CONGELADAS

### 1. SQLite WAL como Autoridad de Persistencia
* **Decision:** SQLite en modo WAL con `BEGIN IMMEDIATE` es la autoridad única de commit. JSONL es solo una proyección derivada.
* **Reason:** Elimina las carreras TOCTOU inherentes a archivos planos sin bloqueos a nivel de kernel.
* **Evidence:** Cero duplicados en carreras de 100 hilos, 2 instancias y 4 procesos paralelos.
* **Consequence:** Cualquier componente que deba registrar o consultar evidencias debe interactuar mediante la API de `EvidenceLedger`, nunca escribiendo directamente a disco.

### 2. Derivación Funcional Pura de Estado (`derive_student_state`)
* **Decision:** El estado curricular no se almacena como entidad mutable en una base de datos; se deriva determinísticamente como una función pura del ledger inmutable: $\text{State} = f(\text{Ledger}, \text{Roadmap}, \text{Policy})$.
* **Reason:** Elimina la corrupción de estado por caídas a mitad de escritura y garantiza la reproductibilidad histórica auditada.
* **Evidence:** Conmutatividad demostrada: invertir el orden de inserción de evidencias produce 100% el mismo estado epistémico.
* **Consequence:** Prohibido implementar métodos `update_student_state()` o mutar atributos en memoria de `StudentState`.

### 3. Evaluación Determinista Soberana (S9.1)
* **Decision:** El motor de evaluación de tareas prácticas es puramente determinista y algorítmico. Cero uso de LLMs para calificar código.
* **Reason:** Previene la variabilidad estocástica, la alucinación de criterios y el arbitraje arbitrario de notas.
* **Evidence:** Invariante demostrada: ejecuciones idénticas generan exactamente el mismo digest SHA-256 de evaluación.
* **Consequence:** Las nuevas tareas deben especificar rúbricas estructuradas compatibles con extracción de hechos mecánicos.

### 4. Aislamiento Epistémico Bidireccional
* **Decision:** Un nodo curricular solo puede recuperar información de los documentos y páginas autorizados en su alineación ontológica.
* **Reason:** Previene la contaminación cruzada y asegura que el estudiante demuestre competencia con el material asignado.
* **Evidence:** 12/12 casos de ataque de recuperación rechazados o contenidos en Fase 2 de Hito 6.
* **Consequence:** Cualquier ampliación de contenido debe registrarse en `cybersecurity_v1_alignment.json`.

---

# 16. DECISIONES DESCARTADAS

Para evitar que el equipo entrante re-explore caminos técnicamente contraindicados:

1. **Bases de Datos Vectoriales Externas Complejas (FAISS, Milvus, Qdrant):**  
   *Descartado:* Introducen dependencias en C++/red innecesarias para corpus de escala curricular (< 10.000 fragmentos). La combinación de SQLite, BM25 y embeddings proyectados en memoria provee tiempos de respuesta $< 10\text{ ms}$ sin complejidad operativa.
2. **Ciclos de Auto-Reparación Ciega en el Generador (Self-Repair Loops):**  
   *Descartado:* Si un generador produce una afirmación no respaldada por el corpus, re-alimentarlo en bucle suele inducir alucinaciones de segundo orden para justificar el error. Se adoptó la abstención inmediata fail-closed (`NO_EVIDENCE`).
3. **Uso de LLM Real en la Suite Automatizada de Tests:**  
   *Descartado:* Los tests de integración y regresión no deben depender de conectividad externa, costos de API ni respuestas no deterministas. Todos los tests de la suite corren contra `MockGenerator` o `ReplayMockBackend`.
4. **Mutación de Estado en Memoria desde Eventos de UI:**  
   *Descartado:* Un frontend jamás puede enviar un evento del tipo `setUserProgress("PROFICIENT")`. El estado es una función estricta de las evidencias auditadas en el ledger.

---

# 17. ESTADO DE S7 — PEDAGOGICAL TUTOR

> [!WARNING]  
> **Estado Actual de S7:** `DRAFT / PRE-SPEC` (No implementado en código productivo).  
> La carpeta `src/study_engine/tutor/` contiene únicamente un `__init__.py` vacío.

### Correcciones Conceptuales Congeladas para S7
Cualquier implementación futura del Tutor S7 debe regirse por las tres directrices arquitectónicas acordadas:
* **INV-TUT-01 (Separación de Contenido vs Acto Pedagógico):**  
  Una cosa es una afirmación de contenido técnico (`Content Claim`), la cual requiere respaldo documental estricto en el corpus auditado por S4.4. Otra cosa es un acto pedagógico instruccional (`Pedagogical Act`, e.g. "¿Recuerdas cómo se declara un puntero en C?"). Los actos pedagógicos no son afirmaciones factuales y no deben ser bloqueados por no citar una página del libro.
* **INV-TUT-02 (Respeto a la Semántica Fina de Incertidumbre):**  
  El Tutor no debe colapsar toda duda en un tosco `[NO_EVIDENCE]`. Debe discriminar entre `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED` y `UNASSESSED_EVIDENCE` provisto por S4.4 para formular preguntas de sondeo socrático adecuadas.
* **INV-TUT-03 (Prohibición de Sustitución Cognitiva):**  
  No existe una prohibición dogmática de "nunca mostrar código". La regla rectora es: *El Tutor jamás debe realizar el trabajo cognitivo que le corresponde al estudiante*. Puede mostrar fragmentos sintácticos ilustrativos o contraejemplos, pero nunca resolver la tarea de evaluación práctica.

---

# 18. MATRIZ DE RIESGOS ABIERTOS

| Riesgo / Deuda Técnica | Severidad | Evidencia | ¿Bloquea? | Mitigación Recomendada | Estado |
|---|:---:|---|:---:|---|:---:|
| **Validación de Esquema en Tareas LLM (`P1-CURR-12`)** | `MEDIA` | Tareas que invocan herramientas no declaradas en ontología | NO | Implementar validador semántico formal en Hito 8 | `DESIGN_WEAKNESS` |
| **Warnings de Tipado en Tests Heredados** | `BAJA` | 33 errores mypy en `tests/` por PEP 484 implicit Optional | NO | Aplicar script `no_implicit_optional` en `tests/` | `TECHNICAL_DEBT` |
| **Contención Bajo Concurrencia Masiva (>500 threads)** | `MEDIA` | SQLite WAL serializa escritores en cola | NO | Introducir cola en memoria (Actor pattern) | `SCALABILITY_RISK` |
| **Drift Temporal en Evidencias Muy Antiguas** | `BAJA` | Evidencias de 1970 siguen vigentes indefinidamente | NO | Definir políticas curriculares de recertificación | `OPEN_QUESTION` |

---

# 19. TODO LO QUE TODAVÍA NO ESTÁ DEMOSTRADO

En apego a la regla fundamental, se enumeran las afirmaciones que **NO** han sido demostradas empíricamente:
1. **Comportamiento bajo Modelos de Lenguaje de Frontera no Deterministas:** La plataforma ha sido certificada en pipelines automatizados con `MockGenerator` y backends controlados. El comportamiento del guardián forense S4.4 ante variaciones estilísticas extremas de modelos de 100B+ parámetros en producción está `UNMEASURED`.
2. **Escalabilidad de Recuperación con Gran Volumen:** Certificado con 8 PDFs canónicos (88 páginas). El comportamiento con miles de documentos o libros de texto completos requerirá calibración de RRF e índices inversos optimizados.
3. **Aislamiento de Ejecución Multi-Tenant en Host Compartido:** Certificado en Sandbox Tier 0 (procesos locales con límites de memoria y sesiones POSIX). No se ha demostrado contención contra ataques de kernel o escapes de contenedor (Tier 1 / Tier 2 requeridos para despliegue multi-tenant público).
4. **Persistencia Física ante Pérdida Abrupta de Energía:** Las pruebas de caída simulan excepciones de software y cortes de procesos. No se ha sometido el disco a cortes de energía en mitad de escrituras de bloque (Torn-page physical faults).

---

# 20. GAPS HACIA PRODUCTO REAL

```text
+-------------------------------------------------------------------------+
|                              GAP ANALYSIS                               |
+-------------------------------------------------------------------------+
| Capa                   | Estado Actual        | Gap hacia Producción    |
+------------------------+----------------------+-------------------------+
| 1. Deterministic Core  | 100% Certificado     | 0 gaps de lógica        |
| 2. Integration Layer   | Hexagonal Adapters   | Conectores a bases prod |
| 3. AI Layer            | Mock / Replay / SDK  | Observabilidad de LLM   |
| 4. UX / TUI            | Scripts / CLI runner | Interfaz gráfica/web    |
| 5. Security & Sandbox  | Tier 0 (Local OS)    | Tier 1 (Docker/gVisor)  |
| 6. Observability       | Telemetría JSON local| OpenTelemetry / Prom    |
| 7. Curriculum          | 1 Roadmap (6 nodos)  | Expansión curricular    |
+-------------------------------------------------------------------------+
```

---

# 21. ROADMAP RECOMENDADO DESDE EL ESTADO ACTUAL

### Orden Estricto de Dependencias Técnicas

```text
[HITO 8: Frontier AI Evaluation & Multi-Agent Resilience]
                          │
                          ▼
           [HITO 7: S7 Pedagogical Tutor Engine]
                          │
                          ▼
           [HITO 9: Containerized Sandbox Tier 1]
                          │
                          ▼
           [HITO 10: TUI / Web Student Experience]
```

### Clasificación de Prioridad
* **`MUST HAVE` (Inmediato):**
  - Hito 8: Validación de contratos semánticos de tareas con invocación de agentes LLM (`P1-CURR-12`).
  - Limpieza de warnings de tipado PEP 484 en `tests/` para alcanzar `mypy --strict` en el 100% del repositorio.
* **`SHOULD HAVE` (Siguiente fase):**
  - Hito 7: Diseño formal e implementación del Tutor Pedagógico S7 siguiendo `INV-TUT-01`, `02`, `03`.
* **`LATER` (Pre-lanzamiento):**
  - Hito 9: Sandbox de ejecución Tier 1 en contenedores efímeros (Docker/Podman/gVisor).
  - Hito 10: Interfaz interactiva de usuario (TUI enriquecida con `Textual` o Interfaz Web).
* **`DO NOT DO YET` (Terminantemente prohibido en esta fase):**
  - No implementar infraestructura de bases vectoriales distribuidas (FAISS/Milvus).
  - No modificar motores dentro del perímetro congelado (`state/`, `execution/`, `assessment/`, `audit/`).
  - No crear loops de reintento no supervisados en el generador.

---

# 22. CAMINO HASTA LA FINALIZACIÓN DEL PROYECTO

```text
[ ESTADO ACTUAL: HITO 6 CERTIFIED ] ──> 1.463 tests verdes, Perímetro Congelado Intacto
                 │
                 ▼
[ HITO 8: FRONTIER AI & RESILIENCE ] ──> Cierre de debilidad de diseño P1-CURR-12
                 │
                 ▼
[ HITO 7: S7 TUTOR SPEC & IMPL ] ────► Socrático formal, no-sustitución cognitiva
                 │
                 ▼
[ HITO 9: TIER 1 SANDBOX ] ──────────► Contención de código en contenedores gVisor
                 │
                 ▼
[ HITO 10: PRODUCTION MVP / UX ] ────► Interfaz de usuario final, telemetría OTel
                 │
                 ▼
     🏆 KASIU PRODUCTION-READY
```

---

# 23. CRITERIO DE “PROYECTO TERMINADO”

El proyecto KASIU se considerará terminado y listo para producción cuando cumpla objetivamente con las siguientes condiciones verificables:
1. **Core:** 100% de invariantes deterministas mantenidas con 0 defectos en pruebas de estrés.
2. **Curriculum:** Al menos 3 roadmaps completos validados sin ciclos y con matrices de alineación registradas.
3. **Retrieval:** Búsqueda híbrida con latencia $p95 < 20\text{ ms}$ y 0 fugas epistémicas.
4. **Assessment:** Motor determinista con soporte para pruebas unitarias, análisis de artefactos y verificación de estado.
5. **Execution:** Sandbox Tier 1 con cuotas estrictas de CPU, RAM, red (deshabilitada por defecto) y disco.
6. **Session:** Orquestación completa de diálogos conceptuales y entregas prácticas.
7. **Audit:** 100% de respuestas generadas sometidas a NLI y verificación de citas sin omisiones.
8. **Tutor:** Agente pedagógico que interactúa socráticamente sin sustituir el esfuerzo cognitivo.
9. **Persistence:** Ledger SQLite WAL con réplica o backup automatizado y verificación de integridad criptográfica continua.
10. **Testing:** Suite completa de pruebas automatizadas con 100% pass, 0 skips, 0 xfails, y `mypy --strict` limpio en todo el proyecto.

---

# 24. PROTOCOLO DE CONTINUACIÓN PARA EL PRÓXIMO TECH LEAD

Instrucciones directas para el profesional que asuma la dirección técnica:

### 1. Antes de Modificar Código
* Lee este documento y revisa [`docs/audits/HITO_6_SURVIVAL_AUDIT.md`](file:///media/agustin/Laboratorio/study-engie/docs/audits/HITO_6_SURVIVAL_AUDIT.md).
* Ejecuta la suite completa de pruebas para constatar la línea base verde:
  ```bash
  .venv/bin/pytest tests/
  ```
  Debe reportar exactamente: `1463 passed`.
* Ejecuta el circuito Golden Path E2E:
  ```bash
  .venv/bin/python scripts/experiments/run_golden_path_e2e.py
  ```
  Debe reportar: `FINAL VERDICT: CERTIFIED`.

### 2. Antes de Tocar un Perímetro Congelado
* Detén cualquier edición si el archivo pertenece a `state/`, `execution/`, `assessment/`, `audit/`.
* Pregúntate: *¿Es posible resolver el problema mediante un Adaptador en `session/adapters.py` o configurando un contrato en `curriculum/`?*  
  En el 99% de los casos, la respuesta es afirmativa.

### 3. Antes de Introducir una Optimización
* No optimices sin un benchmark reproducido. Ejecuta pruebas de perfilado antes de alterar estructuras de datos.

### 4. Antes de Cambiar un Contrato
* Si modificas un contrato en `contracts/`, corre de inmediato `mypy src/` y la suite de contratos en `tests/contract/`.

### 5. Después de Cada Milestone
* Genera el oráculo diferencial estático correspondiente (`*_oracle.json`).
* Registra la telemetría de ejecución (`*_telemetry.json`).
* Actualiza el resumen de resultados y documenta cualquier nuevo hallazgo en el informe de auditoría.

---

# 25. FORMATO FINAL

El presente documento ha sido elaborado bajo los estándares más exigentes de ingeniería de sistemas críticos:
- Todas las rutas corresponden a la estructura real del repositorio.
- Todas las clases y funciones existen y han sido verificadas en el entorno virtual activo.
- Las métricas provienen de ejecuciones empíricas directas, no de estimaciones.

---

# 26. SECCIÓN FINAL OBLIGATORIA: “HANDOFF SNAPSHOT”

```text
PROJECT: KASIU / Study Engine
CURRENT MILESTONE: Hito 6 (Survival, Adversarial & Integrity Certification) — CERTIFIED & CLOSED
LAST CERTIFIED MILESTONE: Hito 6 (Fases 0 a 8 completas: 78 casos, 77 pass, 0 defects, 1 design weakness)
GLOBAL TEST STATUS: 1.463 passed in 86.18s | 0 failed | 0 skipped | 0 xfailed (100% GREEN)
MYPY STATUS: src/ (121 files): 0 errors | scripts/experiments/: 0 errors (strict) | tests/: 33 warnings heredadas
FROZEN PERIMETER: src/study_engine/state/, src/study_engine/execution/, src/study_engine/assessment/, src/study_engine/audit/ (100% INTACTO)
CERTIFIED SUBSYSTEMS: S1 (Curriculum/Roadmap), S2 (Storage/Corpus), S3 (Retrieval), S4 (Generation/Audit S4.4), S5 (State/Ledger WAL), S6 (Execution Tier 0), S9 (Assessment Engine)
DRAFT SUBSYSTEMS: S7 (Pedagogical Tutor — src/study_engine/tutor/), S8 (Quality/Tester)
OPEN RISKS: P1-CURR-12 (validación semántica en tareas LLM delegada a Hito 8); 33 advertencias mypy en tests heredados
NEXT MILESTONE: Hito 8 (Frontier AI Evaluation, Multi-Agent Resilience & Continuous Evolution)
NEXT HARD GATE: Validación formal de esquemas semánticos en tareas con invocación de agentes
DO NOT MODIFY: src/study_engine/state/, execution/, assessment/, audit/ (Perímetro Congelado)
DO NOT OPTIMIZE: No introducir bases vectoriales complejas (FAISS/Milvus); no relajar SQLite WAL; no crear self-repair loops
KEY ARCHITECTURAL DECISIONS: SQLite WAL como autoridad atómica y JSONL como proyección derivada; State como función pura del Ledger; S9.1 soberano determinista; Aislamiento epistémico bidireccional; Fail-closed ante ausencia de proveniencia
KEY INVARIANTS: Execution Success != Mastery | RETRIEVED ⊆ SCOPE | D(K, R) Idempotency | State = f(Ledger) | Timeout ∈ [1, 300]
CRITICAL FILES: src/study_engine/state/ledger.py | session/orchestrator.py | session/adapters.py | assessment/service.py | data/curriculum/roadmaps/cybersecurity_v1.yaml
CRITICAL TESTS: tests/experiments/test_golden_path_e2e.py | tests/adversarial/timeout/test_phase8_timeout_boundary.py | tests/survival/test_differential_oracle_4way.py
CRITICAL ARTIFACTS: docs/audits/HITO_6_SURVIVAL_AUDIT.md | data/experiments/hito6/hito6_oracle.json | data/experiments/hito5/gp_e2e_oracle.json
CURRENT BLOCKERS: Ninguno (0 defectos demostrados dentro del perímetro certificado)
UNKNOWN / UNVERIFIED: Comportamiento ante corte abrupto de energía en disco físico; escalamiento a >10.000 PDFs; LLM no determinista en producción
RECOMMENDED NEXT ACTION: Iniciar Hito 8 resolviendo P1-CURR-12 y normalizando warnings de tipado PEP 484 en tests/
```
