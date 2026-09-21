# 🔍 Configuración de OCR Local y Soberano (TALOS / KASIU)

Para libros o documentos que consisten enteramente en imágenes escaneadas sin capa de texto incrustada (por ejemplo, *Matemáticas Discretas de Kenneth Rosen*, 879 páginas de escaneo puro), TALOS incluye un subsistema de OCR local y hermético.

---

## 1. Descarga del Modelo de Idioma (Español)

Para mantener la **soberanía y privacidad absoluta** (sin enviar páginas a servicios en la nube), el motor utiliza Tesseract localmente mediante PyMuPDF.

1. Descarga el modelo de idioma español optimizado:
   ```bash
   # URL oficial del repositorio de Tesseract
   wget https://github.com/tesseract-ocr/tessdata/raw/main/spa.traineddata
   ```

2. Ubica el archivo en el directorio soberano del proyecto:
   ```bash
   mkdir -p data/ocr/tessdata
   mv spa.traineddata data/ocr/tessdata/
   ```

---

## 2. Detección Automática en el Pipeline

El convertidor `src/study_engine/ingestion/converters/tesseract_fallback.py` busca automáticamente en el siguiente orden de prioridad:

1. `data/ocr/tessdata/` *(Directorio local del proyecto - Prioritario y soberano)*
2. `/usr/share/tesseract-ocr/5/tessdata/` *(Instalación a nivel de sistema OS)*
3. `/usr/share/tesseract-ocr/4.00/tessdata/`

Cuando el archivo `spa.traineddata` está presente:
- `check_tesseract_availability()` retorna `True`.
- Cualquier página con 0 caracteres de texto vectorial se procesa automáticamente mediante `page.get_textpage_ocr(language="spa", tessdata="data/ocr/tessdata")`.
- Los chunks generados se registran con `has_ocr=True` y `ocr_provenance="local_tesseract"`.

---

## 3. Verificación Rápida

Podés verificar si el archivo de idioma fue detectado correctamente ejecutando:

```bash
.venv/bin/python -c '
from study_engine.ingestion.converters.tesseract_fallback import find_tessdata, check_tesseract_availability
print("OCR disponible:", check_tesseract_availability())
print("Ruta tessdata:", find_tessdata())
'
```
