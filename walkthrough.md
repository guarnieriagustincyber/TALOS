# Walkthrough: Cierre Tier-0 y Reconciliación de Suites (2.380 Tests)

Cierre formal y consolidado del slice **Tier-0**, con todas las compuertas reconciliadas a nivel repositorio, desglose suite por suite, evaluación en vivo del **Golden Set v1 (18/18 PASS)** y registro del backlog técnico.

---

## 1. Reconciliación Consolidada de Suites (HEAD)

> **Verificación Matemática Unívoca:** `pytest --collect-only tests/` recolecta **2.380 tests**.
> La suma de las 22 suites del repositorio reconstruye con exactitud:
> **2.370 PASSED** + **7 SKIPPED** + **3 FAILED** = **2.380 TESTS TOTALES RECOLECTADOS**.
> El Golden Set v1 se reporta por separado como evaluación en vivo end-to-end fuera del total estático de tests.

### Desglose Completo por Suite (22 Directorios de `tests/`)

| Suite | Total Recolectado | Passed | Failed | Skipped | Clasificación de Gate | Nota / Detalle |
|---|:---:|:---:|:---:|:---:|---|---|
| `tests/unit` | 793 | 793 | 0 | 0 | **Release Gate (Bloqueante)** | Aislamiento unitario estricto |
| `tests/contract` | 429 | 429 | 0 | 0 | **Release Gate (Bloqueante)** | Tipado, boundaries y schemas canónicos |
| `tests/security` | 52 | 52 | 0 | 0 | **Release Gate (Bloqueante)** | Sanitización PII, inyecciones y contratos estrictos |
| `tests/adversarial` | 655 | 655 | 0 | 0 | **Release Gate (Bloqueante)** | Incluye `crisol` (27) y `crisol_chaos` (22) como subdirectorios |
| `tests/pedagogy` | 65 | 65 | 0 | 0 | **Release Gate (Bloqueante)** | Pipeline socrático, fases y streaming SSE |
| `tests/integration` | 110 | 103 | 0 | 7 | Suite Integrada | 7 skipped por requerir API keys externas de LLM en vivo |
| `tests/web` | 38 | 38 | 0 | 0 | Suite Integrada | Endpoints API y compatibilidad UI |
| `tests/hierarchy` | 36 | 35 | 1 | 0 | Suite Integrada | 1 fail preexistente: migración v3 vs schema actual v4 |
| `tests/survival` | 34 | 34 | 0 | 0 | Suite Integrada | Resiliencia de estado y persistencia |
| `tests/llm_pool` | 31 | 31 | 0 | 0 | Suite Integrada | Circuit breakers y fallback de proveedores |
| `tests/experiments` | 27 | 27 | 0 | 0 | Informativa | Calibración y corridas de golden paths |
| `tests/system` | 22 | 22 | 0 | 0 | Suite Integrada | Cadena de autoridad y límites de subsistemas |
| `tests/context` | 19 | 19 | 0 | 0 | Suite Integrada | Compilador de contexto y router de intención |
| `tests/performance` | 17 | 17 | 0 | 0 | Informativa | TTFT desagregado, benchmarks y presupuestos |
| `tests/llm` | 13 | 12 | 1 | 0 | Suite Integrada | 1 fail preexistente: modelo por defecto xkiro |
| `tests/protected` | 9 | 9 | 0 | 0 | Suite Integrada | Raíz de confianza y contratos inmutables |
| `tests/session` | 9 | 9 | 0 | 0 | Suite Integrada | Sesiones unificadas y submissions |
| `tests/memory` | 7 | 7 | 0 | 0 | Suite Integrada | Extracción de misconceptions y memoria episódica |
| `tests/benchmark` | 6 | 6 | 0 | 0 | Informativa | Perfilado de ingesta y almacenamiento |
| `tests/storage` | 5 | 5 | 0 | 0 | Suite Integrada | Repositorios SQLite y bajo nivel |
| `tests/retrieval` | 2 | 1 | 1 | 0 | Suite Integrada | 1 fail preexistente: ventana de SectionExpander |
| `tests/ci` | 1 | 1 | 0 | 0 | Suite Integrada | Verificación de entorno CI |
| **TOTAL REPOSITORIO** | **2.380** | **2.370** | **3** | **7** | — | **Suma exacta de las 22 suites del repo** |

---

### Evaluación en Vivo End-to-End (Fuera del total estático de tests)

