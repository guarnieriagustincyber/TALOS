# CP085 — búsqueda de evidencia L3 existente

## 1. Resultado ejecutivo

Se buscaron decisiones documentales existentes que pudieran satisfacer L3
para cada relación del scope de release. Se revisaron las fuentes candidatas ya
reconciliadas en CP077–084 y documentos del repositorio que mencionan
identidades, sources, decisiones curriculares, ACL o C4.

No se encontró ninguna decisión que otorgue autorización L3 para una relación.
Se halló evidencia parcial, explícitamente no autorizante, para 84 parejas:
declaraciones de scope/roles versionadas para 82 asociaciones y evaluaciones
C4-DRAFT source-scoped para dos relaciones P-only de `fadena-std`. Para las
15 asociaciones restantes, la búsqueda no encontró documento
source/scope-específico más allá del estado técnico ya excluido como evidencia
autorizante.

```text
L3_EXISTING_EVIDENCE_FOUND = PARTIAL
RELATIONS_WITH_EXISTING_L3_EVIDENCE = 84
RELATIONS_WITHOUT_EXISTING_L3_EVIDENCE = 15
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
```

`PARTIAL` describe documentos pertinentes pero incompletos frente a L3; no
significa `AUTHORIZED`, no revoca ni deniega las relaciones y no cambia la
adjudicación de CP084:

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0
C2_AUTHORIZATION_THRESHOLD = L3
CRITERION_2 = BLOCKED
```

## 2. Estándar de búsqueda y método

Una decisión L3 debe permitir reconstruir, para la relación exacta:

1. notebook/scope;
2. source e identidad/versionado;
3. propósito;
4. decisor;
5. efecto explícito de autorización.

Se consideró `FOUND` solamente evidencia suficiente para todos esos elementos;
`PARTIAL` evidencia documental que trata una relación concreta pero deja
elementos esenciales sin demostrar; y `NOT_FOUND` ausencia de documento
pertinente source/scope-específico tras revisar las fuentes disponibles. En
ningún caso se completaron campos mediante nombre, pertinencia temática,
asociación histórica o similitud.

La búsqueda fue estática y documental. No se consultó la base, no se
ejecutaron tests o runtime y no se modificaron archivos técnicos. El
inventario evaluado se tomó de CP084, sin reconstruir R/U/P ni alterar su
contenido.

## 3. Evidencia candidata encontrada

### 3.1 C4-DRAFT y adjudicaciones source-scoped de `fadena-std`

| DOCUMENT | LOCATION | DATE/VERSION | NOTEBOOK/SCOPE | SOURCE/S | PURPOSE | DECISOR | EXPLICIT_EFFECT | L3_ELEMENTS_COVERED | L3_ELEMENTS_MISSING |
|---|---|---|---|---|---|---|---|---|---|
| [`PLAN_SUITE_FIX_ESTABILIZACION.md`](../docs/PLAN_SUITE_FIX_ESTABILIZACION.md) | Contrato C4-DRAFT, tabla “Aplicación del contrato al corte actual”; filas de Ramakrishnan, SQL soluciones, `src_fadena_prog_archivos`, Ramalho y Rosen; congelamiento del expediente. | C4-DRAFT, corte documental 2026-09-29. | `fadena-std` explícito. | Identifica source IDs para `src_ramakrishnan_gehrke_dbms`, `src_f3352475bc0cd360`, `src_fadena_prog_archivos`, `src_ramalho_fluent_python`, `src_rosen_matematicas_discretas`. | Describe dimensiones curriculares/procedencia o tratamiento pedagógico pendientes por fuente; no concede un propósito autorizado. | No identifica un decisor competente que emita grant. La mención de evidencia aportada por el usuario no se trata como aprobación de ACL. | Declara C4 DRAFT, `AUTHORIZED_SCOPED` para ninguna y cero escrituras autorizadas; cada fila se mantiene `POLICY_DECISION_PENDING`, `PEDAGOGICAL_USE_PENDING` o `UNRESOLVED`. Efecto explícito: no hay grant. | Scope y source identificables; existe evaluación documental por fuente y contexto/condición de uso para esas cinco relaciones. | Sin versión/identidad de artefacto aprobada como objeto de grant, decisor autorizado, decisión terminal positiva ni efecto autorizante. Además, el documento dice expresamente que C4 está en borrador y no es política aprobada. |

Esta evidencia parcial aplica a cinco **relaciones distintas** dentro de
`fadena-std`, pero no produce ninguna autorización:

| notebook_id | source_id | contenido documental específico | L3_EXISTING_EVIDENCE |
|---|---|---|---|
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | C1–C3 fuertes; C4 `POLICY_DECISION_PENDING`; sin autorización de escritura. | PARTIAL |
| `fadena-std` | `src_f3352475bc0cd360` | Material de soluciones; C4 `PEDAGOGICAL_USE_PENDING`; sin autorización de escritura. | PARTIAL |
| `fadena-std` | `src_fadena_prog_archivos` | Procedencia/bibliografía no confirmadas; C4 `UNRESOLVED`. | PARTIAL |
| `fadena-std` | `src_ramalho_fluent_python` | Correspondencia curricular parcial; bibliografía/procedencia institucional no acreditadas; C4 `UNRESOLVED`. | PARTIAL |
| `fadena-std` | `src_rosen_matematicas_discretas` | Bibliografía/procedencia no confirmadas; C4 `UNRESOLVED`. | PARTIAL |

CP084 ya clasifica todas estas asociaciones `NOT_DEMONSTRATED` bajo L3. CP085
no reemplaza ese estado.

### 3.2 Declaraciones técnicas de scope y role

| DOCUMENT | LOCATION | DATE/VERSION | NOTEBOOK/SCOPE | SOURCE/S | PURPOSE | DECISOR | EXPLICIT_EFFECT | L3_ELEMENTS_COVERED | L3_ELEMENTS_MISSING |
|---|---|---|---|---|---|---|---|---|---|
| [`notebook_source_roles.json`](../config/notebook_source_roles.json) | Entradas por notebook y source. | Configuración versionada; no registra decisión aprobatoria por relación. | Los cinco scopes, según las entradas. | 76 asociaciones persistidas con roles declarados. | Etiqueta el rol/tipo de evidencia; no declara concesión de uso para release. | No identificado. | No declara grant; los roles no crean ACL. | Notebook/source y role declarado para esas parejas; identificación técnica del artefacto de configuración. | Propósito autorizante, decisor competente y efecto de autorización. No es L3. |
| [`notebook_registry.py`](../src/study_engine/federation/notebook_registry.py) | `DEFAULT_NOTEBOOKS[].sources`; set cotejado en CP079. | Declaración de registry versionada; no es acto de aprobación. | Los cinco notebooks del release. | Seis asociaciones persistidas de Fase 0 están declaradas en R sin role U; las otras relaciones con R+U se registran bajo la fila anterior. | Declaración de scope/lista de fuentes. | No identificado. | No declara grant; es configuración. | Notebook/source declarados para las seis relaciones R-only. | Propósito autorizante, decisor y efecto de aprobación. No es L3. |

Estas configuraciones se registran como `PARTIAL` únicamente en el sentido
documental definido por CP085: muestran una declaración técnica
relación-específica. No se elevan a autorización. Las 76 entradas U y las seis
entradas R-only representan 82 asociaciones.

### 3.3 Decisiones humanas de benchmark sobre qrels/scopes

Se revisaron el registro de decisiones Gate 2 y los paquetes adjudicados v2.402,
incluidos [`gate2_v2400_explicit_decision_register_2026-09-28.json`](../reports/gate2_v2400_explicit_decision_register_2026-09-28.json),
[`gate2_scope_candidate_adjudication_2026-09-28.json`](../reports/gate2_scope_candidate_adjudication_2026-09-28.json)
y los paquetes de decisiones v2.402 referenciados por ellos.

| DOCUMENT | LOCATION | DATE/VERSION | NOTEBOOK/SCOPE | SOURCE/S | PURPOSE | DECISOR | EXPLICIT_EFFECT | L3_ELEMENTS_COVERED | L3_ELEMENTS_MISSING |
|---|---|---|---|---|---|---|---|---|---|
| Registros de adjudicación de Gate 2 | decisiones por `query_id`, `chunk_id`, grado/qrel y scope de consulta. | v2.402; fechados en los artefactos del 2026-09-28. | Algunos casos nombran `fadena-so2`, `fadena-std`, `fadena-lenguajes` u otros scopes. | Identifican chunks, no necesariamente el source ID/versionado aprobado. | Adjudicar pertinencia/relevancia semántica de evidencia para una consulta del benchmark. | `user` o reviewer identificado para la decisión de qrel. | Aprueba o excluye un qrel/chunk para el benchmark; no concede uso de una relación source/notebook. Los manifiestos declaran `acl_modified=false` o la ACL fuera de alcance. | En ciertos casos: scope de consulta, chunk y decisor para la decisión semántica del qrel. | Source/scoped grant como objeto; identidad/versionado source; propósito de uso curricular; efecto explícito de autorización de fuente. No es evidencia L3 para las relaciones Gate B. |

Las decisiones de qrel no se extrapolan a autorizaciones de source/ACL, aunque
el query tenga un scope igual al notebook del release. Se refieren a otra
pregunta: relevancia de un pasaje para una consulta, no permiso para que una
fuente forme parte del release.

### 3.4 Identidad, auditoría y documentación histórica

| DOCUMENT | LOCATION | DATE/VERSION | NOTEBOOK/SCOPE | SOURCE/S | PURPOSE | DECISOR | EXPLICIT_EFFECT | L3_ELEMENTS_COVERED | L3_ELEMENTS_MISSING |
|---|---|---|---|---|---|---|---|---|---|
| [`notebook_identity_decisions.json`](../config/notebook_identity_decisions.json) | Objeto `purpose` y `decisions` por notebook. | `version: 1`; audit-only. | Identifica varios notebooks, incluidos los cinco. | No contiene grants por source/scope. | Resolver identidad, clasificación y alias. | No registra decisor de grant. | Declara expresamente que no concede acceso y no es leído por la autorización runtime. | Identidad del notebook y decisiones de alias/clasificación. | Source, propósito de uso de source, decisor competente y efecto autorizante. Excluido como grant. |
| [`audit_diagnostico.md`](../docs/audit_diagnostico.md) | Auditoría diagnóstica histórica; métricas por fuente y notas de retrieval/ACL. | Snapshot histórico; su propia nota remite a fuentes normativas vigentes distintas. | Algunos scopes/sources aparecen en métricas y ejemplos. | IDs de source aparecen como unidades de auditoría. | Diagnóstico técnico, conteos y evaluación de cobertura/calidad. | No emite decisiones de autorización por source/notebook. | No concede ACL; métricas “OK” o conteos no son aprobación. | Referencias parciales a identidad/source o medición técnica. | Decisión L3 por relación, decisor y efecto autorizante. No es L3. |
| [`GATE2_GENERATOR_IMPLEMENTATION_PLAN.md`](../docs/GATE2_GENERATOR_IMPLEMENTATION_PLAN.md) | Entradas permitidas, contrato del dataset y fases de decisión de queries/qrels. | Plan de implementación; estado/piloto fechado 2026-09-28. | Define scopes de consultas de benchmark, no autorización de las 99 parejas. | Puede mencionar IDs de source/chunks como evidencia de qrels. | Generación/adjudicación de benchmark y qrels bajo ACL existente. | Reviewer/revisor de benchmark según artefactos de decisión. | No modifica la ACL activa; cambios de scope exigen decisión curricular para el benchmark. | Propósito del benchmark y algunas decisiones por query. | Grant source/notebook L3 y su efecto. No es autorización de las relaciones. |
| [`DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md`](../docs/DIAGNOSTICO_MULTICUADERNO_Y_PLAN_DE_CONTINUIDAD.md), CP077–084 | Decisiones de identidad, inventarios y conclusiones de Gate B. | Diferentes snapshots/checkpoints; CP084 aplica L3. | Scope de cinco notebooks y sus relaciones. | Inventarios R/U/P; CP084 lista las 99 relaciones. | Reconciliación, diagnóstico y clasificación de evidencia. | CP077/083 registran decisiones humanas de scope/umbral; no decisión positiva source-scoped. | Determina que la autorización no está demostrada; no concede ni cambia ACL. | Identidad/scope, evidencia de configuración, estado de las asociaciones y resultado negativo de búsqueda L3. | Decisión positiva L3 y efecto autorizante; por diseño estos artefactos no crean autorizaciones. |

## 4. Clasificación de cada relación del release

Esta tabla repite el universo de CP084 y agrega el resultado de búsqueda
documental. Las categorías `PARTIAL` y `NOT_FOUND` aquí **no cambian** el
resultado normativo L3: las 99 siguen `NOT_DEMONSTRATED`.

- `PARTIAL`: existe declaración R/U relación-específica sin decisión
  autorizante; para las dos P-only de STD indicadas, además existe evaluación
  C4-DRAFT específica que no autoriza.
- `NOT_FOUND`: no se encontró otro documento source/scope-específico que cubra
  esa relación; queda la asociación técnica P observada, que no cuenta como
  decisión documental.
- Ninguna relación es `FOUND`: no se encontró evidencia L3 completa.

### SCOPE-01 — `fase0-soc`

| notebook_id | source_id | L3_EXISTING_EVIDENCE | razón |
|---|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_0bc5d20dcc91895f` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_0fc90b2695369475` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_a9a056742dcf69ae` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fase0-soc` | `src_d253687930308e41` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_e9682dece40b58ab` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_fadena_prog_arboles` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_fadena_prog_archivos` | NOT_FOUND | Solo P para esta pareja; el expediente C4 de STD no se extrapola a Fase 0. |
| `fase0-soc` | `src_fadena_prog_lineales` | NOT_FOUND | Solo P; sin declaración R/U ni decisión documental por pareja. |
| `fase0-soc` | `src_fadena_prog_punteros` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fase0-soc` | `src_fadena_so_concurrencia` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_fadena_so_memoria` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_fadena_so_planificacion` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_fadena_so_procesos` | PARTIAL | R declara source/scope; no grant L3. |
| `fase0-soc` | `src_goodrich_dsa_python` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fase0-soc` | `src_joyanes_fundamentos` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fase0-soc` | `src_kurose_computer_networking` | NOT_FOUND | Solo P; no se extiende la declaración de Teleco a Fase 0. |
| `fase0-soc` | `src_martin_clean_code` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fase0-soc` | `src_ramalho_fluent_python` | NOT_FOUND | Solo P; la declaración/valoración para STD no se extiende a Fase 0. |
| `fase0-soc` | `src_rosen_matematicas_discretas` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fase0-soc` | `src_stallings_computer_security` | NOT_FOUND | Solo P; las declaraciones en otros notebooks no autorizan esta relación. |
| `fase0-soc` | `src_stallings_os_internals_7ed` | NOT_FOUND | Solo P; declaración/role de SO II no se extiende a Fase 0. |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | PARTIAL | R/U declaran source y role; no grant L3. |

