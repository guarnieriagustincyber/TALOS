# CP084 — adjudicación L3 de autorización de fuentes

## 1. Resultado ejecutivo

La persona responsable del producto fijó el umbral uniforme:

```text
C2_AUTHORIZATION_THRESHOLD = L3
```

L3 exige una decisión documental explícita y trazable que identifique scope o
notebook, source, versión/identidad inequívoca, propósito, decisor y efecto
autorizante. Se aplicó el mismo estándar a cada asociación persistida del
release. No se pidió una nueva decisión por fuente ni se dedujo aprobación de
configuración.

La evidencia consolidada en CP077–083 no contiene una decisión que reúna esos
elementos para ninguna de las 99 parejas `notebook_id → source_id`. Por ello,
las 99 se clasifican `NOT_DEMONSTRATED`; no hay relaciones `UNKNOWN` ni
`DEMONSTRATED` en el universo adjudicado.

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0

AUTHORIZATION_PROVENANCE_STATUS = NOT_DEMONSTRATED
CRITERION_2 = BLOCKED
```

`NOT_DEMONSTRATED` no significa rechazada, no autorizada ni revocada. Significa
que no puede hacerse un claim de autorización L3 para esa relación en este
release con la evidencia disponible. Las asociaciones técnicas permanecen sin
cambio; no se elimina ni modifica ninguna.

## 2. Estándar y método de adjudicación

### 2.1 Condiciones L3

Una relación sería `DEMONSTRATED` únicamente con un artefacto rastreable que
permitiera verificar simultáneamente:

1. notebook/scope;
2. source e identidad/versionado cuando corresponda;
3. propósito permitido;
4. decisor identificado;
5. efecto explícito que autoriza el uso.

`P` (asociación SQLite), `R` (registry), `U` (role), un source record, una
declaración de preservación o la disponibilidad técnica no llenan por sí solos
los requisitos faltantes. Ninguna relación cross-scope hereda una decisión de
otra pareja con el mismo `source_id`.

### 2.2 Corpus documental ya revisado

La adjudicación se limita a la evidencia reconciliada en:

- CP077: identidad y scope de cinco notebooks, incluidos los datos persistidos.
- CP078: discrepancia `curriculum_id`.
- CP079: inventario completo R/U/P, roles, asociaciones, source records,
  discrepancias, excepciones y fuentes compartidas.
- CP080: búsqueda de provenance de autorización y separación de declaraciones
  frente a grants.
- CP081: umbral de provenance aplicado, resultado `UNKNOWN` al no haber
  aprobación positiva demostrada, y hallazgos estructurales de expansión.
- CP082: inspección read-only de document/chunk/source; no aporta decisiones
  de autorización.
- CP083: paquete decisional, 99 relaciones y 23 IDs cross-scope; confirma que
  no se encontró aprobación positiva scoped.

CP080–083 no identifican aprobación positiva por relación. C4 en el plan de
estabilización describe un diseño DRAFT para decisiones futuras; no es una
política aplicable ni una decisión emitida. Las decisiones de preservar un
estado, asignar roles o mantener una asociación pendiente no tienen efecto de
grant. En consecuencia, en el universo revisado no hay evidencia contradictoria
o inaccesible que exija `UNKNOWN`: para cada relación se revisaron sus
representaciones conocidas y no se encontró el acto L3 requerido.

## 3. Tabla completa de adjudicación de las 99 relaciones

Todas las filas son asociaciones `P=PRESENT` según CP079 y están incluidas en
el scope fijado en CP077/077. `R` indica declaración registry; `U` muestra las
etiquetas de role versionadas y `—` indica que no hay esa declaración. El
resultado L3 se repite por relación para hacer explícita la adjudicación
independiente. Para cada fila:

```text
EVIDENCE_FOUND = P y, cuando se indica, R/U declarativos
L3_GAP = no se encontró una decisión trazable con todos los elementos L3
L3_STATUS = NOT_DEMONSTRATED
```

### SCOPE-01 — `fase0-soc` (26 relaciones)

| notebook_id | source_id | R | U / role(s) | P | L3_STATUS |
|---|---|---:|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_0bc5d20dcc91895f` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_0fc90b2695369475` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_a9a056742dcf69ae` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_d253687930308e41` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_e9682dece40b58ab` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_prog_arboles` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_prog_archivos` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_prog_lineales` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_prog_punteros` | Y | IMPLEMENTATION, REFERENCE | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_so_concurrencia` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_so_memoria` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_so_planificacion` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_fadena_so_procesos` | Y | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_goodrich_dsa_python` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_joyanes_fundamentos` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_kurose_computer_networking` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_martin_clean_code` | Y | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_ramalho_fluent_python` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_rosen_matematicas_discretas` | Y | FORMAL | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | Y | METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_stallings_computer_security` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_stallings_os_internals_7ed` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |

### SCOPE-02 — `fadena-lenguajes` (17 relaciones)

