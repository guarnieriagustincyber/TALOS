# Checkpoint 060 — auditoría de minimalidad y no-circularidad de decisiones

Fecha: 2026-10-01
Alcance: auditar exclusivamente las afirmaciones y gates propuestos en CP059
contra CP058, manifest, ledger, las referencias de baseline y el crosswalk
descriptivo ya validado. No se elige autoridad, no se adjudica y no se
modifica el canon.

## 1. Resultado ejecutivo

CP059 no demuestra un número exacto de deliberaciones humanas independientes.
Sí permite demostrar lo siguiente:

1. **L0 — `DESCRIPTIVE_CROSSWALK` ya está cerrado.** No requiere decisión
   normativa ni se debe mantener abierto para justificar trabajo posterior.
2. CP059 enumera siete gates H01–H07, pero no son siete decisiones humanas
   independientes:
   - H01 es ante todo un **prerrequisito de evidencia/provenance**, no una
     decisión humana que pueda declarar qué era históricamente el hash
     externo `f058…`.
   - H02 y H03 son la misma clase de cuestión —outcome de relación
     syscall-superficie— aplicada a dos lotes; se consolidan en un gate de
     adjudicación relacional, preservando 157 + 10 registros separados.
   - H05 reúne una decisión de criterio normativo con dos gates de evidencia
     factual (trazabilidad y enforcement); éstos no son deliberaciones que
     puedan suplirse votando.
   - H06 (autorización de cambio canónico) y H07 (validación/readiness) son
     gates distintos y posteriores; ninguno es una adjudicación de
     superficie.
3. Los **385 outcomes globales** son una dimensión de salida independiente de
   las relaciones: no se derivan automáticamente de membership, de una
   exclusión ni de un checkpoint. Son 385 unidades que necesitan estado final
   si se pretende cerrar globalmente; el número de sesiones de deliberación
   para decidirlas no está determinado por la evidencia actual.
4. El grafo de evidencia y decisiones puede ser acíclico. **No se encontró
   un ciclo demostrado** en las dependencias de CP059. Sí se identifica un
   riesgo metodológico: llamar “resolver autoridad” a escoger una copia
   porque permite avanzar, y luego usar los juicios basados en esa copia para
   justificar la misma elección. Ese camino sería circular y queda excluido.
5. El conjunto de decisiones no está actualmente listo para presentarse como
   un paquete de decisiones maduras: la autoridad normativa sigue unresolved
   y no hay evidencia semántica/variant completa para varios grupos. El
   resultado es un **set mínimo de gates y scopes**, no una autorización para
   resolverlos.

### Respuestas A–I

| Pregunta | Resultado de la auditoría |
|---|---|
| A. ¿Cuántas decisiones humanas independientes existen realmente? | No hay un conteo único demostrable. Hay **4 familias de decisión humana** (outcomes relacionales, outcomes globales, criterio de cobertura/variantes, autorización de cambio), más **2 gates de validación** que no son decisiones semánticas (evidencia/autoridad y readiness). Las relaciones y filas individuales conservan sus unidades; 157, 10 y 385 no equivalen a igual número de deliberaciones. |
| B. ¿Cuáles pueden decidirse con evidencia actual? | Ningún outcome normativo nuevo queda demostrado como maduro en forma global. La correspondencia descriptiva y los outcomes históricos ya escritos sí pueden describirse; no son decisiones pendientes. La recuperación de provenance, evidencia de efectos, trazabilidad, enforcement y predicate requieren trabajo/evidencia adicional. |
| C. ¿Cuáles requieren resolver autoridad de baseline? | Outcomes normativos relacionales/globales, interpretación de criterios/variantes, completitud/freeze y readiness. La integridad descriptiva, stale counters y representación histórica literal no. |
| D. ¿Cuáles son necesarias para L1? | Evidencia de autoridad aplicable (no una inferencia humana); criterios normativos; decisiones relacionales y globales con evidencia adecuada. No canonical change authorization si L1 significa cierre documental normativo, no edición del canon. |
| E. ¿Cuáles son necesarias para L2? | Prerrequisitos de L1, además de autorización separada de cambio y diff sustentado por las decisiones/evidencias fuente. |
| F. ¿Cuáles son necesarias para L3? | Prerrequisitos aplicables de L1/L2, particiones/cobertura completas, evidencia de trazabilidad, calificación del enforcement x32/i386, predicate machine-validated y revisión del overlay/snapshot autorizado. |
| G. ¿Existe circularidad? | No en el DAG válido. Sí habría circularidad si una copia se elevara a autoridad por conveniencia y sus propios resultados se usaran para probar su autoridad. Está prohibido ese atajo. |
| H. ¿Existe alguna decisión redundante? | Sí: H02/H03 son dos lotes de la misma pregunta relacional; se consolidan en un solo gate con dos sublotes y 167 unidades. H01 no es decisión de autoridad histórica; H05 mezcla decisión y evidencia. |
| I. ¿Hay condición de readiness sin gate responsable? | Sí: la evidencia de static callsite tracing y el enforcement real de ABI no tienen un gate de decisión que pueda generarlas. Se registran como **gates de evidencia EVID-01/EVID-02**, no como decisiones humanas; el predicate también requiere un artefacto/verificación a cargo de implementación y revisión. |

## 2. Fuente, límites e invariantes observados

CP058/059 y el manifest/ledger son los límites de evidencia de este análisis.
Se hicieron sólo lecturas locales y comprobaciones estructurales de
artefactos; no se repitió la arqueología 011–057 ni se ejecutó código del
proyecto.

