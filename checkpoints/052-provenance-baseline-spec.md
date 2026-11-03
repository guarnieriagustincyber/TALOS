# Checkpoint 052 — provenance de `A_PRE_0_BASELINE_SPEC.md`

Fecha: 2026-10-01
Repositorio: `guarnieriagustincyber/TALOS`
HEAD inicial: `f81134fc2293916210d53c8065f3a0049e52b0b4`

## 1. Estado inicial y alcance

La tarea parte de checkpoint [051](./051-reentrada-autoridad-y-crosswalk.md)
y resuelve exclusivamente su bloqueo de provenance. No se tocó ningún
artefacto canónico ni se ejecutó TALOS, FastAPI, workloads, probes,
benchmarks, procesos de VM, DB, corpus o modelos.

| Estado vinculante | Valor verificado |
|---|---|
| A-PRE-0 | `NOT_READY`, `predicate_result=false` |
| A-PRE-1 | `NOT_AUTHORIZED / NOT_EXECUTED`; `constraints.a_pre_1_authorized=false` |
| Inventory | `frozen=false` |
| Disposiciones globales | 385/385 `UNKNOWN` |
| `STOP_REASON` de checkpoint 051 al reingresar | `UNRESOLVED_PROVENANCE` |

Hashes de entrada:

| Artefacto | SHA-256 |
|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json` | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Spec en `docs/` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Spec en `files/` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |

## 2. Inventario de las copias locales

Se encontraron exactamente las dos copias indicadas dentro del workspace.
Se compararon SHA-256, bytes, estructura Markdown y contenido. El estado de
tracking se refiere a `HEAD=f81134f`, no a las referencias históricas de
agentes.

| Path | SHA-256 | Tamaño / líneas | Metadata observada | Tracking en HEAD |
|---|---|---:|---|---|
| `docs/A_PRE_0_BASELINE_SPEC.md` | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` | 27,283 bytes / 474 líneas | mtime/ctime `2026-09-30 16:24:01.492921813 -0300`, modo `0664` | No está en el tree de HEAD; el archivo presente está untracked |
| `files/A_PRE_0_BASELINE_SPEC.md` | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` | 67,288 bytes / 1,105 líneas | mtime/ctime `2026-10-01 05:02:43.830596029 -0300`, modo `0664` | Tracked; blob Git en HEAD `d100484bc9abfe37dd47a305b9c03d84247ba80b` |

`docs/` y `files/` **no son byte-identical**. La comparación semántica
confirma diferencias normativas/de estado, además de longitud:

- La copia `docs/` abre con `A-PRE-0: SPECIFIED` y alcance de especificación
  PRE que no ejecuta suites ni cambia código funcional.
- La copia `files/` abre con `A-PRE-0: NOT READY`; su alcance incluye calificar
  mecanismos sintéticos y excluye explícitamente ejecutar TALOS/suites.
- Ambas comparten los títulos generales de identidad, perímetro,
  dependencias/runtime, efectos, registro y comparabilidad, pero el contenido
  no es una mera expansión mecánica.
- `files/` incorpora una sección normativa 4.1 y subapartados sobre el
  predicate exacto de READY, ledger/verificación independiente, cruce
  1:1 de syscalls, ABI/trazabilidad, evidencia reservada a A-PRE-1,
  adjudicaciones históricas y revisión de filas sin candidata. Esos títulos no
  están en `docs/`.
- Por tanto, son **dos revisiones documentalmente distintas**. La extensión
  de `files/` es compatible con una evolución del tema, pero no se encontró
  una declaración versionada que identifique el origen de cada cambio o
  establezca que una sea copia autorizada de la otra.

## 3. Genealogía Git

Se inspeccionaron las historias de ruta en todos los refs locales disponibles,
los árboles en HEAD, las referencias `refs/agents/`, branches y tags. Los
hashes de esta tabla son SHA-256 del contenido del archivo en cada commit,
no los IDs de blob Git.

### 3.1 Linaje `docs/`

| Evento | Commit / fecha | Operación / SHA-256 del contenido |
|---|---|---|
| Primera adición localizada | `ded3ccf20b4b3ab7379e0d709acc5ee8653612df`, 2026-09-30 14:58:31 -03 | Añade `docs/A_PRE_0_BASELINE_SPEC.md`; `2c9c3743f2b4a00b5edb478b9aa6cd36492d700dddcbd9c47c002a00d2a47a45` |
| Revisión | `8e2b0d0bcabc37b83bcb337f8ca23ed39c2fb441`, 15:06:57 | Modifica la misma ruta; `0077e45e652baa433af87c3a43acb2c5d69c09ffb1381a81934eb8849e1ae2cf` |
| Revisión | `364ae7f8a989b8d88f691a55a2429478245eda64`, 15:15:19 | Modifica; `75e03557965d0c99c04fb926a8723ccc8cc06cb2a232cec4173c786e60bd57d8` |
| Revisión | `fa841b23b01083bea50c46a445939c8739bc0cbf`, 15:29:16 | Modifica; `888e71ff157ba15e9af5516bd5ebd28deb3d1fcf0bd8f5f8e7992b0348f7918a` |
| Revisión | `48d99d7a84243db2e4472778943f5197ee872ebd`, 15:33:47 | Modifica; `9fa25a5d791cd6cab4c0fea6a976d83123d3ed5837b961c47d1e4dc064cfdaef` |
| Revisión | `a6ef9e78a34bc162f5cca1c6c418abb3eb457fff`, 16:00:49 | Modifica; `7a9ef6244865fad019e375958d851192e714d262c71542e007b0d955ed92f0b0` |
| Revisión | `5313341584942956bd5358d59cc2155bd8286066`, 16:00:49 | Modifica; `61dd24e44daad245169d872845aaa9c937140e4f549cdf831fa2e91a154300f6` |
| Última modificación de contenido hallada | `a3c8e2dab269d7a98184e36f2a7f6511b4a17ac9`, 16:27:30; parent `b0b0b6a50ed14fda8a0bce9c2c4af2eeada4e70f`, direct child `367ce628a8c5dd25395511431b3dae72a61c1299` | Modifica; introduce el SHA actual `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c`. El child `367ce…` es “turn 26 start” y no cambia esta ruta |
| Capturas/snapshots con el mismo blob | `f961c087272ffa4e7a7e1140fea139eb134a3df4` (09-30 18:05), `ecdb90a7fc72bc4acd83fd0847ed7bb67e0fd8c4` (10-01 04:14), `eb1edc7877100dbf09d5a385063fd9cc7106c9bd` (04:20), `e33c5b521df631b7cb10150378149cb09d791889` (18:04) | El mismo contenido/hash `b458…`; no representan cambios de contenido demostrados |

La ruta inicial y sus revisiones aparecen en snapshots/ref de agentes de la
sesión `d8568ceb-3308-4a66-ab15-29e008e371ed`; el blob `b458…` aparece desde
su turno 25 y en snapshots posteriores. No hay tag de release que establezca
autoridad. El commit `a3c8e2d` no es ancestro de HEAD `f81134f`; en HEAD la ruta
`docs/` no existe. El archivo local `docs/` que sí existe está untracked.
No se encontró en la historia de HEAD una declaración de autoridad que una
ese blob a la identidad del overlay calificado.

### 3.2 Linaje `files/`

| Evento | Commit / fecha | Operación / SHA-256 del contenido |
|---|---|---|
| Copia en snapshot de recuperación | `c29efa7918a5a9ca43f1eb94e7d49d619aa51143`, 2026-10-01 05:03:23 -03; parent `f9460b4323e190b66bfe621c72589a3452ed3461`, direct child `a3de513dab07466ffd8ad0e71a77f4dc7df58c36` | Añade `files/A_PRE_0_BASELINE_SPEC.md`; `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| Persistencia en la línea principal | `fae02256a82160f0538b42b0cbc9b2534f0e44aa`, 05:04:56; parent `b12e34099336760e8fd55455526a580cd479dade`, direct child `9ddeccc00194b29556087b25f7a69ad5767af043` | Añade la misma ruta y bytes junto al ledger de recuperación; el child es “save A-PRE session checkpoint” y no cambia esta ruta; hash de contenido sin cambio |
| Snapshot de sesión posterior | `a8eb6b90bf95d8a551dc2b2a0b308ff090aba644`, 05:09:34 | Misma ruta y mismo hash; no es modificación de contenido |
| Snapshot de checkpoint | `e33c5b521df631b7cb10150378149cb09d791889`, 18:04:40 | Mismo hash; snapshot independiente, sin parent |

