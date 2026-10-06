# CHECKPOINT 134 — DISEÑO EXPERIMENTAL Y PREREGISTRO DE FASE 1B
## CORPUS → EVIDENCE: ESPECIFICACIÓN METODOLÓGICA Y PROTOCOLO CANÓNICO

**Fecha:** 2026-10-05  
**Fase:** TALOS V1.5 — Fase 1 (Evidence Retrieval) / Subfase 1B (Corpus → Evidence)  
**Ciclo:** Diseño Metodológico, Formalización de Hipótesis y Preregistro  
**Tipo:** Checkpoint de Gobernanza, Preregistro Experimental y Delimitación Metodológica  
**Autoridad:** Directiva de Especificación y Diseño Experimental de Fase 1B / Antigravity Agent  
**Referencia Documental Primaria:**
- `reports/v1_5_phase1/PHASE_1B_EXPERIMENTAL_DESIGN.md` (SHA-256: `92cfd24dc9409d5829fe7e4881b3a258e8582f52ad15343ce74ebff3b18a7cd3`)
- `reports/v1_5_phase1/PHASE_1A_1B_BOUNDARY_CONTRACT.md` (CP133)
- `reports/v1_5_phase1/TALOS_V1_5_CANONICAL_ROADMAP_RECONSTRUCTION.md` (CP132)
- `reports/v1_5_phase1/PHASE_1A_FINAL_SYNTHESIS.md` (CP131)
- `docs/ROADMAP_V1_5_MASTER.md`

---

## 1. ESTADO DE GOBERNANZA MULTIDIMENSIONAL

```text
1B_DESIGN                 = COMPLETE
1B_EXECUTION              = NOT_STARTED
PROTOCOL_VERSION          = 1.0.0-preregistered
PREDECESSOR_GATE          = GATE_1A_1B_FORMALIZED (CP133)
PRODUCTION_SELECTION      = NOT_PERFORMED
DATABASE_CHANGES          = 0
RUNTIME_CHANGES           = 0
V1_RUNTIME_MODIFIED       = FALSE
V1_ISOLATION              = INVIOLABLE
ACTIVE_WORKSPACE          = CLEAN
NEXT_AUTHORIZED_STEP      = FASE_1B_EXECUTION_AUTHORIZATION
```

---

## 2. RESUMEN DEL CHECKPOINT

El **Checkpoint 134** certifica la culminación y sellado formal del **diseño experimental y protocolo preregistrado de la Fase 1B (Corpus → Evidence)**, estableciendo todas las condiciones científicas, algorítmicas y de evaluación humana previas a cualquier ejecución física:

1. **Desacoplamiento Estructural (Stage A vs. Stage B):**  
   Se separa formalmente la fase de **Retrieval Puro (Stage A: generación y ordenamiento de candidatos)** de la fase de **Evidence Assessment (Stage B: suficiencia contextual, anclaje y compuerta de abstención)**, desmantelando la falacia de que una mayor similitud semántica o léxica garantiza automáticamente suficiencia informativa docente.
2. **Definición de 6 Preguntas de Investigación (RQ1 a RQ6):**  
   Se definen formalmente las interrogantes sobre calidad de retrieval (RQ1), suficiencia textual (RQ2), expansión contextual AST / ContextPack (RQ3), abstención semántica y controles OOD (RQ4), robustez ante representación (RQ5), y trazabilidad criptográfica (RQ6).
3. **Formulación y Congelamiento de Hipótesis (H1 a H5):**  
   Se preregistran 5 hipótesis comprobables con variables independientes/dependientes, controles y criterios de evaluación unívocos:
   - `H1`: Brecha estructural entre relevancia y suficiencia ($\le 15\%$ suficiencia en retrieval atómico).
   - `H2`: Duplicación relativa de suficiencia mediante expansión contextual determinista ($\pm 1$ bloque AST, $\le 1.500$ tokens).
   - `H3`: Superioridad de la fusión híbrida RRF ($k=60$) sobre BM25 y Dense por separado.
   - `H4`: Inutilidad de umbrales estáticos de similitud coseno para separar consultas in-domain de OOD.
   - `H5`: Abstención semántica efectiva mediante score logit de reranker cross-encoder.
