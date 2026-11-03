# CP089 — ADJUDICACIÓN CURRICULAR Y DE REUTILIZACIÓN DEL RELEASE

## 1. Objetivo

Aplicar el marco normativo definido en CP088 y decidir qué parte del universo de 99 relaciones puede adjudicarse objetivamente con la evidencia ya disponible. El alcance es documental y read-only; CP089 no modifica ningún dato técnico ni crea ninguna autorización L3.

## 2. Fuente normativa

1. scope del release decidido por decisión humana; 2. CP088 como modelo de identidad global y relación curricular; 3. evidencia física de carpetas/PDF/hash de CP087; 4. roles declarados ya existentes; 5. historial de CP084–086; 6. evidencia C4-DRAFT cuando corresponde.

## 3. Regla de decisión

```text
SI evidencia suficiente para una relación curricular o de reutilización
    → ADJUDICAR
SI no existe evidencia suficiente para sostener la clasificación sin inventar propósito, prioridad o autorización
    → UNRESOLVED
```

## 4. Principios conservadores aplicados

- La presencia física en una carpeta no iguala a autoría ni L3.
- `PRIMARY` solo significa relación curricular nativa plausible bajo la evidencia estructural disponible; no significa L3 ni prioridad demostrada.
- Las 24 relaciones sin soporte nativo no se eliminan ni se convierten en `NONE`; quedan `UNRESOLVED` salvo evidencia explícita de reutilización.
- Los roles `IMPLEMENTATION`, `REFERENCE`, `METHODOLOGICAL`, `FORMAL` no se traducen automáticamente a categorías curriculares.
- La reutilización FADENA → SOC y las relaciones sin soporte nativo quedan separadas del material nativo FADENA.

## 5. Resultado de la adjudicación

```text
CP088_MODEL = ACCEPTED_AS_NORMATIVE_FRAME
99_RELATIONS_PROCESSED = YES
CURRICULAR_ADJUDICATION = COMPLETE
REUSE_ADJUDICATION = COMPLETE
HUMAN_DECISION_SET = MINIMIZED
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
TECHNICAL_STATE_MODIFIED = NO
C2 = BLOCKED
```

## 6. Matriz completa de 99 relaciones

