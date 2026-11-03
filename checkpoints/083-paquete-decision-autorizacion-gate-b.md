# CP083 — paquete de decisión humana para autorización de Gate B

## 1. Propósito y estado que no se modifica

Este expediente convierte la evidencia ya reconciliada en CP077–082 en una
decisión pendiente de la persona responsable del producto. No repite
arqueología, no adjudica relaciones y no decide por esa persona.

El objeto decisional son las relaciones técnicas `notebook_id → source_id`
existentes en la allowlist persistida de los cinco currículos del release:
¿qué autoridad permite que cada pareja se use para el scope y propósito del
release? La decisión debe distinguir disponibilidad técnica, configuración y
declaración de una aprobación humana o de autoridad curricular.

El conjunto ya fijado por decisión humana es:

| Notebook ID | Scope de release |
|---|---|
| `fase0-soc` | Fase 0 — Programación y Pensamiento Algorítmico |
| `fadena-lenguajes` | FADENA Lenguajes 2026 |
| `fadena-so2` | FADENA Sistemas Operativos II 2026 |
| `fadena-std` | FADENA Sistema de Tratamiento de Datos 2026 |
| `fadena-teleco` | FADENA Telecomunicaciones 2025 |

```text
RELEASE_SCOPE = 5
FADENA_STD_RELEASE_SCOPE = INCLUDED

CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED

AUTHORIZATION_PROVENANCE_STATUS = UNKNOWN
DOCUMENT_SOURCE_CARDINALITY = UNKNOWN
CURRENT_DATA_CROSS_SOURCE_MIXING = NOT_OBSERVED
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
Q2 = OBSERVED_CONSISTENT
FK_INTEGRITY = FAIL (una violación fuera del dominio document/chunk/source)
```

Los estados anteriores se copian como evidencia de contexto, no se actualizan
ni reinterpretan aquí.

## 2. Qué está técnicamente habilitado y qué está aprobado

| Capa | Evidencia alcanzada | Efecto/autoridad exactos |
|---|---|---|
| Configuración técnica | Registry `DEFAULT_NOTEBOOKS` (`R`) y `notebook_source_roles.json` (`U`) contienen declaraciones versionadas; código de inicialización puede derivar asociaciones desde registry. | Declaran configuración y roles. No son por sí solos decisiones de aprobación. |
| Declaración de scope | `R` enumera sources para notebooks; `U` declara rol(es) para sources por notebook. | Documenta lo que las configuraciones expresan. No prueba que alguien con autoridad aprobó el uso para release. |
| Rol de fuente | 76 asociaciones persistidas tienen al menos un role versionado en `U`. | Etiqueta el tipo/uso previsto de evidencia. `authority` numérico de la configuración también es un peso declarativo, no autoridad institucional. |
| Allowlist efectiva | Las 99 asociaciones `P` de `notebook_sources` son el estado técnico persistido; CP079 documenta que el chat las consume como allowlist. | Permite técnicamente el acceso en esta instalación. Prueba `PRESENT`, no quién autorizó ni para qué propósito. |
| Disponibilidad | CP079 encontró source record para todos los 99 IDs de `P`. | Prueba que existe una fila de registro de fuente. No prueba que haya documentos/chunks legibles, OCR suficiente, contenido completo o calidad. |
| Autorización humana | CP077–082 no encontraron aprobación positiva scoped por notebook/source/propósito/versión. | `DIRECT_APPROVAL = 0/99`; `AUTHORIZATION_EVIDENCE` no contiene grant demostrado. No puede afirmarse que las relaciones estén autorizadas ni que estén rechazadas. |
| Autoridad académica/institucional | No se demostró autoridad curricular independiente para las relaciones ni para `fadena-std`. | Desconocida; no se deriva de nombre, rol, source record, `curriculum_id` ni asociación. |