### SCOPE-02 — `fadena-lenguajes`

| notebook_id | source_id | L3_EXISTING_EVIDENCE | razón |
|---|---|---|---|
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | NOT_FOUND | Solo P; no se extiende a Lenguajes una asociación de Fase 0. |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | NOT_FOUND | Solo P para esta pareja; el expediente C4 de STD no se extrapola a Lenguajes. |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | PARTIAL | R/U declaran source y role; no grant L3. |

### SCOPE-03 — `fadena-so2`

| notebook_id | source_id | L3_EXISTING_EVIDENCE | razón |
|---|---|---|---|
| `fadena-so2` | `src_0bc5d20dcc91895f` | NOT_FOUND | Solo P; la nota de reemplazo/role de otra edición no es autorización de esta relación. |
| `fadena-so2` | `src_0fc90b2695369475` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-so2` | `src_a9a056742dcf69ae` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-so2` | `src_d253687930308e41` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-so2` | `src_e9682dece40b58ab` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-so2` | `src_fadena_so2_clase1` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_fadena_so2_clase2` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_fadena_so_concurrencia` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_fadena_so_memoria` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_fadena_so_planificacion` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_fadena_so_procesos` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_stallings_computer_security` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-so2` | `src_stallings_os_internals_7ed` | PARTIAL | R/U declaran source y role; no grant L3. |

### SCOPE-04 — `fadena-std`

| notebook_id | source_id | L3_EXISTING_EVIDENCE | razón |
|---|---|---|---|
| `fadena-std` | `src_032c52bff94a0743` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_0960283d5cef8dee` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_3102eb1e89e2229e` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_3e2e8abda5f55c17` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_52ff5ff3e07c1da5` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_53ef2a7243ae3f63` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_56cfdbe35123c49e` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_6dbdc8e943261fa7` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_755be6c147ddc5dd` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_7822bc3cef85c783` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_7ec00a3365f208e6` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_9946be0e7d11161a` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_9e866bf082e52dd7` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_a01b9809f37fb47b` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_cf46d8f0e018b09e` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_coronel_database_systems_11ed` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-std` | `src_d7ff8399759d387a` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_d946d1a5a3c32144` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-std` | `src_de275591245abbd3` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-std` | `src_f3352475bc0cd360` | PARTIAL | P-only, pero C4-DRAFT lo trata explícitamente por scope/source; estado pedagógico pendiente, no grant. |
| `fadena-std` | `src_f93b8a264e20359c` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-std` | `src_fadena_prog_archivos` | PARTIAL | R/U declaran source y role; además existe evaluación C4-DRAFT source-scoped sin grant. |
| `fadena-std` | `src_fadena_std_unidad1` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-std` | `src_marques_bases_de_datos` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | PARTIAL | R/U declaran source y role; C4-DRAFT indica decisión de política pendiente, no grant. |
| `fadena-std` | `src_ramalho_fluent_python` | PARTIAL | R/U declaran source y role; C4-DRAFT documenta evidencia incompleta, no grant. |
| `fadena-std` | `src_rosen_matematicas_discretas` | PARTIAL | P-only, pero C4-DRAFT lo trata explícitamente por scope/source; estado unresolved, no grant. |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | PARTIAL | R/U declaran source y role; no grant L3. |

