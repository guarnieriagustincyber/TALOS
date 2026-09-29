# Instalación y lock de dependencias

## Autoridad y alcance

- `pyproject.toml` es la única fuente declarativa para runtime y extras.
- `requirements.lock` es un artefacto generado por `uv pip compile` con todos
  los extras (`dev`, `gate2-diagnostics`, `experiments` y `local-inference`).
  Contiene pins para reconstruir el entorno completo de verificación, no define
  dependencias directamente.
- `requirements.txt` se conserva solo por compatibilidad histórica. Es una
  lista parcial obsoleta y no debe usarse para instalar TALOS.

Dependencias directas añadidas tras revisar el código:

| Dependencia | Grupo | Evidencia de uso |
|---|---|---|
| `httpx` | runtime | Importada por backends LLM, factory, provider OpenAI-compatible y retrieval reranker. |
| `numpy` | runtime | Importada por `storage/knowledge_store.py` y retrieval/late chunking; necesaria también en pruebas de rendimiento y vectorización. |
| `pymupdf` | runtime | Importada por convertidores de documentos/PDF del paquete. |
| `python-multipart` | runtime | Requerida por FastAPI para registrar rutas multipart de carga de archivos. |
| `rapidfuzz` | `gate2-diagnostics` | Importación limitada al módulo de relaciones de evidencia de Gate 2. |
| `scipy` | `experiments` | Usada por scripts estadísticos de análisis experimental, fuera del runtime base. |
| `onnxruntime`, `tokenizers` | `local-inference` | Backend opcional de inferencia local ONNX; requerido por casos que usan los modelos ONNX locales. |

Sentence Transformers, PyTorch y Transformers se cargan de forma condicional
en rutas de embeddings avanzadas; no son requisitos de la instalación base ni
de los extras incluidos en este lock. Las funciones que los necesitan deben
reportar claramente su ausencia. `local-inference` cubre el backend ONNX CPU
validado por los tests.

## Regenerar

Fijar la versión de la herramienta usada para esta evidencia y regenerar el
lock desde la raíz del repositorio:

```bash
TOOL_VENV="$(mktemp -d "${TMPDIR:-/tmp}/talos-a2-tools.XXXXXX")"
python3 -m venv "$TOOL_VENV"
"$TOOL_VENV/bin/python" -m pip install "uv==0.12.20"
"$TOOL_VENV/bin/uv" --version
"$TOOL_VENV/bin/uv" pip compile pyproject.toml --all-extras --generate-hashes \
  --python-version 3.10 -o requirements.lock
```

`uv 0.12.20` es la versión usada para regenerar el lock de esta evidencia.
Instalar uv en un entorno aislado de herramientas y registrar su versión en
cambios futuros.

El `--python-version 3.10` valida el límite mínimo declarado por el proyecto;
uv resuelve wheels/hash disponibles para las plataformas compatibles y emite
marcadores de entorno cuando aplican. Tras cualquier cambio en `pyproject.toml`,
repetir la compilación y revisar el diff completo del lock.

## Reconstrucción sin contaminar el entorno de desarrollo

Desde la raíz del checkout, crear un virtualenv externo al repositorio y
sincronizarlo exclusivamente desde el lock:

```bash
TEMP_VENV="$(mktemp -d "${TMPDIR:-/tmp}/talos-a2-venv.XXXXXX")"
python3 -m venv "$TEMP_VENV"
"$TOOL_VENV/bin/uv" pip sync --python "$TEMP_VENV/bin/python" requirements.lock
"$TEMP_VENV/bin/python" -m pip install --no-deps --no-build-isolation -e .
"$TEMP_VENV/bin/python" -m pip check
```

La instalación editable con `--no-deps --no-build-isolation` instala el paquete local después de
sincronizar las dependencias pinneadas, sin permitir que pip sustituya
versiones del lock. `pip check` comprueba que los requisitos declarados por el
paquete están satisfechos. Registrar `sys.executable`, versión de Python,
plataforma y SHA-256 de `requirements.lock`. Antes, definir `TOOL_VENV` con la
ruta del entorno aislado que contiene uv. No activar el virtualenv ni llamar
al wrapper `scripts/test.sh`, que puede seleccionar el `.venv` del checkout.

Smoke imports del entorno reconstruido:

```bash
"$TEMP_VENV/bin/python" -c \
  "import fastapi, httpx, numpy, pydantic, pymupdf, pypdf, yaml"
"$TEMP_VENV/bin/python" -c \
  "from study_engine.cli import main; from study_engine.web.app import app; from study_engine.llm.factory import LLMProviderFactory"
"$TEMP_VENV/bin/python" -c \
  "from rapidfuzz import fuzz; import scipy; import onnxruntime; import tokenizers"
OPENBLAS_NUM_THREADS=1 "$TEMP_VENV/bin/python" \
  -m scripts.quality_gate --profile release
```

El tercer smoke cubre `gate2-diagnostics`, `experiments` y `local-inference`,
incluidos intencionalmente en el lock `--all-extras`. La salida del gate debe preservar
las exclusiones opcionales explicitadas en el contrato de pruebas; un resultado
PASS acredita el test gate bajo este lock y plataforma, no una certificación
automática del producto.

Usar `OPENBLAS_NUM_THREADS=1` para evaluar el umbral de latencia con un
número controlado de threads BLAS, en vez de una sobreasignación dependiente
del host. Registrar esta variable junto con el resultado del gate; no cambiar
el umbral para compensar un entorno de ejecución no controlado.