Así, a la pregunta “¿qué está autorizado técnicamente?” la respuesta precisa
es: el estado `P` de esta instalación constituye la allowlist que el chat usa
técnicamente, según CP079. A “¿qué está realmente aprobado?”: ninguna de las
99 parejas tiene aprobación positiva demostrada en la evidencia revisada. Esto
no equivale a una denegación.

## 3. Convenciones del inventario de 99 relaciones

El inventario completo siguiente parte de los sets `R`, `U`, `P`, conteos y
source-record availability ya reconciliados en CP079. Los nombres de roles
repiten literalmente las etiquetas versionadas declaradas en `U`; no se
interpreta su semántica curricular.

- `R=Y`: source declarado en `DEFAULT_NOTEBOOKS` del notebook.
- `U`: roles declarados en `notebook_source_roles.json`; `—` significa que no
  hay entrada de role para esa pareja.
- `P=PRESENT`: asociación existente en `notebook_sources`.
- `SOURCE_RECORD=PRESENT`: source record presente según CP079; esto no
  establece disponibilidad de contenido.
- `AUTHORIZATION_EVIDENCE` clasifica sólo la evidencia disponible, no el
  estado de autorización:
  - `VERSIONED_ROLE`: role versionado para esa relación;
  - `TECHNICAL_DECLARATION`: aparece en registry `R` pero no tiene role `U`;
  - `NONE`: no existe declaración R/U para una asociación P-only.
- En todas las filas, `DIRECT_APPROVAL=NONE` y
  `AUTHORIZATION_STATUS=UNDETERMINED`. No se encontró decisión que otorgue
  autorización a una relación.

### 3.1 SCOPE-01 — `fase0-soc` (26 relaciones P)

| notebook_id | source_id | R | U / role(s) | P | source record | AUTHORIZATION_EVIDENCE | decisión |
|---|---|---:|---|---|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_0bc5d20dcc91895f` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_0fc90b2695369475` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_a9a056742dcf69ae` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_d253687930308e41` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_e9682dece40b58ab` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_prog_arboles` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_prog_archivos` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_prog_lineales` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_prog_punteros` | Y | IMPLEMENTATION, REFERENCE | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_so_concurrencia` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_so_memoria` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_so_planificacion` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_fadena_so_procesos` | Y | — | PRESENT | PRESENT | TECHNICAL_DECLARATION | NONE; UNDETERMINED |
| `fase0-soc` | `src_goodrich_dsa_python` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_joyanes_fundamentos` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_kurose_computer_networking` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_martin_clean_code` | Y | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_ramalho_fluent_python` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_rosen_matematicas_discretas` | Y | FORMAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | Y | METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fase0-soc` | `src_stallings_computer_security` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_stallings_os_internals_7ed` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |

### 3.2 SCOPE-02 — `fadena-lenguajes` (17 relaciones P)

| notebook_id | source_id | R | U / role(s) | P | source record | AUTHORIZATION_EVIDENCE | decisión |
|---|---|---:|---|---|---|---|---|
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | — | REFERENCE | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | Y | PRIMARY, METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | Y | METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | Y | METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | Y | REFERENCE | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |

### 3.3 SCOPE-03 — `fadena-so2` (14 relaciones P)

| notebook_id | source_id | R | U / role(s) | P | source record | AUTHORIZATION_EVIDENCE | decisión |
|---|---|---:|---|---|---|---|---|
| `fadena-so2` | `src_0bc5d20dcc91895f` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fadena-so2` | `src_0fc90b2695369475` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_a9a056742dcf69ae` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_d253687930308e41` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_e9682dece40b58ab` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so2_clase1` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so2_clase2` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so_concurrencia` | Y | PRIMARY, METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so_memoria` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so_planificacion` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_fadena_so_procesos` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_stallings_computer_security` | Y | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-so2` | `src_stallings_os_internals_7ed` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |

### 3.4 SCOPE-04 — `fadena-std` (30 relaciones P)

