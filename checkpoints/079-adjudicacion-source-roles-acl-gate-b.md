# Checkpoint 079 — adjudicación de source roles y ACL de Gate B

## 1. Alcance y conclusión ejecutiva

Se cotejaron estáticamente los roles de fuentes declarados, las listas de
fuentes del registry y las asociaciones efectivas `notebook_sources` para los
cinco notebooks del release fijado en CP077. La base SQLite se consultó
únicamente con URI `mode=ro` y `PRAGMA query_only=ON`; no se inspeccionaron
contenidos de corpus ni chunks.

La evidencia distingue dos afirmaciones diferentes:

1. **Allowlist técnica actual:** para chat/retrieval por notebook, las
   asociaciones persistidas `notebook_sources` determinan las fuentes
   permitidas; las fuentes pedidas por el cliente se intersectan con esa
   allowlist.
2. **Autorización curricular adjudicada:** no queda demostrada por la mera
   existencia de una asociación, una etiqueta de rol, una entrada de registry
   ni un source record. No se encontró una adjudicación aprobada por fuente
   para el scope de release que explique todas las asociaciones compartidas y
   diferencias observadas.

Por tanto, la reconciliación técnica de roles/ACL **no alcanza para cerrar el
criterio 2**. Se documentan las diferencias concretas, pero no se concede,
revoca ni modifica ninguna relación.

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
CRITERION_1 = BLOCKED  (sin cambio; CP078)
CRITERION_2 = BLOCKED
GATE_B_IDENTITY_STATUS = BLOCKED
```

## 2. Fuentes, método e invariantes

### Fuentes examinadas

- [CP077 — reconciliación de identidad](./077-reconciliacion-identidad-gate-b.md)
- [CP078 — adjudicación de `curriculum_id`](./078-adjudicacion-curriculum-id-gate-b.md)
- [`config/notebook_source_roles.json`](../config/notebook_source_roles.json)
- [`src/study_engine/federation/notebook_registry.py`](../src/study_engine/federation/notebook_registry.py), `DEFAULT_NOTEBOOKS`
- [`src/study_engine/pedagogy/evidence_assembler.py`](../src/study_engine/pedagogy/evidence_assembler.py)
- [`src/study_engine/pedagogy/structured_pipeline.py`](../src/study_engine/pedagogy/structured_pipeline.py)
- [`src/study_engine/web/routes/chat.py`](../src/study_engine/web/routes/chat.py)
- [`src/study_engine/storage/knowledge_store.py`](../src/study_engine/storage/knowledge_store.py)
- [`src/study_engine/retrieval/expansion.py`](../src/study_engine/retrieval/expansion.py)
- [`src/study_engine/retrieval/fabric.py`](../src/study_engine/retrieval/fabric.py)
- [`src/study_engine/web/routes/pedagogy.py`](../src/study_engine/web/routes/pedagogy.py)
- [`src/study_engine/web/routes/retrieval.py`](../src/study_engine/web/routes/retrieval.py)
- [`docs/PLAN_SUITE_FIX_ESTABILIZACION.md`](../docs/PLAN_SUITE_FIX_ESTABILIZACION.md), apartados G2.0 y C4/ACL
- Tests existentes indicados en §7; **no se ejecutaron**.

### Método de cotejo

Para cada notebook `n` se definieron:

- `R(n)`: IDs en `DEFAULT_NOTEBOOKS[n].sources`.
- `U(n)`: IDs llave de `notebook_source_roles.json[n]`.
- `P(n)`: IDs de `notebook_sources` persistidos para ese notebook.
- `S`: source IDs presentes en la tabla de source records.

Los conjuntos se cotejaron con lectura estática de configuración/código y
consultas `SELECT` de sólo lectura. `R`, `U` y `P` son representaciones
distintas: no se sustituyó una por otra ni se interpretó su intersección como
autorización humana.

No se ejecutaron TALOS/FastAPI, endpoints, tests, proveedores, workloads,
benchmarks ni retrieval; tampoco se inspeccionaron DB/corpus de contenido,
modelos o índices. No se modificaron código, configuración, DB, asociaciones,
roles, gates, A-PRE ni artefactos protegidos.

## 3. Semántica y autoridad de cada representación

| Representación | Consumidor/efecto observado | Autoridad demostrada y límite |
|---|---|---|
| `DEFAULT_NOTEBOOKS[].sources` (`R`) | `NotebookRegistry` publica la declaración estática del notebook, incluidas fuentes y datos de registry. | Declaración versionada de registry. No es la ACL consultada por el chat y no demuestra por sí sola autorización pedagógica. |
| `notebook_source_roles.json` (`U`) | `MultiSourceEvidenceAssembler` toma las llaves de roles y las intersecta con `notebook.sources`; los campos `roles`, `title`, `authority` y `status` configuran/etiquetan evidencia en ese flujo. | Configuración declarativa de clasificación. El número `authority` es un peso configurado, no una decisión institucional de ACL. Los roles no agregan por sí mismos fuentes a `P`. |
| `notebook_sources` (`P`) | `KnowledgeStore.get_notebook()` carga estas asociaciones como `Notebook.sources`. El chat resuelve su allowlist a partir de la tabla y filtra las fuentes solicitadas dentro de ella. | Autoridad fáctica sobre las asociaciones persistidas en esta instalación y allowlist técnica del chat. No prueba quién aprobó la asociación, el propósito permitido ni su vigencia curricular. |
| `sources` source record (`S`) | La fila permite resolver metadatos/registro de una fuente. | Sólo prueba presencia de un registro con ese ID en la tabla consultada. No demuestra disponibilidad de contenido, OCR, calidad, autoridad académica ni autorización. |
| `AUTHOR_ROLES_BY_NOTEBOOK` en `structured_pipeline.py` | `resolve_epistemic_role()` etiqueta citas como `pedagogical`, `formal` o `technical` por coincidencia de texto en ID/título/autor. `chat.py` usa esa función al formar metadatos de citas. | Es una segunda representación de clasificación, separada de `notebook_source_roles.json`. No filtra ni concede acceso. No se encontró un contrato versionado que concilie sus vocabularios con los roles de `U`. |

`docs/PLAN_SUITE_FIX_ESTABILIZACION.md` registra expresamente que una
asociación persistida, un rol de fuente, la coincidencia temática, inclusión
bibliográfica o SHA coincidente no bastan **individualmente** para conceder
ACL. Ese pasaje formula invariantes candidatos para el flujo C4; no constituye
una adjudicación de las fuentes enumeradas aquí.

## 4. Flujo estático de roles y acceso

### 4.1 Chat y retrieval por notebook

En `chat.py`, `_authorized_sources_for_scope()` consulta las asociaciones
explícitas de `notebook_sources` para el notebook objetivo. Si el scope es una
carpeta global, agrega las asociaciones de los notebooks descendientes. Luego
`_filter_requested_sources()` conserva sólo IDs o SHA que están dentro de esa
allowlist. Si no quedan fuentes permitidas, el ensamblado retorna abstención.

Las ramas observadas de `_assemble_epistemic_context()` pasan ese conjunto a
las búsquedas y filtran también los resultados devueltos por `source_id`. El
almacén aplica el notebook/source filter en FTS/vector/hybrid cuando se
proporciona. Este flujo no consulta `notebook_source_roles.json` para decidir
la allowlist. Así, en el chat, `P` —y no `R` o `U`— es la representación de
acceso efectivo.

El cache key del contexto incluye scope, notebook y fuentes activas. Es una
separación de caché, no una fuente independiente de autorización.

### 4.2 Ensamblador pedagógico de evidencia

`MultiSourceEvidenceAssembler` obtiene `Notebook.sources`, calcula
`U(n) ∩ P(n)` y sólo intenta cargar chunks para esos IDs. Ante fallo al cargar
el notebook retorna sin evidencia; ante menos de dos citas autorizadas,
abstiene y no enumera fuentes globales. El endpoint de concepto de
`/api/pedagogy/episode/{episode_id}/concept` llama al orquestador que usa este
ensamblador.

Esto demuestra una intersección fail-closed en la implementación. No demuestra
que cada rol sea académicamente correcto ni que cada asociación haya sido
aprobada para el release. El ensamblador tampoco evalúa `status` como
`SOURCE_PENDING_OCR` antes de considerar un source ID activo; la etiqueta es
descriptiva en la configuración observada.

### 4.3 Segunda clasificación de roles en el chat

`AUTHOR_ROLES_BY_NOTEBOOK` contiene cinco mapas por notebook con términos de
autor/fuente y etiquetas `pedagogical`, `formal`, `technical`. Para los cinco
IDs exactos del release hay entrada exacta en el mapa; el helper incluye
además heurísticas por subcadena/fragmentos para otros IDs, pero no se usaron
para adjudicar estos cinco.

Esta clasificación sirve para presentar/organizar citas, no para filtrar
fuentes. No hay evidencia de una tabla de correspondencia aprobada entre estos
roles y `PRIMARY`, `METHODOLOGICAL`, `FORMAL`, `IMPLEMENTATION`,
`COMPLEMENTARY` o `REFERENCE` de `notebook_source_roles.json`. Por eso, una
etiqueta visible de fuente no prueba la aplicación de los roles de `U` ni una
decisión de ACL.

### 4.4 Superficies separadas y límite estático

- `/api/retrieval/fabric/inspect` es una superficie diagnóstica con
  autenticación administrativa. Llama a Retrieval Fabric con notebook ID,
  pero no recibe la allowlist `source_ids` calculada por el chat; se mantiene
  fuera de la evidencia de aislamiento del recorrido de estudiante.
- La expansión `SectionExpander` parte de resultados semilla ya filtrados,
  pero consulta chunks vecinos por `document_id` y sus resultados no vuelven
  a intersectarse con la allowlist `retrieval_source_ids` antes de construir
  `expanded_context_text`. La lectura estática no demuestra que haya chunks
  vecinos con otro `source_id`; tampoco demuestra una invariante de documento
  que lo imposibilite. Queda pendiente validación o evidencia de esa
  invariante antes de usar expansión como prueba de aislamiento total.
- La capa `filter_presentation()` descrita en el código es un filtro de
  chunks de soluciones. No equivale a autorización curricular por source ID.

## 5. Crosswalk por los cinco scopes

En la tabla, `U∩P` es la intersección que puede consumir el ensamblador
pedagógico; el chat considera `P` como allowlist sin restringirlo por `U`.
`R−U` son fuentes registradas sin rol declarativo. `R−(U∪P)` son fuentes de
registry que no tienen ni rol ni asociación; el valor es cero en los cinco
scopes. `U−R` son roles sin entrada en la lista de sources del registry.

| Scope | `|R|` | `|U|` | `|P|` | `|U∩P|` | `|U−P|` | `|P−U|` | `|R−U|` | `|U−R|` | Registry sin rol ni asociación |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `fase0-soc` | 14 | 9 | 26 | 8 | 1 | 18 | 6 | 1 | 0 |
| `fadena-lenguajes` | 10 | 15 | 17 | 15 | 0 | 2 | 0 | 5 | 0 |
| `fadena-so2` | 8 | 16 | 14 | 13 | 3 | 1 | 0 | 8 | 0 |
| `fadena-std` | 9 | 29 | 30 | 28 | 1 | 2 | 0 | 20 | 0 |
| `fadena-teleco` | 8 | 13 | 12 | 12 | 1 | 0 | 0 | 5 | 0 |

### 5.1 Sets completos por scope

Los siguientes sets hacen reproducible el crosswalk. El set de registros
faltantes indicado en §5.2 completa para cada ID la dimensión de source record.
La asignación de categorías de rol por ID sigue estando en la configuración
versionada citada en §2; los tamaños y categorías agregadas de `U∩P` se
resumen en §5.3.

#### SCOPE-01 — `fase0-soc`

```text
R = {
  src_0fc90b2695369475, src_bel_algoritmos_estructuras_python,
  src_d253687930308e41, src_fadena_prog_punteros,
  src_fadena_so_concurrencia, src_fadena_so_memoria,
  src_fadena_so_planificacion, src_fadena_so_procesos,
  src_goodrich_dsa_python, src_joyanes_fundamentos,
  src_martin_clean_code, src_rosen_matematicas_discretas,
  src_spraul_think_like_a_programmer, src_sweigart_automate_boring_stuff
}
U = {
  src_bel_algoritmos_estructuras_python, src_fadena_prog_punteros,
  src_goodrich_dsa_python, src_joyanes_fundamentos,
  src_martin_clean_code, src_rosen_matematicas_discretas,
  src_spraul_think_like_a_programmer, src_sweigart_automate_boring_stuff,
  src_tori_hacking_etico
}
P = {
  src-guia-2025-c04f44ef, src_0bc5d20dcc91895f,
  src_0fc90b2695369475, src_a9a056742dcf69ae,
  src_bel_algoritmos_estructuras_python, src_d253687930308e41,
  src_e9682dece40b58ab, src_f009c4e75f5ca3f2,
  src_fadena_prog_arboles, src_fadena_prog_archivos,
  src_fadena_prog_lineales, src_fadena_prog_punteros,
  src_fadena_so_concurrencia, src_fadena_so_memoria,
  src_fadena_so_planificacion, src_fadena_so_procesos,
  src_goodrich_dsa_python, src_joyanes_fundamentos,
  src_kurose_computer_networking, src_martin_clean_code,
  src_ramalho_fluent_python, src_rosen_matematicas_discretas,
  src_spraul_think_like_a_programmer, src_stallings_computer_security,
  src_stallings_os_internals_7ed, src_sweigart_automate_boring_stuff
}
```

`U−P = {src_tori_hacking_etico}`.
`P−U = {src-guia-2025-c04f44ef, src_0bc5d20dcc91895f,
src_0fc90b2695369475, src_a9a056742dcf69ae, src_d253687930308e41,
src_e9682dece40b58ab, src_f009c4e75f5ca3f2, src_fadena_prog_arboles,
src_fadena_prog_archivos, src_fadena_prog_lineales, src_fadena_so_concurrencia,
src_fadena_so_memoria, src_fadena_so_planificacion, src_fadena_so_procesos,
src_kurose_computer_networking, src_ramalho_fluent_python,
src_stallings_computer_security, src_stallings_os_internals_7ed}`.
`R−U` son `src_0fc90b2695369475`, `src_d253687930308e41` y
`src_fadena_so_{concurrencia,memoria,planificacion,procesos}`; los seis están
asociados (`P`), pero no tienen rol en `U`.

#### SCOPE-02 — `fadena-lenguajes`

```text
R = {
  src_fadena_leng_clase1, src_fadena_leng_clase2,
  src_fadena_prog_lineales, src_fadena_prog_punteros,
  src_joyanes_fundamentos, src_marzal_intro_programacion_c,
  src_spraul_think_like_a_programmer, src_stallman_gnu_c_manual,
  src_sweigart_automate_boring_stuff, src_urrutia_programacion_c_principiantes
}
U = {
  src_1149ca3399b6dd85, src_115f0bc876b44be8,
  src_7ba98d836c32fe4b, src_8ac0eed0a6121c6a,
  src_fadena_leng_clase1, src_fadena_leng_clase2,
  src_fadena_prog_lineales, src_fadena_prog_punteros,
  src_fdc4df20e0f9f99e, src_joyanes_fundamentos,
  src_marzal_intro_programacion_c, src_spraul_think_like_a_programmer,
  src_stallman_gnu_c_manual, src_sweigart_automate_boring_stuff,
  src_urrutia_programacion_c_principiantes
}
P = {
  src_1149ca3399b6dd85, src_115f0bc876b44be8,
  src_7ba98d836c32fe4b, src_8ac0eed0a6121c6a,
  src_fadena_leng_clase1, src_fadena_leng_clase2,
  src_fadena_prog_arboles, src_fadena_prog_archivos,
  src_fadena_prog_lineales, src_fadena_prog_punteros,
  src_fdc4df20e0f9f99e, src_joyanes_fundamentos,
  src_marzal_intro_programacion_c, src_spraul_think_like_a_programmer,
  src_stallman_gnu_c_manual, src_sweigart_automate_boring_stuff,
  src_urrutia_programacion_c_principiantes
}
```

`U−P = ∅`; `P−U = {src_fadena_prog_arboles, src_fadena_prog_archivos}`.
`U−R = {src_1149ca3399b6dd85, src_115f0bc876b44be8,
src_7ba98d836c32fe4b, src_8ac0eed0a6121c6a, src_fdc4df20e0f9f99e}`.
Los cinco roles que no figuran en `R` sí están asociados (`P`) y tienen source
record. La divergencia es de declaración/rol, no ausencia de asociación.

#### SCOPE-03 — `fadena-so2`

```text
R = {
  src_fadena_so2_clase1, src_fadena_so2_clase2,
  src_fadena_so_concurrencia, src_fadena_so_memoria,
  src_fadena_so_planificacion, src_fadena_so_procesos,
  src_stallings_computer_security, src_stallings_os_internals_7ed
}
U = {
  src_0fc90b2695369475, src_a9a056742dcf69ae,
  src_d253687930308e41, src_e9682dece40b58ab,
  src_f009c4e75f5ca3f2, src_fadena_so2_clase1,
  src_fadena_so2_clase2, src_fadena_so_concurrencia,
  src_fadena_so_memoria, src_fadena_so_planificacion,
  src_fadena_so_procesos, src_rudareanu_linux_sysadmins,
  src_silberschatz_so_7ed, src_stallings_computer_security,
  src_stallings_os_internals_7ed, src_tanenbaum_so_modernos_3ed
}
P = {
  src_0bc5d20dcc91895f, src_0fc90b2695369475,
  src_a9a056742dcf69ae, src_d253687930308e41,
  src_e9682dece40b58ab, src_f009c4e75f5ca3f2,
  src_fadena_so2_clase1, src_fadena_so2_clase2,
  src_fadena_so_concurrencia, src_fadena_so_memoria,
  src_fadena_so_planificacion, src_fadena_so_procesos,
  src_stallings_computer_security, src_stallings_os_internals_7ed
}
```

`U−P = {src_rudareanu_linux_sysadmins, src_silberschatz_so_7ed,
src_tanenbaum_so_modernos_3ed}`; los tres config entries tienen
`status=SOURCE_MISSING` y no tienen source record en la tabla consultada.
`P−U = {src_0bc5d20dcc91895f}`.
`U−R = {src_0fc90b2695369475, src_a9a056742dcf69ae,
src_d253687930308e41, src_e9682dece40b58ab, src_f009c4e75f5ca3f2,
src_rudareanu_linux_sysadmins, src_silberschatz_so_7ed,
src_tanenbaum_so_modernos_3ed}`. Los cinco IDs opacos no presentes en `R`
están asociados; sus provenance/identidad no se resuelve por semejanza.

#### SCOPE-04 — `fadena-std`

```text
R = {
  src_coronel_database_systems_11ed, src_date_intro_sistemas_bd_7ed,
  src_elmasri_navathe_sistemas_bd, src_fadena_prog_archivos,
  src_fadena_std_unidad1, src_marques_bases_de_datos,
  src_ramakrishnan_gehrke_dbms, src_ramalho_fluent_python,
  src_silberschatz_fundamentos_bd
}
U = {
  src_032c52bff94a0743, src_0960283d5cef8dee,
  src_3102eb1e89e2229e, src_3e2e8abda5f55c17,
  src_52ff5ff3e07c1da5, src_53ef2a7243ae3f63,
  src_56cfdbe35123c49e, src_6dbdc8e943261fa7,
  src_755be6c147ddc5dd, src_7822bc3cef85c783,
  src_7ec00a3365f208e6, src_9946be0e7d11161a,
  src_9e866bf082e52dd7, src_a01b9809f37fb47b,
  src_cairo_guardati_estructuras_datos, src_cf46d8f0e018b09e,
  src_coronel_database_systems_11ed, src_d7ff8399759d387a,
  src_d946d1a5a3c32144, src_date_intro_sistemas_bd_7ed,
  src_de275591245abbd3, src_elmasri_navathe_sistemas_bd,
  src_f93b8a264e20359c, src_fadena_prog_archivos,
  src_fadena_std_unidad1, src_marques_bases_de_datos,
  src_ramakrishnan_gehrke_dbms, src_ramalho_fluent_python,
  src_silberschatz_fundamentos_bd
}
P = {
  src_032c52bff94a0743, src_0960283d5cef8dee,
  src_3102eb1e89e2229e, src_3e2e8abda5f55c17,
  src_52ff5ff3e07c1da5, src_53ef2a7243ae3f63,
  src_56cfdbe35123c49e, src_6dbdc8e943261fa7,
  src_755be6c147ddc5dd, src_7822bc3cef85c783,
  src_7ec00a3365f208e6, src_9946be0e7d11161a,
  src_9e866bf082e52dd7, src_a01b9809f37fb47b,
  src_cf46d8f0e018b09e, src_coronel_database_systems_11ed,
  src_d7ff8399759d387a, src_d946d1a5a3c32144,
  src_date_intro_sistemas_bd_7ed, src_de275591245abbd3,
  src_elmasri_navathe_sistemas_bd, src_f3352475bc0cd360,
  src_f93b8a264e20359c, src_fadena_prog_archivos,
  src_fadena_std_unidad1, src_marques_bases_de_datos,
  src_ramakrishnan_gehrke_dbms, src_ramalho_fluent_python,
  src_rosen_matematicas_discretas, src_silberschatz_fundamentos_bd
}
```

`U−P = {src_cairo_guardati_estructuras_datos}`; la entrada declara
`status=SOURCE_MISSING` y no hay source record. `P−U =
{src_f3352475bc0cd360, src_rosen_matematicas_discretas}`.
`U−R` tiene 20 IDs: los 14 IDs opacos
`src_032c52bff94a0743`, `src_0960283d5cef8dee`,
`src_3102eb1e89e2229e`, `src_3e2e8abda5f55c17`,
`src_52ff5ff3e07c1da5`, `src_53ef2a7243ae3f63`,
`src_56cfdbe35123c49e`, `src_6dbdc8e943261fa7`,
`src_755be6c147ddc5dd`, `src_7822bc3cef85c783`,
`src_7ec00a3365f208e6`, `src_9946be0e7d11161a`,
`src_9e866bf082e52dd7`, `src_a01b9809f37fb47b`, más
`src_cairo_guardati_estructuras_datos`, `src_cf46d8f0e018b09e`,
`src_d7ff8399759d387a`, `src_d946d1a5a3c32144`,
`src_de275591245abbd3`, `src_f93b8a264e20359c`.
Los 19 IDs de ese conjunto distintos de Cairo están asociados; Cairo no tiene
source record.

#### SCOPE-05 — `fadena-teleco`

```text
R = {
  src-guia-2025-c04f44ef, src_castro_fusario_comunicaciones_redes,
  src_comer_internetworking_tcpip_v1, src_corletti_seguridad_redes,
  src_fadena_teleco_unidad1, src_kurose_computer_networking,
  src_stallings_computer_security, src_stallings_comunicaciones_redes_7ed
}
U = {
  src-guia-2025-c04f44ef, src_001b27137cf6680c,
  src_11195af8e0f2ef40, src_2f1a5843cd1693ba,
  src_castro_fusario_comunicaciones_redes,
  src_comer_internetworking_tcpip_v1, src_corletti_seguridad_redes,
  src_da10b53f20f2a647, src_fadena_teleco_unidad1,
  src_kurose_computer_networking, src_stallings_computer_security,
  src_stallings_comunicaciones_redes_7ed, src_tanenbaum_computer_networks
}
P = {
  src-guia-2025-c04f44ef, src_001b27137cf6680c,
  src_11195af8e0f2ef40, src_2f1a5843cd1693ba,
  src_castro_fusario_comunicaciones_redes,
  src_comer_internetworking_tcpip_v1, src_corletti_seguridad_redes,
  src_da10b53f20f2a647, src_fadena_teleco_unidad1,
  src_kurose_computer_networking, src_stallings_computer_security,
  src_stallings_comunicaciones_redes_7ed
}
```

`U−P = {src_tanenbaum_computer_networks}`; la entrada declara
`status=SOURCE_MISSING` y no hay source record. `P−U = ∅`.
`U−R = {src_001b27137cf6680c, src_11195af8e0f2ef40,
src_2f1a5843cd1693ba, src_da10b53f20f2a647,
src_tanenbaum_computer_networks}`. Los cuatro IDs opacos están asociados y
tienen source record; Tanenbaum no está asociado ni tiene source record.

### 5.2 Source record: excepciones

El cotejo de la tabla `sources` encontró registros para todos los IDs de `R`,
`U` o `P` excepto:

| Scope | ID sin source record | Rol/ACL observado |
|---|---|---|
| `fadena-so2` | `src_rudareanu_linux_sysadmins` | `U−P`; marcado `SOURCE_MISSING` |
| `fadena-so2` | `src_silberschatz_so_7ed` | `U−P`; marcado `SOURCE_MISSING` |
| `fadena-so2` | `src_tanenbaum_so_modernos_3ed` | `U−P`; marcado `SOURCE_MISSING` |
| `fadena-std` | `src_cairo_guardati_estructuras_datos` | `U−P`; marcado `SOURCE_MISSING` |
| `fadena-teleco` | `src_tanenbaum_computer_networks` | `U−P`; marcado `SOURCE_MISSING` |

No se afirma que los source records restantes tengan documentos/chunks
utilizables: esa capa no se inspeccionó. En `fase0-soc`, la fuente Rosen está
en `U∩P`, tiene source record y conserva `status=SOURCE_PENDING_OCR`. El
ensamblador observado no usa ese `status` como guarda; no se comprobó OCR ni
contenido.

### 5.3 Etiquetas declaradas en roles activos

Conteos de etiquetas en las entradas de `U∩P` (un source puede tener más de
una etiqueta):

| Scope | Etiquetas observadas en `U∩P` |
|---|---|
| `fase0-soc` | `PRIMARY` 1; `METHODOLOGICAL` 1; `FORMAL` 1; `IMPLEMENTATION` 2; `COMPLEMENTARY` 3; `REFERENCE` 1 |
| `fadena-lenguajes` | `PRIMARY` 8; `METHODOLOGICAL` 3; `REFERENCE` 2; `COMPLEMENTARY` 2; `IMPLEMENTATION` 1 |
| `fadena-so2` | `PRIMARY` 9; `IMPLEMENTATION` 3; `COMPLEMENTARY` 1; `METHODOLOGICAL` 1 |
| `fadena-std` | `PRIMARY` 14; `IMPLEMENTATION` 9; `COMPLEMENTARY` 4; `FORMAL` 1 |
| `fadena-teleco` | `PRIMARY` 9; `METHODOLOGICAL` 2; `COMPLEMENTARY` 1; `FORMAL` 1 |

Estos conteos describen la configuración actual; no adjudican autoridad,
pertinencia o nivel curricular de ninguna fuente.

## 6. Source IDs asociados a más de un scope

Se considera compartido un ID que aparece en `P` para dos o más scopes del
release. La relación compartida puede ser intencional o no; la asociación no
resuelve su justificación.

| Scopes con asociación | Cantidad | IDs compartidos |
|---|---:|---|
| `fase0-soc` + `fadena-lenguajes` | 6 | `src_fadena_prog_arboles`, `src_fadena_prog_lineales`, `src_fadena_prog_punteros`, `src_joyanes_fundamentos`, `src_spraul_think_like_a_programmer`, `src_sweigart_automate_boring_stuff` |
| `fase0-soc` + `fadena-lenguajes` + `fadena-std` | 1 | `src_fadena_prog_archivos` |
| `fase0-soc` + `fadena-std` | 2 | `src_ramalho_fluent_python`, `src_rosen_matematicas_discretas` |
| `fase0-soc` + `fadena-so2` | 11 | `src_0bc5d20dcc91895f`, `src_0fc90b2695369475`, `src_a9a056742dcf69ae`, `src_d253687930308e41`, `src_e9682dece40b58ab`, `src_f009c4e75f5ca3f2`, `src_fadena_so_concurrencia`, `src_fadena_so_memoria`, `src_fadena_so_planificacion`, `src_fadena_so_procesos`, `src_stallings_os_internals_7ed` |
| `fase0-soc` + `fadena-so2` + `fadena-teleco` | 1 | `src_stallings_computer_security` |
| `fase0-soc` + `fadena-teleco` | 2 | `src-guia-2025-c04f44ef`, `src_kurose_computer_networking` |

No se reinterpretan estos casos como contaminación demostrada. Sí requieren
decisión explícita de por qué la misma source ID está asociada a cada uno de
esos currículos y evidencia de que el resultado de retrieval/contexto respeta
el aislamiento esperado.

## 7. Evidencia existente y límites

Tests **existentes, no ejecutados en esta tarea**:

- `tests/pedagogy/test_evidence_assembler_isolation.py`: fixture de un notebook
  que demuestra intersección de roles con `Notebook.sources`, ausencia de
  enumeración global y abstención por evidencia insuficiente. No cubre los
  cinco registros del release.
- `tests/unit/web/test_retrieval_scope_allowlist.py`: prueba helper de
  allowlist/filtros ID/SHA con dos scopes sintéticos. No reconcilia la DB
  actual ni aprueba las fuentes reales.
- `tests/unit/web/test_global_scope.py`: fixture de notebooks/carpetas que
  comprueba aislamiento de carpeta y el efecto de una asociación explícita.
  No demuestra que las relaciones actuales de los cinco currículos estén
  autorizadas.
- `tests/storage/test_notebook_isolation.py`: casos de aislamiento con
  notebooks y sources de fixture. No generaliza a este inventario persistido.
- `tests/pedagogy/test_chat_sse_endpoint.py`,
  `test_chat_sse_retrieves_only_sources_authorized_for_notebook_scope`: caso
  de integración sintética que inserta fuentes objetivo/foránea, solicita
  ambas y comprueba que el prompt retenga sólo la asociada. Es un caso para
  `fadena-std`, pero usa fuentes temporales creadas por la prueba; no valida
  todas las source IDs ni la representación real de los cinco scopes.

La lectura estática demuestra el diseño de allowlist en rutas concretas, no
su comportamiento efectivo sobre cada source ID real. La fixture aislada no
se extrapola. Tampoco se ejecutaron las pruebas anteriores ni se observó
prompt/contexto generado para los cinco scopes.

## 8. Dictamen del criterio 2 y evidencia mínima que falta

### Estado

```text
SOURCE_ROLE_ACL_STATUS = BLOCKED
CRITERION_2 = BLOCKED
```

El bloqueo es de **adjudicación y cobertura verificable**, no una afirmación
de que cada asociación sea incorrecta. Evidencia concreta que impide cerrar:

1. `U`, `R` y `P` difieren en los casos enumerados en §5; hay 5 role entries
   sin source record y 23 source associations sin entrada de role
   (`18+2+1+2+0`). Para fase0, 6 entradas del registry carecen de role,
   aunque sí están asociadas.
2. Hay 23 source IDs con asociación cross-scope documentada en §6, sin
   adjudicación encontrada que justifique cada relación al release.
3. `SOURCE_PENDING_OCR` está asociado en Fase 0 y no es una guarda efectiva
   del ensamblador; `SOURCE_MISSING` identifica roles que no tienen registro,
   pero no explica por qué fueron configurados como roles del currículo.
4. No hay evidencia revisada de una decisión aprobada por source ID, notebook,
   propósito y versión para conceder ACL. Las asociaciones reflejan el estado
   técnico local, no el provenance decisional.
5. Los roles visibles en `notebook_source_roles.json` y el mapa
   `AUTHOR_ROLES_BY_NOTEBOOK` son dos clasificaciones distintas sin
   correspondencia documentada; los roles de cita no son controles de acceso.
6. La expansión por documento tiene la limitación estática de §4.4. Hace falta
   demostrar la invariante de source ID por documento o validar el post-filter
   sobre el contexto expandido antes de invocar aislamiento de extremo a
   extremo.
7. La evidencia de tests disponible es fixture/sintética y no demuestra el
   comportamiento de los cinco inventarios reales; no se ejecutó ninguna
   prueba en esta tarea.

### Condición objetiva para reconsiderar C2

Sin cambiar asociaciones como parte de este checkpoint, la evidencia futura
debe:

1. registrar para cada asociación/rol de los cinco scopes una decisión con
   notebook ID, source ID/version, propósito, estado y provenance aprobatoria;
   resolver explícitamente `U−P`, `P−U`, `R−U` y las cinco entradas sin source
   record;
2. adjudicar cada source ID compartido, sin inferir intencionalidad a partir
   del ID, título, similitud, registry o etiqueta;
3. confirmar para cada scope que las relaciones persistidas reflejan esas
   decisiones, mediante evidencia versionada de sólo lectura antes de
   cualquier operación separada de ACL;
4. aportar pruebas/integración por los cinco scopes con resultados positivos y
   negativos que observen source IDs en retrieval y contexto final, incluida
   la expansión por secciones;
5. demostrar que las dos capas de roles tienen semántica separada o aportar
   un crosswalk explícito, y comprobar la política para `SOURCE_PENDING_OCR`;
6. preservar UNKNOWN cuando falte provenance, contenido o resultado de
   ejecución.

Este checkpoint no autoriza aplicar cambios de ACL ni afirma que todos los
ítems anteriores requieran cambiar código: identifica sólo la evidencia que
falta para una adjudicación verificable.

## 9. Invariantes y no-acciones

- Se preserva el release de cinco currículos y `fadena-std` incluido.
- `CRITERION_1 = BLOCKED` se conserva según CP078; no se reevalúa aquí
  `curriculum_id`, aliases ni identidad.
- No se cierran C3, C4, C5, Gate B ni `PRODUCT_COMPLETE`.
- No se modificaron código, config, registry, roles, DB, corpus, asociaciones,
  ACL, tests, modelos, fixtures ni gates.
- La DB se consultó en modo read-only para filas de asociaciones y existencia
  de source records; no se leyeron documentos, chunks o corpus.
- No se ejecutaron TALOS/FastAPI, endpoints, tests, benchmarks, workloads,
  proveedores ni procesos de retrieval.
- No se accedió a VM, corpus productivo, modelos o índices; no se cambió
  A-PRE, CP072 ni artefactos protegidos.
- Se preservaron los cambios preexistentes del worktree, incluidos los
  cambios previos de `checkpoints/index.md`.

## Estado final

```text
RELEASE_SCOPE = 5 currículos
FADENA_STD_RELEASE_SCOPE = INCLUDED
IDENTITY_RECONCILIATION = evaluación técnica; CP078 mantiene C1 bloqueado
CURRICULAR_AUTHORITY = pendiente de Gate B criterio 5
SOURCE_ROLE_ACL_STATUS = BLOCKED
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
GATE_B_IDENTITY_STATUS = BLOCKED
```