### SCOPE-05 — `fadena-teleco`

| notebook_id | source_id | L3_EXISTING_EVIDENCE | razón |
|---|---|---|---|
| `fadena-teleco` | `src-guia-2025-c04f44ef` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_001b27137cf6680c` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-teleco` | `src_11195af8e0f2ef40` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_corletti_seguridad_redes` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_da10b53f20f2a647` | PARTIAL | U declara role por source/scope; no grant L3. |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_kurose_computer_networking` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_stallings_computer_security` | PARTIAL | R/U declaran source y role; no grant L3. |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | PARTIAL | R/U declaran source y role; no grant L3. |

## 5. Resumen por scope y diferencia frente a CP084

| notebook_id | asociaciones | PARTIAL | NOT_FOUND | FOUND |
|---|---:|---:|---:|---:|
| `fase0-soc` | 26 | 14 | 12 | 0 |
| `fadena-lenguajes` | 17 | 15 | 2 | 0 |
| `fadena-so2` | 14 | 13 | 1 | 0 |
| `fadena-std` | 30 | 30 | 0 | 0 |
| `fadena-teleco` | 12 | 12 | 0 | 0 |
| **Total** | **99** | **84** | **15** | **0** |

`L3_EXISTING_EVIDENCE=PARTIAL` identifica material que documenta parcialmente
la relación, no una autorización incompleta que pueda usarse como grant. En
concreto:

