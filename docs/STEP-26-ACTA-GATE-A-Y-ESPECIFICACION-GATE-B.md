# TALOS V1.5 — STEP-26: Acta de Gate A y especificación de Gate B

**Rama A:** registro de hashes de candidatos; sin implementación ni ejecución  
**Fecha de inspección:** 2026-10-09  
**Estado documental de Gate A:** `GATE A — CERRADO DOCUMENTALMENTE`  
**Estado de Gate B:** `SPECIFICATION IN PROGRESS`  
**Implementación del harness externo:** `NOT AUTHORIZED`  
**Ejecución B1-R:** `NOT AUTHORIZED`

## 1. Identificación, alcance y evidencia

### 1.1 Identidad del checkout

| Propiedad | Inicio | Cierre |
|---|---|---|
| Repositorio | `/media/agustin/Laboratorio/study-engie` | `/media/agustin/Laboratorio/study-engie` |
| Rama | `talos-current-audit` | `talos-current-audit` |
| HEAD | `cc8acfae623f9d10c8366871470319786b6a7ca4` | `cc8acfae623f9d10c8366871470319786b6a7ca4` |
| Staged | 1.863 | 1.863 |
| Unstaged | 23 | 23 |
| Untracked | 89 antes del informe | 90 después del informe |
| Conflictos reportados | 0 | 0 |

**`OBSERVED`:** identidad y estado inicial se obtuvieron mediante lectura de Git; estado final se cotejó después de crear este único documento. El conteo clasifica registros de `git status --porcelain=v2 --branch --untracked-files=all`: cualquier X distinto de `.` cuenta como staged, cualquier Y distinto de `.` como unstaged, `?` como untracked y `u` como conflicto. Un mismo registro puede contar en staged y unstaged si ambas columnas están modificadas.

**Procedimiento de estado:** `git status --porcelain=v2 --branch --untracked-files=all`. Las rutas se enumeran de forma completa (`--untracked-files=all`), no como directorios untracked colapsados. No se interpretan los conteos como prueba de que no hubiera escrituras transitorias.

### 1.2 Discrepancia histórica

| Fuente documental | Recuento histórico referido |
|---|---:|
| STEP-24 | 87 untracked |
| STEP-25 | 88 untracked |
| STEP-26, estado actual anterior a este informe | 89 untracked |

**`OBSERVED`:** al comenzar esta inspección había 89 entradas untracked.  
**`DOCUMENTED`:** los conteos 87 y 88 aparecen como antecedentes en la directiva STEP-26.  
**`UNRESOLVED`:** no se atribuye causa al cambio entre esos recuentos; el inventario actual no reconstruye ni autentica estados pasados. El documento STEP-26 explica el incremento a 90 al cierre únicamente como la presencia de este nuevo informe, cotejada nominalmente.

### 1.3 Alcance y límites

Se creó únicamente este expediente, en la carpeta documental ya existente. No se alteraron los candidatos untracked ni se incorporaron al índice o inventario normativo. Se registran los seis acuerdos de diseño según la directiva STEP-26 proporcionada por el operador; dicha aprobación es documental y no acredita controles desplegados.

Categorías utilizadas:

- `OBSERVED`: salida directa de una operación de lectura autorizada.
- `STATICALLY_CONFIRMED`: contenido o requisito confirmado documentalmente, sin ejecución.
- `INFERRED`: consecuencia razonable no demostrada dinámicamente.
- `UNKNOWN` / `UNRESOLVED`: evidencia insuficiente o cuestión abierta.
- `NOT_EXECUTED`: comprobación dinámica no realizada.

No se inspeccionó el contenido de los candidatos para buscar secretos. Sus bytes se procesaron únicamente en un flujo de SHA-256 y no se emitieron ni copiaron al informe. Por ello, este inventario **no afirma** que los candidatos estén libres de secretos.

## 2. Resumen de decisiones de Gate A

La directiva STEP-26 aprueba para el diseño las ramas D1–D6 que siguen, sujetas a sus criterios de aceptación. El cierre de Gate A en este expediente significa solamente que esas decisiones y condiciones se registraron documentalmente; no convierte una especificación en control implementado, verificado o efectivo.

## 3. Acta D1–D6

### D1 — Autoridad y separación de privilegios

**Decisión aprobada: Rama A.** El agente y los workers deben usar una identidad dedicada de sistema operativo sin privilegios administrativos. El diseño debe exigir evidencia previa a cualquier autorización futura de que esa identidad no puede usar `sudo`, no pertenece a grupos privilegiados que permitan eludir la separación, no tiene reglas `NOPASSWD` aplicables ni otra ruta autorizada de elevación, no puede modificar la política protegida ni el bootstrap y no puede aprobar cambios en ellos. Deben distinguirse las identidades de operador, agente y workers.

**Criterio de aceptación:** procedimiento de verificación definido y evidencia suficiente futura; crear una cuenta dedicada no basta. **Límite de confianza:** la integridad del sistema operativo, root y los componentes privilegiados permanecen en la base de confianza.  
**Estado:** decisión documental aprobada; implementación y comprobación efectiva `NOT EXECUTED`.

### D2 — Raíz de confianza y política protegida

La política residirá fuera del checkout, será única y no modificable por agente o worker. Tendrá autoridad explícita sobre versión mínima, bootstrap previo a imports del checkout, anti-rollback, seguridad y preflight, perfil seccomp aprobado, aislamiento y límites de recursos, versiones aceptadas de herramientas críticas, y actualización, revocación o sustitución. No habrá artefactos de política con autoridad paralela o contradictoria. Versiones inferiores a la mínima se rechazarán; el estado anti-rollback se protegerá frente a modificaciones del agente.

