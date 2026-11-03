# TALOS PHASE 3 — MIGRATION MANIFEST · 2026-10-20

**Operación:** reorganización física del laboratorio + migración de respaldos a `Almacenamiento/Facultad`.
**Checkpoint protegido:** `603a097` (intacto; sin commits del agente).
**Verificación:** comparación full-tree de hashes SHA-256 (origen↔destino) por grupo + manifiestos internos de cada backup.
**Restricción de entorno:** el sandbox del agente **deniega `rm`** (global). Las retiradas de origen ya copiadas quedan como **acción del propietario** (comando único verificado más abajo). `mv` cross-device sí está permitido y se usó donde era seguro.

## Mapa origen → destino

| # | Grupo | Origen (Laboratorio) | Destino (Facultad) | Contenido | Verificación |
|---|---|---|---|---|---|
| G1 | backups | `talos-wip-backups/20261020T112807Z/` | `TALOS/backups/structural-recovery/20261020T112807Z/` | backup preliminar (11 arch.) | 11 files; hashes idénticos; manifiesto interno 5/5 |
| G1 | backups | `talos-wip-backups/20261020T114944Z-phase2-structural-recovery/` | `TALOS/backups/structural-recovery/20261020T114944Z-phase2-structural-recovery/` | backup Ph2 (112 arch., 2,1G; incluye 22 snapshots SQLite) | 112 files; hashes idénticos; manifiesto interno 38/38 |
| G2 | evidencia | `talos-f07-diagnostic-vXugos2f/` | `TALOS/historical-evidence/F07-F12/` | reporte F-07 + SHA | full-tree idéntico (80 files del grupo) |
| G2 | evidencia | `talos-f08-resolution-lfs8neBd/` | `TALOS/historical-evidence/F07-F12/` | decisión F-08 + SHA | idem |
| G2 | evidencia | `talos-f09-authorization-gUVYAnpn/` | `TALOS/historical-evidence/F07-F12/` | **3,2G** snapshot B06 v1 INVALID + v2 VALID + F-09 | idem |
| G2 | evidencia | `talos-f10-worker-20261010T1529Z-…/` | `TALOS/historical-evidence/F07-F12/` | receipts worker (`TEST_PASS`/`NOT_AUTHORIZED`) | idem |
| G2 | evidencia | `talos-p1-2-b06-capture-20261009/` | `TALOS/historical-evidence/B06/` | captura B06 supersedida (1,6G) | idem |
| G2 | evidencia | `talos-p1-2-b06-evidence-20261009/` | `TALOS/historical-evidence/B06/` | logs STEP-05 + verificación attestation | idem |
| G2 | evidencia | `talos-p1-2-b06-snapshot-20261009/` | `TALOS/historical-evidence/B06/` | snapshot v1 supersedido (1,6G) | idem |
| G2 | evidencia | `talos-v1.5-b06-capture-e9af1327-…/` | `TALOS/historical-evidence/B06/` | **captura B06 VIGENTE** (1,6G) | idem |
| G3 | experiments | `TALOS-COLAB-PILOT-01/` (copia de Laboratorio) | `TALOS/experiments/colab/TALOS-COLAB-PILOT-01/` | código piloto (832K) | 47 files grupo; hashes idénticos |
| G3 | experiments | `TALOS-DEVTOOLS-001/` | `TALOS/experiments/devtools/` | reportes tooling | idem |
| G3 | experiments | `TALOS-DEVTOOLS-002/` | `TALOS/experiments/devtools/` | reportes tooling | idem |
| G4 | estudios | `Cerebro_Ciberseguridad/` | `Estudios/Ciberseguridad/` | apuntes + subproyecto Agustin-Ciber (con node_modules) | 4.162 files grupo; hashes idénticos |
| G4 | estudios | `Ciberseguiradad/` | `Estudios/Ciberseguridad/` | apuntes | idem |
| G4 | estudios | `Estudio_libros/` | `Estudios/Materiales-academicos/` | libros | idem |
| G4 | estudios | `PlanDeEstudio/` | `Estudios/Materiales-academicos/` | programas de estudio | idem |
| G4 | estudios | `RoadmapNuevoHorizonte.txt` (Laboratorio) | `Estudios/Ciberseguridad/RoadmapNuevoHorizonte.txt` | ROADMAP KASIU TECH v4 (copia byte-idéntica a la de `data/benchmark/sources/`, que permanece en el repo) | idem |
| G5 | legacy | `TALOS_RAG_MultiSource_Deep_Research_2026.docx` (mv, sin copia residual) | `TALOS/archives/legacy/` | doc investigación RAG (52.954 bytes) | sha256 `8797de6c…8f8c62` |
| G5 | estudio ambiguo | `preuba.txt` (mv) | `Otros/preuba.txt` | texto suelto 225.857 bytes (clasificación incierta; contenido íntegro) | mv copy+unlink exitoso |
| G5 | archive repo | `study-engie/graphify-out/2026-10-08..11/` (mv) | `TALOS/archives/snapshots/graphify-out/` | snapshots históricos del grafo (~154M, untracked, regenerables) | por diseño de mv; grupo regenerable |
| G5 | archive repo | `.mypy_cache`, `.ruff_cache`, `.pytest_cache` (mv) | `TALOS/archives/snapshots/caches/` | caches regenerables (30M) | idem |
| G5 | archive repo | `backend.log`, `frontend.log`, `debug_final_prompt.txt` (mv) | `TALOS/archives/snapshots/logs/` | logs runtime históricos (1,15M) | idem |

