# TALOS V1.5 — STEP-23B: Validación de capturas históricas del índice

**Resultado:** `UNRESOLVED_HISTORICAL_EVIDENCE`  
**Estado canónico:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**STEP-23:** suspendido  
**Alcance:** validación documental de capturas existentes; no se crea un baseline actual

## 1. Identidad verificada

Antes de inspeccionar las capturas se verificó:

- Rama: `talos-current-audit`.
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`.

Ambos valores coinciden con los esperados. Esta verificación identifica el checkout actual; no autentica ni reconstruye el estado histórico del índice.

## 2. Capturas históricas localizadas

STEP-23A cita dos salidas temporales de herramientas como base de su comparación:

| Referencia citada en la sesión | Uso declarado | Disponibilidad al realizar STEP-23B |
|---|---|---|
| `/tmp/1791589677616-copilot-tool-output-30260-58c0a55a-b0de-4258-b54a-73f120074cdf.txt` | Captura anterior, con conteos `1.869 / 23 / 76` y entradas untracked de directorio | No existe en esa ruta |
| `/tmp/1791589909599-copilot-tool-output-30260-348d70a8-1382-4e44-90a9-74da14f0b989.txt` | Captura posterior `git status --short --untracked-files=all`, con conteos `1.863 / 23 / 82` | No existe en esa ruta |

Las rutas fueron comprobadas de forma no modificadora. Los resultados de comandos y las rutas citadas permiten saber que se intentó una comparación textual `git diff --no-index --unified=0` entre esas salidas, pero los archivos comparados ya no están disponibles para revisar o repetir el análisis. Las capturas eran salidas temporales de herramientas, no artefactos persistidos con identidad, digest, esquema o cadena de custodia.

## 3. Comparabilidad y categorías de estado

STEP-23A describe la captura posterior con `--untracked-files=all`; la captura anterior se representa en el expediente con dos rutas de directorio (`graphify-out/2026-10-08/` y `graphify-out/2026-10-09/`), mientras que la posterior lista ocho archivos bajo esos directorios. Esto evidencia que la granularidad de representación de untracked no es igual. El comando exacto y las opciones de la captura anterior no pueden verificarse a partir de los expedientes persistidos.

Por tanto:

- **Formato/opciones:** no se puede acreditar que ambas capturas se generaran con opciones idénticas. La diferencia observada de granularidad untracked es compatible con distinto modo de enumeración, pero no permite reconstruir la invocación anterior completa.
- **Categorías X/Y/untracked:** los informes contienen conteos agregados de staged, unstaged y untracked. No hay dos inventarios nominales persistidos y completos sobre los que validar, ruta por ruta, la columna `X` (índice) y la columna `Y` (árbol de trabajo). No se puede confirmar que las tres categorías se conservaran íntegramente y con una regla de conteo común.
- **Completitud:** los documentos STEP-22 registran conteos agregados, no el inventario nominal del índice de ambos momentos. Las salidas temporales citadas ya no están disponibles.
- **Procedencia:** no se preservaron identificadores/digests de capturas, invocaciones completas, stdout íntegro o recibos que permitan verificar que cada salida corresponde a un único `git status` completo.
- **Identidad temporal:** los informes asocian los conteos a inicio/cierre de fases, pero la evidencia disponible no permite reconstruir un baseline staged nominal con tiempo y scope verificables de forma independiente.
- **Método de conteo:** STEP-23A señala comandos posteriores y un `awk` para conteos, pero los conteos históricos de STEP-22 son declarativos. No se demuestra que todos usaran el mismo parser, modo untracked ni unidad de conteo.

La ausencia de esas propiedades impide extraer y comparar de forma confiable las entradas staged (`X`) y unstaged (`Y`). No se identifican seis rutas staged por aritmética ni se interpreta la falta de un diff actual como prueba de que nunca hubo una diferencia.

## 4. Evaluación de STEP-23A

La afirmación de STEP-23A de que la comparación nominal no mostró seis rutas staged retiradas no puede reproducirse con las capturas históricas ahora disponibles. La comparación entre textos temporales que ocurrió durante STEP-23A queda registrada como una observación de esa sesión, pero no sustituye evidencia nominal persistida, completa y comparable.

La explicación parcial del conteo untracked como cambio de granularidad es plausible y está respaldada por los nombres de directorio/archivo citados en STEP-23A. No resuelve la discrepancia staged ni demuestra que todo el delta untracked represente únicamente una variación de formato. Se conserva el resultado previo de STEP-23A, `PARTIALLY_RECONCILED`, como registro histórico y no se eleva a reconciliación completa.

## 5. Clasificación final

**`UNRESOLVED_HISTORICAL_EVIDENCE`**

La discrepancia staged no es verificable con la evidencia histórica persistida disponible. Faltan capturas nominales staged completas y comparables, con procedencia e identidad temporal suficientes. La diferencia `1.869` frente a `1.863` no autoriza inferir nombres, operación causante ni actor responsable.

No se creó una captura histórica sustituta ni se comparó la evidencia histórica con el inventario actual. No se atribuye autoría ni causalidad.

## 6. Límites de la actividad

- Inspección de solo lectura; la única identidad del repositorio consultada fue rama y HEAD.
- No se ejecutaron tests, scripts, hooks ni código del repositorio.
- No se modificaron índice, árbol de trabajo, refs, configuración Git ni expedientes anteriores.
- El único archivo nuevo de esta fase es este expediente STEP-23B.
- No se reanuda STEP-23 ni se altera código o perímetro.

**Estado final obligatorio:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`. La reanudación de STEP-23 requiere una decisión explícita del operador.
