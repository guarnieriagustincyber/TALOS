# RECOVERY MANIFEST — TALOS PHASE 2 · 2026-10-20

> **NOTA (2026-10-20, Phase 3):** los directorios externos citados en este documento fueron **migrados con verificación hash** a `/media/agustin/Almacenamiento/Facultad/TALOS/` (historical-evidence/, experiments/, backups/). Las rutas bajo `/media/agustin/Laboratorio/` que aparecen abajo corresponden al estado histórico de Phase 2. Ver `docs/recovery/2026-10-20-PHASE3-MIGRATION-MANIFEST.md` y `Facultad/TALOS/manifests/`.

**Operación:** TALOS PROJECT RECOVERY — PHASE 2 (recuperar → reconciliar → preservar → reorganizar → validar → continuar).
**Checkpoint protegido:** `603a097` — verificado accesible y con el contenido esperado (75 archivos, +7.231; incluye `test_t06_persistent_idempotency.py`, `test_t12_episode_identity_and_restore.py`, `test_t13a_persistent_identity.py`, `test_t15_runtime_boundary.py`, `test_chat_manifest_trust.py`, `test_nli_optimization.py`, `test_grounding_markdown.py`, UI `episodeAttemptService.ts`/`citationIdentity.ts` — show-stat respaldado en el backup).
**Reglas respetadas:** sin `reset/clean/stash/rebase/merge/push/prune`; sin borrar nada; sin tocar DBs productivas ni evidencia sellada; sin exponer secretos.

---

## A. Inventario de worktrees y repositorios externos

| Directorio | Naturaleza | Git/HEAD | Trabajo exclusivo | Respaldo | Decisión |
|---|---|---|---|---|---|
| `study-engie/` | Repo principal | `603a097` @ `checkpoint/talos-v15-20261014`; 133→136 dirty; worktree único | — | ✅ backup phase2 | conservar |
| `study-engie.worktrees/` | Vacío residual; sin worktrees registrados | N/A | nada | n/a | archivar (eliminable con autorización futura) |
| `/media/.../TALOS-COLAB-PILOT-01/` | **Código fuente completo del piloto Colab** (estado `COLAB_PILOT_IMPLEMENTED_PENDING_EXECUTION`) | no-git | `src/`, `tests/`, `notebooks/`, `config/sources.json`, `schemas/`, `docs/` — **no existen dentro del repo** (el repo solo tiene `resultados/*.zip`) | ✅ copiado a backup `external-exclusive/` | **integrar al repo en fase posterior** (mayor riesgo real de pérdida detectado) |
| `TALOS-DEVTOOLS-001/` y `-002/` | Reportes de tooling / MCP | no-git | 9 reportes (md/tsv) | ✅ backup | archivar / integrar si son normativos |
| `talos-f07-diagnostic-vXugos2f/` | Reporte diagnóstico F-07 de la cadena B06 | no-git | `F-07-DIAGNOSTIC-REPORT.md` + SHA + inventario json | ✅ backup | conservar (referenciado por docs/F-11/F-12) |
| `talos-f08-resolution-lfs8neBd/` | Decisión F-08 + preparación B06 | no-git | report + SHA | ✅ backup | conservar |
| `talos-f09-authorization-gUVYAnpn/` | Snapshot B06 sellado: v1 `INVALID/supersedido`, v2 `VALID` (`ad93bec4…`/`1985a58d…`) + decisión F-09 | no-git | 3,2G | 🔒 in-situ (ver `sealed-in-place-registry.txt`) | conservar; no reubicar sin actualizar referencias |
| `talos-f10-worker-20261010T1529Z-…/` | Receipt del worker focal: `TEST_PASS`, gate `NOT_AUTHORIZED` | no-git | receipt jsons + SHA | ✅ backup | conservar |
| `talos-p1-2-b06-capture-20261009/` | Captura B06 (run `745edebe…`) supersedida | no-git | 1,6G | 🔒 in-situ | archivar (propuesta) |
| `talos-p1-2-b06-snapshot-20261009/` | Snapshot v1 supersedido | no-git | 1,6G | 🔒 in-situ | archivar (propuesta) |
| `talos-v1.5-b06-capture-e9af1327-…/` | **Captura B06 VIGENTE** (única referenciada por F-07…F-12; TTL vencido 2026-10-10 → evidencia histórica) | no-git | 1,6G; payload byte-idéntico a la captura 09 y al estado vivo `data/web_state/` | 🔒 in-situ | conservar |
| `talos-wip-backups/` | Respaldos WIP (preliminar + phase2) | no-git | — | (es el backup) | mantener |
| (no TALOS) `Cerebro_Ciberseguridad`, `Ciberseguiradad`, `Estudio_libros`, `PlanDeEstudio`, `preuba.txt`, `RoadmapNuevoHorizonte.txt` (copia externa), `TALOS_RAG_…docx`, `timeshift`, `lost+found`, `.Trash-1000` | personales / sistema | — | — | — | sin intervenir |

