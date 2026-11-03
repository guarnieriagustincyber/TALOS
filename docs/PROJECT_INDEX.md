# PROJECT INDEX — TALOS V1.5 (entrada documental principal)

**Revisión documental:** 2026-10-23 · **Rama verificada:** `checkpoint/talos-v15-20261014` · **HEAD observado:** `fc0411d7392bdc5cf246436e9f7f5b65392426db`.
El working tree contiene cambios locales; este dato no acredita un respaldo. Las secciones
1–7 conservan el contexto registrado el 2026-10-20 sobre `603a097`, no una validación del HEAD actual.

Este archivo es el **único índice canónico** de navegación. Los documentos históricos NO se
reescriben; se conservan por fecha y alcance. Si un documento histórico contradice lo de
abajo, la discrepancia queda registrada y adjudicable, no se reconcilia silenciosamente.

## 0. Reglas de consulta y separación de contexto

- Partir de este índice y consultar solo el contrato, código, pruebas y evidencia pertinentes;
  no cargar indiscriminadamente reportes o checkpoints.
- El código del HEAD y los cambios locales investigados permiten determinar implementación;
  un documento o un grafo no demuestra que una función exista.
- `AGENTS.md`, las políticas y los contratos acreditados gobiernan las obligaciones según
  su autoridad aplicable. Este índice no crea una jerarquía nueva ni deroga contratos.
- Toda evidencia se interpreta para su HEAD, fecha, entorno y alcance. Resultados históricos
  no equivalen a pruebas actuales; los experimentos no promovidos no generan nuevos requisitos.
- Graphify es auxiliar: verificar su snapshot contra el HEAD y los archivos investigados.
  Si no corresponde, o su identidad es desconocida, no usarlo como autoridad de implementación.
  No se regeneró en DOC-REORGANIZATION-FAST-01.

### Clasificación de consulta (sin traslados ni derogaciones)

| Clase | Referencias y tratamiento |
|---|---|
| **ACTIVA — instrucciones y navegación** | `AGENTS.md`, `README.md`, `PHASES.md`, este índice, `docs/CAPABILITY_MATRIX.md`; `AGENT-PROTOCOL.md` conserva sus instrucciones aplicables. |
| **ACTIVA — obligaciones y gates** | `docs/architecture/CROSS-SKILL-CONTRACT-V3.1.md`, `docs/04-DEVELOPMENT-SAFETY-POLICY.md`, `docs/01-SPEC-V1.0.md`, `docs/05-CERTIFICATION-S4.4-V0.md`, `docs/07-STUDY-LOOP-SPECIFICATION-V1.0.md`, `docs/08-S7-TUTOR-POLICY-SPEC-V1.0.md`, `docs/B1R_ACCEPTANCE_CONTRACT.md`, `docs/TEST_CERTIFICATION_PERIMETER.md`. Conservar además contratos SSE, persistencia, evaluación y evidencia exigida por gates abiertos; esta lista no es exhaustiva. |
| **ACTIVA — operaciones y continuidad** | Planes de §2, sujetos a la autorización del trabajo concreto; `docs/DEPENDENCY_REPRODUCIBILITY.md`, `docs/recovery/2026-10-20-PHASE3-MIGRATION-MANIFEST.md` y `docs/recovery/2026-10-20-STRUCTURAL-RECOVERY-MANIFEST.md` para procedencia y recuperación histórica, no como pruebas de respaldo actual. |
| **HISTÓRICA — consulta explícita** | Los tres reportes de la tabla siguiente; sus resultados no describen automáticamente HEAD actual. No cargar el resto de `checkpoints/` o `reports/` por defecto, sin por ello declararlos prescindibles. |
| **EXPERIMENTAL — sin promoción acreditada aquí** | `docs/09-EXPERIMENTAL-SPEC-13-SOURCES.md` se declara experimental y congelada. Conservarla: no se adjudica aquí su promoción ni se derogan obligaciones de su ámbito. |
| **INDETERMINADA — conservar** | `ARCHITECTURE_BASELINE.md` y `AUDIT_CONTEXT.md` mezclan snapshots anteriores con restricciones de perímetro; concurrencia V1.0/V1.1 sin sucesión adjudicada aquí. `OWNER_DECISION_REQUIRED` antes de retirar o resolver autoridad. |

### Candidatos históricos exactos — propuesta condicionada, no autorización de retiro

