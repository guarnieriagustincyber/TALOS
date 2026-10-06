# CP090 — MINIMIZACIÓN Y AGRUPACIÓN DE DECISIONES HUMANAS PARA LAS 52 RELACIONES `UNRESOLVED`

## 1. Estado inicial

```text
TOTAL_RELATIONS = 99
ADJUDICATED = 47
UNRESOLVED = 52
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```

## 2. Principio de minimización

No se busca resolver cada fuente individualmente. Se busca identificar la menor cantidad de decisiones estructurales que expliquen el mismo bloqueo para varios sources. La regla de agrupación es que todas las relaciones del grupo comparten la misma clase de incertidumbre y la misma pregunta bloqueante.

## 3. Clasificación de las 52 relaciones

| notebook_id | source_id | current_relationship_type | declared_role | physical_home_scope | uncertainty_category | blocking_question | candidate_group | evidence_basis |
|---|---|---|---|---|---|---|---|---|
| `fase0-soc` | `src_0bc5d20dcc91895f` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_0fc90b2695369475` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_a9a056742dcf69ae` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fase0-soc` | `src_d253687930308e41` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_e9682dece40b58ab` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_fadena_prog_punteros` | `UNRESOLVED` | `IMPLEMENTATION, REFERENCE` | `fase0-soc` | `E` | ¿La combinación de carpeta, role y provenance exige resolución humana antes de definir la relación curricular? | G4-conflicting-evidence | mixed-role bundle or conflicting evidence between home and role |
| `fase0-soc` | `src_goodrich_dsa_python` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fase0-soc` | `src_martin_clean_code` | `UNRESOLVED` | `IMPLEMENTATION` | `fase0-soc` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fase0-soc` | `src_rosen_matematicas_discretas` | `UNRESOLVED` | `FORMAL` | `fase0-soc` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | `UNRESOLVED` | `METHODOLOGICAL` | `fase0-soc` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fase0-soc` | `src_stallings_os_internals_7ed` | `UNRESOLVED` | `—` | `fadena-so2` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | `UNRESOLVED` | `REFERENCE` | `fadena-lenguajes` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | `UNRESOLVED` | `—` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | `UNRESOLVED` | `—` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | `UNRESOLVED` | `PRIMARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-lenguajes` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | `UNRESOLVED` | `PRIMARY, METHODOLOGICAL` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | `UNRESOLVED` | `METHODOLOGICAL` | `fadena-lenguajes` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | `UNRESOLVED` | `METHODOLOGICAL` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | `UNRESOLVED` | `REFERENCE` | `fadena-lenguajes` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-so2` | `src_e9682dece40b58ab` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-so2` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-so2` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-so2` | `src_fadena_so_concurrencia` | `UNRESOLVED` | `PRIMARY, METHODOLOGICAL` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-so2` | `src_fadena_so_memoria` | `UNRESOLVED` | `COMPLEMENTARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-so2` | `src_fadena_so_planificacion` | `UNRESOLVED` | `PRIMARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-so2` | `src_fadena_so_procesos` | `UNRESOLVED` | `PRIMARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-so2` | `src_stallings_computer_security` | `UNRESOLVED` | `IMPLEMENTATION` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-std` | `src_032c52bff94a0743` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_3102eb1e89e2229e` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_52ff5ff3e07c1da5` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_56cfdbe35123c49e` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_6dbdc8e943261fa7` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_7ec00a3365f208e6` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_9e866bf082e52dd7` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_a01b9809f37fb47b` | `UNRESOLVED` | `IMPLEMENTATION` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_d7ff8399759d387a` | `UNRESOLVED` | `COMPLEMENTARY` | `fadena-std` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | `UNRESOLVED` | `FORMAL` | `fadena-std` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | `UNRESOLVED` | `COMPLEMENTARY` | `fadena-std` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-std` | `src_fadena_prog_archivos` | `UNRESOLVED` | `PRIMARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-std` | `src_marques_bases_de_datos` | `UNRESOLVED` | `COMPLEMENTARY` | `fadena-std` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | `UNRESOLVED` | `COMPLEMENTARY` | `fadena-std` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-std` | `src_ramalho_fluent_python` | `UNRESOLVED` | `IMPLEMENTATION` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-std` | `src_rosen_matematicas_discretas` | `UNRESOLVED` | `—` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-teleco` | `src-guia-2025-c04f44ef` | `UNRESOLVED` | `METHODOLOGICAL` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | `UNRESOLVED` | `FORMAL` | `fadena-teleco` | `A` | ¿Debe el role no equivalente dentro de la carpeta nativa interpretarse como material curricular o como auxiliar/reutilizable? | G1-role-semantics | home_folder_support_present_but_role_semantics_ambiguous |
| `fadena-teleco` | `src_corletti_seguridad_redes` | `UNRESOLVED` | `COMPLEMENTARY` | `fadena-teleco` | `C` | ¿Una relación `COMPLEMENTARY` dentro de la carpeta nativa es válida, o necesita una decisión que preserve la separación entre material nativo y material reutilizado? | G2-native-folder-complementary | same-folder support + COMPLEMENTARY role contradicts native-home assumption |
| `fadena-teleco` | `src_stallings_computer_security` | `UNRESOLVED` | `PRIMARY` | `fase0-soc` | `D` | Existe una política explícita de reutilización cross-scope para este source, o requiere decisión humana individual? | G3-cross-scope-reuse | same-universe-cross-scope, no explicit reuse decision; source home in other notebook/scope |

## 4. Distribución por categoría

