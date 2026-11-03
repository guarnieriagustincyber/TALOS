# TALOS S1 — Consolidación del repositorio para publicación privada

**Directiva:** `TALOS-S1-GITHUB-CONSOLIDATION-01` · **Fecha:** 2026-11-03
**Estado:** `S1_READY_FOR_PRIVATE_PUBLICATION` (sin push: no hay remoto GitHub y la primera publicación requiere confirmación del propietario)

Este documento registra **qué se consolidó y qué quedó fuera**. No adjudica gates, metas, capacidad ni
release. La autoridad documental sigue siendo `docs/PROJECT_INDEX.md`; el estado de Meta 1 / Meta 2 no
se modifica aquí (ver `docs/recovery/2026-10-20-STRUCTURAL-RECOVERY-MANIFEST.md` §F). No duplica el
manifest estructural de 2026-10-20 ni el de migración Fase 3.

## 1. Identidad

| Campo | Valor |
|---|---|
| Repositorio local | `/media/agustin/Laboratorio/study-engie` |
| Rama de origen | `checkpoint/talos-v15-20261014` |
| HEAD de origen | `c358f95eee7ebaf7672f401b219dcd43152edabb` |
| Rama de consolidación | `checkpoint/talos-s1-consolidation` |
| Historial | 2310 commits, 13 ramas locales, 12 tags (`v0.2.0-rc1` … `v1.0.0`); historia intacta, sin rewrite |
| Remoto | `gitlab` (`gitlab.com/talos-grup2/talos.git`) — **sin credencial válida**; no existe remoto GitHub |

## 2. Inventario de componentes presentes

- **Backend:** `src/study_engine/` — 34 paquetes, 349 archivos `.py` rastreados. FastAPI, chat SSE,
  retrieval/ACL L3, auditoría NLI S4.4, pedagogía, sesiones, BKT/SM-2, storage SQLite/FTS, federación.
- **Frontend:** `kasiu-lab/ui/` (React/Vite) — 61 archivos en `src/`; `frontend` es symlink a ese árbol.
- **Configuración:** `config/` (`test_perimeter.json` 27 suites, `bkt_params.json`,
  `notebook_kc_catalog.json`, `l3_authorization_manifest.json`), `configs/`, `pyproject.toml`,
  `requirements*.txt|lock`, `setup.cfg`, `docker/`.
- **Tests:** `tests/` — 529 archivos `.py` rastreados, 27 suites de perímetro.
- **Scripts:** `scripts/` (`quality_gate.py`, `test.sh`, `verify_b1r_artifact.py`, `talos-sgrep`).
- **Notebooks en repo:** `data/colab/talos_reindex_colab.ipynb`, `scripts/talos_reindex_colab.ipynb`,
  `scripts/colab_embed_pending.ipynb`, `experiments/v1_5_phase1a2/colab/phase1a2_colab_runner.ipynb`,
  `notebooks/{corpus_intelligence_lab,cp116_benchmark_runner}.ipynb`.
- **Documentación:** `docs/` (138 archivos rastreados), `checkpoints/` CP001–CP154 (`index.md`),
  `AGENTS.md`, `README.md`, `PHASES.md`.
- **Total rastreado:** 3919 archivos.

## 3. Estado de Colab (sin fusionar, sin reconstruir)

