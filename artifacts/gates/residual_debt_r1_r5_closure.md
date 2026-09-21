# 🏛️ Certificación de Cierre de Deuda Residual: R1-R5 (E2/E3) y CAL-R1-CAL-R6

**Fecha:** 2026-09-13  
**Estado:** FORMALMENTE CERRADO Y VERIFICADO PARA GATE E4  
**Auditoría:** Dirección Técnica / TALOS Core Architecture  

---

## 1. Cierre Formal de Deuda Residual R1-R5 (Fases E2 / E3)

| ID | Requisito de Deuda | Evidencia de Cierre en Artefactos | Estado |
|---|---|---|:---:|
| **R1** | G6 en lista de re-adjudicación de E5 o justificación formal como guardrail | Registrado formalmente en [`gate_report_e2.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e2.md#L47) como `CONDICIONAL (re-adjudicación en E5, n≥100)` con CI Clopper-Pearson `[0.00%, 8.20%]`. | ✅ **CERRADO** |
| **R2** | Nota de ventana de implementación E3 + verificación en Git | Explicado y auditado en [`gate_report_e3.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e3.md#L20-L30) (Sección 1), confirmando desarrollo en ramas separadas y comando `git log` limpio sobre `src/study_engine/evidence/`. | ✅ **CERRADO** |
| **R3** | Tabla de sweep de $\alpha$ en el CalibrationContract | Documentada explícitamente en [`gate_report_e2.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e2.md#L53-L64) (Sección 3): sweep 0.05, 0.10, 0.15 con regla de selección $\min \|FAR - FRR\|$ sujeta a $FAR \le \alpha$. | ✅ **CERRADO** |
| **R4** | Reconciliación de discrepancia de latencia (32.4 ms vs 15.2 ms) | Aclarada en [`gate_report_e2.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e2.md#L75-L93) y [`gate_report_e3.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e3.md#L84-L101): 32.4 ms es el $p95$ general de E1 (FTS5 + Dense + Greedy); 15.2 ms corresponde al subconjunto optimizado con caché caliente en la suite de E2. | ✅ **CERRADO** |
| **R5** | Valores exactos de pins criptográficos de E3 expuestos | Publicados en cabecera de [`gate_report_e3.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/gates/gate_report_e3.md#L10-L17): Commit `2aa6c38...`, KnowledgeStore SHA `03f09818...`, StudentState SHA `646c9781...`, results E2/E3 SHAs. | ✅ **CERRADO** |

---

## 2. Cierre Formal de Residuales CAL-R1 a CAL-R6 (Fase CAL)

| ID | Requisito de Cierre | Evidencia en `artifacts/gates/gate_report_cal.md` | Estado |
|---|---|---|:---:|
| **CAL-R1** | Declaración de alcance de latencia | Medición de 0.64 ms ($p50$) y 0.91 ms ($p95$) declarada explícitamente como ciclo en memoria del probe/arbiter; I/O offline batch admisible en 2-15s por libro. | ✅ **CERRADO** |
| **CAL-R2** | Determinismo del probe versionado | Probe v1.0.0 produce 10/10 hashes idénticos en ejecuciones repetidas. | ✅ **CERRADO** |
| **CAL-R3** | Clopper-Pearson CIs en recuperación estructural | Tablas y bloques de código con CIs calculados y documentados en reporte de gate. | ✅ **CERRADO** |
| **CAL-R4** | Desigualdad de gobernanza cloud | $\tau_{\text{cloud}} = 0.85 > \tau_{\text{local}} = 0.75$ formalmente operativa y testeada. | ✅ **CERRADO** |
| **CAL-R5** | Pins completos de congelación CAL | Commit `2aa6c38`, SHA de routing freeze (`2b43b6...`), SHA manifest (`4b63ff...`), $\tau_{\text{conflict}}=0.12$, $\delta_{\text{canon}}=0.15$. | ✅ **CERRADO** |
| **CAL-R6** | Trazabilidad forense de conflictos | Los 4 documentos en conflicto (`doc_multicolumn_01` a `04`) poseen `conflict_flag=True` en sus chunks y registro dual en SQLite. | ✅ **CERRADO** |