| Estado/hash protegido | Valor de partida y cierre |
|---|---|
| Manifest SHA-256 | `801f529655f1f4f250a2a374d2afa63f858a9c0875e0e3dc620d112df5f9fd6e` |
| Ledger SHA-256 | `0961b8a23e72ab78791278ae4cf42238eaf586e43c60d341829742ebb2144a42` |
| `requirements.lock` SHA-256 | `813454bf8dfd410e78789af43b92965b78fdba416757f141e4e6a0c2ee2f4a70` |
| Baseline spec `files/` SHA-256 | `23e268c18814d34a1581ce4706344f9aff142633bcd8dd1224b6a3352750ccd0` |
| Baseline spec `docs/` SHA-256 | `b4581b1af6e3d04bedc299c8be3972d345a35d110de59f8b6543c7dafc365c8c` |
| Baseline esperado por ledger | `f058426b2a7315a90b651eb77d27f2e1c64209105fe8fdc4c1213218d19a0ad4`; no recuperado y no presente en el overlay identificado por el ledger |
| Baseline authority | `AUTHORITY_UNRESOLVED`; no se establece autoridad por tracking, path, fecha, hash local o semejanza |
| Filas syscall | 385; comprobación local del array manifest: 385 objetos, 385 nombres únicos y 385 NR únicos |
| Disposiciones globales | 385/385 `UNKNOWN`; `final_surface_or_exclusion_disposition_count=0` |
| Tags/leads | 162 tags; 5 superpuestos a exclusiones; 157 relaciones abiertas |
| UNKNOWN relacionales | 10 |
| Provenance parcial | 61 pares: S10=36, S11=22, S15=3 |
| Checkpoint-only | 77: 44 YES condicionales, 23 exclusiones, 10 UNKNOWN |
| Inventory/readiness | `frozen=false`; A-PRE-0 `NOT_READY`; A-PRE-1 `NOT_AUTHORIZED / NOT_EXECUTED` |

Las diferencias entre los dos hashes locales y `f058…` no demuestran cuál
fuente tiene autoridad normativa. CP052–054 documentan que el crosswalk
descriptivo es independiente de esa elección; significado normativo,
completitud y readiness no lo son.

## 3. Extracción exacta de los gates de CP059

Los siguientes siete IDs corresponden, uno por uno, a H01–H07 de CP059. No se
les agrega una decisión nueva durante la extracción.

| ID estable | Gate propuesto en CP059 | Pregunta literal/resultado que propone | Evidencia previa | Artefactos afectados | Nivel que CP059 le atribuye | Dependencia de baseline | Dependencias declaradas en CP059 | Gates que CP059 hace depender |
|---|---|---|---|---|---|---|---|---|
| `DEC-060-01` | H01 — resolver autoridad/provenance | ¿Puede demostrarse qué contrato normativo rige, o se propone una autoridad prospectiva? | Ledger cita `f058…` como ausente; CP052 no vincula las dos copias a ese artefacto; CP053 conserva STOP | Especificación/overlay/ledger y toda conclusión normativa posterior | L1–L3 | `REQUIRED` para juicios normativos | Recuperación/verificación de provenance; el texto de CP059 ofrece además una elección operativa prospectiva | DEC-02…DEC-07 |
| `DEC-060-02` | H02 — outcomes de 157 leads | ¿Qué outcome relacional corresponde a cada par abierto, conforme a scope y evidencia? | CP058 enumera los 157; 96 refs recuperables y 61 parciales | Relaciones/superficies; si se autoriza después, manifest/ledger | L1; además aporta a L3 | `REQUIRED` para outcome normativo | DEC-01; para casos variant-dependent, criterio/particiones de DEC-05 | DEC-06/07; y sólo donde corresponda, decisiones globales DEC-04 |
| `DEC-060-03` | H03 — outcomes de 10 UNKNOWN relacionales | ¿Qué outcome corresponde a cada relación explícitamente UNKNOWN, o debe permanecer UNKNOWN con fundamento? | CP014/022/024/040 y CP058 §6 conservan razón/alcance sin outcome final | Relaciones/superficies; eventual manifest/ledger | L1; además aporta a L3 | `REQUIRED` para outcome normativo | DEC-01; evidencia semántica por caso; criterio/particiones donde aplique | DEC-06/07; y sólo donde corresponda, DEC-04 |
| `DEC-060-04` | H04 — outcomes globales de 385 filas | ¿Cuál es la disposición final de cada fila si se persigue cierre global? | Manifest/ledger: 385 UNKNOWN y cero finales | Disposition rows del manifest/ledger | L1 global; L3 | `REQUIRED` | DEC-01 y el criterio aplicable de DEC-05; membership no sustituye disposition | DEC-06/07 |
| `DEC-060-05` | H05 — criterio de completitud/variantes, trazabilidad y enforcement | ¿Qué particiones/criterios hacen completa cobertura y qué evidencia de rutas/ABI se admite? | Manifest `coverage_unit_contract` PARTIAL; freeze blockers y ledger identifican trazabilidad/enforcement abiertos | Contrato de cobertura, particiones, trazabilidad, control de launcher, predicate | L1 (criterio); L3 (evidencias) | `REQUIRED` para criterio normativo; `PARTIAL` para evidencia factual | DEC-01; CP059 coloca H02–H04 antes o dentro del criterio sin precisar dependencia | DEC-02…DEC-04; DEC-06/07 |
| `DEC-060-06` | H06 — autorización de reparación/materialización canónica | ¿Se autoriza un cambio controlado de manifest/ledger y qué change set queda aprobado? | 44 YES históricos, diferencias de representación; CP058/059 prohíben inferir materialización | Manifest, ledger, registros de provenance y/o counters, sólo con scope autorizado | L2 | `PARTIAL` por contenido; autorización como acto no selecciona baseline | Outcomes/criterios/evidencia y DEC-01 | DEC-07 |
| `DEC-060-07` | H07 — predicate machine-validated/readiness review | ¿Está definido e implementado un predicate verificable, y se revisan los checks contra evidencia aprobada? | Ledger `predicate_result=false`, no predicate separado machine-validated, readiness NOT_READY | Predicate/ledger/overlay de calificación | L3 | `REQUIRED` para evaluar criterio autorizado; `PARTIAL` para la mera existencia del mecanismo | DEC-01…DEC-05 y evidencias faltantes; DEC-06 sólo si readiness usa el nuevo snapshot canónico | Cierre de L3, sin garantizar pass |

