# Checkpoint 077 — reconciliación efectiva de identidad para Gate B

## 1. Alcance, autoridad de scope y límites

La decisión de producto suministrada por el usuario en la Directiva 077 fija
el denominador de esta evaluación. Se registra como decisión humana explícita,
no como conclusión inferida de la configuración:

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
```

Scopes incluidos:

1. Fase 0 — Programación y Pensamiento Algorítmico.
2. FADENA Lenguajes 2026.
3. FADENA Sistemas Operativos II 2026.
4. FADENA Sistema de Tratamiento de Datos 2026.
5. FADENA Telecomunicaciones 2025.

Este checkpoint realiza cotejo declarativo y lectura limitada, read-only, de
las cinco identidades y sus source IDs/asociaciones persistidas. No evalúa el
contenido del corpus ni determina si los shared sources son apropiados.
`fadena-std` se incluye para identidad técnica; su autoridad curricular sigue
siendo una cuestión separada de Gate B criterio 5.

Se usaron:

- `checkpoints/075-evaluacion-gate-b-evidencia-existente.md`.
- `checkpoints/076-scope-release-gate-b.md`, como corte histórico anterior a
  la decisión humana explícita de este turno.
- `checkpoints/074-criterios-objetivos-product-complete.md`.
- `docs/PLAN_MAESTRO_CIERRE_TALOS.md`.
- `docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`.
- `config/notebook_kc_catalog.json` (key, nombre de catálogo y
  `curriculum_id`).
- `config/notebook_source_roles.json` (source IDs y roles declarados).
- `config/notebook_identity_decisions.json` (clasificación audit-only y
  `alias_target`).
- `src/study_engine/federation/notebook_registry.py` (`DEFAULT_NOTEBOOKS`,
  declaración estática del registry).
- `src/study_engine/pedagogy/fase0_seed.py` (`NOTEBOOK_PROFILES`).
- `src/study_engine/web/dependencies.py`, que fija
  `repo_root/data/web_state` como working directory predeterminado del store.
- `data/web_state/knowledge_store.db`, leído con SQLite URI `mode=ro` y
  `PRAGMA query_only = ON`; se seleccionaron sólo las cinco filas de
  `notebooks`, sus asociaciones en `notebook_sources` y existencia por ID de
  los source records relacionados.

`DEFAULT_NOTEBOOKS` se examinó estáticamente. No se inició la aplicación y no
se inspeccionó ningún registry en memoria de un proceso activo; tal estado
runtime queda desconocido. La base consultada es la base persistida del
working directory predeterminado, no una afirmación sobre todos los posibles
despliegues.

No se ejecutaron TALOS/FastAPI, tests, providers ni benchmarks. No se
modificaron registros, ACL, código, configuración ni corpus. Las listas y
deltas reportados describen identidades/source IDs, no autorizan cambios.

## 2. Convenciones para identidad y alias

- `registry estático` = fila correspondiente en `DEFAULT_NOTEBOOKS`; este
  modelo no tiene campo `curriculum_id`.
- `persistido` = fila de `notebooks` en `data/web_state/knowledge_store.db`.
- `catálogo` = fila con la key exacta del notebook en
  `config/notebook_kc_catalog.json`.
- `perfil` = entrada exacta de `NOTEBOOK_PROFILES`.
- `alias_target: null` significa que esa decisión audit-only no declara un
  destino de alias; por sí solo no demuestra que nunca haya existido otro
  alias histórico.
- Para los cinco IDs seleccionados, no se encontró alias autorizado que
  sustituya la identidad exacta. Una etiqueta o similitud nominal no se
  convierte en alias.

Relaciones explícitamente rechazadas o delimitadas por las decisiones
audit-only:

- `fase0-soc` no es un alias FADENA.
- `fadena-so2` es distinto de `fadena-so`; no redirigir uno al otro.
- `fadena-prog` y `fadena-so` se identifican como scopes legacy distintos,
  no como aliases de los perfiles release. El registry estático conserva la
  frase histórica “Legacy Alias” en sus nombres, pero la decisión
  `notebook_identity_decisions.json` dice preservar esos scopes y no declara
  `alias_target`; ese texto no se interpreta como autorización de alias para
  los cinco incluidos.
- Para Lenguajes, STD y Telecomunicaciones, `alias_target: null` y las
  decisiones de identidad mantienen el ID exacto; no se halló una lista
  positiva de aliases autorizados.

## 3. Resultado de identidad por scope

En todas las filas siguientes el ID de catálogo, el ID del registry estático,
el ID del perfil y el ID persistido coinciden exactamente. En las cinco,
sin embargo, el `curriculum_id` persistido es `fadena_v1`, mientras que el
catálogo y el perfil declaran un ID distinto. El registry estático no
representa `curriculum_id`, por lo que no puede cerrar ese desacuerdo.

| Scope / release name | canonical_id / notebook_id | `curriculum_id` esperado (catálogo / perfil) | Alias / `alias_status` | Identidad catálogo | Identidad registry estático | Identidad persistida | Consistencia / clasificación |
|---|---|---|---|---|---|---|---|
| SCOPE-01 — Fase 0 — Programación y Pensamiento Algorítmico | `fase0-soc` | `roadmap_kasiu_v4_fase0` | `alias_target: null`; sin alias autorizado declarado. La decisión especifica que no es alias FADENA. | Key `fase0-soc`; nombre `Fase 0 - Fundamentos de Programación y Ciberdefensa`; ID esperado. | `fase0-soc`; nombre `Roadmap KASIU TECH v4 - Fase 0`; subject `Programación y Pensamiento Algorítmico`; sin campo `curriculum_id`. | ID, nombre y subject coinciden con registry estático; `curriculum_id = fadena_v1`, no coincide. | ID/name/subject alineados; discrepancia material del ID curricular persistido. `FAIL` → `IDENTITY_DISCREPANCY`. |
| SCOPE-02 — FADENA Lenguajes 2026 | `fadena-lenguajes` | `fadena_lenguajes_2026` | `alias_target: null`; no se declara alias autorizado; conservar ID exacto. | Key `fadena-lenguajes`; nombre `Lenguajes de Programación - FADENA 2026`; ID esperado. | Mismo ID y nombre; subject `Lenguajes de Programación`; sin campo `curriculum_id`. | Mismo ID, nombre y subject; `curriculum_id = fadena_v1`, no coincide. | ID/name/subject alineados; discrepancia material del ID curricular persistido. `FAIL` → `IDENTITY_DISCREPANCY`. |
| SCOPE-03 — FADENA Sistemas Operativos II 2026 | `fadena-so2` | `fadena_so2_2026` | `alias_target: null`; sin alias autorizado; la decisión distingue este ID de `fadena-so`. | Key `fadena-so2`; nombre `Sistemas Operativos II - FADENA 2026`; ID esperado. | Mismo ID y nombre; subject `Sistemas Operativos`; sin campo `curriculum_id`. | Mismo ID/nombre; subject `Sistemas Operativos`; `curriculum_id = fadena_v1`, no coincide con el esperado. | Discrepancia del ID curricular y variación de subject frente al perfil (`Sistemas Operativos II`). No se decide si es abreviación legítima. `FAIL` → `IDENTITY_DISCREPANCY`. |
| SCOPE-04 — FADENA Sistema de Tratamiento de Datos 2026 | `fadena-std` | `fadena_std_2026` | `alias_target: null`; sin alias autorizado declarado; se conserva el ID exacto. | Key `fadena-std`; nombre `Sistema de Tratamiento de Datos - FADENA 2026`; ID esperado. | Mismo ID y nombre; subject `Tratamiento de Datos y Bases de Datos`; sin campo `curriculum_id`. | Mismo ID/nombre y subject que registry; `curriculum_id = fadena_v1`, no coincide. | Discrepancia del ID curricular y variación de subject frente al perfil (`Sistema de Tratamiento de Datos`). `FAIL` → `IDENTITY_DISCREPANCY`. **La autoridad académica sigue pendiente** y no se decide aquí. |
| SCOPE-05 — FADENA Telecomunicaciones 2025 | `fadena-teleco` | `fadena_teleco_2025` | `alias_target: null`; sin alias autorizado declarado; conservar ID exacto. | Key `fadena-teleco`; nombre `Infraestructura de Telecomunicaciones - FADENA 2025`; ID esperado. | Mismo ID y nombre; subject `Telecomunicaciones y Redes`; sin campo `curriculum_id`. | Mismo ID/nombre y subject que registry; `curriculum_id = fadena_v1`, no coincide. | Discrepancia del ID curricular y variación de subject frente al perfil (`Infraestructura de Telecomunicaciones`). `FAIL` → `IDENTITY_DISCREPANCY`. |

Fuentes de la tabla: entradas de `config/notebook_kc_catalog.json`,
`config/notebook_identity_decisions.json`,
`src/study_engine/federation/notebook_registry.py`,
`src/study_engine/pedagogy/fase0_seed.py`, y las cinco filas persistidas de
`data/web_state/knowledge_store.db`. Los nombres del catálogo no siempre son
un campo `subject`; no se los equipara automáticamente con subject.

### Síntesis por campo

```text
IDs notebook (catálogo ↔ registry estático ↔ perfil ↔ persistido): 5/5 exactos
curriculum_id (catálogo ↔ perfil): 5/5 exactos
curriculum_id (persistido ↔ catálogo/perfil): 0/5 exactos
registry estático con curriculum_id: 0/5 (campo no representado)
alias positivo autorizado para los cinco: ninguno documentado
aliases sin destino declarado: 5/5 (`alias_target: null`)
estado runtime del registry en memoria: UNKNOWN (no se inició runtime)
```

El valor persistido `fadena_v1` aparece en las cinco filas aun cuando el
catálogo/perfil asigna cinco identidades curriculares específicas. Se registra
como contradicción efectiva; no se infiere que sea sólo un marcador legacy ni
se corrige en este checkpoint.

## 4. Source roles, registry y asociaciones persistidas

El registry estático trae listas `sources`; `notebook_source_roles.json`
declara roles por source ID; SQLite materializa asociaciones
`notebook_sources`. Los conteos y diferencias abajo son exactos para las tres
representaciones inspeccionadas. “Sin rol” o “sin asociación” es una
discrepancia de representación, no una decisión automática de borrar,
añadir o autorizar una fuente.

| Scope | Sources en registry estático | Sources con roles declarados | Asociaciones persistidas | Deltas observados |
|---|---:|---:|---:|---|
| SCOPE-01 `fase0-soc` | 14 | 9 | 26 | Registry sin rol: `src_0fc90b2695369475`, `src_d253687930308e41`, `src_fadena_so_concurrencia`, `src_fadena_so_memoria`, `src_fadena_so_planificacion`, `src_fadena_so_procesos`. Rol sin registry ni asociación: `src_tori_hacking_etico`. Asociaciones sin rol: 18 (lista completa en §4.1). Registry sin asociación: ninguna. |
| SCOPE-02 `fadena-lenguajes` | 10 | 15 | 17 | Roles que no aparecen en registry: `src_1149ca3399b6dd85`, `src_115f0bc876b44be8`, `src_7ba98d836c32fe4b`, `src_8ac0eed0a6121c6a`, `src_fdc4df20e0f9f99e`; los cinco sí están asociados en DB. Asociaciones sin rol: `src_fadena_prog_arboles`, `src_fadena_prog_archivos`. Registry sin asociación: ninguna. |
| SCOPE-03 `fadena-so2` | 8 | 16 | 14 | Roles que no aparecen en registry: `src_0fc90b2695369475`, `src_a9a056742dcf69ae`, `src_d253687930308e41`, `src_e9682dece40b58ab`, `src_f009c4e75f5ca3f2`, `src_rudareanu_linux_sysadmins`, `src_silberschatz_so_7ed`, `src_tanenbaum_so_modernos_3ed`; los tres últimos no están asociados y no existen como source records en esta DB. La asociación `src_0bc5d20dcc91895f` no tiene rol ni está en la lista del registry. Las otras cinco asociaciones adicionales frente al registry sí aparecen en roles. |
| SCOPE-04 `fadena-std` | 9 | 29 | 30 | Veinte fuentes con rol no aparecen en registry. `src_cairo_guardati_estructuras_datos` tiene rol pero no asociación y no tiene source record. Dos asociaciones no tienen rol: `src_f3352475bc0cd360` y `src_rosen_matematicas_discretas`. Registry sin asociación: ninguna. |
| SCOPE-05 `fadena-teleco` | 8 | 13 | 12 | Roles que no aparecen en registry: `src_001b27137cf6680c`, `src_11195af8e0f2ef40`, `src_2f1a5843cd1693ba`, `src_da10b53f20f2a647`, `src_tanenbaum_computer_networks`; los primeros cuatro están asociados, Tanenbaum no está asociado y no tiene source record. Registry sin asociación: ninguna. |

La verificación de existencia de source records se hizo por ID solamente, sin
leer títulos, documentos ni chunks. Entre los IDs examinados, los faltantes
son exactamente:

- SCOPE-03: `src_rudareanu_linux_sysadmins`,
  `src_silberschatz_so_7ed`, `src_tanenbaum_so_modernos_3ed`.
- SCOPE-04: `src_cairo_guardati_estructuras_datos`.
- SCOPE-05: `src_tanenbaum_computer_networks`.

### 4.1 Asociaciones persistidas de SCOPE-01 sin rol declarado

```text
src-guia-2025-c04f44ef
src_0bc5d20dcc91895f
src_0fc90b2695369475
src_a9a056742dcf69ae
src_d253687930308e41
src_e9682dece40b58ab
src_f009c4e75f5ca3f2
src_fadena_prog_arboles
src_fadena_prog_archivos
src_fadena_prog_lineales
src_fadena_so_concurrencia
src_fadena_so_memoria
src_fadena_so_planificacion
src_fadena_so_procesos
src_kurose_computer_networking
src_ramalho_fluent_python
src_stallings_computer_security
src_stallings_os_internals_7ed
```

El conteo coincide: 18 asociaciones sin rol declarado. De las nueve fuentes
con roles, ocho aparecen asociadas y `src_tori_hacking_etico` no aparece en
las asociaciones persistidas.

## 5. Asociaciones compartidas entre los cinco scopes

La consulta read-only encontró source IDs asociados explícitamente a más de
un notebook dentro del release. La lista completa observada es:

| Source ID | Scopes persistidos |
|---|---|
| `src-guia-2025-c04f44ef` | `fase0-soc`, `fadena-teleco` |
| `src_0bc5d20dcc91895f` | `fase0-soc`, `fadena-so2` |
| `src_0fc90b2695369475` | `fase0-soc`, `fadena-so2` |
| `src_a9a056742dcf69ae` | `fase0-soc`, `fadena-so2` |
| `src_d253687930308e41` | `fase0-soc`, `fadena-so2` |
| `src_e9682dece40b58ab` | `fase0-soc`, `fadena-so2` |
| `src_f009c4e75f5ca3f2` | `fase0-soc`, `fadena-so2` |
| `src_fadena_prog_arboles` | `fase0-soc`, `fadena-lenguajes` |
| `src_fadena_prog_archivos` | `fase0-soc`, `fadena-lenguajes`, `fadena-std` |
| `src_fadena_prog_lineales` | `fase0-soc`, `fadena-lenguajes` |
| `src_fadena_prog_punteros` | `fase0-soc`, `fadena-lenguajes` |
| `src_fadena_so_concurrencia` | `fase0-soc`, `fadena-so2` |
| `src_fadena_so_memoria` | `fase0-soc`, `fadena-so2` |
| `src_fadena_so_planificacion` | `fase0-soc`, `fadena-so2` |
| `src_fadena_so_procesos` | `fase0-soc`, `fadena-so2` |
| `src_joyanes_fundamentos` | `fase0-soc`, `fadena-lenguajes` |
| `src_kurose_computer_networking` | `fase0-soc`, `fadena-teleco` |
| `src_ramalho_fluent_python` | `fase0-soc`, `fadena-std` |
| `src_rosen_matematicas_discretas` | `fase0-soc`, `fadena-std` |
| `src_spraul_think_like_a_programmer` | `fase0-soc`, `fadena-lenguajes` |
| `src_stallings_computer_security` | `fase0-soc`, `fadena-so2`, `fadena-teleco` |
| `src_stallings_os_internals_7ed` | `fase0-soc`, `fadena-so2` |
| `src_sweigart_automate_boring_stuff` | `fase0-soc`, `fadena-lenguajes` |

La asociación compartida prueba sólo que la relación está materializada en
SQLite para esos IDs. No prueba que la compartición sea curricularmente
correcta o incorrecta ni que un source ID esté autorizado por un rol
apropiado. Esa adjudicación queda para criterios 2–4 y no se hace aquí.

## 6. Resultado y estado del criterio 1

```text
SCOPE-01 fase0-soc       = IDENTITY_DISCREPANCY
SCOPE-02 fadena-lenguajes = IDENTITY_DISCREPANCY
SCOPE-03 fadena-so2       = IDENTITY_DISCREPANCY
SCOPE-04 fadena-std       = IDENTITY_DISCREPANCY
SCOPE-05 fadena-teleco    = IDENTITY_DISCREPANCY