| Artefacto | Ubicación | Estado |
|---|---|---|
| Resultados `TALOS_INGESTION_V4.1` | `fuentes/TALOS_INGESTION_V4.1_results.zip` (fuera de Git) | corrida del 2026-11-02, 22 contenidos, `final_receipt.json` con `bundle_hash 4e77ded3…804f`; SHA-256 del ZIP `3d8cb716…0136b` |
| Validación jerárquica V5.1.5 | `TALOS-COLAB-PILOT-01/resultados/evaluacion_v515_01_RESULTADOS.zip` (fuera de Git) | `toc/*_structure_v515.json`, `chapters_v515.json`, `chunk_links_v515.json`, `conflicts_v515.json`, `validation_{report,manifest}.json`; SHA-256 `a52f684c…02e18` |
| Runtime V5.1.8–V5.2.0 | `TALOS-COLAB-PILOT-01/resultados/talos_v51[6-9]_01.zip`, `talos_v520_01.zip` (fuera de Git) | v520 SHA-256 `11b8e84b…cb0c`; `canonical/`, `documents/`, `enhancements/` |
| Notebooks Colab | **solo externos**: `/media/agustin/Almacenamiento/Facultad/TALOS/experiments/colab/TALOS-COLAB-PILOT-01/notebooks/` (`TALOS_COLAB_A_AUTOMATICO.ipynb`, `TALOS_COLAB_B_POR_METODOS.ipynb`, `TALOS_COLAB_PILOT_01.ipynb`, `Untitled1.ipynb`) | copia divergente en `/media/agustin/Almacenamiento/Facultad/TALOS-COLAB-PILOT-01/` — **no fusionar** (C-6) |
| Estado documental V5 | `docs/ROADMAP_INTEGRAL_TALOS.md` §9.4 (V5.1.3) / §9.5 (V5.1.4 propuesta) | V5.1.3 `NOT_READY_FOR_PRODUCTIVE_RAG`; V5.1.4 `PROPOSED/EXPERIMENTAL/NOT_AUTHORIZED`; V5.1.5 no tiene registro documental en el repo |

Pendiente del propietario: incorporar de forma controlada los notebooks V5.1.5/V4.1 si son los
originales que produjeron esos ZIP. No se reconstruyeron desde conversaciones.

## 4. Documentación vigente vs histórica

Sin cambios de autoridad. Resumen operativo (fuente: `docs/PROJECT_INDEX.md` §0):

- **ACTIVA:** `AGENTS.md`, `README.md`, `PHASES.md`, `docs/PROJECT_INDEX.md`, `docs/CAPABILITY_MATRIX.md`,
  contratos de `docs/architecture/`, `docs/01-SPEC-V1.0.md`, `docs/04-DEVELOPMENT-SAFETY-POLICY.md`,
  `docs/05-CERTIFICATION-S4.4-V0.md`, `docs/07-STUDY-LOOP-SPECIFICATION-V1.0.md`,
  `docs/08-S7-TUTOR-POLICY-SPEC-V1.0.md`, `docs/B1R_ACCEPTANCE_CONTRACT.md`,
  `docs/TEST_CERTIFICATION_PERIMETER.md`.
- **HISTÓRICA:** `checkpoints/`, `reports/`, auditorías fechadas; consulta explícita.
- **UNKNOWN abiertos:** C-1…C-11 de `docs/PROJECT_INDEX.md` §5 sin resolver; C-7 (token GitLab) sigue
  accionado al owner.

## 5. Exclusiones (material que permanece fuera de Git)

| Ruta | Tamaño | Motivo |
|---|---|---|
| `.m1_01/` | 2,0 GB | `working*/{vector,knowledge}_store.db`, WAL y logs de servidor; evidencia preservada en `/media/agustin/Almacenamiento/Facultad/TALOS/m1-01-evidence-20261020/`; `PROJECT_INDEX` §4 ya declara que no se versiona |
| `.m1_02/`, `.m1_03/`, `.m1_04/`, `.m1_04b/`, `.m1_ep01/`, `.m1_ep02/`, `.m1_h2a/` | 12 MB | evidencia de corridas live (capturas, trazas, prompts) preservada en `.../TALOS/m1-*-evidence-*`; contiene prompts y salidas de proveedor |
| `TALOS-COLAB-PILOT-01/` | 534 MB | ZIP de resultados de ingesta (hasta 133 MB por archivo), derivados de PDF protegidos |
| `fuentes/` | 169 MB | fuentes bibliográficas y resultados de ingesta V4.1 (PDF y páginas renderizadas) |
| `drive_upload/` | 112 MB | staging de transporte hacia Drive/Colab |
| `data/`, `models/`, `artifacts/`, `reports/`, `tmp/`, `logs/`, `state/`, `.venv/` | ~3 GB | bases SQLite de alumno/estado, índices, corpus, modelos descargados, resultados y logs |
| `graphify-out/cache/`, `graphify-out/20*/`, `.rebuild.lock` | ~150 MB | caché y snapshots regenerables del grafo |
| `.env` | — | credenciales; `.env.example` (sin valores) permanece rastreado |
| `*.pdf`, `*.db`, `spa.traineddata` | — | PDF con restricciones, estado académico, modelo OCR |