`fae0225` es ancestro de HEAD, no tiene tag que determine autoridad y el blob
`files/` se conserva en HEAD sin modificación de contenido posterior. El
commit `c29efa7` pertenece a refs de agentes separados; `fae0225` es el punto
de persistencia del archivo en `main`. No se encontró un commit que registre
un rename de `docs/` a `files/` ni una declaración formal de copia/derivación
entre ambos blobs. El hecho de que `files/` esté tracked en `main` establece
su persistencia en ese repositorio, no que sea la especificación esperada por
el overlay.

### 3.3 Resumen genealógico

| Copia | Primer commit de ruta/contenido | Última modificación de contenido | Path histórico | Branch/tag | Estado de la copia local actual |
|---|---|---|---|---|---|
| `docs/` | `ded3ccf…` añade una revisión anterior; el contenido SHA actual aparece en `a3c8e2d…` | `a3c8e2d…` dentro del linaje de refs de agentes; snapshots posteriores preservan los mismos bytes | `docs/A_PRE_0_BASELINE_SPEC.md` | No es ancestro de HEAD; commits visibles por `refs/agents/`; sin tag relevante | Untracked y ausente del tree HEAD |
| `files/` | `c29efa7…` en snapshot de agente; persistencia en `main` por `fae0225…` | No se halló modificación de contenido después de su adición; los snapshots posteriores conservan `23e…` | `files/A_PRE_0_BASELINE_SPEC.md` | `fae0225…` es ancestro de `main`; sin tag relevante | Tracked en HEAD |

