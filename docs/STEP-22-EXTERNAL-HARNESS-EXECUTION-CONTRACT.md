# STEP-22 — External harness execution contract

**Tipo:** especificación contractual estática  
**Entrada:** `TRUST_ARCHITECTURE_SELECTED_UNIMPLEMENTED`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Resultado:** `BLOCKED_WITH_EXPLICIT_FINDINGS`  
**Estado de este documento:** diseño propuesto; no implementado ni validado

## 1. Propósito, autoridad y vocabulario

Esta especificación describe cómo podría ejecutarse el Quality Gate bajo la arquitectura A seleccionada en STEP-21: un controlador externo al checkout que posee autoridad host; el checkout, sus tests, configuración y artefactos se consideran inputs no confiables hasta su validación.

Etiquetas utilizadas:

- **OBSERVADO:** evidencia estática registrada en STEP-18, STEP-19 o STEP-20.
- **DECISIÓN STEP-21:** dirección arquitectónica seleccionada documentalmente.
- **PROPUESTA STEP-22:** contrato futuro, no implementado.
- **PENDIENTE:** decisión, identidad o prueba que no existe en la evidencia observada.

El resultado `BLOCKED_WITH_EXPLICIT_FINDINGS` se elige porque faltan dos precondiciones de raíz: una autoridad aprobadora identificada y un bootstrap/ancla externo, protegido y verificable. El detalle protocolario que sigue ayuda a acotar su posterior diseño; no convierte esas precondiciones ausentes en resueltas.

Fuentes de evidencia: [STEP-18](./TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md), [STEP-19](./TALOS-P1.2-STEP-19-EXTERNAL-TRUST-BOOTSTRAP.md), [STEP-20](./TALOS-P1.2-STEP-20-READ-ONLY-TRUST-DISCOVERY.md), [STEP-21](./TALOS-P1.2-STEP-21-TRUST-ARCHITECTURE-ADJUDICATION.md), [perímetro de certificación](./TEST_CERTIFICATION_PERIMETER.md), `scripts/test.sh:1-16`, `scripts/quality_gate.py:569-718,730-928,1218-1245,1473-1605`, `scripts/quality_gate_isolation.py:63-101,213-307`, `config/test_perimeter.json:1-135`, `tests/audit/b1r_contract.json:1-120`.

## 2. Arquitectura y límites de confianza

### 2.1 Roles propuestos

1. **Autoridad aprobadora externa:** rol de gobernanza que aprueba, limita, vence y revoca una identidad exacta de controlador/política. **PENDIENTE:** no se identificó quién desempeña ese rol.
2. **Bootstrap verificador:** componente mínimo cuya identidad se ancla fuera del checkout. Valida la autorización antes de cargar código host del controller o del checkout. **PENDIENTE:** no se encontró ni eligió un bootstrap implementado, trust anchor o formato de autorización.
3. **Controlador externo:** ejecuta solo el protocolo fijo aprobado. Es el único owner de la autoridad host: Git inicial/final, creación del workspace, configuración del boundary, lanzamiento, recolección y agregación.
4. **Checkout TALOS:** datos de entrada no confiables en host. Ninguna configuración que venga del checkout puede ampliar el perfil, los nodeids, los roots, mounts, comandos, permisos o canales de salida autorizados por la política externa.
5. **Worker Bubblewrap:** proceso confinado que ejecuta tests/código del checkout y devuelve resultados limitados. No decide su autorización ni certifica su propio aislamiento.
6. **Verificador de artefactos:** componente separado del productor; consume bytes exactos permitidos. Su identidad debe estar aprobada por la política. La implementación actual del checkout no adquiere independencia por ser llamada “verifier”.
7. **Observador de aislamiento:** componente/procedimiento autorizado que recoge evidencia específica del launch y del boundary. El estado declarado por el worker no basta.
8. **Agregador:** componente confiable (puede ser parte del controller si queda dentro de la identidad aprobada) que valida autorización, resultados, subresultados y cobertura obligatoria. No se importa desde el checkout con autoridad host.