| notebook_id | source_id | R | U / role(s) | P | source record | AUTHORIZATION_EVIDENCE | decisión |
|---|---|---:|---|---|---|---|---|
| `fadena-std` | `src_032c52bff94a0743` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_0960283d5cef8dee` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_3102eb1e89e2229e` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_3e2e8abda5f55c17` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_52ff5ff3e07c1da5` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_53ef2a7243ae3f63` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_56cfdbe35123c49e` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_6dbdc8e943261fa7` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_755be6c147ddc5dd` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_7822bc3cef85c783` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_7ec00a3365f208e6` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_9946be0e7d11161a` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_9e866bf082e52dd7` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_a01b9809f37fb47b` | — | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_cf46d8f0e018b09e` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_coronel_database_systems_11ed` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_d7ff8399759d387a` | — | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_d946d1a5a3c32144` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | Y | FORMAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_de275591245abbd3` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_f3352475bc0cd360` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fadena-std` | `src_f93b8a264e20359c` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_fadena_prog_archivos` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_fadena_std_unidad1` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_marques_bases_de_datos` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_ramalho_fluent_python` | Y | IMPLEMENTATION | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-std` | `src_rosen_matematicas_discretas` | — | — | PRESENT | PRESENT | NONE | NONE; UNDETERMINED |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |

### 3.5 SCOPE-05 — `fadena-teleco` (12 relaciones P)

| notebook_id | source_id | R | U / role(s) | P | source record | AUTHORIZATION_EVIDENCE | decisión |
|---|---|---:|---|---|---|---|---|
| `fadena-teleco` | `src-guia-2025-c04f44ef` | Y | METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_001b27137cf6680c` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_11195af8e0f2ef40` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | Y | FORMAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_corletti_seguridad_redes` | Y | COMPLEMENTARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_da10b53f20f2a647` | — | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_kurose_computer_networking` | Y | PRIMARY, METHODOLOGICAL | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_stallings_computer_security` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | Y | PRIMARY | PRESENT | PRESENT | VERSIONED_ROLE | NONE; UNDETERMINED |

Comprobación aritmética del inventario: `26 + 17 + 14 + 30 + 12 = 99`
relaciones `P`; 76 tienen `U`, 6 tienen `R` pero no `U`, y 17 son `P` sin
declaración `R` ni role `U`. No hay `DIRECT_APPROVAL` en ninguna de las 99.

## 4. Excepciones y relaciones incompletas de configuración

### 4.1 `P−U`: persistidas sin role

Hay 23 relaciones persistidas sin role: 6 tienen declaración en `R` y 17 no
están en `R` ni `U`. Ninguna está clasificada como no autorizada; la
autorización permanece `UNDETERMINED`.

| notebook_id | source_id | R | posible origen técnico ya documentado | evidencia de autorización |
|---|---|---:|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | Y | Sólo instalación más declaración registry; CP079 señala preservación de asociaciones existentes y pertinencia pendiente para parte de Fase 0. | NONE |
| `fase0-soc` | `src_0bc5d20dcc91895f` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_0fc90b2695369475` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_a9a056742dcf69ae` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_d253687930308e41` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_e9682dece40b58ab` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_fadena_prog_arboles` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_fadena_prog_archivos` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_fadena_prog_lineales` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_fadena_so_concurrencia` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_fadena_so_memoria` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_fadena_so_planificacion` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_fadena_so_procesos` | Y | Registry más instalación; sin role Fase 0. | NONE |
| `fase0-soc` | `src_kurose_computer_networking` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_ramalho_fluent_python` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_stallings_computer_security` | — | Sólo instalación; origen no registrado. | NONE |
| `fase0-soc` | `src_stallings_os_internals_7ed` | — | Sólo instalación; origen no registrado. | NONE |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | — | Sólo instalación; CP079 registra origen/carpeta no confirmados. | NONE |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | — | Sólo instalación; CP079 registra origen/carpeta no confirmados. | NONE |
| `fadena-so2` | `src_0bc5d20dcc91895f` | — | Sólo instalación; CP079 documenta una edición antigua reemplazada en la clasificación de role, no decisión de ACL. | NONE |
| `fadena-std` | `src_f3352475bc0cd360` | — | Sólo instalación; CP079 identifica tratamiento pedagógico/ACL pendiente para material de soluciones. | NONE |
| `fadena-std` | `src_rosen_matematicas_discretas` | — | Sólo instalación; CP079 registra provenance específica pendiente. | NONE |

