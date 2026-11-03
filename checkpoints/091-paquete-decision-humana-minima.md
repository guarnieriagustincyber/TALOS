# CP091 — PAQUETE DE DECISIÓN HUMANA MÍNIMA PARA CERRAR LAS 52 RELACIONES

## 1. Objetivo y límites

Este paquete presenta reglas estructurales para que la persona responsable
decida cómo tratar las 52 relaciones `UNRESOLVED` de CP089–090. No aplica las
reglas ni resuelve ninguna relación. La decisión seguirá siendo humana.

CP091 es documental y de solo lectura. No modifica SQLite, asociaciones,
roles, ACL, corpus, PDFs, `curriculum_id`, retrieval, SectionExpander, ni
estados de runtime. No ejecuta TALOS, FastAPI, tests, providers o benchmarks.
No emite autorización L3.

## 2. Verificación del estado de entrada

Los conteos de CP090 coinciden con la matriz y los grupos:

| Estado/grupo CP090 | Conteo |
|---|---:|
| Relaciones totales | 99 |
| Adjudicadas en CP089 | 47 |
| `UNRESOLVED` | 52 |
| G1 — `ROLE_SEMANTIC_UNRESOLVED` | 19 |
| G2 — `NATIVE_FOLDER_ROLE_UNRESOLVED` | 8 |
| G3 — `MISSING_NATIVE_SUPPORT` | 24 |
| G4 — `CONFLICTING_EVIDENCE` | 1 |

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```

Siendo consistente el estado de entrada, el paquete continúa. Las 47
adjudicaciones previas se preservan; las propuestas siguientes solo podrían
afectar la clasificación documental futura de las 52 filas pendientes.

```text
TOTAL_RELATIONS = 99
ADJUDICATED = 47
UNRESOLVED = 52
G1_ROLE_SEMANTICS = 19
G2_NATIVE_FOLDER_COMPLEMENTARY = 8
G3_CROSS_SCOPE_REUSE = 24
G4_CONFLICTING_EVIDENCE = 1
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
```

## 3. DECISIÓN D1 — Semántica de roles en carpeta nativa

**Pregunta de política:** ¿Cómo deben interpretarse los roles
`IMPLEMENTATION`, `REFERENCE`, `METHODOLOGICAL` y `FORMAL` cuando el PDF tiene
identidad exacta y está en la carpeta curricular del notebook?

Las 19 relaciones de G1 afectadas (scope — `source_id`) son:

| Scope | `source_id` | Role declarado |
|---|---|---|
| `fase0-soc` | `src_martin_clean_code` | `IMPLEMENTATION` |
| `fase0-soc` | `src_rosen_matematicas_discretas` | `FORMAL` |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | `METHODOLOGICAL` |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | `REFERENCE` |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | `IMPLEMENTATION` |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | `METHODOLOGICAL` |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | `REFERENCE` |
| `fadena-so2` | `src_e9682dece40b58ab` | `IMPLEMENTATION` |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | `IMPLEMENTATION` |
| `fadena-std` | `src_032c52bff94a0743` | `IMPLEMENTATION` |
| `fadena-std` | `src_3102eb1e89e2229e` | `IMPLEMENTATION` |
| `fadena-std` | `src_52ff5ff3e07c1da5` | `IMPLEMENTATION` |
| `fadena-std` | `src_56cfdbe35123c49e` | `IMPLEMENTATION` |
| `fadena-std` | `src_6dbdc8e943261fa7` | `IMPLEMENTATION` |
| `fadena-std` | `src_7ec00a3365f208e6` | `IMPLEMENTATION` |
| `fadena-std` | `src_9e866bf082e52dd7` | `IMPLEMENTATION` |
| `fadena-std` | `src_a01b9809f37fb47b` | `IMPLEMENTATION` |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | `FORMAL` |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | `FORMAL` |

El home físico solo demuestra soporte/ubicación nativa; ninguna alternativa
convierte automáticamente estas filas en `PRIMARY`, `AUXILIARY` o L3.

### Alternativas

**D1-A — Roles como tratamiento interno, separados de pertenencia**

Los roles son dimensiones de tratamiento que no impiden la pertenencia nativa.
Se conserva el role literal y la pertenencia puede registrarse como `NATIVE`;
la categoría `PRIMARY`/`AUXILIARY` u otra función requiere una política
separada. Para el bundle `IMPLEMENTATION` + `REFERENCE` de D4, ambos roles
pueden coexistir como dimensiones distintas; no se fuerza una sola etiqueta.

**D1-B — El role no basta para establecer una función curricular**

Los roles no equivalen a `PRIMARY`. Las 19 filas siguen pendientes de una
clasificación funcional adicional. Esto no niega su soporte físico nativo ni
elige automáticamente `AUXILIARY`. El bundle de D4 también queda sin función
curricular adjudicada, sin requerir una decisión separada sobre si pueden
coexistir sus dos etiquetas.

**D1-C — Otro tratamiento**

Definir explícitamente una regla alternativa. No se infiere una respuesta por
silencio.

## 4. DECISIÓN D2 — `COMPLEMENTARY` dentro de la carpeta nativa

**Pregunta de política:** ¿Puede coexistir `COMPLEMENTARY` como tipo de
tratamiento con `NATIVE` como pertenencia física/curricular al scope?

Las ocho relaciones afectadas son:

| Scope | `source_id` |
|---|---|
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` |
| `fase0-soc` | `src_goodrich_dsa_python` |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` |
| `fadena-std` | `src_d7ff8399759d387a` |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` |
| `fadena-std` | `src_marques_bases_de_datos` |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` |
| `fadena-teleco` | `src_corletti_seguridad_redes` |

### Alternativas

**D2-A — Coexistencia permitida**

La relación puede ser `NATIVE` por pertenencia y `COMPLEMENTARY` por
tratamiento. No se convierte automáticamente en `PRIMARY`; no cambia la
ubicación física.

**D2-B — Coexistencia no establecida**

Las ocho relaciones permanecen `UNRESOLVED` hasta que exista tratamiento
documental explícito. El home físico no basta para anular el role.

**D2-C — Otro tratamiento**

Definir una regla distinta. No se reclasifica ni se mueve ningún PDF en CP091.

## 5. DECISIÓN D3 — Reutilización cross-scope

**Pregunta de política:** ¿Qué regla debe regir las 24 relaciones existentes
cuyo documento tiene home físico en otro scope?

La clasificación por dirección evita asumir reciprocidad:

- **7 FADENA → SOC:** home `fadena-so2`, destino `fase0-soc`.
- **17 SOC → FADENA:** home `fase0-soc`, destinos FADENA.
- **0 FADENA → FADENA** y **0 SOC → SOC** en este conjunto concreto de 24.

Las 24 relaciones (destino — `source_id`) son:

| Dirección | Scope destino | `source_id` |
|---|---|---|
| FADENA → SOC | `fase0-soc` | `src_0bc5d20dcc91895f` |
| FADENA → SOC | `fase0-soc` | `src_0fc90b2695369475` |
| FADENA → SOC | `fase0-soc` | `src_a9a056742dcf69ae` |
| FADENA → SOC | `fase0-soc` | `src_d253687930308e41` |
| FADENA → SOC | `fase0-soc` | `src_e9682dece40b58ab` |
| FADENA → SOC | `fase0-soc` | `src_f009c4e75f5ca3f2` |
| FADENA → SOC | `fase0-soc` | `src_stallings_os_internals_7ed` |
| SOC → FADENA | `fadena-lenguajes` | `src_fadena_prog_arboles` |
| SOC → FADENA | `fadena-lenguajes` | `src_fadena_prog_archivos` |
| SOC → FADENA | `fadena-lenguajes` | `src_fadena_prog_lineales` |
| SOC → FADENA | `fadena-lenguajes` | `src_fadena_prog_punteros` |
| SOC → FADENA | `fadena-lenguajes` | `src_joyanes_fundamentos` |
| SOC → FADENA | `fadena-lenguajes` | `src_spraul_think_like_a_programmer` |
| SOC → FADENA | `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` |
| SOC → FADENA | `fadena-so2` | `src_fadena_so_concurrencia` |
| SOC → FADENA | `fadena-so2` | `src_fadena_so_memoria` |
| SOC → FADENA | `fadena-so2` | `src_fadena_so_planificacion` |
| SOC → FADENA | `fadena-so2` | `src_fadena_so_procesos` |
| SOC → FADENA | `fadena-so2` | `src_stallings_computer_security` |
| SOC → FADENA | `fadena-std` | `src_fadena_prog_archivos` |
| SOC → FADENA | `fadena-std` | `src_ramalho_fluent_python` |
| SOC → FADENA | `fadena-std` | `src_rosen_matematicas_discretas` |
| SOC → FADENA | `fadena-teleco` | `src-guia-2025-c04f44ef` |
| SOC → FADENA | `fadena-teleco` | `src_stallings_computer_security` |

Toda reutilización conserva el documento global, su home original y el scope
destino como una relación lógica separada. No implica prioridad ni L3.

### Alternativas

**D3-A — Política general cross-scope**

Permitir reutilización como `COMPLEMENTARY` en ambas direcciones. En estas
filas eso cubre los siete casos FADENA → SOC y los 17 casos SOC → FADENA; no
declara que una dirección se deduzca de la otra, sino que la misma regla
explícita se adopta para ambas. No mueve ni duplica documentos, no cambia home,
y no crea L3.

**D3-B — Sin política general**

No establecer reutilización general. Las 24 relaciones siguen `UNRESOLVED`;
cada nueva reutilización requiere una decisión explícita. No equivale a
rechazo, eliminación o revocación de las relaciones existentes.

**D3-C — Solo SOC consume fuentes FADENA**

Permitir FADENA → SOC como `COMPLEMENTARY` para los siete casos listados.
Mantener SOC → FADENA sin una regla general: sus 17 relaciones quedan
`UNRESOLVED` y requieren decisión explícita separada. No se presume
reciprocidad.

**D3-D — Otro tratamiento**

Definir explícitamente qué direcciones y condiciones cubre la política. No se
extiende por analogía a FADENA → FADENA o SOC → SOC.

## 6. DECISIÓN D4 — Bundle de roles en `src_fadena_prog_punteros`

Esta es una excepción ya incluida dentro de las 52, no una relación adicional.
Corresponde a `fase0-soc` → `src_fadena_prog_punteros`, con home físico
`fase0-soc` y roles `IMPLEMENTATION` + `REFERENCE`. El caso puede ser absorbido
por la regla general D1:

```text
D4_DEPENDS_ON_D1 = YES
D4_SEPARATE_RESPONSE_REQUIRED = NO
```

- Con **D1-A**, los dos roles coexisten como dimensiones de tratamiento y el
  registro no necesita reducirlos a uno. La función curricular sigue siendo
  distinta de L3.
- Con **D1-B**, ambos roles se conservan, pero no bastan para asignar
  `PRIMARY`/`AUXILIARY`; la función queda pendiente dentro de la misma política
  D1.
- Con **D1-C**, la regla alternativa debe indicar si cubre bundles de roles.

Así se conserva la excepción en la auditoría sin pedir una cuarta respuesta.
No se decide por mayoría de roles ni se modifica el role existente.

## 7. Matriz de impacto y dependencias

| Decisión | Relaciones directas | Naturaleza | Dependencia |
|---|---:|---|---|
| D1 | 19 + el bundle D4 dependiente (1) | Semántica de roles en home nativo | Regla general |
| D2 | 8 | `COMPLEMENTARY` con home nativo | Independiente de D1 |
| D3 | 24 | Reutilización cross-scope: 7 FADENA → SOC, 17 SOC → FADENA | Independiente; direcciones no recíprocas |
| D4 | 1 (superpuesta al tratamiento D1, no sumar al total) | Bundle `IMPLEMENTATION` + `REFERENCE` | Absorbida/condicionada por D1 |

```text
DECISIONES_INDEPENDIENTES_REQUERIDAS = 3
D4_DEPENDS_ON_D1 = YES
D4_SEPARATE_RESPONSE_REQUIRED = NO
UNIQUE_RELATIONS_COVERED = 52
```

La suma de categorías de CP090 sigue siendo 19 + 8 + 24 + 1 = 52. D4 se
mantiene visible como excepción categórica, pero no se suma como cuarta
pregunta ni como relación adicional.

## 8. Cuestiones fuera de este paquete

Las decisiones D1–D3 no resuelven:

- prioridad numérica, orden o secuenciación pedagógica;
- asignación a una fase SOC específica;
- BKT, pesos de retrieval o ranking de fuentes;
- autorización L3;
- autoridad académica externa o validación institucional;
- `curriculum_id` o ACL técnica.

```text
curricular relationship != L3 authorization
```

Una respuesta afirmativa no modifica `L3_DEMONSTRATED`; cualquier relación
curricular que se determine después conserva el estado de autorización
documental vigente hasta un acto L3 trazable independiente.

## 9. Formato de respuesta humana

No se interpreta silencio como aceptación. Responder una opción por regla:

```text
D1 = [A / B / C]
D2 = [A / B / C]
D3 = [A / B / C / D]
```

D4 no requiere una respuesta separada; queda condicionado por D1 según §6.
Las opciones personalizadas D1-C, D2-C o D3-D necesitan que se escriba la
regla alternativa.

## 10. Estado posterior a CP091

CP091 organiza preguntas y consecuencias; no aplica ninguna alternativa ni
crea adjudicaciones:

```text
CP090 = ACCEPTED
CP091 = DECISION_PACKAGE_READY
CP091_PACKAGE = COMPLETE
HUMAN_DECISIONS_PENDING = YES
52_RELATIONS = PRESERVED
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```