| categoría | descripción | conteo |
|---|---|---:|
| `A` | ROLE_SEMANTIC_UNRESOLVED | 19 |
| `C` | NATIVE_FOLDER_ROLE_UNRESOLVED | 8 |
| `D` | MISSING_NATIVE_SUPPORT | 24 |
| `E` | CONFLICTING_EVIDENCE | 1 |

`B` y `F` no aparecen en la resolución actual: no hay un conjunto de filas que comparta una incertidumbre distinta de las ya descritas dentro de la evidencia disponible.

## 5. Grupos homogéneos y decisiones estructurales mínimas

### G1 — `ROLE_SEMANTIC_UNRESOLVED` (A)

Aplica a 19 relaciones con `physical_home_scope == notebook_id` y roles no equivalentes (IMPLEMENTATION, REFERENCE, METHODOLOGICAL, FORMAL). El bloqueo no es la ausencia de datos sino la falta de política explícita para traducir esos roles a la categoría curricular correcta.

Pregunta mínima:

```text
DECISION D1
Pregunta: ¿Debe un role `IMPLEMENTATION`/`REFERENCE`/`METHODOLOGICAL`/`FORMAL` dentro del corpus nativo de un notebook definirse como material curricular oficial, auxiliar o no curricular?
Afecta: 19 relaciones
Resultado si YES: se puede resolver el bloque de roles no equivalentes con una política común.
Resultado si NO: las filas siguen como `UNRESOLVED` y requieren tratamiento individual o la creación de una regla específica.
```

### G2 — `NATIVE_FOLDER_ROLE_UNRESOLVED` (C)

Aplica a 8 relaciones donde la carpeta local confirma soporte nativo pero el role es `COMPLEMENTARY`. El material ya está físicamente en la carpeta del notebook; la pregunta no es “si existe”, sino “si la etiqueta `COMPLEMENTARY` puede coexistir con la pertenencia nativa del notebook sin traducirse a una relación auxiliar definitiva”.

```text
DECISION D2
Pregunta: ¿`COMPLEMENTARY` dentro de la carpeta nativa es una etiqueta administrativa de reutilización o una contradicción que exige tratar la relación como `UNRESOLVED` hasta nueva decisión?
Afecta: 8 relaciones
Resultado si YES: se define una excepción documentada para la relación complementaria dentro del home nativo.
Resultado si NO: la relación permanece `UNRESOLVED` y la evidencia nativa no se usa para convertirla automáticamente en `PRIMARY` o `AUXILIARY`.
```

### G3 — `MISSING_NATIVE_SUPPORT` (D)

Aplica a 24 relaciones donde el PDF tiene home físico distinto del notebook objetivo. El bloqueo estructural es que no hay local support nativo y no existe una regla explícita de reutilización para esos pares.

```text
DECISION D3
Pregunta: ¿la política del release autoriza la reutilización cross-scope sin convertir el archivo en material nativo del notebook destino?
Afecta: 24 relaciones
Resultado si YES: todas estas filas pueden agruparse bajo una política común de reutilización (`COMPLEMENTARY` o `AUXILIARY` según la regla elegida).
Resultado si NO: el bloque queda como `UNRESOLVED` y cada caso requiere revisión individual o un rechazo explícito de reutilización.
```

### G4 — `CONFLICTING_EVIDENCE` (E)

Aplica a 1 relación (`src_fadena_prog_punteros` con `IMPLEMENTATION, REFERENCE` en la carpeta nativa). La combinación de roles no puede interpretarse sin más ni menos como una categoría curricular establecida. Es la única excepción con conflicto explícito dentro de un mismo home.

```text
DECISION D4
Pregunta: ¿la combinación de roles dentro de una carpeta nativa debe tratarse como un bundle compartido de soporte metodológico o como una relación de propósito contradictorio?
Afecta: 1 relación
Resultado si YES: se resuelve el bundle como una única regla de propósito y no se rompe la decisión de grupo.
Resultado si NO: se mantiene como excepción individual.
```

## 6. Decisión humana mínima requerida

La carga humana mínima observable es 4 decisiones estructurales, no 52 decisiones individuales:

1. D1: política para roles no equivalentes en carpeta nativa.
2. D2: política para `COMPLEMENTARY` dentro de la carpeta nativa.
3. D3: política de reutilización cross-scope sin nativización.
4. D4: tratamiento de bundles de roles conflictivos.

Esto reduce el problema de 52 decisiones potenciales a 4 preguntas estructurales y un conjunto residual de excepciones documentadas. La reducción no resuelve la relación ni la autorización L3; solo minimiza la decisión humana.

## 7. Casos que no pueden agruparse

No hay evidencia suficiente para agrupar los casos en un único bloque cuando la regla no es la misma para todas. En particular, las excepciones que permanecen individuales son aquellas en las que la razón del bloqueo es la falta de una decisión explícita de reutilización, no una sola categoría técnica. En este corte, la mayoría de las filas salen del modelo de reutilización cross-scope o del rol semántico no equivalente, no de una sola política compartida.

## 8. Impacto

```text
ANTES:
52 decisiones potenciales

DESPUÉS:
4 decisiones estructurales mínimas
+ excepciones individuales documentadas
```

## 9. Estado L3/C2 y técnico

```text
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```

## 10. Cierre

```text
CP089 = ACCEPTED
CP090_ANALYSIS = COMPLETE
99_RELATIONS_PROCESSED = YES
47_PREVIOUSLY_ADJUDICATED = PRESERVED
52_UNRESOLVED_ANALYZED = YES
HUMAN_DECISION_SET = MINIMIZED
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```

