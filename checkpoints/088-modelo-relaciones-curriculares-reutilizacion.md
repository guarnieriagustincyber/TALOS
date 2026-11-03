# CP088 — modelo de relaciones curriculares, reutilización y prioridad

## 1. Propósito y límites de esta definición

Este checkpoint define el lenguaje documental para distinguir la identidad
física/global de un PDF de las relaciones pedagógicas que pueden vincularlo a
distintos scopes. Reinterpreta conceptualmente, pero no adjudica como
correctas/incorrectas, las mismas 99 relaciones inventariadas en CP084–087.

La clasificación `relationship_candidate` es deliberadamente provisional:
describe qué lectura conceptual permite la evidencia estructural, no una
decisión curricular ni un permiso. `PRIMARY`, `COMPLEMENTARY` y `AUXILIARY`
solo se convierten en relaciones aprobadas mediante una decisión posterior
explícita. `UNRESOLVED` significa que no puede elegirse entre ellas sin
inventar propósito, origen o prioridad.

No se modificaron datos ni configuración. En particular, CP088 no cambia ACL,
`notebook_sources`, roles, curriculum IDs ni CP084–087; no emite grants y deja
C2 bloqueado.

## 2. Modelo normativo de entidad y relación

```text
DOCUMENT
  └── DOCUMENT_IDENTITY = GLOBAL
        ├── SHA-256 de bytes (identidad de esa versión física)
        └── source_id (identificador local del registro correspondiente)

SCOPE (notebook + fase cuando aplique)
  └── CURRICULAR_RELATION
        ├── type: PRIMARY | COMPLEMENTARY | AUXILIARY
        ├── purpose: explícito
        ├── priority: explícita y propia de esta relación
        └── provenance / decision: explícita y trazable
```

Se establece:

```text
DOCUMENT_IDENTITY = GLOBAL
PHYSICAL_DUPLICATION_POLICY = FORBIDDEN
REUSE_OF_EXISTING_DOCUMENT = ALLOWED
DOCUMENT != CURRICULAR_RELATION
```

Para una copia PDF disponible, SHA-256 completo identifica los bytes
observados. `source_id` apunta a la identidad global que el registro local
asocia a esos bytes, pero no reemplaza hash de versión, evidencia de origen ni
provenance editorial. Si hay más de un hash bajo un mismo concepto/título,
son artefactos/versiones diferentes hasta que una fuente fiable demuestre otra
cosa. En CP087 los 76 paths produjeron 74 hashes; los mapeos por hash a
`source_id` quedaron resueltos. Dos duplicaciones físicas exactas son
observables:

- Kurose tiene el mismo SHA-256 en `fuentes/fase0-soc/` y
  `fuentes/fadena-teleco/`.
- `UNIDAD1.pdf` y `UNIDAD1STD.pdf` tienen el mismo SHA-256 y
  `source_id` en `fuentes/fadena-std/`.

Estas copias existentes son hechos del checkout, no una recomendación. La
política de no duplicación significa que múltiples usos deben referenciar un
documento global compartido mediante relaciones lógicas; no se duplican bytes
para crear una relación. CP088 no elimina ni fusiona las dos copias
observadas.

Una relación curricular no muda la identidad ni el “hogar físico” de un
documento. Un mismo documento global puede tener, por ejemplo, una relación
PRIMARY con Telecomunicaciones, COMPLEMENTARY con SOC Fase 0 y ninguna
relación con SOC Fase 3. Son vínculos distintos con propósitos y provenance
propios.

## 3. Semántica de las relaciones

