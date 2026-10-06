# Checkpoint 070 — auditoría de necesidad del Camino A

Fecha: 2026-10-01

## 1. Resultado

```text
RESULT = EXTERNAL_AUTHORITY_MATERIALLY_REQUIRED
EXTERNAL_AUTHORITY_NECESSARY = YES
BASELINE_SPEC_AUTHORITY = AUTHORITY_UNRESOLVED
EXTERNAL_SPEC_ARTIFACT = UNRECOVERED
GATE_EXTERNAL_EVIDENCE_AUTHORIZATION = NOT_AUTHORIZED
```

La dependencia material no se extiende a todo hecho sobre TALOS ni a toda
medición operacional. Se limita al cierre normativo/global y a la calificación
formal de A-PRE-0 bajo el objetivo y predicate documentados: éstos exigen
criterio e inventario con autoridad identificada, evidencia enlazada al mismo
snapshot cualificado y ausencia de unidades requeridas `UNKNOWN`. La evidencia
operacional histórica permite afirmaciones acotadas sobre casos concretos,
pero no sustituye el criterio, el inventario final ni la identidad normativa
requerida para ese cierre.

“Externa” no significa que el hash particular `f058…` sea la única vía
concebible. El requisito material es establecer autoridad de baseline. Una
designación válida de otro artefacto por un actor/proceso competente podría
ser una vía distinta; no existe tal designación en la evidencia disponible y
no se crea en CP070. La búsqueda de evidencia externa continúa no autorizada.

## 2. Estado de entrada y fuentes

Se preservan los estados de CP063–069:

```text
STOP_REASON = OPEN_EXTERNAL_EVIDENCE_REQUIRED
SCOPE_UNPROVEN = PRESERVED
inventory.frozen = false
A_PRE_0 = NOT_READY
A_PRE_1 = NOT_AUTHORIZED / NOT_EXECUTED
```

Fuentes leídas en modo documental: CP050–069 pertinentes; manifest y ledger;
la copia local `files/A_PRE_0_BASELINE_SPEC.md`; checkpoints de adjudicación
S01/S02 y S12–S16; la evidencia histórica que el ledger ya referencia. No se
consultaron los paths externos citados en el ledger ni se abrió evidencia
fuera del workspace. No hubo web/GitHub/GitLab/contacto, probes nuevos,
ejecución de TALOS, VM o modificación canónica.

## 3. Qué bloquea exactamente `f058…`

`f058…` no recuperado bloquea vincular una especificación concreta al campo
`current_normative_spec` del overlay declarado y, con ello, demostrar qué
criterio rige una evaluación normativa ligada a ese overlay. La siguiente
matriz separa esa afirmación de los hechos operacionales e históricos:

