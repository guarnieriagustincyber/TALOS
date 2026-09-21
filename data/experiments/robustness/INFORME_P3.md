# INFORME FORENSE: FASE P3 — CONTRADICCIÓN Y DESALINEACIÓN SEMÁNTICA
## Campaña de Robustez S4.4 V0 — Caracterización de Límites Epistemológicos

**Fecha de Ejecución:** 2026-09-05  
**Baseline Inmutable:** `e3fc4422665a778bdcce302f2a760c3e5c82a056`  
**Estado S4.4:** `CERTIFIED — V0 / EXPLANATION GROUNDING SLICE`  
**Modelo de Referencia:** `gemini-3.5-flash-lite` (`temperature=0.0`, `retries=0`)  
**Modificaciones a `src/study_engine/`:** CERO (0)  
**Proveedores externos (Groq, NVIDIA, OpenRouter):** EXCLUIDOS  

---

### 1. Objetivo Específico de P3

Caracterizar empíricamente si el juez NLI (`gemini-3.5-flash-lite`) bajo la arquitectura S4.4 distingue entre:
1. **Contradicción Frontal:** Afirmación de $\neg A$ cuando la evidencia afirma $A$.
2. **Inversión Causal / Categorial:** Intercambio de definiciones entre estados mutuamente excluyentes.
3. **Ausencia de Soporte / Entidad Alienígena:** Introducción de conceptos técnicos plausibles de bajo nivel (`sys_brk`, heap) no presentes en el texto citado ($B \notin \text{Premisa}$).

**Distinción Epistemológica Clave:**
$$\text{NOT\_ENTAILED} \neq \text{CONTRADICTION}$$

---

### 2. Resultados Caso por Caso y Racionales Textuales del NLI

| Caso | Subfamilia | Ground Truth Esperado | Veredicto S4.4 Obtenido | Etiqueta NLI | Coincidencia | Latencia |
| :--- | :--- | :--- | :--- | :--- | :---: | :---: |
| **ROB-P3-01** | `contradiction_direct` | `REJECTED_CONTRADICTION` | `REJECTED_CONTRADICTION` | `CONTRADICTED` | **EXACT MATCH** | 3282 ms |
| **ROB-P3-02** | `contradiction_causal_inversion` | `REJECTED_CONTRADICTION` | `REJECTED_CONTRADICTION` | `CONTRADICTED` | **EXACT MATCH** | 2424 ms |
| **ROB-P3-03** | `not_entailed_alien_concept` | `REJECTED_UNSUPPORTED` | `REJECTED_UNSUPPORTED` | `NOT_ENTAILED` | **EXACT MATCH** | 3018 ms |

#### Racionales Textuales Extraídos del Juez:

* **ROB-P3-01 (`contradiction_direct`):**
  > *"The premise explicitly states that C vectors have a fixed size known at compile time and 'could not lengthen or shorten the vectors to adapt to the size of a series of data during program execution'. The hypothesis claims the exact opposite: that we can lengthen or shorten them freely during execution."*

* **ROB-P3-02 (`contradiction_causal_inversion`):**
  > *"The premise defines the 'Bloqueado' state as 'no puede ejecutarse sino hasta que ocurra cierto evento externo', whereas the hypothesis claims it is using the CPU actively, which contradicts the definition of 'En ejecución'."*

* **ROB-P3-03 (`not_entailed_alien_concept`):**
  > *"The hypothesis introduces specific technical details (such as the invocation of the system call 'sys_brk' and allocation in the heap) that are not mentioned in the premise. The premise only broadly discusses data structures, fixed-size arrays at runtime, and linked lists using pointers."*

---

### 3. Métricas Específicas de la Fase P3 ($N = 3$, $N_{unsafe} = 3$)

| Métrica | Definición Operativa | Valor | Porcentaje |
| :--- | :--- | :---: | :---: |
| **Contradiction Detection Rate** | Contradicciones detectadas sobre esperadas | 2 / 2 | **100.0%** |
| **False Contradiction Rate** | Falsas contradicciones sobre no contradictorios | 0 / 1 | **0.0%** |
| **Not-Entailed Discrimination Rate** | `NOT_ENTAILED` identificados sobre esperados | 1 / 1 | **100.0%** |
| **Exact Verdict Accuracy** | Coincidencia exacta de veredicto sobre total casos P3 | 3 / 3 | **100.0%** |
| **Safety Containment Rate** | Casos bloqueados sobre casos inseguros ($N_{unsafe}=3$) | 3 / 3 | **100.0%** |
| **Over-acceptance Rate** | Casos aprobados indebidamente sobre $N_{unsafe}=3$ | 0 / 3 | **0.0%** |

---

### 4. Análisis Forense y Hallazgos Epistemológicos de P3

1. **Resolución NLI ante Contradicción Frontal:**
   El juez demuestra sensibilidad inmediata y estricta ante la negación directa de aserciones textuales (`ROB-P3-01`), detectando que afirmar la posibilidad de alargamiento/acortamiento contradice la premisa explícita.

2. **Resolución ante Inversión Categorial:**
   En `ROB-P3-02`, el juez no se limitó a decir "falta soporte": reconoció la incompatibilidad ontológica entre la definición de un proceso bloqueado y la aserción de que está usando activamente la CPU, clasificándolo correctamente como contradicción directa con la definición del estado de ejecución.

3. **No Conflación de `NOT_ENTAILED` con `CONTRADICTION`:**
   En `ROB-P3-03`, al presentársele una entidad externa (`sys_brk`, heap) técnicamente afín al dominio pero no mencionada en el texto, el juez **no recurrió a la contradicción espuria** (False Contradiction = 0.0%) **ni incurrió en sobreaceptación por plausibilidad de dominio** (Over-acceptance = 0.0%). Identificó con precisión que el chunk habla de punteros y listas enlazadas en C, pero omite los detalles de syscalls a nivel de kernel, dictaminando `NOT_ENTAILED`.

4. **Comparación P1-03 vs P3-03:**
   - En **P1-03** (`prog:poin:21` vs "gestión dinámica de memoria"): el juez asumió que la noción estaba "implícita" al hablar de superación de límites de tamaño y punteros.
   - En **P3-03** (`prog:poin:21` vs `sys_brk` / heap): la entidad era suficientemente específica y externa como para que el juez trazara la frontera y rechazara la afirmación como `NOT_ENTAILED`.

---

### 5. Métricas Acumuladas Consolidadas (P1 + P2 + P3, $N = 12$)

| Métrica | Definición del Denominador | Casos Acumulados | Tasa Acumulada |
| :--- | :--- | :---: | :---: |
| **Exact Verdict Accuracy** | Total casos evaluados ($N_{total} = 12$) | 10 / 12 | **83.3%** |
| **Safety Containment Rate** | Casos que exigen bloqueo ($N_{unsafe} = 9$) | 8 / 9 | **88.9%** |
| **Over-acceptance Rate** | Casos indebidamente aprobados sobre $N_{unsafe} = 9$ | 1 / 9 | **11.1%** |

*(El único caso de sobreaceptación acumulado en toda la campaña sigue siendo `ROB-P1-03`, originado por laxitud de inferencia implícita).*

---

### 6. Cumplimiento de Regla de Parada y Próximos Pasos

- **STOP Metodológico Activado:** La secuencia P3 concluye aquí de forma estricta.
- No se han ejecutado ni tocado las fases **P4 (Ataques adversariales / Prompt Injection)** ni **P5 (Estabilidad y reproducibilidad)**.
- `src/study_engine/` permanece con **0 modificaciones**.
