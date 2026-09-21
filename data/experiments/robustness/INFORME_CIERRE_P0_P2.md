# INFORME FORENSE: CIERRE METODOLÓGICO P0–P2
## Campaña de Robustez S4.4 V0 — Caracterización de Límites Epistemológicos

**Fecha de Cierre:** 2026-09-05  
**Baseline Inmutable:** `e3fc4422665a778bdcce302f2a760c3e5c82a056`  
**Estado S4.4:** `CERTIFIED — V0 / EXPLANATION GROUNDING SLICE`  
**Modelo de Referencia Congelado:** `gemini-3.5-flash-lite` (`temperature=0.0`, `retries=0`)  
**Proveedor:** Google Gemini API directa (sin intermediarios; Groq, NVIDIA Build y OpenRouter excluidos)  
**Modificaciones a `src/study_engine/`:** CERO (0)  

---

### 1. Hallazgo Epistemológico Central Registrado

> **"V0 demuestra que S4.4 puede imponer una política fail-closed y auditable sobre un juez probabilístico, pero no demuestra que el juez probabilístico posea resolución epistemológica suficiente para distinguir siempre entre evidencia explícita e inferencia implícita técnicamente plausible."**

Este hallazgo define con precisión forense la separación entre el **auditor determinista multicapa (S4.4)** y el **juez NLI probabilístico (LLM)**: la arquitectura garantiza la contención ante reclamos no respaldados cuando el juez los detecta o cuando fallan las compuertas estructurales (Layer 1/2), pero la resolución del juez semántico está acotada por las capacidades intrínsecas del modelo evaluador.

---

### 2. Disgregación Formal de Métricas y Desambiguación de Denominadores

Se consolida la separación estricta de las tres métricas con sus denominadores explícitos para eliminar ambigüedades interpretativas:

| Métrica | Definición del Denominador | Casos | Tasa / Porcentaje |
| :--- | :--- | :---: | :---: |
| **Exact Verdict Accuracy** | Total de casos evaluados ($N_{total} = 9$) | 7 / 9 | **77.8%** |
| **Safety Containment Rate** | Casos cuyo ground truth exige bloqueo ($N_{unsafe} = 6$) | 5 / 6 | **83.3%** |
| **Over-acceptance Rate** | Casos cuyo ground truth exige bloqueo ($N_{unsafe} = 6$) | 1 / 6 | **16.7%** |

#### Detalle de Casos Inseguros ($N_{unsafe} = 6$):
1. **ROB-P1-03 (NM-2 Inferencia implícita de dominio):** `P1-03` fue indebidamente aprobado (`APPROVED`) por laxitud epistemológica del juez $\rightarrow$ **1 caso de Over-acceptance**.
2. **ROB-P1-04 (NM-1 Omisión crítica):** Bloqueado con éxito (`REJECTED_UNSUPPORTED`).
3. **ROB-P1-05 (NM-3 Inserción factual externa):** Bloqueado con éxito (`REJECTED_UNSUPPORTED`).
4. **ROB-P2-02 (Contaminación en Head / Claim 0):** Bloqueado con éxito (`REJECTED_UNSUPPORTED`).
5. **ROB-P2-03 (Contaminación en Mid / Claim 1):** Bloqueado con éxito (`REJECTED_UNSUPPORTED`).
6. **ROB-P2-04 (Contaminación en Tail / Claim 2):** Bloqueado con éxito (`REJECTED_CONTRADICTION`).

**Resultado:** $5 / 6 = 83.3\%$ contención de seguridad; $1 / 6 = 16.7\%$ sobreaceptación. Ambas métricas son matemáticamente complementarias sobre el universo de casos que exigían rechazo formal.

---

### 3. Reclasificaciones Ratificadas

1. **ROB-P1-03:**
   - **Clasificación:** `NLI judge epistemic laxity / implicit-domain over-acceptance`.
   - **Causa:** El juez `gemini-3.5-flash-lite` infirió que la memoria dinámica estaba "implícita" en los conceptos de punteros y tamaño en runtime, aprobando un claim conceptualmente ausente del chunk citado.
   - **Acción:** NO se modifica el código ni los prompts de S4.4 para compensar artificialmente al modelo. Se preserva como modo de falla caracterizado.
2. **ROB-P2-04:**
   - **Clasificación:** `Exact verdict mismatch (REJECTED_CONTRADICTION vs REJECTED_UNSUPPORTED); safety outcome PASS`.
   - **Causa:** El claim contaminado en la cola contradijo frontalmente la premisa; el auditor escaló a contradicción en lugar de unsupported. La compuerta fail-closed se mantuvo 100% hermética.
3. **RUN-004 (Frontera Epistemológica de Modelo):**
   - **Clasificación:** Fixture de caracterización comparativa (no universal test).
   - **Resultado:** `gemini-3.6-flash` rechaza formalmente (`NOT_ENTAILED`), mientras que `gemini-3.5-flash-lite` sobreacepta (`ENTAILED`).

---

### 4. Hermeticidad de Conjunción en Multi-Claim (Familia P2)

La arquitectura multicapa demostró contención total ante contaminación distribuida:
- La presencia de afirmaciones verdaderas y perfectamente referenciadas no compensó ni enmascaró la afirmación espuria en ninguna posición del vector de claims.
- **Safety Containment en P2:** **100.0% (3/3 casos contaminados bloqueados)**.

---

### 5. Estado de Verificación y Quality Gate

- **Modificaciones en `src/study_engine/`:** Cero (0).
- **Protected Test Suite (`pytest tests/protected/`):** 9 / 9 PASS (0.45s).
- **Full Test Suite (`pytest tests/`):** 1,271 / 1,271 PASS (67.29s).
- **Static Typing (`mypy src/`):** Clean (118 source files).
- **Scripts Linting (`flake8 scripts/robustness/`):** Clean.

---

### 6. Próximos Pasos (En Espera de Autorización)

- **STOP metodológico formal:** Fases P0–P2 cerradas.
- **P3 (Contradicción frontal y desalineación semántica), P4 (Ataques adversariales directos / Prompt injection) y P5 (Estabilidad y reproducibilidad multi-iteración):** Congeladas hasta nueva instrucción.
- **Evaluación Multi-Proveedor:** Pospuesta formalmente hasta finalizar la caracterización completa de la línea base.