| Categoría | Semántica que se adopta | Evidencia mínima para proponerla | No significa |
|---|---|---|---|
| `PRIMARY` / curricular nativa | Documento perteneciente al corpus propio del scope y que ocupa una función prioritaria en el trayecto. Para FADENA, la carpeta curricular propia más identidad exacta del PDF es evidencia de hogar/intención nativa. | Path bajo la carpeta propia con SHA→`source_id` exacto; evidencia/decisión de función curricular primaria para ese scope. | La carpeta sola no demuestra bibliografía oficial, autoridad externa, prioridad numérica ni L3. |
| `COMPLEMENTARY` | Documento cuyo hogar curricular original es otro scope, pero una decisión explícita permite usarlo para complementar el aprendizaje en el scope destino. No cambia su hogar ni lo vuelve nativo del destino. | Hogar/origen distinto y decisión específica de reutilización con scope y propósito. La configuración técnica por sí sola no completa la decisión. | No es un alias, herencia automática, inclusión primaria ni autorización L3 implícita. |
| `AUXILIARY` | Material de apoyo para ampliar, aclarar o contextualizar, fuera del material prioritario y sin constituir corpus primario. | Propósito auxiliar explícito, relación destino identificada y prioridad relativa documentada. | No puede asignarse automáticamente a cualquier recurso sin una decisión de propósito. |
| `NONE` | No se ha establecido una relación curricular para el par documento/scope. | Decisión explícita de que no existe relación, o ausencia de relación técnica en un análisis de inventario. | La ausencia de una fila no es rechazo, revocación ni orden para modificar ACL. |
| `UNRESOLVED` | Evidencia insuficiente o representaciones que no permiten asignar una de las categorías anteriores sin inferencia. | Campos de origen, función, propósito o semántica de role incompletos/discordantes. | No es una decisión negativa. |

Los vocabularios `PRIMARY`, `COMPLEMENTARY`, `IMPLEMENTATION`,
`METHODOLOGICAL`, `REFERENCE` y `FORMAL` presentes en U no se traducen todos
automáticamente a las cuatro categorías anteriores. Solo `PRIMARY` y
`COMPLEMENTARY` son homónimos directos del modelo, y aun así siguen siendo
declaraciones de role, no grants ni adjudicaciones finales. Otros roles quedan
`UNRESOLVED` hasta que una definición/aprobación documental establezca su
equivalencia. Si la carpeta local contradice un role explícito
`COMPLEMENTARY`, el candidato se mantiene `UNRESOLVED`; no se decide si el
documento es nativo o reutilizado.

En la matriz, `relationship_candidate = PRIMARY` es una **hipótesis
estructural** de material nativo: exige soporte de carpeta con identidad exacta
y un role `PRIMARY` o ninguno contradictorio. No afirma que ya se haya probado
la función pedagógica prioritaria requerida por la definición completa de
`PRIMARY`. Esa función y su prioridad siguen sujetas a decisión/evidencia
posterior; por eso todas las filas conservan `priority_candidate =
NOT_ESTABLISHED`. La matriz no adjudica ninguna relación como aprobada.

## 4. Regla estructural para FADENA

Cada notebook/facultad FADENA mantiene su corpus curricular estricto:

```text
FADENA_NOTEBOOK
  = documentos con hogar físico en su carpeta curricular
    + relaciones de reutilización explícitas y permitidas,
      claramente separadas del corpus nativo
```

Un PDF en `fuentes/fadena-std/` con identidad exacta sustenta
`NATIVE_FOLDER_SUPPORT` para el notebook STD; no concede L3, no determina
autoridad académica y no elimina C4-DRAFT. Un PDF que solo está bajo otra
carpeta no pasa por defecto al corpus primario del notebook FADENA destino.
Una asociación existente en `notebook_sources` tampoco constituye pertenencia
curricular ni permiso.

Si la institución permite reutilizar un documento de otra materia FADENA, la
relación destino debe quedar marcada explícitamente como reutilización
complementaria o auxiliar y conservarse separada del material nativo. No se
cambia el scope de origen ni se heredan sus asociaciones.

## 5. Modelo especial de SOC-Roadmap por fases

SOC-Roadmap no es una única carpeta/cuaderno equivalente a una facultad
FADENA:

```text
SOC-Roadmap
  ├── Fase 0
  ├── Fase 1
  ├── Fase 2
  ├── Fase 3
  └── ...
```

Cada fase puede tener relaciones PRIMARY, COMPLEMENTARY y AUXILIARY,
independientes de las de otras fases. La relación conceptual tiene clave
`(document identity, SOC phase/scope)`, no solo `source_id` global. Un
documento del home físico `fuentes/fadena-so2/` no se convierte
automáticamente en PRIMARY para SOC Fase 0. La existencia de un material
FADENA en la carpeta `fuentes/fase0-soc/` indica ubicación/intención física en
este checkout, no que sea curricularmente nativo de la institución FADENA.

Los nombres de los archivos phase-like `so_*.pdf` y las relaciones actuales
no bastan para decidir a qué fase posterior pertenecen. CP088 no crea relaciones
para SOC Fase 1–N.

## 6. Prioridad pedagógica