Las decisiones de preservar o dejar pendiente son `DOCUMENTED_DECISION` sobre
el tratamiento del estado, no decisiones que otorguen uso. CP079 deja la
autoridad ACL de `fadena-std` pendiente para sus 30/30 asociaciones.

### 4.2 `R−U`: registry sin role

Estas seis parejas están declaradas en registry, no tienen role y sí están
persistidas:

| notebook_id | source_id | REGISTRY_DECLARATION | ROLE_DECLARATION | PERSISTED_ASSOCIATION | autorización |
|---|---|---|---|---|---|
| `fase0-soc` | `src_0fc90b2695369475` | YES | NO | PRESENT | UNDETERMINED |
| `fase0-soc` | `src_d253687930308e41` | YES | NO | PRESENT | UNDETERMINED |
| `fase0-soc` | `src_fadena_so_concurrencia` | YES | NO | PRESENT | UNDETERMINED |
| `fase0-soc` | `src_fadena_so_memoria` | YES | NO | PRESENT | UNDETERMINED |
| `fase0-soc` | `src_fadena_so_planificacion` | YES | NO | PRESENT | UNDETERMINED |
| `fase0-soc` | `src_fadena_so_procesos` | YES | NO | PRESENT | UNDETERMINED |

La ausencia de role no se interpreta como denegación ni como permiso.

### 4.3 `U−P`: roles declarados que no están asociados

| notebook_id | source_id | INTENDED_DECLARATION | PERSISTED_ASSOCIATION | disponibilidad/status ya documentado | autorización |
|---|---|---|---|---|---|
| `fase0-soc` | `src_tori_hacking_etico` | YES | NO | Source record presente; role declarado pero no provisionado, motivo no adjudicado (`UNKNOWN`). | NONE |
| `fadena-so2` | `src_rudareanu_linux_sysadmins` | YES | NO | `SOURCE_MISSING`; sin source record. | NONE |
| `fadena-so2` | `src_silberschatz_so_7ed` | YES | NO | `SOURCE_MISSING`; sin source record. | NONE |
| `fadena-so2` | `src_tanenbaum_so_modernos_3ed` | YES | NO | `SOURCE_MISSING`; sin source record. | NONE |
| `fadena-std` | `src_cairo_guardati_estructuras_datos` | YES | NO | `SOURCE_MISSING`; sin source record. | NONE |
| `fadena-teleco` | `src_tanenbaum_computer_networks` | YES | NO | `SOURCE_MISSING`; sin source record. | NONE |

`INTENDED_DECLARATION` no crea una asociación ni otorga acceso. No se crean
asociaciones como parte de este expediente.

## 5. Las 23 fuentes con asociaciones cross-scope

Los scopes enumerados abajo son aquellos donde el source aparece en `P`.
`R/U` resume la evidencia declarativa ya reconciliada para esa pareja: `R`,
`U(role)` o `P-only`. La columna final aplica a cada relación individual de
ese source en cada scope.