**Criterio de aceptación:** contrato que identifique artefacto, propietario, permisos, autoridad, formato de versión, actualización y tratamiento de corrupción o ausencia.  
**Estado:** decisión aprobada; protección y anti-rollback efectivos `NOT EXECUTED`.

### D3 — Threat model, aislamiento y preflight

El threat model inicial incluye tests defectuosos o maliciosos; acceso no autorizado a archivos, credenciales, producción o red; falsificación de evidencia; agotamiento de recursos; configuración ausente, incompleta o contradictoria; fallos de aislamiento; y alteración o rollback de política. Se excluye explícitamente la explotación del kernel como amenaza que el harness deba contener; es un riesgo residual. Si se incluye, se requiere reconsideración arquitectónica —por ejemplo, VM desechable— antes de ejecución.

El preflight deberá verificar identidad y privilegios efectivos; integridad, permisos y versión de política; versión/capacidades de Bubblewrap; efectividad de aislamiento; cgroups v2; límites efectivos de CPU, memoria, procesos y tiempo; perfil seccomp autorizado y aplicado; mounts y namespaces; inaccesibilidad de recursos prohibidos; ausencia de secretos no autorizados; y captura de evidencia. Cada requisito, método y fallo pertenece a la política única D2. El perfil seccomp no se genera libremente durante la ejecución. Si cualquier control obligatorio no puede verificarse, no inicia el worker.

**Criterio de aceptación:** predicado verificable, fuente de autoridad y fallo explícito para cada control; configuración presente no equivale a aplicación efectiva.  
**Estado:** diseño aprobado; aislamiento, cuotas, seccomp y preflight efectivos `NOT EXECUTED`.

### D4 — Independencia de worker, observer y verifier

Responsabilidades: **bootstrap/controlador** autoriza entorno y código; **worker** ejecuta el trabajo autorizado sin autoridad sobre evidencia externa; **observer** registra hechos observables desde fuera del dominio del worker; **verifier** valida evidencia, integridad, esquema, cobertura y resultado.

El worker no tendrá acceso al canal observer→verifier: ni escritura, ni lectura, descubrimiento de información protegida ni modificación indirecta. El observer escribe en un canal controlado y el verifier lo consume por una vía definida y protegida. El worker no puede fabricar, borrar, sustituir o corregir registros autoritativos.

**Criterio de aceptación:** contrato de permisos, flujo de datos, autoridad de lectura/escritura y comprobación futura de separación.  
**Estado:** diseño aprobado; independencia efectiva `NOT EXECUTED`.

### D5 — Campaña, identidad y repeticiones

La campaña prevista es de diez casos con tres repeticiones cada uno: **30 observaciones planificadas**, no observaciones realizadas. La identidad mínima de cada observación incluye `campaign_id`, `run_id`, `case_id`, `nodeid`, `repetition_index`, `attempt_id`, `worker_id`, `tree_digest` y referencias de artefactos.

Las repeticiones deben ser independientes bajo condiciones aprobadas, con identidad de worker y entorno. No se permiten reintentos automáticos silenciosos. Todo intento fallido, interrumpido o inválido se conserva y clasifica. Un reintento futuro necesita nuevo `attempt_id`, motivo, vínculo al intento original y autorización conforme a política. Una campaña fija un único `tree_digest`; todos los casos e intentos autorizados deben corresponder al mismo digest, y un cambio de árbol invalida la aprobación y exige nueva autorización.

**Criterio de aceptación:** identidad, unicidad, independencia, fallos y reintentos especificados antes de cualquier ejecución.  
**Estado:** contrato pendiente de Gate B; campaña `NOT EXECUTED`.

### D6 — Cobertura exacta e inventario autorizado

La cobertura normativa es la pareja indivisible **`(nodeids, tree_digest)`**. La campaña futura debe demostrar igualdad exacta entre inventario esperado aprobado, inventario obtenido del árbol autorizado mediante procedimiento posteriormente aprobado e inventario realmente ejecutado/reportado. Ausentes, adicionales, duplicados, inválidos y no ejecutados deben tener reglas explícitas de rechazo.

Igualdad de nodeids no prueba identidad del código; el digest vinculado es obligatorio. El digest no prueba que el inventario sea correcto; ambos se revisan y aprueban conjuntamente. Los once nodeids del worktree candidato no quedan aprobados por observación ni por hash. Los candidatos untracked de este expediente quedan excluidos de la pareja normativa.

**Criterio de aceptación:** pareja exacta revisada y aprobada, procedimiento de comparación y rechazo fail-closed.  
**Estado:** inventario normativo pendiente; no se ejecutó `pytest --collect-only` ni otro mecanismo de colección.

## 4. Inventario nominal de untracked y hashes

**Instante observado:** `2026-10-09T21:35:02.439684-03:00`  
**Comando de inventario:** `git ls-files --others --exclude-standard -z`  
**Conteo:** 89 objetos, todos archivos regulares.  
**Resultado:** 89 SHA-256 estables; 0 excepciones; 0 enlaces simbólicos; 0 objetos especiales.

