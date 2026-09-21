# ROUTER SECURITY REPORT

## FASE 2 — Suite Adversarial del Semantic Router

**Fecha:** 2026-09-09
**Autor:** OpenCode (FASE 2 — Hardening del Routing)
**Componentes auditados:** `tutor/semantic_router.py`, `tutor/policy_validator.py`, `session/study_loop.py`

---

## 1. Principio Fundamental Verificado

```
Qwen / SemanticRouter  →  IntentContract (PROPUESTA, no confiable)
                                      │
                                      v
                       DeterministicPolicyValidator  (AUTORIDAD)
                                      │
                                      v
                             AuthoritativeRoute  (la ÚNICA ruta)
```

Nunca: `Qwen → route`. La salida del LLM es siempre una **propuesta**; la decisión de ruta pertenece exclusivamente a `DeterministicPolicyValidator.resolve()`.

**`confidence` no concede autoridad.** Se descarta en la decisión; solo el `intent` validado (taxonomía cerrada) más inputs autoritativos (roadmap, current_node) determinan la ruta.

---

## 2. Baseline

- **Commit de referencia:** `4f056a9` / `5734b1b` (v0.2.0-rc1/rc2)
- **Estado inicial:** Integración del SemanticRouter en `study_loop.py` estaba **incompleta** (archivos untracked, `__init__` no aceptaba `semantic_router`, routing usaba `detect_question_type` legacy).
- **Suite adversarial previa:** 0 tests dedicados (solo `test_semantic_router.py` de integración con 5 tests, expectativas internas inconsistentes).

---

## 3. Hardening Aplicado

### `tutor/policy_validator.py` (reescrito con modelo autoritativo)

| Garantía | Implementación |
|---|---|
| **`needs_*` sin autoridad** | `_AUTHORITATIVE_NEEDS` recomputa determinísticamente los flags por `intent`. El LLM no puede activar/desactivar retrieval. |
| **`confidence` sin autoridad** | No se lee en `resolve()`. |
| **Action tampering** | `_FORBIDDEN_ACTIONS` rechaza `execute_code`, `mark_mastered`, `write_ledger`, `change_notebook`, etc. |
| **Action whitelist** | `_ALLOWED_ACTIONS` — solo las acciones canónicas por intent son permitidas. |
| **Unknown intent** | `_ROUTE_KIND_BY_INTENT` — intents fuera de la taxonomía → `REJECTED`. |
| **Payload contradictorio** | El `resolve()` descarta `action`/`needs_*` del LLM; colapsa al `intent` validado (sin adivinar). |
| **Nueva API** | `AuthoritativeRoute` (inmutable) + `resolve()` — la ruta autoritativa. `validate()` preserva backward-compat. |

### `tutor/semantic_router.py` (endurecido)

| Garantía | Implementación |
|---|---|
| **Output size bound** | `MAX_OUTPUT_CHARS = 16384` — respuestas gigantes → fallback seguro (Group M). |
| **Parsing estricto** | Solo JSON object con `intent` en taxonomía cerrada es aceptado; arrays/strings/null/intents desconocidos → fallback. |
| **Unicode hardening** | Saneamiento de surrogates (`re.sub [\ud800-\udfff]`) — evita crash en `PromptMessage` (bug real encontrado). |
| **Fallback determinista** | `_fallback_intent()` — greeting/navigation/meta heurístico; ambigüo → `CLARIFICATION_REQUEST` (nunca technical sin fundamento). |

### `session/study_loop.py` (integración)

- Routing condicional: usa `SemanticRouter → PolicyValidator.resolve → route` cuando hay router configurado; si no, `detect_question_type` legacy.
- Los short-circuits (greeting/navigation/clarification) y el flujo técnico audited se rigen por el `route_kind` autoritativo.
- `question_type` mapea a valores legacy consumidos por el frontend (`greeting`/`curricular`/`technical`/`meta`).

---

## 4. Categorías Adversariales Cubiertas