**Duplicados por identidad verificados:** `RoadmapNuevoHorizonte.txt` (Laboratorio ↔ `data/benchmark/sources/` en repo) byte-idénticos. Ningún directorio externo contiene commits no presentes en `603a097` (todos son no-git).

**Incidente de seguridad detectado (acción del owner, no del agente):** el remoto `gitlab` de `study-engie` tiene un access token embebido en la URL (`git remote -v` lo muestra). Recomendación: rotar la credencial y migrar a `credential.helper`. No se copió a ningún respaldo ni informe.

## B. Respaldo

**Nuevo (esta fase):** `/media/agustin/Laboratorio/talos-wip-backups/20261020T114944Z-phase2-structural-recovery/` (2,1G):

| Artefacto | Contenido | Verificación |
|---|---|---|
| metadatos | HEAD/branch/status-porcelain(133)/log/worktree-list, `show-stat-603a097.txt` | incluidos en sha256 |
| `patches/` | diff HEAD pendiente: no-graphify (24K) + graphify (47M) | incluidos en sha256 |
| `untracked-essential.tar.gz` | `TALOS-COLAB-PILOT-01/resultados`, `.github/`, `.opencode/README.md` (+ listas) | restauración de muestra OK (zip y doc idénticos) |
| `dbs/` | **22 snapshots SQLite consistentes** (apertura modo-ro + `backup`, sin servicios activos — verificado) | `quick_check` OK en las 22 (`dbs/snapshot-results.txt`) |
| `external-exclusive/` | piloto Colab completo (832K) + talos-f07/f08/f10 + DEVTOOLS-001/002 + talos-p1-2-b06-evidence | incluidos en sha256 |
| registros | `backup-sha256.txt` (36 hashes, todos OK), `exclusions.txt`, `sealed-in-place-registry.txt`, `secrets-registry.txt`, `README.txt` | `sha256sum -c` OK |

**Exclusiones declaradas:** `graphify-out/` (regenerable; diff tracked preservado en `patches/`), `.venv`/`node_modules`/caches, `models/` (748M descargables), `.env` (NUNCA respaldado; solo se registró su existencia), payloads sellados B06 (preservados in-situ con sus propios SHA256SUMS).
**Respaldo preliminar (NO modificado):** `20261020T112807Z/` — capturó el estado en `db6b5b7` antes del commit de preservación; red de seguridad histórica.
**Prueba no destructiva de restauración:** OK (extracción de zip y doc del tar + comparación de hash contra los originales).
**Limitación expresamente declarada:** todo el respaldo vive en el MISMO disco; la copia a volumen externo es tarea del owner (pendiente; por B.4 esto impide tratar el respaldo como protección antipérdida física).

## C. Matriz funcional reconciliada

→ `docs/CAPABILITY_MATRIX.md` (matriz canónica única; 30 filas, estado de 4 niveles `EXISTS_CODE / INTEGRATED / VALIDATED / ACCEPTED`, alcance M1/M2/POST, brecha y acción).
Resumen: ~12 capacidades INTEGRadas para Meta 1; ~8 PARTIAL/UNKNOWN por serie T01–T20 y P1.2; Fases 2–4 de V1.5 ABSENT por bloqueo de promoción (`PHASE_1_PROMOTABLE=FALSE`); huérfanos declarados (F24/F25/F26). **Ninguna capacidad está en estado `ACCEPTED` a 2026-10-20.**

## D. Mapa documental canónico

→ `docs/PROJECT_INDEX.md` (índice único con precedencia documental y contradicciones visibles C-1..C-7).
Nuevo en esta fase: orden de recuperación del checkpoint `603a097` dentro del backup y registro explícito del namespace **F1/F2/F3** (post-T07, grounding/SSE/NLI) cuya definición hoy solo existe en el mensaje del commit — **contradicción menor nueva (C-8)**.

## E. Manifiesto de limpieza

