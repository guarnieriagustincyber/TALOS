# CP092 — APLICACIÓN DOCUMENTAL DE LA POLÍTICA CURRICULAR Y DE REUTILIZACIÓN

## 1. Objetivo, autorización y límites

Aplica documentalmente las decisiones indicadas en esta directiva: `D1=A`, `D2=A`, `D3=C` y `D4=DERIVED_FROM_D1`. No modifica estado técnico de TALOS. Se limita a los artefactos documentales de checkpoints y su índice; no ejecuta TALOS, FastAPI, tests, providers o benchmarks y no modifica DB, `notebook_sources`, ACL, roles técnicos, corpus, PDFs, `curriculum_id`, retrieval, SectionExpander, BKT, runtime ni configuración.

## 2. Estado de entrada y reconciliación

La matriz de CP090 contiene 52 filas únicas con la distribución esperada. CP089 conserva 47 relaciones previamente adjudicadas; este checkpoint no las vuelve a clasificar.

| Estado de entrada | Conteo |
|---|---:|
| Relaciones totales | 99 |
| Previamente adjudicadas | 47 |
| Previamente `UNRESOLVED` | 52 |
| G1 — roles semánticos en home nativo | 19 |
| G2 — `COMPLEMENTARY` en home nativo | 8 |
| G3 — sin soporte nativo | 24 |
| G4 — bundle de roles | 1 |

```text
D1 = A
D2 = A
D3 = C
D4 = DERIVED_FROM_D1
```

## 3. Modelo aplicado

- La identidad de documento permanece global. `source_id` identifica la fila correspondiente y CP087 aporta el cotejo exacto de PDF/SHA-256; la relación destino no crea otra identidad física.
- `NATIVE`/`REUSED` describen pertenencia respecto del scope destino; no sustituyen a la función curricular.
- La función (`PRIMARY` o `COMPLEMENTARY`) es una dimensión independiente de los roles técnicos/declarativos. D1-A no infiere función a partir de `IMPLEMENTATION`, `REFERENCE`, `METHODOLOGICAL` o `FORMAL`.
- D2-A permite `NATIVE + COMPLEMENTARY`; no convierte `COMPLEMENTARY` en `PRIMARY` ni `AUXILIARY`.
- D3-C concede únicamente reutilización lógica FADENA→SOC como `COMPLEMENTARY`. SOC→FADENA queda fuera de la cobertura concedida; `POLICY_NOT_GRANTED` no significa rechazo ni revocación.
- D4 conserva ambos roles de `src_fadena_prog_punteros`, sin escoger uno principal, como consecuencia de D1-A.

## 4. Matriz documental de las 52 relaciones

`identity` es `GLOBAL:<source_id>` como identificador local de identidad global; el hash/bytes observados se encuentran en el cotejo CP087, no se repiten aquí. `destination_scope` coincide con `scope`. `previous_status` reproduce la clasificación CP090. `new_documentary_status` informa si la aplicación determina todas las dimensiones curriculares requeridas: una membresía nativa resuelta sin función no cuenta como relación completamente resuelta.