Las dos rutas coexistieron en el snapshot de `a8eb6b9` y en el de
`e33c5b5`, pero con hashes y contenido diferentes. Esa coexistencia descarta
que esos snapshots las trataran como archivos byte-identical; no determina
por sí misma cuál estaba designado como normativa.

## 4. Referencias documentales

Se buscaron paths, los tres hashes, términos “baseline spec”,
“specification”, “normative spec” y “overlay v4” en manifest, ledger,
checkpoints 011–051, índice y documentación del workspace. Las referencias
halladas son:

| Fuente | Ruta/SHA citada | Contexto y afirmación | Qué no demuestra |
|---|---|---|---|
| `files/A_PRE_0_SURFACE_MANIFEST.json` | Ninguna referencia directa localizada a una de las specs o a `f058…` | El manifest contiene filas, contratos y crosswalk; no nombra una baseline spec por path/hash | No adjudica autoridad documental |
| `files/A_PRE_0_QUALIFICATION_LEDGER.json`, `qualification_identity.current_normative_spec` | `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md`; `sha256=f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4` | Identifica el “current normative spec” esperado por la identidad calificada y registra `present_in_qualified_overlay=false`; el ledger también condiciona elegibilidad de evidencia a rebind a un overlay con la spec normativa | No suministra el archivo ni demuestra que el contenido sea igual a cualquiera de las dos copias locales |
| `checkpoints/011-consolidacion-pistas-y-legacy.md` | No path/hash específico | Resume A-PRE-0 y la consolidación documental; no nombra la spec | No decide autoridad |
| `checkpoints/012-punto-de-guardado-luz-verde.md` | `files/A_PRE_0_BASELINE_SPEC.md` | Lista la copia como artefacto actualizado que contiene la consolidación de pistas/filas legacy; prohíbe modificar el overlay v4 | No fija hash ni dice que esa copia sea la normative spec que el overlay esperaba |
| `checkpoints/013-punto-de-guardado-cierre-y-reanudacion.md` | “overlay v4” sin hash/copy path | Define restricciones de no modificar el overlay y describe trabajo documental cerrado | No vincula la copia a la identidad del overlay |
| `checkpoints/014`–`028` | Referencias genéricas a “la especificación A-PRE-0” / overlay, sin hashes de estas copias | Resúmenes de decisiones por superficies y restricciones | No da cadena de identidad de archivo |
| `checkpoints/021-preparacion-lote-05-s05.md` | “especificación A-PRE-0 local”, sin path/hash | Invoca separación S05/S06 | No identifica cuál copia local |
| `checkpoints/029-preparacion-lote-09-s09.md` | `docs/A_PRE_0_BASELINE_SPEC.md` | Cita preflight REVIEW REQUIRED / NOT READY y A-PRE-1 no ejecutado/no autorizado | Referencia de contenido/estado, no atestación de autoridad frente al overlay |
| `checkpoints/030`–`047` | No se halló un SHA que una una copia local a la identidad overlay; los hits de “overlay” son restricciones o estado | Contexto de adjudicación/reconciliación documental | No designa la spec normativa externa |
| `checkpoints/048-reconciliacion-global-s01-s16.md` | `docs/A_PRE_0_BASELINE_SPEC.md`, SHA `b458…` | Hash observado al hacer la reconciliación inicial | Fija la identidad local observada, no el rol canónico |
| `checkpoints/049-arqueologia-delta-contadores-manifest.md` | “Baseline spec”, SHA `b458…` | Registra el hash de la spec usada en esa arqueología | No lo compara con `f058…` ni lo liga al overlay |
| `checkpoints/050-handoff-nuevo-chat.md` y resumen ejecutivo | Paths `docs/` y `files/`, hashes `b458…` y `23e…`; path externo y hash `f058…` | Declara las dos copias distintas y que el hash esperado se registra como ausente del overlay v4 | Es handoff/observación; no resuelve la cadena de identidad |
| `checkpoints/051-reentrada-autoridad-y-crosswalk.md` | Ambos hashes locales y `f058…` | Clasifica `BASELINE_SPEC_AUTHORITY = UNRESOLVED` y detiene la reconciliación | No resuelve por sí mismo el provenance |
| `docs/PLAN_MAESTRO_CIERRE_TALOS.md`, `docs/REALITY_AUDIT_REPORT.md`, `docs/BACKEND_OPERATIONAL_ARCHAEOLOGY.md` | Enlaces relativos `./A_PRE_0_BASELINE_SPEC.md` dentro de `docs/` | Usan la copia de `docs/` como referencia explicativa de identidad/plan/especificación | Enlaces relativos no establecen la versión externa esperada ni revinculan evidencia |
| `files/A_PRE_0_BASELINE_SPEC.md` | Referencias textuales a `rev4-clean` y overlay v4 | Dice que la reconciliación modifica la especificación del checkout fuente y no modifica retroactivamente el overlay v4 | No contiene una declaración de que este mismo blob sea el hash que el overlay espera |
| `checkpoints/index.md` | Ningún hash de spec | Índice cronológico de checkpoints; no hace una designación normativa independiente | No decide autoridad |