Para archivos regulares se abrió cada ruta con protección contra enlaces en el componente final y en los directorios padre, se leyó por bloques de 1 MiB y se compararon device, inode, modo, tamaño, mtime y ctime antes/después de la lectura y contra el path actual. Los hashes se registraron solo cuando esas identidades coincidieron. No se siguieron enlaces ni se recorrieron ubicaciones externas. El resultado describe el estado puntual y no el origen, autoría, confianza o aptitud de ejecución del archivo.

Todos los elementos de esta tabla son candidatos untracked, **no normativos y no aprobados**. Los hashes identifican bytes observados; no autentican quién los produjo ni garantizan que permanezcan iguales posteriormente.

| Ruta relativa | Tipo | Bytes | SHA-256 | Estado |
|---|---|---:|---|---|
| `checkpoints/154-p1-2-b06-capture-strategy-checkpoint.md` | regular | 6518 | `ffc37ba31a591dbf87aaf2d41999b09145839bf8dfdf05e0a503b0adaed8f2d8` | HASHED_STABLE |
| `docs/STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md` | regular | 12622 | `dc66df475c86cfb76b34f1d08a8c601104e1c368cb83286efbf316b657be049d` | HASHED_STABLE |
| `docs/STEP-22-DECISIONS-AND-BLOCKERS.md` | regular | 11925 | `79b668e7814ca2c959bcb168f13f87654413153ce11e7f4898d8d78fdc4d37c6` | HASHED_STABLE |
| `docs/STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md` | regular | 23311 | `50735d32ae69ceea17622341d407d2eb4a80019124fdb0cd35186062c5d9d482` | HASHED_STABLE |
| `docs/STEP-22-TRUST-BOUNDARY-MATRIX.md` | regular | 9718 | `ae1da485baa4bb5a5307dbf77ce01001bda4d1345722fffd16438cf84e39325c` | HASHED_STABLE |
| `docs/STEP-23A-GIT-ANOMALY-ADJUDICATION.md` | regular | 7568 | `2296e91389f2850abc238fff8d05b113251dd3796eda2d32c6570f028086c121` | HASHED_STABLE |
| `docs/STEP-23B-HISTORICAL-INDEX-CAPTURE-VALIDATION.md` | regular | 5908 | `b3b61071757a2382ee91bd8345558f95a9cc28dd5634424cdf30bf8adb43b398` | HASHED_STABLE |
| `docs/STEP-23C-ADJUDICACION-DOCUMENTAL-Y-BLOQUEOS-ABIERTOS.md` | regular | 19445 | `2a408d5baa0eaa6bb1d540d2c6c31e89f939a831c3ebdf83454f3032d9b6023c` | HASHED_STABLE |
| `docs/STEP-23C-BASELINE-ACTUAL-Y-PRESERVACION-DEL-ESTADO.md` | regular | 7619 | `73cdefd6b4ca6499dc034614f429c8e4afe5f98aecab7d8e7a18a05a45e8057f` | HASHED_STABLE |
| `docs/STEP-23C.1-ADJUDICACION-FINAL.md` | regular | 18163 | `c9559723cad7f169e96b36de6f4c52f85e13b889ebca1080268db958ac021081` | HASHED_STABLE |
| `docs/STEP-24-INVESTIGACION-DIRIGIDA-DE-BLOQUEOS.md` | regular | 58148 | `037c8da0af1e49bf9bf9bbe331b216e84bab100f22b5d5803e5e1c384568c3b3` | HASHED_STABLE |
| `docs/STEP-25-ADJUDICACION-Y-CAMINO-DE-RESOLUCION.md` | regular | 32628 | `9dbf5cc6d8fcaf29d3165ba91ee4c457ad7a078d46457f3964b5c744fa6018a1` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-06-FAILURE-ADJUDICATION.md` | regular | 16975 | `7d35abbc4c972c999dbbc49a1453ce04a22f0208a2e609b9e32b000e3e5ca599` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-07-MINIMAL-FIXES.md` | regular | 1342 | `478ac4991171586241cc89e9d742dde0fd361a541e3cc03f25332bcbb62897ae` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-08-STATIC-REVIEW.md` | regular | 9715 | `07106fbd67c3475b1755613f4566d2bb53449320c60352aed20c55b5beb09548` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-09-MINIMAL-CORRECTIONS.md` | regular | 8568 | `6cc49e43fcc67350a78eda253a3cfaca87b250f4174a4b304925b17f9d700c92` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-10-DIFF-ADJUDICATION.md` | regular | 21695 | `188bafade50f091c4310064331b80e244a177cf45f8bd2ae8cecc15021ec6853` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-11-WORKSPACE-GUEST-PATH.md` | regular | 7943 | `a47bebd3629bb445bb304d37df6c0ce90964e3ac4322c9ddb91c2a9d0bc1d07c` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-12-STATIC-REVIEW.md` | regular | 11689 | `12d74d3fcb1f48dd8ad956cb0ab66d305dd7479cae3bed2e9a8d359902a36981` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-13-STATIC-NESTED-WORKSPACE-ADJUDICATION.md` | regular | 19057 | `65fb9ccb74fc107656e2f7460551351befc6c9fb4f257578e3faddb644f6d90e` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-14-HARNESS-ISOLATION-CONTRACT-DESIGN.md` | regular | 20270 | `8dc7e5ffea73eb3b7e03e714d3525d717ceb6a4ccae4b14ae9615e9141d4d78f` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-15-ARCHITECTURE-COVERAGE-ADJUDICATION.md` | regular | 23965 | `31ac8a7948c5ce6f5ee761cdd4d1990ec654a9513fb046d331af5dd1679496ba` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-16-B1R-HOST-CONTROLLER-ADJUDICATION.md` | regular | 23319 | `63c23ecceb051103f4eca05da9da60248d5c5171dbe9195d0c52162a2c294cc9` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-17-DEDICATED-HARNESS-COVERAGE-DESIGN.md` | regular | 30918 | `da50d1ee8a81343fccb44f0f3ddda043d7568500c62d8f06997ff51550044c2f` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md` | regular | 32194 | `a0b5d39bdecec4b84f73f9f88485f17b39215ea934f1edd4748b4c1b10cc5c5e` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-19-EXTERNAL-TRUST-BOOTSTRAP.md` | regular | 25621 | `dabe858b98e308573771c8a08f35f0eaf28f14e9cf7ab1e7aa29a4b37cbf9cac` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-20-READ-ONLY-TRUST-DISCOVERY.md` | regular | 16932 | `4e672546f7cf7e8c86932841192574fb888266f06ad8920ea6828898986dfc7e` | HASHED_STABLE |
| `docs/TALOS-P1.2-STEP-21-TRUST-ARCHITECTURE-ADJUDICATION.md` | regular | 24162 | `002272f947185846bd5b567d4d8335ec48570767ce4bbf735af4564361c77441` | HASHED_STABLE |
| `docs/TALOS-P1_2-STEP-05-B06-EXECUTION.md` | regular | 11948 | `0296758ffd3fc1cd3365f915818e8ba35a16f2292f0eedf9cae724615c15bdd3` | HASHED_STABLE |
| `graphify-out/2026-10-08/.graphify_labels.json` | regular | 40200 | `14c1ab94617eb5bdbb53180e5f045ad1acaf826265c332d020992b8ece5bd3ad` | HASHED_STABLE |
| `graphify-out/2026-10-08/GRAPH_REPORT.md` | regular | 253154 | `18991216bd82a632dda31dfaf36ffb684b88d865d1a8cbfaf51efd260c09c7b0` | HASHED_STABLE |
| `graphify-out/2026-10-08/graph.json` | regular | 38442517 | `3292c5702af53f621b27924aba06d57f4406f15a2e39526c065ac6eaf92b5dc7` | HASHED_STABLE |
| `graphify-out/2026-10-08/manifest.json` | regular | 377088 | `be6c1eb6d1ab5ed3fe4c8bede3c17edc2f907f8ad03b491618dac56b025b8cf8` | HASHED_STABLE |
| `graphify-out/2026-10-09/.graphify_labels.json` | regular | 40010 | `81ee6db45a2299e87180a2b371580f887fceea40a1dade5c9ccab9c95991eb3e` | HASHED_STABLE |
| `graphify-out/2026-10-09/GRAPH_REPORT.md` | regular | 255067 | `d6bf146c1e37955faeb5ac87f42606a55dc395951b6bbd05b9993a9524a30265` | HASHED_STABLE |
| `graphify-out/2026-10-09/graph.json` | regular | 38577803 | `9f75e93283e5cbd91a49b0d6436e93b67c088f7b503b362beb4a4dcd63e88e9a` | HASHED_STABLE |
| `graphify-out/2026-10-09/manifest.json` | regular | 377683 | `ee8d376762e15f4dec38a66dcf461c97928b88b1bd5bae85cb2370dbb30444a2` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/052da470d736f6d6412fff898bf39373f6d3882722ad82865c9f6d68426bfc99.json` | regular | 23061 | `ade745fd98df6a2df57d7b3e052fb41362ed4e8df8dec4053f93a91187fa3329` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/0b29bfcf38de4bddf3bdbe459b9c51bbdb5479b5e8b3e2d5f4c8d11828deb92d.json` | regular | 164667 | `93227fdf3b38587c06c27b168f683f8f91761f19757c5f34d26300d8f8de36eb` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/161ec2016bcc6e180a8588582aebb38566ed6554b1789627088f8a065f183fd6.json` | regular | 69179 | `6be49e3dcb57f8c11760c25510612c4ab4c29fee678256cc056e699144c1aebc` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/161f445d834113b37309f39dec75541338c3531ef17d1b1252b610743f2683e0.json` | regular | 20749 | `f4cf8bcfb881fa5a2476eab76c8fd330d424b5b8d9d04385a68af6c9da958c02` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/1bd5a385347735487355666554120dd81a217af71dfdbc1ee8859075844e1c71.json` | regular | 144939 | `67197f80f26963263ba597862a116ba9693d5cd891666dc12941e11d27139f25` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/1e703f95546e6b296be7232ad160cb81914503d7166a570c68cbf8c2637100b9.json` | regular | 144159 | `b4a02f1b51234be5bf91f416f22146d8437e29aaa41df4eeadc055e40f89bc11` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/22100de07504215e4dc6d3e5ecbe9a5bf56cc219ad0178506efcb6d5d66b18d6.json` | regular | 64789 | `8db5f416b6d86ac35d3a5dbe46c19e07d25d0463034f7bd32a77c890aef1177e` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/2c3fb6e91b36a1bfee06c780b5abd411f633c584059e64e3ffbe853394ddd4a1.json` | regular | 48068 | `5b0e8dfee14afd8532e5009b9b9ee3d4f967b4445464a5b8966f5bcfdf966b5c` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/3351458db5192cce53546c88cd581e56788571ad0d9f58f125115ec76e2d3f89.json` | regular | 86808 | `0cddc2472b2af74bd1fa99891582912e3370eac2ba112ca3bdda62cc0d4294a4` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/34b2c7deebf79a4172ba037fab7b88d5955a427f2d0cc09ab7f708242ae7d480.json` | regular | 50459 | `66fbd1564dcc0e4e1d037c00a8b0c1cbb032f711b2bcf0b56b74da504f0a994a` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/37183887e424515bb5e1d8ed752edd0e4a0ffc97dda56c69f400344b6c8797c5.json` | regular | 38248 | `1532c7c173c1dc9d4d4bffd61cc044b13a74f532d5a317f895ecdaf4aabb951b` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/3b68d2bcc45cd5afe7bff326e50e6f887b055786d748443fd20fce1f44fe99f8.json` | regular | 41748 | `69a789ae3d1477ff87e3f977f120e4366b802a8f9de2601dd73dbb3a6d4c2fc5` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/583300e438a8056119bc76aa9fc380eb07bbec835e6b3163c8b558c5cb5898c6.json` | regular | 23501 | `14b622ef399d80e53a7bac4c90cc5f0bbf7f7b1a2b02ea229f152eb82a3d9285` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/58befaf8ffb4085d5a9e689864b4e4d80a584aa38e15a9760020fd3726186829.json` | regular | 42133 | `a5b52454e6888b05247a462a64bac4c3881eb6a6429b4b52ed3c6f8f80f35a30` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/5f271e101e522cdc691d9f4f369813032f8db75d8db1b061797c8ef464a48eb0.json` | regular | 4162 | `ea74d02472f44c7a83faea736d2cb282e2607377d0cc9f84f28ee00f34218207` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/65f0b2bede8feea2cfa89e32e7e3b08fd5bd091b15176f1b6eb3e98b7d20f719.json` | regular | 144604 | `068b343dffd78eb8bb869691e77f000fade4391a0a7356629868b0c071f10353` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/6f3feec24994ef2e8d64700e25f710a4e969e890a4e3dc41b427d6b32d966e60.json` | regular | 35680 | `ee67673904b7f317a672053ec003ee8643e86b82e918fa8af0298e1d06fde268` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/70432a4fe5f3c75ac1e25206fc0e9fbdd150a1aee8f02236a9165e4fc6618a42.json` | regular | 93927 | `a3d404fb5b5bcb2cdac8aee43699bca3cadeb80bdffd6f0d5a9125d758b599bd` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/7bae7ea9677d3c7c828a87ca1e2045fb7be19ea3863994084e21ac6669ca0738.json` | regular | 25487 | `c9368ac64561dae11ac27fb0da9cc90799a1876d362ae834faa8117fa58635f7` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/7e4da33c1006a2a75fc0ccf5600c33e2497542a44a2155015d920293a9bf280e.json` | regular | 144938 | `359362f73ca8d91a31b7e99acbd34221eabae661fbf970607c75bb282b54b7eb` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/86a13696b586bd3a8d359adab185432dfb508010f88b867523f2a2b522258ed5.json` | regular | 20749 | `f4cf8bcfb881fa5a2476eab76c8fd330d424b5b8d9d04385a68af6c9da958c02` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/8e2e09a744c83afebc0d876c32d5d9b781d6bda367026df7ab3c7757805f29cc.json` | regular | 34941 | `d1fab24318577e629f8e614eef50d2813d4b41674fb542d486f7b09d4f84f89f` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/90d1341c09bd8f56cd912fa071b7e99ed8fe9d548389b7c1b4404e6701a094db.json` | regular | 46074 | `9e3b084692e9035d180331c421ae0822a6b501c5bf9e998bceb82b71abc3ade0` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/94044187c1884af40fd783e7b1745c9324023ef68ef9c32dfb0fa9f2ebd9abee.json` | regular | 18697 | `e4a68d14cd4cca168137619b52a972ec111ac67e3b4d711f41f7626cebd268bb` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/96d91474db35a3e02b348217a561142e5ed73728d6d29e12f07408cd6e8df60c.json` | regular | 111471 | `4341067325947bdb974768a86f4506234c3190a8648c8b0486256ea74df46139` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/9cb49fc160bc33733657a9533dfd96d5eedf4e4e986196e6c7ad56caaef2db11.json` | regular | 49826 | `5bf3ce8059f7d06f99130f617f7f9ce77223a33538bff3219ee256263907e74f` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/a5fe60e6f1dfbba13b062dcc9445abbb1b4ab939248ba6c4b99e23342707ad13.json` | regular | 36823 | `3d9f4eec1bad04ba3ab671aa06fd5aae1134e3dec3cf9e0c9f67e0250f0f1a57` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/a847449137c0dac8835befd71b930e01c1176719e1da5c2715a2241304c652c4.json` | regular | 11440 | `ba2fb2d11f23a08298bb937e49ea7b9e3be1d446d02437c6c2655d9569d79ba8` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/ab96b48ec22fb24d8b2db75d5dc69b367d80f72158003533bf6c9a2d073024a0.json` | regular | 193785 | `d6d544480ba24430009d645ec10d7fa029c94b059e9c7da0be4bd00408369bcf` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/ad4b6de79640034751b4f4f353b44f90023e2583987c3f30aeb766ae45d44b63.json` | regular | 86807 | `d87611ce9f726022436d952fede6c4c05401b1c15dab9a58b1aafbeaf0cf0d17` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/b3ac07f7dc4fcce1d56ccfa0f8171ea03e936ee7949d7de91d450740cdedbddf.json` | regular | 164446 | `bb0bca741201379c1b03a29efb6fdbf51e6f1681fa8308cb0d3fc5caaa846ccb` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/b4e21849b6b6697b9687f724fa552c0deb376e7e970c0fc2c0e51cf4369da68d.json` | regular | 74 | `436b073b1a2c5e3a10ba314bda87a18b7fe7deedf14c79b99583a5b4457f9e52` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/bbba6be824f1a62d15ce0734c7a9a059c2b3f231a512a0c7758c9c543a85d548.json` | regular | 23191 | `ef8cdad49e30b634b68175bce7df50ccdce807d25eed376b8033f05c10a73c18` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/c22b7724e1445d473f04d64422d4e967c895502fa09b02c64c0a5fc6963eabd2.json` | regular | 72159 | `5ada5f9a07f4db7e96a5f965b2a5616dec765fbd3079c853b01ee6ffb08e2d8d` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/c2328b71b3133c4a941d6248ad81849894aa576cff92adeb23dba0b3244f25bd.json` | regular | 36823 | `d9aa7ab6bbac468cd4c92852761a29504760d478627baef22704a5de3f207ab6` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/c2ef170eb10c704a19f3d70a1bac61057149792ddfa7b1a3f21ae264e71c1fa2.json` | regular | 9255 | `0f2e75d6c8952d5469f0ca124277e13ba76061e67ad6ba88ecd461e89c137213` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/c669c1871edd0994814f3f008c12c13b23a591c842e1bfdd536ca0b2739818cb.json` | regular | 204434 | `c5ba2f34df17b4d07b01b67ba2094b24c34fc2bd8e0f89edc5c2093464491333` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/cf36b980f9d0e85f0202ef270c870b780e0193f2cb085a555a8f9e3ab0871cc4.json` | regular | 71267 | `85d05438b76e3c99947722e5211bbd1f108afa4ee1b06113e6aac306ba51bebc` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/d150b0759381f788a34393b4b50487a55f54c4562a6e4b7ff724262e8a0449ee.json` | regular | 14842 | `90e1318f36da2d01014fea191c4f5afe6fe32c3369a89627448c79a58c96b00b` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/d1e76f50ff675a462db84e8fe89b54f3dd9d1ded3e20e2d5506316b6626afae0.json` | regular | 23462 | `8bacae3089da39fdf2e8574fd9350d525b151108949c618ccebe20763ec9d5e7` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/d5871969764a3f2dd29ba475adad9f0dbf49c846549b894bb26d7353505fc138.json` | regular | 74 | `436b073b1a2c5e3a10ba314bda87a18b7fe7deedf14c79b99583a5b4457f9e52` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/df5f8d549fae20f4e09203c3f895521564a2d5f8e0c5832984a59d68afa50035.json` | regular | 46696 | `ce6d7c950b1e7ea7f7bcfe1ed3698a3bd9a53cd20d448f0916ac2773ed80893f` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/dffefd0c49adadea34ca7a152bdcc89b663cded7010daed8338471444b03e144.json` | regular | 144935 | `89e7288a0dd32016e335549cc71b7f3a86e74e2707012b458a25dfe6e2a048f9` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/e2f90d4a86f4ed9a037fd4c2adee5a95354fc3ab721f4cb96011138255277de9.json` | regular | 28746 | `6c0f84dad00f72bd2b9032099bb29ec2646dea292c6aa85e84c5d7022b7a8268` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/e4d25687a75f1dd8a955cbfbaeba89a1211b7b06dbd7f8612551b4916b1ec338.json` | regular | 79469 | `5d48397b0acb6572f86be7f37c41713dc5c7de41762dae10b7ad63a84d1f1e2e` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/e54baf9e4484d6e8ee82bab5eff8797c01e2be8a0524abae171726b60bdd3857.json` | regular | 18546 | `92273451573060425cb07707e5818e3d15a7c6d00dccdfdb8e4b67946ec280dc` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/f7c457e76f322207718bfc4399396790d14b45a3f6676d7bc7d15a6b167a5d61.json` | regular | 46696 | `e9413e006e6e3bf1bacf1ae09512c7f9d0a5e25b92027c97e2e8497ab4c3d9e7` | HASHED_STABLE |
| `graphify-out/cache/ast/v0.9.77-s5/fb9ee10d4d756453e5f2bdc47a4cd94f9c796f6847f63fba281183e77c74b65b.json` | regular | 144939 | `746618c83ecb54d3ec477b485c9b9f64c0a8b66a355e7c07107fcad43f23b671` | HASHED_STABLE |
| `scripts/capture_quiesced_test_sources.py` | regular | 8633 | `47a4e1e988ea4e7d1c351c840e55fdd09a610b57ab42d06e5e1c67cfba7ca761` | HASHED_STABLE |
| `scripts/quality_gate_isolation.py` | regular | 15663 | `e860623d1f02938dfbc32eac7aa143b6d82094a3a3a5865f0bc1aebf7ff62ed8` | HASHED_STABLE |
| `tests/unit/diagnostics/test_quality_gate_focal_execution.py` | regular | 33656 | `bfdfbdf89fd3460afeed99fd5e9d49340e705df49ee0aa87fd44e252fe86c7ac` | HASHED_STABLE |
| `tests/unit/diagnostics/test_quality_gate_isolation.py` | regular | 16176 | `81c2904a97b216f8ef03ba32d00a40b0e79cde1f3dbe19321e207765f49829f0` | HASHED_STABLE |