| CLAIM | DEPENDENCY_ON_BASELINE | WHY | CURRENT_EVIDENCE |
|---|---|---|---|
| “La revisión normativa que gobierna la calificación del overlay v4 es el artefacto identificado por `f058…`.” | `DIRECT` | El ledger registra path/hash pero el objeto no está en el overlay ni se recuperó; falta identidad verificable y autoridad. No puede afirmarse que una copia local sea ese artefacto. | Ledger `qualification_identity.current_normative_spec`: path externo, SHA `f058…`, `present_in_qualified_overlay=false`; CP052/064 no hallaron identidad local equivalente. |
| “El conjunto actual de 16 superficies y sus fronteras es el inventario normativo completo/requerido para A-PRE-0.” | `DIRECT` | El manifest se describe como propuesta no congelada (`frozen=false`); identificar los dominios requeridos y cierre aceptable es una afirmación normativa, no sólo contar sus objetos. | Manifest contiene 16 superficies; ledger registra `surface_count=16`, freeze blockers y 385 filas UNKNOWN. |
| “Las relaciones syscall↔surface y exclusiones documentadas bastan para un cierre L1 normativo.” | `DIRECT` | Los checkpoints prueban que se documentaron outcomes y scopes históricos; no establecen por sí solos el criterio autorizado ni la regla que permite declarar cierre. | Adjudicaciones S01–S16 y CP055/056; CP060 identifica authority y criterion como prerequisitos de L1. |
| “El estado 385/385 `UNKNOWN` satisface la regla de cierre global aplicable.” | `DIRECT` | Un estado serializado es un hecho; si UNKNOWN es admisible para closure y bajo qué criterio debe establecerlo una fuente autorizada. | Manifest/ledger tienen 385 dispositions UNKNOWN; CP060 DEC-060-04 exige authority para outcomes globales. |
| “A-PRE-0 está `READY` para el snapshot cualificado y su predicate.” | `DIRECT` | El predicate vigente exige inventario congelado, paths/casos requeridos cerrados, evidencia del mismo snapshot/policy/platform/threat model y que la revisión normativa actual esté en el overlay. La revisión `f058…` no está allí; otros términos también fallan. | Ledger predicate v2 `result=false`; causa explícita: `qualified overlay does not contain current normative spec hash`; además `inventory.frozen=false`, UNKNOWN, traceability incompleta, etc. |
| “Una denegación seccomp específica bajo el perfil probado ocurrió y cubrió ese subcaso.” | `NOT_REQUIRED_FOR_TARGET` | La proposición factual histórica se limita al caso, perfil/hash y evidencia registrados; no requiere declarar qué baseline es normativa. | Ledger guarda casos BLOCKED para nueve llamadas async y refs/hash de probe/isolation; CP050 limita el alcance. |
| “El mecanismo X está ausente/inofensivo para todos los workloads o variantes.” | `DIRECT` | Es un claim universal de cobertura/seguridad que requiere scope completo, criterion autorizado, rutas alternativas y evidencia sin UNKNOWN; no se sigue de los casos acotados. | Manifest conserva UNKNOWN en dominios/rutas; predicate exige todo path/case requerido y alternativas explícitas. |

Las dos primeras afirmaciones y la decisión de closure afectan el target
práctico A-PRE-0; las afirmaciones universales no pueden sustituirse por
subcasos observados. El historial literal (qué checkpoint escribió qué) se
puede conservar sin autoridad, pero no equivale al claim normativo
correspondiente.

## 4. Matriz de dependencia de claims

| CLAIM / objetivo | Clasificación | Base |
|---|---|---|
| Hashes, bytes, rutas locales, referencias y contenidos documentales actuales | `DERIVABLE_INDEPENDENTLY` | Verificación local/lectura documental; no declara cuál fuente rige. |
| Existencia e identidad de la referencia ledger `f058…`, y que el ledger registra ausencia en overlay | `DERIVABLE_INDEPENDENTLY` | Se prueba que el registro contiene esos valores, no la identidad de bytes externos. |
| Que CP014/016/024/026/028/030/032/034/036/038/039/040/041/043 documentan decisiones con scopes históricos concretos | `DERIVABLE_INDEPENDENTLY` | Puede atribuirse el contenido al checkpoint; no se eleva a autoridad actual ni canon. |
| Resultado operacional exacto de los casos históricos acotados (sección 7) | `DERIVABLE_INDEPENDENTLY` para el hecho histórico; `INDIRECT` para usarlo en readiness | El caso puede afirmarse bajo su scope. Para contar como evidencia calificante se exige rebinding y validación contra el snapshot/criterio autorizados. |
| Qué criterio debe gobernar el cierre normativo de memberships, variantes y 385 dispositions | `DIRECT` | CP060–062 dicen explícitamente que la authority es required para outcomes/criterion; las copias locales no resuelven cuál rige. |
| L1: cierre global normativo de 048 | `DIRECT` | Requiere authority, criterion, evidencia por unidad y regla autorizada para el tratamiento de outcomes/UNKNOWN (CP060). |
| L2: edición canónica limitada a hechos puramente descriptivos, si se autorizara y no alterara significado | `INDIRECT` | Un cambio de formato/descripción puede justificarse por evidencia propia; un cambio de membership, disposition, criterio o contenido normativo sí requiere authority. No se propone cambio. |
| L3: calificación formal `A_PRE_0_READY` del target actual | `DIRECT` | El predicate v2 requiere la revisión normativa actual dentro del overlay y todos los demás términos; el ledger consigna esa ausencia como causa falsa. |
| Cierre operativo estrecho: “este perfil/hash denegó estos syscalls/subcasos concretos” | `NOT_REQUIRED_FOR_TARGET` | Puede reportarse como resultado histórico delimitado sin adoptar baseline; no constituye cierre completo de TALOS/A-PRE-0. |
| Afirmar que la autoridad externa no es necesaria porque existen algunos `BLOCKED`/`OBSERVED` | `DIRECT` (dependencia inválida) | Los resultados de efecto no identifican criterion, inventario requerido, scope total ni authority; el ledger dice que 0 casos históricos son elegibles para el predicate actual. |