| Ruta original | Alcance histórico | Referencias que deben preservarse o actualizarse antes de retirar |
|---|---|---|
| `TALOS_OPENCODE_TOOLCHAIN_AUDIT.md` | Auditoría 2026-10-06, HEAD `713409f` | `docs/P1_2_y_RELEASE_GATE_ISOLATION_SQLITE_SNAPSHOT_RESOLUTION.md` y `docs/STEP-31B-AUDITORIA-CONSISTENCIA-INTERNA-Y-COBERTURA-BRECHAS.md`. |
| `docs/audit_diagnostico.md` | Declara snapshot `main@480ce17` y nota de vigencia histórica | `checkpoints/085-busqueda-evidencia-l3-existente.md`, `checkpoints/103-arqueologia-c3-hard-ceiling.md` y `docs/REALITY_AUDIT_REPORT.md`. |
| `docs/audit_comparativo_v1.md` | Informe comparativo fechado 2026-09-23 | `docs/REALITY_AUDIT_REPORT.md`. |

Los tres están tracked y sin cambios locales al comprobarlos. La búsqueda textual de nombres
no encontró consumidores en código, tests, scripts o configuración examinados, pero no prueba
ausencia de dependencias dinámicas ni libera cadenas de evidencia de gates. No hay lote
autorizado para retiro: copiar externamente con permisos adecuados, verificar hashes y
recuperación, resolver referencias y autoridad de gates, y obtener aprobación de las rutas exactas.

Conservar especialmente `checkpoints/123-e2e-study-loop-analysis.md`,
`checkpoints/125-forensic-isolation-audit.md`, los checkpoints del 13/14 de octubre,
la evidencia formal de Fase 1 de Meta 2 y la cadena B1-R/P1.2 (§5 y §7).
Los identificadores CP123/CP125 aparecen en tests activos; no son candidatos de este lote.
Los criterios completos T01–T20 no deben reconstruirse por inferencia.

**Limitación de procedencia:** DOC-AUTHORITY-01 y DOC-ARCHIVE-01 no fueron localizados por
nombre o identificador en los archivos locales examinados. Esta separación focal usa las
referencias existentes de este índice; no sustituye esos inventarios ni una auditoría global.

## 1. Identidad y misión

TALOS (sistema de estudio personal; marca *KASIU*, materiales *FADeNA*) es un **tutor de estudio en
ciberseguridad e ingeniería basado en evidencia**: chat socrático con grounding PDF→cita,
currículo por cuadernos (KCs + prerrequisitos), ejercicios deterministas, evaluación sin
LLM, BKT + SM-2, abstención fail-closed y auditoría forense NLI. Backend
`src/study_engine/` (FastAPI, 29 paquetes), UI `kasiu-lab/ui/` (Vite/React).

## 2. Referencias documentales previas (no crean un orden de autoridad)

| Grupo de navegación | Documento | Alcance registrado al 2026-10-20 |
|---|---|---|
| 0 | `AGENTS.md` (raíz) | Normas del agente: autoridad, fail-closed, prohibición de git-destructivas |
| 1 | `docs/PLAN_MAESTRO_CIERRE_TALOS.md` | Estado operativo P0–P3 → **es el plan de cierre V1, NO es el plan T01–T20** (ver §4) |
| 2 | `docs/ROADMAP_V1_5_MASTER.md` | Metodología y promotion gates de las Fases V1.5 (1 Evidence → 2 Pedagogy → 3 Student Eval → 4 Visual) |
| 3 | `docs/TALOS_ROADMAP_V1_V1_5_V2.md` | Frontera de versiones V1/V1.5/V2 (mapa de dependencias) |
| 4 | `docs/01-SPEC-V1.0.md`, `docs/07-STUDY-LOOP-SPECIFICATION-V1.0.md`, `docs/08-S7-TUTOR-POLICY-SPEC-V1.0.md`, `docs/E3_ARCHITECTURE.md`, `docs/ARCHITECTURE.md`, `docs/CAPABILITIES.md` | Especificaciones originales V1.0-elite (congeladas; snapshot 2026-09-23) |
| 5 | `docs/PLAN_MEJORA_PEDAGOGICA_TALOS.md` | Serie PED-F0…F7 (Gates A–E) |
| 6 | `docs/CAPABILITY_MATRIX.md` | **Matriz única capacidad↔implementación↔evidencia** (mantenerla al hacer cambios) |
| 7 | `checkpoints/` e índice `checkpoints/index.md` | Historial CP001–CP154 (evidencia fechada; tests referencian CP123/CP125) |
| 8 | `docs/checkpoints/TALOS_V15_CHECKPOINT_2026-10-13.md` / `-14` | Únicos registros físicos de la serie T01–T20 (ver §4) |