El hash `f058…` aparece como valor en el ledger y en los checkpoints 050–052;
el índice no lo contiene. Los hashes locales `b458…` y `23e…` se registran en
048–052 como observaciones de las copias, no como hashes alternativos dentro
del manifest.

## 5. Reconstrucción del hash `f058…`

1. Hash completo: `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4`.
2. Algoritmo: SHA-256, porque el ledger lo almacena en el campo `sha256`; es
   una cadena hexadecimal de 64 caracteres.
3. Artefacto que pretende identificar: el ledger lo asigna a
   `/home/agustin/apre-runner/rev4-clean/docs/A_PRE_0_BASELINE_SPEC.md` bajo
   `qualification_identity.current_normative_spec`.
4. Relación con overlay: el mismo ledger registra el overlay calificado
   `overlay-async-seccomp-v4`, commit
   `2b2083795602f9099db43bb7ee35b0c030bdf51b`, tree
   `d7ae2718c0a969fd1cf8eee0678f0d6f209c59a7`, y
   `present_in_qualified_overlay=false`.
5. Recuperación Git: se enumeraron y se calculó SHA-256 de los nueve blobs
   accesibles por las rutas históricas `docs/A_PRE_0_BASELINE_SPEC.md` y
   `files/A_PRE_0_BASELINE_SPEC.md`. Incluyen las revisiones históricas de
   `docs/`, la copia de `files/` y snapshots de agente. Además se comprobaron
   421 blobs Markdown con rutas bajo `docs/`, `files/` y `checkpoints/` en los
   refs disponibles. Ninguno da `f058…`; los dos hashes actuales tampoco
   coinciden.