## 5. Requisitos de A-PRE-0, uno por uno

La matriz toma los 17 `required_checks` del ledger predicate v2, junto a las
causas actuales y el predicate exacto de la spec local. No recalcula ni cambia
el estado global.

| REQUIREMENT | EVIDENCE_ALREADY_AVAILABLE | BASELINE_AUTHORITY_REQUIRED | ALTERNATIVE_EVIDENCE | STATUS |
|---|---|---|---|---|
| `inventory.frozen is true` | Campo actual `false`; 16 superficies y 385 filas enumeradas | Sí, para definir/aceptar el inventario requerido y sus fronteras bajo el criterio objetivo | Revisión descriptiva/operacional puede documentar los dominios, pero no declarar cierre normativo o freeze | `BASELINE_BLOCKED` |
| Target ABI, kernel release y syscall-table source identity bound | Ledger enlaza ABI/kernel y package/source/table hashes; firma OpenPGP no verificada | No para verificar literalmente esos identificadores; sí para declarar suficiente la identidad normativa objetivo | Hash/fuente del paquete y tabla; firma verificable sería evidencia adicional de integridad/origen | `PARTIALLY_DEPENDENT` |
| x32/i386 excluidos por scope y launcher enforcement qualified | Exclusión consta; enforcement `NOT_QUALIFIED` | El scope declarado es documental; criterio de aceptación depende del contrato autorizado | Evidencia operacional independiente del launcher/policy podría calificar el enforcement bajo un criterio ya autorizado | `PARTIALLY_DEPENDENT` |
| Required surface IDs coinciden exactamente con canonical manifest | Manifest enumera 16; `frozen=false`; propuesta marcada como no calificación | Sí, para la afirmación de que ese set es el canonical/requerido | Conteo/listado estructural reproducible sólo confirma el set presente | `BASELINE_BLOCKED` |
| Cada required path/case explícito y `OBSERVED` o `BLOCKED` | Ledger documenta casos concretos y múltiples `UNKNOWN`/dominios UNKNOWN | Sí, para definir qué paths son requeridos; no para describir un caso histórico | Nuevos resultados de caso podrían medir un subcaso, pero no elegir el conjunto requerido | `PARTIALLY_DEPENDENT` |
| Cada status con refs y hashes válidos | Refs y hashes están serializados; validez de bytes referenciados no queda establecida sólo por la cadena del ledger | No para verificar integridad hash factual; sí para decidir elegibilidad normativa | Recuperar/verificar los artefactos citados y sus bytes/identidad, sin convertirlos en autoridad | `SATISFIABLE_INDEPENDENTLY` |
| OBSERVED demuestra evento/recurso/proceso/resultado para scope declarado | 16 OBSERVED históricos delimitados, con limitaciones por subcaso | No para repetir el hecho histórico; sí para acreditar que el scope es requerido/representativo | Inspección de evidencia exacta o nueva medición operacional acotada | `PARTIALLY_DEPENDENT` |
| BLOCKED enlaza denegación con policy/resource/process activos | 11 BLOCKED históricos, incluyendo nueve async bajo perfil/hash exactos | No para el evento exacto; sí para acreditar cobertura requerida al objetivo actual | Reproducción/validación de artifacts del caso exacto y snapshot/policy; no extrapolar otros dominios | `PARTIALLY_DEPENDENT` |
| Alternative paths tienen cases o rationale OOS | Paths/variants incompletos; varios unknown paths explícitos | Sí, para decidir qué rutas/variantes son suficientes o fuera de scope | Inventario operacional puede encontrar/medir rutas, no autorizar omitirlas | `PARTIALLY_DEPENDENT` |
| Misma qualified snapshot, policy, platform y threat model | Ledger identifica un overlay pero declara que no contiene el hash normativo; evidencia histórica no está re-vinculada | Sí, para identificar revisión normativa/overlay que gobierna el target | Crear más hashes locales no sustituye la identidad autorizada del baseline/snapshot | `BASELINE_BLOCKED` |
| Sensor requirements separados; Python audit telemetry no cierra surface | `sys.addaudithook` está `AUXILIARY_ONLY`/`PARTIAL`; regla expresa en ledger/spec | No para describir arquitectura del sensor; criterion required para darlo por suficiente | Validación independiente de sensor bajo contrato aplicable | `PARTIALLY_DEPENDENT` |
| FD injection etiquetada `sensor_sensitivity`, no containment | Tres controles etiquetados y limitaciones documentadas | No para mantener la etiqueta y reportar el hecho | Evidencia independiente del path normal para hygiene/containment | `SATISFIABLE_INDEPENDENTLY` para el claim acotado; no para readiness |
| Launcher FD hygiene al entrar independientemente qualified | Requisito está `UNKNOWN`; control negativo cubre un FD/path probado | Criterio de aceptación autorizado necesario para qualification | Pruebas/inspección operacional adicional del launcher podrían aportar evidencia, una vez definido el criterio | `PARTIALLY_DEPENDENT` |
| No required unit/path UNKNOWN | 385 global dispositions UNKNOWN; required domains/paths también UNKNOWN | Sí: authority/criterion determina cuáles unidades son required y qué cierre acepta | Evidencia operacional sólo puede cerrar casos medidos; no elimina unidades no enumeradas ni redefine REQUIRED | `BASELINE_BLOCKED` |
| Ninguna evidencia missing/invalid/contradictory | Ledger reporta causas pendientes y cero casos elegibles; las referencias requieren comprobación propia | No para detectar missing/hash/inconsistency; sí para determinar impacto en criterio/coverage requerido | Integridad y consistencia de artifacts independiente, para el scope que se examine | `PARTIALLY_DEPENDENT` |
| Collector, builder, independent verifier fail-closed | Ledger: verifier independiente requerido, `NOT_IMPLEMENTED`; fixture/harness sintético no basta | Criterio de aceptación de salida/coverage requiere autoridad; implementación técnica puede verificarse independientemente | Construir y probar herramienta aparte sería evidencia técnica, pero no subsana requisitos de inventory/authority | `PARTIALLY_DEPENDENT` |
| TALOS execution/collection durante qualification es cero | Restricción y registro documental indican cero | No | Auditoría de logs/registro de ejecución si estuvieran disponibles | `SATISFIABLE_INDEPENDENTLY` |

