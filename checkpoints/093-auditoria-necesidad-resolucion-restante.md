# CP093 — AUDITORÍA DE NECESIDAD DE RESOLUCIÓN DE LAS 37 RELACIONES RESTANTES

## 1. Objetivo y límites

Audita si las 37 filas que CP092 mantiene abiertas son requisitos reales de
Gate B o si parte de su estado abierto se debe a exigir una dimensión
`curricular_function` que CP074 no impone. Se distinguen existencia técnica,
pertenencia curricular y autorización L3; no se crean clasificaciones ni se
modifica política o estado técnico.

La inspección se limita a CP074–092 y a la evidencia estática ya citada por
esos checkpoints. No se ejecutaron TALOS, FastAPI, tests, providers,
benchmarks, retrieval ni workloads; no se inspeccionaron ni modificaron DB,
corpus, PDFs, ACL, configuración o código productivo.

## 2. Estado de entrada

La matriz de CP092 y los grupos de CP090 concuerdan:

| Estado | Conteo |
|---|---:|
| Relaciones totales | 99 |
| Previamente adjudicadas en CP089 | 47 |
| Resueltas por CP092 | 15 |
| Restantes abiertas tras CP092 | 37 |
| Grupo A — `NATIVE` con función no establecida | 20 |
| Grupo B — SOC → FADENA, policy no concedida | 17 |

```text
D1 = A
D2 = A
D3 = C
D4 = DERIVED_FROM_D1
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
C2 = BLOCKED
```

## 3. Tres preguntas distintas

| Pregunta | Evidencia que responde | Resultado relevante aquí |
|---|---|---|
| `RELATION_EXISTS` | Asociación técnica `notebook_id → source_id`. | Sí para las 37: forman parte del universo de asociaciones cotejado en CP079/084 y la matriz de CP092. Esto describe existencia, no legitimidad curricular. |
| `RELATION_IS_CURRICULAR` | Home/organización y reglas curriculares explícitas para el scope destino. | Para Grupo A, CP092 establece pertenencia `NATIVE`, pero no asigna función `PRIMARY`/`COMPLEMENTARY`. Para Grupo B, la reutilización curricular sigue `UNRESOLVED` porque D3=C no cubre SOC→FADENA. |
| `RELATION_IS_AUTHORIZED_L3` | Acto trazable con scope, fuente e identidad/version, propósito, decisor y efecto autorizante. | No demostrado para ninguna de las 99; CP084 mantiene 0/99. `NOT_DEMONSTRATED` no equivale a rechazo, revocación o invalidez. |

## 4. Grupo A — 20 `NATIVE` con función no establecida

### 4.1 Evaluación de necesidad

**Resultado:** `curricular_function` es
`MODEL_ASSUMPTION_NOT_REQUIRED` **como dimensión obligatoria de Gate B**.
`NATIVE + ROLE` puede representar una relación curricular válida de
pertenencia/tratamiento sin forzar `PRIMARY` o `COMPLEMENTARY`.

Evidencia:

1. CP092 aplicó D1=A: la pertenencia y el role son dimensiones ortogonales;
   los 19 roles individuales y el bundle D4 se preservan sin inferir función.
2. CP074 §5 enumera cinco criterios de Gate B. El criterio 2 requiere
   consistencia de roles/ACL y que retrieval/prompt solo permitan fuentes
   autorizadas; no exige que cada asociación tenga el campo
   `curricular_function` con valor `PRIMARY` o `COMPLEMENTARY`.
3. Los criterios 1 y 3 se ocupan de identidad, aliases, `curriculum_id` y
   selección del perfil; tampoco exigen esa dimensión.
4. CP079 distingue roles declarativos de la allowlist técnica y advierte que
   ninguno prueba por sí mismo aprobación curricular o autorización. No
   documenta una correspondencia normativa que obligue a traducir cada role a
   `PRIMARY`/`COMPLEMENTARY`.
5. CP084 sí requiere **propósito** como elemento de L3. Ese requisito no
   demuestra que la etiqueta de función curricular sea la única forma válida
   de expresar el propósito; tampoco permite dar por demostrado el propósito
   para estas 20 relaciones.

Por tanto:

```text
GROUP_A_20_STATUS = MODEL_ASSUMPTION_NOT_REQUIRED
NATIVE_RELATION_CAN_EXIST_WITHOUT_FUNCTION = YES
FUNCTION_CLASSIFICATION_REQUIRED_FOR_GATE_B = NO
L3_FOR_GROUP_A = NOT_DEMONSTRATED
```