`.gitignore` se amplió de forma incremental con `.m1_*/`, `.talos-fidelity-review/`,
`TALOS-COLAB-PILOT-01/`, `graphify-out/{cache,20*,.rebuild.lock}`. No se dejó de rastrear ningún
archivo ya versionado.

## 6. Riesgos pendientes

1. **Token GitLab embebido** en `remote.origin` de `.git/config` (`git remote -v` lo expone). No está en
   contenido rastreado ni en la historia; `git ls-remote` ya falla (token inválido/vencido). Requiere
   rotación por el owner y borrado de la URL con credencial antes de publicar en otro remoto.
2. **Tamaño del repositorio:** `.git` = 3,0 GB y 1806 archivos `graphify-out/` rastreados con
   `graph.json` de ~40 MB por snapshot histórico. No se purgó (prohibido rewrite). El primer push a
   GitHub será lento y puede tocar límites operativos del hosting.
3. **Binarios rastreados heredados:** `spa.traineddata` (17 MB, duplicado en `data/ocr/tessdata/`),
   `kasiu-lab/storage/covers/*.webp`, `mermaid.min.js`. Se conservan; no se limpiaron.
4. **Referencias documentales a artefactos fuera de Git:** `artifacts/performance/front_b_local_core_2026-10-29.json`,
   `artifacts/gates/gate_report_e4.md`, `.m1_*/…`. Válidas como referencia, no reconstruibles desde el repo.
5. **`graphify-out/`** queda modificado y sin commitear (artefacto regenerado). Su snapshot no acredita el
   HEAD; según `AGENTS.md` no es autoridad de implementación.
6. **Remoto GitHub inexistente**: no hay baseline remota. La publicación queda condicionada (ver §8).

## 7. Continuidad

- Checkpoints relevantes: `checkpoints/147-fase-1-sintesis-global-y-cierre-canonico.md`,
  `checkpoints/153-probe-1-cierre-canonico.md`, `checkpoints/154-p1-2-b06-capture-strategy-checkpoint.md`,
  `checkpoints/index.md` (CP001–CP154).
- Evidencia externa preservada: `/media/agustin/Almacenamiento/Facultad/TALOS/{historical-evidence,
  m1-*-evidence-*,manifests,experiments/colab}`.
- **Meta 1:** último estado documentado = `docs/recovery/2026-10-20-STRUCTURAL-RECOVERY-MANIFEST.md` §F
  (5 brechas; ninguna aceptación). Sin nueva adjudicación.
- **Meta 2:** mismo §F (T01–T20 incompleto/UNKNOWN, Fases 2–4 ABSENT, `PHASE_1_PROMOTABLE=FALSE`).
  Sin nueva adjudicación.
- **Discrepancias código ↔ documentación:** `docs/CAPABILITY_MATRIX.md` registra actualizaciones focales de
  octubre (F06, F25, F27) sobre HEAD `c358f95` + cambios locales; esas corridas no se re-ejecutaron en S1 y
  siguen siendo evidencia de su fecha, no del estado actual (`TEST_NOT_RUN_CURRENT`).

## 8. Condición para continuar al Paso 2

El Paso 2 (revisión integral de cierre) puede iniciarse sobre `checkpoint/talos-s1-consolidation`.
Antes de publicar se requiere: (a) confirmación explícita del owner para la primera publicación,
(b) decisión sobre el remoto (crear repositorio **privado** en GitHub conservando esta historia), y
(c) rotación del token GitLab (riesgo §6.1). Ninguna de las tres bloquea el trabajo local del Paso 2.