Resultado de la matriz: hay requisitos verificables o medibles
independientemente, pero varios términos necesarios para la calificación
actual son `BASELINE_BLOCKED`, y otros permanecen incompletos por razones
operacionales, de evidencia o de implementación. La existencia de una ruta
independiente para algunos checks no satisface la conjunción completa.

## 6. Estado S01–S16 y materialidad de UNKNOWN

La tabla conserva el resumen documental CP050 y no vuelve a adjudicar
membership. “Global U” significa que las 385 dispositions permanecen
UNKNOWN, no que cada superficie tenga una disposition separada. “Relational
U” denota la incertidumbre de relación/candidatura documentada para esa
superficie. Los estados exactos de membresía no se convierten en evidencia
de efecto.

| Surface | Evidencia/estado documental existente | UNKNOWN / límite relevante para cierre |
|---|---|---|
| S01 | 28 YES documentados; CP014 deja cuatro exclusiones y siete relaciones UNKNOWN en su lote | Los siete UNKNOWN relacionales son significativos si el criterio final incluye esa frontera; `open_by_handle_at` 304 permanece UNKNOWN. En todos los casos disposition global sigue UNKNOWN. |
| S02 | 15 YES de payload; tres NO relacionales para sync calls; 19 exclusiones históricas preservadas | NO de S02 no significa NO global; todas las dispositions globales siguen UNKNOWN. |
| S03 | Nueve YES condicionados por lifecycle/FD | Hygiene normal del launcher sigue UNKNOWN; el FD negativo sólo cubre descriptor/path probado. |
| S04 | 35 YES; `umask` excluido de S04; cinco leads abiertos | Cinco leads continúan sin outcome; no disposition global final. |
| S05 | Seis YES file-backed | `madvise` UNKNOWN hasta partición de `MADV_*`; 17 leads no promovidos; coverage general incompleta. |
| S06 | Nueve YES documentados, todavía checkpoint-only en la representación indicada por CP050 | `msync` UNKNOWN; 19 leads; variantes anonymous/memfd/secretmem, shared/private y otras rutas no cerradas. |
| S07 | 17 YES IP documentados checkpoint-only; `socketpair` NO para S07 | El NO es sólo relación S07; no resuelve efecto/global; casos AF_UNIX quedan separados. |
| S08 | 18 YES AF_UNIX documentados; 54/55 faltaban de representación según CP046 | 16 contextos UNREVIEWED/discrepancias de representación y variantes pathname/abstract/unnamed separadas; no equivale a coverage IPC completa. |
| S09 | Cinco YES acotados a SCM_RIGHTS/adquisición interproceso | No incluir SCM_CREDENTIALS ni inferir uso/efecto; disposition global UNKNOWN. |
| S10 | 31 YES y seis NO documentados | 12 leads de readiness no promovidos; 36 provenance partial; no cierre de IPC/coordinación y effects globales. |
| S11 | 17 YES condicionados | 14 leads de lifecycle/control sin promover; 22 provenance partial (además de cuatro refs directas); outcome global UNKNOWN. |
| S12 | Tres YES de interfaz io_uring; casos `BLOCKED` exactos del perfil async | Los bloqueos no convierten membership en disposición y no cubren SQE/rutas/configuración general; artefactos no re-vinculados al snapshot cualificado. |
| S13 | Seis YES de Linux native AIO; seis denegaciones `EPERM` exactas bajo el mismo perfil/hash | No se extrapola a otros perfiles, operaciones completas o S14; evidencia no elegible para predicate actual hasta rebind. |
| S14 | Nueve interfaces POSIX AIO YES a nivel de biblioteca | No son syscalls ni prueban workers/implementación/runtime; correlación y completion permanecen UNKNOWN. |
| S15 | Tres YES acotados (`bpf`, `perf_event_open`, creación `userfaultfd`); `ioctl` family UNKNOWN; FIONREAD exacto OBSERVED | No hay coverage de otros commands/objetos; default-deny `NOT_DEMONSTRATED`; no inferir de S13. |
| S16 | 33 YES documentados/materializados bajo scopes limitados | 51 leads no promovidos; namespaces/credentials/privileges/seccomp enforcement no quedan calificados por membership. |