**Nota de fidelidad:** la tabla representa los 89 paths retornados por el inventario NUL-delimitado. Los hashes se registraron sin imprimir contenido. Cualquier error de lectura o cambio concurrente habría quedado como excepción; no se observó ninguno. La entrada de este expediente no forma parte de la instantánea inicial, pues se creó después de calcularla.

### 4.1 Exclusión normativa

Estos 89 objetos permanecen excluidos de D6: no son inventario aprobado, no forman la pareja `(nodeids, tree_digest)`, no quedan confiables por ser hasheados y no fueron añadidos a Git. Incorporarlos requiere revisión y aprobación separadas. El hash no confiere autoridad.

## 5. Especificación documental de Gate B

Gate B permanece `SPECIFICATION IN PROGRESS`. Esta sección define el contrato documental que falta cerrar; no es un contrato ejecutable ni una autorización.

### B.1 — Artefacto de política protegida

**Debe especificar:** ubicación y raíz de confianza fuera del checkout; propietario y permisos; esquema/campos obligatorios; versionado y mínimo aceptable; anti-rollback y su estado protegido; actualización, revocación y recuperación; identidad e integridad del bootstrap antes de imports del checkout; requisitos/versiones mínimas de Bubblewrap; cgroups v2 y límites efectivos; perfil seccomp aprobado; preflight; políticas de secretos, red, filesystem y mounts; y respuestas ante ausencia, corrupción, contradicción o imposibilidad de verificar.