Contradicciones abiertas registradas con fecha y productor (ver §5) — no resolverlas
editando documentos históricos.

## 3. Roadmap académico externo (NO es roadmap de desarrollo)

`ROADMAP KASIU TECH — v4 Definitiva (AI-Integrated)`: mapa estratégico del dominio para
estudio independiente (Fases 0→5 + gateways + AI governance). **No reemplaza las materias
FADeNA ni el plan operativo de TALOS.**

- Copias byte-idénticas (verificado 2026-10-20): `/media/agustin/Laboratorio/RoadmapNuevoHorizonte.txt` y `data/benchmark/sources/RoadmapNuevoHorizonte.txt`.
- Ubicación actual dentro del repo es **errónea** (directorio de fuentes de benchmark).
- Reubicación propuesta (no ejecutada; el archivo está rastreado): mover a `docs/` con
  actualización de referencias — pendiente de navegar consumidores de `data/benchmark/sources/`.
- Referencia canónica provisional: este índice (§3).

## 4. Serie T01–T20 — estado de recuperación

El plan maestro V1.5 de 20 paquetes **conserva autoridad conversacional pero no existe
como archivo físico**: `TALOS_V15_CHECKPOINT_2026-10-13.md` declara que los textos no se
localizaron; `ROADMAP_INTEGRAL_TALOS.md` §11 mantiene la secuencia sin sustitur el plan.
No recrear el plan: los criterios completos de **T02, T03, T05, T08–T14, T16–T19 son
UNKNOWN** (fail-closed).

Recuperado físicamente mejor de lo documentado en `603a097` (2026-10-20): tests y código
de **T13a** (`tests/unit/session/test_t13a_persistent_identity.py`, `session/session_store.py`),
**T06** (`tests/unit/pedagogy/test_t06_persistent_idempotency.py`, `student/storage.py`),
**T12** (`tests/unit/pedagogy/test_t12_episode_identity_and_restore.py`, UI
`episodeAttemptService.ts`) y **T15** (`tests/unit/web/test_t15_runtime_boundary.py`,
`web/app.py`/`dependencies.py`). Estado: implementados con tests sintéticos; **sin
checkpoint que cierre su aceptación** ni registro de corrida desde 2026-10-14
(`TEST_NOT_RUN_CURRENT`).

Checkpoint de corridas focales 2026-10-20 (M1-01, agente, sintético, sin checkpoint de
aceptación): **T06, T12, T13a, T15 = 25 passed** (`.m1_01/M1_01_RESUMEN.md` §5). Estado
de los focales del día no modifica el `TEST_NOT_RUN_CURRENT` normativo de los paquetes.
Clasificación entregada: `M1_ACADEMIC_LOOP_PARTIAL`. Evidencia M1-01 preservada fuera de
Git en `Almacenamiento/Facultad/TALOS/m1-01-evidence-20261020/` (`manifest.json`,
SHA-256 `89985f41c3ad07e38b698e4f34297edbe01b262af528a385e29b5d5c61175758`); `.m1_01/` no se versiona.

Colisión de nomenclatura a vigilar: los labels **F1/F2/F3** de `603a097` (grounding,SSE,NLI)
son namespaces post-T07 nuevos y NO corresponden a las Fases 1–3 metodológicas de V1.5
ni a PED-Fx. Fuente única actual: mensaje del propio commit (`git show -s 603a097`).

## 5. Contradicciones y UNKNOWNs visibles