`DEC-060-01` y `DEC-060-05` no son preguntas atómicas en CP059. Se conservan
sus IDs para auditar exactamente la propuesta; las divisiones posteriores
identifican qué es decisión y qué es evidencia/implementación.

## 4. Test de redundancia, por pares

Clasificación según la pregunta de independencia indicada en la directiva.
`INDEPENDENT` significa que responder una no responde la otra; no niega que
haya una dependencia de orden. `SEQUENTIAL_DEPENDENCY` identifica una
precondición real, no duplicación. La matriz considera los siete gates tal
como CP059 los presentó.

| Par | Clasificación | Resultado |
|---|---|---|
| 01–02 | `SEQUENTIAL_DEPENDENCY` | La autoridad/evidencia del contrato precede la interpretación normativa de leads. |
| 01–03 | `SEQUENTIAL_DEPENDENCY` | Mismo prerrequisito para outcomes de los UNKNOWN relacionales. |
| 01–04 | `SEQUENTIAL_DEPENDENCY` | Mismo prerrequisito para dispositions globales normativas. |
| 01–05 | `SEQUENTIAL_DEPENDENCY` | La autoridad debe conocerse antes de afirmar criterios normativos de cobertura; la prueba factual posterior es distinta. |
| 01–06 | `SEQUENTIAL_DEPENDENCY` | Un cambio puede autorizarse como operación, pero contenido canónico correcto requiere criterio/autoridad. |
| 01–07 | `SEQUENTIAL_DEPENDENCY` | No se evalúa readiness contra una norma cuya autoridad no se ha establecido. |
| 02–03 | `SAME_DECISION_DIFFERENT_FORMULATION` | Ambos preguntan outcome de relación syscall-superficie. Se consolidan como un gate relacional con dos sublotes (157 leads y 10 UNKNOWN); cada par mantiene su registro/evidencia. |
| 02–04 | `INDEPENDENT` | Membership de superficie no produce automáticamente un outcome global de disposición/efecto. |
| 02–05 | `SEQUENTIAL_DEPENDENCY` | Los outcomes afectados por flags, operaciones, recursos o variantes dependen del criterio/partición aplicable; no todos los 157 comparten una sola respuesta. |
| 02–06 | `SEQUENTIAL_DEPENDENCY` | No se puede materializar un lead sin outcome y change authorization. |
| 02–07 | `SEQUENTIAL_DEPENDENCY` | Los leads abiertos/evidencia faltante impactan checks de readiness. |
| 03–04 | `INDEPENDENT` | UNKNOWN relacional no equivale a disposición global; las dos salidas se conservan separadas. |
| 03–05 | `SEQUENTIAL_DEPENDENCY` | Varios UNKNOWN dependen de resolver operación/selector/partición antes del outcome. |
| 03–06 | `SEQUENTIAL_DEPENDENCY` | Un eventual cambio relacional requiere outcome y autorización aparte. |
| 03–07 | `SEQUENTIAL_DEPENDENCY` | UNKNOWN sin resolver permanece como condición que readiness debe evaluar. |
| 04–05 | `SEQUENTIAL_DEPENDENCY` | La disposición global necesita criterio autorizado y evidencia adecuada; no se infiere del contador/estado. |
| 04–06 | `SEQUENTIAL_DEPENDENCY` | La edición no puede serializar outcomes globales antes de que existan decisiones sustentadas y autorización. |
| 04–07 | `SEQUENTIAL_DEPENDENCY` | Readiness depende de outcomes globales completos conforme al ledger. |
| 05–06 | `SEQUENTIAL_DEPENDENCY` | Autorizar el change set presupone alcance/criterios identificados; el acto de autorización no los reemplaza. |
| 05–07 | `SEQUENTIAL_DEPENDENCY` | El predicate tiene que comprobar el criterio y las unidades de cobertura autorizadas. |
| 06–07 | `SEQUENTIAL_DEPENDENCY` | Sólo si readiness se evalúa sobre el snapshot modificado; no hay dependencia si se revisa un snapshot distinto, cuya identidad debe declararse. |

No hay dos gates `SUBSUMED_BY_OTHER_DECISION` además de la consolidación
02–03: las demás pares responden preguntas distintas o tienen orden de
precedencia distinto. La categoría `SAME_DECISION_DIFFERENT_FORMULATION` no
borra los diez outcomes; elimina el doble gate organizativo.

### 4.1 H05 separado por pregunta

H05 incluye cuatro cosas no intercambiables:

1. **Criterio normativo de cobertura/particiones** — decisión humana
   dependiente de baseline. No se puede derivar de una lista de flags o de un
   checkpoint.
2. **Static callsite → workload → runtime/native/dependency → syscall** —
   evidencia factual que CP058/manifest dice incompleta. Un humano puede
   aprobar un criterio, pero no puede decidir que una ruta existe sin
   evidencia.
3. **Enforcement x32/i386 en launcher** — evidencia de un control operativo
   que el ledger marca `NOT_QUALIFIED`; definir el criterio es una decisión,
   probar el enforcement es evidencia/calificación.
4. **Predicate machine-validated** — trabajo de especificación/implementación
   y validación, separado de decidir la semántica de una syscall.

Sólo el punto 1 es una decisión normativa unitaria. Los puntos 2–4 se
conservan como gates de evidencia/validación con responsables de ejecución
posterior, no se inflan como decisiones humanas que estos documentos puedan
resolver.

## 5. Circularidad y grafo de dependencias

### 5.1 Dependencias evaluadas