La prioridad es una propiedad de la relación, nunca del documento global:

```text
priority = f(document, scope, phase, purpose)
```

No se establece en este corte una escala numérica normativa ni se deduce una
prioridad a partir del orden de archivos, orden de source IDs, catálogo de
roles, `authority` global, página/secuencia, ubicación de carpeta o presencia
en ACL. Cuando no hay decisión ordenada que especifique el nivel:

```text
priority_candidate = NOT_ESTABLISHED
```

El ejemplo conceptual Kurose/Telecom/SOC expresa categorías posibles, no fija
que exista un `priority=2` persistido para Fase 0. No se reescribe metadata
global del PDF para atender una relación particular.

## 7. Reutilización, deduplicación y no herencia

```text
RELATION(A → B)       NO IMPLICA RELATION(A → C)
SOURCE EXISTS         NO IMPLICA CURRICULAR MEMBERSHIP
notebook_sources      NO IMPLICA CURRICULAR AUTHORIZATION
same source_id        NO IMPLICA same pedagogical purpose
```

Una relación por scope requiere su propia función, propósito y provenance. Un
source ID compartido no hereda ni propaga roles, prioridad o grant. Cuando el
mismo SHA/documento se necesita en dos trayectorias, se mantiene una identidad
física global y se documentan relaciones separadas; no se copian los bytes
para fingir propiedad local.

Para el ejemplo de Kurose, se observa el mismo hash en las carpetas Fase 0 y
Telecomunicaciones. La relación de Telecomunicaciones es nativa por carpeta.
La relación de Fase 0 se etiqueta en la matriz como `COMPLEMENTARY` candidato
por ser el ejemplo explícito de reutilización del modelo solicitado; el hecho
de que su PDF también aparezca en la carpeta de Fase 0 revela una duplicación
física que contradice la política objetivo de no duplicación, pero no cambia
la clasificación pedagógica candidata ni concede autorización.

## 8. Método de reinterpretación y leyenda de la matriz

Universo fijo extraído de CP084 y cotejado con CP087:

```text
fase0-soc         26
fadena-lenguajes  17
fadena-so2        14
fadena-std        30
fadena-teleco     12
TOTAL             99
```

Campos de la matriz:

- `physical_pdf_present`: copia con hash exacto observada dentro del home
  físico esperado para ese notebook, según CP087.
- `physical_home_scope`: carpeta(s) donde se encontró el hash; cuando la
  relación no tiene soporte local se nombra la carpeta real. `UNRESOLVED`
  significa sin match local, no “PDF no existe”.
- `declared_role`: etiqueta CP084 literal; `—` significa sin U role declarado.
- `relationship_candidate`: hipótesis conceptual/no autorizante según §3–7.
  `PRIMARY` registra soporte nativo estructural, no demuestra por sí solo
  función pedagógica prioritaria ni satisface la definición completa de
  `PRIMARY`; requiere soporte de carpeta propia y etiqueta `PRIMARY` o ningún
  role contradictorio. La fila Fase 0/Kurose sigue el ejemplo explícito de
  reutilización y es `COMPLEMENTARY`. Los demás roles que no pueden traducirse
  sin una regla aprobada, y las relaciones sin PDF local, quedan `UNRESOLVED`.
  Ninguna fila se asigna `AUXILIARY` o `NONE`: no hay decisión explícita de
  propósito auxiliar/no-relación y todas las filas del universo son
  relaciones técnicas actuales.
- `priority_candidate`: `NOT_ESTABLISHED` en todas las filas; no hay valor
  numérico local de prioridad relacional reconciliado.
- `CROSS_SCOPE_STATUS`: `NATIVE_FOLDER_SUPPORT` cuando el hash sí está en la
  carpeta destino; `NO_NATIVE_SUPPORT` si no está. Este estado solo describe
  ubicación. `NO_NATIVE_SUPPORT` no es un error, una denegación ni una
  clasificación pedagógica `NONE`.

R/U/P de CP084 se citan solo como evidencia ya existente de declaración/estado
técnico. No se reconstruyen ni cambian. Para rutas y hashes completos, véase
el inventario CP087 §3–4; el path del home en CP087 identifica el
`physical_home_scope` que se repite aquí.

## 9. Matriz conceptual completa de las 99 relaciones

### SCOPE-01 — `fase0-soc` (26)