| Grupo | Descripción | Casos |
|---|---|---|
| **A** | Malformed output → SAFE FALLBACK | 15 |
| **B** | Provider failure (timeout, conn, empty, huge) | 4 |
| **C** | Prompt injection (forbidden action) | 3 |
| **D** | Authority separation (`needs_*` sin autoridad) | 2 |
| **E** | Curriculum tampering | 1 |
| **F** | Cross-notebook isolation | 1 |
| **G** | Ambiguous natural language | 7 |
| **H** | Ambiguous follow-ups | 6 |
| **I** | Confidence adversarial | 5 |
| **J** | Action tampering | 8 |
| **K** | Unknown intent | 2 |
| **L** | Immutability (`IntentContract`) | 2 |
| **M** | Output size | 2 |
| **N** | Unicode / normalization | 6 |
| **O** | Heuristic fallback | 3 |
| **P** | Route monotonicity | 1 |
| **Q** | Policy override | 1 |
| **R** | Deterministic replay | 1 |
| **S** | No side effects | 1 |
| **T** | End-to-end security | 4 |

**Total de casos adversariales: 76**

---

## 5. Métricas

| Métrica | Valor |
|---|---|
| Total adversarial cases (nuevos) | **76** |
| Fallos iniciales (brechas reales) | **3** |
| — Unicode crash en `interpret()` | 1 |
| — Test fixtures incompletos (faltaba `needs_curriculum`) | 2 |
| Fixes de hardening aplicados | 2 (Unicode sanitize + strict parse) |
| Fixes de test (alinear expectativa inconsistente) | 1 |
| **Unauthorized route escapes** | **0** |
| Política: LLM error → contenido | Verificado |
| Cobertura de grupos A–T | 20/20 |

---

## 6. Garantías de Policy (todas testadas)

1. `needs_evidence=true` desde el LLM en `STUDY_NAVIGATION` **NO** activa retrieval (Group D).
2. `needs_evidence=false` desde el LLM en `TECHNICAL_QUESTION` **NO** desactiva la auditoría (Group D).
3. `confidence=1` no autoriza nada (Group I).
4. Acciones no autorizadas (`execute_code`, `mark_mastered`, ...) → `REJECTED` (Group J).
5. Payload contradictorio → colapsa al intent validado, sin adivinar (Group Q).
6. Unknown intent (`AUTONOMOUS_AGENT`) → rechazado / fallback seguro (Group K).
7. El LLM no puede cambiar `notebook_id`, `curriculum_id`, `current_node`, ni state (Groups E, F).
8. Router failure → `CLARIFICATION_REQUEST` / fallback seguro, nunca technical sin fundamento (Group B).
9. Less-trusted router nunca obtiene más privilegios que uno confiable (Group P).
10. Routing es clasificación + policy selection, **sin side effects** (Group S).

---

## 7. Riesgos Residuales

| Riesgo | Severidad | Nota |
|---|---|---|
| `question_type` es una proyección legacy (no la taxonomía IntentType completa) | INFO | El frontend consume valores legacy; la taxonomía autoritativa vive en `IntentContract`. |
| `detect_question_type` legacy sigue activo cuando no hay router configurado | P3 | Camino de compatibilidad; no es un escape porque no toca S4.4. |
| NLI Judge real no testado (solo MockNLIJudge) | P2 | Preexistente, fuera de scope Fase 2. |
| `test_web_api.py` falla por `no such column: curriculum_id` en KnowledgeStore | P2 | **Preexistente** (schema mismatch del trabajo untracked en `storage/`), NO introducido por Fase 2. |
| `state/ledger.py:131` (Any) | P3 | Perímetro congelado; deuda documentada, requiere recertificación. |

---

## 8. Conclusión

> **Router is untrusted. Policy is authoritative. No unauthorized route escapes detected.**

- **76** casos adversariales nuevos, cubriendo **20 grupos (A–T)**.
- **0** escapes de policy.
- Los **3** fallos iniciales se resolvieron con **2 fixes de hardening** (Unicode sanitize, parsing estricto) y **1 alineación de test** (expectativa inconsistente).
- **Perímetro congelado** (`state/`, `execution/`, `assessment/`, `audit/`) **intacto** (git diff vacío).
- **mypy --strict:** solo el error preexistente `ledger.py:131` (fuera de scope, perímetro).

---

## 9. Comandos de Verificación

```bash
# Suite adversarial (incluye 76 nuevos)
pytest tests/adversarial/ -q

# Integration router + study loop
pytest tests/integration/test_semantic_router.py tests/integration/test_study_loop_v1.py -q

# mypy strict (solo ledger.py:131 preexistente)
mypy --strict src/study_engine

# Perímetro congelado intacto
git diff --stat src/study_engine/state/ src/study_engine/execution/ src/study_engine/assessment/ src/study_engine/audit/
```