- 82 relaciones tienen declaración técnica versionada R o U;
- dos relaciones P-only de `fadena-std` tienen evaluación C4-DRAFT específica;
- 15 relaciones P-only no tienen documentación source/scope-específica
  identificada;
- cero relaciones tienen decisión L3 completa.

## 6. Efecto sobre C2 y siguiente acción mínima

La búsqueda cierra la pregunta “¿ya existe en el repositorio una autorización
L3 que no se haya incorporado a CP084?”: no. Ninguna evidencia candidata
permite cambiar `L3_NOT_DEMONSTRATED` a `DEMONSTRATED`. El único siguiente
paso que permitiría cambiar ese resultado es disponer de una decisión
documental explícita con los elementos L3 para las relaciones que el release
pretenda presentar como autorizadas, o redefinir explícitamente el conjunto de
relaciones cubiertas por el claim de release. CP085 no genera esa decisión, no
pide una nueva decisión humana y no propone cambios de implementación.

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
L3_UNKNOWN = 0
AUTHORIZATION_PROVENANCE_STATUS = NOT_DEMONSTRATED
CRITERION_2 = BLOCKED
```

## 7. No-acciones

No se creó autorización ni se modificaron DB, ACL, asociaciones, roles,
registry, catálogo, perfiles, `curriculum_id`, retrieval, SectionExpander,
código, fixtures, corpus, embeddings o modelos. No se ejecutaron
TALOS/FastAPI, tests, benchmarks, providers, workloads ni migraciones. No se
reparó la FK observada en CP082 ni se alteró la frontera de expansión. Los
estados de CP084 permanecen sin cambio.

## Cierre requerido

```text
L3_EXISTING_EVIDENCE_FOUND = PARTIAL
RELATIONS_WITH_EXISTING_L3_EVIDENCE = 84
RELATIONS_WITHOUT_EXISTING_L3_EVIDENCE = 15
NEW_AUTHORIZATION_CREATED = NO
TECHNICAL_STATE_MODIFIED = NO
```