| scope | source_id | identity | home_scope | destination_scope | native_membership | reuse_status | curricular_function | roles | resolution_basis | previous_status | new_documentary_status | authorization_status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `fase0-soc` | `src_0bc5d20dcc91895f` | `GLOBAL:src_0bc5d20dcc91895f` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_0fc90b2695369475` | `GLOBAL:src_0fc90b2695369475` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_a9a056742dcf69ae` | `GLOBAL:src_a9a056742dcf69ae` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | `GLOBAL:src_bel_algoritmos_estructuras_python` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_d253687930308e41` | `GLOBAL:src_d253687930308e41` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_e9682dece40b58ab` | `GLOBAL:src_e9682dece40b58ab` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | `GLOBAL:src_f009c4e75f5ca3f2` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_fadena_prog_punteros` | `GLOBAL:src_fadena_prog_punteros` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION, REFERENCE` | D1=A; identidad exacta y home físico según CP087/CP090; ambos roles se conservan como dimensiones independientes. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_goodrich_dsa_python` | `GLOBAL:src_goodrich_dsa_python` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_martin_clean_code` | `GLOBAL:src_martin_clean_code` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_rosen_matematicas_discretas` | `GLOBAL:src_rosen_matematicas_discretas` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `FORMAL` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | `GLOBAL:src_spraul_think_like_a_programmer` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `METHODOLOGICAL` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_stallings_os_internals_7ed` | `GLOBAL:src_stallings_os_internals_7ed` | `fadena-so2` | `fase0-soc` | `REUSED` | `ALLOWED_BY_CP092_FADENA_TO_SOC` | `COMPLEMENTARY` | `NOT_DECLARED` | D3=C; home FADENA distinto del destino fase0-soc; política explícita de reutilización FADENA→SOC. | `UNRESOLVED` | `RESOLVED_REUSED_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | `GLOBAL:src_sweigart_automate_boring_stuff` | `fase0-soc` | `fase0-soc` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | `GLOBAL:src_7ba98d836c32fe4b` | `fadena-lenguajes` | `fadena-lenguajes` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `REFERENCE` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | `GLOBAL:src_fadena_prog_arboles` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `NOT_DECLARED` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | `GLOBAL:src_fadena_prog_archivos` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `NOT_DECLARED` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | `GLOBAL:src_fadena_prog_lineales` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | `GLOBAL:src_fadena_prog_punteros` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `COMPLEMENTARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | `GLOBAL:src_fdc4df20e0f9f99e` | `fadena-lenguajes` | `fadena-lenguajes` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | `GLOBAL:src_joyanes_fundamentos` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY, METHODOLOGICAL` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | `GLOBAL:src_marzal_intro_programacion_c` | `fadena-lenguajes` | `fadena-lenguajes` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `METHODOLOGICAL` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | `GLOBAL:src_spraul_think_like_a_programmer` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `METHODOLOGICAL` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | `GLOBAL:src_stallman_gnu_c_manual` | `fadena-lenguajes` | `fadena-lenguajes` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `REFERENCE` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | `GLOBAL:src_sweigart_automate_boring_stuff` | `fase0-soc` | `fadena-lenguajes` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `COMPLEMENTARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_e9682dece40b58ab` | `GLOBAL:src_e9682dece40b58ab` | `fadena-so2` | `fadena-so2` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | `GLOBAL:src_f009c4e75f5ca3f2` | `fadena-so2` | `fadena-so2` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_fadena_so_concurrencia` | `GLOBAL:src_fadena_so_concurrencia` | `fase0-soc` | `fadena-so2` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY, METHODOLOGICAL` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_fadena_so_memoria` | `GLOBAL:src_fadena_so_memoria` | `fase0-soc` | `fadena-so2` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `COMPLEMENTARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_fadena_so_planificacion` | `GLOBAL:src_fadena_so_planificacion` | `fase0-soc` | `fadena-so2` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_fadena_so_procesos` | `GLOBAL:src_fadena_so_procesos` | `fase0-soc` | `fadena-so2` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-so2` | `src_stallings_computer_security` | `GLOBAL:src_stallings_computer_security` | `fase0-soc` | `fadena-so2` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `IMPLEMENTATION` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_032c52bff94a0743` | `GLOBAL:src_032c52bff94a0743` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_3102eb1e89e2229e` | `GLOBAL:src_3102eb1e89e2229e` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_52ff5ff3e07c1da5` | `GLOBAL:src_52ff5ff3e07c1da5` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_56cfdbe35123c49e` | `GLOBAL:src_56cfdbe35123c49e` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_6dbdc8e943261fa7` | `GLOBAL:src_6dbdc8e943261fa7` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_7ec00a3365f208e6` | `GLOBAL:src_7ec00a3365f208e6` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_9e866bf082e52dd7` | `GLOBAL:src_9e866bf082e52dd7` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_a01b9809f37fb47b` | `GLOBAL:src_a01b9809f37fb47b` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `IMPLEMENTATION` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_d7ff8399759d387a` | `GLOBAL:src_d7ff8399759d387a` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | `GLOBAL:src_date_intro_sistemas_bd_7ed` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `FORMAL` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | `GLOBAL:src_elmasri_navathe_sistemas_bd` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_fadena_prog_archivos` | `GLOBAL:src_fadena_prog_archivos` | `fase0-soc` | `fadena-std` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_marques_bases_de_datos` | `GLOBAL:src_marques_bases_de_datos` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | `GLOBAL:src_ramakrishnan_gehrke_dbms` | `fadena-std` | `fadena-std` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_ramalho_fluent_python` | `GLOBAL:src_ramalho_fluent_python` | `fase0-soc` | `fadena-std` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `IMPLEMENTATION` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-std` | `src_rosen_matematicas_discretas` | `GLOBAL:src_rosen_matematicas_discretas` | `fase0-soc` | `fadena-std` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `NOT_DECLARED` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-teleco` | `src-guia-2025-c04f44ef` | `GLOBAL:src-guia-2025-c04f44ef` | `fase0-soc` | `fadena-teleco` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `METHODOLOGICAL` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | `GLOBAL:src_comer_internetworking_tcpip_v1` | `fadena-teleco` | `fadena-teleco` | `NATIVE` | `NOT_APPLICABLE` | `NOT_ESTABLISHED` | `FORMAL` | D1=A; identidad exacta y home físico según CP087/CP090; el role se conserva como dimensión independiente. | `UNRESOLVED` | `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED` | `L3_NOT_DEMONSTRATED` |
| `fadena-teleco` | `src_corletti_seguridad_redes` | `GLOBAL:src_corletti_seguridad_redes` | `fadena-teleco` | `fadena-teleco` | `NATIVE` | `NOT_APPLICABLE` | `COMPLEMENTARY` | `COMPLEMENTARY` | D2=A; identidad exacta en carpeta del destino y role COMPLEMENTARY según CP087/CP090. | `UNRESOLVED` | `RESOLVED_NATIVE_COMPLEMENTARY` | `L3_NOT_DEMONSTRATED` |
| `fadena-teleco` | `src_stallings_computer_security` | `GLOBAL:src_stallings_computer_security` | `fase0-soc` | `fadena-teleco` | `NOT_NATIVE_AT_DESTINATION` | `POLICY_NOT_GRANTED` | `UNRESOLVED` | `PRIMARY` | D3=C no cubre SOC→FADENA; no hay resolución independiente en CP089–091; política no concedida no equivale a rechazo. | `UNRESOLVED` | `UNRESOLVED_REUSE_POLICY_NOT_GRANTED` | `L3_NOT_DEMONSTRATED` |