| dependency_id | source | target | type | evidence | circular |
|---|---|---|---|---|---|
| DEP-01 | Evidencia/provenance de la autoridad aplicable | DEC-02, DEC-03, DEC-04 y criterio DEC-05 | `PREREQUISITE` | CP052–054; ledger apunta a `f058…` que no está recuperado/overlay | `NO` |
| DEP-02 | Criterio/partición de cobertura autorizada | Outcomes relacionales DEC-02/03 y globales DEC-04, donde la variante cambia el significado | `SEMANTIC_PRECONDITION` | Manifest `coverage_unit_contract`; CP058 describe casos por backing, flag, comando, ABI y variante | `NO` |
| DEP-03 | Evidencia específica de relación/efecto | Outcome de cada par en DEC-02/03/04 | `EVIDENCE_INPUT` | CP058 §5–6 y lotes fuente; los leads y UNKNOWN no son outcomes | `NO` |
| DEP-04 | DEC-02/03/04 + criterio DEC-05 + evidencia admisible | Autorización/change set DEC-06 | `CHANGE_CONTROL_PRECONDITION` | CP058 P02–P05 y manifest `change_control` | `NO` |
| DEP-05 | DEC-01 authority evidence + DEC-02/03/04 + DEC-05 + evidencia/calificación faltante | Gate de predicate/readiness DEC-07 | `READINESS_PRECONDITION` | Ledger readiness reasons y CP059 H07 | `NO` |
| DEP-06 | DEC-06 | DEC-07, sólo si predicate se ejecuta sobre el snapshot cambiado | `SNAPSHOT_IDENTITY` | Manifest/ledger identifican snapshot/hash y qualification identity | `NO` |
| DEP-07 | DEC-02/03/04 outcomes | Evidencia invocada para justificar DEC-01 como autoridad | `PROHIBITED_SELF_JUSTIFICATION` (riesgo, no dependencia válida) | No hay evidencia permitida que establezca `f058…` por outcomes basados en una copia local | `YES` si se usa; excluida del DAG |

### 5.2 Conclusión de circularidad

El DAG válido es acíclico:

```text
provenance/authority evidence ─┬─> criteria/partitions ─> relation/global outcomes
                               │                            │
                               └────────────────────────────┴─> change authorization
                                                               │
evidence: callsite trace + ABI enforcement + predicate ────────┴─> readiness review
```

El nodo de autoridad sólo puede cerrarse mediante evidencia de identidad,
precedencia y provenance apropiada. El ledger y CP052 indican que el hash
esperado existe como referencia, no que su contenido sea conocido o que una
copia local sea su equivalente.

**Riesgo circular prohibido:** “elegir” `files/` o `docs/` porque una de ellas
permite cerrar el inventario, y luego usar los resultados del inventario como
prueba de que esa copia era la autoridad correcta. También sería circular
decir que el checkpoint es autoritativo porque contiene la misma conclusión
que se intenta usar para elevarlo. La salida permitida mientras falte
provenance es conservar `AUTHORITY_UNRESOLVED`, no resolver el ciclo por
preferencia.

## 6. Suficiencia por nivel

Definiciones usadas aquí:

- **L0 — `DESCRIPTIVE_CROSSWALK`:** snapshot de 385 filas y discrepancias
  descriptivas ya correlacionadas, sin declarar validez normativa.
- **L1 — `GLOBAL_CLOSURE`:** cierre normativo/documental de 048 sobre
  relaciones y outcomes globales; no implica que los archivos canónicos se
  hayan editado.
- **L2 — `CANONICAL_MODIFICATION`:** modificación controlada, verificable y
  autorizada de manifest/ledger.
- **L3 — `A_PRE_0_READINESS`:** evaluación del predicate contra un snapshot y
  overlay autorizados, con todas las evidencias requeridas.

| Nivel | Condiciones necesarias | Gates/decisiones requeridos | ¿Suficientes hoy? | Resultado |
|---|---|---|---|---|
| `L0_DESCRIPTIVE_CROSSWALK` | 385 filas únicas; campos actuales descritos; checkpoint-only, leads, UNKNOWN y provenance marcados sin inferir | Ninguno: evidencia suficiente ya incorporada en CP055–059 | **Sí, ya está cerrado** | No crear decisión humana para L0 |
| `L1_GLOBAL_CLOSURE` | Autoridad normativa demostrada; criterio autorizado; relaciones/outcomes por unidad con evidencia; 385 disposiciones globales finales o UNKNOWN sustentados por una regla de cierre autorizada; diferencias categorizadas | DEC-060-01 como gate de evidencia; criterio de DEC-060-05; gate relacional consolidado DEC-060-02/03; DEC-060-04 | **No** | Faltan authority evidence, criterios y evidencia por caso. La mera existencia de 44 YES históricos no completa L1 |
| `L2_CANONICAL_MODIFICATION` | L1 para el contenido afectado; change set exacto, source refs/justificación; autorización y hash/review del diff; preservar el scope de cada relación | L1 + DEC-060-06; agrupación de cambios puede incluir materialización documental y outcomes autorizados, no adjudicarlos | **No** | Ningún cambio canónico autorizado en esta tarea |
| `L3_A_PRE_0_READINESS` | L1; disposition global completa; finite partitions; static traceability suficiente; x32/i386 enforcement calificado; predicate machine-validated; identidad overlay/spec/snapshot comprobable; ledger checks pasan | L1 + evidencia EVID-01/EVID-02 + gate predicate DEC-060-07; L2 sólo si la evaluación requiere otro snapshot | **No** | Ledger dice `NOT_READY`, `predicate_result=false`; no evaluable como READY |

L1 se entiende como cierre **normativo**, en distinción explícita del cierre
descriptivo de CP058. Aún si una futura operación decide preservar un
UNKNOWN, sólo podría contar como cierre normativo cuando el criterio
autorizado admita explícitamente esa salida; hoy no hay evidencia para
presuponerlo.

## 7. Dependencia del baseline: histórico versus normativo

