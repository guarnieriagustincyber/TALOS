# STEP-22 — Trust boundary matrix

**Estado:** propuesta contractual; no implementada ni validada  
**Resultado STEP-22:** `BLOCKED_WITH_EXPLICIT_FINDINGS`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`

Este anexo operacionaliza la arquitectura A de [STEP-21](./TALOS-P1.2-STEP-21-TRUST-ARCHITECTURE-ADJUDICATION.md) y el contrato principal [STEP-22](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md).

## 1. Matriz de componentes

| Componente | Autoridad prevista | Identidad / procedencia requerida | Inputs y confianza | Privilegios/capacidades | Evidencia producida/consumida | Fallo obligatorio |
|---|---|---|---|---|---|---|
| Autoridad aprobadora | Aprueba/expira/revoca controller, policy y run. | Identidad institucional/operativa y atribución de decisiones, definidas por gobernanza fuera del checkout. **No identificada.** | Scope, identidad candidata, perfil/nodeids, vigencia. | No ejecuta tests por virtud de su autoridad; emite decisión delimitada. | Registro externo de aprobación, revocación, fecha, scope y rationale. | Sin autoridad o registro verificable: `NOT_AUTHORIZED`. |
| Trust anchor / bootstrap | Valida autorización e identidad antes del controller. | Implementación/clave/raíz distribuida por canal independiente del checkout. **No encontrada ni elegida.** | Autorización y artefactos candidatos tratados como datos. | Solo iniciar controller exacto si policy verifica. | Decisión de verificación, identidad, vigencia y rechazo. | Ancla ausente, alterada o identidad no verificable: `AUTHORIZATION_INVALID`/`BLOCKED`. |
| Controlador externo | Único orquestador con autoridad host. | `controller_id/version`, dependencias transitivas, runtime y config fijados/aprobados fuera del checkout. **Pendiente.** | Checkout como input no confiable; auth externa; policy aprobada. | Git host, workspace bajo root allowlisted, Bubblewrap argv fijo, recolección/agregación limitada. No comandos/mounts arbitrarios desde checkout. | Git inicial/final; launch receipt; logs acotados; mappings; resultados y agregación. | Identidad, scope o entorno discrepante: `PREFLIGHT_BLOCKED`. |
| Runtime e imports pre-worker | Permite ejecutar controller verificado. | Intérprete, runtime libs, plugins, módulos y dependencias identificados transitivamente. **No fijados/aprobados.** | Binarios/sources instalados; configuración efectiva. | Código host antes del worker. | Inventory/version evidence, proveniencia autorizada. | Módulo inesperado o identidad no cubierta: detener antes de ejecución. |
| Git / observador checkout | Captura el estado del mismo checkout antes/después. | Binario y método de invocación definidos por policy/controller aprobado. | Ruta canónica y checkout identity. | Solo lectura del repo y metadatos relevantes; no exponer `.git` al worker. | Exit/stdout/stderr/status/timestamp, checkout/run ID. | Falla o estado no interpretable => `OBSERVATION_FAILED`, nunca clean success. |
| Perímetro / inventario | Define expected suites/nodeids y clasificación. | Identidad de policy/perímetro autorizada, versión y scope; no confiar en modificación self-asserted por checkout. | Configuración checkout como candidata a comparar; allowlist externa como autoridad. | Determina obligations; no concede ejecución fuera de scope. | Expected nodeid set, classification y profile mapping. | Mismatch, duplicado o item sin clasificación => `PREFLIGHT_BLOCKED` / coverage error. |
| Configuración de aislamiento | Determina mounts, roots protegidas, workspace y capabilities. | Política fija aprobada y vínculo a versión controller/launcher. | Paths y datos del repo no confiables; roots de policy externas. | Solo mounts explícitos, RO salvo workspace aprobado. | Launch config digest, mount plan y evidencia del worker. | Request no allowlisted, protección ausente o mismatch => no lanzar / `ISOLATION_UNVERIFIED`. |
| Workspace host | Root de artefactos temporales y output. | Creado/poseído por controller aprobado, vinculado al run. | IDs de run y límites policy. | Writable solo por worker mediante mount derivado. No overlap con checkout o roots protegidas. | Canonical root identity, host/guest mapping, inventory. | symlink/traversal/overlap/identity mismatch => bloquea. |
| Worker Bubblewrap | Ejecuta código/tests de checkout dentro del boundary. | Identidad de proceso/argv/profile/worker enlazada por controller. | Checkout RO, entradas aprobadas, workspace limitado. | Sin `.git` real, bases/corpus/roots productivas ni secretos; sin requests dinámicos al host. | Exit/timeout, stdout/stderr limitados, archivos allowlisted. | No-start, crash, timeout, escape/violation, protocolo inválido => no PASS. |
| Test code, fixtures, plugins | Ninguna autoridad host; son inputs de prueba. | Identificados por checkout identity para trazabilidad, no confianza. | Código no confiable. | Solo capacidades guest otorgadas explícitamente. | Assertions funcionales y comportamiento del item dentro de worker. | No puede autorizarse, evaluar aislamiento ni entregar comandos al controller. |
| Artefactos del worker | Productor de bytes funcionales allowlisted. | Enlazados a run/worker/nodeid/case y paths relativos. | Bytes no confiables hasta verificación. | Escribe solo workspace asignado. | Digest, tamaño, nombre, lineage y resultados funcionales. | Ausente, duplicado, symlink, traversal, hash mismatch => inválido. |
| Verificador independiente | Evalúa bytes/contrato del artefacto. | Binario/código/policy identity separada del productor y aprobada externamente. **Pendiente.** | Bytes exactos y schema autorizado. | Lectura acotada; no modifica checkout ni declara aislamiento. | Findings y status de conformidad del artefacto. | Identidad desconocida, error o “technical pass” sin scope => `ARTIFACT_VERIFICATION_FAILED`. |
| Observador aislamiento | Evalúa evidencia del lanzamiento/boundary. | Mecanismo/procedimiento y producer identity aprobados. **Pendiente de definición/evidencia.** | Launch receipt, pruebas/observaciones independientes. | No confía en la declaración del worker. | Status separado `DEMONSTRATED/UNKNOWN/BREACHED`, límites y coverage. | Evidencia ausente o insuficiente => `ISOLATION_UNVERIFIED`. |
| Agregador | Adjudica perfiles y global result. | Parte del controller aprobado o componente externo con identidad propia. **No implementado.** | Set esperado, resultados y subresultados con IDs/correlación. | No importa agregador del checkout en host. | Coverage ledger, rechazo/contradicción, status global. | Ausencia/duplicado/contradicción/error => bloquea. |
| Evidencia externa | Preserva decisión y outputs relevantes. | Almacenamiento/control independiente del checkout y del worker. **No identificado.** | Auth, logs, resultados, hashes y limitaciones. | Append/preserve según policy, no reescritura silenciosa. | Paquete reconstruible por `run_id`. | No puede preservar evidencia crítica => no adjudicar PASS. |

## 2. Roles por etapa y autoridad

| Etapa | Host autorizado | Worker | Consumidor |
|---|---|---|---|
| Autorización | Bootstrap externo verifica autorización y controller antes de cualquier módulo checkout. | Aún no existe. | Controller solo inicia con comprobación válida. |
| Preflight | Controller identifica checkout/profile/policy, resuelve expected coverage, captura Git inicial. | No ejecuta. | Gate de autorización/policy. |
| Preparación | Controller crea host workspace y valida no overlap/canonical identity. | No elige ni crea host root. | Launcher usa mapping fijo. |
| Ejecución | Controller construye argv/env/mounts allowlisted y lanza bubblewrap. | Ejecuta pytest/test code confinado. | Parent nodeid conserva owner; child outputs son subresultados. |
| Recolección | Controller copia solo files permitidos, captura Git final y launch results. | No declara integridad de sus outputs. | Verifier/observador/agregador. |
| Verificación | Verifier independiente analiza bytes; observador evalúa boundary; Git comparator compara capturas. | Sin autoridad de adjudicación. | Agregador. |
| Adjudicación | Agregador autorizado compara expected vs observed y dimensiones. | No participa en decisión global. | Registro externo de evidencia. |

## 3. Evidencia y alcance epistemológico

- **Integridad de input**: bytes identificados coinciden con el digest declarado. No equivale a autorización para ejecutarlos.
- **Autorización**: una autoridad válida aprobó identidad, scope y vigencia a través de bootstrap independiente. No se encontró en STEP-18–20.
- **Aislamiento**: evidencia independiente de boundary efectivo. Que `/usr/bin/bwrap` exista o que el worker lo reporte no basta.
- **Integridad de artefacto**: bytes recolectados son los bytes validados. No prueba verdad ni autoría legítima.
- **Git equality**: status observado antes/después coincide. No demuestra ausencia de escrituras transitorias.
- **Test PASS**: assertions del item satisfechas dentro de su proceso. No declara global isolation, trust ni release.

## 4. Precondiciones que permanecen bloqueantes

1. Designar autoridad aprobadora/revocadora.
2. Seleccionar trust anchor y mecanismo de distribución independientes.
3. Definir controller/bootstrap exacto, runtime/dependencias y protección check-to-use.
4. Aprobar política profiles/nodeids, aislamiento, roots/mounts y workspace.
5. Identificar verificador, observador y agregador autorizados.
6. Establecer almacenamiento de evidencia externo y revocación/expiración.
7. Autorizar separadamente validación dinámica del bootstrap, boundary y B1-R.

Hasta resolver estas condiciones, las capacidades de sistema descritas en STEP-20 no pueden considerarse autoridad de certificación.