| source_id | scopes donde está P y evidencia por scope | aprobación demostrada por relación |
|---|---|---|
| `src-guia-2025-c04f44ef` | `fase0-soc`: P-only; `fadena-teleco`: R + U(`METHODOLOGICAL`) | NONE |
| `src_0bc5d20dcc91895f` | `fase0-soc`: P-only; `fadena-so2`: P-only | NONE |
| `src_0fc90b2695369475` | `fase0-soc`: R; `fadena-so2`: U(`PRIMARY`) | NONE |
| `src_a9a056742dcf69ae` | `fase0-soc`: P-only; `fadena-so2`: U(`PRIMARY`) | NONE |
| `src_d253687930308e41` | `fase0-soc`: R; `fadena-so2`: U(`PRIMARY`) | NONE |
| `src_e9682dece40b58ab` | `fase0-soc`: P-only; `fadena-so2`: U(`IMPLEMENTATION`) | NONE |
| `src_f009c4e75f5ca3f2` | `fase0-soc`: P-only; `fadena-so2`: U(`IMPLEMENTATION`) | NONE |
| `src_fadena_prog_arboles` | `fase0-soc`: P-only; `fadena-lenguajes`: P-only | NONE |
| `src_fadena_prog_archivos` | `fase0-soc`: P-only; `fadena-lenguajes`: P-only; `fadena-std`: R + U(`PRIMARY`) | NONE |
| `src_fadena_prog_lineales` | `fase0-soc`: P-only; `fadena-lenguajes`: R + U(`PRIMARY`) | NONE |
| `src_fadena_prog_punteros` | `fase0-soc`: R + U(`IMPLEMENTATION`,`REFERENCE`); `fadena-lenguajes`: R + U(`COMPLEMENTARY`) | NONE |
| `src_fadena_so_concurrencia` | `fase0-soc`: R; `fadena-so2`: R + U(`PRIMARY`,`METHODOLOGICAL`) | NONE |
| `src_fadena_so_memoria` | `fase0-soc`: R; `fadena-so2`: R + U(`COMPLEMENTARY`) | NONE |
| `src_fadena_so_planificacion` | `fase0-soc`: R; `fadena-so2`: R + U(`PRIMARY`) | NONE |
| `src_fadena_so_procesos` | `fase0-soc`: R; `fadena-so2`: R + U(`PRIMARY`) | NONE |
| `src_joyanes_fundamentos` | `fase0-soc`: R + U(`PRIMARY`); `fadena-lenguajes`: R + U(`PRIMARY`,`METHODOLOGICAL`) | NONE |
| `src_kurose_computer_networking` | `fase0-soc`: P-only; `fadena-teleco`: R + U(`PRIMARY`,`METHODOLOGICAL`) | NONE |
| `src_ramalho_fluent_python` | `fase0-soc`: P-only; `fadena-std`: R + U(`IMPLEMENTATION`) | NONE |
| `src_rosen_matematicas_discretas` | `fase0-soc`: R + U(`FORMAL`); `fadena-std`: P-only | NONE |
| `src_spraul_think_like_a_programmer` | `fase0-soc`: R + U(`METHODOLOGICAL`); `fadena-lenguajes`: R + U(`METHODOLOGICAL`) | NONE |
| `src_stallings_computer_security` | `fase0-soc`: P-only; `fadena-so2`: R + U(`IMPLEMENTATION`); `fadena-teleco`: R + U(`PRIMARY`) | NONE |
| `src_stallings_os_internals_7ed` | `fase0-soc`: P-only; `fadena-so2`: R + U(`PRIMARY`) | NONE |
| `src_sweigart_automate_boring_stuff` | `fase0-soc`: R + U(`COMPLEMENTARY`); `fadena-lenguajes`: R + U(`COMPLEMENTARY`) | NONE |

Son 23 IDs compartidos que abarcan 48 relaciones. Que el mismo ID aparezca en
varios scopes no demuestra contaminación ni autoriza/rechaza ninguno de ellos.
No se evalúa aquí si una fuente “tiene sentido” en una materia; la decisión
pendiente es si cada relación está aprobada para ese scope.

## 6. Autoridad de `fadena-std`

```text
FADENA_STD_RELEASE_SCOPE = INCLUDED
FADENA_STD_AUTHORITY_STATUS = UNRESOLVED
```

Son preguntas distintas:

