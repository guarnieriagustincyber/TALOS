# 🏛️ Arquitectura E3: Capa Cognitiva Determinista del Estudiante

**Subsystem:** E3 (`src/study_engine/student/`)  
**Estado:** Implementado, Verificado y Congelado  
**Invariante Fundamental:** **El LLM nunca decide el nivel de maestría ni evalúa el estado cognitivo del estudiante.** Todo cálculo de maestría es 100% determinista y bayesiano.

---

## 1. Topología del Submódulo y Fronteras de Estado

```
┌────────────────────────────────────────────────────────────────────────┐
│                   STUDENT DOMAIN & COGNITIVE LAYER                     │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │                      StudentStorage (SQLite)                   │   │
│   │   - bkt_states: (kc_id, p_L, p_T, p_G, p_S, attempts, update)  │   │
│   │   - anchor_states: (anchor_id, interval, rep, EF, review, q)   │   │
│   │   - remediation_choices: (kc_id, topic_id, choice, created_at) │   │
│   └────────────────────────────────────────────────────────────────┘   │
│                                  │                                     │
│        ┌─────────────────────────┼─────────────────────────┐           │
│        ▼                         ▼                         ▼           │
│ ┌──────────────┐         ┌──────────────┐          ┌──────────────┐    │
│ │  BKTTracker  │         │ LagunaDetect │          │ SpacedRepet  │    │
│ │ (Corbett 95) │         │ (Interrupts) │          │    (SM-2)    │    │
│ └──────────────┘         └──────────────┘          └──────────────┘    │
│        ▲                         │                         │           │
│        │                         ▼                         │           │
│ ┌──────────────┐         ┌──────────────┐                  │           │
│ │  Readiness   │         │    Depth     │                  │           │
│ │    Probe     │         │  Modulator   │                  │           │
│ └──────────────┘         └──────────────┘                  │           │
│        ▲                         ▲                         │           │
│        │                         │                         │           │
│ ┌────────────────────────────────────────────────────────────────┐     │
│ │                   ObservationBridge (Patrón Compositor)        │     │
│ │  - SymbolicVerifier (VERIFIED_TRUE / REJECTED_HALLUCINATION)   │     │
│ │  - ExactCorrector (Determinista, p_G según formato / n_options)│     │
│ └────────────────────────────────────────────────────────────────┘     │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Resolución H1: Relación entre BKTTracker y StudentState Congelado

El `StudentState` original (ubicado en `src/study_engine/contracts/student_state.py` y `state/state_contracts.py`) fue certificado como perímetro inmutable en el Gate E2.

### Definición Formal de Frontera:
1. **`BKTTracker` como Proyección Probabilística de Solo-Lectura:**  
   `BKTTracker` modela la creencia bayesiana $P(L) \in [0.0, 1.0]$ sobre el dominio de cada Knowledge Component (KC) a partir de evidencias formales de evaluación.
2. **Superficie Única de Verdad hacia la Generación:**  
   El `DepthModulator` consulta **únicamente** la proyección probabilística de `BKTTracker` para decidir las directivas de profundidad pedagógica en el prompt. No existe ambigüedad de doble fuente de verdad.
3. **Inmutabilidad del Perímetro:**  
   E3 **no escribe** en el `StudentState` congelado. Cualquier sincronización futura entre la proyección probabilística de BKT y el ledger determinista de `StudentState` deberá articularse mediante un ADR independiente (H1).

---

## 3. Componentes Implementados

### 3.1 BKTTracker (`src/study_engine/student/bkt_tracker.py`)
Implementa las fórmulas canónicas de Corbett & Anderson (1995):
- **Parámetros por defecto:** $p_{L0} = 0.10, p_T = 0.30, p_G = 0.25, p_S = 0.10$.
- **Actualización Bayesiana:**
  $$\text{Si acierto: } P(L|\text{correct}) = \frac{P(L) \cdot (1 - P(S))}{P(L) \cdot (1 - P(S)) + (1 - P(L)) \cdot P(G)}$$
  $$\text{Si error: } P(L|\text{incorrect}) = \frac{P(L) \cdot P(S)}{P(L) \cdot P(S) + (1 - P(L)) \cdot (1 - P(G))}$$
  $$\text{Transición: } P(L_{t+1}) = P(L|\text{obs}) + (1 - P(L|\text{obs})) \cdot P(T)$$
- **Derivación Dinámica de $p_G$ (Enmienda H3):**
  - Ejercicios simbólicos abiertos (`SYMBOLIC_OPEN`): $p_G = 0.02$ (la probabilidad de adivinar un cálculo formal de memoria o punteros es casi nula).
  - Ejercicios de opción cerrada (`CLOSED_CHOICE`): $p_G = 1 / n\_options$.
- **Fail-Closed (H4):** `kc_id` es obligatorio y no-vacío. Observaciones con `UNVERIFIED_DIALOGUE` son rechazadas inmediatamente.

### 3.2 ReadinessProbe (`src/study_engine/student/readiness_probe.py`)
Evalúa los prerequisitos antes de iniciar un tema curricular:
- **Tiers de Maestría:**
  - $P(L) \ge 0.80 \to \text{DOMINADO}$ (Confianza alta si tiene intentos)
  - $0.50 \le P(L) < 0.80 \to \text{NOCIÓN}$
  - $P(L) < 0.50 \to \text{AUSENTE}$
- **Decisión de Preparación:**
  - 0 ausentes $\to$ `START`
  - 1 a 2 ausentes $\to$ `START_WITH_SCAFFOLD`
  - $>2$ ausentes $\to$ `REMEDIATE_FIRST`
- **Invariante Consultivo:** La recomendación **nunca actúa como veto**. El estudiante puede acceder libremente al contenido.
- **Modos (Enmienda H8):** `plan_only=True` para evaluación no interactiva determinista en benchmarks vs `administer=True` interactivo con banco diagnóstico precalculado.

### 3.3 LagunaDetector (`src/study_engine/student/laguna_detector.py`)
Monitorea en tiempo real los ejercicios evaluados durante la sesión de estudio:
- Si el KC evaluado es un prerequisito del tema actual (`current_topic_id`) y tras un fallo el estudiante tiene $P(L) < 0.60$:
  - Emite `RemediationInterrupt` con opciones: `PAUSE_AND_REMEDIATE`, `NOTE_AND_CONTINUE`, `DUAL_TRACK`.
- **Registro Local de DUAL_TRACK (Enmienda H6):** La elección de `DUAL_TRACK` se guarda en `remediation_choices` en `StudentStorage` y se inyecta en las directivas pedagógicas del `DepthModulator`. La orquestación completa de tracks paralelos se difiere a E3.1.

### 3.4 DepthModulator (`src/study_engine/student/depth_modulator.py`)
Genera directivas pedagógicas inyectables en el bloque de sistema del prompt según $P(L)$:
- $P(L) \ge 0.80$: Profundidad avanzada (terminología técnica sin preámbulos, casos extremos, sin analogías obvias).
- $0.50 \le P(L) < 0.80$: Profundidad estándar (definir términos al inicio, analogías físicas moderadas, ejemplos intermedios).
- $P(L) < 0.50$: Fundamentos (definir todos los términos, múltiples analogías físicas, progresión gradual).
- **Invariante Epistémico:** No muta fragmentos de evidencia, ordenamiento de recuperación ni ponderación de fuentes.

### 3.5 SpacedRepetitionScheduler (`src/study_engine/student/spaced_repetition.py`)
Planificador determinista de repaso espaciado bajo SM-2:
- Intervalos: $1 \to 6 \to \text{round}(\text{interval} \times EF)$ días.
- Piso de $EF$: $\ge 1.30$.
- **Mapeo Determinista Observación $\to$ Calidad SM-2 (Enmienda H7):**
  - Simbólico correcto $\to q = 5$
  - Correcto tras reintento $\to q = 4$
  - Opción múltiple correcta $\to q = 4$
  - Incorrecto recuperable (near-miss) $\to q = 3$
  - Incorrecto $\to q = 1$

### 3.6 ObservationBridge (`src/study_engine/student/observation_bridge.py`) (Enmienda H2)
Actúa como punto de composición desacoplado entre los evaluadores deterministas (`SymbolicVerifier`, correctores exactos) y el estado cognitivo:
- Ejecuta atómicamente la actualización de BKT, la comprobación de lagunas y la programación SM-2.
- **Fail-Closed:** Rechaza veredictos no verificables (`UNVERIFIABLE`).
- No invade el módulo congelado `assessment/`.

---

## 4. Métricas y Validación Experimental

En la corrida del benchmark formal (`scripts/benchmark_phase_e3.py`), se verificaron los 10 criterios de aceptación:

| Criterio | Resultado Obtenido | Requisito del Gate |
|---|---|---|
| Latencia de actualización BKT ($p95$) | **0.022 ms** | $< 1.0$ ms |
| Recuperación estadística de parámetros (MAE) | **0.0401** | $< 0.10$ |
| Precisión de detección de lagunas | **100.0%** (50/50 casos) | $\ge 90.0\%$ |
| Monotonicidad y Clamping $[0, 1]$ | **Verificado** | Crecimiento/Decrecimiento estricto |
| Aislamiento entre Knowledge Components | **Verificado** | 0 cross-talk |
| Cero llamadas a LLM para maestría | **0 llamadas** | 0 llamadas |
