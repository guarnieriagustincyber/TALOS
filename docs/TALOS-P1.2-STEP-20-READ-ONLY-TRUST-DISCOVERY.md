# TALOS P1.2 — STEP-20: read-only environment trust discovery

**Entrada:** `EXTERNAL_TRUST_DESIGN_PARTIAL`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Tipo:** inspección de entorno, solo lectura  
**Resultado:** `EXTERNAL_TRUST_DESIGN_PARTIAL`

## 1. Identidad y estado del repositorio

Observado al inicio:

- Ruta canónica del repositorio: `/media/agustin/Laboratorio/study-engie`.
- Rama: `talos-current-audit`.
- HEAD: `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Contexto de usuario mínimo observado: UID/GID `1000:1000`; `$HOME=/home/agustin`.
- `git status --porcelain=v1` resumido: 1.869 paths staged, 23 unstaged y 70 untracked. Los conteos no prueban autoría.
- STEP-18 y STEP-19 estaban presentes; el expediente STEP-20 no existía.

Las identidades son observaciones de esta fase; las registradas previamente en STEP-19 no se trataron como actuales ni como autorización.

Comprobación final, después de crear este expediente:

- Rama y HEAD sin cambios: `talos-current-audit`, `cc8acfae623f9d10c8366871470319786b6a7ca4`.
- Git reportó 1.869 paths staged, 23 unstaged y 71 untracked. El único estado correspondiente a esta fase es `?? docs/TALOS-P1.2-STEP-20-READ-ONLY-TRUST-DISCOVERY.md`; staged y unstaged conservaron sus conteos iniciales.
- Los conteos describen paths, no autoría. No se revirtieron ni atribuyeron cambios preexistentes.

## 2. Alcance y procedimiento de inspección

Se limitaron las consultas a:

- Resolución de comandos mediante `command -v` y el `PATH` de esta sesión; no se volcó el entorno completo.
- Metadatos de rutas y directorios mediante `stat`, `readlink`, consultas de existencia y `dpkg-query` sobre la base local de paquetes.
- Búsqueda de nombres, con profundidad máxima de un nivel y patrones dirigidos a TALOS, Quality Gate, A-PRE, Bubblewrap, aislamiento, trust y autorización.
- Lectura estática de `scripts/test.sh`, partes pertinentes de `scripts/quality_gate.py` y `scripts/quality_gate_isolation.py`, `trust_root.py`, perímetro y expedientes STEP-18/19.

Directorios de búsqueda de nombres externos: `$HOME/.local/bin`, `$HOME/.opencode/bin`, `$HOME/.cargo/bin`, `/usr/local/bin`, `/usr/local/sbin`, `/usr/bin`, `/usr/sbin`, `/usr/games`, `/usr/local/games`, `/snap/bin`, el directorio de ripgrep incluido en VS Code, `/usr/local/libexec`, `/usr/libexec`, `/usr/lib/talos`, `/opt` (solo entradas de primer nivel), `/opt/talos`, `/etc/talos`, `/etc/opt/talos`, `/usr/local/etc/talos`, `$HOME/.config/talos`, `$HOME/.local/share/talos` y `$HOME/.config/systemd/user`.

No se recorrió el disco, el home completo, árboles de dependencias, cachés ni historiales. No se inspeccionaron servicios de CI/supervisión: no se encontró evidencia concreta de que participen en el flujo local actual. Los directorios de autorización TALOS consultados que no existían se registran como ausentes en este entorno en este momento, no como prueba de inexistencia universal.

## 3. Candidatos y metadatos observados

### 3.1. Herramientas resueltas

| Comando | Resolución/metadatos observados | Procedencia local observable | Evaluación de autoridad |
|---|---|---|---|
| `python3` | `/usr/bin/python3` → `/usr/bin/python3.12`; archivo destino `root:root`, modo `755`; `/usr/bin` `root:root`, modo `755`. | `dpkg-query`: `python3-minimal 3.12.3-0ubuntu2.1`. | Intérprete de sistema identificado por ruta y paquete, pero no se verificó la integridad de sus bytes ni existe evidencia de aprobación para el supervisor TALOS. |
| `python` | No resuelto en el `PATH` observado. | No aplicable. | No constituye bootstrap externo. |
| `git` | `/usr/bin/git`, archivo `root:root`, modo `755`; `/usr/bin` modo `755`. | `dpkg-query`: `git 1:2.43.0-1ubuntu7.3`. | Permite observación Git del host; no se encontró controlador autorizado que la vincule al resultado del gate. |
| `bwrap` | `/usr/bin/bwrap`, archivo `root:root`, modo `755`; `/usr/bin` modo `755`. | `dpkg-query`: `bubblewrap 0.9.0-1ubuntu0.3`. | Capacidad OS instalada, no un harness ni una política externa de mounts/perfiles. No se ejecutó ni se verificó su comportamiento. |
| `bubblewrap` | Nombre no resuelto; el comando disponible es `bwrap`. | Paquete `bubblewrap` indicado arriba. | El nombre alternativo no aporta otra autoridad. |
| `openssl` | `/usr/bin/openssl`, `root:root`, modo `755`. | `dpkg-query`: `openssl 3.0.13-0ubuntu3.16`. | Herramienta criptográfica genérica; no se encontró manifiesto/autorización TALOS asociado ni se ejecutó. |
| `gpg` | `/usr/bin/gpg`, `root:root`, modo `755`. | `dpkg-query`: `gpg 2.4.4-2ubuntu17.6`. | Herramienta genérica; no se encontró clave/verificador de autorización TALOS ni se ejecutó. |
| `ssh-keygen` | `/usr/bin/ssh-keygen`, `root:root`, modo `755`. | `dpkg-query`: `openssh-client 1:9.6p1-3ubuntu13.19`. | Herramienta genérica; no demuestra una firma de release aprobada ni se ejecutó. |
| `trust` | `/usr/bin/trust`, `root:root`, modo `755`. | `dpkg-query`: `p11-kit`. | Utilidad genérica de trust store; no se encontró configuración que la vincule a la autorización del supervisor. No se ejecutó. |
| `cosign`, `age`, `minisign` | No resueltos en el `PATH` observado. | No aplicable. | La ausencia en la resolución consultada no demuestra inexistencia en todo el sistema. |

Los archivos de sistema enumerados son de propietario/grupo `root:root` y los directorios consultados `/usr` y `/usr/bin` son `root:root`, modo `755`. Las consultas de paquete prueban una relación con la base local de paquetes, no la autenticidad del repositorio de paquetes, integridad actual del archivo, control de la cuenta root ni una aprobación normativa TALOS.

### 3.2. Intérprete seleccionado por el wrapper del checkout

La lectura estática de [`scripts/test.sh`](../scripts/test.sh) confirma que el wrapper elige primero `$REPOSITORY_ROOT/.venv/bin/python` si es ejecutable y solo recurre a `python3` mediante `PATH` cuando esa ruta no está disponible (`scripts/test.sh:4-16`). En el checkout observado:

- `.venv`, `.venv/bin` son directorios `agustin:agustin`, modo `775`.
- `.venv/bin/python` es un symlink `agustin:agustin` que resuelve a `/usr/bin/python3.12`.
- No se ejecutó el intérprete ni se inspeccionaron/importaron sus módulos.

Aunque el destino observado es un intérprete de sistema, el path prioritario y sus directorios padre dentro del checkout son sustituibles por el propietario actual. Por lo tanto, el mecanismo de selección no fija por sí solo identidad confiable del ejecutable ni de los módulos que el supervisor importa antes de Bubblewrap. Esto describe la configuración observada; no afirma que se haya iniciado el gate.

### 3.3. Búsqueda dirigida de wrappers y configuración externa

No se encontraron nombres de wrappers específicos de TALOS, Quality Gate, A-PRE o aislamiento en los directorios de binarios consultados. La única coincidencia de nombre genérico relacionada con trust fue `/usr/bin/trust`, clasificada arriba como utilidad del paquete `p11-kit`, no como autorización del supervisor.

No existían `/opt/talos`, `/etc/talos`, `/etc/opt/talos`, `/usr/local/etc/talos`, `$HOME/.config/talos`, `$HOME/.local/share/talos` ni `$HOME/.config/systemd/user`. No se identificó en el alcance consultado un manifiesto de autorización, clave pública de TALOS, configuración de release firmada, registro de aprobación o política de actualización/revocación. No se leyeron claves privadas ni se consultaron almacenes de claves personales. No se hizo búsqueda general de todos los certificados del sistema: una CA genérica sin vínculo de procedencia/política tampoco probaría autorización para el runner.

Estos resultados significan **no encontrado en el alcance inspeccionado**. No demuestran que no exista un servicio remoto, configuración en otra ruta, control administrativo externo o mecanismo fuera de este host.

### 3.4. Distinción de clases de evidencia

- **Instalado y observado:** herramientas de sistema y sus rutas/propietarios/modos; relación con paquetes del sistema observada en la base local de paquetes.
- **Documentado como diseño, no encontrado instalado:** el wrapper externo de A-PRE descrito en [`A_PRE_0_BASELINE_SPEC.md`](A_PRE_0_BASELINE_SPEC.md) (`:406-475`) carece allí de ruta, owner, identidad/versionado y autorización concreta. No se encontró en las rutas inspeccionadas.
- **Dentro del checkout:** `quality_gate.py`, `quality_gate_isolation.py`, `apre_harness.py`, `verify_apre_result.py` y `trust_root.py`; sus hashes, checks y contratos no se vuelven independientes del checkout por estar implementados o descritos allí.
- **No hallado como mecanismo desplegado:** bootstrap que autorice al supervisor antes de importarlo, firma/clave ancla TALOS externa, vínculo de política a mounts y perfiles, revocación, ni agregador externo autorizado.

## 4. Matriz de confianza del candidato externo

El candidato más relevante encontrado es la capacidad de Bubblewrap del sistema (`/usr/bin/bwrap`). Los programas criptográficos también están instalados como utilidades genéricas, pero no se encontró que participen en un bootstrap de autorización TALOS. La matriz evalúa la evidencia del mecanismo pertinente, no una política hipotética:

| Propiedad | Evidencia/resultado |
|---|---|
| **Independencia** | `PARCIAL` — `bwrap` y otras utilidades están fuera del checkout, con propietario `root` y directorios de sistema no escribibles por el usuario observado. No se verificó control de root/paquetes ni hay vínculo de autorización TALOS. |
| **Identidad** | `PARCIAL` — rutas canónicas, metadatos y paquete/versiones locales identificados; bytes del ejecutable, build y dependencias transitivas no verificados criptográficamente. |
| **Procedencia** | `PARCIAL` — la base local los atribuye a paquetes del sistema. No se validó el origen del repositorio, firma del paquete ni cadena de custodia. |
| **Autorización previa** | `NO ENCONTRADO EN EL ALCANCE` — no se observó un verificador externo que bloquee la ejecución del supervisor hasta aprobar su identidad. |
| **Integridad** | `PENDIENTE DE VALIDACIÓN` — no se verificó el contenido del paquete/binarios ni se ejecutó verificación de integridad. |
| **TOCTOU** | `PENDIENTE DE VALIDACIÓN` — no hay contrato observado que vincule la aprobación previa a los mismos bytes ejecutados y evite sustitución entre comprobación y uso. |
| **Alcance** | `NO ENCONTRADO EN EL ALCANCE` — no se encontró autorización externa que limite perfiles, nodeids, mounts, roots protegidas, workspace o recolección. |
| **Revocación** | `NO ENCONTRADO EN EL ALCANCE` — sin registro/autorización TALOS identificados, no hay evidencia de revocación o expiración. |
| **Actualización** | `PARCIAL` — existe instalación administrada por paquetes según la base local; no se encontró procedimiento que apruebe externamente una nueva versión del supervisor/runtime TALOS ni política anti-downgrade. |
| **Fallo cerrado** | `PENDIENTE DE VALIDACIÓN` — el código del checkout describe fail-closed para ausencia de `bwrap`, pero no se probó y no equivale a fail-closed ante autorización externa ausente/inválida/vencida. |
| **Auditoría** | `PARCIAL` — se observaron versiones de paquete y estado Git; no un registro externo de aprobador, decisión, vigencia, identidad autorizada y resultado. |

No hay base para calificar el candidato como mecanismo de confianza suficiente. La presencia de Bubblewrap ofrece una capacidad potencial de aislamiento, no una autorización del controlador ni evidencia dinámica de la frontera efectiva.

## 5. Elementos pendientes de validación

Quedaron sin comprobar, deliberadamente, todas las propiedades que requieren ejecutar un candidato o cambiar/consultar estado más allá de esta inspección:

- Integridad de los bytes de Python, Git, Bubblewrap y utilidades criptográficas; firma/procedencia de paquetes y cadena de suministro.
- Comportamiento efectivo de `bwrap`, namespaces, mounts, red, enmascaramiento y política del worker.
- Propietario/control administrativo real de la autoridad root y seguridad operacional de actualización.
- Procedencia de módulos/dependencias Python host y si son los bytes autorizados al importar.
- Existencia de configuración remota/de CI no conectada documentalmente al flujo local, almacenes de claves no consultados o servicios externos.
- Existencia/validez de aprobaciones manuales, firma, expiración, rotación o revocación.
- Verificación de una firma, ejecución de wrappers/verificadores candidatos, hashing integral de artefactos como decisión de autorización o test de TOCTOU.

Los permisos observados describen el estado actual de rutas, no prueban ausencia de sustitución en todo momento. No se consultaron valores de variables sensibles ni contenidos de credenciales/keys.

## 6. Impacto sobre supervisor, B1-R y cobertura

La arquitectura estática del checkout mantiene `quality_gate.py` como supervisor host; importa código/configuración del checkout, prepara el workspace y después llama al launcher Bubblewrap (`quality_gate.py:1218-1245,1473-1605`; `quality_gate_isolation.py:213-307`). La herramienta `/usr/bin/bwrap` encontrada no sustituye una autorización externa del supervisor ni autoriza las opciones de mount que le pasa el código del checkout.

No se encontró un componente externo identificado que pueda asumir de manera verificable los siete deberes de B1-R: Git inicial host, autorización/lanzamiento del worker confinado, 30 observaciones funcionales, recolección/verificación del artefacto, evidencia de aislamiento, Git final host y agregación compuesta. `git` y el verifier del checkout existen como piezas, pero falta un controller/owner autorizado que las vincule por identidad y run-id. La igualdad del `git status --porcelain --untracked-files=all` pre/post sigue significando solo igualdad de estados reportados; no demuestra ausencia de escrituras transitorias. Un `TECHNICAL PASS` tampoco autentica al productor ni prueba aislamiento.

Las once obligaciones identificadas en STEP-18 permanecen bajo propiedad estándar `required` en suites `tests/unit` y `tests/audit`; no se modificó perímetro, clasificación ni owner. No se registran como ejecutadas en esta fase:

1. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_maps_host_path_to_mounted_workspace`
2. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_workspace_guest_path_rejects_paths_outside_workspace`
3. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_bubblewrap_denies_protected_paths_and_allows_derived_workspace`
4. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolation_fails_closed_when_bubblewrap_is_unavailable`
5. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_isolated_process_exit_code_is_preserved`
6. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_active_virtual_environment_is_available_read_only_in_sandbox`
7. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_synthetic_pytest_runs_inside_the_process_boundary`
8. `tests/unit/diagnostics/test_quality_gate_isolation.py::test_snapshot_contract_tests_run_without_git_or_production_mounts`
9. `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_focal_binding_is_validated_inside_bubblewrap`
10. `tests/unit/diagnostics/test_quality_gate_focal_execution.py::test_isolated_focal_runner_propagates_binding_and_writes_receipt`
11. `tests/audit/test_b1_route_repeatability.py::test_synthetic_chat_route_is_repeatable_and_sterile`