| Dimensión | Evidencia y estado |
|---|---|
| Source/ACL authorization | 30 asociaciones `P`; 28 tienen role versionado y 2 son P-only. CP080/081 no encontraron grants positivos para ninguna; autorización de las 30 = `UNDETERMINED`. |
| Identidad técnica curricular | CP078 encontró `curriculum_id` esperado `fadena_std_2026` frente a `fadena_v1` persistido; `CURRICULUM_ID_STATUS = CONTRADICTORY`. Esta discrepancia sigue abierta y este expediente no la reinterpreta. |
| Autoridad académica/institucional | Sigue sin demostrarse para el programa curricular de STD. `fadena_v1`, la presencia de fuentes y sus roles no son sustitutos de esa autoridad. |
| Decisión humana de scope | `fadena-std` permanece incluido por decisión humana previa del release. Su inclusión no concede authority ni ACL. |

Por tanto, decidir el umbral de evidencia para autorizar las parejas source/ACL
no resolverá automáticamente la identidad `curriculum_id` ni la autoridad
académica de STD.

## 7. Findings técnicos separados de la decisión de autorización

### 7.1 Frontera de expansión

CP082 inspeccionó la base local en `mode=ro`/`query_only`: 115 documentos,
105705 chunks, 112 documentos con chunks, 3 sin chunks; cero mismatches
`documents.source_id`/`chunks.source_id` y cero documentos con múltiples
chunk sources. Resultado:

```text
Q2 = OBSERVED_CONSISTENT
CURRENT_DATA_CROSS_SOURCE_MIXING = NOT_OBSERVED
STRUCTURAL_GUARANTEE = NOT_DEMONSTRATED
EXPANSION_SOURCE_BOUNDARY = UNKNOWN
```

CP081 encontró que los expansores consultan por `document_id` sin filtro
`source_id` de semilla ni post-filter source-scoped. Así, no hay evidencia de
contaminación en la instalación inspeccionada, pero tampoco garantía
estructural de que nunca ocurra. Este punto técnico no es una decisión de
autorización y no cambia C2.

### 7.2 Hallazgo de integridad referencial

```text
FINDING_ID = FK-NOTEBOOK-SOURCES-001
STATUS = OPEN
SCOPE = OUTSIDE_DOCUMENT_CHUNK_SOURCE_ANALYSIS
```

CP082 registró exactamente:

```text
notebook_sources
rowid 47
→ sources
FK 0
```

Es una violación referencial independiente. CP083 no investigó causa ni
identidad del source, no la reparó, no la interpreta como ACL incorrecta y no
la usa para alterar C1/C2. Podrá ser objeto de un checkpoint específico si se
decide continuar con ese análisis.

## 8. Decisión humana pendiente: nivel de evidencia de C2

Pregunta que debe resolver la persona responsable del producto:

> **¿Qué nivel de evidencia acepta como suficiente para considerar autorizada
> una relación `notebook_id → source_id` para este release?**

| Nivel | Evidencia mínima | Claim que puede sostener | Claim que no sostiene por sí solo |
|---|---|---|---|
| `L0` | Asociación `P` observada en instalación. | “Está habilitada en la allowlist técnica de esta instalación.” | No sostiene declaración versionada, aprobación humana ni autoridad académica externa. |
| `L1` | Declaración versionada `R`/configuración de scope. | “El registry/config versionado declara esta relación.” | No prueba grant, aprobación humana ni autoridad académica externa. |
| `L2` | `R` más role `U` versionado para la relación. | “El scope y el rol están declarados de forma versionada.” | No prueba que una autoridad humana aprobó el uso; no es autoridad académica externa. |
| `L3` | Decisión documental explícita por notebook, source (y versión), propósito, decisor y efecto. | “La decisión registrada autoriza explícitamente esta relación para el alcance declarado”, si el decisor tiene la competencia que acepta el producto. | No prueba autoridad externa distinta ni validez académica más allá del alcance de la decisión. |
| `L4` | Aprobación verificable de autoridad externa/institucional competente, con scope y vigencia. | “La autoridad externa/institucional identificada aprobó el uso dentro de ese scope.” | No prueba comportamiento técnico de ACL/retrieval ni aislamiento E2E. |