### UNKNOWN que importa y UNKNOWN descriptivo

- **Material para el target actual:** las 385 dispositions globales UNKNOWN
  son un false cause explícito del ledger y bloquean L1/L3. También son
  materiales los required domains/paths con UNKNOWN, porque el predicate
  prohíbe required units/alternative paths UNKNOWN.
- **Material condicional:** los diez UNKNOWN relacionales y los UNKNOWN
  específicos (por ejemplo `madvise`, `msync`, `ioctl`, variantes/paths)
  afectan closure cuando pertenecen al scope que el criterio autorizado
  defina; no se pueden descartar como meramente documentales sin ese scope.
- **Sólo descriptivo si no se invoca:** UNKNOWN o gaps sobre provenance
  histórica individual, relación checkpoint-only o formato de representación
  pueden quedar como limitaciones explícitas para un claim que no dependa de
  ellos. Eso no cierra ninguna disposition UNKNOWN.
- **Ningún UNKNOWN se cambia** ni se clasifica normativamente en CP070.

S12/S13 aportan evidencia operacional fuerte pero estrecha: 9/9 llamadas
async indicadas denegadas con `EPERM` bajo perfil/hash exactos, y algunas
observaciones sintéticas con ring/contexto vacío/cero requests. S14 es capa
API distinta y permanece sin evidencia de workers/completion. S15 sólo tiene
FIONREAD sobre pipe sintético como OBSERVED; comandos opacos y enforcement
permanecen abiertos. S16 tiene 33 relaciones YES, no prueba efectiva de
transiciones/privilegios ni enforcement. Estos datos reducen incertidumbre de
casos particulares, no del cierre integral.