**Aceptación:** un único artefacto autoritativo y una matriz de predicados, evidencia, autoridad y fallo; no se permite self-approval del agente. La ausencia o versión inferior bloquea.

### B.2 — Identidad y formato

Definir formato, generación y unicidad de `campaign_id`, `run_id`, `case_id`, `nodeid`, `repetition_index`, `attempt_id`, `worker_id` y `tree_digest`; indicar qué autoridad genera o suministra cada valor y qué campos son independientes del worker. Especificar relación retry→intento original y deduplicación.

**Aceptación:** esquema versionado, claves únicas, procedencia por campo y ejemplos válidos/ inválidos; no imponer formatos sin justificación.

### B.3 — Evidencia del observer

Especificar identidad de campaña/observación/worker/intento, tree digest, tiempos observables, proceso y resultado, preflight/controles, referencias de artefactos, integridad/autenticidad/orden, registros parciales/duplicados/ausentes/contradictorios y canal aislado. Separar evidencia autoritativa de informativa y no aceptar archivos del worker como prueba independiente de su propio comportamiento.

**Aceptación:** esquema y matriz de procedencia por campo, reglas de validación, dirección del flujo y controles verificables para impedir acceso (lectura, escritura, descubrimiento e indirecto) del worker al canal observer→verifier.