**Operaciones EJECUTADAS (reversibles, Grupo F1 — solo untracked sin consumidor):**

| Fecha (UTC) | Operación | Origen → Destino | Reversión |
|---|---|---|---|
| 2026-10-20 ~11:57Z | mv `./sqlite:` | → `archive/local-accidents-2026-10-20/sqlite:` | `mv archive/local-accidents-2026-10-20/sqlite: ./sqlite:` (desde raíz del repo) |
| 2026-10-20 ~11:57Z | mv `./file:data` | → `archive/local-accidents-2026-10-20/file:data` | ídem |
| misma | registro creado | `archive/local-accidents-2026-10-20/OPERATION_MANIFEST.txt` (untracked) | opcional con autorización |

Estado git: antes 133 → después 136 entradas porcelain (delta = los 3 documentos nuevos + `archive/` re-enumerado como untracked; **delta esperado y consistente**). Cero borrados permanentes.

**Operaciones PROPUESTAS (no ejecutadas; cada una requiere autorización específica):**

1. **F2 — deduplicación de corpus (NO ejecutada por directiva):** Joyanes ×3 (20,9 MB), corpus-bundle 74 MB ×2 (`reports/` ↔ `drive_upload_cp116`), `spa.traineddata` ×2 (raíz ↔ `data/ocr/tessdata`), embeddings qwen3 ×2 bundles (~183 MB), ~20 PDFs repetidos entre `fuentes/` / `corpus_upload/` / `data/benchmark/sources/` / `kasiu-lab/storage/sources/`. Propuesta: designar `data/sources/` canónico y actualizar referencias de ingestion/scripts después de navegar consumidores en runtime.
2. **F3 — worktrees y experimentos:** integrar el código de `TALOS-COLAB-PILOT-01` al repo; archivar capturas B06 supersedidas con actualización de las referencias del docs/F-11-F-12. Decisión previa requerida.
3. **F4 — git hygiene (propuesta, sin tocar índice):**
   - conciliar `.gitignore` con tracking vigente: `artifacts/` (tracked a pesar del ignore), `tmp/` (29 tracked), `benchmark/results/`, `graphify-out/` (conservar `graph.json` actual; ignorar snapshots históricos y cache ast), `reports/` (rastrear solo lo canónico — `V1_RELEASE_CERTIFICATION.md`, `v1_5_phase1/`; los bundles y outputs a LFS/externo);
   - mover a almacenamiento externo/LFS: `reports/talos_corpus_bundle_*.zip` (~114 MB), `models/` (748M), `kasiu-lab/ui/bin/tailwindcss` (107 MB);
   - candidatos a eliminar tras próxima corrida y con autorización: `backend.log`, `frontend.log`, `debug_final_prompt.txt`, marcadores vacíos `BASELINE`/`PHASE_*`/`PROMOTION`, `.mypy_cache`/`.ruff_cache`/`.pytest_cache`, snapshots `graphify-out/2026-10-08..11/` (~183 MB);
   - añadir a `.gitignore`: `archive/`, `sqlite:`, `file:data`, `data/web_state/`, DBs runtime (`*.db` de `data/`), `TALOS-COLAB-PILOT-01/resultados/` (o pasarlas a LFS).
4. **Seguridad:** rotar token GitLab (owner), activar `credential.helper`.
5. **Documentación:** consolidar la navigación en `docs/PROJECT_INDEX.md` (ya referenciado desde README).

## F. Estado de Meta 1 y Meta 2

**Meta 1 — tutor académicamente funcional:**
- Base técnica presente e integrada (F01–F11, F13–F19, F23): abrir sesión → consulta con evidencia y citas → ejercicio → evaluación determinista → actualización BKT/SM-2 → briefing. El flujo es factible localmente hoy.
- Brechas funcionales reales para declarar Meta 1:
  (i) P1.2 quality gate sin corrida canónica exitosa (última ejecución: bloqueo por provenance del snapshot B06; F-09 dejó la captura `VALID` y el worker `TEST_PASS` con gate `NOT_AUTHORIZED` — falta adjudicar la corrida del gate);
  (ii) corrida registrada de la suite actual de los trabajos T13a/T06/T12/T15 (`TEST_NOT_RUN_CURRENT` desde 2026-10-14);
  (iii) validar el contrato terminal SSE en ruta real (contradicción C-2 B1-R);
  (iv) un piloto académico E2E con estudiante real en un cuaderno FADeNA;
  (v) el código del piloto Colab debe integrarse al repo para cerrar el riesgo de omisión (C-6).