CRITERION_1 = BLOCKED
GATE_B_IDENTITY_STATUS = BLOCKED
```

La decisión de scope está cerrada, pero la identidad efectiva no está
reconciliada: las cinco filas persistidas tienen el mismo `curriculum_id`
genérico `fadena_v1` en lugar de los IDs específicos del catálogo/perfil; hay
además variaciones de subject y discrepancias entre registry, roles y
asociaciones. No se declara que sean datos obsoletos ni se corrigen. El estado
`BLOCKED` expresa que faltan adjudicación/provenance y una reconciliación
aprobada; no es una conclusión sobre cuál representación debe prevalecer.

Para que el criterio 1 pueda pasar se requiere, fuera de esta tarea:

1. determinar con evidencia/decisión la semántica de `fadena_v1` en las cinco
   filas y resolver la concordancia de `curriculum_id` sin asumir que el
   catálogo, registry o DB prevalece automáticamente;
2. adjudicar las variaciones de `subject` en SO2, STD y Telecomunicaciones
   frente a los perfiles, preservando nombres de curso y etiquetas si son
   conceptos distintos;
3. cerrar el inventario de aliases con designaciones explícitas y conservar
   las no-equivalencias de Fase 0/FADENA y SO2/`fadena-so`;
4. reconciliar listas del registry, roles y asociaciones persistidas, incluido
   cada source ID con o sin source record, sin cambiar ACL hasta decisión
   autorizada;
5. resolver la discrepancia de conteo/listado señalada en §4.1 a partir de la
   consulta estructurada, antes de usar esa enumeración como sumando;
6. registrar versión/snapshot del registry de despliegue si la aceptación
   requiere comprobarlo en lugar de la declaración `DEFAULT_NOTEBOOKS`.

## 7. Evidencia adicional que falta para criterios 2–5

Esta reconciliación prepara, pero no cierra, el resto de Gate B:

- **Criterio 2 — roles y ACL efectiva:** hace falta adjudicar las diferencias
  entre `notebook_source_roles.json`, source IDs del registry, asociaciones
  persistidas y existencia de source records; justificar cada source
  compartido y verificar que el allowlist efectivo refleje las decisiones.
  No se deben añadir/quitar asociaciones por similitud de nombre.
- **Criterio 3 — selección de perfil por identidad:** hace falta resolver el
  `curriculum_id` persistido discrepante y las variaciones de `subject`, y
  luego producir evidencia integrada de que cada identidad explícita del
  release selecciona el perfil correcto y una identidad desconocida usa
  fallback neutral. Los tests existentes no reparan el estado persistido.
- **Criterio 4 — ausencia de contaminación:** hace falta una matriz positiva y
  negativa por los cinco scopes, con los source-sharing cases adjudicados y
  observación del prompt/contexto por scope. La existencia de una asociación
  compartida no se interpreta como contaminación sin probar su ruta.
- **Criterio 5 — autoridad de `fadena-std`:** como
  `FADENA_STD_RELEASE_SCOPE = INCLUDED`, sigue pendiente una fuente curricular
  autorizada que respalde el programa detallado y su vínculo con la identidad
  y fuentes. La reconciliación técnica de `fadena_std_2026` no demuestra
  autoridad académica.

No se construye todavía la matriz completa de contaminación, no se ejecutan
las pruebas pendientes y no se declara Gate B cerrado.

## 8. Invariantes y no-acciones

- La decisión humana del scope se registra: cinco currículos; `fadena-std`
  incluido.
- No se modificaron código, configuración, DB, source associations, ACL,
  registry, corpus, modelos, fixtures ni gates.
- La DB se consultó por URI `mode=ro` con `PRAGMA query_only = ON`.
- No se ejecutó TALOS/FastAPI, tests, providers ni benchmarks.
- No se reabrió CP072 ni se cambió A-PRE.
- No se declaró autoridad curricular para `fadena-std`, Gate B cerrado ni
  `PRODUCT_COMPLETE`.
- Los cambios preexistentes del worktree se preservaron.

## Estado final

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED
GATE_B_IDENTITY_STATUS = BLOCKED
```