6. Hash textual en historia: antes de este checkpoint, la declaración
   primaria está en el ledger; handoff 050 la repite y 051 la registra como
   hash externo no presente en el overlay. No aparece como hash de contenido
   en los checkpoints anteriores ni en el manifest. Este checkpoint vuelve a
   citarlo para documentar la búsqueda.
7. Eliminación/renombre: no se encontró una versión nombrada de estas rutas
   con SHA `f058…` en los objetos Git disponibles, ni un commit de rename que
   conecte la ruta `rev4-clean` con una copia local. Esto no prueba que el
   archivo externo nunca existiera; no se accedió a `rev4-clean` ni al overlay
   por restricción de alcance.

Resultado: **`EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`**. El registro del ledger
es evidencia de qué path/hash se esperaba, no sustituto del contenido ni
prueba independiente de que el archivo externo siga existiendo.

## 6. Timeline documental mínimo

| Evento | Commit/checkpoint | Artefacto / SHA | Operación y evidencia | Efecto sobre autoridad |
|---|---|---|---|---|
| Primera baseline local de este linaje | `ded3ccf…`, 2026-09-30 14:58 | Spec `docs/`, SHA `2c9c…` | Adición inicial de la ruta en historial de agente | Inicio histórico de ese path; no fija autoridad del futuro overlay |
| Revisiones de `docs/` | `8e2b0d0`, `364ae7f`, `fa841b2`, `48d99d7`, `a6ef9e7`, `5313341`, `a3c8e2d` (09-30, 15:06–16:27) | Hashes intermedios en §3.1; último `b458…` | Serie de modificaciones, con el SHA observado actual producido por `a3c8e2d` | Versión final del linaje de agente local; no identidad `f058…` |
| Persistencia de artefactos de recuperación | `c29efa7…` (10-01 05:03), `fae0225…` (05:04) | `files/` SHA `23e…`; ledger SHA actual registrado en el checkout | El archivo ampliado se añade como artefacto de recuperación; `fae0225` lo persiste en la línea principal junto al ledger | Prueba persistencia de esa copia en main, no que sea el objeto del hash esperado |
| Snapshot overlay qualification identity | Ledger del snapshot persistido por `fae0225…`, fecha del ledger `2026-10-01` | Overlay commit/tree arriba; spec esperada `rev4-clean/...`, SHA `f058…`, declarada ausente del overlay | Identidad declarada por el ledger; overlay no inspeccionado en esta tarea | El vínculo declarado apunta a un tercer hash no recuperado |
| Checkpoint de handoff previo | 012–013 | Referencia a `files/` y a overlay v4, sin hash para la relación | Archivos listados como artefactos de recuperación y restricciones de no modificar overlay | No designación inequívoca |
| Adjudicaciones posteriores | 014–047 | Uso documental genérico de la especificación; checkpoint 029 enlaza `docs/` | Se consulta contenido local para alcance/preflight | Referencia de uso; sin rebind al overlay |
| Reconciliaciones | 048–049 | SHA `b458…` para `docs/` | Identidad local observada durante análisis | No iguala ni reemplaza el hash externo |
| Handoff | 050 | Registra `b458…`, `23e…`, `f058…` | Explicita la discrepancia y ausencia declarada | Abre el bloqueo |
| Diagnóstico de provenance | 051 | Las tres identidades; `STOP_REASON=UNRESOLVED_PROVENANCE` | Detiene el crosswalk por falta de autoridad demostrada | Estado de parada al inicio de esta tarea |
| Esta resolución documental | 052 | Los mismos hashes; `f058…` no recuperado | Reconstruye history, refs y hashes sin reparar archivos | Confirma que no hay autoridad local demostrable; conserva la parada |

