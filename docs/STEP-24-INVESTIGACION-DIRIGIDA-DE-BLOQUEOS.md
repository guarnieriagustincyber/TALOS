# TALOS V1.5 — STEP-24: Investigación dirigida de bloqueos, raíz de confianza y aislamiento

**Resultado:** `INVESTIGATED_WITH_EXPLICIT_RESOLUTION_PATHS`  
**Estado canónico:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`  
**TALOS V1:** congelado  
**Harness externo:** no autorizado para implementación  
**B1-R:** no autorizado para ejecución  
**Anomalía histórica Git:** `UNRESOLVED_HISTORICAL_EVIDENCE`

## 1. Resumen ejecutivo

La causa central que bloquea una validación controlada no es la ausencia de un comando de sandbox, sino la falta de una cadena de autoridad e identidad independiente del checkout. `OBSERVED`: el flujo local candidato importa y ejecuta lógica del checkout en el host antes de crear el worker; el ancla `trust_root.py` y su verificador también están en el checkout y solo cubren el manifiesto protegido concreto. No se encontró evidencia de un bootstrap externo TALOS aprobado que autorice el controller, el runtime, la política y el verifier antes del primer import host. (Fuentes: [STEP-18](./TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md), [trust_root.py](../src/study_engine/contracts/trust_root.py), [quality_gate.py](../scripts/quality_gate.py)).

`OBSERVED`: el árbol actual contiene un candidato de implementación local de Bubblewrap, pero sus archivos principales no corresponden todos a contenido de HEAD: `scripts/quality_gate.py` y `config/test_perimeter.json` tienen cambios unstaged; `scripts/quality_gate_isolation.py` y dos módulos de pruebas relevantes son untracked y no existen en HEAD. Por ello, este análisis describe el worktree inspeccionado, no una versión aprobada, reproducible o distribuida.

`INFERRED`: la política de mounts propuesta puede reducir acceso de filesystem y crea namespaces, pero no establece por sí sola aislamiento suficiente para código hostil: no se observan límites de CPU/memoria/PIDs, límite de tiempo del gate exterior ni filtro seccomp en el helper inspeccionado. El kernel y el proceso host que construye argv siguen en la base de confianza. El diseño necesita autoridad externa, cadena de bytes check-to-use, política cerrada y evidencia independiente antes de poder adjudicar un resultado.

`OBSERVED`: el contrato/test/verifier B1-R prevé los diez casos × tres repeticiones, pero cada observación solo lleva `case_id`; la posición en una lista es la única distinción entre repeticiones. No hay identidad individual `run_id`/worker/repetition/artefacto en el reporte actual. Además, el test consulta Git desde el proceso de test mientras el helper de sandbox enmascara `.git`; es una incompatibilidad estática plausible que debe comprobarse, no un resultado de ejecución.

`DOCUMENTED`: no hay evidencia nominal histórica suficiente para reconciliar 82/84 untracked; los informes STEP-23A/B mantienen esa limitación. Ningún dato actual permite reconstruir los inventarios perdidos.

**Candidata recomendada, no aprobada:** controlador/bootstrap fuera del checkout con una raíz local explícita bajo control del operador; política versionada que no pueda ampliarse desde el checkout; worker Bubblewrap con namespaces y filesystem mínimo, reforzado con límites de recursos y seccomp/cgroup cuando estén disponibles; verifier separado; reporte por item/subobservación; y, si el modelo incluye adversario capaz de explotar el kernel, ejecución en VM desechable. La elección humana de autoridad, mecanismo de anclaje, límites y nivel de garantía sigue pendiente. Esta recomendación no autoriza implementación ni ejecución.

## 2. Identidad, alcance y limitaciones

### 2.1 Identidad y precondición

`OBSERVED`: repositorio `/media/agustin/Laboratorio/study-engie`, rama `talos-current-audit`, HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`; coinciden con la referencia STEP-24. El objetivo `docs/STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md` no existía antes de esta fase.

`OBSERVED`: el estado Git inicial era extenso y preexistente: 1.863 rutas staged, 23 unstaged y 87 untracked, sin conflictos. Entre los archivos relevantes:

| Ruta | Estado de worktree observado | Implicación |
|---|---|---|
| `config/test_perimeter.json` | Modificado unstaged | El JSON inspeccionado es una versión candidata local; no una policy externa autenticada. |
| `scripts/quality_gate.py` | Modificado unstaged | La lógica inspeccionada es del worktree y no se presupone idéntica a HEAD. |
| `scripts/quality_gate_isolation.py` | Untracked; ausente de HEAD | El helper leído es una incorporación local, sin identidad de versión aprobada. |
| `tests/unit/diagnostics/test_quality_gate_isolation.py` | Untracked | Los tests de boundary leídos no están presentes en HEAD. |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py` | Untracked | Los tests focales leídos no están presentes en HEAD. |
| `src/study_engine/contracts/trust_root.py` | En HEAD; sin cambio reportado | Su contenido se leyó estáticamente; el ancla sigue dentro del checkout. |
| `tests/audit/b1r_contract.json`, `tests/audit/test_b1_route_repeatability.py`, `scripts/verify_b1r_artifact.py` | En HEAD; sin cambio reportado | Contrato/test/verifier del B1-R actual inspeccionado. |

Los informes documentales STEP-22/23 existentes son entradas de esta investigación, no autoridad independiente. No se utilizaron capturas históricas desaparecidas.

### 2.2 Alcance y límites

`OBSERVED`: se leyeron documentos de STEP-18 a STEP-24, configuración, runner, helper de aislamiento, tests y verifier referenciados. Se usaron búsquedas estáticas, lectura Git y una consulta de solo lectura del entorno. No se ejecutaron tests, colección, scripts, workers, harness, imports de TALOS, builds, hooks o comandos de preparación; no se accedió a DBs, corpus, snapshots ni estado de aprendizaje.

La consulta local observó `/usr/bin/bwrap` y `/usr/bin/unshare` resolubles; `podman` y `docker` no aparecieron en PATH. Para el proceso de inspección se observó UID 1000, `CapEff=0`, `NoNewPrivs=0`, `Seccomp=0`. Son hechos de este proceso/instante, no propiedades de un worker ni demostración del comportamiento de Bubblewrap, del kernel entero, de la instalación o de un futuro executor. No se ejecutó `bwrap`.

`UNVERIFIED`: integridad del binario Bubblewrap instalado, configuración efectiva de user namespaces en un worker, identidad de runtime/dependencias, disponibilidad de cgroups/seccomp/VM, mounts efectivos, trazas del sistema de archivos, aislamiento real, recolección real de nodeids y toda observación B1-R dinámica.

## 3. Mapa de dependencias de bloqueos

```text
Decisión humana de autoridad (A-01)
        ↓
Ancla/bootstrap externo e identidad aprobada (A-02)
        ↓
Identidad transitiva y protección check-to-use (C-01)
        ↓
Policy cerrada: perfiles, nodeids, mounts y límites (D-02)
        ↓
Controller host + worker confinado + evidencia independiente (B-01)
        ↓
Artefactos y observaciones con identidad inequívoca (D-01)
        ↓
Agregación fail-closed y adjudicación autorizada (D-03)
        ↓