Se conserva la distinción STEP-18: los tests con fakes prueban orquestación simulada, no una frontera Bubblewrap real; un proceso hijo es subresultado y no satisface por sí solo el nodeid padre. Los `qualification-required` no se usan para descargar estas obligaciones `required`.

## 7. Resultado y cierre

**Resultado STEP-20:** `EXTERNAL_TRUST_DESIGN_PARTIAL`.

Se identificaron capacidades de sistema instaladas y metadatos observables, pero no una autorización externa desplegada que ate autoridad, identidad aprobada y bytes ejecutados del supervisor host. La búsqueda de wrappers/configuración fue dirigida y acotada; “no encontrado” se limita a las rutas/nombres inspeccionados. No se selecciona T1/T2/T3 ni se adopta T4.

No se ejecutaron scripts del proyecto, intérpretes Python, tests, Quality Gate, benchmarks, wrappers, verificadores, binarios candidatos ni verificaciones funcionales/criptográficas. No se leyeron claves privadas ni secretos; no se accedió a datos protegidos. No se cambiaron permisos, propietarios, configuración, servicios ni instalaciones. Solo se creó este expediente; los cambios preexistentes se preservaron.

**Estado obligatorio:** `P1.2 = BLOCKED-REGRESSION`. STEP-20 no autoriza implementación, pruebas, cierre de P1.2 ni transición a P1.3.