| notebook_id | source_id | R | U / role(s) | P | L3_STATUS |
|---|---|---:|---|---|---|
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | — | REFERENCE | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | Y | PRIMARY, METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | Y | METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | Y | METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | Y | REFERENCE | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |

### SCOPE-03 — `fadena-so2` (14 relaciones)

| notebook_id | source_id | R | U / role(s) | P | L3_STATUS |
|---|---|---:|---|---|---|
| `fadena-so2` | `src_0bc5d20dcc91895f` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_0fc90b2695369475` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_a9a056742dcf69ae` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_d253687930308e41` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_e9682dece40b58ab` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so2_clase1` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so2_clase2` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so_concurrencia` | Y | PRIMARY, METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so_memoria` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so_planificacion` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_fadena_so_procesos` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_stallings_computer_security` | Y | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-so2` | `src_stallings_os_internals_7ed` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |

### SCOPE-04 — `fadena-std` (30 relaciones)

| notebook_id | source_id | R | U / role(s) | P | L3_STATUS |
|---|---|---:|---|---|---|
| `fadena-std` | `src_032c52bff94a0743` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_0960283d5cef8dee` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_3102eb1e89e2229e` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_3e2e8abda5f55c17` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_52ff5ff3e07c1da5` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_53ef2a7243ae3f63` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_56cfdbe35123c49e` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_6dbdc8e943261fa7` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_755be6c147ddc5dd` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_7822bc3cef85c783` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_7ec00a3365f208e6` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_9946be0e7d11161a` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_9e866bf082e52dd7` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_a01b9809f37fb47b` | — | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_cf46d8f0e018b09e` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_coronel_database_systems_11ed` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_d7ff8399759d387a` | — | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_d946d1a5a3c32144` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | Y | FORMAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_de275591245abbd3` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_f3352475bc0cd360` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_f93b8a264e20359c` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_fadena_prog_archivos` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_fadena_std_unidad1` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_marques_bases_de_datos` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_ramalho_fluent_python` | Y | IMPLEMENTATION | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_rosen_matematicas_discretas` | — | — | PRESENT | NOT_DEMONSTRATED |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |

### SCOPE-05 — `fadena-teleco` (12 relaciones)

| notebook_id | source_id | R | U / role(s) | P | L3_STATUS |
|---|---|---:|---|---|---|
| `fadena-teleco` | `src-guia-2025-c04f44ef` | Y | METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_001b27137cf6680c` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_11195af8e0f2ef40` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | Y | FORMAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_corletti_seguridad_redes` | Y | COMPLEMENTARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_da10b53f20f2a647` | — | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_kurose_computer_networking` | Y | PRIMARY, METHODOLOGICAL | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_stallings_computer_security` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | Y | PRIMARY | PRESENT | NOT_DEMONSTRATED |

## 4. Razón precisa por resultado

### `NOT_DEMONSTRATED` — 99 relaciones

Para cada una de las 99 filas de §3, la evidencia concreta ya examinada es su
presencia `P` y, según la fila, una declaración `R`, un role `U`, ambos o
ninguno. CP080–083 no encontraron un documento de decisión que vincule esa
pareja notebook/source a una versión/identidad, propósito, decisor y efecto
autorizante. Por tanto, **el elemento que falta en cada fila es el acto L3
trazable**; no se rellenan los restantes elementos a partir de R/U/P.

La clasificación se aplica incluso cuando:

- `R=Y` o existe un role `U`: es configuración/declaración, no grant;
- hay `R+U`: la suma de dos declaraciones sigue sin ser una decisión explícita;
- sólo existe `P`: la allowlist prueba habilitación técnica local, no aprobación;
- el source está compartido: cada pareja conserva evaluación independiente;
- existe una decisión de preservar o dejar pendiente: no otorgó permiso de uso.

### `UNKNOWN` — 0 relaciones

No se utilizó `UNKNOWN`: las representaciones de las 99 parejas fueron
reconciliadas y el expediente CP077–083 informa que no se encontró aprobación
positiva. No hay en el material examinado un artefacto relevante contradictorio
o inaccesible que impida aplicar la regla preferente `NOT_DEMONSTRATED`.

### `DEMONSTRATED` — 0 relaciones

No se encontró artefacto que satisfaga todos los elementos L3 para ninguna
relación. No hay evidencia concreta que registrar bajo esta categoría.

## 5. Resumen por notebook

| notebook_id | relaciones P evaluadas | DEMONSTRATED | NOT_DEMONSTRATED | UNKNOWN |
|---|---:|---:|---:|---:|
| `fase0-soc` | 26 | 0 | 26 | 0 |
| `fadena-lenguajes` | 17 | 0 | 17 | 0 |
| `fadena-so2` | 14 | 0 | 14 | 0 |
| `fadena-std` | 30 | 0 | 30 | 0 |
| `fadena-teleco` | 12 | 0 | 12 | 0 |
| **Total** | **99** | **0** | **99** | **0** |

## 6. Fuentes cross-scope: adjudicación por pareja

CP079/083 identificaron 23 IDs en 48 asociaciones cross-scope. La misma fuente
en dos notebooks representa dos relaciones distintas; la tabla refleja
individualmente cada resultado. No hay autorización L3 heredada entre scopes.

| source_id | scope 1 | L3 | scope 2 | L3 | scope 3, si aplica | L3 |
|---|---|---|---|---|---|---|
| `src-guia-2025-c04f44ef` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-teleco` | NOT_DEMONSTRATED | — | — |
| `src_0bc5d20dcc91895f` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_0fc90b2695369475` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_a9a056742dcf69ae` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_d253687930308e41` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_e9682dece40b58ab` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_f009c4e75f5ca3f2` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_fadena_prog_arboles` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |
| `src_fadena_prog_archivos` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | `fadena-std` | NOT_DEMONSTRATED |
| `src_fadena_prog_lineales` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |
| `src_fadena_prog_punteros` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |
| `src_fadena_so_concurrencia` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_fadena_so_memoria` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_fadena_so_planificacion` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_fadena_so_procesos` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_joyanes_fundamentos` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |
| `src_kurose_computer_networking` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-teleco` | NOT_DEMONSTRATED | — | — |
| `src_ramalho_fluent_python` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-std` | NOT_DEMONSTRATED | — | — |
| `src_rosen_matematicas_discretas` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-std` | NOT_DEMONSTRATED | — | — |
| `src_spraul_think_like_a_programmer` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |
| `src_stallings_computer_security` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | `fadena-teleco` — NOT_DEMONSTRATED |
| `src_stallings_os_internals_7ed` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-so2` | NOT_DEMONSTRATED | — | — |
| `src_sweigart_automate_boring_stuff` | `fase0-soc` | NOT_DEMONSTRATED | `fadena-lenguajes` | NOT_DEMONSTRATED | — | — |