Ningún nivel se elige en CP083. `L0`, `L1` y `L2` describen estado/configuración
técnica; no deben presentarse como autoridad académica externa.

## 9. Alternativas decisionales sin recomendación

La siguiente matriz expone consecuencias, no selecciona ni ordena opciones.

| Decisión | Qué significa | Evidencia/acto requerido | Efecto sobre C2 y el release |
|---|---|---|---|
| Aceptar declaración versionada como autorización de release | El responsable decide que cierta combinación de `R`/`U` satisface el umbral interno. | Decisión humana explícita que identifique nivel, alcance, relaciones cubiertas y decisor; no modificar los artefactos técnicos en este checkpoint. | Permite reconsiderar C2 bajo esa convención, pero no constituye por sí sola autoridad académica externa ni resuelve expansión/fallas técnicas. |
| Exigir autorización documental por source/scope | Cada pareja necesita decisión explícita y trazable antes de contarse como autorizada. | Documento/decisión por relación con source, notebook, versión, propósito, estado y autoridad. | C2 permanece bloqueado hasta obtener y cotejar las decisiones aplicables. |
| Excluir relaciones no autorizadas del release | Se reduce el conjunto de asociaciones que el release pretende afirmar. | Decisión humana expresa que enumere las parejas excluidas y revise el scope afectado. | Requiere recalcular C2 para el scope/release modificado; no borra implementación ni cambia la allowlist automáticamente. |
| Mantener las cinco scopes y asociaciones como provisionales | Se permite continuar trabajo técnico sin afirmar aprobación para release. | Decisión humana que registre el carácter provisional y sus límites. | No permite cerrar C2 ni hacer claim de autorización de release. |

No se recomienda una alternativa. Las decisiones de scope e inclusión
existentes, incluida la de `fadena-std`, no se modifican implícitamente por
elegir un umbral probatorio.

## 10. Qué falta y qué no puede concluirse

Falta la decisión explícita sobre el umbral de C2 y el acto/documento trazable
correspondiente según el nivel que se elija. Si se requiere aprobación
relacional, deberá identificar qué parejas de las 99 quedan cubiertas; la
presencia en los cuadros de este paquete no concede ni sugiere una respuesta.

No puede concluirse todavía:

- que cualquiera de las 99 relaciones tenga autorización normativa positiva;
- que las relaciones sin role estén prohibidas;
- que las 17 `P`-only tengan un origen concreto;
- que los source records presentes equivalgan a contenido utilizable;
- que la expansión esté estructuralmente aislada, aunque la mezcla no fue
  observada en esta base;
- que la integridad global de FK pase;
- que `fadena-std` tenga autoridad curricular demostrada;
- que la discrepancia `fadena_v1` esté resuelta;
- que Gate B, C1/C2 o `PRODUCT_COMPLETE` estén cerrados.

## 11. Fuentes y límites

Este expediente consolida exclusivamente los inventarios y findings ya
reconciliados en:

- CP077: scope de release y cotejo de identidad;
- CP078: `curriculum_id` contradictorio;
- CP079: sets completos R/U/P, 99 asociaciones, roles, source records,
  excepciones y 23 sources cross-scope;
- CP080: interpretación de provenance y frontera estática de expansión;
- CP081: umbral estricto de autorización `UNKNOWN`, modelo sin garantía global
  document/source y ausencia de post-filter;
- CP082: inspección read-only, mezcla actual no observada, Q2 consistente y
  finding FK separado.

No se ejecutaron TALOS, FastAPI, tests, benchmarks, providers, retrieval,
workloads ni migraciones. No se consultó la DB para reconstruir inventarios ni
se modificaron ACL, asociaciones, roles, registry, catálogo, perfiles, código,
DB, fixtures o gates.

## Estado final

```text
HUMAN_DECISION_REQUIRED = YES
CRITERION_1 = BLOCKED
CRITERION_2 = BLOCKED
```