## 7. Evidencia dinámica histórica ya registrada

Se reproducen únicamente los límites ya escritos en CP050 y en el ledger:

| Área/caso | Resultado histórico | Qué sostiene | Qué no sostiene |
|---|---|---|---|
| io_uring | `BLOCKED`/`EPERM` para setup/enter/register exactos bajo `a-pre-native-async-deny-v1`, hash `ff44e7…` | Denegación de esos calls bajo ese perfil identificado | Otras operaciones, perfiles, SQE/coverage integral, paths alternos o efecto global |
| Linux native AIO | `BLOCKED`/`EPERM` para las seis llamadas exactas bajo el mismo perfil/hash | Denegación de esas seis llamadas bajo esa condición | AIO genérico, otros perfiles, POSIX AIO/S14 ni coverage universal |
| FD regular | FD deliberadamente inyectado `OBSERVED`; un FD no pasado `BLOCKED` en control negativo acotado | Sensibilidad y resultado de ese FD/launcher path | Hygiene general del launcher normal; permanece UNKNOWN |
| `MAP_SHARED` | FD/mapping inyectado `OBSERVED`; pathname sin FD `BLOCKED` en subcaso probado | Mapping/flush/read-back sintético con ese recurso y el path sin FD probado | Mapping general, stores CPU visibles por syscall, otras clases de backing/FD |
| AF_UNIX | FD conectado inyectado `OBSERVED`; pathname sin FD `BLOCKED` en subcaso probado | Control exacto de socket/path | IPC/socket general, otros endpoints, herencia/hygiene global |
| `ioctl(FIONREAD)` | `OBSERVED` en pipe sintético, valor documentado | Ese command/objeto | Familia ioctl, policy general o default-deny |
| Auditoría Python | `sys.addaudithook` `AUXILIARY_ONLY`/`PARTIAL` | Telemetría auxiliar en su scope | Ausencia/completitud de syscalls nativas |

La afirmación “el efecto exacto ocurrió/estuvo bloqueado” no requiere por sí
misma authority. La afirmación “esto satisface el control o coverage requerido
para A-PRE-0/TALOS” requiere definir scope y criterio y validar identidad del
snapshot; ledger establece `current_ready_predicate_eligible_case_count=0`.
La evidencia operacional no se desecha, pero tampoco sustituye esos requisitos.

## 8. Dependencia entre niveles L0–L3

Para CP070 se usa la estratificación solicitada por Directiva 070:

| Nivel | Objeto | Efecto de authority unresolved |
|---|---|---|
| `L0 — identidad/provenance` | Quién produjo qué artefacto, identidad, hash y lineage | No invalida hashes ni genealogías locales verificadas. Sí deja sin demostrar identidad/authority del `f058…` y limita la elegibilidad/rebinding de evidencia al snapshot normativo. |
| `L1 — semántica/membresía documental` | Relación entre syscall, superficie, operaciones/variantes y criterio | Pueden preservarse atribuciones históricas a checkpoints y memberships registradas. El cierre normativo de pertenencia, exclusión, UNKNOWN aceptable y completitud depende de authority/criterion. |
| `L2 — efecto operacional` | Qué ocurrió o fue denegado en el subcaso probado | La incertidumbre de L0/L1 no borra la medición exacta. Pero la falta de baseline no define qué casos son requeridos ni permite elevar casos acotados a coverage del objetivo. |
| `L3 — conclusión de seguridad/cierre` | Declaración de readiness/contención integral A-PRE-0 | Depende de L2 suficiente y de L1/scope autorizado, identidad/snapshot y no-UNKNOWN. L0/L1 no bloquean toda observación L2, pero sí el claim de cierre L3 definido hoy. |

