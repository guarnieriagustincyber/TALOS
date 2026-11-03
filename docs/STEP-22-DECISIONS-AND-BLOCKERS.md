# STEP-22 — Decisions and blockers

**Entrada:** `TRUST_ARCHITECTURE_SELECTED_UNIMPLEMENTED`  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`  
**Resultado:** `BLOCKED_WITH_EXPLICIT_FINDINGS`

Este registro distingue decisiones documentales de STEP-21, propuestas de STEP-22, evidencia observada y autorizaciones pendientes. No es una aprobación de implementación.

## 1. Estado e identidad

Al inicio: rama `talos-current-audit`, HEAD `cc8acfae623f9d10c8366871470319786b6a7ca4`; Git reportó 1.869 staged, 23 unstaged y 72 untracked. Los conteos no prueban autoría.

Los cuatro destinos STEP-22 no existían al inicio. Tras crearlos, rama y HEAD permanecen iguales; Git reporta 1.869 staged, 23 unstaged y 76 untracked. El único conjunto nuevo de estado de esta fase son estos cuatro paths untracked; staged/unstaged permanecen con sus conteos iniciales. Se preservaron cambios preexistentes y no se atribuye su autoría.

## 2. Fuentes y límites

Fuentes documentales:

- [STEP-18 host authority and ownership](./TALOS-P1.2-STEP-18-HOST-AUTHORITY-COVERAGE-OWNERSHIP.md).
- [STEP-19 external trust bootstrap](./TALOS-P1.2-STEP-19-EXTERNAL-TRUST-BOOTSTRAP.md).
- [STEP-20 read-only trust discovery](./TALOS-P1.2-STEP-20-READ-ONLY-TRUST-DISCOVERY.md).
- [STEP-21 trust architecture adjudication](./TALOS-P1.2-STEP-21-TRUST-ARCHITECTURE-ADJUDICATION.md).
- Existing static facts cited there from `scripts/test.sh`, `scripts/quality_gate.py`, `scripts/quality_gate_isolation.py`, `src/study_engine/contracts/trust_root.py`, `config/test_perimeter.json`, `tests/audit/b1r_contract.json`, `docs/TEST_CERTIFICATION_PERIMETER.md`, and `docs/A_PRE_0_BASELINE_SPEC.md`.

STEP-22 did not repeat environment discovery or run dynamic inspection. No source facts beyond the cited evidence are asserted. No tests, project scripts, Python imports, benchmark, gate, worker, Bubblewrap probe, protected data access or snapshot operation was performed.

## 3. Decisiones adoptadas y propuestas

| ID | Tipo | Decisión/propuesta | Estado |
|---|---|---|---|
| D-01 | STEP-21 decision | Arquitectura A: controller externo con identidad aprobada; bootstrap externo forma parte necesaria del diseño. | Seleccionada como dirección, no implementada. |
| D-02 | STEP-21 decision | Checkout y tests son inputs no confiables para la autoridad host; no se ejecuta código arbitrario de tests en host como conveniencia. | Adoptada como restricción contractual. |
| D-03 | STEP-22 proposal | Solo controller autorizado observa Git host-side, crea workspace, lanza worker, recolecta y agrega. | Especificada, sin evidencia runtime. |
| D-04 | STEP-22 proposal | Worker no tiene API genérica de comandos/mounts, no ve `.git` real/roots protegidas por default y no se autoriza a sí mismo. | Especificada; policy exacta no aprobada. |
| D-05 | STEP-22 proposal | Resultados versionados separan función, artefactos, aislamiento, Git, coverage y agregado; todos enlazados por `run_id`. | Especificada en anexo principal/matrices; no implementada. |
| D-06 | STEP-22 proposal | Once nodeids conservan owner estándar y clasificación `required`; B1-R mantiene 30 observaciones internas. | Obligación contractual preservada; no ejecución ni cambio de perímetro. |
| D-07 | STEP-22 outcome | `BLOCKED_WITH_EXPLICIT_FINDINGS` porque falta autoridad aprobadora/trust anchor/bootstrap y policy externa específica. | Resultado seleccionado. |

## 4. Blockers que requieren resolución externa

| ID | Bloqueo concreto | Responsable que debe designarse | Evidencia/decisión necesaria antes de implementación |
|---|---|---|---|
| B-01 | No se identificó quién puede aprobar, expirar y revocar una versión de controller. | Gobernanza/propietario normativo de TALOS, identidad aún desconocida. | Designación formal de autoridad, ámbito, proceso de aprobación y registro externo. |
| B-02 | No existe en evidencia STEP-18–20 trust anchor/bootstrap identificado fuera del checkout. | Autoridad aprobadora + propietario del entorno de ejecución, aún desconocidos. | Elegir canal/raíz/verificador; demostrar que no puede ser sustituido por checkout y verifica antes de código no confinado. |
| B-03 | Identidad del controller, runtime, imports, dependencias y herramientas pre-worker no está aprobada como conjunto transitivo. | Propietario técnico del harness y autoridad aprobadora. | Inventory reproducible, identidad/version exacta y decisión aprobada sobre supply chain/procedencia. |
| B-04 | Mecanismo check-to-use/anti-TOCTOU no definido. | Propietario técnico del bootstrap. | Procedimiento verificable que utilice los mismos bytes aprobados, con manejo de sustitución y rollback. |
| B-05 | Política de perfil, nodeids, mounts, roots protegidas, workspace, capacidades, límites de recursos y allowlists requiere aprobación externa. | Propietario de política de aislamiento/gate y autoridad aprobadora. | Policy identity/version, scope y cambios aprobados; sin posibilidad de ampliar desde checkout. |
| B-06 | Firma/autenticación, expiración, nonce/replay, revocación y operación offline no elegidos. | Autoridad aprobadora y custodio de trust anchor. | Perfil de autorización y lifecycle explícitos; no inventar clave o CA en implementación. |
| B-07 | No hay contrato/implementación para importar evidencia externa compuesta al agregador actual. | Propietario del Quality Gate y autoridad del perímetro. | Schema, exactly-once ownership, expected inventory y reglas de contradicción; autorización explícita para cambios futuros. |
| B-08 | Verificador de artefactos, observador de aislamiento y agregador no tienen identidades independientes aprobadas. | Autoridad aprobadora y propietarios funcionales por componente. | Identidades, scopes y consumer evaluations separadas. |
| B-09 | B1-R necesita Git host-side, worker realmente confinado, artifact/verifier y aislamiento separado; el test actual no acredita esa composición. | Propietario de B1-R, controller owner, test perimeter owner. | Refactor/diseño futuro explícitamente autorizado preservando assertions y 30 observaciones; evidencia de no exposición de `.git`. |
| B-10 | Los límites exactos de recursos/envelope y manejo de retries no tienen política aprobada. | Propietario técnico y autoridad del gate. | Valores/versiones allowlisted; reglas que nunca oculten fallo previo o permitan output ilimitado. |
| B-11 | No se validó empíricamente autorización, integridad del runtime, Bubblewrap, boundary, artefactos o recolección. | Autoridad de ejecución futura y verificadores respectivos. | Etapa de validación autorizada separada con evidencias y límites; no usar disponibilidad del binario como prueba. |

La identidad de los responsables no se rellena con nombres supuestos. STEP-22 no tiene jurisdicción para nombrarlos ni concederles autoridad.

## 5. Criterios de aceptación STEP-22

| Criterio | Estado | Evidencia/razón |
|---|---|---|
| Roles y límites de confianza | `SPECIFIED — PROPOSAL` | Contrato principal §2/§5 y trust matrix. No validados en ejecución. |
| Autoridad aprobadora o bloqueo concreto | `BLOCKED — AUTHORITY UNDESIGNATED` | Se identifica el rol requerido, pero no una identidad autorizada; B-01. |
| Controller identity y ancla independiente | `BLOCKED — NOT FOUND/SELECTED` | Requisitos definidos; evidencia STEP-18–20 no encontró mecanismo desplegado; B-02/B-03. |
| Bootstrap y dependencias pre-worker | `SPECIFIED — PROPOSAL; NOT VERIFIED` | Contrato principal §3–4; no existe mecanismo probado. |
| TOCTOU/config change | `SPECIFIED — REQUIREMENT; DESIGN PENDING` | Se exige vínculo check-to-use, pero implementación/estrategia técnica aprobada no existe; B-04. |
| Interfaz worker versionada | `SPECIFIED — PROPOSAL` | Envelope/capabilities y rejection rules en contrato principal §5; aún sin schema implementado ni policy limits aprobados. |
| Mounts/capacidades/fail-closed | `SPECIFIED — PROPOSAL; NOT VERIFIED` | Restricciones declaradas; boundary actual no validado y policy final pendiente. |
| Result schema y validación strict | `SPECIFIED — PROPOSAL` | Contrato principal §6; máximos presentados como propuesta para aprobación, no como norma vigente. |
| Verificación independiente de artefactos | `BLOCKED — VERIFIER IDENTITY PENDING` | Consumer/producer separation definida; identidad y ejecución independiente no demostradas. |
| Git pre/post y limitaciones | `SPECIFIED — CONTRACT` | Same checkout/command/run; error bloquea; equality no demuestra ausencia de escrituras transitorias. |
| Once nodeids e `required` | `SPECIFIED — PRESERVED` | Matrices enumeran exactamente once; no se modifica config/owner; futura ingesta no implementada. |
| B1-R 30 observaciones | `SPECIFIED — CONTRACT; NOT EXECUTED` | 10×3, con Git/artifact/isolation separados; evidencia dinámica ausente. |
| Agregación/rejection matrix | `SPECIFIED — PROPOSAL` | Anexo define absent/duplicate/invalid/contradictory/error paths y no-PASS. |
| State machine | `SPECIFIED — PROPOSAL` | Contrato principal §9; no implementada. |
| Casos de rechazo | `SPECIFIED — PROPOSAL` | Rejection matrix cubre autorización, identidad, cobertura, artefactos, aislamiento, Git y errores. |
| Blockers humanos/externos | `SPECIFIED — EXPLICIT` | B-01..B-11 con roles responsables aún por designar. |
| Plan futuro separado | `SPECIFIED — NOT AUTHORIZED` | Contrato principal §10 y blocker register. |
| No ejecución/no cambio ejecutable o perímetro | `SATISFIED FOR STEP-22` | Solo cuatro documentos nuevos; estado Git verificado; no se ejecutaron scripts/tests ni se tocó configuración/código. |

**Cierre por criterio:** los contratos de datos y rechazo están descritos, pero los criterios críticos de autoridad, ancla y bootstrap no pueden tener estado aceptado sin evidencia/decisión externa. Por ello no se declara `EXTERNAL_HARNESS_CONTRACT_SPECIFIED`.

## 6. Secuencia requerida para reabrir

Sin conceder autorización de antemano:

1. Resolver B-01/B-02: autoridad y trust anchor/bootstrap.
2. Aprobar controller/runtime/dependencies, policy scope, revocación y check-to-use (B-03..B-06).
3. Aprobar schema, coverage owner y evaluadores/verifier (B-07/B-08/B-10).
4. Autorizar diseño/implementación posterior con alcance acotado, preservando las once obligaciones y sin ejecución automática.
5. Autorizar por separado pruebas del bootstrap y fallos cerrados.
6. Autorizar por separado pruebas de boundary Bubblewrap y evidencia real de aislamiento.
7. Autorizar prueba compuesta de B1-R (30 observaciones) con Git host-side y verifier identificados.
8. Adjudicar cobertura exacta de ambos perfiles y resultados; resolver contradicciones/unknowns.
9. Solo una decisión posterior puede reabrir P1.2; esta etapa no efectúa esa transición.

## 7. Cierre de actividad

- Archivos nuevos: [contrato principal](./STEP-22-EXTERNAL-HARNESS-EXECUTION-CONTRACT.md), [trust boundary matrix](./STEP-22-TRUST-BOUNDARY-MATRIX.md), [aggregation/rejection matrix](./STEP-22-AGGREGATION-AND-REJECTION-MATRIX.md), este [registro de decisiones y bloqueos](./STEP-22-DECISIONS-AND-BLOCKERS.md).
- No se modificaron documentos previos, código ejecutable, tests, configuración, trust roots ni perímetro.
- No se ejecutaron `pytest`, nodeids, Quality Gate, benchmarks, scripts del proyecto, imports Python, workers ni pruebas de aislamiento.
- No se accedió a bases/corpus protegidos ni se crearon snapshots/workspaces auxiliares.
- Git inicial: 1.869 staged, 23 unstaged, 72 untracked. Git final: 1.869 staged, 23 unstaged, 76 untracked. Rama/HEAD sin cambio. Los cuatro nuevos untracked son los deliverables; el resto preexistía según el estado inicial; conteos no demuestran autoría.
- No se atribuyen cambios preexistentes a esta etapa.

**Resultado final:** `BLOCKED_WITH_EXPLICIT_FINDINGS`.  
**Estado canónico:** `P1.2 = BLOCKED-REGRESSION`.
