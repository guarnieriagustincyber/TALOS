# 00-DOCUMENTATION-NORMALIZATION.md
## Baseline de Calidad, Taxonomía Epistémica y Reordenamiento de Hitos
**Fecha de Ratificación:** 7 de Septiembre de 2026  
**Autoridad:** Tech Lead & Systems Architect  
**Estado:** VIGENTE / CONGELADO  

---

## 1. Línea Base Oficial de Pruebas (`CURRENT_TEST_BASELINE`)

A partir de la culminación y certificación del Hito 6 (Fases 0 a 8), la línea base oficial e inmutable de pruebas de la plataforma queda fijada en:

$$\mathbf{CURRENT\_TEST\_BASELINE = 1.463\ tests}$$

```text
DISTRIBUCIÓN DE LA SUITE COMPLETA (pytest tests/)
├── Tests Colectables:  1.463
├── Tests Ejecutados:   1.463
├── Tests PASSED:       1.463 (100.0%)
├── Tests FAILED:           0 (0.0%)
├── Tests SKIPPED:          0 (0.0%)
├── Tests XFAILED:          0 (0.0%)
└── Duración Total:     ~86.18 segundos
```

> [!IMPORTANT]
> **Regla de Integridad de Tests:**  
> Bajo ninguna circunstancia se modificarán, renombrarán o suprimirán tests existentes con el único propósito de hacer coincidir cifras con reportes históricos previos. La cifra de 1.463 refleja la suma acumulativa de la suite base (1.271) + SSA-0R (31) + GP-B / Hito 4 (12) + Hito 5 (6) + Hito 6 (Fases 0 a 8: 143 tests de integración, contrato y adversariales). Cualquier divergencia histórica se documentará como evolución cronológica, nunca alterando el código de pruebas.

---

## 2. Taxonomía Epistémica Oficial

Para evitar la ambigüedad en informes técnicos y directivas de desarrollo, se establece la siguiente partición epistemológica obligatoria:

| Término | Definición Formal | Criterio de Aplicación |
|---|---|---|
| **`CERTIFIED`** | Invariante o subsistema verificado empíricamente contra un **oráculo diferencial estático independiente**, con suite adversarial ejecutada, telemetría forense persistida y dictamen formal sin defectos residuales. | S1 (Curriculum), S2 (Storage/Ingestion), S3 (Retrieval), S4 (Generation/Audit S4.4), S5 (State/Ledger WAL), S6 (Execution Tier 0), S9 (Assessment Engine). |
| **`VERIFIED`** | Componente sometido a pruebas mecánicas (unitarias, de integración o de contrato) en escenarios nominales o controlados, sin campaña adversarial exhaustiva formal. | Adaptadores de sesión (`session/adapters.py`), cargadores de roadmap (`roadmap/loader.py`). |
| **`UNMEASURED`** | Propiedad, hipótesis o escenario donde no se han obtenido métricas cuantitativas empíricas directas en el entorno actual. | Comportamiento bajo LLM real estocástico no determinista en producción, escalabilidad con $>10.000$ documentos, aislamiento físico multi-tenant Tier 1 (gVisor/Docker). |

---

## 3. Reordenamiento Oficial de Hitos del Proyecto KASIU

Por dictamen formal del Tech Lead, se corrige el orden de hitos del proyecto priorizando la construcción de un ciclo de aprendizaje funcional antes de la evaluación comparativa de modelos de frontera:

```text
HITO 6: Survival, Adversarial & Integrity           ✅ CERTIFIED & CLOSED
   ↓
DOCUMENTATION NORMALIZATION                         🔵 VIGENTE (TASK 0)
   ↓
HITO 7: Real Study Loop                             🔵 EN ESPECIFICACIÓN (TASKS 1-3)
   ↓
HITO 7.1: S7 Controlled Tutor (TutorPolicy)         ⚪ PENDIENTE
   ↓
HITO 7.2: Real LLM Single Provider                  ⚪ PENDIENTE
   ↓
HITO 8: Model/Provider Sensitivity Campaign         ⚪ PENDIENTE
   ↓
HITO 9: Sandbox Tier 1 (Containerized gVisor)       ⚪ PENDIENTE
   ↓
HITO 10: Real UX (Thin Client TUI/Web)              ⚪ PENDIENTE
   ↓
HITO 11: Real-Student Pedagogical Validation        ⚪ PENDIENTE
   ↓
RELEASE CANDIDATE (KASIU MVP)                       ⚪ PENDIENTE
```

---

## 4. Perímetro Congelado (Frozen Core)

Se ratifica que los siguientes directorios constituyen el **núcleo congelado** de KASIU:
1. `src/study_engine/state/` (Ingestion Engine, Ledger SQLite WAL, State Engine, Policy Engine)
2. `src/study_engine/execution/` (Python Adapter, Process Manager, Sanitizer)
3. `src/study_engine/assessment/` (Deterministic Evaluator, Aggregator, Service S9.1)
4. `src/study_engine/audit/` (Auditor S4.4, Citation Verifier, NLI Engine, Guards)

Cualquier nuevo desarrollo del Hito 7 y subsiguientes debe integrarse exclusivamente a través de la capa de orquestación, puertos y adaptadores (`session/`, `tutor/`, `curriculum/`), **sin modificar el código fuente de los subsistemas congelados**.