Así, evidencia L2 es independiente como hecho acotado, no como sustituto
automático de la conclusión L3. El bloqueo de autoridad en L0/L1 no hace
falsas las mediciones, pero sí impide su agregación normativa a readiness.

## 9. Resultado y siguiente paso

```text
RESULT = EXTERNAL_AUTHORITY_MATERIALLY_REQUIRED
BLOCKED_CLAIMS = autoridad/criterio del inventario requerido; cierre L1; aceptación normativa de las 385 dispositions y casos UNKNOWN; calificación formal A_PRE_0_READY contra overlay/snapshot autorizado
INDEPENDENT_CLAIMS = identidad/hash de copias locales y registros; contenido histórico de checkpoints; resultados operacionales de subcasos exactos con scope/profile/resource declarados
A_PRE_0_BASELINE_DEPENDENCIES = current normative spec identity in qualified overlay; authorized criterion/scope; closure rule for required UNKNOWN/variants; evidence rebinding to same qualified snapshot
S01_S16_MATERIAL_DEPENDENCIES = las 16 superficies forman el inventario propuesto; outcomes globales 385 UNKNOWN y paths required UNKNOWN afectan cierre; UNKNOWN relacionales/domain-specific son materiales si caen en scope requerido; status YES/NO por sí solo no es effect coverage
L0_L3_DEPENDENCY = L0 local hashes/provenance factual independently verifiable; L1 normative closure depends on authority; L2 exact subcase evidence independently reportable but not sufficient for closure; L3 formal readiness directly depends on authoritative scope/criterion and all other gates
EXTERNAL_AUTHORITY_NECESSARY = YES (for the defined normative A-PRE-0 closure; not for narrow historical/operational claims, and not uniquely tied to recovering f058 if a valid replacement designation is established)
NEXT_MINIMAL_ACTION = HUMAN_DECISION_ON_REOPENING_PATH_A (external search remains NOT_AUTHORIZED)
```

Conclusión específica: el bloqueo no afecta sólo a una afirmación histórica
sobre qué archivo se usó. El predicate ledger actual incluye como condición
que la revisión normativa esté en el overlay cualificado; además, L1 requiere
authority/criterion para cerrar outcomes. Por tanto, la autoridad es una
dependencia material del objetivo definido de cierre normativo/A-PRE-0.
No se demuestra que la recuperación exacta de `f058…` sea la única solución
posible: serviría el artefacto con identidad y autoridad verificables, o una
designación normativa equivalente y competente, con scope y precedencia.

CP070 no ejecuta búsqueda externa ni propone decidir ahora si reabrir Camino
A. Si se opta por avanzar esa ruta, primero se requiere una decisión humana
separada porque CP067 registra `GATE_EXTERNAL_EVIDENCE_AUTHORIZATION =
NOT_AUTHORIZED`. No se realiza el mapa completo de TALOS en este checkpoint.

## 10. Verificación e invariantes

| Check | Resultado |
|---|---|
| Filas / nombres / números | 385 / 385 únicos / 385 únicos |
| Disposiciones globales | 385 `UNKNOWN` |
| `inventory.frozen` | `false` |
| Baseline / artefacto | `AUTHORITY_UNRESOLVED` / `UNRECOVERED` |
| Gate de búsqueda externa | `NOT_AUTHORIZED`; ninguna búsqueda ejecutada |
| Contador 63 | `SCOPE_UNPROVEN`, preservado |
| A-PRE-0 / A-PRE-1 | `NOT_READY` / `NOT_AUTHORIZED / NOT_EXECUTED` |
| Canon | Sin cambios de manifest, ledger, baseline spec, memberships, dispositions, freeze o readiness |
| Actividad | Sin probes nuevos, TALOS, VM, búsquedas externas ni packets |