### B.4 — Semántica de estados y agregación

Definir sin ambigüedad `PASS`, `FAIL`, `BLOCKED`, `UNKNOWN`, `INVALID` y `NOT_EXECUTED`. Ausencia, excepción no capturada, contradicción o procedencia insuficiente nunca implican `PASS`. `BLOCKED` identifica una barrera que impide iniciar/continuar; `UNKNOWN` expresa insuficiencia de evidencia; `INVALID` incumplimiento del contrato por observación/evidencia; `NOT_EXECUTED` ausencia de ejecución; `FAIL` incumplimiento demostrado por evidencia válida; `PASS` evidencia suficiente, válida e independiente.

**Aceptación:** transiciones y agregación por observación, caso, repetición, campaña y gate; un intento fallido nunca se borra ni se sustituye por uno exitoso.

### B.5 — Predicados de preflight

Para cada requisito D1–D4, especificar ID estable, autoridad, predicado de aceptación, evidencia producida, observador, condición de fallo, estado ante falta de evidencia y consecuencia para iniciar campaña.

**Aceptación:** matriz completa y fail-closed. Imposibilidad de demostrar un control no equivale a satisfacción.

### B.6 — Inventario normativo y digest

Definir de modo reproducible qué rutas/tipos de archivo entran en el digest, exclusiones autorizables y autoridad que las aprueba, manejo de symlinks/archivos generados/cambios concurrentes, obtención autorizada de nodeids esperados, comparación exacta, invalidadores, versionado y preservación de la pareja `(nodeids, tree_digest)`.