| Afirmación | Baseline como evidencia histórica | Baseline como autoridad normativa | Clasificación |
|---|---|---|---|
| El ledger contiene path/hash `f058…` y declara `present_in_qualified_overlay=false` | Sí: hecho de registro reproducible, bytes externos ausentes | No prueba qué texto contenía ni qué contrato gobierna | `NONE` para describir ese campo |
| Hay dos archivos locales con hashes distintos | Sí: existencia/integridad de esas copias | No determina cuál debe regir | `NONE` para comparar; `REQUIRED` para elegir criterio normativo |
| CP024/026/028 escribieron 44 YES condicionales y CP014/016 escribió 23 exclusiones | Sí: puede atribuirse exactamente a esos documentos | Un checkpoint no es autoridad automática para canon/readiness | `NONE` para historia literal; `REQUIRED` para declarar efecto normativo |
| CP055/056 describe 385 filas y sus campos | Sí: crosswalk y correlación actuales | No requiere adoptar contenido de baseline | `NONE` |
| 157 leads / 10 UNKNOWN mantienen esos estados descriptivos | Sí | No decide cómo el contrato aplicable clasifica su significado | `NONE` para estado actual; `REQUIRED` para outcome |
| Completitud de memberships, efecto/exclusión, variants y cierre global | Evidencia histórica puede informar, no establece precedencia | Sí, define qué cuenta como completo y admisible | `REQUIRED` |
| Cambio canónico y A-PRE-0 readiness | Historial puede informar provenance/change control | Sí, contenido correcto y predicate se evalúan contra autoridad identificada | `PARTIAL` para autorización de cambio; `REQUIRED` para justificar contenido/readiness |

Un hash prueba identidad de bytes sólo si esos bytes están disponibles para
hash; no prueba procedencia, equivalencia con otra revisión ni autoridad.

## 8. Suficiencia de evidencia para cada gate

Clasificación aplicada al **estado actual**, no a evidencia hipotética que
podría obtenerse en el futuro.

| ID/gate | Estado de evidencia | Explicación |
|---|---|---|
| DEC-060-01 — autoridad/provenance | `NOT_DECIDABLE_WITH_CURRENT_EVIDENCE` | El hash externo está citado pero no recuperado; las dos copias locales difieren. Un humano no puede convertir eso en identidad histórica demostrada por acto de voluntad. |
| DEC-060-02 — 157 leads | `REQUIRES_BASELINE_AUTHORITY` y, en múltiples pares, `NOT_DECIDABLE_WITH_CURRENT_EVIDENCE` | La lista y provenance status existen; lead no es evidencia de efecto/outcome. CP058 deja necesidades específicas por recursos, flags, comandos, syscall-family y variantes. Los 61 pares no tienen fuente primaria individual. |
| DEC-060-03 — 10 UNKNOWN relacionales | `REQUIRES_BASELINE_AUTHORITY` y `NOT_DECIDABLE_WITH_CURRENT_EVIDENCE` | Los checkpoints explican por qué están UNKNOWN; no contienen decisiones finales ni resuelven las fronteras semánticas. |
| DEC-060-04 — 385 outcomes globales | `REQUIRES_BASELINE_AUTHORITY` | El estado actual 385 UNKNOWN es decidible como dato, no como outcome. Las memberships/relaciones no reemplazan el análisis global de efectos requerido por el propio manifest. |
| DEC-060-05a — criterio/particiones de coverage | `REQUIRES_BASELINE_AUTHORITY` | El contrato local disponible es evidencia de una revisión, no prueba que sea la autoridad del overlay; manifest declara `completion_status=PARTIAL`. |
| DEC-060-05b — static trace evidence | `DECIDABLE_AFTER_DOCUMENTARY_REPAIR` | Para afirmar qué callsites/rutas existen se requiere traza/captura documental admisible, hoy marcada incompleta; ningún voto la sustituye. No se ejecuta esa recolección en esta tarea. |
| DEC-060-05c — x32/i386 enforcement | `DECIDABLE_AFTER_DOCUMENTARY_REPAIR` | Criterio de exclusión consta; ledger lo marca `NOT_QUALIFIED`. La conclusión sobre enforcement requiere evidencia/calificación, no decisión sobre el valor del campo. |
| DEC-060-06 — autorización de canonical change | `DECIDABLE_NOW` sólo como permiso de proceso/change control, no como aprobación de contenido | La autorización de un diff concreto requiere que exista un change set sustentado; no hay change set propuesto y la tarea prohíbe modificación. No es permiso implícito ni decisión actualmente solicitada. |
| DEC-060-07 — predicate/readiness review | `DECIDABLE_AFTER_DOCUMENTARY_REPAIR` para definir mecanismo; `REQUIRES_BASELINE_AUTHORITY` para evaluar el resultado normativo | El ledger constata que no hay predicate separado machine-validated y el resultado actual es false; un pass no se puede decidir por deliberación. |

En el uso estricto de categorías, si un gate combina condiciones se informa
la más bloqueante y se desglosan sus subcondiciones. `DECIDABLE_NOW` para
autorizar una operación no significa que esa operación esté autorizada en
este checkpoint ni que pueda modificar el canon.

## 9. Taxonomía de causas para las 385 disposiciones UNKNOWN

Las causas no son mutuamente excluyentes ni suman 385. CP058 establece
unidades descriptivas y de relación; ninguna de las siguientes categorías
transforma automáticamente un UNKNOWN en una tarea única o en un outcome.

