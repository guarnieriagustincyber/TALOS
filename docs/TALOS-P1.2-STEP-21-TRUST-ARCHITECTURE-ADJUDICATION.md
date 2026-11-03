# TALOS P1.2 — STEP-21: trust architecture adjudication

**Entrada:** `EXTERNAL_TRUST_DESIGN_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** decisión arquitectónica y contrato estático  
**Resultado:** `TRUST_ARCHITECTURE_SELECTED_UNIMPLEMENTED`

## 1. Identidad y estado observado

Al inicio de STEP-21:

- Repositorio: `/media/agustin/Laboratorio/study-engie`.
- Rama: `talos-current-audit`.
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Git reportó 1.869 paths staged, 23 unstaged y 71 untracked. Son conteos de estado y no demuestran autoría.
- El destino STEP-21 no existía. Los expedientes STEP-18, STEP-19 y STEP-20 estaban presentes.

Esta etapa usa la evidencia documental ya registrada en esos expedientes; no repite búsquedas del entorno ni eleva sus observaciones a validación dinámica.

Comprobación final tras crear el expediente: rama y HEAD no cambiaron; Git reportó 1.869 paths staged, 23 unstaged y 72 untracked. El único estado nuevo de esta etapa es `?? docs/TALOS-P1.2-STEP-21-TRUST-ARCHITECTURE-ADJUDICATION.md`; los conteos staged y unstaged permanecen iguales. Los conteos no prueban autoría y los cambios preexistentes se preservaron.

## 2. Evidencia relevante

### STEP-18 — autoridad host y ownership

STEP-18 documentó que el flujo actual ejecuta `scripts/quality_gate.py` del checkout en el host antes de iniciar Bubblewrap; importa helpers/configuración del checkout, prepara workspaces y lanza pytest después mediante el launcher de aislamiento. La trust root del manifiesto protegido no autentica el supervisor, el intérprete ni todos los módulos importados. El resultado fue `HOST_AUTHORITY_ADJUDICATION_PARTIAL`; no se demostró política de autorización host independiente.

La propiedad actual de los nodeids permanece estándar: los items de `tests/unit` y `tests/audit` son `required`. Ninguno fue transferido a un controller externo. STEP-18 identificó once items afectados, listados en §7.

### STEP-19 — contrato de bootstrap

STEP-19 concluyó que los hashes y verificadores internos detectan ciertas discrepancias de contenido, pero no autorizan independientemente el código que los calcula, ejecuta o valida. La mención de un wrapper externo en la especificación A-PRE no identificó instalación, owner, versión autorizada, ancla, aprobador ni revocación desplegados.

T1 (aprobación manual), T2 (harness independiente) y T3 (firma) quedaron como diseños posibles no observados; T4 (confianza únicamente en checkout) fue rechazado como independencia. Resultado: `EXTERNAL_TRUST_DESIGN_PARTIAL`.

### STEP-20 — descubrimiento acotado del entorno

STEP-20 encontró herramientas de sistema como `bwrap`, `git` y utilidades criptográficas genéricas, pero no una autorización TALOS, wrapper de Quality Gate instalado, clave/ancla con procedencia demostrada o política de revocación en las rutas inspeccionadas. La presencia de Bubblewrap es capacidad instalada, no autorización del supervisor ni prueba del aislamiento efectivo. La búsqueda fue acotada y no demuestra inexistencia universal.

STEP-20 observó que `scripts/test.sh` prefiere `.venv/bin/python`; en ese checkout el path era un symlink modificable por el usuario observado. Esto no establece una identidad de ejecución independiente. Resultado: `EXTERNAL_TRUST_DESIGN_PARTIAL`.

## 3. Decisión arquitectónica

### Recomendación principal: A — harness externo con identidad aprobada

Se selecciona A como **arquitectura de referencia futura**, no como mecanismo existente ni autorización de implementación. Un controlador externo, instalado y aprobado fuera del checkout, será el único componente con autoridad de orquestación host. Debe usar un bootstrap independiente que valide su propia identidad/política y la autorización vigente antes de cargar o ejecutar cualquier código no confinado del proyecto.

El controlador no importa módulos Python del checkout en el host. El checkout se trata como input no confiable: código de tests solo se ejecuta dentro del worker Bubblewrap; las configuraciones, manifests, reportes y artefactos se parsean con esquemas/versiones y límites fijados por el controlador aprobado. El checkout no puede solicitar comandos host arbitrarios, mounts, roots o expansión de perfiles.

La recomendación combina el límite operacional de A con la función de verificación previa descrita en B, pero **no** propone un segundo bootstrap escrito en el checkout. El bootstrap es parte del entorno/controlador externo cuya identidad y raíz deben ser aprobadas de manera independiente.

### Autoridad aprobadora: rol requerido, identidad no adjudicada

La política futura debe designar explícitamente una autoridad operativa/normativa (persona, equipo o proceso institucional con responsabilidad de release) que pueda aprobar, expirar y revocar versiones del controlador. Ninguna autoridad concreta fue identificada en STEP-18–20; no se inventa ni se presume una.

La designación de esa autoridad, su ámbito y el anclaje de su decisión son una **precondición bloqueante**. Por ello, queda seleccionada una forma arquitectónica suficiente, pero la implementación y operación no pueden comenzar hasta que esa autoridad exista y emita una decisión fuera del checkout.

### Comparación de alternativas

| Alternativa | Límite de confianza y operación | Auditabilidad / complejidad | Adjudicación |
|---|---|---|---|
| **A. Harness externo con identidad aprobada** | Autoriza, observa Git, crea/valida workspace, decide mounts, lanza Bubblewrap, recolecta y agrega. El checkout no ejecuta con autoridad host ni amplía capacidades mediante configuración/request. | Frontera explícita y evidencia separable. Exige instalar, identificar, aprobar, actualizar y revocar el controller fuera del repo; requiere diseñar un protocolo de datos y cobertura. | **Seleccionada como dirección principal no implementada.** Reduce la superficie de código del checkout con autoridad host. Sigue pendiente nombrar la autoridad aprobadora, anclar identidad, política y despliegue. |
| **B. Bootstrap mínimo con autorización externa** | Un bootstrap externo verifica autorización antes de cargar al supervisor. El bootstrap y su clave/verificador raíz necesitan a su vez identidad protegida e independiente. | Puede acotar la capa confiable, pero introduce una raíz de confianza adicional, vinculación check-to-use, distribución de claves y riesgo TOCTOU. | **No se selecciona como alternativa independiente al harness.** La función de bootstrap se requiere dentro de A; no se ejecutará el supervisor del checkout simplemente tras una verificación autocontenida por él mismo. |
| **C. Supervisor del checkout con validaciones internas** | El checkout conserva supervisor, imports, ancla, verificador y reporte. Puede sustituirlos conjuntamente y presentarse como autorizado. | Menor cambio de despliegue, pero autoridad y juicio dependen del mismo objeto evaluado. Los checks no eliminan la autoautorización. | **Rechazada para este requisito.** No ofrece independencia aunque sus tests internos pasen o sus hashes sean consistentes. |

La selección de A no resuelve por inferencia las decisiones de política externa. Se identifica un contrato de destino que puede someterse a aprobación; no se afirma que su aprobador, bootstrap, instalación o mecanismos existan actualmente.

## 4. Contrato mínimo de autorización e identidad

### Estado: requisitos propuestos, no implementados

| Elemento | Contrato futuro mínimo | Evidencia actual |
|---|---|---|
| **Autoridad aprobadora** | Rol designado por una política fuera del checkout; autoriza una identidad/version específica y puede expirar/revocar. Mantiene registro inmutable de decisión, scope y vigencia. | No identificada en STEP-18–20. Decisión externa pendiente. |
| **Bootstrap confiable** | Ejecutable/harness cuya identidad se estableció por un canal externo al checkout. Comprueba autorización antes de importar cualquier módulo host del checkout; si no puede validarla, no ejecuta supervisor ni fallback. | No encontrado en el entorno inspeccionado. |
| **Identidad aprobada** | Identifica controller y módulos transitivos host, binarios/runtime, dependencias, configuración efectiva de política, interfaz de datos, versión de esquema y herramientas críticas usadas para observar Git y lanzar Bubblewrap. | Solo rutas/paquetes locales parcialmente identificados; no existe identidad aprobada cerrada. |
| **Integridad de ejecución** | La comprobación cubre bytes exactos que se ejecutarán. El controller ejecuta una copia aprobada/controlada o asegura la identidad del objeto abierto frente a sustitución; no acepta un hash producido por el propio checkout como autorización. | Sin mecanismo observado. |
| **TOCTOU** | La verificación y el uso se vinculan al mismo artefacto inmutable o a handles/copias protegidas; todo cambio entre aprobación y ejecución invalida la corrida. | Sin contrato o evidencia observada. |
| **Ámbito** | Allowlist explícita de perfiles, suites/nodeids, roots protegidas, mounts, workspace, variables, comandos, procesos y artefactos. El checkout puede restringir el scope, nunca ampliarlo. No hay broker genérico de comandos/rutas. | El runner del checkout contiene lógica de perfil/mount; falta autorización externa de esa política. |
| **Vigencia y actualización** | Política de expiración, rotación, revisión y aprobación de nuevas versiones; control anti-rollback; revocación propagada antes de la siguiente ejecución autorizada. | No observado para supervisor TALOS. |
| **Fallo cerrado** | Autorización ausente, no verificable, inválida, expirada, revocada, contradictoria, fuera de scope o con identidad distinta => `BLOCKED`/`ERROR`; sin ejecución privilegiada ni degradación a runner del checkout. | El checkout describe fail-closed para algunas condiciones de aislamiento; no existe evidencia del gate de autorización propuesto. |
| **Auditoría** | Evidencia fuera del checkout: decisión/aprobador, versión y digest autorizados, vigencia, política/scope, identidad observada, run-id, checkout, worker, perfiles/nodeids, resultados y errores de autorización. | STEP-20 observó metadatos de paquetes y Git, no registro externo de aprobación/ejecución. |

### Supuestos que deben aprobarse antes de implementación

1. Existe una autoridad externa legítima y operable que puede aprobar y revocar el controlador.
2. Hay un canal/almacenamiento fuera del checkout con control suficiente para distribuir identidad y decisión, y un bootstrap de procedencia verificable.
3. El runtime/dependencias que utilizará el controlador pueden fijarse sin importar código no autorizado del checkout.
4. La política de perfiles, roots, mounts, workspaces y artefactos se puede hacer fija y auditable en el controller.
5. El protocolo y la evidencia se pueden consumir sin ejecutar el parser/agregador del checkout con autoridad host.

Ninguno de estos supuestos se declara probado por la disponibilidad de `bwrap`, los paquetes del sistema, los hashes de A-PRE ni el estado de Git.

## 5. Responsabilidades host y worker

### Controlador externo autorizado — autoridad host propuesta

1. Verificar su identidad bootstrap y la autorización vigente antes de iniciar lógica del gate.
2. Validar identidad del checkout como input (commit, tree y estado reportado) sin concederle autoridad por esa identidad.
3. Capturar Git inicial y final del mismo checkout con el mismo comando/scope; conservar códigos, stdout/stderr y errores.
4. Crear un workspace host de run único, canonicalizarlo, comprobar contención/no-solapamiento y asociarlo a un destino guest fijo.
5. Aplicar la política aprobada de Bubblewrap/mounts/roots protegidas y lanzar solo el perfil/nodeids permitidos.
6. Recoger únicamente archivos de salida allowlisted asociados al mismo run; preservar exit code, timeout, diagnósticos y errores.
7. Validar independiente el formato/integridad/provenance de reportes según una política identificada.
8. Obtener evidencia de la frontera real separada del resultado funcional.
9. Agregar por suite y nodeid sin perder obligaciones, clasificaciones, subresultados ni contradicciones.
10. Guardar evidencia y decisión fuera del checkout, sin presentar un resultado del worker como autorización del controller.

### Worker Bubblewrap propuesto

- Ejecuta pytest, tests y código del checkout como inputs no confiables solo dentro del boundary aprobado.
- No ve el `.git` real ni accede a bases/corpus/raíces protegidas; cualquier excepción requiere política explícita separada y no se presume para STEP-21.
- Usa solo mounts read-only y workspace writable autorizados; conserva `/tmp` guest aislado y el enmascaramiento definido por política.
- No puede elegir roots, mounts, comandos host ni ampliar perfiles mediante requests.
- No determina su propia autorización, no declara que el aislamiento fue efectivo y no reemplaza Git host-side o al agregador.

Estos son roles contractuales propuestos. La arquitectura actual observada en STEP-18 y STEP-20 no se declara conforme ni probada por esta adjudicación.

## 6. B1-R: ejecución compuesta y agregación

B1-R conserva las diez condiciones funcionales del contrato y las tres repeticiones por condición: **30 observaciones normalizadas**. El item pytest B1-R mantiene ownership estándar `required`; el controlador externo no convierte sus propios subresultados en un nodeid ejecutado.

### Enlace de evidencia mínimo

Cada bundle/run debe vincular, sin campos ambiguos:

- `run_id` único y resultado de autorización: controller identity/version, policy identity/scope, aprobación vigente y perfil autorizado.
- Identidad observada del checkout (commit/tree/estado inicial) y del worker/lanzamiento; los valores observados no sustituyen la autorización.
- Nodeid exacto, clasificación vigente `required`, owner estándar pytest, suite/perfil y obligación de ejecución.
- Para cada una de 30 observaciones: caso contractual, ordinal de repetición `1..3`, resultado normalizado, diagnóstico, timeout y vínculo al proceso worker.
- Exit code, timeout, stdout/stderr y error de worker sin fallback o interpretación como éxito.
- Artefacto exacto recolectado, identidad/run/path allowlisted, integridad y salida/findings del verificador independiente.
- Evidencia de aislamiento producida/observada por un componente autorizado distinto del worker; boundary, mounts y condiciones cubiertas.
- Capturas Git inicial y final host-side con mismo checkout/comando/scope, exit/error y estado reportado. Solo se evalúa igualdad de ambos estados observables.
- Resultado agregado del item/suite con referencias a todos los subresultados y al mismo `run_id`.

### Productores, consumidores y reglas

| Dimensión | Productor | Consumidor/regla |
|---|---|---|
| Autorización/identidad | Bootstrap/controller externo | Rechazar ausencia, expiración, revocación, scope incorrecto o mismatch antes de host execution. |
| Función | Worker confinado | Verificar diez casos × tres repeticiones y conservar normalización/diagnósticos; faltantes o duplicados bloquean. |
| Artefacto | Worker a ruta allowlisted | Recolector verifica origen/run/path y verificador independiente analiza bytes exactos. `TECHNICAL PASS` no autentica al productor ni prueba aislamiento. |
| Aislamiento | Controller/observador aprobado | Comprobar evidencia específica del launch/boundary requerido; ni return code cero ni tests funcionales la sustituyen. |
| Git pre/post | Observador host aprobado | Exigir dos capturas válidas del mismo checkout y comando; comparar igualdad reportada. Error de Git nunca equivale a estado vacío/limpio. No afirmar ausencia de escrituras transitorias. |
| Resultado del nodeid | Agregador externo autorizado | Componer los resultados solo si todos son válidos, completos, compatibles y vinculados al mismo run/profile/identity. |

**Bloqueo obligatorio:** nodeid/subresultado ausente o duplicado; worker/verifier/controller no autorizado; perfil no permitido; clasificación distinta de la vigente; run/checkout/identidad contradictoria; repetición, observación o artefacto faltante; error de verificación; evidencia real de aislamiento ausente; Git no observable; o status Git distinto => no PASS (`ERROR`, `FAIL` o `BLOCKED` conforme a la política aplicable). No se sintetiza un resultado global desde return codes solamente.

## 7. Cobertura obligatoria

Las siguientes once obligaciones permanecen bajo propiedad estándar de pytest y clasificación `required` en `tests/unit` o `tests/audit`. El contrato externo puede aportar subresultados al item compuesto solo después de una aprobación/adjudicación futura; no puede sustituir items padre, omitirlos del perfil estándar o reclassificarlos. No se cambia `config/test_perimeter.json`, perfiles, owners ni reglas existentes en STEP-21.

| # | Nodeid canónico | Clasificación y propiedad actual | Separación contractual necesaria |
|---:|---|---|---|
| 1 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace` | `required`; item pytest estándar | Helper de mapeo no equivale a ejecución Bubblewrap ni a una autorización host. |
| 2 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace` | `required`; item pytest estándar | Assertion de contención se conserva; no prueba por sí sola el boundary OS. |
| 3 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace` | `required`; item pytest estándar | Boundary real del child permanece subresultado vinculado al item; fake no satisface esta propiedad. |
| 4 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable` | `required`; item pytest estándar | Test de fail-closed simulado conserva su significado; no es prueba positiva de aislamiento. |
| 5 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved` | `required`; item pytest estándar | Exit code child es subresultado del item, no otro nodeid. |
| 6 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox` | `required`; item pytest estándar | Evidencia de runtime/mount read-only requiere observación del worker/boundary, no solo ruta esperada. |
| 7 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary` | `required`; item pytest estándar | Pytest hijo no cuenta como ejecución independiente del item padre. |
| 8 | `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts` | `required`; item pytest estándar | El observador host conserva identidad Git; el child prueba solo los límites que sus assertions ejercitan. |
| 9 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap` | `required`; item pytest estándar | Requiere boundary real; no se reemplaza por binding reportado sin validación independiente. |
| 10 | `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt` | `required`; item pytest estándar | Fake verifica orquestación simulada; nunca se presenta como evidencia de aislamiento real. |
| 11 | `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile` | `required`; item pytest estándar | Item compuesto necesita subresultados de worker, artifact/verifier, aislamiento y Git, sin cambiar ownership. |

El agregador debe tomar el conjunto esperado de nodeids del perímetro autorizado para el perfil y comparar contra resultados observados. Un perfil inexistente/no autorizado/incompleto no satisface ningún item. Cada item tiene exactamente un owner y un resultado pytest; los procesos hijos, controladores, verificadores y observadores se almacenan como subresultados con rol e identidad. Ausencia, duplicación o contradicción bloquea el gate. `qualification-required` conserva su semántica release-only y no descarga estos items `required`.

## 8. Trabajo futuro y criterios de autorización

STEP-21 no implementa ni autoriza tareas futuras. Para reabrir la implementación deberán adjudicarse por separado, con alcance/autoridad propios:

1. **Designación de autoridad:** identificar formalmente aprobador/revocador, jurisdicción, procedimiento y almacenamiento de aprobación externo al checkout.
2. **Provisión del controller/bootstrap:** determinar responsable, origen de distribución/instalación, identidad exacta, runtime/dependencias y protección frente a sustitución/rollback; demostrar que no importa código arbitrario del checkout con autoridad host.
3. **Política ejecutable:** fijar perfiles, los once nodeids y sus clasificaciones, roots/mounts, workspace, comandos, canales de salida y tratamiento de errores.
4. **Integridad check-to-use:** definir y validar cómo se ejecutan los mismos bytes cuya identidad se aprobó, cómo se detecta TOCTOU y cómo se aplica expiración/revocación/fallo cerrado.
5. **Protocolo de cobertura:** definir schema/versionado de item y subresultados, unicidad/run-id, fuentes canónicas de clasificación, agregación, discrepancias y preservación externa.
6. **Validación del bootstrap:** en etapa explícitamente autorizada, demostrar rechazo de autorización ausente, inválida, vencida, revocada, fuera de scope, identidad alterada, downgrade y sustitución entre check/use. Probar sin ejecutar código host del checkout antes de la autorización.
7. **Validación de aislamiento:** tests sintéticos aprobados que acrediten boundary real, mounts, denegaciones, raíces protegidas, `/tmp`, red y propagación de errores; distinguirlos de tests de helpers/fakes.
8. **Adjudicación B1-R:** demostrar 30 observaciones, guards/probes/counters, artefacto y verificador independiente, Git inicial/final host-side y evidencia real de aislamiento, con enlaces de identidad/run y dimensiones separadas.
9. **Revisión de cobertura:** demostrar para ambos perfiles que los once items `required` siguen exigibles, ejecutados una vez por owner autorizado, con ausencias/duplicados/contradicciones fail-closed. Ningún hijo sustituye al padre.
10. **Criterio de reapertura P1.2:** una adjudicación posterior debe inspeccionar resultados/evidencias anteriores, preservar los bloqueos no resueltos y autorizar expresamente implementación y cada ejecución dinámica antes de realizarlas. Esta selección de arquitectura no convierte evidencia propuesta en `PASS`, aislamiento demostrado ni elegibilidad de release.

La persona/autoridad que puede conceder esa autorización de implementación no queda nombrada aquí: debe ser determinada por la gobernanza aplicable. La aprobación de esta decisión documental no basta por sí sola.

## 9. Cierre

- **Resultado:** `TRUST_ARCHITECTURE_SELECTED_UNIMPLEMENTED`; se selecciona A como dirección de diseño, con bootstrap externo como requisito constitutivo y autoridad aprobadora aún pendiente.
- Rama/HEAD iniciales: `talos-current-audit`, `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Se preservaron cambios staged, unstaged y untracked; sus conteos no establecen autoría.
- No se ejecutaron `pytest`, nodeids, Quality Gate, benchmarks, tests de aislamiento, scripts del proyecto ni imports Python de TALOS.
- No se modificaron código, tests, configuración, perímetro, trust roots ni artefactos previos; no se accedió a bases/corpus protegidos ni se crearon snapshots.
- Este expediente no afirma que A, el bootstrap, el controller, Bubblewrap, el contrato B1-R o la agregación estén implementados, probados o certificados.
- STEP-21 no autoriza implementación, ejecución de pruebas, cierre de P1.2 ni transición a P1.3.

**Estado obligatorio al finalizar:** `P1.2 = BLOCKED-REGRESSION`.
