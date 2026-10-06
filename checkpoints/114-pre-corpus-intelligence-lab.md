# CP114-PRE v4 / v4.1 / v4.2 — Diseño, Revisión y Endurecimiento del Corpus Intelligence Lab

**Tipo:** Auditoría de Arquitectura de Datos + Endurecimiento de Laboratorio Multi-Candidato Pre-Colab  
**Subdominio:** Corpus Intelligence / Ingestión Pre-V1  
**Precondición:** CP113-R1 = PASS / CLOSED  
**Gate B:** C1–C5 = PASS / CLOSED  
**Integridad de Datos:** `DATABASE_CHANGES = 0`  
- `BASELINE_KNOWLEDGE_DB_SHA256 = fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1` (`data/web_state/knowledge_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_VECTOR_DB_SHA256    = 013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f` (`data/web_state/vector_store.db` READ-ONLY / UNCHANGED)  
- `BASELINE_GIT_COMMIT          = f81134fc2293916210d53c8065f3a0049e52b0b4`  
- `BASELINE_DATE                = 2026-10-02T19:24:19-03:00`  
**Estado Operacional:**  
- `COLAB_EXECUTION = NOT_EXECUTED (Pendiente de ejecución por el usuario)`  
- `PRODUCTION_MUTATION = FORBIDDEN`  
- `PRODUCTION_MIGRATION = NOT_IMPLEMENTED / NOT_EXECUTED`  
- `PILOT_STAGE = READY_FOR_EXPLICIT_USER_EXECUTION`  
- `CP114_PRE_V4_2_VERDICT = PASS / READY_FOR_COLAB`  

---

## 0. Resumen Ejecutivo y Marco Arquitectónico

El presente ciclo concluye el **diseño arquitectónico (v4)** y la **auditoría de consistencia normativa pre-Colab (v4.1)** del nuevo **Corpus Intelligence Pipeline** de TALOS, tras haber demostrado empíricamente en CP114-PRE v3 que la ingesta productiva previa (`pypdf` plano $\to$ micro-segmentación de 500 chars) genera una representación documental severamente degradada (0% tablas, 0% jerarquía AST, mutilación de palabras y sub-llenado del 80% en los embeddings).

### Principio Rector de Separación
```text
┌────────────────────────────────────────────────────────────────────────┐
│                        ARQUITECTURA TRI-PARTITA                        │
├──────────────────────────┬─────────────────────────┬───────────────────┤
│ 1. CORPUS PROCESSING     │ 2. CORPUS AUTHORITY     │ 3. CORPUS STORAGE │
│    (Cómputo Pesado)      │    (Gobernanza Epistémica│    (Persistencia) │
├──────────────────────────┼─────────────────────────┼───────────────────┤
│ • Extracción de Layout   │ • Custodia de PDFs RAW  │ • Bundle inter-   │
│ • Parsing AST            │ • Hashes criptográficos │   medio en disco  │
│ • Tablas (TableFormer)   │ • Asociación Curricular │ • Almacén canó-   │
│ • Semantic Chunking      │ • Control de Citas C1   │   nico en SQLite  │
│ • Embeddings Qwen/BGE    │ • Validación de Gate    │   (local seguro)  │
│                          │ • Aprobación Humana     │                   │
├──────────────────────────┼─────────────────────────┼───────────────────┤
│ Entorno: Google Colab    │ Entorno: TALOS Local PC │ Entorno: Local    │
│ (GPU T4 / Epímero)       │ (Soberanía y Decisión)  │ (ACID & FTS5)     │
└──────────────────────────┴─────────────────────────┴───────────────────┘
```

> `COLAB puede procesar. TALOS decide qué aceptar. SQLite conserva lo aceptado.`

---

## 1. Adjudicación y Correcciones Normativas de CP114-PRE v4.1

En la revisión de consistencia v4.1 se corrigieron diez (10) inconsistencias normativas antes de cualquier interacción con Google Colab:

1. **Protocolo Transaccional Multi-Base:**  
   Se corrigió la afirmación técnicamente incorrecta de una "única transacción SQLite ACID" entre dos bases independientes. Se formalizó el protocolo **Staged Two-Phase Multi-Base** (`VALIDATE -> STAGE -> PREPARE -> COMMIT/REPLACE -> VERIFY`) con snapshots `.bak` y reversión automática.
2. **Desacoplamiento Estricto del Gate:**  
   Se separó la validación técnica (`TECHNICAL_VALIDATION = PASS/FAIL`) de la soberanía de decisión humana (`HUMAN_ACCEPTANCE = ACCEPTED/REJECTED`). Un delta positivo en métricas o retrieval no autoriza automáticamente la ingesta.
3. **Reclasificación de Umbrales Arbitrarios:**  
   Se retiraron del gate normativo los thresholds porcentuales ciegos ($\ge 90\%$, $\ge 95\%$) transformándolos en **métricas diagnósticas empíricas** (`table_structure_rate`, `heading_path_coverage`, `lexical_fragmentation_rate`).
4. **Preservación de la Taxonomía CP113-R1 de Retrieval:**  
   El benchmark comparativo evalúa por separado la cadena formal: $\text{Query} \to \text{Hit} \to \text{Relevant Evidence} \to \text{Sufficient Evidence} \to \text{Grounded Response}$.
5. **Estrategias de Chunking como Hipótesis Experimentales:**  
   El tamaño de 1.200–1.500 caracteres se reclasificó como Estrategia C (candidata experimental), a ser contrastada en Colab frente a la Estrategia A (baseline 500 chars), Estrategia B (~800 chars) y Estrategia D (~2.000 chars).
6. **Estandarización de Identidad y Provenance:**  
   Se adoptó la convención inmutable `document_id = "sha256:<64 hex>"` y `chunk_id = "<doc_id>:p<start>-<end>:c<index>"`. Se prohibieron los hashes truncados. Se formalizó la regla `bbox = null` cuando el extractor no emite coordenadas espaciales, prohibiendo inventar datos.
7. **Blindaje de Privacidad en `corpus_prepare.py`:**  
   Se incorporó una blacklist estricta para bloquear `.env`, `*.db`, `*.sqlite*`, `student_state`, tokens, claves y logs en el staging local.
8. **Normalización del Cuaderno Colab:**  
   `notebooks/corpus_intelligence_lab.ipynb` fue estructurado en 15 stages completos (0 a 14) con validación fail-closed de dependencias, advertencias claras sobre GPU y 100% de sintaxis Python validada por AST.

---

## 2. Artefactos Entregados y Auditados en el Repositorio

1. **Arquitectura del Pipeline:**
   - [`docs/CORPUS_INTELLIGENCE_ARCHITECTURE.md`](file:///media/agustin/Laboratorio/study-engie/docs/CORPUS_INTELLIGENCE_ARCHITECTURE.md)  
   Desacoplamiento tripartito, clasificación de especificaciones (Invariantes, Baseline e Hipótesis) y diagramas de flujo.
2. **Especificación del Formato de Bundle:**
   - [`docs/TALOS_CORPUS_BUNDLE_V1.md`](file:///media/agustin/Laboratorio/study-engie/docs/TALOS_CORPUS_BUNDLE_V1.md)  
   Contrato normativo `talos-corpus-bundle-v1`: responsabilidades ontológicas por archivo, estandarización de identificadores y política de `bbox = null`.
3. **Protocolo del Gate de Importación:**
   - [`docs/CORPUS_IMPORT_GATE.md`](file:///media/agustin/Laboratorio/study-engie/docs/CORPUS_IMPORT_GATE.md)  
   Protocolo fail-closed de 8 niveles, desacoplamiento técnico/humano y flujo staged coordinado multi-base.
4. **Script Local de Preparación y Staging con Blindaje:**
   - [`scripts/corpus_prepare.py`](file:///media/agustin/Laboratorio/study-engie/scripts/corpus_prepare.py)  
   CLI determinista con filtros de seguridad y privacidad para escaneo, deduplicación y preparación del piloto.
5. **Cuaderno Interactivo para Google Colab:**
   - [`notebooks/corpus_intelligence_lab.ipynb`](file:///media/agustin/Laboratorio/study-engie/notebooks/corpus_intelligence_lab.ipynb)  
   Cuaderno en 15 etapas estructuradas (Stage 0 a Stage 14) con extracción estructural, evaluación de estrategias A–D, vectorización y empaquetado.
6. **Informe Exhaustivo de Diseño:**
   - [`reports/corpus_intelligence_lab/CP114_PRE_V4_DESIGN.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP114_PRE_V4_DESIGN.md)
7. **Informe de Auditoría de Consistencia v4.1:**
   - [`reports/corpus_intelligence_lab/CP114_PRE_V4_1_AUDIT.md`](file:///media/agustin/Laboratorio/study-engie/reports/corpus_intelligence_lab/CP114_PRE_V4_1_AUDIT.md)

---

## 3. Selección del Piloto Representativo (3 Documentos)

1. **Pilot #1 — Sistemas Operativos y Control:**  
   `Operating Systems - Internals and Design Principles 7th.pdf` (William Stallings, 820 págs, ~6.8 MB).  
   *Características:* Tablas de control de procesos (PCBs, registros), jerarquía de secciones, texto denso y diagramas.
2. **Pilot #2 — Código y Algoritmos:**  
   `Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf` (Luis Joyanes Aguilar, 21 MB).  
   *Características:* Bloques de código C/C++, algoritmos, bucles anidados e indentación sintáctica.
3. **Pilot #3 — Unidad Modular de Benchmark:**  
   `prog_punteros.pdf` (FADENA, 61 KB).  
   *Características:* Unidad curricular acotada con correspondencia directa en el oráculo del benchmark canónico.

---

## 4. Protocolo Operativo para el Usuario (Paso a Paso)

### Paso 1: Preparación Local de Archivos
En la terminal local de la PC, ejecutar el script de preparación del piloto:
```bash
.venv/bin/python3 scripts/corpus_prepare.py --pilot --copy
```
*Efecto:* Crea el directorio local `corpus_upload/` con `manifest.json` y la carpeta `pdf/` conteniendo exclusivamente los 3 PDFs del piloto.

### Paso 2: Subida a Google Drive / Colab
Copiar la carpeta `corpus_upload/` a Google Drive en la ruta:
```text
Mi unidad / TALOS / corpus_upload /
```
*(O arrastrar `corpus_upload/` a `/content/corpus_upload` al iniciar la sesión de Colab).*

### Paso 3: Abrir y Ejecutar el Cuaderno en Google Colab
1. Abrir Google Colab y cargar:
   ```text
   notebooks/corpus_intelligence_lab.ipynb
   ```
2. Asignar aceleración: **Entorno de ejecución > Cambiar tipo de entorno de ejecución > T4 GPU**.
3. Seleccionar **Entorno de ejecución > Ejecutar todas (Run all)**.
4. El cuaderno procesará las 15 etapas de forma autónoma y empaquetará:
   ```text
   talos_corpus_bundle_<run_id>.zip
   ```

### Paso 4: Descarga y Notificación
Guardar el archivo `.zip` descargado en la ruta local:
```text
reports/corpus_intelligence_lab/
```
E informar a Antigravity:
```text
CORPUS_BUNDLE_READY
```

---

## 5. Estado Final del Checkpoint

```text
CP114_PRE_V4_2 = PASS / READY_FOR_COLAB

CURRENT_PRODUCTION = UNCHANGED
KNOWLEDGE_STORE_DB = UNCHANGED (fe53f3b4e1cd6e01effb5c9f38222636199955c027484f4ff15ed95f93d5b2b1)
VECTOR_STORE_DB    = UNCHANGED (013a2462e6de6ca7cf13443338e44b7795dce4b2f7f6117827bd2ccadd0c568f)

COLAB_EXECUTION    = NOT_EXECUTED (Esperando ejecución manual del usuario)
PDF_UPLOAD         = NOT_EXECUTED
PRODUCTION_IMPORT  = NOT_IMPLEMENTED / NOT_EXECUTED

CANDIDATE_STRATEGIES   = FULLY_PRESERVED (baseline, strategy_b, strategy_c, strategy_d)
AUTOMATIC_WINNER       = NONE (selection_status = NOT_SELECTED)
BENCHMARK_TAXONOMY     = CP113-R1_STRICT (Sin heurística léxica, sin score>=0.50 como adjudicación)
CORPUS_BUNDLE_CONTRACT = NORMALIZED_MULTI_CANDIDATE (talos-corpus-bundle-v1)
TALOS_IMPORT_GATE      = TECHNICALLY_CORRECT (8 Niveles Fail-Closed + Staged Multi-Base + Human Acceptance)
PRIVACY_GUARDS         = ENFORCED (.env y *.db estrictamente aislados)
PILOT                  = READY_FOR_EXPLICIT_USER_EXECUTION
```