| Causa documentada | Alcance/cuánto cubre | Gate responsable | Lo que falta |
|---|---|---|---|
| Falta de membership/candidate context | 187 filas sin `candidate_surface_ids` según el recálculo actual de CP056/058; 184 filas sin contexto. Son medidas de representación, no prueba de NO | DEC-060-02/03 para relaciones relevantes; DEC-060-04 para disposición global | Relación/superficie respaldada o exclusión por efecto; no llenar IDs por inferencia |
| Falta de variant partition | El contrato de cobertura está `PARTIAL`; el universo de unidades finitas no está enumerado en las cifras de fila | DEC-060-05a | Selectores, valores, clase de recurso, fase y criterio de cierre según norma autorizada |
| Falta de effect evidence | 385/385 dispositions siguen UNKNOWN y el manifest declara cero finales; cantidad de filas por subtipo causal no demostrada | DEC-060-04, con evidencia por unidad | Evidencia de efecto o exclusión que cumpla el criterio |
| Falta de provenance | 61 relaciones parciales; adicionalmente el artefacto externo `f058…` no fue recuperado | DEC-060-01 como prerequisite; DEC-060-02 sólo cuando el resultado invoca linaje histórico | Fuente individual para afirmar origen; autoridad/provenance para fijar el contrato |
| Dependencia de superficie | 157 leads y 10 UNKNOWN relacionales; una syscall puede participar en varias superficies | DEC-060-02/03 (gate relacional consolidado) y DEC-060-04 por separado | Outcome por par y, separadamente, outcome global |
| Dependencia de baseline | Aplica al juicio normativo sobre el contrato/scope, no al conteo descriptivo de filas | DEC-060-01 (prerrequisito evidencial) | Identidad, precedencia y authority evidence |
| Trazabilidad de workload | Manifest marca static call-site mapping como freeze blocker; no está completo | DEC-060-05b (gate de evidencia, no decisión) | Cadena workload→Python/native/dependency→syscall con evidencia admisible |
| Enforcement ABI | Ledger marca x32/i386 excluidos por scope y enforcement `NOT_QUALIFIED` | DEC-060-05c (gate de calificación) | Evidencia de rechazo en el límite del launcher o cambio formal de scope, fuera de esta tarea |

Los datos de CP058 permiten contar 385 outcomes UNKNOWN, 157 leads, 10
UNKNOWN relacionales y 61 provenance partial. No permiten asignar a cada fila
global una y sólo una causa primaria. Forzar particiones disjuntas sería una
clasificación normativa nueva.

## 10. Test de los 157 leads y los 61 provenance partial

### 10.1 Grupos de CP059 verificados como rollups, no decisiones comunes

Los IDs LG04/LG05/LG06/LG10/LG11/LG15/LG16 son grupos de consulta por
superficie, no un solo outcome por grupo. Sus miembros, según CP058, son:

| Grupo | Miembros | Criterio/evidencia común real | Excepciones / división necesaria | Dependencia |
|---|---:|---|---|---|
| LG04 / S04 | 5 | Leads identificados por CP019/020 | Mezcla cuotas, xattrs y file attributes; no un único efecto/outcome común | `REQUIRED` |
| LG05 / S05 | 17 | Superficie general de memoria/archivo | Backing file-backed, residencia, NUMA, remap y advice; múltiples operaciones/variantes | `REQUIRED` |
| LG06 / S06 | 19 | Superficie general de memoria anónima | Heap, memfd, NUMA, residencia, shadow stack y seal son cuestiones diferenciadas; overlap NR con S05 no fusiona relaciones | `REQUIRED` |
| LG10 / S10 | 36 | CP011/012 agregan un lote de timers/scheduler/futex y CP049 registra 36 refs | Familias timer, scheduler, affinity, signal/timer FD, futex y rseq no admiten outcome colectivo; 36 tienen provenance parcial | `REQUIRED`; provenance histórica `PARTIAL` |
| LG11 / S11 | 26 | CP033 identifica evidencia directa para cuatro miembros; CP058/059 ubica 22 con soporte agregado | Separar al menos 4 con referencia exacta y 22 provenance partial; además identidad, scheduler, ptrace, process_vm, kcmp y process release son efectos diferentes | `REQUIRED`; para 22, provenance `PARTIAL` |
| LG15 / S15 | 3 | Inventario de tres interfaces opacas | `security`, `uretprobe`, `uprobe` son APIs/operaciones separadas; nombres no deciden pertenencia | `REQUIRED`; provenance `PARTIAL` |
| LG16 / S16 | 51 | CP041 lista las 51 referencias | Identidad/credenciales, kernel/module, namespaces/LSM y controles son familias normativas diferentes | `REQUIRED` |

Verificación aritmética del conjunto de tags:

```text
5 + 17 + 19 + 36 + 26 + 3 + 51 = 157 relaciones abiertas
157 + 5 tags superpuestos con exclusiones = 162 tags
```

Los cinco overlaps permanecen identificados y no vuelven al set: S01 NR
253/255/294/300 y S04 `umask` NR 95. En cambio, overlap de un NR entre
superficies (p. ej. S05/S06 o S11/S16) sí son pares de relación distintos.

**Conclusión de minimalidad:** mantener siete grupos de superficie como
índice de evidencia es útil, pero afirmar que son siete decisiones comunes
sería ocultar diferencias. Las decisiones se registran por la cuestión
relacional/efecto que la evidencia permita delimitar; no se suman como 157
sesiones humanas, ni se colapsan en siete outcomes colectivos.

### 10.2 Provenance de los 61 pares

| Subgrupo | Requiere acción por sí solo | Requiere autoridad para outcome normativo | Puede bloquear outcome | Afirmación limitada |
|---|---|---|---|---|
| S10, 36 | No para crosswalk; sí recuperar source si se quiere afirmar quién/qué los originó | Sí para decidir pertenencia bajo contrato | Sólo si la decisión pretende usar provenance agregada como evidencia decisiva; la falta de linaje por sí sola no prueba NO | No atribuir a checkpoint individual |
| S11, 22 | No para crosswalk; sí para provenance individual | Sí para outcome bajo contrato | Igual; cuatro referencias recuperables de S11 no prueban los otros 22 | No atribuir a CP033/034 los 22 |
| S15, 3 | No para crosswalk; sí si una conclusión necesita linaje individual | Sí para outcome bajo contrato | Sólo si la decisión depende del origen histórico | No completar por similitud de API |