**Aceptación:** proceso futuro revisable y autoridad de aprobación identificada. No ejecutar colección ni producir/aprobar ahora un inventario.

### B.7 — Repeticiones, fallos y reintentos

Definir independencia de las tres repeticiones, inicio/cierre de una observación, interrupciones/fallos ambientales, invalidez, autorización de retry, preservación de intentos y condiciones de bloqueo. El plan es 10×3 = 30, no evidencia de que esas observaciones existan. Un retry requiere nuevo `attempt_id`, motivo, vínculo y autorización explícita; no puede reemplazar el intento original ni alterar silenciosamente el total.

**Aceptación:** protocolo de campaña, tabla de estados y regla de cierre exacta.

### B.8 — Trazabilidad

Cada requisito debe mapear a decisión Gate A, componente responsable, evidencia exigida, criterio de aceptación, estado actual, gate de verificación y autorización requerida. Separar requisito documentado, implementación y eficacia demostrada.

**Aceptación:** matriz íntegra y revisable antes de considerar Gate B completo. Gate B solo cambia de estado después de completar y someter el contrato a revisión expresa del operador.

## 6. Matriz resumida de trazabilidad

| Decisión/requisito | Responsable de diseño | Evidencia futura requerida | Criterio de aceptación | Estado actual | Gate / autorización |
|---|---|---|---|---|---|
| D1 privilegios separados | Política/host protegido | Identidad efectiva, grupos, sudoers/NOPASSWD, permisos de política/bootstrap | Sin elevación ni autoaprobación; evidencia verificable | Documentado; `NOT EXECUTED` | B: contrato; validación futura requiere autorización específica |
| D2 raíz/política única | Policy owner y bootstrap independiente | Identidad, custodia, permisos, versión mínima, anti-rollback, historial de cambios | Una autoridad protegida; fail-closed ante estado inválido | Documentado; eficacia `UNKNOWN` | B: especificar; E/F requieren autorización separada |
| D3 amenaza y aislamiento | Policy owner / preflight | Predicados, seccomp, mounts/namespaces, cgroups y límites efectivos | Todo control requerido verificable antes de worker; de lo contrario no inicia | Threat model documentado; controles `NOT EXECUTED` | B contrato; cualquier provisión/ejecución requiere autorización futura |
| D4 evidencia independiente | Observer y verifier separados del worker | Control de canal, procedencia, integridad y prueba de accesos | Worker no lee, descubre ni cambia canal; verifier consume evidencia preservada | Diseño documentado; independencia `NOT EXECUTED` | B contrato; prueba dinámica no autorizada |
| D5 campaña e intentos | Controlador/observer/verifier | IDs, worker/env, tree digest, referencias, fallos y retries | 10 casos×3 repeticiones planeadas; unicidad y retries sin pérdida | Plan documental; ninguna campaña ejecutada | B contrato; B1-R no autorizada |
| D6 cobertura/digest | Policy owner + revisor de inventario | Pareja aprobada, colección/execution inventories, comparación exacta | Igualdad exacta bajo un mismo tree digest; no omisiones/extras/duplicados | Pareja no aprobada; candidatos excluidos | B contrato; colección y aprobación no autorizadas |