La tabla cubre las 48 relaciones cross-scope, no 23 grants compartidos.

## 7. `fadena-std`: cuestiones separadas

```text
FADENA_STD_RELEASE_SCOPE = INCLUDED
FADENA_STD_SOURCE_ACL_L3 = 0 DEMONSTRATED / 30 NOT_DEMONSTRATED / 0 UNKNOWN
CURRICULUM_ID_STATUS = CONTRADICTORY
ACADEMIC_INSTITUTIONAL_AUTHORITY = NOT_DEMONSTRATED
```

La decisión L3 de este checkpoint se limita a uso de fuentes por notebook.
No resuelve ni debilita las otras dos cuestiones:

- **Source/ACL authorization:** las 30 relaciones `fadena-std → source` no
  tienen decisión L3 identificada; roles versionados en 28 no son grants.
- **Identidad curricular:** CP078 conserva la discrepancia entre
  `fadena_std_2026` esperado y `fadena_v1` persistido. CP084 no interpreta,
  modifica ni usa `fadena_v1` como autoridad.
- **Autoridad académica/institucional:** permanece sin demostración. El
  threshold L3 operativo sobre una asociación no certifica autoridad
  académica del programa ni la procedencia institucional del currículo.

La inclusión de `fadena-std` en el release sigue siendo la decisión de scope
humana previa; no convierte ninguna de sus asociaciones en aprobada.

## 8. Efecto sobre C2 y claim de release

```text
CRITERION_2 = BLOCKED
```

Las 99 asociaciones examinadas están técnicamente presentes, pero ninguna
cumple el umbral L3 para presentarse como autorizada en el release. No se
elimina automáticamente ninguna pareja. Para el estado actual, no puede
emitirse un claim de autorización L3 para esas relaciones. C2 permanece
bloqueado en los cinco scopes afectados; la determinación mecánica posterior
es conteo/cotejo contra decisiones L3 trazables si aparecen, no una nueva
inferencia por role, registry, instalación o similitud.

La evidencia de CP082 sobre mezcla de `document_id`/`source_id` y la falta de
garantía estructural siguen siendo un finding técnico independiente: no
demuestran ni sustituyen autorización L3.

## 9. No-acciones y estado final

No se modificaron DB, ACL, `notebook_sources`, registry, roles, catálogo,
perfiles, `curriculum_id`, retrieval, SectionExpander, código, fixtures,
corpus, embeddings o modelos. No se ejecutaron TALOS/FastAPI, providers,
benchmarks, workloads ni tests. No se reparó
`FK-NOTEBOOK-SOURCES-001`, no se cerró la frontera de expansión y no se
modificaron C1, C2, Gate B ni `PRODUCT_COMPLETE`.

```text
C2_AUTHORIZATION_THRESHOLD = L3
HUMAN_DECISION_REQUIRED = NO
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0

AUTHORIZATION_PROVENANCE_STATUS = NOT_DEMONSTRATED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
```