| notebook_id | source_id | physical_home_scope | declared_role | curricular_status | relationship_type | purpose_status | priority_status | authorization_status | evidence_basis | decision_class |
|---|---|---|---|---|---|---|---|---|---|---|
| `fase0-soc` | `src-guia-2025-c04f44ef` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_0bc5d20dcc91895f` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_0fc90b2695369475` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_a9a056742dcf69ae` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_bel_algoritmos_estructuras_python` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_d253687930308e41` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_e9682dece40b58ab` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_f009c4e75f5ca3f2` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_fadena_prog_arboles` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_prog_archivos` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_prog_lineales` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_prog_punteros` | `fase0-soc` | `IMPLEMENTATION, REFERENCE` | NATIVE | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_fadena_so_concurrencia` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_so_memoria` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_so_planificacion` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_fadena_so_procesos` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_goodrich_dsa_python` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_joyanes_fundamentos` | `fase0-soc` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_kurose_computer_networking` | `fase0-soc`, `fadena-teleco` | `—` | CROSS_SCOPE_REUSE | COMPLEMENTARY | EXPLICIT | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_martin_clean_code` | `fase0-soc` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_ramalho_fluent_python` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_rosen_matematicas_discretas` | `fase0-soc` | `FORMAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_spraul_think_like_a_programmer` | `fase0-soc` | `METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_stallings_computer_security` | `fase0-soc` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fase0-soc` | `src_stallings_os_internals_7ed` | `fadena-so2` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fase0-soc` | `src_sweigart_automate_boring_stuff` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_1149ca3399b6dd85` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-lenguajes` | `src_115f0bc876b44be8` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-lenguajes` | `src_7ba98d836c32fe4b` | `fadena-lenguajes` | `REFERENCE` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_8ac0eed0a6121c6a` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-lenguajes` | `src_fadena_leng_clase1` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-lenguajes` | `src_fadena_leng_clase2` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-lenguajes` | `src_fadena_prog_arboles` | `fase0-soc` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_fadena_prog_archivos` | `fase0-soc` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_fadena_prog_lineales` | `fase0-soc` | `PRIMARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_fadena_prog_punteros` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_fdc4df20e0f9f99e` | `fadena-lenguajes` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_joyanes_fundamentos` | `fase0-soc` | `PRIMARY, METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_marzal_intro_programacion_c` | `fadena-lenguajes` | `METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` | `fase0-soc` | `METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_stallman_gnu_c_manual` | `fadena-lenguajes` | `REFERENCE` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-lenguajes` | `src_urrutia_programacion_c_principiantes` | `fadena-lenguajes` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_0bc5d20dcc91895f` | `fadena-so2` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_0fc90b2695369475` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_a9a056742dcf69ae` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_d253687930308e41` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_e9682dece40b58ab` | `fadena-so2` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_f009c4e75f5ca3f2` | `fadena-so2` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_fadena_so2_clase1` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_fadena_so2_clase2` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-so2` | `src_fadena_so_concurrencia` | `fase0-soc` | `PRIMARY, METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_fadena_so_memoria` | `fase0-soc` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_fadena_so_planificacion` | `fase0-soc` | `PRIMARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_fadena_so_procesos` | `fase0-soc` | `PRIMARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_stallings_computer_security` | `fase0-soc` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-so2` | `src_stallings_os_internals_7ed` | `fadena-so2` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_032c52bff94a0743` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_0960283d5cef8dee` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_3102eb1e89e2229e` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_3e2e8abda5f55c17` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_52ff5ff3e07c1da5` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_53ef2a7243ae3f63` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_56cfdbe35123c49e` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_6dbdc8e943261fa7` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_755be6c147ddc5dd` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_7822bc3cef85c783` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_7ec00a3365f208e6` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_9946be0e7d11161a` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_9e866bf082e52dd7` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_a01b9809f37fb47b` | `fadena-std` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_cf46d8f0e018b09e` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_coronel_database_systems_11ed` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_d7ff8399759d387a` | `fadena-std` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_d946d1a5a3c32144` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_date_intro_sistemas_bd_7ed` | `fadena-std` | `FORMAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_de275591245abbd3` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_elmasri_navathe_sistemas_bd` | `fadena-std` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_f3352475bc0cd360` | `fadena-std` | `—` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_f93b8a264e20359c` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_fadena_prog_archivos` | `fase0-soc` | `PRIMARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_fadena_std_unidad1` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-std` | `src_marques_bases_de_datos` | `fadena-std` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_ramakrishnan_gehrke_dbms` | `fadena-std` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_ramalho_fluent_python` | `fase0-soc` | `IMPLEMENTATION` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_rosen_matematicas_discretas` | `fase0-soc` | `—` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-std` | `src_silberschatz_fundamentos_bd` | `fadena-std` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src-guia-2025-c04f44ef` | `fase0-soc` | `METHODOLOGICAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-teleco` | `src_001b27137cf6680c` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_11195af8e0f2ef40` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_2f1a5843cd1693ba` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_castro_fusario_comunicaciones_redes` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_comer_internetworking_tcpip_v1` | `fadena-teleco` | `FORMAL` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-teleco` | `src_corletti_seguridad_redes` | `fadena-teleco` | `COMPLEMENTARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | HUMAN_DECISION_REQUIRED |
| `fadena-teleco` | `src_da10b53f20f2a647` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_fadena_teleco_unidad1` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_kurose_computer_networking` | `fadena-teleco`, `fase0-soc` | `PRIMARY, METHODOLOGICAL` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |
| `fadena-teleco` | `src_stallings_computer_security` | `fase0-soc` | `PRIMARY` | NOT_ESTABLISHED | UNRESOLVED | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | missing_native_support_or_conflict | HUMAN_DECISION_REQUIRED |
| `fadena-teleco` | `src_stallings_comunicaciones_redes_7ed` | `fadena-teleco` | `PRIMARY` | NATIVE | PRIMARY | NOT_ESTABLISHED | NOT_ESTABLISHED | L3_NOT_DEMONSTRATED | home_folder_exact_match | ADJUDICATED |

## 7. Resumen por scope

| scope | total | PRIMARY | COMPLEMENTARY | AUXILIARY | UNRESOLVED | human_decision_required |
|---|---:|---:|---:|---:|---:|---:|
| `fase0-soc` | 26 | 11 | 1 | 0 | 14 | 14 |
| `fadena-lenguajes` | 17 | 6 | 0 | 0 | 11 | 11 |
| `fadena-so2` | 14 | 7 | 0 | 0 | 7 | 7 |
| `fadena-std` | 30 | 14 | 0 | 0 | 16 | 16 |
| `fadena-teleco` | 12 | 8 | 0 | 0 | 4 | 4 |

## 8. Excepciones y decisiones humanas requeridas

Las relaciones que quedan en `HUMAN_DECISION_REQUIRED` son las que no pueden resolverse sin inventar propósito, prioridad, identidad o autorización. En este corte, la mayoría de las excepciones son las 24 relaciones sin soporte nativo y los roles no equivalentes en carpetas propias que contradicen la identidad curricular sin aportar una definición explícita de reutilización.

### 8.1 Reuso explícito ya admisible

- `fase0-soc` → `src_kurose_computer_networking` = `CROSS_SCOPE_REUSE` / `COMPLEMENTARY` / `ADJUDICATED`.

### 8.2 Casos que requieren decisión humana

- Relaciones con carpeta propia pero `role` no equivalente (`IMPLEMENTATION`, `METHODOLOGICAL`, `REFERENCE`, `FORMAL`, `COMPLEMENTARY`) deben quedarse en `UNRESOLVED` hasta una definición explícita.
- Relaciones sin soporte nativo de carpeta y sin evidencia explícita de reutilización quedan `NOT_ESTABLISHED` / `UNRESOLVED`.
- Cualquier conflicto entre `carpeta`, `role`, `C4-DRAFT` o `notebook_sources` se conserva como `CONFLICTING_EVIDENCE` y exige decisión humana.

## 9. Regla final

> “¿Qué relaciones podemos determinar objetivamente con lo que ya sabemos?”

La respuesta de CP089 es que 47 relaciones pueden adjudicarse por reglas definidas y evidencia suficiente; 52 relaciones quedan como `UNRESOLVED` para decisión humana posterior. Ninguna de estas adjudicaciones convierte el conjunto en una autorización L3 ni modifica un estado técnico.

## 10. Cierre

```text
CP088_MODEL = ACCEPTED_AS_NORMATIVE_FRAME
99_RELATIONS_PROCESSED = YES
CURRICULAR_ADJUDICATION = COMPLETE
REUSE_ADJUDICATION = COMPLETE
HUMAN_DECISION_SET = MINIMIZED
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
TECHNICAL_STATE_MODIFIED = NO
C2 = BLOCKED
```
