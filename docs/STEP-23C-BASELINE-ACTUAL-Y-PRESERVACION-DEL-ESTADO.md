# STEP-23C — Baseline actual y preservación del estado

**Estado canónico:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**Anomalía histórica:** `UNRESOLVED_HISTORICAL_EVIDENCE`  
**Tipo:** referencia actual de solo lectura; no reconstruye estados anteriores

## 1. Identidad y precondiciones

Antes de la inspección sustantiva se observó:

- Repositorio: `/media/agustin/Laboratorio/study-engie`
- Rama: `talos-current-audit`
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`
- Resultado: rama y HEAD coinciden con los esperados por STEP-23C.

Existencia y rutas documentales al tomar el baseline:

| Expediente | Ruta | Estado |
|---|---|---|
| Contrato de ejecución STEP-22 | `docs/STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md` | Presente |
| Matriz de fronteras STEP-22 | `docs/STEP-22-TRUST-BOUNDARY-MATRIX.md` | Presente |
| Matriz de agregación STEP-22 | `docs/STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md` | Presente |
| Decisiones y bloqueos STEP-22 | `docs/STEP-22-DECISIONS-AND-BLOCKERS.md` | Presente |
| Informe general previo STEP-23 | No existe expediente persistido con ese título/ruta; STEP-23 estaba suspendido | Ausente |
| STEP-23A | `docs/STEP-23A-GIT-ANOMALY-ADJUDICATION.md` | Presente |
| STEP-23B | `docs/STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md` | Presente |
| Baseline STEP-23C | `docs/STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md` | Creado en esta fase, después de tomar el baseline |
| Adjudicación STEP-23C | `docs/STEP-23C-ADJUDICACION-DOCUMENTAL-Y-BLOQUEOS-ABIERTOS.md` | Creado en esta fase, después de tomar el baseline |

El estado protegido se limitó a la observación de las rutas incluidas por Git. No se abrieron bases de datos, corpus, snapshots ni contenido de raíces protegidas. La búsqueda por nombres conocidos de `knowledge_store.db`, `vector_store.db`, `student_state.db`, `data/student`, `data/web_state`, `data/student_submissions` y `snapshots/` no encontró entradas en la captura de estado. Esto solo significa que esos nombres no aparecen como cambios reportados por esta captura; no prueba ausencia de cambios ignorados, efectos transitorios ni estados fuera del alcance de Git.

## 2. Captura nominal actual

**Comando exacto:**

```text
git status --porcelain=v2 --branch --untracked-files=all
```

La salida íntegra se conservó, fuera del repositorio y del índice, en:

```text
/home/agustin/.copilot/session-state/af341721-5b9b-479c-9eb0-a54bd677732d/files/step23c-git-status-v2.txt
```

La captura contiene 1.957 líneas y 407.534 bytes. Incluye cabeceras de rama y cada registro de estado producido por la invocación. SHA-256 sobre esos bytes:

```text
5877c09f5d2729b5066bf36cfd4f3f31a4e6fdb82e50e1a946a3fddc7848fe5c
```

Ventana de observación local:

- Antes del comando: `2026-10-09T21:04:08,450223614-03:00`
- Después del comando: `2026-10-09T21:04:08,463279816-03:00`

La captura incluye las cabeceras:

```text
# branch.oid cc8acfae623f9d10c8366871470319786b6a7ca4
# branch.head talos-current-audit
# branch.upstream origin/talos-current-audit
# branch.ab +0 -0
```

La captura se escribió en la carpeta de archivos persistentes de esta sesión, no bajo el checkout. Su digest permite detectar cambios posteriores de esos bytes, pero no autentica Git, el host, la hora, el origen del estado ni el proceso que lo produjo.

## 3. Reglas y recuentos derivados de la misma captura

Los recuentos siguientes se derivaron exclusivamente de `step23c-git-status-v2.txt`, sin invocar otra forma de `git status`:

- Para registros `1`, `2` o `u`, la pareja de estado es `XY`: `X` es índice frente a HEAD y `Y` es árbol de trabajo frente al índice.
- Cada ruta cuyo carácter `X` no sea `.` suma una entrada staged.
- Cada ruta cuyo carácter `Y` no sea `.` suma una entrada unstaged.
- Un registro `?` suma una entrada untracked.
- Una ruta `MM` suma a staged y unstaged, pero es una sola ruta rastreada; los dos recuentos no son mutuamente excluyentes.
- La salida usó `--untracked-files=all`, por lo que enumera rutas untracked sin colapsarlas en directorios. El conteo representa registros de ruta, no una inferencia sobre su tipo de contenido.
- Los registros `2` identifican rename/copy y `u` identifica entradas no fusionadas/conflictos; sus registros se cuentan como una ruta afectada en cada columna `XY` distinta de `.`.

| Métrica | Recuento |
|---|---:|
| Rutas staged (`X != .`) | 1.863 |
| Rutas unstaged (`Y != .`) | 23 |
| Registros untracked (`?`) | 84 |
| Rutas rastreadas con algún cambio reportado (`1`, `2` o `u`) | 1.869 |
| Registros ordinarios (`1`) | 1.869 |
| Registros rename/copy (`2`) | 0 |
| Registros unmerged/conflicto (`u`) | 0 |
| Eliminaciones (`D` en X o Y) | 0 |
| Registros no interpretados, excluyendo cabeceras | 0 |

Distribución observada de parejas `XY`:

| `XY` | Rutas |
|---|---:|
| `M.` | 32 |
| `A.` | 1.814 |
| `MM` | 6 |
| `AM` | 11 |
| `.M` | 6 |

Verificación aritmética de la misma captura: staged = 32 + 1.814 + 6 + 11 = 1.863; unstaged = 6 + 11 + 6 = 23; rutas rastreadas con algún cambio = 32 + 1.814 + 6 + 11 + 6 = 1.869.

Los cuatro expedientes STEP-22 y los dos expedientes STEP-23A/B figuran como rutas untracked en el baseline. Los dos informes STEP-23C todavía no existían al momento de la captura.

## 4. Relación con la anomalía histórica

STEP-23A conserva `PARTIALLY_RECONCILED`; STEP-23B conserva `UNRESOLVED_HISTORICAL_EVIDENCE`. La explicación de granularidad untracked es compatible con las rutas citadas en STEP-23A, pero no demuestra que todo el delta se explique por ella. La discrepancia staged histórica sigue sin resolverse.

Este baseline describe únicamente el estado observado en el instante y scope anteriores. No se compara con las capturas históricas perdidas, no permite deducir rutas staged ausentes y no atribuye cambios a STEP-23, STEP-23A, STEP-23B, al operador ni a otro proceso.

## 5. Límites y preservación

- No se modificaron código, índice, configuración, perímetro, refs ni expedientes preexistentes.
- No se ejecutaron tests, scripts del proyecto, hooks, builds, workers ni código del repositorio.
- No se abrieron ni modificaron bases, corpus, snapshots o datos protegidos.
- El baseline íntegro está fuera del repositorio; el informe y el digest permiten localizarlo y comprobar igualdad de bytes, no reconstruir una historia autenticada.
- Los dos únicos paths documentales nuevos autorizados para STEP-23C son los dos expedientes STEP-23C declarados arriba.

## 6. Comprobación nominal final

Para verificar los cambios de esta fase se volvió a ejecutar exactamente:

```text
git status --porcelain=v2 --branch --untracked-files=all
```

La captura final se conservó fuera del repositorio en:

```text
/home/agustin/.copilot/session-state/af341721-5b9b-479c-9eb0-a54bd677732d/files/step23c-git-status-v2-final.txt
```

- Ventana: `2026-10-09T21:06:26,100044035-03:00` a `2026-10-09T21:06:26,115777575-03:00`.
- SHA-256: `f720d1ceb5ea1587ae8e7ff001851dfab0202888da4a33ea48d41385d1a06d4e`.
- La comparación nominal de ambas salidas porcelain v2 contiene exactamente dos registros añadidos y ninguna otra diferencia: `? docs/STEP-23C-ADJUDICACION-DOCUMENTAL-Y-BLOQUEOS-ABIERTOS.md` y `? docs/STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md`.
- Rama y HEAD finales: `talos-current-audit` / `cc8acfae623f9d10c8366871470319786b6a7ca4`.

Esta igualdad nominal entre el baseline y la captura final demuestra que las únicas diferencias Git observadas durante esta fase son los dos expedientes autorizados. No demuestra ausencia de escrituras transitorias ni efectos no observables por Git.