### 2.2 Flujo conceptual

```text
autoridad externa (pendiente de designación)
    → autorización de ejecución concreta
bootstrap externo verificado
    → autentica autorización e identidad exacta antes de código del checkout
controlador externo autorizado
    → observa Git, valida inputs, crea workspace, construye mounts
    → lanza worker Bubblewrap sin interfaz de expansión de privilegios
worker confinado
    → ejecuta items/tests y produce solo artefactos allowlisted
controlador + verificadores independientes
    → recopilan Git, artefactos y evidencia de boundary por separado
agregador autorizado
    → compara cobertura esperada y emite estado; fail-closed
```

Bubblewrap es mecanismo de aislamiento del worker, no autoridad para aprobar el controlador. Su instalación o return code no demuestra que el boundary efectivo sea correcto. La arquitectura actual documentada en STEP-18/20 ejecuta el supervisor del checkout en host; esta propuesta no afirma que la implementación existente satisfaga el flujo anterior.

## 3. Autorización de una ejecución concreta

### 3.1 Datos que debe vincular la autorización

La futura autorización de ejecución debe autenticarse mediante un mecanismo que la autoridad externa deberá seleccionar y aprobar. No se presupone una firma, clave, MAC o servicio concretos. El objeto debe contener como mínimo:

- `schema_version` (entero, versión conocida).
- `authorization_id`, `run_id` únicos e irrepetibles.
- identidad de autoridad emisora y método de aprobación registrado.
- `controller_id`, `controller_version`, identidad/hash de bootstrap y política.
- identidad permitida del runtime, dependencias y herramientas pre-worker.
- repositorio esperado y una regla explícita de checkout (commit/tree y, si se permite, estado de trabajo); nada inferido solo del nombre de ruta.
- `profile_id`, suites, clasificación y conjunto exacto de nodeids autorizados.
- política de aislamiento/version, roots protegidas, mounts y workspace allowlisted.
- fecha de emisión, `not_before`, expiración, nonce/no-replay y estado de revocación consultable o snapshot autenticado de revocación.
- límites de duración, procesos, memoria/CPU si se aplican, tamaños/cantidades de resultados y artefactos.
- identidad del verificador, agregador, esquemas y versiones aprobadas.

### 3.2 Decisiones de política todavía abiertas

No están elegidos: autoridad concreta; raíz bootstrap y su custodio; firma/MAC u otro mecanismo autenticado; formato canónico de autorización; ubicación/control del registro; política de vigencia y revocación offline; regla exacta de checkout limpio/sucio y firma de árbol; versión/runtime/dependencias permitidos; límites de recursos; y proceso de aprobación/rollback.

Esas decisiones afectan seguridad y no se resuelven con defaults documentales. **Sin ellas no puede producirse una autorización válida.** Un archivo dentro del checkout, hash calculado por este, commit reportado por este, clave pública sin procedencia, paquete de sistema o decisión genérica de diseño no satisface la precondición.

### 3.3 Bootstrap y check-to-use

Propuesta necesaria:

1. Un launcher/bootstrap instalado fuera del checkout inicia desde una cadena de confianza aprobada.
2. Antes de importar supervisor, helpers, plugins o dependencias del checkout, valida autorización, vigencia, revocación, identidad del controller/runtime/policy y scope del run.
3. Rechaza campos desconocidos críticos, esquema incompatible, identidades duplicadas/contradictorias y downgrade.
4. Ejecuta el artefacto verificado exacto desde una ubicación/copia protegida o mantiene un handle/copia inmutable que evite TOCTOU; revalidar un path y luego abrirlo por nombre sin protegerlo no basta.
5. La autorización se enlaza a un único `run_id`, nonce y checkout/profile/nodeid permitido. No puede reusarse para otro run, checkout o perfil salvo política externa explícita.
6. Cualquier error de verificación termina antes de ejecutar código del checkout con autoridad host.