- Siguiente etapa: (1) snapshot limpio + `quality_gate` para conocer la línea base real; (2) adjudicar T15 (frontera runtime) y cerrar los efectos de import de T01; (3) resolver B1-R; (4) cerrar serie T con el plan reconstruido por el owner; (5) piloto académico con un usuario y un cuaderno.

**Meta 2 — V1.5 completo (sin recortarlo a MVP):**
- PENDIENTE de ejecución con autorización: reconstrucción física del plan T01–T20 íntegro (C-4 — criterios de T02/T03/T05/T08–T14/T16–T19 = UNKNOWN); promoción de corpus (Fase 1 cerró con `PHASE_1_PROMOTABLE=FALSE`, C0 retenida; Fase 2 BLOCKED); ingesta multimodal T08/T09; PED-F6/Gate D aceptación completa (contrato terminal); PED-F7 y Fases 2–4 de V1.5 (ABSENT); A-PRE-1 (requiere ptrace habilitado en host); publish en `origin/main` sin verificación de sincronía con GitHub.
- La reorganización física NO constituye por sí sola Meta 1/2; es factor preparatorio.

**UNKNOWN declarados (fail-closed):** (C-4) plan T01–T20; (C-8) definición física de F1/F2/F3; si existe una corrida no registrada del WIP: se supone `NOT_RUN`; dependencia en runtime de `kasiu-lab/storage` respecto de la ingesta UI (pendiente de verificar antes del Grupo F2-copias); precondiciones hardware del host para A-PRE-1; sincronía exacta de `origin/main` con el HEAD local; si quedan referencias desde código a los directorios `archive/accidentes` movidos (se verificó "sin consumidores", se mantiene UNKNOWN parcial).

## G. Estado final de Git

- **HEAD/rama:** `603a097` @ `checkpoint/talos-v15-20261014` (predecesores: `db6b5b7`, `0323394`). Sin commits adicionales (la política de OpenCode deniega commits; respetada).
- **Cambios de esta operación respecto del inicio:** 3 documentos creados (`docs/PROJECT_INDEX.md`, `docs/CAPABILITY_MATRIX.md`, `docs/recovery/2026-10-20-STRUCTURAL-RECOVERY-MANIFEST.md`) + README actualizado (link de navegación) — todos untracked; 2 movimientos F1 (untracked→untracked bajo `archive/`); **0 archivos tracked de código modificados por el agente**; 0 borraduras; 0 cambios de índice Git.
- **Entradas porcelain:** final `136` (vs 133 inicial: delta por documentación nueva).
- **No se alteró:** commit `603a097` ni historia; fuentes, corpus, y todas las bases de datos productivas quedaron intactas (solo lectura).

## Registro de cierre contra §12

1. Estado preservado ✅ (commit `603a097` + backup verificado 36/36 + prueba de restauración).
2. Worktrees relevantes identificados ✅ (A).
3. Sin trabajo conocido sin referencia recuperable ✅ mitigado (piloto Colab y cadena F respaldados; **integración al repo = acción futura**).
4. Capacidades originales reconciliadas hasta el alcance de la evidencia ✅ (CAPABILITY_MATRIX).
5. Fuente de verdad documental clara ✅ (PROJECT_INDEX + contradicciones visibles).
6. Limpieza autorizada verificada ✅ (Grupo F1: 2 movimientos + manifiesto).
7. Movimientos de riesgo medio/alto ⚠️ procedimiento específico en E.1–E.4; **no ejecutados** (sin autorización explícita).
8. Estado de ambas metas explicable sin reconstruir conversaciones ✅ (F).

**`TALOS_STRUCTURAL_RECOVERY_COMPLETED_WITH_VERIFIED_GAPS`**

**Gaps abiertos declarados:** plan T01–T20 no recuperado (C-4); contradicción B1-R (C-2); P1.2 sin corrida canónica (C-3); código del piloto Colab fuera de git (C-6); token GitLab expuesto (C-7); respaldo solo en disco local (limitación declarada); F1/F2/F3 sin documentación (C-8).
**Pendientes para el owner / siguiente sesión:** copia del respaldo a volumen externo; rotación de token; integración del piloto Colab; corrida registrada de la suite T; adjudicación de la corrida del quality gate P1.2 con la captura e9af1327; reconciliar §10 del ROADMAP_V1_5_MASTER con §5.0 (C-1).