## 7. Riesgos y cuestiones abiertas

- **`NOT EXECUTED`:** identidad de privilegios, protección externa de política, anti-rollback, Bubblewrap, seccomp, cgroups, mounts, límites y ausencia de credenciales no se comprobaron operacionalmente.
- **`UNKNOWN`:** identidad del propietario/autoridad real de política, procedimiento efectivo de actualización/revocación, custodia del ancla, implementación de observer/verifier y evidencia autenticada de aislamiento.
- **`UNRESOLVED`:** los cambios históricos entre 87/88/89 untracked no se atribuyen ni reconstruyen por aritmética o nombres.
- **`NOT AUTHORIZED`:** implementación harness/bootstrap/worker/observer/verifier, setup de usuario/política, preflight operativo, colección, tests, B1-R y cambios de perímetro.
- **Riesgo residual aprobado para diseño:** la explotación del kernel está fuera del threat model inicial; incluirla exige re-adjudicar arquitectura antes de permitir ejecución.

No se afirma que separación de privilegios, aislamiento, anti-rollback, seccomp o independencia del observer/verifier funcionen.

## 8. Operaciones realizadas y no realizadas

**Realizadas (`OBSERVED`):** lectura de identidad/estado Git; inventario NUL de untracked; hash SHA-256 local de archivos regulares con controles de estabilidad/no-follow; creación y lectura estática de este único expediente; cotejo de estado Git final.

**No realizadas (`NOT_EXECUTED`):** tests o `pytest`/`--collect-only`; scripts del proyecto; workers; Bubblewrap; `unshare`; imports/backend/application/lifespan/container; builds, benchmarks, hooks o validaciones dinámicas; instalación o cambio de configuración; operaciones Git mutantes; inspección del contenido de archivos candidatos; acceso o escritura a bases de datos, corpus, snapshots o estado de aprendizaje.

## 9. Condiciones de salida y estado final

### Gate A

**`GATE A — CERRADO DOCUMENTALMENTE`**, limitado a la aprobación documental de las decisiones D1–D6 para el diseño. La Rama A, límites de root/OS, política única D2–D3 y preflight, vínculo D5/D6 con `tree_digest`, prohibición de acceso worker al canal observer→verifier, inventario de candidatos con hashes y exclusión normativa, y entregables/criterios de Gate B están registrados. Este estado no significa “implementado”, “efectivo”, “aislamiento demostrado” ni “autorizado para ejecutar”.

### Gate B

**`SPECIFICATION IN PROGRESS`**. Falta producir el contrato completo, resolver los formatos/autoridades/predicados indicados en B.1–B.8 y obtener revisión expresa del operador.

### Estado canónico preservado

- `P1.2 = BLOCKED-REGRESSION`
- `P1.3 = BLOCKED`
- `B1-R = NOT AUTHORIZED`
- Harness externo = `NOT AUTHORIZED`
- TALOS V1 permanece congelado.
- Playwright permanece limitado a regresión congelada.
- Qwen permanece bloqueado.
- Bases de datos, corpus, snapshots y estado de aprendizaje de producción permanecen protegidos.

Este expediente no autoriza implementación, instalación, preflight operativo, colección, workers, campañas B1-R, cambios al inventario normativo, alteraciones de TALOS V1 ni acceso a datos de producción. Cualquier actividad posterior requiere una directiva y autorización explícitas separadas.
