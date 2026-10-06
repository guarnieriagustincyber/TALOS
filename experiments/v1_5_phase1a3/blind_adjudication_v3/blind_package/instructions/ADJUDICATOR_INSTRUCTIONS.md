# INSTRUCCIONES PARA EL ADJUDICADOR HUMANO ($N=1$) — PAQUETE V3
## TALOS V1.5 — Fase 1A.3: Adjudicación Incremental de Candidatos Armonizados

1. Abra `cases/cases_presentation.md` y `form/adjudication_form_v3.json`.
2. Para cada uno de los 22 casos (`CASE-01` a `CASE-22`):
   - Lea la consulta y las condiciones de relevancia/suficiencia establecidas en la rúbrica.
   - Examine el fragmento recuperado por cada uno de los **3 pipelines enmascarados** (`Pipeline_Sigma`, `Pipeline_Tau`, `Pipeline_Upsilon`).
   - Asigne una calificación discreta (0, 1 o 2) en las cuatro dimensiones estándar:
     * `relevance` (0: None, 1: Partial, 2: Highly Relevant)
     * `sufficiency` (0: Insufficient, 1: Partial, 2: Self-Sufficient)
     * `grounding_potential` (0: Risk, 1: Partial, 2: Strict)
     * `context_quality` (0: Mutilated, 1: Acceptable, 2: Clean)
   - Si detecta un fallo específico (ej. "oración cortada en puntero", "código truncado", "outlier"), documéntelo en `notes`.
3. Guarde el archivo `adjudication_form_v3.json` completado.
4. Nota de Blinding: Por mandato metodológico estricto (Directiva 1A.3, Sec. 16), todos los identificadores de modelos, referencias a la Condición H y puntajes de similitud coseno han sido eliminados de esta presentación para prevenir sesgos de anclaje numérico.
5. Tras completar la evaluación humana, el archivo de llaves `key/pipeline_mapping_v3.json` se desbloqueará para reconciliar los juicios con la identidad técnica de los embeddings.