Esto elimina únicamente el argumento de que las 20 están incompletas **por
carecer de la etiqueta de función**. No adjudica `PRIMARY` ni
`COMPLEMENTARY`, no demuestra un propósito de autorización L3 y no cierra
C2. Las 20 siguen sin L3 demostrado.

### 4.2 Universo afectado

Las 20 filas, agrupadas por notebook, son:

| Scope | `source_id` | Role conservado |
|---|---|---|
| `fase0-soc` | `src_fadena_prog_punteros` | `IMPLEMENTATION`, `REFERENCE` |
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

La primera fila es el bundle D4 y mantiene ambas etiquetas. La tabla describe
la decisión documental CP092; no es una afirmación de que se haya modificado
el archivo de roles técnico.

## 5. Grupo B — 17 relaciones SOC → FADENA

### 5.1 Significado de `POLICY_NOT_GRANTED`

La interpretación adecuada entre las opciones propuestas es:

```text
D — RELATION_OUTSIDE_CURRENT_RELEASE_POLICY
```

D3=C concede la regla direccional FADENA→SOC, no una regla inversa. Por ello,
las 17 asociaciones SOC→FADENA quedan fuera de la cobertura positiva de la
política adoptada para el release. Esto no es una determinación afirmativa
`RELATION_UNAUTHORIZED`, `RELATION_INVALID`, rechazo, exclusión permanente ni
revocación. En cuanto a autorización de fuente, su estado histórico sigue
siendo `L3_NOT_DEMONSTRATED`.

```text
RELATION_EXISTS = YES
RELATION_IS_CURRICULAR = UNRESOLVED
RELATION_IS_AUTHORIZED_L3 = NOT_DEMONSTRATED
POLICY_NOT_GRANTED = OUTSIDE_CURRENT_RELEASE_POLICY; NOT A REJECTION
```

### 5.2 Universo afectado

Las 17 asociaciones existentes son:

| Scope destino | `source_id` (home `fase0-soc`) |
|---|---|
| `fadena-lenguajes` | `src_fadena_prog_arboles` |
| `fadena-lenguajes` | `src_fadena_prog_archivos` |
| `fadena-lenguajes` | `src_fadena_prog_lineales` |
| `fadena-lenguajes` | `src_fadena_prog_punteros` |
| `fadena-lenguajes` | `src_joyanes_fundamentos` |
| `fadena-lenguajes` | `src_spraul_think_like_a_programmer` |
| `fadena-lenguajes` | `src_sweigart_automate_boring_stuff` |
| `fadena-so2` | `src_fadena_so_concurrencia` |
| `fadena-so2` | `src_fadena_so_memoria` |
| `fadena-so2` | `src_fadena_so_planificacion` |
| `fadena-so2` | `src_fadena_so_procesos` |
| `fadena-so2` | `src_stallings_computer_security` |
| `fadena-std` | `src_fadena_prog_archivos` |
| `fadena-std` | `src_ramalho_fluent_python` |
| `fadena-std` | `src_rosen_matematicas_discretas` |
| `fadena-teleco` | `src-guia-2025-c04f44ef` |
| `fadena-teleco` | `src_stallings_computer_security` |

No se borran ni se cambian estas asociaciones en CP093. Tampoco se concluye
que hayan alcanzado retrieval o prompt: CP079 demuestra una allowlist técnica
basada en `notebook_sources`, no un acto humano de autorización; esta auditoría
no vuelve a ejecutar ni inspeccionar el camino runtime.

## 6. Impacto frente a los cinco criterios de Gate B de CP074

`NOT_BLOCKED` en esta tabla significa **no bloqueado por estas 37 filas en
particular**, no `PASS`; el estado probatorio previo de CP075 se conserva.
`BLOCKED` identifica un obstáculo de assurance documentado, no un defecto
runtime reproducido.