No se encontró evidencia que convierta las dos copias en réplica exacta,
rename, o bifurcación con relación de autoridad declarada. La copia
`files/` se añadió al repositorio principal como recuperación; la copia
`docs/` actual procede de otro linaje histórico y está untracked en el estado
actual. Ninguno de esos hechos demuestra cuál gobernaba el overlay v4.

## 7. Criterio y decisión de autoridad

La existencia de dos textos distintos con estados y alcance materialmente
diferentes, el path/hash externo declarado por el ledger, la ausencia
registrada de ese artefacto en el overlay y la falta de enlace verificable
entre `f058…` y cualquiera de los blobs locales impiden asignar una autoridad
única.

**`BASELINE_SPEC_AUTHORITY = UNRESOLVED`**
Categoría permitida equivalente: **`AUTHORITY_UNRESOLVED`**.

No se clasifican las copias como `CANONICAL_DOCS_COPY`,
`CANONICAL_FILES_COPY`, `HISTORICAL_COPY`, `DERIVED_COPY` ni
`DUPLICATE_CONFIRMED`: para cada una falta la prueba necesaria de relación
con el snapshot normativo del overlay. No se ha sustituido `f058…` por la
copia con nombre o ruta más cercana.

**`EXTERNAL_SPEC_ARTIFACT = UNRECOVERED`**

**`STOP_REASON = UNRESOLVED_PROVENANCE`**

## 8. Estado final y reanudación

| Estado | Resultado |
|---|---|
| A-PRE-0 | `NOT_READY`; `predicate_result=false` |
| A-PRE-1 | `NOT_AUTHORIZED / NOT_EXECUTED` |
| Inventory | `frozen=false` |
| Disposiciones globales | 385/385 `UNKNOWN` |
| Reconciliación 048 | Continúa bloqueada; no puede reanudarse por este checkpoint |
| Actividad dinámica | Ninguna |

El estado canónico no se modificó. No se modificaron manifest, ledger,
`requirements.lock`, ninguna de las dos specs, ni las disposiciones. No se
accedió al overlay externo ni a `rev4-clean`.

## 9. Integridad final

| Comprobación | Resultado |
|---|---|
| JSON de manifest válido | Sí |
| JSON de ledger válido | Sí |
| Filas / nombres únicos / números únicos | 385 / 385 / 385 |
| Disposiciones globales | 385/385 `UNKNOWN` |
| Manifest SHA inicial = final | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger SHA inicial = final | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` SHA inicial = final | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| `docs/` SHA inicial = final | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| `files/` SHA inicial = final | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| `git diff --check` | Passed |
| Cambios canónicos | 0 |
| Actividad dinámica | Ninguna |