Clasificación: **0/61 requieren acción para cerrar L0**; **61/61 no
demuestran outcome normativo y quedan sujetos al gate relacional**, pero no
constituyen un gate de provenance separado para todo caso. Si evidencia
semántica independiente suficiente apareciera, ese outcome no exigiría
reconstruir un origen histórico que no se usa. Ningún linaje se completa aquí.

## 11. Test de las 77 checkpoint-only

“Está en un checkpoint” sólo demuestra que el documento hizo esa afirmación;
no crea una decisión nueva en 060. La presencia histórica tampoco autoriza
materializarla.

| Relaciones | Ya representadas canónicamente | Evidencia checkpoint | Clasificación para decisión actual | Gate/acción si L2 requiere completitud |
|---|---|---|---|---|
| 44 YES condicionales (9 S06, 17 S07, 18 S08) | No como adjudicaciones serializadas completas; 42 tienen contexto U, dos S08/54–55 no tienen contexto S08 actual | CP024/026/028; CP046 confirma diferencia de representación y scope | No nueva decisión relacional: outcomes históricos documentados; no usar sólo checkpoint como autoridad normativa | Incluir en change set de DEC-060-06 únicamente si el criterio autorizado exige esa representación y se acredita evidencia fuente |
| 19 exclusiones S02 | Checkpoint-only conforme a CP058 | CP016; exclusiones de relación, no outcome global | `NOT_A_BLOCKER`; no reabrir por su sola aparición en un checkpoint | Sólo incluir si un modelo canónico completo requiere explicitarlas; sin inferir dispositions globales |
| 4 exclusiones S01 | Checkpoint-only conforme a CP058 | CP014; también explican cuatro tags redundantes | `NOT_A_BLOCKER`; no contarlas como leads abiertos | Igual que arriba; no reabrir ni duplicar tags |
| 10 UNKNOWN relacionales | No materializados como outcome final | CP014/022/024/040; UNKNOWN explícito | Requieren el gate relacional consolidado, no por ser checkpoint-only sino porque no hay outcome final | Cualquier edición posterior queda bajo DEC-060-06 |

Cardinalidad: `44 + 19 + 4 + 10 = 77`. Ninguna de las 67 decisiones
históricas YES/NO se transforma en adjudicación nueva por CP060. Ninguna se
materializa. Los diez UNKNOWN ya aparecen en el set relacional de 10, no se
añaden por segunda vez.

## 12. Set mínimo de decisiones y gates

El set mínimo distingue **decisiones humanas**, **prerrequisitos de
evidencia** y **validaciones**. Suprimir cualquier decisión listada deja
bloqueada una afirmación o acción específica; suprimir cualquiera de los
prerrequisitos factuales impide alegar evidencia suficiente, pero no crea una
decisión semántica.

### 12.1 `MINIMAL_DECISION_SET`

| DECISION_ID | QUESTION | WHY_REQUIRED | EVIDENCE_AVAILABLE | BASELINE_DEPENDENCY | LEVEL_UNLOCKED | DEPENDS_ON | UNLOCKS | REMOVAL_TEST |
|---|---|---|---|---|---|---|---|---|
| `MDS-01` | Para cada par syscall-superficie abierto, ¿qué outcome está respaldado o debe seguir UNKNOWN? | Membership y UNKNOWN relacionales son salidas distintas del global; 167 pares abiertos no se cierran por sus tags | 157 leads listados + 10 UNKNOWN con razones documentales; evidencia específica desigual/incompleta | `REQUIRED` | L1 | `GATE-E01`; criterio MDS-03; evidencia por relación | Cierra relación sólo al nivel justificable; alimenta pero no determina MDS-02 | Sin él siguen 157 leads y 10 UNKNOWN sin outcome relacional justificado |
| `MDS-02` | Para cada una de las 385 filas, ¿qué disposition global corresponde conforme al contrato y evidencia? | Manifest define disposición global aparte; actualmente 385/385 UNKNOWN y cero final | Universo 385, identidad del register y estado UNKNOWN verificados; no hay disposition final | `REQUIRED` | L1 | `GATE-E01`; criterio MDS-03; evidencia de efecto | Permite reclamar cierre global sólo con resultados admitidos | Sin él las 385 siguen UNKNOWN; membership YES/NO no responde la pregunta global |
| `MDS-03` | Una vez establecida la autoridad aplicable, ¿qué criterio y particiones finitas bastan para declarar cobertura/variantes completas? | El contrato exige unidades por surface/syscall/ABI/selector/resource/phase/outcome y declara PARTIAL | Manifest identifica los ejes y requisitos de campos; no enumera cierre finito completo; la autoridad sigue unresolved | `REQUIRED` | L1 para criterio; prerequisite de L3 | `GATE-E01` | Da regla para variantes y soporta MDS-01/02 donde una variante cambia significado | Sin él no se puede afirmar finite coverage ni evaluar UNKNOWN fuera de partición |
| `MDS-04` | ¿Se autoriza este change set canónico exacto, con refs y justificación revisables? | Una conclusión documental no concede permiso para editar manifest/ledger | No hay change set propuesto en CP060; el contenido debe provenir de gates previos | `PARTIAL`: autorización del acto distinta de autoridad semántica del contenido | L2 | `GATE-E01`, MDS-01…03 en lo que el change set toque; evidencia source/custody; revisión/hash | Autoriza sólo diff definido, no arreglos amplios ni cambios derivados automáticamente | Sin él ningún cambio a manifest/ledger queda legítimamente autorizado |

**Conteo:** cuatro familias mínimas de decisión humana en este modelo. Este
conteo es de **familias/preguntas**, no de deliberaciones ni unidades: MDS-01
preserva 167 relaciones (cada cual puede necesitar un outcome independiente);
MDS-02 preserva 385 unidades de salida. No hay evidencia para afirmar “cuatro
reuniones”, “167 decisiones humanas” o “385 deliberaciones”.

