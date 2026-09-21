# 🏛️ Architecture Decision Record (ADR): Pix2Text vs MathPix vs Conversión Estándar para Fórmulas Matemáticas

**Fecha:** 2026-09-13  
**Estado:** DECIDIDO / CONDICIONAL (Enmienda E4-1)  
**Autor:** TALOS Core Engineering / Epistemic Auditor  

---

## 1. Contexto y Problema

Durante el Gate CAL, se identificó que documentos con fórmulas matemáticas densas en PDF o imágenes presentan degradación de texto plano en OCR estándar (`MarkItDown`, `AnyDoc`), requiriendo el flag de auditoría `formulas_unextracted = True`. Para materias avanzadas (p. ej. Criptografía, Matemáticas Discretas, Complejidad Computacional), la extracción exacta de expresiones LaTeX es crítica para la verificación simbólica.

Se evaluaron tres opciones arquitectónicas:
1. **Mathpix Cloud API:** Alta precisión en fórmulas, pero introduce dependencia de red externa, costo recurrente por página y viola la soberanía de cómputo local offline.
2. **Pix2Text (p2t):** Modelo open-source local offline especializado en reconocimiento de texto libre y fórmulas matemáticas LaTeX en imágenes y PDFs.
3. **Pipeline Estándar CAL (MarkItDown / AnyDoc) con Marcado Forense:** Mantener extracción local rápida, marcando chunks con fórmulas no extraídas y activando Pix2Text únicamente como convertidor secundario especializado bajo ruteo determinista.

---

## 2. Decisión Adoptada

Se adopta la **Opción 3 (Pipeline Híbrido con Integración de Pix2Text como Especialista Local Offline)**:
- **Baseline General:** Mantener `MarkItDown` como convertidor primario ultrarrápido ($p95 < 1\text{ ms}$).
- **Detección Forense:** Los chunks con expresiones matemáticas complejas degradadas reciben el atributo `metadata.formulas_unextracted = True`.
- **Especialista Pix2Text:** Cuando un documento supera el umbral del $15\%$ de chunks con fórmulas degradadas (según la consulta en [`docs/ingestion_escalada.md`](file:///media/agustin/Laboratorio/study-engie/docs/ingestion_escalada.md)), se ejecuta `pix2text` en entorno de ingesta offline para generar una versión secundaria canónica.
- **Rechazo de MathPix Cloud:** Queda formalmente descartado por violar los principios de reproducibilidad determinista sin conexión de TALOS.

---

## 3. Consecuencias y Monitoreo

- **Positivas:** Cero regresión en latencia de ingesta para el 90% de los documentos convencionales. Aislamiento total de red mantenido.
- **Negativas / Costos:** Pix2Text requiere dependencias adicionales de visión por computadora (PyTorch, ONNX) en el entorno de ingesta pesada.
- **Monitoreo:** Cada corrida de ingesta escalada emite el reporte de chunks afectados vía `docs/ingestion_escalada.md`.