Validación experimental autorizada (B-02 / D-04)
```

La anomalía histórica `E-01` es un workstream separado: no es precondición para diseñar una captura futura, pero impide cualquier afirmación retrospectiva sobre la discrepancia anterior. Ningún paso de esta cadena autoriza automáticamente el siguiente.

## 4. Matriz maestra de bloqueos

| ID | Bloqueo y causa concreta | Evidencia / clase | Resolución propuesta | Decisión necesaria | Criterio objetivo de cierre |
|---|---|---|---|---|---|
| A-01 | No hay autoridad externa identificada que apruebe, revoque y actualice la identidad del controller/policy. | `DOCUMENTED`: STEP-22 B-01/B-06; STEP-21 §3. `UNVERIFIED`: autoridad operacional actual fuera del alcance inspeccionado. | Definir autoridad compatible con proyecto personal y registro comprobable. | Quién aprueba; scope; vencimiento/revocación; quién verifica la decisión. | Decisión fechada/identificada en canal fuera del checkout, con versión, scope, lifecycle y evidencia de revisión. |
| A-02 | No hay bootstrap/ancla TALOS externa demostrada antes de ejecutar código host del checkout. | `OBSERVED`: el `main()` de [quality_gate.py](../scripts/quality_gate.py) importa y verifica `trust_root.py` del checkout; esa raíz solo hash-ea el manifiesto protegido. `DOCUMENTED`: STEP-18/19/20 no hallaron mecanismo externo en sus scopes. | Bootstrap mínimo independiente que valida política/controller exactos antes de importar código del repo. | Ubicación/custodia de ancla; local firmado vs paquete de sistema; offline/online. | Ausencia, invalidez, expiración, revocación y downgrade detienen antes del primer import no confiable; evidencia del verificador es externa al checkout. |
| C-01 | Identidad del controller/runtime/config y ejecución de mismos bytes no está autenticada ni protegida check-to-use. | `OBSERVED`: wrapper prioriza `.venv/bin/python`; runner/helpers/config viven en checkout. El helper de aislamiento actual es untracked; runner/config están dirty. `DOCUMENTED`: STEP-18 §§3.1–3.3. | Identificar transitivamente binario, imports, plugins, argv, config y policy; ejecutar copia verificada inmutable/FD fijado. | Scope de inventario, política de actualizaciones y control de rollback. | Digest firmado/anclado fuera del repo; evidencia vincula bytes verificados con bytes mapeados/cargados y consumidor; sustitución concurrente bloqueada. |
| B-01 | El worker tiene una frontera filesystem/namespaces candidata, pero la ejecución efectiva, perfil de permisos y límites de recursos no se demuestran. | `OBSERVED`: helper dirty/untracked construye `bwrap --unshare-all`, sesión nueva, repo RO, workspace RW, máscaras y env reducido. No se observan argumentos seccomp/CPU/memoria/PIDs ni timeout en llamada del gate. `UNVERIFIED`: worker real. | Usar el helper solo como componente de policy externa revisada; añadir límites explícitos y recoger evidencia del launch desde supervisor independiente. | Amenaza objetivo: código accidental/malicioso vs exploit de kernel; disponibilidad/capacidad permitidas. | Pruebas autorizadas prueban filesystem, namespaces, red, credenciales, descendientes, recursos, fail-closed y ausencia de escrituras fuera del scope; limitaciones documentadas. |
| B-02 | Herramienta instalada no equivale a controller confiable, aislamiento ni sistema desplegado. | `OBSERVED`: `bwrap`/`unshare` están en PATH de esta sesión; no se verificó versión/binario ni se ejecutaron. `DOCUMENTED`: STEP-20. | Inventariar paquete/binario y configuración dentro del preflight futuro, sin confiar solo en nombre/ruta. | Fuente de paquete permitida y responsable de actualización. | Identidad/procedencia aprobadas, versionado, capacidades efectivas y test de boundary; instalar el paquete por sí solo no cierra bloqueo. |
| D-01 | B1-R no identifica individualmente las repeticiones ni las vincula a run/worker/artefacto; JSON duplicate keys no se rechazan explícitamente. | `OBSERVED`: contrato tiene 10 casos/3 repeticiones; el test agrega listas sin ordinal y cada observation solo lleva `case_id`; verifier comprueba cardinalidad/igualdad pero no identidad por intento. `OBSERVED`: se usa `json.loads` sin `object_pairs_hook`. | Esquema versionado por `(run_id,nodeid,case_id,repetition,attempt)` y `observation_id`; parsing que rechaza nombres JSON duplicados; strict schema y artefact references. | Política de retry y si las tres repeticiones son secuenciales o ejecuciones aisladas. | Exactamente 30 claves esperadas únicas y sin extras; identidad de ejecución/worker, timestamps, artifact digests y verifier validables por consumidor independiente. |
| D-02 | Config clasifica suites, no aporta un inventario normativo autenticado de once nodeids; selección efectiva no fue recolectada. | `OBSERVED`: JSON marca `tests/unit` y `tests/audit` required; `quality_gate.py` activa esas carpetas en ambos perfiles. Config y runner están modificados; dos módulos unit son untracked. | Policy externa fija el set exacto por perfil; comparar configuración candidata y colección reportada con ese set. | Autoridad de perímetro y exactitud por perfil. | Inventario aprobado fuera del checkout; captura de `--collect-only`/ejecución futura, exact match por perfil y decisión sobre cambios de tests; ejecución requiere autorización separada. |
| D-03 | Máquina de estados mezcla nombres de fases y resultados, y no define precedencia total para resultados concurrentes. | `DOCUMENTED`: STEP-22 contrato §9 y matriz §6 tienen estados y regla parcial, pero no una tabla de transición exhaustiva. | Formalizar etapas separadas de status funcional/evidencia/aislamiento/Git/cobertura y una función de agregación versionada. | Política sobre combinación `FAIL` + `BLOCKED`, retries, cancelación y timeout. | Tabla exhaustiva con pruebas de todas las combinaciones críticas; desconocido no se vuelve PASS y todas las causas se conservan. |
| D-04 | B1-R ejecuta Git desde test hijo, mientras helper oculta `.git`; la compatibilidad no está probada. | `OBSERVED`: test `_git_status()` usa `git -C ... status --porcelain --untracked-files=all` con `check=True`; helper monta `.git` como directorio vacío. `INFERRED`: bajo ese sandbox el Git interno probablemente falla como no-repository. No se ejecutó. | Mover Git pre/post a observer/controller host; pasar referencias/resultados firmados de estado al contrato del item, no montar `.git` al worker. | Cómo integrar la assertion histórica de sterility sin transferir authority al worker. | Prueba sintética autorizada confirma consulta host y test sin `.git` pasa con artefactos vinculados; ninguna exposición de `.git` real. |
| E-01 | La discrepancia histórica 82/84 no se puede reconciliar con capturas nominales completas disponibles. | `DOCUMENTED`: STEP-23A/23B/23C; capturas STEP-23A citadas ya no disponibles. `OBSERVED`: digests STEP-23C coinciden con bytes conservados, no con historia anterior. | Mantener unknown; protocolo de captura uniforme para el futuro. | No se requiere decisión para preservar incertidumbre; cualquier reclasificación requiere evidencia nominal nueva directa. | Solo reconciliar con dos capturas completas, comparables, con procedencia/tiempo/flags/parser; si no existen, cierre explícito como históricamente irresoluble. |
| F-01 | La aprobación y el nivel de independencia requeridos no están definidos para un proyecto personal. | `DOCUMENTED`: STEP-21 requiere rol aprobador y ancla, sin asignar identidad. No se presume una institución/tercero. | Modelo de autoridad de operador local con separación funcional y registro; revisor independiente opcional según garantía. | El operador decide qué identidad controla claves/policy y si requiere segunda persona o segundo host. | Aprobación explícita identificada y verificable, con separación y limitaciones acordes al modelo de amenaza elegido. |

## 5. Línea A — raíz de confianza y alternativas

### 5.1 Hallazgos de mecanismos existentes

- `OBSERVED`: [trust_root.py](../src/study_engine/contracts/trust_root.py) compara SHA-256 de `tests/protected/manifest.json` con una constante en el mismo checkout. Esto verifica igualdad de bytes respecto de esa constante, pero no autentica la propia constante, `quality_gate.py`, el helper de Bubblewrap, runtime, dependencia o política de perfiles.
- `OBSERVED`: [quality_gate.py](../scripts/quality_gate.py) importa esa raíz desde `src/` luego de cargar el código del checkout; su decisión es posterior a ejecutar/importar el código que pretende validar. La comprobación no es bootstrap externo.
- `OBSERVED`: la configuración focal B06 incluye fingerprints/digests para recursos del alcance focal, pero esa lógica está en el runner del checkout y tiene scope focal; no es identidad aprobada general del host controller.
- `DOCUMENTED`: STEP-20 encontró herramientas criptográficas genéricas, no un manifiesto TALOS firmado, trust root con procedencia independiente o flujo de revocación en los paths inspeccionados.
- `OBSERVED`: el helper Bubblewrap candidato y dos tests que lo cubren son untracked; el runner y configuración están dirty. La revisión de contenido actual no autentica sus bytes ni una versión aprobada.

### 5.2 Comparación de alternativas

| Alternativa | Qué autentica / dependencia | Riesgos residuales | Complejidad, coste y reversibilidad | Evaluación |
|---|---|---|---|---|
| Digest embebido en el checkout | Detecta una diferencia respecto del digest autocontenido. Confía en el checkout que contiene dato y verificador. | Sustitución conjunta del controller/verifier/ancla; no signer identity, aprobación ni anti-rollback. | Muy bajo coste; fácil de cambiar; poco valor contra checkout hostil. | No satisface raíz externa. Mantener solo para integridad local acotada. |
| Aprobación manual + hash externo, operador-local | El operador compara identidad completa contra registro/valor custodiado fuera del checkout. Confía en el dispositivo/medio donde se guarda el ancla y en el proceso manual. | Error humano, copia incorrecta, almacenamiento local comprometido; el hash no demuestra quién lo aprobó si no hay registro. | Bajo/medio; reversible y apropiado para proyecto personal; requiere repetir approval en update/revoke. | Candidato mínimo viable si el bootstrap también está fuera del checkout y el registro conserva decision/scope/time. |
| Policy/manifiesto firmado + clave pública fijada externamente | Firma enlaza bytes/policy al control de una clave; bootstrap valida clave, scope, vencimiento, versión y revocación. | Firma no corrige una clave pública mal anclada, máquina comprometida, identidad de signer ambigua, o check/use mutable. | Medio/alto; gestión de clave/rotación/revocación y operación offline. Reversible con versionado/revocation. | Candidato recomendado solo si la carga de lifecycle es aceptada; signing tool no se debe incrustar como trust por sí sola. |
| Verificación de paquete/artefacto por mecanismo del SO | Confía en raíz del OS, repositorio de paquetes, propietario/permisos y actualización del sistema. | Cambios de path/config, ambiente Python/imports, root/admin comprometido; paquete instalado no fija policy TALOS. | Medio; aprovecha operación del host y puede facilitar updates; revocación depende del OS. | Puede anclar bootstrap, no reemplaza policy TALOS ni verificación del proceso/runtime transitivo. |
| Identidad keyless/Sigstore/OIDC | Verifica firma y claims del issuer/identity bajo política elegida; puede aportar bundle/log evidence. | Depende del issuer, identity matching, transparencia/conectividad/tiempo y del bootstrap que valida; no demuestra ejecución aislada. | Alto para un flujo local/offline; rotación de identidad menos manual pero más dependencias. | No necesaria por defecto en proyecto personal; opción futura si hay CI/distribución pública y se aprueba el modelo de identidad. |
| Harness externo con bootstrap local + policy firmada | Separa controller/verifier del checkout; ancla firma/hashes con una ubicación independiente; datos del repo se validan como inputs. | OS/kernel, bootstrap, custodia de clave y política siguen confiables; una firma no evita TOCTOU ni comprometimiento del host. | Medio/alto; demanda empaquetado reproducible, lifecycle y evidencia. | Mejor balance como arquitectura futura candidata, alineada con STEP-21; no implementada ni aprobada. |

### 5.3 Propuesta de cadena de identidad

`PROPOSED`: cada salto debe tener productor, identidad esperada, verificación antes de consumir y evidencia preservada. La cadena no está desplegada.

| Etapa | Producer → artifact | Identity / verification | Momento y consumer | Fallo bloqueante / riesgo residual |
|---|---|---|---|---|
| Política | autoridad designada → policy+signature/revision | Scope, perfil, nodeids, límites, expiración, signer identity y anti-rollback anclados fuera del checkout | Bootstrap antes de cualquier import del repo | Missing/invalid/expired/revoked/rollback => no launch; la autoridad y key custody aún dependen del operador. |
| Bootstrap | operador/OS package → ejecutable verifier/controller bootstrap | Digest o firma verificada por raíz distribuida/custodiada fuera del repo | Antes de cargar controller | Si mismo checkout contiene bootstrap y clave, circularidad; ejecutar exactamente el objeto verificado. |
| Controller/runtime | bootstrap/installer → controller, interpreter, imports y tools transitivos | Inventory cerrado con versiones/digests y provenance; resolver dependencias sin checkout como sys.path host | Antes de operaciones host; el controller valida módulos antes de importarlos | Cualquier module/config/path no allowlisted => detener; paquete/OS trust queda en base de confianza. |
| Inputs/perímetro | checkout → candidate config/tests | Parseo como data con schema/size limits; comparar con policy externa y expected nodeid inventory | Preflight; consumer controller | Checkout no amplía scope; config local dirty no puede ser policy authority. |
| Workspace/snapshot | controller → workspace y inputs autorizados | Paths canonicales, identidad, hashes, no overlap; mismos bytes fijados para mount | Antes de launch; consumer worker | Symlink/TOCTOU/overlap mismatch => no launch; preservar digest y mapping. |
| Worker launch | controller → argv/env/mount plan | Policy fixed, `run_id`, `worker_id`, profile; receipt externo con namespaces y cgroup/limits | Al crear worker, observado por host supervisor | Worker self-report no basta; identidad del launcher/kernel y lectura de `/proc` tienen limitaciones. |
| Resultado/artifacts | worker → output bytes, result records | Per-run schema, sizes, allowlist, digests, IDs; no trust en payload declarativo | Recolectar sin seguir links; consumer verifier | Missing/extra/duplicate/contradictory/truncated => invalid/block. |
| Verificación y agregación | verifier/observer → findings; aggregator → verdict | Identidades separadas, consume mismos bytes; reglas versionadas y cobertura exacta | Después de recolección; auditor/operador lee paquete | Auto-attestation/worker output no puede declarar isolation/global PASS. |

## 6. Línea B — amenazas, capacidades y alternativas de aislamiento

### 6.1 Modelo de amenazas

**Activos:** código del controller/bootstrap; checkout/fixtures; `.git` y evidencia de estado; bases/corpus/snapshots/datos de aprendizaje; secretos/credenciales; OS, dispositivos/sockets; resultados y artefactos.

**Adversario considerado:** test, fixture, plugin, configuración o artefacto deliberadamente malicioso o defectuoso, con ejecución arbitraria dentro del worker. Puede intentar leer/mutar mounts, descubrir procesos, abrir red/sockets, crear children, agotar recursos, alterar reportes o explotar el kernel.

**Frontera de confianza propuesta:** operador y decisión de policy; bootstrap/controller verificado; OS/kernel; verifier/observer independientes; almacenamiento de evidencia. El worker nunca es autoridad.

**Fuera de garantía actual:** compromiso del kernel/firmware, root/admin host, cuenta operador, hardware, side channels, microarchitectural leakage y disponibilidad absoluta. Si el riesgo incluye exploit de kernel por test adversarial, namespaces sobre el mismo kernel no bastan como frontera fuerte; se evalúa VM separada.

### 6.2 Capacidades y evidencia

| Recurso/capacidad | Controller | Worker candidato | Verifier | Evidencia actual |
|---|---|---|---|---|
| Código trusted/bootstrap | UNKNOWN autorizado; hoy candidato del checkout se ejecuta host-side según STEP-18 | No debería escribirlo ni importarlo con autoridad host; repo bind RO propuesto | Leer identity/artefactos; no ejecutar checkout | No hay controller externo identificado. |
| Checkout (fuera de `.git`) | Lee configuración/snapshot y construye mounts | Bind RO propuesto; ejecuta test code dentro | No necesita acceso al checkout salvo policy/read-only | Helper local declara RO; no se ejecutó. |
| `.git` | Observer host necesitaría acceso read-only | Helper candidato lo oculta con directorio vacío | No necesario si recibe captura preservada | B1-R actual invoca Git en hijo; posible incompatibilidad. |
| Datos protegidos | Debe denegar salvo recurso explícito aprobado | Masks para directorios/archivos de listas/filtros y sin mount de datos externos declarados | No requiere datos productivos | No inspectados; test fixture sintético no ejecutado. |
| Workspace/output | Crea/posee y valida; permite salida acotada | Mount RW en `/workspace/run`; `/tmp` guest tmpfs | Lee bytes recogidos readonly | RW host path bajo `/tmp` según helper; ownership efectiva y límites no demostrados dinámicamente. |
| Red | Observa Git/bootstrap; aún no se definió controller network policy | `--unshare-all` propuesto, network namespace | Solo requiere artefactos | Salida de red no probada; loopback/host connectivity real no se verificó. |
| Secrets/env | No deben heredarse sin allowlist | `--clearenv` y env selectivo; `.env` oculto | Sin secretos | Helper estático; variables efectivas no verificadas. |
| Process/PID | Host observer/controller separado | PID namespace; proceso child/subprocess permitido | Sin ejecución del test | No se encontró límite de PIDs o control verificado de descendientes; `--die-with-parent` no es evidencia por sí sola de cleanup completo. |
| CPU/memoria/tiempo/storage | Define quotas de policy | UNKNOWN límite efectivo | Verifica reporte/exit | No se observaron cgroups, `prlimit`, RLIMIT ni timeout pasado por gate. |
| Kernel/syscalls/capabilities | Confía en kernel y launcher | `--unshare-all`; tests estáticos esperan `CapEff=0`; no seccomp encontrado en argv | No decide trust kernel | Solo el proceso de inspección tiene `CapEff=0`; no dice worker. |
| Dispositivos/sockets | Controlador necesita interfaces mínimas | Helper usa `/dev` nuevo, `/proc` nuevo; no se montan sockets host explícitos en fragmento inspeccionado | No necesita interfaces host | Config efectivo no ejecutado. |

### 6.3 Implementado/candidato/no demostrado

- `OBSERVED`: el worktree candidato invoca Bubblewrap con `--unshare-all`, `--die-with-parent`, `--new-session`, `--clearenv`; binds `/usr`, librerías y algunos archivos de sistema read-only; monta checkout read-only, workspace run writable, `/tmp` tmpfs, `/proc` y `/dev` nuevos; enmascara `.git`, `.venv`, `.env`, directorios protegidos listados y ciertos archivos tipo DB. El worker verifica namespace IDs contra valores pasados por el parent y escribe marcador en workspace.
- `OBSERVED`: el parent `subprocess.run` captura stdout/stderr y `close_fds=True`, pero su argumento `timeout` es opcional. La invocación del gate inspeccionada no pasa un timeout al helper. Las invocaciones internas del test B1-R sí tienen 120s y 30s; eso no limita por sí mismo todo el worker que ejecuta la suite.
- `OBSERVED`: la inspección enfocada no encontró `--seccomp`, límites cgroup, RLIMIT/prlimit, `--uid`/`--gid` ni topes de CPU/memoria/PIDs. No se afirma ausencia en todo el OS; se constata ausencia en el código/rutas inspeccionados.
- `INFERRED`: el sandbox reduce exposición de mounts y namespaces, pero el test conserva el kernel host, ejecuta con una identidad derivada del usuario/namespace que no está especificada aquí y puede consumir recursos sin límites explícitos; el control de daño requiere más que bloquear rutas.
- `UNVERIFIED`: el actual `bwrap` está instalado, pero no se consultó su versión/paquete ni se ejecutó. Ninguna test assertion fue ejecutada en esta etapa.

### 6.4 Comparación de mecanismos

| Mecanismo | Aporta | No aporta / riesgo | Uso candidato |
|---|---|---|---|
| Proceso normal/usuario separado | Separación organizativa, permisos DAC distintos si están bien configurados | No oculta por sí solo rutas/sockets disponibles al usuario; no limita kernel/system calls; usuario operador puede compartir recursos | Insuficiente solo; útil como defensa adicional con identidad dedicada y filesystem controlado. |
| Bubblewrap + namespaces/mount allowlist | Root filesystem construido explícitamente, bind RO/RW, user/mount/PID/network/IPC namespaces según configuración | Misma kernel; seguridad depende de argv/mounts; no aporta policy TALOS, límites recursos o seccomp automáticamente; sockets montados pueden dar capacidades externas | Más cercano al helper actual; candidato si se completa policy, límites, auditoría y pruebas. |
| seccomp | Restringe syscalls permitidas/argumentos cuando filter correcta y aplicada antes del código hostil | No oculta archivos ni autentica policy; perfil equivocado rompe runtime; tampoco resuelve recursos totalmente ni kernel bugs permitidos | Defense-in-depth después de mapear syscalls y probar fail-closed; no usar lista copiada sin validación. |
| cgroups v2 / rlimits | Limita memoria/CPU/PIDs/I/O/tiempo/archivos según controllers disponibles | No limita acceso de datos; controllers/config pueden no estar delegados; rlimits no cubren todos los recursos/transitorios | Requisito de disponibilidad para worker local; preflight debe verificar cuotas efectivas. |
| Contenedor OCI/rootless | Empaquetado, namespaces, cgroups, policy y distribución según runtime | “Container” no es frontera por etiqueta; daemon/privileged socket, mounts, capabilities y runtime pasan a ser TCB | Alternativa si ya existe un runtime administrado y política auditable; `docker`/`podman` no se resolvieron en PATH de esta sesión. |
| VM desechable | Kernel invitado distinto; más fuerte frente a kernel exploit del guest que sandbox de procesos | Hipervisor/host siguen TCB; coste de arranque, imagen, updates, transferencia de datos y observabilidad; comparte hardware | Escalar a VM si código adversarial o kernel boundary fuera de scope aceptable. |

**Recomendación de aislamiento:** no reemplazar por un contenedor genérico. Mantener modelo externo de controller y usar namespace/mount Bubblewrap como una capa de una policy específica; añadir cgroup resource envelope y seccomp evaluados en fase autorizada; evitar todos los sockets y secretos host; limitar filesystem a checkout RO, runtime aprobado RO y workspace efímero acotado. Si la amenaza incluye un exploit deliberado del kernel, elegir VM en decisión humana.

## 7. Línea C — cadena check-to-use y ventanas TOCTOU

`DOCUMENTED`: STEP-22 pide usar los mismos bytes verificados, pero deja ubicación inmutable/copia/handle como alternativas, sin mecanismo elegido. `OBSERVED`: la ruta actual prepara y ejecuta scripts/imports desde el checkout; unpath de runtime `.venv` también puede ser seleccionable desde checkout; el helper que arma bwrap es local/untracked. La verificación del manifiesto no cubre esa cadena.

| Ventana | Sustitución/riesgo | Control propuesto | Evidencia requerida |
|---|---|---|---|
| Resolución de launcher e intérprete | Reemplazar `test.sh`, Python path o symlink antes de inicio | Bootstrap absoluto fuera de checkout y runtime fijado por identidad | Recibo con inode/device/digest/versión y origen; evidencia del proceso ejecutado. |
| Imports del controller | Cambiar módulo entre digest y `import`; `sys.path` resuelve checkout | No importar módulos checkout en host; paquete controller sellado instalado fuera; `sys.path`/env cerrados | Inventory transitivo y prueba de import trace; bytes leídos/mapeados coinciden con policy. |
| Policy/config/perímetro | Checkout cambia config antes de cargarla y altera nodeids/mounts | Policy externa autoritativa; checkout config solo candidate/data | Digest policy externo; diff explícito; mismatch bloquea. |
| Dependencias/plugins | Resolver versiones distintas o plugin auto-load | Lock/build reproducible, plugin autoload deshabilitado o allowlist exacta | SBOM/lock e identidad runtime; dependencia efectiva ligada a run. |
| Workspace/mount | Cambiar symlink/rename/path entre canonicalize y bind | Abrir directorios por FD y mount por identidad estable; no solo revalidar pathname | Race test con reemplazo concurrente; montaje observado coincide con identidad preflight. |
| Snapshot/input | Archivo muta después de hash y antes de copy/mount | Capturar a read-only immutable copy; hash bytes copiados y luego montar esa copia | Antes/después digest y evidencia de bytes worker. |
| Bwrap executable/config | Binario o argv sustituidos; variable de entorno altera launcher | Binario/args fijados en controller externo; entorno mínimo; no shell command strings | Digest/path de bwrap + argv efectivo + launch receipt independiente. |
| Output/verifier | Cambiar output después de digest o verificar un path distinto | Recoger handle/bytes una sola vez; almacenar immutable; verifier recibe el mismo byte stream/content digest | Matching digest en worker, collector, verifier y evidencia conservada. |
| Revocación/rollback | Usar policy vieja válida criptográficamente | Monotonic version/counter o registro de revocación, vigencia y anti-replay | Rechazo de expirado, revocado, nonce repetido y downgrade. |

Una secuencia SHA-256 local identifica contenido, pero no prueba autorización. Firma auténtica prueba afirmación del dueño de la clave según política; no prueba que esa clave represente autoridad correcta ni que el mismo bytes se ejecutó. Una provenance attestation identifica proceso/inputs según confianza en builder; tampoco reemplaza boundary ni evaluación del consumidor.

## 8. Línea D — auditoría estática B1-R, perímetro y cobertura

### 8.1 B1-R y esquema futuro

`OBSERVED`: [b1r_contract.json](../tests/audit/b1r_contract.json) tiene exactamente diez IDs y `repetitions_per_case=3`; el test declara esos mismos diez y bucle con tres ejecuciones por caso. Total proyectado = 30.

Cada registro actual incluye `case_id`, HTTP status, content type, eventos, último evento, flags de terminal/stream, excepciones observadas, boundary label y forbidden accesses. No incluye `run_id`, `worker_id`, índice de repetición, `observation_id`, timestamp por observación ni referencia/digest de artefacto por observación. La lista tiene orden, pero orden de array no es identidad estable.

El verifier actual comprueba schema/contract digest de nivel superior, conjunto exacto de case IDs, cardinalidad tres, campos esperados, igualdad normalizada de las tres corridas, probes, counters y counts. El test comprueba presencia del archivo generado, invoca verifier como proceso separado y compara Git antes/después. Límites observados:

- No existe ordinal/repetition ID que permita identificar una observación particular o distinguir registros idénticos de duplicados.
- No se vincula resultado a run/worker autorizado, identidad de controller o checkout.
- No hay validación de digest/allowlist del artefacto en verifier actual; el subprocess valida su salida funcional, no independencia de autoridad.
- No hay evidencia de aislamiento efectivo consumida por el verifier.
- No hay detección explícita de nombres duplicados en objetos JSON; `json.loads` se usa sin un parser que rechace duplicate keys.
- No hay strict rejection general de campos extra desconocidos en reporte.
- Ausencia/exceso de caso y longitud != 3 se rechazan; diferencias de resultado repetido disparan finding; ausencia de un campo esperado se rechaza indirectamente cuando no coincide con el contrato.
- La igualdad de Git antes/después no detecta escrituras transitorias, archivos ignorados ni modificaciones externas.

`PROPOSED`: para cada ejecución, definir claves exactas:

```text
(run_id, profile_id, parent_nodeid, case_id, repetition_index, attempt_id)
observation_id = SHA256(canonical_encoding(the tuple above))
```

`observation_id` es un identificador de vínculo, no evidencia de autenticidad. Cada record incluye productor y worker identity, timestamps, exit/signal/timeout status, observation payload, artifact refs (name, size, digest, immutable storage ID), verifier findings y limitations. La policy fija si retry es permitido; un retry usa `attempt_id` distinto y jamás sobrescribe el fallo anterior. El agregador debe rechazar key duplicada, ID incoherente, campo crítico desconocido, caso/repetition faltante/extra, dos resultados contradictorios, artifact missing/mismatch, worker/run mismatch y verifier ausente/error.

### 8.2 Once nodeids obligatorios

Los once IDs se preservan en la matriz STEP-22 §2; clasificación de suite observada en [config/test_perimeter.json](../config/test_perimeter.json):

| # | Nodeid exacto |
|---:|---|
| 1 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` |
| 2 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` |
| 3 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` |
| 4 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` |
| 5 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` |
| 6 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` |
| 7 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` |
| 8 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` |
| 9 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` |
| 10 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` |
| 11 | `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` |

`OBSERVED`: config clasifica `tests/unit` y `tests/audit` como `required`; `quality_gate.py` activa toda suite `required` en perfiles `required` y `release`, construye paths de suite y los pasa a `pytest.main`. Los diez nodeids unit y el nodeid audit se encuentran declarados en sus archivos del worktree inspeccionado.

`UNVERIFIED`: no se hizo pytest collection; no se afirma que los once sean colectados, no-skipped, ejecutados exactamente una vez o pasados por ambos perfiles. La config no enumera estos once individualmente. Aparte, los dos test modules unit están untracked, y la configuración/runner dirty; la declaración `required` describe un candidato de checkout y no acredita expected inventory normativo fuera del checkout.

`PROPOSED` verificación futura (con autorización separada): un executor externo mantiene expected nodeid set versionado y por profile; recolecta resultados en worker; compara igualdad exacta con el esperado. Si hace falta solo demostrar selección, `pytest --collect-only` bajo el boundary aprobado puede capturar colección, pero colección no prueba ejecución/pase. La selección no se debe probar ejecutando suites antes de permiso explícito.

### 8.3 B1-R y Git: interacción que requiere resolver

`OBSERVED`: [test_b1_route_repeatability.py](../tests/audit/test_b1_route_repeatability.py) ejecuta `_git_status(repo_root)` antes y después con `git -C <checkout> status --porcelain --untracked-files=all`, `check=True`. `OBSERVED`: [quality_gate_isolation.py](../scripts/quality_gate_isolation.py) reemplaza `.git` del checkout guest por directorio vacío. `INFERRED`: cuando B1-R corra dentro de ese worker, la consulta Git probablemente falla (no repository) en lugar de producir comparación de estado. No se ejecutó; la fase futura deberá probar el contrato de forma autorizada.

**Resolución preferida:** Git before/after pertenece a controller/observer host autorizado y sus resultados se vinculan a nodeid B1-R. El test del worker no debe recibir `.git` ni autoridad Git; el consumidor compara observación host-side y guarda sus limitaciones. No ocultar el fallo con valor vacío ni convertirlo en PASS.

## 9. Máquina de estados y agregación

Las etiquetas de fase no son resultados. `UNSTARTED`, `AUTHORIZATION_CHECK`, `WORKERS_RUNNING`, `RESULTS_VALIDATION`, `ISOLATION_EVALUATION`, `GIT_COMPARISON`, `COVERAGE_AGGREGATION` son etapas; `PASS`, `FAIL`, `BLOCKED`, `ERROR`, `TIMEOUT`, `UNKNOWN` son resultados por dimensión/objeto.

| Etapa | Estado observado/propuesto | Evento/condición | Regla de decisión |
|---|---|---|---|
| Authorization/preflight | `NOT_AUTHORIZED`, `AUTHORIZATION_INVALID`, `PREFLIGHT_BLOCKED` | No approval, signature/policy mismatch, expiry/revocation/rollback, runtime/check-out mismatch | Terminal antes de worker; nunca ejecutar fallback del checkout. |
| Worker launch | `WORKER_NOT_STARTED`, `WORKER_STARTED`, `WORKER_FAILED`, `WORKER_TIMED_OUT`, `WORKER_ABORTED` | spawn fail, exit, signal, deadline, parent loss | Registrar salida/timeout/error distinto; parcial no es PASS. Matar/recolectar descendientes según policy. |
| Functional item | `PASS`, `FAIL`, `ERROR`, `SKIP`, `NOT_RUN` | pytest item result | Mantener por nodeid; skip/no-collect no equivale a pass de required. |
| Artifact verification | `VALID`, `MISSING`, `INVALID`, `VERIFIER_ERROR`, `UNKNOWN` | schema, digest, allowlist, consumer verifier | Cualquier desconocido/error no satisface gate; preservar bytes y findings. |
| Isolation evaluation | `DEMONSTRATED`, `NOT_DEMONSTRATED`, `BREACHED`, `UNKNOWN` | launch evidence, namespace/mount/resource/escape signals | Worker no se auto-certifica; ausencia o scope incompleto no PASS. |
| Git observation | `OBSERVED_EQUAL`, `OBSERVED_DIFFERENT`, `UNCOMPARABLE`, `OBSERVER_ERROR` | before/after captures, same checkout+method | Igualdad solo status observado; diferencia/error bloquea criterio que exige igualdad. |
| Coverage | `COMPLETE`, `INCOMPLETE`, `DUPLICATE`, `CONTRADICTORY`, `UNEXPECTED` | Expected vs actual nodeids/cases/attempts | Exact match; nunca escoger resultado favorable ni descartar unexpected. |
| Aggregation | `PASS`, `FAIL`, `BLOCKED`, `UNKNOWN` | Consumer policy combina dimensiones | Rechazar PASS si hay blocker, unknown, missing evidence o contradiction. Conservar lista de causas y precedencia versionada. |

**Tabla de combinación mínima (propuesta):**

| Función | Evidencia requerida | Resultado compuesto |
|---|---|---|
| Assertion falla con identidad/evidencia válidas | Funcional `FAIL`; demás dimensiones pueden ser válidas | `FAIL`, conservar diagnósticos. |
| Assertion pasa pero aislamiento ausente, verifier falla o Git no comparable | Funcional `PASS` y dimensión crítica `UNKNOWN/ERROR` | `BLOCKED` o `UNKNOWN`, nunca `PASS`. |
| Worker timeout/crash o output truncado requerido | Estado de proceso abnormal; artifact/results incompletos | `BLOCKED` (con estado funcional `ERROR/NOT_RUN`); preservar timeout/partial outputs. |
| Duplicate o contradiction de resultado | Dos observaciones para misma clave o datos incompatibles | `BLOCKED`, guardar ambas; no resolver con orden/último valor. |
| Cobertura incompleta | Faltan nodeids/casos/repeticiones requeridos | `BLOCKED`; no extrapolar suite PASS a item ausente. |
| Todo completo | Authorization, identity, item functional pass, artifact valid, isolation demonstrated, Git comparable/criterio satisfecho, exact coverage y no contradiction | Solo entonces el agregador autorizado puede emitir `PASS` en scope de policy. |

La matriz STEP-22 aporta muchos rechazos, pero deja para aprobación la normalización total de estados, timeout vs fail precedence, retry semantics y comportamiento ante errores concurrentes. Esta tabla es propuesta, no implementación.

## 10. Línea E — adjudicación de evidencia histórica Git

- `DOCUMENTED`: STEP-23A `PARTIALLY_RECONCILED`, cuenta 82 untracked en observación posterior y reporta una explicación de granularidad parcial; staged histórico no resuelto.
- `DOCUMENTED`: STEP-23B `UNRESOLVED_HISTORICAL_EVIDENCE`; las dos capturas temporales STEP-23A citadas ya no estaban disponibles; no había dos inventarios nominales persistidos y comparables.
- `OBSERVED`: STEP-23C guardó dos capturas completas porcelain-v2 fuera del repo, con digests recalculados en STEP-23C.1: baseline 84 untracked y final 86 (final agrega dos informes STEP-23C). Esos digests acreditan igualdad con los bytes actuales guardados, no origen/tiempo autenticados.
- `INFERRED`: el crecimiento observado es compatible con informes creados por fases intermedias, pero sin las capturas emparejadas y metadata de todos los instantes no se declara causalidad ni que expliquen todo 82→84.
- No se halló evidencia nominal nueva directa que resuelva la captura perdida. Se preserva `UNRESOLVED_HISTORICAL_EVIDENCE`; no calcular rutas faltantes por aritmética ni usar el baseline actual como proxy del pasado.

**Protocolo futuro de captura:** misma invocación, por ejemplo `git status --porcelain=v2 --branch --untracked-files=all -z`, con bytes stdout/stderr, exit code, UTC timestamp monotónico y civil, repo canonical path, branch/HEAD, versión Git, opciones exactas, locale y parser/count-rule version. Guardar bytes fuera del repo en almacenamiento autorizado de solo escritura/append; calcular SHA-256 sobre los bytes exactos; derivar staged/unstaged/untracked de esa misma salida y conservar registros rename/conflict/unusual path. Capturar inicio y fin con identidad común de run; comparar nominalmente, no solo conteos. Registrar limitaciones: status no detecta escritura transitoria, ignorados o efectos fuera de Git.

## 11. Línea F — decisiones que requieren al operador

| Decisión | Opciones viables | Ventajas/desventajas y coste | Recomendación técnica | Quién debe aprobar |
|---|---|---|---|---|
| Modelo de autoridad personal | Operador como policy owner; operador + segundo revisor; proceso/servicio institucional existente | Operador único simple y reversible, pero self-review limitado; segundo revisor da separación humana con coordinación/coste; institución aporta controles pero no se presume disponible. | Para proyecto personal: operador puede aprobar, con registro explícito y verificación técnica separada; exigir segunda persona solo si la garantía/blast radius lo justifica. | Operador propietario de TALOS; actor/rol debe identificarse explícitamente. |
| Ancla/bootstrap | Digest fuera de repo; clave pública fijada en entorno OS; policy firmada; package manager trust | Digest simple pero lifecycle manual; firma facilita rotación pero añade clave/issuer/rollback; package manager delega confianza al OS. | Elegir mecanismo mínimo que soporte el threat model; todos requieren bootstrap fuera del checkout y protección check-to-use. | Operador decide custodia y canal. |
| Confianza en el kernel | Namespace+bwrap; bwrap+cgroup/seccomp; VM | Procesos son baratos, mismos kernel; capas adicionales aumentan complejidad; VM mejora límite de kernel guest con costes operacionales. | Bwrap reforzado si tests son inputs no confiables pero no se modela kernel exploit; VM si ese adversario está dentro del scope. | Operador aprueba nivel de riesgo residual. |
| Modo de actualización | Manual version bump/approval; signed rolling policy/revocation; pin y detener updates | Pin reduce sorpresa pero envejece; auto-update reduce drift pero requiere revocation/reproducibility; manual con log reversible. | Pin exacto por run y aprobación explícita para cambiar; no latest/downgrade silencioso. | Policy owner. |
| Verificación independiente | Mismo proceso con módulos separados; verifier fuera del checkout; reviewer/host secundario | Separación lógica simple no resiste sustitución conjunta; external binary separa checkout; segundo host/persona cuesta más y reduce riesgo compartido. | Como mínimo verifier/bootstrap no modificable desde checkout; mayor independencia según riesgo. | Operador decide assurance target; verifier identity definida antes de uso. |
| B1-R retries e identidad | Tres secuencias seriales; workers separados; retries solo como attempts adicionales | Serial simple; worker separado aumenta isolation but execution count/cost; retries pueden esconder flakiness. | Tres observaciones exactamente con ordinal; no retry por defecto; si retry, no reemplaza intento y policy define adjudicación. | Test/perimeter policy owner. |
| Expected nodeids por perfil | Suites required; lista exacta por perfil externa; allowlist por item | Suite flexible pero amplía scope; lista exacta precisa pero mantenimiento de churn; ambos requieren approval de cambio. | Mantener suites en repo como candidate, con expected exact IDs firmados externamente para gate certificador. | Autoridad de perímetro. |

La autorización general recibida para STEP-24 permite investigar y documentar; no contesta ninguna de estas decisiones ni las convierte en `APPROVED`.

## 12. Referencias técnicas primarias consultadas

Estas referencias ayudan a diseñar controles; no prueban el estado de este host y no se adoptan herramientas/dependencias:

1. [Linux namespaces(7)](https://man7.org/linux/man-pages/man7/namespaces.7.html): describe que namespaces aíslan vistas de recursos globales y enumera tipos (mount, PID, network, IPC, user, etc.). No autentica configuración ni limita recursos automáticamente.
2. [Linux user_namespaces(7)](https://man7.org/linux/man-pages/man7/user_namespaces.7.html): explica UID/GID/capabilities por user namespace, incluido que capabilities en namespace hijo no son capabilities en parent. No demuestra mapping/permissions de un worker sin medirlos.
3. [Linux seccomp(2)](https://man7.org/linux/man-pages/man2/seccomp.2.html): describe filtros syscall BPF y requisito `no_new_privs` o capability en user namespace. No define un perfil seguro apropiado para pytest ni protege filesystem por sí solo.
4. [Bubblewrap README](https://github.com/containers/bubblewrap/blob/main/README.md): dice explícitamente que bubblewrap es constructor de sandbox, no policy de seguridad lista; protección depende de argumentos, advierte sobre recursos montados y límites. Es documentación upstream; no valida la versión local.
5. [Linux cgroup v2](https://docs.kernel.org/admin-guide/cgroup-v2.html): referencia primaria para controles de recursos agrupados (controllers disponibles dependen del sistema). No establece cuotas ni delegación en este checkout.
6. [SLSA provenance v1.1](https://slsa.dev/spec/v1.1/provenance): modelo de provenance enlaza artefactos/buildDefinition/builder/runDetails y define dependencias; su garantía depende de confiar en `builder.id` y verificar downstream. No autentica el controller local ni demuestra aislamiento.
7. [in-toto](https://in-toto.io/): describe attestations de qué pasos fueron realizados, por quién y en qué orden. No determina quién debe ser autoridad TALOS ni que el executor no mienta si está comprometido.
8. [Sigstore Cosign verification](https://docs.sigstore.dev/cosign/verifying/verify/): muestra verificación de firma/blob e identidad/issuer y valida digest claims cuando aplica. No fija por sí sola política de confianza, protección de clave, anti-TOCTOU o aislamiento del worker.

## 13. Experimentos futuros mínimos, todavía no ejecutados

Cada experimento requiere una autorización separada, policy identificada, fixtures sintéticas, workspace descartable fuera del repo y evidencia guardada fuera del checkout. Ninguno se ejecutó en STEP-24.

| Experimento | Precondiciones y riesgo | Oráculo/resultado esperado | Autorización requerida |
|---|---|---|---|
| Bootstrap negativa | Controller/bootstrap externo implementado y autorizado; no usar secrets/datos reales | Ausente, signature inválida, policy expirada/revocada, rollback y nonce replay detienen antes de importar checkout | Autorizar prueba del bootstrap y entorno/custodia. |
| TOCTOU | Copia de controller/input sintético y harness race controlado | Sustitución entre verify/use no cambia bytes ejecutados; si no puede garantizarlo, bloquear | Autorizar adversarial race test aislado. |
| Mount/path escape | Bwrap config versionada, filesystem sintético y probe set cerrado | Lecturas/escrituras a host, `.git`, secretos y protected paths denegadas; workspace autorizado accesible; evidencia independiente | Autorizar aislamiento; no usar DB/corpus real. |
| Namespaces/red/capabilities | Worker sintético; observar namespaces/capabilities desde supervisor confiable | namespace IDs diferencian; host network/sockets/credentials no accesibles; worker no tiene capacidad host | Autorizar observación de boundary, no solo worker report. |
| Resource exhaustion/cleanup | cgroup/rlimits configurados, workload sintético acotado | CPU/mem/PID/storage/timeout enforced; proceso y descendants terminan; host permanece responsive | Autorizar límites y prueba con budget explícito. |
| Seccomp | syscall profile definido desde necesidades reales y fallos esperados | syscall prohibida rechazada; syscalls requeridas funcionan; filter heredado por children según política | Autorizar diseño y test con kernel/runtime identificados. |
| Perfil/coverage | policy expected nodeids firmada; sin ejecutar test bodies para collect-only | exact nodeid equality por profile; los absent/unexpected/duplicate bloquean; collection no se trata como PASS | Autorizar collection primero; autorización adicional para ejecución. |
| B1-R end-to-end | refactor aprobado para Git host-side, esquema IDs y verifier independiente; solo synthetic route | 30 claves exactas con IDs, artifacts validados, resultados funcionales separados; test sin `.git` no intenta Git host | Autorizar implementación por separado y luego ejecución por separado. |
| Evidencia Git | observer/controller y formato versionados; checkout desechable | Capturas nominales idénticas en flags/parser; errors/mismatch no producen status clean; reconocer escrituras transitorias no detectadas | Autorizar prueba observer. |

## 14. Criterios de cierre por bloqueo

| ID | Criterio verificable de cierre |
|---|---|
| A-01 | Autoridad identificada, scope/proceso de aprobación/revocación/updates y revisión registrados fuera del checkout. |
| A-02 | Bootstrap y trust anchor exactos existen fuera del checkout; sus bytes/procedencia verificables; test fail-closed previo a imports. |
| C-01 | Inventario transitivo aprobado; evidencia vincula digest validado a bytes ejecutados; race/rollback tests autorizados pasan sin unknown oculto. |
| B-01 | Boundary documentado con recursos/mounts/UID/caps/network/kernel threats; medidas efectivas observadas desde fuera del worker y límites de recursos enforcement verificados. |
| B-02 | Instalación/version de bwrap y policy de argumentos autorizadas; disponibilidad sola no basta. |
| D-01 | Cada observación tiene clave/ID y bindings exactos; parser/schema rechaza duplicados, faltantes, extra, contradictorios y artifact mismatch. |
| D-02 | Inventario por perfil autenticado fuera del checkout; exact-match de colección y posterior resultado de ejecución bajo autorización. |
| D-03 | Máquina de estados/precedencia/retries cerrada y exhaustivamente verificada; multi-causa no se pierde. |
| D-04 | Flujo Git reside host-side, B1-R no requiere `.git` guest, y prueba sintética autorizada demuestra binding/comparabilidad. |
| E-01 | Reconciliación solo con evidencia histórica nominal completa/comparable; si no existe, preservar explícitamente como no resoluble. |
| F-01 | Operador decide modelo de autoridad e independencia de reviewer acorde al threat model; decisión no asumida por implementación. |

Ninguno de estos bloqueos se considera cerrado por STEP-24.

## 15. Ruta posterior propuesta, no autorizada

1. Operador decide A-01/F-01: autoridad, nivel de assurance, custodia de ancla y separación de roles.
2. Aprobar arquitectura/policy en documento separado: perfiles y nodeid inventory, identidad, recursos, boundary y lifecycle.
3. Emitir directiva específica para diseñar/provisionar bootstrap/controller; definir tests negativos y almacenamiento de evidencia.
4. Tras una revisión de diseño independiente, emitir autorización separada de implementación.
5. Autorizar experimentalmente bootstrap/TOCTOU/isolation con entorno sintético y límites; no tocar datos protegidos.
6. Cerrar contratos de B1-R/coverage/aggregation y resolver conflicto potencial Git-in-worker antes de B1-R autorizado.
7. Ejecutar B1-R y cobertura solo con autorización explícita; adjudicar cada dimensión por separado.
8. Una autoridad competente decide cualquier cambio posterior de estado P1.2/P1.3. STEP-24 no lo hace.

## 16. Estado final, preservación y conclusión

`OBSERVED`: rama y HEAD no cambiaron durante STEP-24. El estado final conserva los cambios staged, unstaged y untracked preexistentes; la única nueva ruta atribuible a esta fase es este expediente. No se ejecutaron pruebas/scripts/harness/worker ni código de TALOS. No se modificaron código, configuración, tests, perímetro, refs o expedientes previos.

`DOCUMENTED`: P1.2 sigue `BLOCKED-REGRESSION`; P1.3 sigue `BLOCKED`; Qwen sigue bloqueado; Playwright permanece limitado a la regresión congelada; bases, corpus, snapshots y estado de aprendizaje protegidos. La anomalía histórica queda `UNRESOLVED_HISTORICAL_EVIDENCE`.

**Conclusión:** `INVESTIGATED_WITH_EXPLICIT_RESOLUTION_PATHS`. Se concretaron causas, evidencia, incertidumbres, alternativas, criterios de cierre y experimentos necesarios. `UNVERIFIED` permanecen bootstrap/ancla externa, autorización, identidad transitiva, TOCTOU efectivo, aislamiento real, recursos, colección/ejecución de once nodeids, B1-R dinámico y reconciliación histórica.

**Estado canónico final:** `P1.2=BLOCKED-REGRESSION`; `P1.3=BLOCKED`.  
**Harness:** implementación no autorizada.  
**B1-R:** ejecución no autorizada.  
**Siguiente paso recomendado:** decisión explícita del operador sobre el modelo de autoridad y garantía; no iniciar trabajo técnico sin una directiva específica.