La ubicación protegida, semántica de firma, implementación del bootstrap y técnica exacta anti-TOCTOU quedan **PENDIENTES**. No se afirma que existan.

## 4. Cadena previa al worker y datos no confiables

La identidad aprobada debe abarcar el bootstrap/controller y la cadena transitiva efectivamente ejecutada en host: runtime/interpreter, librerías cargadas, módulos internos, configuración que afecta al boundary, binarios invocados, verificador y agregador. Fijar solo el script principal no cubre imports top-level ni herramientas auxiliares.

El controller debe:

- No importar `scripts/`, `src/`, `tests/` ni plugins Python del checkout antes/durante la fase host autorizada.
- Parsear inputs de checkout como datos con parser/versiones validados, limites de tamaño/profundidad y esquema conocido.
- Mantener la allowlist de perfiles, nodeids, roots, mounts, env, argumentos, artefactos y destinos fuera del checkout.
- No interpolar comandos desde strings del checkout; invocar argv estructurado de una allowlist.
- Tratar respuestas del worker como afirmaciones no confiables hasta validación independiente.
- Fallar ante módulos/dependencias inesperados, archivos críticos modificados, runtime no permitido o scope incompatible.

Los hashes identifican bytes; no aprueban su ejecución por sí mismos. Una firma futura solo establecería autenticidad respecto a una clave cuya procedencia y custodio estén aprobados externamente.

## 5. Interfaz controller–worker (propuesta)

### 5.1 Envelope de launch

Propuesta de envelope JSON versionado (no implementado):

| Campo | Tipo / regla propuesta |
|---|---|
| `schema_version` | entero; aceptar únicamente versiones explícitamente soportadas. |
| `run_id`, `worker_id` | UUID canónico; únicos en el run y no reutilizables. |
| `authorization_id`, `controller_identity`, `policy_identity` | strings no vacíos, vinculados al objeto externo verificado. |
| `checkout_identity` | objeto: repositorio esperado, commit completo/tree digest observado, política de dirty state y evidencia; valores declarados por checkout no son autoridad. |
| `profile_id` | enum de perfiles aprobados; no permitir valor ad hoc desde checkout. |
| `nodeids` | lista exacta tomada de la autorización/perímetro canónico; cada elemento string canónico; sin duplicados. |
| `argv` | vector de argumentos estructurados generado por controller; no aceptar comando libre del worker. |
| `inputs` | referencias a archivos allowlisted con digest verificado, tamaño acotado y mount RO; no aceptar paths host arbitrarios. |
| `workspace` | identidad host mantenida solo en controller y mountpoint guest fijo; enviar al worker solo mapping guest necesario. |
| `limits` | timeout y límites de salida/artefactos definidos por política versionada; su elección concreta requiere aprobación. |
| `environment` | mapa allowlisted; rechazar variables adicionales, paths host, secretos y override de política. |

No se decide aquí un valor universal de timeout/bytes/procesos: son límites de política por perfil y deben quedar aprobados antes de implementación. Hasta tener esos valores, cualquier protocolo que los deje ilimitados no es aceptable.

### 5.2 Boundary y capacidades

Propuesta:

- Checkout montado read-only en guest; `.git` real, roots protegidas, bases/corpus/modelos de producción y secretos no montados.
- Workspace host único bajo una ubicación autorizada, validado por canonicalización/identidad; bind solo al guest path fijo y writable requerido.
- `/tmp` guest separado (tmpfs); red, namespaces, proc/dev y mounts de runtime definidos explícitamente y verificados contra policy.
- Worker no recibe API/broker genérico que pueda pedir paths, comandos, mounts, más workers/perfiles o acceso al host.
- stdin cerrado o limitado; stdout/stderr de tamaño máximo; timeout mata el proceso y sus descendientes conforme al mecanismo aprobado.
- Salidas solo en destinos y nombres allowlisted bajo el workspace/run; no symlinks, hardlinks, path traversal ni archivos adicionales no declarados.
- Interrupción, señal, crash, timeout, output truncado, child residual o protocolo inválido => estado explícito no satisfactorio; no fallback sin aislamiento.

