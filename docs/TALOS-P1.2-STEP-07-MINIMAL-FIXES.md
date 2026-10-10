# TALOS-P1.2-STEP-07 — FIXES MÍNIMOS ADJUDICADOS

Estado: `BLOCKED-REGRESSION`

## Objetivo

Aplicar correcciones mínimas, legibles y acotadas para los defectos adjudicados en STEP-06 sin reabrir el Quality Gate ni tocar datos protegidos.

## Cambios hechos

1. Normalización de rutas SQLite URI en `src/study_engine/storage/sqlite_engine.py`
   - Soporta valores como `sqlite:///tmp/...`, `sqlite:////...` y `file://...`.
   - Convierte las URIs a un `Path` real antes de crear directorios o conectar la base.
   - Preserva el comportamiento de `:memory:` y evita tratar literales de URI como rutas de archivo.

2. Import faltante en `tests/pedagogy/test_chat_sse_endpoint.py`
   - Se añade `import sqlite3` antes de usar `sqlite3.connect(...)`.
   - Esto corrige el `NameError` identificado sin cambiar la lógica de producción.

## No ejecutado

- No se ejecutó `pytest`.
- No se ejecutó `scripts/test.sh`.
- No se ejecutó `scripts/quality_gate.py`.
- No se tocaron bases protegidas ni snapshot B06.
- No se altera el estado de bloqueo operativo de P1.2.

## Estado de cierre para esta fase

P1.2 permanece `BLOCKED-REGRESSION` y requiere revisión humana antes de reintentar una ejecución del gate. La corrección aplicada es una preparación mínima para la siguiente validación autorizada, no una revalidación de la suite.
