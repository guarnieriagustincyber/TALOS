# Checkpoint 143: Especificación Canónica, Preflight Aprobado y Sellado Criptográfico de Fase 1D (Evidence Selection & Calibration)

**Fecha:** 2026-10-05T16:15:00-03:00  
**Fase:** FASE 1 — EVIDENCE RETRIEVAL / SUBFASE 1D — EVIDENCE SELECTION & CALIBRATION  
**Tipo de Documento:** CHECKPOINT DE GOBERNANZA, ESPECIFICACIÓN Y PREREGISTRO  
**Autoridad:** Directiva Canónica de Diseño, Especificación Metodológica y Preregistro / Antigravity Agent  
**Predecesores Directos:**
* Checkpoint 142 (`checkpoints/142-fase-1c-ejecucion-frontera-corpus-runtime.md`)  
**Sucesor Inmediato:** Checkpoint 143-R1 (`checkpoints/143-r1-reconciliacion-pre-ejecucion-fase-1d.md`)  
**Estatus de Fase 1D:** `SPECIFICATION_SEALED (RECONCILED IN CP143-R1) | PREFLIGHT = PASSED | EXECUTION = NOT_AUTHORIZED`  
**Aislamiento de Producción:** `DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED`

> [!NOTE]
> Este checkpoint fue objeto de reconciliación metodológica canónica pre-ejecución en [Checkpoint 143-R1](file:///media/agustin/Laboratorio/study-engie/checkpoints/143-r1-reconciliacion-pre-ejecucion-fase-1d.md) para formalizar el marco estadístico de $H_1$, la grilla de búsqueda de $H_4$ y el estatus operacional de $H_5$. Consulte CP143-R1 para el protocolo definitivo re-sellado.

---

## 1. ESTADO DE GOBERNANZA

```text
===============================================================================
TALOS V1.5 — CHECKPOINT 143: PHASE 1D SPECIFICATION, PREREGISTRATION & SEAL
===============================================================================

PHASE_1A                        = COMPLETE (CP131)
GATE_1A_1B                      = FORMALIZED (CP133)
FASE_1B                         = COMPLETE / CANONICALLY CLOSED (CP140)
FASE_1C                         = COMPLETE / CERTIFIED (CP142)
FASE_1D                         = SPECIFICATION_SEALED / PREFLIGHT_PASSED
  ├─ ESPECIFICACIÓN TÉCNICA     = v1.0.0-canonical (SHA-256: de6c5a1d...)
  ├─ PREREGISTRO FORMAL         = v1.0.0-canonical (SHA-256: 7a06ce07...)
  ├─ GUÍA METODOLÓGICA          = v1.0.0-canonical (SHA-256: 3807add6...)
  ├─ PREFLIGHT TÉCNICO          = PASSED (16/16, SHA-256: 1b42cfe8...)
  ├─ REGISTRO DE SELLO          = CERTIFIED (SHA-256: d767fccb...)
  ├─ MANIFIESTO DE EJECUCIÓN    = FROZEN (SHA-256: 5ad103d7...)
  ├─ BANCO DE CONSULTAS         = FROZEN (22 queries, SHA-256: e15d5106...)
  ├─ QRELS BASELINE             = FROZEN (176 cells, SHA-256: ed1c1f30...)
  └─ EJECUCIÓN EXPERIMENTAL     = NOT_AUTHORIZED (SPECIFICATION ONLY)
FASE_1E                         = BLOCKED (Promotion Gate)
FASE_2                          = NOT_AUTHORIZED
FASE_2.X (MODELOS DECISIÓN EST) = CANDIDATE / NOT_AUTHORIZED (CP138)

PRODUCTION_SELECTION            = NOT_PERFORMED
DATABASE_CHANGES                = 0
V1_RUNTIME_MODIFIED             = FALSE
PRODUCTION_ISOLATION            = INVIOLABLE (Certified Bit-for-Bit)

===============================================================================
```

---

## 2. INVENTARIO DE ARTEFACTOS Y VERIFICACIÓN CRIPTOGRÁFICA DE FASE 1D

| Artefacto | Ruta Canónica | SHA-256 | Estatus |
| :--- | :--- | :--- | :---: |
| **Especificación de Benchmark**| `reports/v1_5_phase1/PHASE_1D_RETRIEVAL_BENCHMARK_SPECIFICATION.md` | `de6c5a1d9591e477d78cd51b026df733a68ee24b114ca9efb7f491539a5a827e` | `SEALED` |
| **Preregistro Experimental** | `reports/v1_5_phase1/PHASE_1D_PREREGISTRATION.md` | `7a06ce07a2c7cc4564be971ef40c343ef0d8e09619267d2c34943896fdb0c4de` | `SEALED` |
| **Guía Metodológica** | `reports/v1_5_phase1/PHASE_1D_METHODOLOGY.md` | `3807add6ccae89b69354f77b8a6bbff173a05d16924ec4b275967d42a2d75bee` | `CANONICAL` |
| **Informe de Preflight** | `reports/v1_5_phase1/PHASE_1D_PREFLIGHT_REPORT.md` | `1b42cfe8ed606127188df4875bed81a33f77314514b54cd775240f16ca05c4d3` | `PASSED` |
| **Registro de Sello** | `reports/v1_5_phase1/PHASE_1D_PROTOCOL_SEAL.md` | `d767fccb423a7004818014a5ddd024309980ecb3f3afe58c27ca2785935d4d5c` | `CERTIFIED` |
| **Manifiesto de Ejecución** | `experiments/v1_5_phase1d/manifests/PHASE_1D_EXECUTION_MANIFEST.json` | `5ad103d78ba2365ad27556a33b924287df99ba27c517738ffb3666a1a5b3c9ad` | `FROZEN` |
| **Banco de Consultas** | `experiments/v1_5_phase1d/benchmark_queries.json` | `e15d5106ea2a14964572485be3b6e06145d4e4b0a6aa2e0c9e27d23de1b7d90c` | `FROZEN` |
| **Qrels Baseline** | `experiments/v1_5_phase1d/qrels/QREL_1D_BASELINE.json` | `ed1c1f30ab87ef64b0c1647b8d6cef9ddc473fe0538f1d15730277568dbf38aa` | `FROZEN` |
| **Configuración del Benchmark**| `experiments/v1_5_phase1d/configs/benchmark_config.json` | `e421e690ae92a1683dbf9a10663f1172eaf994ed3d4ad7f34f8d6df45c04471e` | `FROZEN` |
| **Protocolo de Cegamiento** | `experiments/v1_5_phase1d/protocol/blinding_protocol.json` | `df72f8b58b3f4f532ce5bcb6fd8998ae28ed532500ba3d0dd089f9fdf635bccf` | `FROZEN` |

---

## 3. RESUMEN DEL DISEÑO EXPERIMENTAL PREREGISTRADO

1. **Pregunta Central:**
   Evaluar qué estrategia recupera de manera más fiable evidencia relevante y suficiente en consultas curriculares, y bajo qué condiciones TALOS se abstiene adecuadamente ante evidencia insuficiente o fuera de dominio.
2. **Desacoplamiento Conceptual:**
   Separación formal de Retrieval (ranking), Relevance (pertinencia tópica), Sufficiency (completitud factual para responder) y Abstention/Calibration (seguridad fail-closed).
3. **Hipótesis Científicas Congeladas (H1 a H5):**
   - **H1:** Brecha relevancia–suficiencia ($\overline{P@1} - \overline{S@1} \ge 0.15$).
   - **H2:** Valor de la expansión estructural mediante diseño estrictamente pareado ($\Delta S_i = S_{C6, i} - S_{C5, i}$ sobre el mismo candidato semilla).
   - **H3:** Superioridad de la fusión híbrida RRF ($C4$) sobre componentes individuales ($C0, C1, C2, C3$) en nDCG@5 y MRR@5.
   - **H4:** Calibración mediante umbral de similitud estático ($\tau_{\text{sim}} = 0.40$).
   - **H5:** Abstención confiable mediante reranking neuronal y compuerta guard ($C7$, $\tau = 0.35$, $A_{\text{OOD}} = 100\%$, $\text{FRR}_{\text{ID}} \le 10\%$).
4. **Condiciones Experimentales:**
   $C_0$ (BM25/FTS5), $C_1$ (Dense Qwen 1024d), $C_2$ (Dense BGE 1024d), $C_3$ (Dense E5 384d), $C_4$ (Hybrid RRF $k=60$), $C_5$ (Reranker BGE), $C_6$ (Reranker + Expansión), $C_7$ (Reranker + Expansión + Guard $\tau=0.35$).
5. **Compromisos Anti-P-Hacking:**
   Prohibición absoluta de alterar queries, qrels, umbrales o parámetros tras la observación de resultados.

---

## 4. PREFLIGHT TÉCNICO APROBADO (16 / 16)

Se auditó el cumplimiento estricto de los 16 requisitos previos mandatados por la directiva:
* Bloqueadores Críticos: 0
* Problemas Mayores: 0
* Commit de Runtime Anclado: `f81134fc2293916210d53c8065f3a0049e52b0b4`
* Bases de Datos Productivas Verificadas e Inmutables: 6 de 6 idénticas a baseline.
* Dictamen: `PHASE_1D_PREFLIGHT = READY_FOR_EXECUTION`.

---

## 5. AISLAMIENTO DE PRODUCCIÓN CERTIFICADO

Se ratifica formalmente la verificación de hash SHA-256 de las 6 bases de datos productivas:
* `cal_store.db`: `82773155ca35028274ba0f378fdcd37a5374bb4483a579654a6e9facfd443782`
* `knowledge_store.db`: `fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1`
* `quotas.db`: `09838ed16f1bbab384e6a83be651c9f8657db11c6a72caa5c32947a2cc18050d`
* `student_state.db`: `f70f380dbad3f50cb7fa825009d8afd7d0d07ed0b4501c329c65288d4e840b2d`
* `study_engine.db`: `e3ba06536f7dbba337dee3c1c5f01b43660ce276abb54c5cee2d5defc5b970aa`
* `vector_store.db`: `d6d9f8c8eb6e5188e8e600a73cc05bd001d2e389061815d7d0df33f447a9dde4`

```text
DATABASE_CHANGES = 0 | V1_RUNTIME_MODIFIED = FALSE | PRODUCTION_SELECTION = NOT_PERFORMED
```

---

## 6. CONDICIÓN DE PASO Y SIGUIENTE ACCIÓN

La especificación, preregistro e insumos de Fase 1D quedan formalmente sellados.  
La ejecución física del benchmark requiere una **Directiva Canónica de Autorización de Ejecución de Fase 1D** independiente.