Estas son condiciones de diseño, no evidencia de que la política Bubblewrap actual las satisfaga.

## 6. Esquema de resultados propuesto

### 6.1 Registro envelope

Cada objeto es JSON UTF-8 canónico bajo schema versionado. Límites máximos y enumeraciones cerradas son parte del contrato. Los siguientes límites son **propuesta de diseño** para aprobar/ajustar antes de implementación, no configuración existente:

- envelope de resultado: 1 MiB máximo; profundidad JSON máxima 32; máximo 10.000 registros de caso/subresultado por envelope;
- stdout y stderr combinados por worker: 16 MiB; conservar indicación de truncamiento y bytes observados;
- artefacto genérico: 64 MiB por archivo, máximo 128 archivos/worker; un perfil puede fijar límites menores, no mayores sin versión/policy nueva;
- strings: máximo 16 KiB salvo blob/base64, que no se acepta en JSON de resultado;
- listas: máximo del tamaño esperado por contrato; para B1-R exactamente 10 casos × 3 repeticiones, no más;
- desconocido/duplicado: rechazar campos críticos desconocidos; campos de extensión solo en namespace/version allowlisted; claves JSON duplicadas inválidas.

Campos obligatorios:

```text
schema_version
run_id
authorization_id
controller_identity
bootstrap_identity
policy_identity
checkout_identity
profile_id
perimeter_identity
expected_nodeids[]
node_results[]
worker_results[]
artifact_results[]
isolation_observations[]
git_observations[before, after]
aggregator_identity
aggregator_version
started_at, completed_at
incidents[]
profile_result
global_result
```

`node_results[]` incluye exactamente un owner-item por nodeid: `nodeid`, `classification`, `owner`, `execution_mechanism`, `worker_id`, `functional_status`, `exit_code`, `timeout_status`, referencias a artifact/isolation/Git y diagnostics. Subresultados distinguen productor y consumidor, `run_id`, `worker_id`, scope, evidencia, status y limitaciones.

### 6.2 Dimensiones separadas

Nunca colapsar:

1. `functional_status`: `PASS | FAIL | ERROR | NOT_RUN`.
2. `artifact_status`: `VALID | INVALID | MISSING | NOT_APPLICABLE` (solo cuando el contrato de nodeid lo permite).
3. `isolation_status`: `DEMONSTRATED | NOT_DEMONSTRATED | BREACHED | UNKNOWN`.
4. `git_observation_status`: estado separado para antes/después y `EQUAL | DIFFERENT | UNCOMPARABLE`.
5. `coverage_status`: `COMPLETE | INCOMPLETE | DUPLICATE | CONTRADICTORY`.
6. `profile_status` y `global_status`: estados adjudicados por agregador, no por worker.

`NOT_APPLICABLE` requiere regla de policy y justificación identificada; no equivale a evidencia ausente. El worker no puede emitir `isolation_status=DEMONSTRATED` como autoridad. Solo el evaluador de aislamiento consume observaciones autorizadas.

### 6.3 Validación e integridad

- Hashes criptográficos identifican bytes de artefactos; el controller recomputa sobre bytes recolectados y el verificador valida contenido conforme a su identidad/policy.
- Vincular cada artefacto a `run_id`, worker, nodeid/caso, nombre allowlisted, ruta guest relativa, digest y tamaño.
- No seguir symlinks/hardlinks no permitidos; rechazar rutas absolutas, `..`, destino fuera de workspace, nombre duplicado o tipo inesperado.
- Verificador lee los mismos bytes que el controller preserva; cualquier transformación debe ser identificada y producir digest/lineage nuevos.
- Un hash coincidente significa integridad respecto a bytes identificados, no verdad, autenticidad del productor, ejecución del caso correcto o aislamiento.
- JSON inválido, bytes extra, versiones no soportadas, hash discordante, salida truncada necesaria, artefacto omitido o mismatch de run/checkout/profile => `RESULT_INVALID` o `ARTIFACT_VERIFICATION_FAILED`; no se ignora.