## 5. Resultado por decisión

### D1 = A y D4 derivada — 20 relaciones

Las 19 relaciones de G1 y el bundle G4 se clasifican como `NATIVE` por coincidencia de identidad/home según CP087. Se preservan todos los roles existentes; para `src_fadena_prog_punteros` se conservan `IMPLEMENTATION` y `REFERENCE` como dimensiones coexistentes. D1-A resuelve pertenencia y semántica ortogonal del role, pero no decide la función curricular. Por ello, estas 20 filas mantienen `curricular_function = NOT_ESTABLISHED` y el estado general `PARTIALLY_CLASSIFIED_FUNCTION_UNRESOLVED`.

### D2 = A — 8 relaciones resueltas

Las ocho filas G2 quedan como `NATIVE + COMPLEMENTARY`. Se conserva su role `COMPLEMENTARY` y su home; la coexistencia entre pertenencia nativa y función complementaria es la decisión explícita de D2-A. No se infiere prioridad ni L3.

### D3 = C — 7 relaciones FADENA→SOC resueltas

Las siete relaciones cuyo home es `fadena-so2` y destino `fase0-soc` quedan como `REUSED + COMPLEMENTARY`, manteniendo el home FADENA. No se mueve ni duplica ningún PDF. D3-C no concede prioridad ni autorización L3.