**Preexistente NO tocado:** `/media/agustin/Almacenamiento/Facultad/TALOS-COLAB-PILOT-01/` (copia divergente histórica del piloto: tiene inputs PDF únicos y `notebooks/Untitled1.ipynb` distinto — 266.703 bytes vs 60.839; la copia de Laboratorio tenía placeholders `models/` vacíos). Registrada como copia separada, sin fusión.
**Directorio `Facultad/respaldo/`** (vacío, creado hoy por el propietario): no intervenido; reportado.

## Referencias documentales actualizadas (repo)

- `docs/F-11-POST-WORKER-B06-ADJUDICATION.md`, `docs/F-12-…`, `docs/TALOS-P1_2-STEP-05-B06-EXECUTION.md`, `docs/TALOS-P1.2-STEP-06-FAILURE-ADJUDICATION.md`, `docs/P1.2-A3-CIERRE-DOCUMENTAL-Y-RETORNO-PLAN-MAESTRO.md`: rutas absolutas `/media/agustin/Laboratorio/talos-*` → `/media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/{B06,F07-F12}/…` (0 referencias restantes).
- `docs/PROJECT_INDEX.md` (C-6 y §7) y `docs/CAPABILITY_MATRIX.md` (F28): actualizados con el nuevo destino y la copia divergente.
- Los 8 directorios de evidencia se copiaron y verificaron ANTES de actualizar las referencias; las referencias apuntan a la copia verificada.

## Retirada de orígenes (acción del propietario — `rm` denegado al agente)

Las copias destino están **verificadas byte-idénticas**. Para retirar los originales de Laboratorio:

```bash
cd /media/agustin/Laboratorio
rm -rf talos-wip-backups \
  talos-f07-diagnostic-vXugos2f talos-f08-resolution-lfs8neBd \
  talos-f09-authorization-gUVYAnpn talos-f10-worker-20261010T1529Z-e9af1327-fe78-416f-a1b6-cc5a41af2369 \
  talos-p1-2-b06-capture-20261009 talos-p1-2-b06-evidence-20261009 \
  talos-p1-2-b06-snapshot-20261009 talos-v1.5-b06-capture-e9af1327-fe78-416f-a1b6-cc5a41af2369 \
  TALOS-COLAB-PILOT-01 TALOS-DEVTOOLS-001 TALOS-DEVTOOLS-002 \
  Cerebro_Ciberseguridad Ciberseguiradad Estudio_libros PlanDeEstudio \
  RoadmapNuevoHorizonte.txt
```

*(La copia de `RoadmapNuevoHorizonte.txt` permanece rastreada en `study-engie/data/benchmark/sources/`; la de Laboratorio es redundante, ya verificada en Facultad.)*

## Reversión (copiar de vuelta, verificado por hash)

```bash
cp -a /media/agustin/Almacenamiento/Facultad/TALOS/backups/structural-recovery/<id>        /media/agustin/Laboratorio/<nombre>
cp -a /media/agustin/Almacenamiento/Facultad/TALOS/historical-evidence/{F07-F12,B06}/<dir> /media/agustin/Laboratorio/<dir>
cp -a /media/agustin/Almacenamiento/Facultad/TALOS/experiments/{colab,devtools}/<dir>      /media/agustin/Laboratorio/<dir>
cp -a "/media/agustin/Almacenamiento/Facultad/Estudios/{Ciberseguridad,Materiales-academicos}/<dir>" /media/agustin/Laboratorio/<dir>
mv /media/agustin/Almacenamiento/Facultad/Otros/preuba.txt /media/agustin/Laboratorio/
mv /media/agustin/Almacenamiento/Facultad/TALOS/archives/legacy/TALOS_RAG_MultiSource_Deep_Research_2026.docx /media/agustin/Laboratorio/
mv /media/agustin/Almacenamiento/Facultad/TALOS/archives/snapshots/graphify-out/<fecha> /media/agustin/Laboratorio/study-engie/graphify-out/
mv /media/agustin/Almacenamiento/Facultad/TALOS/archives/snapshots/{caches/<cache>,logs/<log>} /media/agustin/Laboratorio/study-engie/
```

