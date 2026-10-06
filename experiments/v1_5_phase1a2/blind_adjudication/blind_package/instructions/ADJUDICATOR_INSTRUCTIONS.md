# INSTRUCCIONES PARA EL ADJUDICADOR HUMANO ($N=1$)

1. Abra `cases/cases_presentation.md` y `form/adjudication_form.json`.
2. Para cada uno de los 22 casos (`CASE-01` a `CASE-22`):
   - Lea la consulta y las condiciones de relevancia/suficiencia.
   - Examine el fragmento recuperado por cada pipeline enmascarado (`Pipeline_Alpha` a `Pipeline_Iota`).
   - Asigne una calificación discreta (0, 1 o 2) en las cuatro dimensiones de la rúbrica:
     * `relevance`
     * `sufficiency`
     * `grounding_potential`
     * `context_quality`
   - Si detecta un fallo específico (ej. "oración cortada en puntero", "outlier masivo"), anótelo en `notes`.
3. Guarde el archivo `adjudication_form.json` completado.
4. Una vez completado, el archivo de llaves `key/pipeline_mapping.json` será desbloqueado para desenmascarar los resultados y calcular las métricas canónicas (`Relevant@1`, `Sufficient@1`, `Grounding@1`).