| notebook_id | source_id | physical_pdf_present | physical_home_scope | declared_role | relationship_candidate | priority_candidate | CROSS_SCOPE_STATUS |
|---|---|---:|---|---|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_0bc5d20dcc91895f` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_0fc90b2695369475` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_a9a056742dcf69ae` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | YES | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_d253687930308e41` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_e9682dece40b58ab` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_fadena_prog_arboles` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_prog_archivos` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_prog_lineales` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_prog_punteros` | YES | `fase0-soc` | IMPLEMENTATION, REFERENCE | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_so_concurrencia` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_so_memoria` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_so_planificacion` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_fadena_so_procesos` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_goodrich_dsa_python` | YES | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_joyanes_fundamentos` | YES | `fase0-soc` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_kurose_computer_networking` | YES | `fase0-soc`, `fadena-teleco` | — | COMPLEMENTARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_martin_clean_code` | YES | `fase0-soc` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_ramalho_fluent_python` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_rosen_matematicas_discretas` | YES | `fase0-soc` | FORMAL | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | YES | `fase0-soc` | METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_stallings_computer_security` | YES | `fase0-soc` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fase0-soc` | `src_stallings_os_internals_7ed` | NO | `fadena-so2` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | YES | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |

### SCOPE-02 — `fadena-lenguajes` (17)

| notebook_id | source_id | physical_pdf_present | physical_home_scope | declared_role | relationship_candidate | priority_candidate | CROSS_SCOPE_STATUS |
|---|---|---:|---|---|---|---|---|
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | YES | `fadena-lenguajes` | REFERENCE | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | NO | `fase0-soc` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | NO | `fase0-soc` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | NO | `fase0-soc` | PRIMARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | NO | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | YES | `fadena-lenguajes` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | NO | `fase0-soc` | PRIMARY, METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | YES | `fadena-lenguajes` | METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | NO | `fase0-soc` | METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | YES | `fadena-lenguajes` | REFERENCE | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | NO | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | YES | `fadena-lenguajes` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |

### SCOPE-03 — `fadena-so2` (14)

| notebook_id | source_id | physical_pdf_present | physical_home_scope | declared_role | relationship_candidate | priority_candidate | CROSS_SCOPE_STATUS |
|---|---|---:|---|---|---|---|---|
| `fadena-so2` | `src_0bc5d20dcc91895f` | YES | `fadena-so2` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_0fc90b2695369475` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_a9a056742dcf69ae` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_d253687930308e41` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_e9682dece40b58ab` | YES | `fadena-so2` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | YES | `fadena-so2` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_fadena_so2_clase1` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_fadena_so2_clase2` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-so2` | `src_fadena_so_concurrencia` | NO | `fase0-soc` | PRIMARY, METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_memoria` | NO | `fase0-soc` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_planificacion` | NO | `fase0-soc` | PRIMARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_procesos` | NO | `fase0-soc` | PRIMARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_stallings_computer_security` | NO | `fase0-soc` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_stallings_os_internals_7ed` | YES | `fadena-so2` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |

### SCOPE-04 — `fadena-std` (30)

| notebook_id | source_id | physical_pdf_present | physical_home_scope | declared_role | relationship_candidate | priority_candidate | CROSS_SCOPE_STATUS |
|---|---|---:|---|---|---|---|---|
| `fadena-std` | `src_032c52bff94a0743` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_0960283d5cef8dee` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_3102eb1e89e2229e` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_3e2e8abda5f55c17` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_52ff5ff3e07c1da5` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_53ef2a7243ae3f63` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_56cfdbe35123c49e` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_6dbdc8e943261fa7` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_755be6c147ddc5dd` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_7822bc3cef85c783` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_7ec00a3365f208e6` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_9946be0e7d11161a` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_9e866bf082e52dd7` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_a01b9809f37fb47b` | YES | `fadena-std` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_cf46d8f0e018b09e` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_coronel_database_systems_11ed` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_d7ff8399759d387a` | YES | `fadena-std` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_d946d1a5a3c32144` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | YES | `fadena-std` | FORMAL | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_de275591245abbd3` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | YES | `fadena-std` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_f3352475bc0cd360` | YES | `fadena-std` | — | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_f93b8a264e20359c` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_fadena_prog_archivos` | NO | `fase0-soc` | PRIMARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_fadena_std_unidad1` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_marques_bases_de_datos` | YES | `fadena-std` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | YES | `fadena-std` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-std` | `src_ramalho_fluent_python` | NO | `fase0-soc` | IMPLEMENTATION | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_rosen_matematicas_discretas` | NO | `fase0-soc` | — | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | YES | `fadena-std` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |

### SCOPE-05 — `fadena-teleco` (12)

| notebook_id | source_id | physical_pdf_present | physical_home_scope | declared_role | relationship_candidate | priority_candidate | CROSS_SCOPE_STATUS |
|---|---|---:|---|---|---|---|---|
| `fadena-teleco` | `src-guia-2025-c04f44ef` | NO | `fase0-soc` | METHODOLOGICAL | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-teleco` | `src_001b27137cf6680c` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_11195af8e0f2ef40` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | YES | `fadena-teleco` | FORMAL | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_corletti_seguridad_redes` | YES | `fadena-teleco` | COMPLEMENTARY | UNRESOLVED | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_da10b53f20f2a647` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_kurose_computer_networking` | YES | `fadena-teleco`, `fase0-soc` | PRIMARY, METHODOLOGICAL | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |
| `fadena-teleco` | `src_stallings_computer_security` | NO | `fase0-soc` | PRIMARY | UNRESOLVED | NOT_ESTABLISHED | NO_NATIVE_SUPPORT |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | YES | `fadena-teleco` | PRIMARY | PRIMARY | NOT_ESTABLISHED | NATIVE_FOLDER_SUPPORT |

### Recuento conceptual

| notebook_id | relaciones | PRIMARY candidate | COMPLEMENTARY candidate | AUXILIARY candidate | UNRESOLVED |
|---|---:|---:|---:|---:|---:|
| `fase0-soc` | 26 | 11 | 1 | 0 | 14 |
| `fadena-lenguajes` | 17 | 6 | 0 | 0 | 11 |
| `fadena-so2` | 14 | 7 | 0 | 0 | 7 |
| `fadena-std` | 30 | 14 | 0 | 0 | 16 |
| `fadena-teleco` | 12 | 8 | 0 | 0 | 4 |
| **TOTAL** | **99** | **46** | **1** | **0** | **52** |

No hay `NONE` candidato en este inventario, porque las 99 filas son relaciones
técnicas presentes; esta tabla no es un universo de todas las relaciones
posibles. `AUXILIARY` tampoco se asigna por inferencia a `IMPLEMENTATION`,
`REFERENCE`, `METHODOLOGICAL` o `FORMAL`.

## 10. Tratamiento de los 24 casos sin soporte nativo de carpeta

Los 24 no se declaran errores. Son relaciones cuyo PDF de hash exacto se
encuentra en otra carpeta, sin copia en la carpeta del notebook destino. En la
matriz quedan `CROSS_SCOPE_STATUS = NO_NATIVE_SUPPORT`; la intención de
reutilización permanece `UNRESOLVED`, excepto que ninguna recibe
`COMPLEMENTARY` por defecto. No se elimina, aprueba, replica ni cambia ninguna.

| notebook_id destino | source_id | physical_home_scope CP087 | candidato conceptual | CROSS_SCOPE_STATUS |
|---|---|---|---|---|
| `fase0-soc` | `src_0bc5d20dcc91895f` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_0fc90b2695369475` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_a9a056742dcf69ae` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_d253687930308e41` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_e9682dece40b58ab` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fase0-soc` | `src_stallings_os_internals_7ed` | `fadena-so2` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_concurrencia` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_memoria` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_planificacion` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_fadena_so_procesos` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-so2` | `src_stallings_computer_security` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_fadena_prog_archivos` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_ramalho_fluent_python` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-std` | `src_rosen_matematicas_discretas` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-teleco` | `src-guia-2025-c04f44ef` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |
| `fadena-teleco` | `src_stallings_computer_security` | `fase0-soc` | UNRESOLVED | NO_NATIVE_SUPPORT |

Kurose no está en esa lista de 24: su hash aparece en ambas carpetas y su
relación técnica existe en ambos scopes. La relación de Fase 0 queda
`COMPLEMENTARY` candidata por la instrucción explícita del modelo; la copia
duplicada no se trata como requisito para esa reutilización y no se mantiene
como política deseada.

## 11. Lista de asuntos para decisión posterior

### NATIVE candidate

46 relaciones tienen hash en la carpeta destino y `PRIMARY` declarado o
ningún role contradictorio. Son candidatas estructurales de material nativo;
`NATIVE_FOLDER_SUPPORT` es evidencia de ubicación e intención física, no
adjudicación final de función pedagógica prioritaria, de que el material
pertenezca curricularmente al curso ni autorización.

### REUSE candidate

Una relación conceptual `COMPLEMENTARY` queda identificada explícitamente:
`fase0-soc → src_kurose_computer_networking`. Es el ejemplo indicado por la
persona responsable del modelo. Debe seguir siendo un vínculo separado de
`fadena-teleco → src_kurose_computer_networking`. Cualquier otro uso entre
scopes se mantiene `UNRESOLVED` hasta que se documenten función, propósito y
provenance; no se usa similitud temática para llenarlos.

### AUXILIARY candidate

Ninguno establecido en esta pasada. Los roles `IMPLEMENTATION`,
`METHODOLOGICAL`, `REFERENCE` o `FORMAL` no se traducen por intuición a
`AUXILIARY`; falta una definición/decisión de relación que establezca propósito
y prioridad.

### UNRESOLVED

52 filas quedan sin categoría conceptual segura: las 24 relaciones sin
soporte de carpeta destino y 28 con soporte local pero role explícito no
equivalente o contradictorio con una interpretación automática de `PRIMARY`.
El `source_id`, path/hash y role relevante permanecen visibles en §9 para
futura resolución. La clasificación no indica inclusión o exclusión.

## 12. Caso especial `fadena-std`

Se conserva `FADENA_STD_RELEASE_SCOPE = INCLUDED`. CP085 y los documentos C4
siguen vigentes sin reinterpretación favorable ni desfavorable:

| source_id | estado C4-DRAFT vigente | hogar físico CP087 | lectura de CP088 |
|---|---|---|---|
| `src_ramakrishnan_gehrke_dbms` | `POLICY_DECISION_PENDING` | `fadena-std` | Nativo por ubicación física; candidato de relación conceptual queda `UNRESOLVED` por role `COMPLEMENTARY` y estado C4 pendiente. |
| `src_f3352475bc0cd360` | `PEDAGOGICAL_USE_PENDING` | `fadena-std` | Carpeta nativa; candidate `PRIMARY` por ausencia de role contradictorio, pero el propósito pedagógico de las soluciones sigue pendiente. No se concede autorización. |
| `src_fadena_prog_archivos` | `UNRESOLVED` | `fase0-soc` | Sin respaldo nativo en STD; vínculo destino sigue `UNRESOLVED`. |
| `src_ramalho_fluent_python` | `UNRESOLVED` | `fase0-soc` | Sin respaldo nativo en STD; vínculo destino sigue `UNRESOLVED`. |
| `src_rosen_matematicas_discretas` | `UNRESOLVED` | `fase0-soc` | Sin respaldo nativo en STD; vínculo destino sigue `UNRESOLVED`. |

La presencia física de un PDF en `fuentes/fadena-std/` no demuestra autoridad
académica externa, bibliografía, firma institucional, permiso legal o
autorización L3. Las cinco evaluaciones source-specific se mantienen separadas
de la tipología conceptual y del estado de autorización.

## 13. Efecto, estado L3 y criterios de cierre

CP088 define el modelo y deja 99 relaciones reclasificadas **solo en sentido
conceptual**. No modifica CP084, CP085 o CP086 como evidencia histórica, ni
actualiza estado técnico. El nuevo marco puede ser usado por un checkpoint
posterior para reevaluar las relaciones, nunca para inferir una autorización.

```text
DOCUMENT_IDENTITY = GLOBAL
DOCUMENT_IDENTITY_MODEL = DEFINED
RELATION_MODEL = DEFINED
FADENA_STRICT_CURRICULUM = DEFINED
SOC_ROADMAP_PHASE_MODEL = DEFINED
CROSS_SCOPE_REUSE = DEFINED
PHYSICAL_DEDUPLICATION = DEFINED
AUTOMATIC_SCOPE_INHERITANCE = FORBIDDEN
99_RELATIONS_RECLASSIFIED_CONCEPTUALLY = YES

L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0
L3_AUTHORIZATION = UNCHANGED
C2_AUTHORIZATION_THRESHOLD = L3
C2 = BLOCKED
CRITERION_2 = BLOCKED
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
```