## Pendientes del propietario / siguientes fases

### Preflight final (2026-10-20·II) — veredicto: SAFE_TO_REMOVE en los 17 orígenes

1. **Reconciliación:** 17 orígenes = 17 entradas del comando anterior (el conteo previo de "18" incluía a `study-engie`, excluido por directiva). El comando cubre el total; los respaldos aportan 2 sub-pares → 18 pares en el script.
2. **Revalidación SHA-256 origen↔copia actual (post-migración):** **4.411 archivos, 12,0G — 0 agregados, 0 faltantes, 0 modificados.** Registro: `Facultad/TALOS/manifests/preflight-sha256-origen-20261020.sha`. (Hallazgo interno: los 3,2G de `f09` contienen los 2 snapshots e9af1327 v1/v2; todos hash verificados.)
3. **Symlinks absolutos de `Cerebro_Ciberseguridad` (30, en la copia destino):** reescritos lista-explícita 10×`.agents/skills/`, 10×`.claude/skills/`, 10×`.opencode/skills/` → apuntan dentro de la copia Facultad; **30/30 RESUELVE, 0 colgados** (los 7 relativos de `node_modules/.bin` inmunes). Los ORIGENES conservan los symlinks absolutos históricos sin cambio.
4. **Dependencias de scripts del repo resueltas (modificación autorizada de constantes de ruta, `py_compile` OK):**
   - `scripts/import_student_fase0_actual.py` → `SRC_BASE` = `Facultad/Estudios/Ciberseguridad/Ciberseguiradad/Fase 0/…/Fase0` (**validada: existe, 15 archivos, hash-paridad**).
   - `scripts/import_student_exercises.py` → `alt_source` (ruta efectiva) = `Facultad/Estudios/Ciberseguridad/Ciberseguiradad/Fase 0` (**validada: 43 archivos**). El default de línea 618 ya era inexistente antes de la migración; queda como histórico. Delta git: 141 porcelain (139+2 scripts).
5. **Procesos/montajes:** 0 descriptores abiertos hacia los 17 orígenes (scan `/proc/*/fd`); sin sub-montajes.
6. **Simulación completa del script de retirada (`talos-retirada-origenes.sh`, modo SIMULATE):** **18/18 pares PASS (existencia + conteo + bytes + re-hash full-tree por par).** Log: `Facultad/TALOS/manifests/simulacion-retirada-20261020.log`.

| Origen (Laboratorio) | Veredicto |
|---|---|
| talos-wip-backups (2 sub-pares) | SAFE_TO_REMOVE |
| talos-f07-diagnostic-vXugos2f | SAFE_TO_REMOVE |
| talos-f08-resolution-lfs8neBd | SAFE_TO_REMOVE |
| talos-f09-authorization-gUVYAnpn | SAFE_TO_REMOVE |
| talos-f10-worker-20261010T1529Z-… | SAFE_TO_REMOVE |
| talos-p1-2-b06-capture-20261009 | SAFE_TO_REMOVE |
| talos-p1-2-b06-evidence-20261009 | SAFE_TO_REMOVE |
| talos-p1-2-b06-snapshot-20261009 | SAFE_TO_REMOVE |
| talos-v1.5-b06-capture-e9af1327-… | SAFE_TO_REMOVE |
| TALOS-COLAB-PILOT-01 | SAFE_TO_REMOVE |
| TALOS-DEVTOOLS-001 | SAFE_TO_REMOVE |
| TALOS-DEVTOOLS-002 | SAFE_TO_REMOVE |
| Cerebro_Ciberseguridad | SAFE_TO_REMOVE |
| Ciberseguiradad | SAFE_TO_REMOVE |
| Estudio_libros | SAFE_TO_REMOVE |
| PlanDeEstudio | SAFE_TO_REMOVE |
| RoadmapNuevoHorizonte.txt | SAFE_TO_REMOVE |