| Evaluación en Vivo | Muestra | Passed | Failed | Métrica Clave | Estado |
|---|:---:|:---:|:---:|---|:---:|
| **Golden Set v1** | 18 queries | 18 | 0 | $p50 = 2.331\text{ ms}$ (budget $\le 3.000\text{ ms}$), exactitud KC 100% | ✅ **PASS** |

---

## 2. Declaración Formal de Gates de Producción

1. **GATE DE RELEASE (Compuertas Bloqueantes de Producción):**
   Las 5 suites nucleares que garantizan la integridad semántica, seguridad y correctitud dialéctica del motor de estudio:
   - `tests/unit` (793 tests) + `tests/contract` (429 tests) + `tests/security` (52 tests) = **1.274 tests PASS**.
   - `tests/adversarial` = **655 tests PASS** (en 5 tandas de memoria controlada).
   - `tests/pedagogy` = **65 tests PASS**.
   - Regresión de gate de relevancia: `tests/integration/test_relevance_gate_regression.py` = **7 tests PASS**.
   - Criterio soberano de integración en vivo: **Golden Set v1 = 18/18 PASS**.
   *Condición de Release:* Cero fallos tolerados en este conjunto para autorizar merges a main o entregas de fase.

2. **SUITES INFORMATIVAS Y DE RESILIENCIA:**
   - `tests/adversarial/crisol_chaos` (22 tests, subconjunto de `adversarial`): Inyección de fallas caóticas de infraestructura.
   - `tests/performance`, `tests/benchmark`, `tests/experiments`: Perfilado analítico y telemetría de latencia sin aserciones bloqueantes de semántica funcional.

---

## 3. Backlog Técnico Registrado

### BACKLOG-LEX-001 — Canonicalización singular→plural en query_rewriter.py
- **Identificador:** `BACKLOG-LEX-001`
- **Estado:** PENDIENTE (no bloqueante para `content_registry`).
- **Problema diagnosticado:** En el corpus bibliográfico técnico, ciertos conceptos clave aparecen exclusivamente en su forma plural (ej. *"pilas"* en `prog_lineales.pdf:p01:c0000`). Conforme a la regla de seguridad de Commit 6, los términos con longitud $< 5$ caracteres (como *"pila"*, 4 chars) tienen prohibido el comodín de prefijo `*` para evitar falsos positivos OOD (`"int *p"`). En consecuencia, SQLite FTS unicode61 busca el término literal *"pila"*, devuelve 0 filas, y la compuerta de relevancia rechaza la consulta por `LOW_DENSE_NO_LEXICAL`.
- **Solución técnica especificada:** Implementar en `src/study_engine/retrieval/query_rewriter.py` (vía `_TYPO_CORRECTIONS` o un mapa curado `_CANONICAL_INFLECTIONS`) un mapeo de **REEMPLAZO canónico curado** (`"pila"` $\rightarrow$ `"pilas"`).
- **Restricción crítica de diseño:** Debe operar estrictamente como **reemplazo sustitutivo**, NUNCA como adición o disyunción sinónima (`pila OR pilas`). Si se agregara como término adicional, inflaría el denominador $|raw\_terms|$ en la guarda de cobertura de Commit 6 (`knowledge_store.py:566`), provocando que un chunk que solo contiene la forma singular o plural falle el umbral de cobertura estricta (100% para $\le 3$ términos).
- **Invariante de seguridad:** El umbral de comodín $\ge 5$ caracteres en `lexical_index.py` **NO se toca**, preservando el blindaje estricto contra consultas OOD.
- **Test futuro requerido al implementar:**
  - Query: `"¿qué es una pila?"` sobre el cuaderno `NB-CYBERSECURITY-V1` o nodo curricular equivalente.
  - Aserción: `len(candidates) >= 1` con admisión válida en `prog_lineales.pdf`.

---

## 4. Estado de Salida
1. **Total de Pruebas Reconciliadas:** **2.380 tests recolectados** = **2.370 PASS** + **7 SKIPPED** + **3 FAILED preexistentes**.
2. **Golden Set v1:** **18/18 PASS**, $p50 = 2331\text{ ms} \le 3000\text{ ms}$.
3. **Perímetro Congelado:** 100% limpio (`git diff origin/main -- src/study_engine/{state, execution, assessment, audit}/` = 0).
4. **Árbol de Trabajo:** Limpio en rama `main`. El sistema queda listo para dar inicio al slice de `content_registry`.