## 7. Observación Git y afirmaciones permitidas

### 7.1 Observación pre/post

El controller autorizado captura antes y después del run:

- identidad del mismo checkout (ruta real y commit/tree según policy);
- comando Git y flags exactos, incluyendo untracked conforme al contrato B1-R;
- exit code, stdout, stderr, timestamp y `run_id`;
- estado de diferencias obtenido y clasificación de cambios.

La comparación B1-R actual significa igualdad de lo reportado por `git status --porcelain --untracked-files=all` en ambas capturas. Un error, output no parseable, checkout distinto, captura ausente o scope/command diferente implica `OBSERVATION_FAILED`/`UNCOMPARABLE`, nunca estado vacío o PASS. Diferencias implican `CHECKOUT_CHANGED`.

### 7.2 Límites

Git pre/post igual no demuestra ausencia de escrituras transitorias, archivos ignorados/no observados, efectos externos o cambios revertidos entre capturas. No exponer `.git` real al worker para obtener observación. Afirmaciones más fuertes requieren prevención/telemetría adicional de escrituras con scope y limitaciones explícitos; la fuente y autoridad de esa evidencia deben adjudicarse antes de usarla.

## 8. B1-R y relación con cobertura

B1-R exige diez condiciones por tres ejecuciones, es decir 30 observaciones. Cada tupla `(run_id, nodeid, case_id, repetition=1..3)` debe aparecer exactamente una vez. La lista de diez `case_id` proviene del contrato B1-R autorizado; no se acepta que el worker modifique el inventario. Se verifican además las comparaciones normalizadas, probes, guards, counters, diagnósticos, resultado funcional, artefacto y verifier según sus contratos vigentes.

Las 30 observaciones son subresultados del item B1-R; no sustituyen ese nodeid ni los otros diez nodeids obligatorios. A su vez, ejecutar los once nodeids no satisface la matriz de 30 observaciones si B1-R no produjo su propia evidencia completa.

Para PASS compuesto de B1-R se requieren todas estas dimensiones independientes: functional pass, artifact valid, isolation demonstrated por evidencia del controller/evaluador, Git before/after ambos observables y equivalentes, y ownership/cobertura exactos. Un resultado de verifier “TECHNICAL PASS”, exit code cero o status Git igual no sustituye a otra dimensión.

## 9. Estados y máquina de estados

Los estados mínimos solicitados se asignan por ámbito:

| Estado | Ámbito | Significado / transición |
|---|---|---|
| `NOT_AUTHORIZED` | ejecución global/preflight | No existe autorización aplicable; detener antes de código no confiable en host. |
| `AUTHORIZATION_INVALID` | autorización/preflight | Firma/identidad/scope/expiración/revocación/nonce inválido o contradictorio. |
| `PREFLIGHT_BLOCKED` | ejecución global | Entorno, checkout, policy, herramientas o identidad no satisface precondiciones. |
| `WORKER_NOT_STARTED` | worker | Lanzamiento denegado/fallido antes de ejecutar; el caso no puede ser PASS. |
| `WORKER_FAILED` | worker/caso | Exit no satisfactorio, crash, señal, error o resultado funcional fallido. |
| `WORKER_TIMED_OUT` | worker/caso | Límite temporal excedido; detener y recoger diagnóstico sin convertirlo en éxito. |
| `RESULT_INVALID` | objeto/caso | Schema, identidad, run, datos, cardinalidad o integridad inválidos. |
| `ARTIFACT_VERIFICATION_FAILED` | artefacto/caso | Artefacto faltante, inválido, no vinculable o rechazado por verificador. |
| `ISOLATION_UNVERIFIED` | evaluación de aislamiento | Falta evidencia suficiente de boundary real; no afirmar demostrado. |
| `COVERAGE_INCOMPLETE` | perfil | Nodeid, caso, repetición o subresultado requerido ausente; también registrar duplicados/contradicciones explícitamente. |
| `CHECKOUT_CHANGED` | observación checkout/perfil | Estado Git final distinto al inicial; evaluar según policy sin éxito automático. |
| `OBSERVATION_FAILED` | observador Git | Git falló, estado no parseable o captura incompleta. |
| `PASS` | caso/perfil/global | Solo si todas las precondiciones y dimensiones aplicables del scope resultan satisfechas. |
| `FAIL` | caso/perfil/global | Propiedad funcional/assertion no satisfecha con evidencia válida. |
| `BLOCKED` | caso/perfil/global | No se puede adjudicar debido a autoridad, identidad, precondición o evidencia faltante/inválida. |