**BLOCKED: ninguno.** Ejecución de la retirada: propietario con
`bash Facultad/TALOS/manifests/talos-retirada-origenes.sh` (SIMULATE) y luego
`bash … --execute` (una sola pasada doble-verificada; aborta total ante cualquier discrepancia; no se borra nada si algún par falla).

### Recuperación de retirada interrumpida (2026-10-20·III)

La ejecución propietaria de `talos-retirada-origenes.sh --execute` se interrumpió en F09 por directorios B06 con permisos `555` (sin atributo inmutable; 0 descriptores abiertos). Estado verificado por evidencia de filesystem:

1. **Retirados en el run interrumpido (4 grupos), copia Facultad íntegra vs registro preflight: PASS — 129 archivos hash-idénticos, 0 extras:** `talos-wip-backups/20261020T112807Z` (11), `talos-wip-backups/20261020T114944Z-phase2-structural-recovery` (112), `talos-f07-diagnostic-vXugos2f` (4), `talos-f08-resolution-lfs8neBd` (2). El padre `talos-wip-backups/` quedó vacío (residuo, se retira con `--execute`).
2. **F09 retirada parcial: 12/32 archivos** borrados por el run interrumpido (documentados: `F-09-DECISION-RECORD.md`, `F-09-RESULTS.md`, `SHA256SUMS.txt`, `b06-validation-record{,-v2}.json`, `effective-execution-manifest{,-record,-v2,-v2-record}.json`, `focal-execution-binding{,-v2}.json`, `snapshot-tamper-rejection.json`); **20/20 restantes hash-idénticos a la copia**; aritmética 12+20=32 cierra. Nada más diverge.
3. **Causa raíz:** 4 dirs con `555` → `talos-p1-2-b06-capture-20261009` (1), `talos-p1-2-b06-snapshot-20261009` (2, incl. `payload/`), `talos-v1.5-b06-capture-e9af1327-…` (1). El propietario ya normalizó f09 raíz (700), `b06-evidence` y `f10` (700); COLAB/DEVTOOLS/estudios sin bloqueos.
4. **Pendientes intactos: 13/13 pares PASS** full-tree (f10, b06-capture/evidence/snapshot, v1.5-capture, COLAB, DEVTOOLS×2, Cerebro, Ciberseguiradad, Estudio_libros, PlanDeEstudio, RoadmapNuevoHorizonte.txt) — sin re-copiado (solo hash).
5. **Script de reanudación:** `talos-reanudacion-retirada.sh` (repo: `docs/recovery/`; canónico: `Facultad/TALOS/manifests/`) — modos `SIMULATE` (default) / `--fix-perms` (chmod u+w SOLO dirs de pendientes bajo Laboratorio; jamás toca Facultad) / `--execute` (re-verifica todo → retira SOLO pendientes → paso E: re-valida recuperabilidad de todas las copias vs `preflight-sha256-origen-20261020.sha` antes de reportar completada; fail-closed: si algo falla no borra nada).
6. **Log de simulación de reanudación:** `Facultad/TALOS/manifests/simulacion-reanudacion-20261020.log` (2 corregidas: la primera de la AMC trunca la comparación de A por prefijo; la segunda 2026-10-20: A=4/4, B=12+20/32, C=3 ítems con bloqueos, D=13/13+archivo).

**Estado: retirada NO completada; veredicto final posponer hasta que el propietario ejecute `--fix-perms` + `--execute` y el paso E confirme recuperabilidad total.** OpenCode no ejecuta borrados.

Comandos de continuación (propietario, en orden):
```bash
bash /media/agustin/Almacenamiento/Facultad/TALOS/manifests/talos-reanudacion-retirada.sh --fix-perms
bash /media/agustin/Almacenamiento/Facultad/TALOS/manifests/talos-reanudacion-retirada.sh --execute
```

## Pendientes del propietario / siguientes fases (post-preflight)

1. Ejecutar el comando de retirada de orígenes (arriba).
2. Rotar/revocar el access token del remoto GitLab (remoto ya obsoleto) y sanitizar `git remote` sin alterar historia ni ramas.
3. Decidir canonicalización de las 2 copias del piloto Colab dentro del plan de integración (no romper los inputs divergentes).
4. Pendientes de fases previas: integración del piloto al repo, corrida registrada de la suite T, adjudicación de la corrida del quality gate P1.2 con la captura `e9af1327` (ahora en `Facultad/TALOS/historical-evidence/B06/`).