4. **Matriz Factorial de 8 Condiciones ($C_0$ a $C_7$):**  
   Se formalizan las condiciones experimentales sin denominaciones subjetivas:
   - $C_0$: Baseline FTS5 BM25 V1 (C1, Top-5, sin expansión, sin abstención).
   - $C_1, C_2, C_3$: Dense Retrieval en Condición H (Qwen3, BGE-M3, E5-small).
   - $C_4$: Fusión Híbrida RRF (FTS5 + Dense Qwen).
   - $C_5$: RRF + Neural Cross-Encoder Reranker (`BAAI/bge-reranker-base`).
   - $C_6$: Condición $C_5$ + Expansión Contextual Determinista AST.
   - $C_7$: Condición $C_6$ + Compuerta de Abstención Semántica.
5. **Protocolos de Integridad, Cegamiento y Evaluación:**  
   - Banco de consultas inmutable (22 consultas oficiales de `benchmark_queries_pilot.json`).
   - Controles negativos OOD (`Q1A2-37`, `Q1A2-38`, `Q1A2-39`, `Q1A2-40`) con exigencia de 100% de abstención.
   - Adjudicación humana ciega con enmascaramiento estricto de modelos, condiciones y scores numéricos.
   - Catálogo de 10 métricas (`MET-01` a `MET-10`) con distinción entre métricas técnicas y juicios humanos.
   - 7 Criterios canónicos de aborto inmediato (`ABORT_*`).
6. **Aislamiento Total de TALOS V1:**  
   Se reitera la inmutabilidad de las bases operativas (`knowledge_store.db`, `vector_store.db`, `student_state.db`) con `DATABASE_CHANGES = 0`.

---

## 3. AUDITORÍA DE INSUMOS Y SALIDAS

### Insumos Clave:
- Contrato Canónico de Frontera: `reports/v1_5_phase1/PHASE_1A_1B_BOUNDARY_CONTRACT.md` (SHA-256: `71948cd9c2e4276feb426fc4aa2a223f002c0b16dfa90d3f269c806d4b792c95`).
- Roadmap Canónico Global: `reports/v1_5_phase1/TALOS_V1_5_CANONICAL_ROADMAP_RECONSTRUCTION.md` (CP132).
- Síntesis Final de 1A: `reports/v1_5_phase1/PHASE_1A_FINAL_SYNTHESIS.md` (CP131).
- Manifiesto Condición H: `experiments/v1_5_phase1a3/C2_HARMONIZED_MANIFEST.jsonl` (SHA-256: `bc683f0b...`).
- Banco Oficial de Consultas: `experiments/v1_5_phase1a2/configs/benchmark_queries_pilot.json` (SHA-256: `97a29e2f...`).

### Salidas Producidas:
- Documento de Diseño Experimental y Preregistro:  
  `reports/v1_5_phase1/PHASE_1B_EXPERIMENTAL_DESIGN.md`  
  (SHA-256: `92cfd24dc9409d5829fe7e4881b3a258e8582f52ad15343ce74ebff3b18a7cd3`).
- Checkpoint de Gobernanza:  
  `checkpoints/134-fase-1b-diseno-experimental.md`.

---

## 4. DICTAMEN FINAL DE CIERRE

```text
FASE 1B EXPERIMENTAL DESIGN:
COMPLETE

FASE 1B PREREGISTERED PROTOCOL:
SEALED (v1.0.0-preregistered)

FASE 1B EXECUTION:
NOT_STARTED

PRODUCTION SELECTION:
NOT_PERFORMED

DATABASE CHANGES:
0

RUNTIME CHANGES:
0

V1 RUNTIME MODIFIED:
FALSE

NEXT AUTHORIZED WORK:
FASE 1B — AUTORIZACIÓN Y EJECUCIÓN EXPERIMENTAL DEL PROTOCOLO PREREGISTRADO
(O EN PARALELO: TRACK DE PLATAFORMA B0.5)
```