Flujo global:

```text
UNSTARTED
  → AUTHORIZATION_CHECK
      → NOT_AUTHORIZED | AUTHORIZATION_INVALID | PREFLIGHT_BLOCKED
      → AUTHORIZED
          → WORKERS_RUNNING
              → WORKER_NOT_STARTED | WORKER_FAILED | WORKER_TIMED_OUT
              → RESULTS_VALIDATION
                  → RESULT_INVALID | ARTIFACT_VERIFICATION_FAILED
                  → ISOLATION_EVALUATION
                      → ISOLATION_UNVERIFIED
                  → GIT_COMPARISON
                      → OBSERVATION_FAILED | CHECKOUT_CHANGED
                  → COVERAGE_AGGREGATION
                      → COVERAGE_INCOMPLETE
                      → FAIL | BLOCKED | PASS
```

Las causas pueden coexistir; el envelope debe preservar todas, con una regla de precedencia versionada. Ninguna causa de bloqueo puede desaparecer por una causa de menor severidad. `PASS` solo es alcanzable cuando autorización, identidad, worker, artefactos, aislamiento, observaciones Git y cobertura exigida son válidos y compatibles. Los subestados funcionales no se sustituyen por el estado del perfil/global.

## 10. Rechazos obligatorios y separación plan/validación

El agregador rechaza con estado explícito: autorización ausente/inválida/expirada/revocada; identidad/versión no autorizada; mismatch de runtime/policy; perfil/nodeid fuera de scope; entrada/campo crítico desconocido; identidad/run contradictoria; duplicado o ausente; timeout/error no representado; artefacto fuera de allowlist, truncado, duplicado, malformado o hash mismatch; verifier incompatible/no autorizado; evidencia real de aislamiento ausente; Git no observable/diferente; y error del controller/agregador.

Implementación futura (no autorizada aquí): seleccionar autoridad y bootstrap; empaquetar controller/policy/runtime; diseñar interfaz/artefactos; adaptar integración sin alterar cobertura. Validación futura (autorización separada): pruebas de autenticación/revocación/rollback/TOCTOU/fail-closed; boundary real Bubblewrap con pruebas sintéticas; integración exacta de cobertura; B1-R completo bajo aislamiento real; auditoría de side effects y adjudicación humana. No se considera que planificar equivalga a demostrar.

## 11. Decisión STEP-22 y bloqueo explícito

Los contratos de interfaz, resultados, Git, aislamiento y cobertura quedan especificados como **propuestas** en este documento y en sus matrices compañeras. No puede declararse `EXTERNAL_HARNESS_CONTRACT_SPECIFIED` porque faltan contratos críticos de autoridad: quién aprueba/revoca, cuál es el trust anchor/bootstrap concreto, cómo se autentica su procedencia, dónde se instala y cómo se verifica la identidad efectiva antes de uso. También faltan decisiones aprobadas sobre política exacta, límites de recursos y semántica de autorización.

**Resultado:** `BLOCKED_WITH_EXPLICIT_FINDINGS`. La resolución requiere decisión de gobernanza externa y evidencia de provisionamiento/verificación; no se suple implementando una firma o clave arbitraria dentro del checkout.

**Estado obligatorio:** `P1.2 = BLOCKED-REGRESSION`. STEP-22 no autoriza implementación, tests, modificación del perímetro ni transición de fase.