### D3 = C — 17 relaciones SOC→FADENA aún `UNRESOLVED`

La decisión solo cubre FADENA→SOC. Las 17 filas con home `fase0-soc` y destino FADENA conservan `native_membership = NOT_NATIVE_AT_DESTINATION`, `reuse_status = POLICY_NOT_GRANTED`, `curricular_function = UNRESOLVED` y estado `UNRESOLVED_REUSE_POLICY_NOT_GRANTED`. No se clasifican como rechazadas, excluidas, revocadas ni borradas; una política o decisión futura puede tratarlas separadamente. CP089–091 no documentan una resolución independiente que las saque de este grupo.

## 6. Recuento resultante

```text
TOTAL_RELATIONS = 99
PREVIOUSLY_ADJUDICATED = 47
PREVIOUSLY_UNRESOLVED = 52
D1_APPLIED = YES
D2_APPLIED = YES
D3_APPLIED = YES
D4_DERIVED = YES
RELATIONS_RESOLVED_BY_CP092 = 15
RELATIONS_REMAINING_UNRESOLVED = 37
  NATIVE_BUT_FUNCTION_UNRESOLVED = 20
  SOC_TO_FADENA_POLICY_NOT_GRANTED = 17
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```

Los 15 resueltos son exactamente las ocho relaciones de D2-A más las siete FADENA→SOC de D3-C. Las otras 37 permanecen separadas: 20 con pertenencia/roles identificados, pero función no inferida, y 17 fuera de la política de reutilización concedida. Se preservan las 47 adjudicaciones previas: 47 + 15 + 37 = 99.

## 7. Revisión de C2 y autorización

```text
C2_AUTHORIZATION_THRESHOLD = L3
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
```

La relación curricular no es autorización L3. CP092 no crea un acto autorizante, no altera las decisiones históricas L3 y no convierte D1/D2/D3 en autorización académica o institucional.

## 8. GAP entre modelo normativo y representación técnica documentada

CP079 describe `notebook_sources` como asociación persistida que alimenta `Notebook.sources` y la allowlist técnica; también describe `notebook_source_roles.json` como configuración declarativa de roles, separada de la ACL efectiva. Esas representaciones documentan asociación y roles, pero la evidencia consultada no demuestra que el modelo implementado persista en una única relación versionada todas las dimensiones normativas ahora requeridas: identidad/versionado global, home, pertenencia, función curricular, propósito/provenance por scope, prioridad y autorización L3.

```text
MODEL_GAP = DOCUMENTED
GAP_DESCRIPTION = source-notebook association and role configuration do not, in the inspected documentation, encode the complete multidimensional curricular relation and its provenance
GAP_REPAIRED = NO
```

El GAP es una diferencia documental entre el modelo normativo adoptado y las representaciones cuya semántica CP079 observó; no afirma que se haya inspeccionado de nuevo runtime o base de datos, ni que el software necesariamente carezca de toda representación adicional. No se implementa ni repara en este checkpoint.

## 9. Cierre

```text
CP091 = ACCEPTED
CP092 = DOCUMENTARY_POLICY_APPLIED
D1 = A
D2 = A
D3 = C
D4 = DERIVED_FROM_D1
DOCUMENT_IDENTITY = GLOBAL
PHYSICAL_DUPLICATION = FORBIDDEN
FADENA_TO_SOC_REUSE = ALLOWED_AS_COMPLEMENTARY
SOC_TO_FADENA_REUSE = NOT_GRANTED_BY_CP092
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
TECHNICAL_STATE_MODIFIED = NO
```