| Criterio CP074 | Resultado respecto de Grupos A/B | Razón y evidencia |
|---|---|---|
| 1. IDs canónicos, aliases y `curriculum_id` reconciliados | `NOT_BLOCKED` | La función `PRIMARY`/`COMPLEMENTARY` y la dirección SOC→FADENA no cambian la identidad ni los aliases. CP075 mantiene el criterio en `PARTIAL_EXISTING_EVIDENCE` por falta de reconciliación efectiva del conjunto; CP093 no lo pasa. |
| 2. Roles de fuente y ACL efectiva consistentes | `BLOCKED` | Independientemente de la función curricular, CP084 fija umbral L3 y 0/99 grants demostrados; CP079 señala que las asociaciones `notebook_sources` son la allowlist técnica, pero no prueban aprobación ni propósito. Para las 17 cubiertas por una dirección no concedida, no hay evidencia que justifique tratarlas como permitidas bajo D3=C. Es un blocker de autorización/assurance, no evidencia de que se observó una fuga. CP075 ya reportaba evidencia parcial. |
| 3. Selección de perfil por identidad explícita | `NOT_BLOCKED` | Los grupos no alteran IDs, `curriculum_id` ni el mecanismo de selección. CP075 mantiene evidencia parcial porque la selección no está reconciliada e integrada para el release efectivo; las 37 no añaden ese tipo de discrepancia ni producen un PASS. |
| 4. Ausencia de contaminación entre currículos | `BLOCKED` | El criterio CP074 exige aislamiento salvo asociación explícita autorizada. D3=C no autoriza SOC→FADENA y las 17 asociaciones siguen presentes técnicamente según el universo/allowlist descritos en CP079; no se demuestra que la ruta de release las excluya ni que exista autorización aplicable. Es un blocker de assurance hasta reconciliar la allowlist con la política. No se afirma contaminación efectiva, porque no se ejecutó ni observó runtime. |
| 5. Autoridad curricular de `fadena-std` si se incluye | `BLOCKED` | `fadena-std` está incluido en el release fijado (`FADENA_STD_RELEASE_SCOPE = INCLUDED`, CP077–079). CP075 condiciona el cierre a fuente curricular oficial verificable y vínculo con perfil/fuentes; CP092 no acredita esa autoridad. La falta de `curricular_function` no resuelve ni causa este blocker independiente. |

En consecuencia, las 20 del Grupo A no añaden un requisito Gate B por etiqueta
de función, pero el criterio 2/C2 continúa bloqueado por la exigencia L3 y
otras reconciliaciones pendientes. Las 17 del Grupo B sí dejan abierto un
problema de policy/allowlist para los criterios 2 y 4. Ninguno de estos
resultados demuestra por sí mismo una falla de producto observada; sí impide
declarar assurance completo con la evidencia disponible.

## 7. Matriz de niveles de cierre

| Grupo | Relación documental | Gate B / C2 | Clasificación del bloqueo y límite |
|---|---|---|---|
| A — 20 `NATIVE + ROLE` | `RELATION_EXISTS = YES`; pertenencia nativa establecida por CP092; función `PRIMARY`/`COMPLEMENTARY` no establecida. Puede existir relación nativa sin esa etiqueta. | La ausencia de función no bloquea por sí sola Gate B. L3 sigue `NOT_DEMONSTRATED`; C2 no pasa. | **No es `PRODUCT_BLOCKER` demostrado por falta de función.** La función es `MODEL_ASSUMPTION_NOT_REQUIRED` para Gate B. El estado L3 es un **assurance blocker** independiente. |
| B — 17 SOC→FADENA | `RELATION_EXISTS = YES`; relación curricular `UNRESOLVED`; política de reutilización fuera del alcance positivo actual. No es rechazo. | **Bloquea assurance de criterios 2 y 4** mientras se mantenga la asociación técnica sin evidencia de autorización/exclusión coherente. C2 también sigue bloqueado por L3. | **`OPTIONAL_POLICY_OPEN`** en cuanto a una posible decisión futura de reutilización y **`ASSURANCE_BLOCKER`** para afirmar allowlist/no-contaminación ahora. No se ha demostrado un `PRODUCT_BLOCKER` runtime. |

## 8. Revisión del `MODEL_GAP` de CP092

CP079 describe `notebook_sources` como fuente de asociaciones que alimenta
`Notebook.sources`/allowlist y `notebook_source_roles.json` como declaración
de roles distinta. CP074 define resultados observables de identidad,
autorización de fuentes y aislamiento, no un schema único con todas las
dimensiones curriculares. Por tanto, el `MODEL_GAP` de CP092 debe acotarse:

| Dimensión | Necesidad demostrada para Gate B/C2 | Conclusión documental |
|---|---|---|
| Identidad global, source ID y versión/bytes | Sí para identificar la fuente y satisfacer los elementos de identidad/version de L3; identidad del notebook/aliases también pertenece al criterio 1. | Debe poder reconstruirse con fuentes/versiones inequívocas; no se ha probado que requiera una tabla única. |
| Scope destino y asociación fuente→notebook | Sí: los criterios 1–4 dependen de mantener la identidad/scope; criterios 2 y 4 requieren que las fuentes efectivas y su aislamiento sean verificables. | Obligación funcional/de assurance; no prescribe una representación física concreta. |
| Home y pertenencia (`NATIVE`/`REUSED`) | Necesarios para explicar la dirección de reutilización de las relaciones de este caso y preservar el límite curricular adoptado. | Metadatos normativos/provenance relevantes para el análisis; CP074 no exige estos campos como schema runtime en todos los casos. |
| `curricular_function` (`PRIMARY`/`COMPLEMENTARY`) | No se demuestra como requisito de Gate B. | Metadata opcional para estos criterios; no inferir función para las 20. Puede ser exigible por una política futura/claim curricular más específica. |
| Roles declarados | El criterio 2 exige consistencia de roles y ACL; CP079 muestra que los roles declarativos no son la allowlist. | La etiqueta/version de role y su relación con el scope deben auditarse; no se exige colapsarlas en la función curricular. |
| Propósito y provenance/decisor/efecto autorizante | Sí para el umbral L3 de C2 establecido por CP084. | Evidencia autorizante trazable obligatoria; no puede sustituirse por asociación, role o función curricular. |
| Prioridad pedagógica numérica | No aparece en los cinco criterios Gate B de CP074 ni en los elementos L3 enumerados por CP084 como campo separado. | No es requisito demostrado de cierre actual; queda como política/metadata futura. El propósito L3 sigue requerido, pero no equivale a un ranking numérico. |

Así, el `MODEL_GAP` persiste como falta de representación documental
consolidada/reconciliable para algunas dimensiones. No se sostiene que todas
las dimensiones mencionadas en CP092 sean requisitos mínimos de persistencia
para Gate B. No se diseña un schema ni se propone migración.

## 9. Categorías de bloqueo y decisiones nuevas

- `PRODUCT_BLOCKER`: no se ha demostrado un defecto funcional/runtime causado
  por estas 37 filas; no se atribuye esta categoría.
- `ASSURANCE_BLOCKER`: sí aplica a la demostración de autorización/allowlist
  en los criterios 2 y 4 para las 17 relaciones SOC→FADENA, y al requisito L3
  global de C2. No afirma una fuga observada.
- `OPTIONAL_POLICY_OPEN`: aplica a la posibilidad de una política futura para
  SOC→FADENA; no convierte la falta actual de grant en rechazo ni exige abrir
  una decisión en este checkpoint.
- `MODEL_GAP`: queda acotado a la diferencia entre las dimensiones
  normativas/documentales y lo que CP079 demuestra que representan las
  asociaciones y roles técnicos.

```text
NEW_HUMAN_DECISION_REQUIRED = NO
```

No aparece contradicción que requiera ampliar ahora el paquete de decisiones:
D3=C ya delimita la dirección permitida; la limitación de evidencia de L3 y
la falta de prueba de alineación allowlist/policy son asuntos de assurance,
no una inferencia de que la política elegida deba cambiarse.

## 10. Cierre

```text
CP092 = ACCEPTED
CP093 = COMPLETE
GROUP_A_20_STATUS = MODEL_ASSUMPTION_NOT_REQUIRED
NATIVE_RELATION_CAN_EXIST_WITHOUT_FUNCTION = YES
GROUP_B_17_STATUS = OUTSIDE_CURRENT_RELEASE_POLICY; NOT REJECTED
GATE_B_IMPACT = CRITERIA_2_AND_4_ASSURANCE_BLOCKED; CRITERION_5_INDEPENDENTLY_BLOCKED
L3_DEMONSTRATED = 0
L3_NOT_DEMONSTRATED = 99
TECHNICAL_STATE_MODIFIED = NO
```

El estado de C2 sigue siendo `BLOCKED`: la falta de
`curricular_function` en Grupo A no lo bloquea, pero tampoco reemplaza el acto
L3; la política actual deja Grupo B fuera de su cobertura positiva y la
evidencia existente no demuestra todavía el control de las asociaciones
efectivas.