| # | Contradicción / UNKNOWN | Fuente A | Fuente B | Estado |
|---|---|---|---|---|
| C-1 | `ROADMAP_V1_5_MASTER` §5.0 declara Fases 1A–1E cerradas; §10 las lista PENDING | §5.0 (oct-2026) | §10 sin conciliar | abierta |
| C-2 | B1-R: `TECHNICAL PASS` histórico vs expediente `FAIL` vigente | checkpoint 2026-10-13 | adjudicaciones B1-B/B1-R previas | abierta |
| C-3 | P1.2 quality gate: `1 failed/3100 passed` (fallo funcional histórico, no adjudicado) vs `exit 2` por provenance de snapshot (2026-10-09) | PLAN_MAESTRO | TALOS_ROADMAP_V1_V1_5_V2 §8.2 | abierta |
| C-4 | Plan T01–T20 íntegro no recuperado | checkpoint 10-13/14 | — | UNKNOWN normativo |
| C-5 | Snapshot payload B06: v1 `INVALID/supersedido`; v2 `VALID` `ad93bec4` / `1985a58d`; TTL vencido 2026-10-10 | talos-f09 (externo) | talos-p1-2-b06-* (externo) | adjudicada: solo e9af1327 es vigente |
| C-6 | Código del piloto Colab (`TALOS-COLAB-PILOT-01/`: src, tests, notebooks, config) existe SOLO fuera del repo (832K, sin git). **Migrado con verificación hash (2026-10-20, Phase 3)** a `/media/agustin/Almacenamiento/Facultad/TALOS/experiments/colab/TALOS-COLAB-PILOT-01/`; existe además una copia divergente histórica en `/media/agustin/Almacenamiento/Facultad/TALOS-COLAB-PILOT-01/` (preexistente, no fusionar: tiene inputs PDF únicos y `Untitled1.ipynb` distinto) | dir externo | repo solo tiene `resultados/*.zip` | hallazgo; preservado en Facultad + backup |
| C-7 | Token de acceso GitLab embebido en URL del remoto `gitlab` (exposición: cualquier `git remote -v`) | git config | — | accionado al owner (rotar, sin cambios del agente) |
| C-8 | M1-01 (2026-10-20): circuito académico en vivo con NLI/audit reales produce `REJECTED_UNSUPPORTED` por compliance parcial (~50%) de citas `[E#]` del generador vivo — audit fail-closed correcto, varianza de proveedor no resuelta (no es defecto del mecanismo) | audit `CHECK_FACTUAL_GROUNDING` L1 + NLI L2 (`.m1_01/probe_concept_audit.py`, probe `3× ENTAILED / 1× UNASSESSED-503`) | corridas live v6/v7 (`.m1_01/evidence/`) | abierta (UNKNOWN, proveedor) |
| C-9 | M1-01: rate-limit Gemini (HTTP 503) en NLI deja claims `UNASSESSED` (técnico) → `FLAGGED_UNASSESSED`; sin mecanismo de reintento para técnico-fallo en el path `explain_concept` (solo chat retry por DEFERRED) | audit metrics v7 | orchestrator fail-closed | abierta (plataforma) |
| C-10 | M1-01: briefing de sesión sintética dirige al perfil real "Agustín" (student-study-loop-v1) — provenance del StudentState consultado UNKNOWN; riesgo de mezcla real/sintético | `/api/chat/briefing` v6 | StudentState isolation (BKT p_L del sintético conserva 0.0 sin mutación) | abierta (verificar aislamiento de perfil) |
| C-11 | M1-01: 4 suites de `tests/unit/pedagogy` fallan (f4_format_policy[asyncio], cold_start_unification, solution_protection, spiral_curriculum setup) — no atribuibles a los cambios de M1-01 (focales/protected en verde), corredas sin baseline contra HEAD | pytest local | `test_suite 1478/1478` (health, cache CI) | UNKNOWN (preexistente?, sin verifier) |

## 6. Mapa de datos y del sistema

Puntos de verdad: `data/web_state/{vector_store,knowledge_store,student_state,sessions}.db` (+vec_shards), `data/student/`, `config/{notebook_kc_catalog,l3_authorization_manifest,bkt_params,test_perimeter}.json`. P0 threat model: host-local (1 slot, RLIMIT 512MiB, 3s). Entradas API/UI: `web/routes/*` (19 routers) y `kasiu-lab/ui` (ChatWorkspace como única vista raíz, tabs dentro de ella). Perímetro de tests: `config/test_perimeter.json` (27 suites). Quality gate: `scripts/quality_gate.py` / `scripts/test.sh`.

## 7. Evidencia de cadena B06 (externos referenciados)

`docs/F-11-POST-WORKER-B06-ADJUDICATION.md` y `docs/F-12-...` citan los directorios de evidencia
(migrados con verificación hash el 2026-10-20 a `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/`):
`F07-F12/talos-f07-diagnostic-vXugos2f/`, `F07-F12/talos-f08-resolution-lfs8neBd/`, `F07-F12/talos-f09-authorization-gUVYAnpn/`,
`F07-F12/talos-f10-worker-.../`, `B06/talos-v1.5-b06-capture-e9af1327-.../capture-attestation.json`.
Estado normativo guardado ahí: B06 `PREPARED_AND_VALIDATED`, worker `TEST_PASS`, gate `NOT_AUTHORIZED`.
En `/media/agustin/Almacenamiento/Facultad/TALOS/manifests/` está el manifiesto de migración (origen→destino, hashes, reversión).
Estado de respaldo de estos externos ver copia en `20261020T114944Z-phase2-structural-recovery`.
Evidencia vinculante de los SHA y estados: talos-f09-authorization-gUVYAnpn.
