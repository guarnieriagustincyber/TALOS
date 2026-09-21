# 📚 Runbook: Ingesta Escalada de Documentos en TALOS (Fase E4 / Enmienda E4-1)

Este runbook define el procedimiento operativo estandarizado (SOP) para la ingesta escalada de nuevos corpus y cuadernos de estudio bajo la arquitectura **CAL (Conversion Arbitration Layer)** y la federación de cuadernos de la Fase E4.

---

## 1. Principios Rectores de Ingesta

1. **Soberanía Epistémica:** Cero invocaciones a LLMs durante las etapas de probe, ruteo, conversión, arbitraje o paginación.
2. **Invarianza RAW:** Los archivos físicos originales se leen en modo de solo lectura. Su hash SHA-256 se calcula antes de cualquier procesamiento y se registra en `provenance.source_hash`.
3. **Paginación Fiel:**
   - Documentos paginados (PDF): páginas 1-based reales preservadas.
   - Hojas de cálculo (XLSX): paginación ordinal por hoja (`sheet_idx + 1`).
   - Presentaciones (PPTX): paginación ordinal por diapositiva (`slide_idx + 1`).
4. **Metadata Curricular Cerrada:** Cada chunk generado debe contener estrictamente los atributos curriculares: `subject`, `level`, `book`, `chapter`, `section`, `page_start`, `page_end`.

---

## 2. Flujo Operativo de Ingesta

### Paso 1: Verificación de Formato y Probe Determinista
Para cada documento a incorporar:
```bash
PYTHONPATH=src .venv/bin/python3 -c "
from study_engine.ingestion.conversion_probe import ConversionProbe
probe = ConversionProbe()
profile = probe.probe_document('path/to/document.ext')
print('Probe profile:', profile.to_dict())
"
```

### Paso 2: Ruteo y Conversión Conforme a Tabla Congelada
El documento se convierte utilizando los conversores primario y secundario según `config/routing_table.frozen.json`.
- Si `divergence > 0.12`: Se marca `has_conflict = True` y se audita el conflicto.
- Si secundario supera al primario por $\delta_{\text{canon}} \ge 0.15$: Se promueve el secundario como canónico con flag `stability_check`.

### Paso 3: Monitoreo de Fórmulas Matemáticas y Flagging
Durante la ingesta, documentos con presencia de fórmulas en texto plano o LaTeX degradado son etiquetados en su metadata JSON con:
```json
{
  "formulas_unextracted": true,
  "formula_count_estimated": 12
}
```

### Paso 4: Consulta Forense en SQLite de Fórmulas Degradadas
Para auditar la densidad de fórmulas no extraídas en el almacén de conocimiento:
```sql
SELECT 
    c.source_id,
    c.document_name,
    COUNT(c.id) AS total_chunks,
    SUM(CASE WHEN json_extract(c.metadata, '$.formulas_unextracted') = 1 
             OR json_extract(c.metadata, '$.formulas_unextracted') = true 
        THEN 1 ELSE 0 END) AS unextracted_formula_chunks,
    ROUND(CAST(SUM(CASE WHEN json_extract(c.metadata, '$.formulas_unextracted') = 1 
                        OR json_extract(c.metadata, '$.formulas_unextracted') = true 
                   THEN 1 ELSE 0 END) AS REAL) / COUNT(c.id) * 100, 2) AS unextracted_pct
FROM chunks c
GROUP BY c.source_id, c.document_name
HAVING unextracted_formula_chunks > 0
ORDER BY unextracted_pct DESC;
```

---

## 3. Umbrales de Alerta y Escalación a OCR Especializado (Pix2Text)

- **Umbral Verde ($< 5\%$ de chunks con fórmulas degradadas en el cuaderno):** Ingesta estándar mediante MarkItDown / AnyDoc.
- **Umbral Amarillo ($5\% - 15\%$):** Se genera aviso en reporte de auditoría. Se activa cuarentena temporal para claims matemáticos exactos (`claim_type = mathematical`).
- **Umbral Rojo ($> 15\%$ de chunks matemáticos afectados):** Se detiene la admisión curricular del documento y se deriva al pipeline especializado de OCR matemático documentado en [`artifacts/decisions/pix2text_decision_record.md`](file:///media/agustin/Laboratorio/study-engie/artifacts/decisions/pix2text_decision_record.md).

---

## 4. Hook de Monitoreo de Recuperación Estructural Post-Ingesta (E5.5 / CAL-R3)

Tras cada lote de ingesta escalada o actualización del almacén de conocimiento, se ejecuta obligatoriamente el hook de auditoría estructural:
```bash
PYTHONPATH=src .venv/bin/python3 scripts/monitor_structural_recovery.py --db-path data/benchmark/db/benchmark_store.db
```

Este hook:
1. Extrae y certifica el hash SHA-256 inmutable de la base de conocimiento (`provenance.corpus_hash`).
2. Mide la tasa de preservación y recuperación para:
   - **Tablas Markdown:** Preservación de pipes `|` y formato tabular sin colapso.
   - **Bloques de Código:** Fenced code blocks con delimitadores pareados y syntaxes conservadas.
   - **Jerarquía de Encabezados:** Estructura de títulos (`#`, `##`, `###`) sin saltos de nivel degradados.
3. Calcula intervalos de confianza exactos Clopper-Pearson al 95%.
4. Emite la alerta determinista `STRUCTURAL_RECOVERY_DEGRADED` en caso de que el límite inferior del CI de cualquier estructura caiga por debajo del umbral base fijado en el Gate CAL.

---

## 5. Protocolo de Remediación Estructural de Tablas (Fase E6 / Post-E5)

Para subsanar la alerta `STRUCTURAL_RECOVERY_DEGRADED` de forma no destructiva y sin metric gaming:
1. **Detección Columnar Especializada:** Emplear `pdfplumber` o la API de tablas de `pymupdf` (`page.find_tables()`) exclusivamente sobre las páginas detectadas con contenido tabular en PDFs.
2. **Re-generación Canónica:** Re-emitir chunks tabulares en formato Markdown delimitado estándar (`| col1 | col2 |` con separador `|---|---|`).
3. **Medición sobre Conjunto Adjudicado Real:** Medir la tasa de retención sobre las tablas curricularmente adjudicadas antes de promover la alerta a estado `PASSED`.