La identidad de `f058…` no es una decisión MDS: la recuperación/provenance es
el prerrequisito externo GATE-E01. MDS-03 sólo define cómo aplicar un
criterio cuya autoridad se haya establecido; no selecciona una copia local.
Una eventual elección prospectiva de un nuevo criterio sería un acto
normativo distinto; no se incorpora ni recomienda en este checkpoint.

### 12.2 Gates de evidencia/validación requeridos para readiness (no decisiones)

| GATE_ID | Condición objetiva | Estado actual | Afecta nivel | Por qué no es decisión humana |
|---|---|---|---|---|
| `GATE-E01` | Recuperar y demostrar identity/provenance/precedencia de la autoridad normativa que el ledger declara | `UNRECOVERED`; `AUTHORITY_UNRESOLVED` | L1–L3 | No se puede fabricar origen o equivalencia mediante votación |
| `GATE-E02` | Evidencia de static workload→Python/native/dependency→syscall completa según criterio autorizado | Incompleta; manifest la marca freeze blocker | L3 | La ruta existe o no existe; falta evidencia registral |
| `GATE-E03` | Calificación del enforcement x32/i386 en launcher | `NOT_QUALIFIED` | L3 | La existencia del control requiere evidencia/calificación |
| `GATE-E04` | Predicate machine-validated que consume criterio, snapshot y evidencia correctos | No existe separado; ledger `predicate_result=false` | L3 | Construcción y validación de artefacto, no decisión de outcome |
| `GATE-E05` | Identidad/revisión de snapshot y overlay usados para el readiness check | Overlay citado, artefacto normativo ausente | L3 | Verificación de identidad/integridad no resuelve autoridad por sí sola |

Una especificación de criterio decidida en MDS-04 no produce por sí misma
callsite trace, enforcement calificado ni predicate verificado.

## 13. Grafo final de decisiones

```text
L0_DESCRIPTIVE_CROSSWALK
└── CERRADO; no requiere decisión nueva

GATE-E01: authority/provenance evidence (no elección por inferencia)
└── MDS-03: criterio normativo/particiones finitas
    ├── MDS-01: outcomes relacionales abiertos (157 leads + 10 UNKNOWN)
    ├── MDS-02: outcomes globales (385 filas)
    └── MDS-04: autorización de change set exacto → L2_CANONICAL_MODIFICATION
        └── GATE-E02 + GATE-E03 + GATE-E04 + GATE-E05
            └── revisión readiness L3_A_PRE_0 (predicate puede fallar)
```

Las relaciones MDS-01 y dispositions MDS-02 son salidas independientes;
MDS-03 puede preceder sólo las unidades para las que una partición cambia
la pregunta. No se afirma un orden total entre todas las filas. La revisión
L3 verifica criterios/evidencia; no es una decisión que convierta el estado
en READY.

## 14. `NOT_DECISIONS`

- 11 stale counters: aritmética/descripción histórica reproducible; no
  requieren deliberación ni reparación para L0/L1.
- Contador 63 `SCOPE_UNPROVEN`: excluir como métrica; no crear un gate para
  definirlo mientras ningún nivel dependa de él.
- Discrepancias representacionales y defaults ausentes de campos: registrar
  estructura actual; no confundir diferencia de serialización con decisión
  semántica.
- 44 YES checkpoint-only y 23 exclusiones: outcomes históricos describibles,
  no decisiones nuevas por aparecer en checkpoint; eventual materialización
  se somete al change authorization MDS-04.
- Los 61 provenance partial: no son un gate general ni una decisión; sólo
  recuperar fuente si una afirmación/outcome invoca el linaje individual.
- Cinco tags con exclusiones ya documentadas: no son cinco leads abiertos ni
  se reabren automáticamente.
- Hashes, unicidad, recuentos, whitespace y `git diff --check`: verificaciones
  de integridad, no decisiones.
- 385 estados `UNKNOWN`: describirlos es estado, no 385 tareas automáticamente.
  Para salir de UNKNOWN se necesita MDS-02; una relación de superficie no
  sustituye su outcome.
- Los 10 UNKNOWN relacionales están dentro del gate relacional MDS-01, no
  como un segundo tipo de autorización.
- “Decidir authority” por escoger la spec con mayor tracking/fecha/ruta/hash:
  no es una decisión válida ni evidencia histórica.
- “Aprobar READY” mediante voto: readiness requiere que gate de predicate y
  evidencias pasen; no es una decisión sustitutiva.

## 15. Invariantes finales y verificación

| Verificación | Resultado |
|---|---|
| Filas / nombres / NR | 385 / 385 únicos / 385 únicos |
| Leads | 162 tags; 5 exclusiones solapadas; 157 relaciones abiertas, agrupadas en CP058/059 |
| UNKNOWN relacionales | 10, preservados |
| Provenance partial | 61 (S10 36, S11 22, S15 3), no completados |
| Checkpoint-only | 77 = 44 YES + 23 exclusiones + 10 UNKNOWN; no materializados |
| Baseline | `AUTHORITY_UNRESOLVED`; `f058…` sigue `UNRECOVERED` |
| Inventory/global outcomes | `frozen=false`; 385/385 `UNKNOWN` |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Canon | Sin cambios a manifest, ledger, specs, lock o crosswalk |
| Actividad dinámica | Ninguna; no TALOS, FastAPI, workloads, probes, benchmarks, VM, DB, corpus o modelos |
| Whitespace | `git diff --check` y revisión de trailing whitespace limpios |
| Hashes protegidos | Coinciden con §2 |

Resultado de salida: L0 permanece cerrado; no se recomienda ni resuelve
ninguna decisión. La autoridad de baseline queda expresamente sin resolver.
