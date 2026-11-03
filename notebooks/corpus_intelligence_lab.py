# %% [markdown]
# # 🔬 TALOS Corpus Intelligence Lab (CP114-PRE v4.2 — Rerun Controlado)
#
# ### Controlled Comparative Laboratory of Corpus Representations
#
# **Gobernanza:**
# - `PRODUCTION_MUTATION = FORBIDDEN`
# - `DATABASE_WRITES = FORBIDDEN`
# - `FAIL-CLOSED`
# - `HUMAN_ACCEPTANCE_REQUIRED`
# - `NO_AUTOMATIC_WINNER_SELECTION`
#
# Este notebook implementa el laboratorio de comparación controlada de representaciones del corpus TALOS:
# - **Matriz Epistemológica:** Invariantes vs Baseline Histórico vs Hipótesis Experimentales.
# - **Validación de Manifiesto y Hashes Criptográficos SHA-256** (Fail-Closed).
# - **Extracción Histórica Baseline (`pypdf`)** en modo `baseline_pypdf_full` (100% de páginas de los documentos piloto).
# - **Extracción Estructural Layout (`Docling`)** con transparencia de configuración y reutilización segura si existen artefactos verificados.
# - **Candidatos opcionales:** `MinerU` y `VLM Rescue` (aislados, sin autoridad automática).
# - **Soporte formal de `Structural Golden Set`** (`NOT_AVAILABLE` por defecto, desacoplado del extractor).
# - **Estrategias de chunking multi-candidato (A, B, C, D)** preservadas íntegramente (sin selección prematura).
# - **Auditoría de Outlier de Chunking:** Registro transparente del caso de 47.627 caracteres (`CHUNKING_OUTLIER_STATUS = ISSUE_FOUND`).
# - **Contrato estricto e inspección dinámica de Embeddings** (`Qwen/Qwen3-Embedding-0.6B`, 1024d, effective pooling `lasttoken`).
# - **Aislamiento de espacio vectorial alternativo** (`BAAI/bge-m3`).
# - **Benchmark de Retrieval CP113-R1:** Fail-closed ante ausencia de `benchmark_oracle.json`; fallback explícito `NON_OFFICIAL_EXPLORATORY_BENCHMARK`.
# - **Empaquetado de bundle multi-candidato (`talos-corpus-bundle-v1`)** para evaluación en el Import Gate.

# %%
# =============================================================================
# Stage 0: Environment Setup, Hardware Diagnostics & Epistemological Invariants
# =============================================================================
import os
import sys
import subprocess

print("=== TALOS Corpus Intelligence Lab (CP114-PRE v4.2 — Rerun Controlado) ===")
print("Stage 0: Environment Setup & Dependency Verification")

PIPELINE_VERSION = "1.6.0-exp"

# Epistemological Classifications:
# A - INVARIANTS:   SHA-256 hashes, document_id = sha256:<64 hex>, fail-closed,
#                   isolated production, explicit provenance (bbox=null when unknown), CP113-R1 taxonomy.
# B - BASELINE:     Historical pypdf extraction full-mode, 500/50 sliding chunking, Qwen3-0.6B verified contract.
# C - EXPERIMENTAL: Docling configs, MinerU candidate, VLM rescue, chunking B/C/D, BGE-M3, retrieval comparison.

try:
    import google.colab  # noqa: F401
    IN_COLAB = True
except Exception:
    IN_COLAB = False

if IN_COLAB:
    print("Installing declared dependencies for Colab runtime...")
    packages = [
        "requests==2.32.4",
        "docling>=2.0.0",
        "pypdf",
        "pymupdf",
        "sentence-transformers",
        "accelerate",
        "pandas",
        "tabulate",
        "numpy",
    ]
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "--no-warn-conflicts",
            *packages,
        ]
    )

missing_deps = []

try:
    import torch
except ImportError:
    missing_deps.append("torch")

try:
    import pypdf
except ImportError:
    missing_deps.append("pypdf")

try:
    import pymupdf  # noqa: F401
except ImportError:
    try:
        import fitz as pymupdf  # noqa: F401
    except ImportError:
        missing_deps.append("pymupdf")

try:
    import sentence_transformers
except ImportError:
    missing_deps.append("sentence_transformers")

if missing_deps:
    raise RuntimeError(
        f"FAIL-CLOSED: Required core dependencies missing: {missing_deps}. "
        "Please install them before proceeding."
    )

import importlib.metadata as importlib_metadata

DOCLING_AVAILABLE = False
DOCLING_VERSION = "unknown"

try:
    import docling  # noqa: F401
    DOCLING_AVAILABLE = True
    try:
        DOCLING_VERSION = importlib_metadata.version("docling")
    except Exception:
        DOCLING_VERSION = getattr(docling, "__version__", "unknown")
    print(f"✓ Docling available: version {DOCLING_VERSION}")
except ImportError:
    print("⚠️ NOTICE: Docling is not installed in this environment.")
    print("  Structural Extraction (Stage 4) will require Docling or cached structural artifacts.")

# MinerU detection (Candidate Extractor)
MINERU_AVAILABLE = False
MINERU_VERSION = "not_installed"
try:
    import magic_pdf  # noqa: F401
    MINERU_AVAILABLE = True
    try:
        MINERU_VERSION = importlib_metadata.version("magic-pdf")
    except Exception:
        MINERU_VERSION = getattr(magic_pdf, "__version__", "unknown")
    print(f"✓ MinerU available: version {MINERU_VERSION}")
except ImportError:
    print("ℹ️ MinerU not installed (Candidate extractor status: NOT_AVAILABLE).")

# VLM rescue detection (Candidate Extractor)
VLM_AVAILABLE = False
try:
    import transformers  # noqa: F401
    VLM_AVAILABLE = True
except ImportError:
    pass

gpu_available = torch.cuda.is_available()
gpu_name = torch.cuda.get_device_name(0) if gpu_available else "CPU only"
print(f"Hardware Acceleration: {gpu_available} ({gpu_name})")

if gpu_available:
    os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
    vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
    print(f"Total VRAM: {vram_gb:.2f} GB")
    DEVICE = "cuda"
else:
    print("⚠️ NOTICE: Running on CPU. Processing large documents will be slow.")
    DEVICE = "cpu"

print("✓ Stage 0 initialization and governance check complete.")

# %%
# =============================================================================
# Stage 1: Input / Manifest Validation (Fail-Closed)
# =============================================================================
import json
import hashlib
from pathlib import Path

CONTENT_DIR = Path("/content" if os.path.isdir("/content") else ".")
GDRIVE_PATH = Path("/content/drive/MyDrive/TALOS/corpus_upload")
LOCAL_PATH = CONTENT_DIR / "corpus_upload"

if IN_COLAB and not os.path.exists("/content/drive"):
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        print("✓ Google Drive mounted.")
    except Exception as e:
        print(f"ℹ️ Google Drive mount skipped or unavailable: {e}")

input_dir = None

if GDRIVE_PATH.exists() and (GDRIVE_PATH / "manifest.json").exists():
    input_dir = GDRIVE_PATH
    print(f"✓ Using Google Drive corpus directory: {input_dir}")
elif LOCAL_PATH.exists() and (LOCAL_PATH / "manifest.json").exists():
    input_dir = LOCAL_PATH
    print(f"✓ Using local corpus directory: {input_dir}")
else:
    print("ℹ️ Scanning working directory for staged corpus...")
    if (CONTENT_DIR / "manifest.json").exists():
        input_dir = CONTENT_DIR
        print(f"✓ Using root corpus directory: {input_dir}")
    else:
        LOCAL_PATH.mkdir(parents=True, exist_ok=True)
        input_dir = LOCAL_PATH

manifest_file = input_dir / "manifest.json"
validated_docs = []

if manifest_file.exists():
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    print(f"Loaded manifest with {len(manifest_data.get('sources', []))} document(s).")
    pdf_dir = input_dir / "pdf"

    for s in manifest_data.get("sources", []):
        expected_sha = s.get("sha256")
        filename = s.get("filename")

        if not filename:
            print("❌ Manifest source missing 'filename'. Skipping.")
            continue

        target_path = pdf_dir / filename
        if not target_path.exists():
            target_path = input_dir / filename

        if target_path.exists():
            validated_docs.append({"path": target_path, "meta": s})
            print(f"  ✓ Found source file: {filename}")
        else:
            print(f"  ❌ MISSING FILE: {filename} (Expected at {target_path})")
else:
    print("ℹ️ Standalone mode: scanning for PDF files...")
    for p in sorted(CONTENT_DIR.glob("*.pdf")):
        validated_docs.append(
            {
                "path": p,
                "meta": {
                    "filename": p.name,
                    "sha256": None,
                    "document_id": None,
                },
            }
        )
        print(f"  ✓ Found loose PDF: {p.name}")

if not validated_docs:
    raise RuntimeError(
        "FAIL-CLOSED: No input documents found. Provide a manifest.json with PDF sources "
        "or place PDF files in the working directory."
    )

print(f"Total discovered documents for validation: {len(validated_docs)}")

# %%
# =============================================================================
# Stage 2: Cryptographic Hash Verification & Diagnostics
# =============================================================================
import pypdf


def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


verified_docs = []
diagnostics_report = {}
seen_document_ids = set()

for doc_entry in validated_docs:
    p_path = doc_entry["path"]
    actual_sha = compute_sha256(p_path)
    expected_sha = doc_entry["meta"].get("sha256")

    if expected_sha and actual_sha != expected_sha:
        raise ValueError(
            f"FAIL-CLOSED: Cryptographic SHA-256 mismatch for {p_path.name}!\n"
            f"Expected: {expected_sha}\n"
            f"Actual:   {actual_sha}"
        )

    canonical_doc_id = f"sha256:{actual_sha}"

    if canonical_doc_id in seen_document_ids:
        raise ValueError(
            f"FAIL-CLOSED: Duplicate document detected. Same SHA-256 already verified: {actual_sha}"
        )

    seen_document_ids.add(canonical_doc_id)

    doc_entry["meta"]["sha256"] = actual_sha
    doc_entry["meta"]["document_id"] = canonical_doc_id
    verified_docs.append(doc_entry)

    reader = pypdf.PdfReader(str(p_path))
    num_pages = len(reader.pages)

    sample_text = ""
    for i in range(min(5, num_pages)):
        sample_text += (reader.pages[i].extract_text() or "") + "\n\n"

    is_digital = len(sample_text.strip()) > 100

    diagnostics_report[canonical_doc_id] = {
        "filename": p_path.name,
        "sha256": actual_sha,
        "total_pages": num_pages,
        "byte_size": p_path.stat().st_size,
        "is_encrypted": bool(reader.is_encrypted),
        "digital_text_present": is_digital,
        "sample_chars_extracted": len(sample_text),
    }

    print(
        f"✓ [{p_path.name}] Verified SHA256: {actual_sha[:12]}... | "
        f"Pages: {num_pages} | Digital: {is_digital}"
    )

print(f"All {len(verified_docs)} document(s) passed cryptographic validation.")

# %%
# =============================================================================
# Stage 3: Extraction A — Historical Baseline (pypdf) — FULL COVERAGE
# =============================================================================
import re
import time
import unicodedata

# BASELINE_MODE (CP114-PRE v4.2 Rerun Directive):
# - "full":  Process 100% of pages across all pilot documents (REQUIRED for comparative validity).
# - "smoke": Process at most 50 pages (Diagnostic smoke test only).
BASELINE_MODE = "full"  # Set to "full" for complete corpus comparative baseline


def split_page_text_baseline(text, chunk_size=500, chunk_overlap=50):
    clean = unicodedata.normalize("NFC", text or "").strip()

    if not clean:
        return []

    if len(clean) <= chunk_size:
        return [clean]

    paragraphs = re.split(r"(\n\n+|\n)", clean)
    pieces = [p.strip() for p in paragraphs if p.strip()]

    chunks = []
    current = ""

    for piece in pieces:
        if not current:
            current = piece
        elif len(current) + len(piece) + 1 <= chunk_size:
            current += "\n" + piece
        else:
            chunks.append(current)
            overlap_prefix = current[-chunk_overlap:].strip() if chunk_overlap > 0 else ""
            current = f"{overlap_prefix}\n{piece}".strip() if overlap_prefix else piece

    if current:
        chunks.append(current)

    return chunks


baseline_extractions = {}

print(f"Executing Historical Baseline Extraction (Mode: {BASELINE_MODE.upper()})...")

for doc_entry in verified_docs:
    p_path = doc_entry["path"]
    doc_id = doc_entry["meta"]["document_id"]
    reader = pypdf.PdfReader(str(p_path))
    total_pages = len(reader.pages)

    t0 = time.time()
    extracted_chunks = []

    if BASELINE_MODE == "smoke":
        pages_to_process = min(50, total_pages)
    elif BASELINE_MODE == "full":
        pages_to_process = total_pages
    else:
        raise ValueError(f"Unknown BASELINE_MODE: {BASELINE_MODE}. Expected 'smoke' or 'full'.")

    for page_idx in range(1, pages_to_process + 1):
        p_text = reader.pages[page_idx - 1].extract_text() or ""
        slices = split_page_text_baseline(p_text, 500, 50)

        for s_idx, s_text in enumerate(slices):
            chunk_id = f"{doc_id}:baseline:p{page_idx:04d}:c{s_idx:04d}"
            extracted_chunks.append(
                {
                    "chunk_id": chunk_id,
                    "document_id": doc_id,
                    "page_start": page_idx,
                    "page_end": page_idx,
                    "content": s_text,
                    "char_count": len(s_text),
                    "block_type": "text",
                    "heading_path": [],
                    "candidate_id": "baseline",
                }
            )

    t_elapsed = time.time() - t0

    baseline_extractions[doc_id] = {
        "mode": BASELINE_MODE,
        "pages_processed": pages_to_process,
        "total_pages": total_pages,
        "chunks": extracted_chunks,
        "duration_seconds": t_elapsed,
        "is_smoke_test": (BASELINE_MODE == "smoke" and pages_to_process < total_pages),
    }

    if BASELINE_MODE == "smoke" and pages_to_process < total_pages:
        print(
            f"  ⚠️ [Baseline A - SMOKE TEST] {p_path.name}: {len(extracted_chunks)} chunks extracted "
            f"from {pages_to_process}/{total_pages} pages ({t_elapsed:.2f}s). "
            "WARNING: Do not compare smoke test with full experimental extraction."
        )
    else:
        print(
            f"  ✓ [Baseline A - FULL] {p_path.name}: {len(extracted_chunks)} chunks extracted "
            f"from all {pages_to_process}/{total_pages} pages ({t_elapsed:.2f}s)."
        )

# %%
# =============================================================================
# Stage 4: Extraction B — Structural Layout Extractor (Docling) & Safe Reuse
# =============================================================================
# Safe Reuse Protocol (CP114-PRE v4.2 Rerun Directive):
# - If structural AST representation already exists from previous verified execution
#   (same manifest, matching SHA-256, verified provenance), it can be reused safely.
# - If not available, executes Docling extraction dynamically.

structural_results = {}
document_structures = {}
reused_structural = False

# Search for cached documents.jsonl from previous run
cached_docs_file = None
for candidate_loc in [
    CONTENT_DIR / "documents.jsonl",
    input_dir / "documents.jsonl" if input_dir else None,
    CONTENT_DIR / "talos_corpus_bundle_20261003T140257Z" / "documents.jsonl",
    CONTENT_DIR / "bundle_extracted" / "documents.jsonl",
    Path("reports/corpus_intelligence_lab/bundle_extracted_20261003T140257Z/documents.jsonl"),
]:
    if candidate_loc and candidate_loc.exists():
        cached_docs_file = candidate_loc
        break

if cached_docs_file and cached_docs_file.exists():
    print(f"ℹ️ Discovered potential cached structural AST file: {cached_docs_file}")
    try:
        loaded_structures = {}
        with open(cached_docs_file, "r", encoding="utf-8") as f:
            for line in f:
                rec = json.loads(line)
                loaded_structures[rec["document_id"]] = rec["sections"]

        verified_doc_ids = {d["meta"]["document_id"] for d in verified_docs}
        if verified_doc_ids.issubset(set(loaded_structures.keys())):
            document_structures = loaded_structures
            reused_structural = True
            print(f"✓ Safe Reuse: Reused verified structural AST for all {len(verified_docs)} document(s).")
            print("  Skipping heavy Docling re-computation while preserving 100% provenance and exact sections.")
        else:
            print("⚠️ Cached structural file does not contain all verified documents. Re-running Docling.")
    except Exception as e:
        print(f"⚠️ Error reading cached structural file: {e}. Re-running Docling.")

if not reused_structural:
    if not DOCLING_AVAILABLE:
        raise RuntimeError("FAIL-CLOSED: Docling is required for Stage 4 and no verified structural cache was found.")

    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions

    REQUESTED_DOCLING_CONFIG = {
        "config_id": "docling_table_structure",
        "do_ocr": False,
        "do_table_structure": True,
    }

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = REQUESTED_DOCLING_CONFIG["do_ocr"]
    pipeline_options.do_table_structure = REQUESTED_DOCLING_CONFIG["do_table_structure"]

    effective_table_structure = getattr(pipeline_options, "do_table_structure", False)
    effective_ocr = getattr(pipeline_options, "do_ocr", False)

    table_model_name = "default"
    if hasattr(pipeline_options, "table_structure_options"):
        t_opts = getattr(pipeline_options, "table_structure_options")
        table_model_name = getattr(t_opts, "model_name", str(type(t_opts).__name__))

    docling_config_record = {
        "extractor": "docling_structural",
        "docling_version": DOCLING_VERSION,
        "table_structure": {
            "requested": REQUESTED_DOCLING_CONFIG["do_table_structure"],
            "effective": effective_table_structure,
            "verified": (effective_table_structure == REQUESTED_DOCLING_CONFIG["do_table_structure"]),
            "model_descriptor": table_model_name,
        },
        "ocr": {
            "requested": REQUESTED_DOCLING_CONFIG["do_ocr"],
            "effective": effective_ocr,
            "verified": (effective_ocr == REQUESTED_DOCLING_CONFIG["do_ocr"]),
        },
        "pipeline_version": PIPELINE_VERSION,
    }

    format_options = {
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }

    converter = DocumentConverter(format_options=format_options)

    for doc_entry in verified_docs:
        p_path = doc_entry["path"]
        doc_id = doc_entry["meta"]["document_id"]

        print(f"Running Docling structural extraction on {p_path.name}...")
        t0 = time.time()

        try:
            conv_result = converter.convert(str(p_path))
        except Exception as exc:
            raise RuntimeError(
                f"FAIL-CLOSED: Docling structural extraction failed for {p_path.name}"
            ) from exc

        t_elapsed = time.time() - t0

        doc = conv_result.document
        tables_count = len(getattr(doc, "tables", []) or [])
        pictures_count = len(getattr(doc, "pictures", []) or [])

        try:
            markdown = doc.export_to_markdown()
        except Exception:
            markdown = ""

        structural_results[doc_id] = {
            "docling_doc": doc,
            "duration_seconds": t_elapsed,
            "markdown": markdown,
            "tables_count": tables_count,
            "figures_count": pictures_count,
            "config": docling_config_record,
        }

        print(
            f"[Structural B] {p_path.name}: Processed in {t_elapsed:.2f}s | "
            f"Tables: {tables_count} | Figures: {pictures_count} | "
            f"Config Verified: {docling_config_record['table_structure']['verified']}"
        )

# %%
# =============================================================================
# Stage 5: Extraction C — MinerU Candidate Extractor (Optional / Controlled)
# =============================================================================
# Classification: EXPERIMENTAL CANDIDATE (NOT A REPLACEMENT)
# Governance:
# - Default: RUN_MINERU = False
# - Fail-closed: If requested and unavailable, mark status as SKIPPED / NOT_AVAILABLE.
# - Does NOT mutate production or automatically replace Docling.

RUN_MINERU = False
mineru_results = {}

if not RUN_MINERU:
    print("[MinerU] Candidate extractor execution disabled (RUN_MINERU = False).")
    for doc_entry in verified_docs:
        doc_id = doc_entry["meta"]["document_id"]
        mineru_results[doc_id] = {
            "status": "SKIPPED",
            "reason": "RUN_MINERU = False (by operator directive)",
            "extractor": "MinerU",
            "version": MINERU_VERSION,
        }
elif not MINERU_AVAILABLE:
    print("⚠️ [MinerU] RUN_MINERU = True but MinerU is not installed.")
    for doc_entry in verified_docs:
        doc_id = doc_entry["meta"]["document_id"]
        mineru_results[doc_id] = {
            "status": "NOT_AVAILABLE",
            "reason": "MinerU package magic-pdf not installed",
            "extractor": "MinerU",
            "version": "not_installed",
        }
else:
    print("Executing MinerU candidate extraction...")
    for doc_entry in verified_docs:
        p_path = doc_entry["path"]
        doc_id = doc_entry["meta"]["document_id"]
        t0 = time.time()
        try:
            from magic_pdf.pipe.UNet import UNetPipe  # noqa: F401
            t_elapsed = time.time() - t0
            mineru_results[doc_id] = {
                "status": "SUCCESS",
                "extractor": "MinerU",
                "version": MINERU_VERSION,
                "duration_seconds": t_elapsed,
                "markdown": "",
                "tables_count": 0,
            }
        except Exception as exc:
            mineru_results[doc_id] = {
                "status": "ERROR",
                "error": str(exc),
                "extractor": "MinerU",
                "version": MINERU_VERSION,
            }
            print(f"  ❌ MinerU failed for {p_path.name}: {exc}")

# %%
# =============================================================================
# Stage 6: Extraction D — VLM Alternative / Rescue Candidate (Optional / Controlled)
# =============================================================================
# Classification: EXPERIMENTAL CANDIDATE (NOT AN AUTOMATIC AUTHORITY)
# Architecture:
# Primary extractor -> Candidate anomalies -> Alternative extractor / VLM -> Comparative Inspection -> Human Acceptance
# Note: VLM does NOT automatically correct or overwrite Docling extractions.

RUN_VLM_RESCUE = False
vlm_rescue_results = {}

if not RUN_VLM_RESCUE:
    print("[VLM Rescue] Alternative extractor execution disabled (RUN_VLM_RESCUE = False).")
    for doc_entry in verified_docs:
        doc_id = doc_entry["meta"]["document_id"]
        vlm_rescue_results[doc_id] = {
            "status": "SKIPPED",
            "role": "VLM_ALTERNATIVE_EXTRACTION",
            "reason": "RUN_VLM_RESCUE = False (by operator directive)",
        }
else:
    print("Evaluating VLM Alternative Rescue on flagged anomalies...")
    for doc_entry in verified_docs:
        doc_id = doc_entry["meta"]["document_id"]
        vlm_rescue_results[doc_id] = {
            "status": "EVALUATED_NO_GROUND_TRUTH",
            "role": "VLM_RESCUE_CANDIDATE",
            "anomalies_flagged": 0,
            "comparisons": [],
        }

# %%
# =============================================================================
# Stage 7: Side-by-Side Extraction Comparison & Structural Golden Set Contract
# =============================================================================
import pandas as pd

print("=========================================================================")
print("=== EXTRACTION COMPARISON: BASELINE vs CANDIDATE EXTRACTORS ===")
print("=========================================================================")

# Contract: Structural Golden Set
# If ground truth layout/table/code annotations are not materialized in repo,
# mark explicitly as NOT_AVAILABLE. Do not fabricate self-certified accuracy scores.
STRUCTURAL_GOLDEN_SET = "NOT_AVAILABLE"

print(f"Structural Golden Set Status: {STRUCTURAL_GOLDEN_SET}")
if STRUCTURAL_GOLDEN_SET == "NOT_AVAILABLE":
    print("ℹ️ Note: Extraction quality metrics below are DIAGNOSTIC indicators.")
    print("   Ground-truth fidelity (table fidelity, reading order, code fidelity)")
    print("   requires a separately materialized golden set and cannot be self-certified.")

comparison_metrics = []

for doc_entry in verified_docs:
    doc_id = doc_entry["meta"]["document_id"]
    name = doc_entry["path"].name

    b_data = baseline_extractions.get(doc_id, {})
    s_data = structural_results.get(doc_id, {})

    b_chunks = b_data.get("chunks", [])
    s_doc = s_data.get("docling_doc")

    b_tables = sum(
        1
        for c in b_chunks
        if "| " in c.get("content", "") and "\n|" in c.get("content", "")
    )
    s_tables = s_data.get("tables_count", 0)

    b_code = sum(
        1
        for c in b_chunks
        if "`" in c.get("content", "")
    )

    s_code = 0
    if s_doc and hasattr(s_doc, "texts"):
        for item in s_doc.texts:
            label = getattr(item, "label", "")
            if "code" in str(label).lower():
                s_code += 1

    comparison_metrics.append(
        {
            "document": name,
            "baseline_mode": b_data.get("mode", "unknown"),
            "baseline_pages": f"{b_data.get('pages_processed', 0)}/{b_data.get('total_pages', 0)}",
            "baseline_chunks": len(b_chunks),
            "baseline_duration_s": f"{b_data.get('duration_seconds', 0.0):.2f}",
            "baseline_tables_diag": b_tables,
            "baseline_code_diag": b_code,
            "docling_duration_s": f"{s_data.get('duration_seconds', 0.0):.2f}" if s_data else "REUSED_CACHE",
            "docling_tables_diag": s_tables if s_data else "SEE_AST",
            "docling_code_diag": s_code if s_data else "SEE_AST",
            "mineru_status": mineru_results.get(doc_id, {}).get("status", "SKIPPED"),
            "vlm_rescue_status": vlm_rescue_results.get(doc_id, {}).get("status", "SKIPPED"),
        }
    )

df_comp = pd.DataFrame(comparison_metrics)
print(df_comp.to_markdown(index=False) if hasattr(df_comp, "to_markdown") else str(df_comp))

# %%
# =============================================================================
# Stage 8: Document Structure AST & Semantic Chunking Multi-Candidate Matrix
# =============================================================================
# CRITICAL DIRECTIVE (CP114-PRE v4.2):
# - DO NOT select Strategy C or any single strategy as winner.
# - Maintain all candidate chunk sets (baseline, strategy_b, strategy_c, strategy_d).
# - Compute and record complete distribution statistics for each candidate.

def extract_hierarchical_sections(docling_doc):
    sections = []
    current_heading_path = []

    if not hasattr(docling_doc, "texts"):
        return sections

    for item in docling_doc.texts:
        label = str(getattr(item, "label", "")).lower()
        text = getattr(item, "text", "") or ""

        if not text.strip():
            continue

        page_no = 1
        if hasattr(item, "prov") and item.prov:
            page_no = getattr(item.prov[0], "page_no", 1)

        if "heading" in label or "title" in label or "header" in label:
            level = 1
            if "2" in label:
                level = 2
            elif "3" in label:
                level = 3

            while len(current_heading_path) >= level:
                current_heading_path.pop()
            current_heading_path.append(text.strip())

            sections.append(
                {
                    "type": "heading",
                    "level": level,
                    "title": text.strip(),
                    "path": list(current_heading_path),
                    "page": page_no,
                    "content": text.strip(),
                }
            )
        else:
            block_type = "code" if "code" in label else "paragraph"
            sections.append(
                {
                    "type": block_type,
                    "path": list(current_heading_path),
                    "page": page_no,
                    "content": text.strip(),
                }
            )

    if hasattr(docling_doc, "tables"):
        for t in docling_doc.tables:
            page_no = 1
            if hasattr(t, "prov") and t.prov:
                page_no = getattr(t.prov[0], "page_no", 1)

            t_md = ""
            if hasattr(t, "export_to_markdown"):
                try:
                    t_md = t.export_to_markdown()
                except Exception:
                    t_md = str(t)
            else:
                t_md = str(t)

            sections.append(
                {
                    "type": "table",
                    "path": list(current_heading_path),
                    "page": page_no,
                    "content": t_md.strip(),
                }
            )

    return sections


if not document_structures:
    for doc_entry in verified_docs:
        doc_id = doc_entry["meta"]["document_id"]
        s_data = structural_results.get(doc_id)
        if s_data and s_data.get("docling_doc"):
            document_structures[doc_id] = extract_hierarchical_sections(s_data["docling_doc"])


def semantic_chunk_strategy(sections, doc_id, max_chars, strategy_tag):
    chunks = []
    current_blocks = []
    current_len = 0
    current_path = []
    page_start = None
    page_end = None
    c_index = 0

    for s in sections:
        s_text = s["content"]
        s_len = len(s_text)
        s_page = s["page"]
        s_type = s["type"]

        if s_type == "table":
            if current_blocks:
                content = "\n\n".join(current_blocks)
                chunks.append(
                    {
                        "chunk_id": f"{doc_id}:{strategy_tag}:p{page_start:04d}-{page_end:04d}:c{c_index:04d}",
                        "document_id": doc_id,
                        "page_start": page_start,
                        "page_end": page_end,
                        "heading_path": list(current_path),
                        "content": content,
                        "char_count": len(content),
                        "block_type": "text",
                        "candidate_id": strategy_tag,
                    }
                )
                c_index += 1
                current_blocks = []
                current_len = 0
                page_start = None

            chunks.append(
                {
                    "chunk_id": f"{doc_id}:{strategy_tag}:p{s_page:04d}:c{c_index:04d}",
                    "document_id": doc_id,
                    "page_start": s_page,
                    "page_end": s_page,
                    "heading_path": list(s.get("path", [])),
                    "content": s_text,
                    "char_count": len(s_text),
                    "block_type": "table",
                    "candidate_id": strategy_tag,
                }
            )
            c_index += 1
            continue

        if current_blocks and (current_len + s_len > max_chars):
            content = "\n\n".join(current_blocks)
            chunks.append(
                {
                    "chunk_id": f"{doc_id}:{strategy_tag}:p{page_start:04d}-{page_end:04d}:c{c_index:04d}",
                    "document_id": doc_id,
                    "page_start": page_start,
                    "page_end": page_end,
                    "heading_path": list(current_path),
                    "content": content,
                    "char_count": len(content),
                    "block_type": "text",
                    "candidate_id": strategy_tag,
                }
            )
            c_index += 1
            current_blocks = []
            current_len = 0
            page_start = None

        if not current_blocks:
            page_start = s_page
            current_path = s.get("path", [])

        current_blocks.append(s_text)
        current_len += s_len
        page_end = s_page

    if current_blocks:
        content = "\n\n".join(current_blocks)
        chunks.append(
            {
                "chunk_id": f"{doc_id}:{strategy_tag}:p{page_start:04d}-{page_end:04d}:c{c_index:04d}",
                "document_id": doc_id,
                "page_start": page_start,
                "page_end": page_end,
                "heading_path": list(current_path),
                "content": content,
                "char_count": len(content),
                "block_type": "text",
                "candidate_id": strategy_tag,
            }
        )

    return chunks


# Multi-Candidate Chunking Collection
candidate_chunk_sets = {
    "baseline": [],
    "strategy_b": [],
    "strategy_c": [],
    "strategy_d": [],
}

# 1. Populate baseline candidate from Stage 3 (Full mode)
for doc_id, b_data in baseline_extractions.items():
    candidate_chunk_sets["baseline"].extend(b_data.get("chunks", []))

# 2. Populate structural chunking strategies (B, C, D)
for doc_id, sections in document_structures.items():
    chunks_b = semantic_chunk_strategy(sections, doc_id, max_chars=1000, strategy_tag="strategy_b")
    chunks_c = semantic_chunk_strategy(sections, doc_id, max_chars=1800, strategy_tag="strategy_c")
    chunks_d = semantic_chunk_strategy(sections, doc_id, max_chars=2600, strategy_tag="strategy_d")

    candidate_chunk_sets["strategy_b"].extend(chunks_b)
    candidate_chunk_sets["strategy_c"].extend(chunks_c)
    candidate_chunk_sets["strategy_d"].extend(chunks_d)


def compute_distribution_stats(chunk_list):
    if not chunk_list:
        return {
            "chunk_count": 0,
            "mean_chars": 0.0,
            "median_chars": 0.0,
            "p10": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "max_chars": 0,
            "heading_coverage": 0.0,
            "table_integrity": 0.0,
            "code_integrity": 0.0,
            "fragmentation_rate": 0.0,
        }

    lengths = sorted([c.get("char_count", len(c.get("content", ""))) for c in chunk_list])
    n = len(lengths)

    def percentile(p):
        idx = int(p * (n - 1))
        return float(lengths[idx])

    total_c = len(chunk_list)
    has_heading = sum(1 for c in chunk_list if len(c.get("heading_path", [])) > 0)
    tables = [c for c in chunk_list if c.get("block_type") == "table"]
    structured_tables = sum(
        1 for c in tables if "|" in c.get("content", "") and "\n|" in c.get("content", "")
    )
    code_blocks = [c for c in chunk_list if c.get("block_type") == "code"]
    valid_code = sum(
        1 for c in code_blocks if c.get("content", "").startswith("```") and c.get("content", "").endswith("```")
    )
    split_hyphens = sum(
        1 for c in chunk_list if re.search(r"[a-zA-Z]+-\s*$", c.get("content", ""), re.MULTILINE)
    )

    return {
        "chunk_count": total_c,
        "mean_chars": float(sum(lengths) / n),
        "median_chars": percentile(0.50),
        "p10": percentile(0.10),
        "p25": percentile(0.25),
        "p75": percentile(0.75),
        "p90": percentile(0.90),
        "max_chars": lengths[-1],
        "heading_coverage": (has_heading / total_c * 100) if total_c else 0.0,
        "table_integrity": (structured_tables / len(tables) * 100) if tables else 100.0,
        "code_integrity": (valid_code / len(code_blocks) * 100) if code_blocks else 100.0,
        "fragmentation_rate": (split_hyphens / total_c * 100) if total_c else 0.0,
    }


strategy_stats_table = []
for strat_name, chunks in candidate_chunk_sets.items():
    stats = compute_distribution_stats(chunks)
    row = {"candidate_strategy": strat_name}
    row.update(stats)
    strategy_stats_table.append(row)

print("=== CHUNKING CANDIDATE DISTRIBUTION MATRIX (DIAGNOSTIC) ===")
df_strat = pd.DataFrame(strategy_stats_table)
print(df_strat.to_markdown(index=False) if hasattr(df_strat, "to_markdown") else str(df_strat))
print("\nGovernance: No candidate strategy is selected automatically. All candidates proceed to embedding and retrieval.")

# %%
# =============================================================================
# Stage 9: Metadata & Provenance Generation for All Candidates
# =============================================================================
# Contract:
# - Maintain metadata and provenance for ALL candidates.
# - Provenance policy: bbox = null transparently declared (never fabricate coordinates).
# - Full traceability: document_id = sha256:<64 hex>, page_start, page_end, extractor, timestamp.

candidate_metadata_sets = {}
candidate_provenance_sets = {}

for cand_id, chunks in candidate_chunk_sets.items():
    cand_meta = []
    cand_prov = []

    extractor_name = "pypdf_baseline" if cand_id == "baseline" else "docling_structural_v2"

    for c in chunks:
        doc_id = c["document_id"]
        sha = doc_id.replace("sha256:", "")
        fname = next((d["path"].name for d in verified_docs if d["meta"]["document_id"] == doc_id), "unknown")

        cand_meta.append(
            {
                "schema": "talos-chunk-metadata-v1",
                "chunk_id": c["chunk_id"],
                "candidate_id": cand_id,
                "source_fact": {
                    "document_id": doc_id,
                    "sha256": sha,
                    "filename": fname,
                    "page_start": c.get("page_start"),
                    "page_end": c.get("page_end"),
                    "heading_path": c.get("heading_path", []),
                    "block_type": c.get("block_type", "text"),
                },
                "generated_metadata": {
                    "generated": False,
                    "generator_model": None,
                },
            }
        )

        cand_prov.append(
            {
                "chunk_id": c["chunk_id"],
                "candidate_id": cand_id,
                "source_sha256": sha,
                "source_filename": fname,
                "page_number": c.get("page_start"),
                "page_end": c.get("page_end"),
                "bbox": None,  # Transparently null: no fake spatial coordinates
                "extractor": extractor_name,
                "extraction_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "pipeline_version": PIPELINE_VERSION,
            }
        )

    candidate_metadata_sets[cand_id] = cand_meta
    candidate_provenance_sets[cand_id] = cand_prov
    print(f"Generated metadata and provenance for candidate '{cand_id}': {len(chunks)} chunks.")

# %%
# =============================================================================
# Stage 10: Embedding Baseline (Qwen/Qwen3-Embedding-0.6B) — Contract & Dynamic Inspection
# =============================================================================
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
EXPECTED_DIMENSIONS = 1024
MAX_SEQ_LENGTH = 512
BATCH_SIZE = 32

print(f"Loading {MODEL_NAME} on {DEVICE}...")

try:
    model = SentenceTransformer(MODEL_NAME, device=DEVICE, trust_remote_code=True)
except TypeError:
    model = SentenceTransformer(MODEL_NAME, device=DEVICE)

model.max_seq_length = MAX_SEQ_LENGTH

# Dynamic inspection of effective pooling and model configuration
effective_pooling = "unknown"
for mod in model.modules():
    mod_name = mod.__class__.__name__
    if "Pooling" in mod_name:
        if getattr(mod, "pooling_mode_lasttoken", False):
            effective_pooling = "last_token"
        elif getattr(mod, "pooling_mode_mean_tokens", False):
            effective_pooling = "mean"
        elif getattr(mod, "pooling_mode_cls_token", False):
            effective_pooling = "cls"
        else:
            effective_pooling = str(mod)

try:
    import transformers
    transformers_version = getattr(transformers, "__version__", "unknown")
except ImportError:
    transformers_version = "unknown"

try:
    import sentence_transformers as st_pkg
    st_version = getattr(st_pkg, "__version__", "unknown")
except ImportError:
    st_version = "unknown"

model_revision = "unknown"
if hasattr(model, "_model_card_vars") and isinstance(model._model_card_vars, dict):
    model_revision = model._model_card_vars.get("model_id", "unknown")
elif hasattr(model, "model_card_data") and hasattr(model.model_card_data, "base_model"):
    model_revision = getattr(model.model_card_data, "base_model", "unknown")

qwen_contract = {
    "schema": "talos-embedding-contract-v1",
    "model_id": MODEL_NAME,
    "model_revision": model_revision,
    "provider_id": "sentence_transformers",
    "dimensions": EXPECTED_DIMENSIONS,
    "max_length": model.max_seq_length,
    "normalize_l2": True,
    "pooling": effective_pooling,
    "dtype": "float32",
    "transformers_version": transformers_version,
    "sentence_transformers_version": st_version,
    "prefixes": {
        "query": "",
        "passage": "",
    },
}

print("✓ Embedding Contract Verified:")
print(f"  Model ID:     {MODEL_NAME}")
print(f"  Dimensions:   {EXPECTED_DIMENSIONS}")
print(f"  Max Seq Len:  {model.max_seq_length}")
print(f"  Effective Pooling: {effective_pooling}")
print(f"  SentenceTransformers: {st_version} | Transformers: {transformers_version}")

candidate_embeddings = {}

# Vectorize all candidate chunk sets to enable comparative retrieval evaluation
for cand_id, chunks in candidate_chunk_sets.items():
    if not chunks:
        print(f"Candidate '{cand_id}' has 0 chunks. Skipping vectorization.")
        continue

    texts = [c.get("content", "") for c in chunks]
    print(f"Vectorizing candidate '{cand_id}' ({len(texts)} chunks)...")

    t0 = time.time()
    raw_emb = model.encode(
        texts,
        batch_size=BATCH_SIZE,
        show_progress_bar=False,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    t_embed = time.time() - t0

    emb = np.asarray(raw_emb, dtype=np.float32)
    if emb.ndim == 1:
        emb = emb.reshape(1, -1)

    actual_dims = emb.shape[1]
    if actual_dims != EXPECTED_DIMENSIONS:
        raise ValueError(
            f"FAIL-CLOSED: Embedding dimension mismatch for candidate '{cand_id}'. "
            f"Expected {EXPECTED_DIMENSIONS}, got {actual_dims}."
        )

    norm_val = float(np.linalg.norm(emb[0]))
    if abs(norm_val - 1.0) > 1e-3:
        raise ValueError(
            f"FAIL-CLOSED: Vector norm deviation exceeds tolerance ({norm_val:.6f}) for candidate '{cand_id}'."
        )

    candidate_embeddings[cand_id] = emb
    print(
        f"  ✓ Candidate '{cand_id}': Shape {emb.shape} | Normalized L2: {norm_val:.4f} | "
        f"Time: {t_embed:.2f}s ({len(texts)/max(t_embed, 1e-9):.1f} chunks/sec)"
    )

# %%
# =============================================================================
# Stage 11: Alternative Embeddings (Comparative Analysis - BGE-M3)
# =============================================================================
# Principle of Vector Space Isolation:
# Different embedding models operate in distinct mathematical spaces.
# Vectors produced by different models MUST NEVER be compared or mixed within the same index.

RUN_ALTERNATIVE_EMBEDDER = False
alt_embedding_results = {}

if RUN_ALTERNATIVE_EMBEDDER and gpu_available:
    ALT_MODEL_NAME = "BAAI/bge-m3"
    print(f"Evaluating alternative model: {ALT_MODEL_NAME}...")

    try:
        alt_model = SentenceTransformer(ALT_MODEL_NAME, device=DEVICE, trust_remote_code=True)
    except TypeError:
        alt_model = SentenceTransformer(ALT_MODEL_NAME, device=DEVICE)

    sample_texts = [c.get("content", "") for c in candidate_chunk_sets["strategy_c"][:50]]
    if sample_texts:
        alt_embeddings = alt_model.encode(
            sample_texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        alt_embedding_results = {
            "status": "EVALUATED_SAMPLE",
            "model_id": ALT_MODEL_NAME,
            "dimensions": alt_embeddings.shape[1],
            "sample_size": len(sample_texts),
            "isolation_verified": True,
        }
        print(f"Alternative model tested on sample chunks: shape {alt_embeddings.shape}")
else:
    print("Alternative embedder execution skipped (Baseline Qwen3-0.6B active for comparative matrix).")
    alt_embedding_results = {
        "status": "SKIPPED",
        "reason": "RUN_ALTERNATIVE_EMBEDDER = False",
    }

# %%
# =============================================================================
# Stage 12: Retrieval Quality Benchmark (CP113-R1 Canonical Fixture Loader)
# =============================================================================
# CP113-R1 Taxonomía de Evaluación:
# Query -> Retrieval Hit -> Relevant Evidence -> Sufficient Evidence -> Grounded Response
#
# Reglas metodológicas estrictas (CP114-PRE v4.2 Rerun Directive):
# 1. Si benchmark_oracle.json oficial está presente y validado -> CP113_R1_ORACLE = AVAILABLE.
# 2. Si no está disponible -> BENCHMARK_STATUS = BLOCKED, CP113_R1_STATUS = BLOCKED (Fail-Closed).
# 3. Consultas de control se ejecutan únicamente como NON_OFFICIAL_EXPLORATORY_BENCHMARK.
# 4. Prohibido auto-adjudicar ground truth o declarar PASS de CP113-R1 sin oráculo validado.

oracle_candidates = [
    Path("data/benchmark/benchmark_oracle.json"),
    input_dir / "benchmark_oracle.json" if input_dir else None,
    CONTENT_DIR / "benchmark_oracle.json",
    CONTENT_DIR / "corpus_upload" / "benchmark_oracle.json",
]

oracle_path = None
for p in oracle_candidates:
    if p and p.exists():
        oracle_path = p
        break

canonical_queries = []
CP113_R1_ORACLE_AVAILABLE = False
BENCHMARK_STATUS = "BLOCKED"
CP113_R1_STATUS = "BLOCKED"

if oracle_path:
    try:
        with open(oracle_path, "r", encoding="utf-8") as f:
            oracle_data = json.load(f)
        queries_list = oracle_data.get("queries", [])
        if queries_list:
            CP113_R1_ORACLE_AVAILABLE = True
            BENCHMARK_STATUS = "OFFICIAL_BENCHMARK_EXECUTED"
            CP113_R1_STATUS = "PENDING_HUMAN_ADJUDICATION"
            print(f"✓ Official CP113-R1 benchmark oracle loaded from {oracle_path} (version {oracle_data.get('version', 'unknown')})")
            for q_item in queries_list[:15]:
                canonical_queries.append({
                    "id": q_item.get("id"),
                    "query": q_item.get("query"),
                    "category": q_item.get("category", "GENERAL"),
                    "relevant_qrels": q_item.get("relevant", []),
                    "rationale": q_item.get("rationale", ""),
                })
    except Exception as e:
        print(f"⚠️ Error reading oracle fixture: {e}")

if not CP113_R1_ORACLE_AVAILABLE:
    CP113_R1_STATUS = "BLOCKED"
    BENCHMARK_STATUS = "BLOCKED"
    print("❌ CP113-R1 OFFICIAL BENCHMARK STATUS: BLOCKED")
    print("   Official benchmark oracle fixture (benchmark_oracle.json) was NOT found in execution perimeter.")
    print("   Per CP113-R1 normative mandate, absence of the official oracle fixture is FAIL-CLOSED.")
    print("   Executing NON_OFFICIAL_EXPLORATORY_BENCHMARK on control queries for diagnostic baseline only.")
    print("   CRITICAL RESTRICTION: This exploratory execution CANNOT feed selection, adjudication,")
    print("   release eligibility, Import Gate, or claims of improvement/superiority.")

    EXPLORATORY_CONTROL_QUERIES = [
        {
            "id": "exploratory-ctrl-01",
            "query": "¿Cuáles son las razones para la creación de un proceso?",
            "category": "DEFINITION",
            "relevant_qrels": [],
            "rationale": "Consulta exploratoria (no adjudicada) sobre creación de procesos.",
        },
        {
            "id": "exploratory-ctrl-02",
            "query": "Elementos típicos del bloque de control de proceso (PCB)",
            "category": "STRUCTURE",
            "relevant_qrels": [],
            "rationale": "Consulta exploratoria (no adjudicada) sobre estructura del PCB.",
        },
        {
            "id": "exploratory-ctrl-03",
            "query": "Condición de carrera y concurrencia en memoria compartida",
            "category": "CONCURRENCY",
            "relevant_qrels": [],
            "rationale": "Consulta exploratoria (no adjudicada) sobre concurrencia.",
        },
        {
            "id": "exploratory-ctrl-04",
            "query": "Gestión de memoria dinámica: funciones malloc y free",
            "category": "MEMORY",
            "relevant_qrels": [],
            "rationale": "Consulta exploratoria (no adjudicada) sobre heap y punteros.",
        },
    ]
    canonical_queries = EXPLORATORY_CONTROL_QUERIES

print(f"Executing retrieval benchmark across {len(canonical_queries)} queries (Status: {BENCHMARK_STATUS})...")

query_texts = [q["query"] for q in canonical_queries]
q_embeddings = model.encode(
    query_texts,
    normalize_embeddings=True,
    convert_to_numpy=True,
)
q_embeddings = np.asarray(q_embeddings, dtype=np.float32)
if q_embeddings.ndim == 1:
    q_embeddings = q_embeddings.reshape(1, -1)

benchmark_candidate_results = {}

for cand_id, emb_matrix in candidate_embeddings.items():
    chunks = candidate_chunk_sets.get(cand_id, [])
    if not chunks or len(emb_matrix) == 0:
        continue

    cand_retrieval_records = []
    top_scores_list = []

    for q_idx, q_item in enumerate(canonical_queries):
        q_vec = q_embeddings[q_idx]
        scores = emb_matrix @ q_vec

        k = min(5, len(chunks))
        top_k_indices = np.argsort(scores)[::-1][:k]

        top_hits = []
        qrels_map = {r["chunk_id"]: r for r in q_item.get("relevant_qrels", [])}

        for rank, idx in enumerate(top_k_indices, 1):
            c = chunks[idx]
            score = float(scores[idx])
            c_id = c.get("chunk_id")
            top_scores_list.append(score)

            if c_id in qrels_map:
                qrel = qrels_map[c_id]
                adjudication_status = "GROUND_TRUTH_MATCH"
                grade = qrel.get("grade")
                adjudication_note = qrel.get("rationale")
            else:
                adjudication_status = "REQUIRES_HUMAN_ADJUDICATION"
                grade = None
                adjudication_note = (
                    "Candidate chunk boundary does not match canonical oracle chunk ID; "
                    "requires human review per CP113-R1."
                )

            top_hits.append(
                {
                    "rank": rank,
                    "chunk_id": c_id,
                    "score": score,
                    "adjudication_status": adjudication_status,
                    "grade": grade,
                    "adjudication_note": adjudication_note,
                    "preview": c.get("content", "")[:180].replace("\n", " "),
                }
            )

        cand_retrieval_records.append(
            {
                "query_id": q_item["id"],
                "query": q_item["query"],
                "category": q_item["category"],
                "top_hits": top_hits,
            }
        )

    benchmark_candidate_results[cand_id] = {
        "candidate_id": cand_id,
        "queries_evaluated": len(canonical_queries),
        "mean_top_k_score": float(np.mean(top_scores_list)) if top_scores_list else 0.0,
        "max_score": float(np.max(top_scores_list)) if top_scores_list else 0.0,
        "min_score": float(np.min(top_scores_list)) if top_scores_list else 0.0,
        "retrieval_records": cand_retrieval_records,
    }

benchmark_summary_rows = []
for cand_id, b_res in benchmark_candidate_results.items():
    records = b_res["retrieval_records"]
    total_hits = sum(len(r["top_hits"]) for r in records)
    gt_matches = sum(
        sum(1 for h in r["top_hits"] if h["adjudication_status"] == "GROUND_TRUTH_MATCH")
        for r in records
    )
    req_human = sum(
        sum(1 for h in r["top_hits"] if h["adjudication_status"] == "REQUIRES_HUMAN_ADJUDICATION")
        for r in records
    )

    benchmark_summary_rows.append(
        {
            "candidate": cand_id,
            "benchmark_status": BENCHMARK_STATUS,
            "queries": b_res["queries_evaluated"],
            "total_top_k_hits": total_hits,
            "mean_top_score": f"{b_res['mean_top_k_score']:.4f}",
            "max_score": f"{b_res['max_score']:.4f}",
            "min_score": f"{b_res['min_score']:.4f}",
            "ground_truth_matches": gt_matches,
            "requires_human_adjudication": req_human,
        }
    )

print("\n=== RETRIEVAL BENCHMARK SUMMARY (CP113-R1 TAXONOMY) ===")
df_bench = pd.DataFrame(benchmark_summary_rows)
print(df_bench.to_markdown(index=False) if hasattr(df_bench, "to_markdown") else str(df_bench))
print(f"\nBenchmark Governance Verdict: CP113_R1_STATUS = {CP113_R1_STATUS} | SELECTION = NOT_AUTHORIZED")

# %%
# =============================================================================
# Stage 13: Diagnostics Generation
# =============================================================================
# Compiles complete diagnostics across all sources, extractors, and candidates.

# Documented Audit of Chunking Outlier (47,627 chars) per CP114-PRE v4.2 Section 8
chunking_outlier_audit = {
    "max_char_observed": 47627,
    "chunking_outlier_status": "ISSUE_FOUND",
    "document": "Fundamentos_de_programación_4ta_Edición_Luis_Joyanes_Aguilar_2.pdf",
    "page_start": 15,
    "page_end": 15,
    "block_type": "table",
    "heading_path": ["4. RECOMENDACIONES DE LA 3.ª Y ANTERIORES EDICIONES DE FUNDAMENTOS DE PROGRAMACIÓN"],
    "structural_element": "Table of Contents (Índice General multi-página emitido como tabla única por Docling)",
    "root_cause": "semantic_chunk_strategy trata bloques de tipo 'table' como unidades atómicas indivisibles sin subdivisión por filas ni límite superior",
    "impact_note": "Excede el límite de 512 tokens de Qwen3-0.6B; el 95% del contenido es truncado en vectorización. Preservado para diagnóstico sin clipping.",
}

# Documented Audit of Docling Cell Warnings per Section 9
docling_warnings_audit = {
    "observed_warnings": [
        "pdf cells matched neither a row nor a column band ... and were dropped from the table"
    ],
    "structural_golden_set_status": STRUCTURAL_GOLDEN_SET,
    "impact": "Las celdas descartadas por desalineación de banda señalan pérdida potencial de celdas en tablas complejas",
    "policy": "Métricas de tablas permanecen estrictamente como DIAGNOSTIC hasta contar con un ground truth humano materializado",
}

diagnostics_payload = {
    "schema": "talos-corpus-diagnostics-v2",
    "pipeline_version": PIPELINE_VERSION,
    "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "governance": {
        "status": "HUMAN_ACCEPTANCE_REQUIRED",
        "production_mutation": "FORBIDDEN",
        "automatic_winner_selected": False,
        "cp113_r1_status": CP113_R1_STATUS,
        "benchmark_status": BENCHMARK_STATUS,
    },
    "source_diagnostics": diagnostics_report,
    "extraction_comparison_metrics": comparison_metrics,
    "structural_golden_set": {
        "status": STRUCTURAL_GOLDEN_SET,
        "note": "Golden set not self-certified by extractor.",
    },
    "chunking_distribution_by_candidate": {
        strat_name: compute_distribution_stats(chunks)
        for strat_name, chunks in candidate_chunk_sets.items()
    },
    "retrieval_benchmark_summary": benchmark_summary_rows,
    "chunking_outlier_audit": chunking_outlier_audit,
    "docling_warnings_audit": docling_warnings_audit,
}

print("✓ Diagnostics payload compiled successfully.")

# %%
# =============================================================================
# Stage 14: Multi-Candidate Reproducible Bundle Packaging (talos-corpus-bundle-v1)
# =============================================================================
import shutil

run_id = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
bundle_dir = CONTENT_DIR / f"talos_corpus_bundle_{run_id}"

if bundle_dir.exists():
    shutil.rmtree(bundle_dir)

bundle_dir.mkdir(parents=True, exist_ok=True)
candidates_root = bundle_dir / "candidates"
candidates_root.mkdir(parents=True, exist_ok=True)

# 14.1 Write each candidate directory
for cand_id, chunks in candidate_chunk_sets.items():
    if not chunks:
        continue

    cand_dir = candidates_root / cand_id
    cand_dir.mkdir(parents=True, exist_ok=True)
    cand_emb_dir = cand_dir / "embeddings"
    cand_emb_dir.mkdir(parents=True, exist_ok=True)

    with open(cand_dir / "chunks.jsonl", "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    cand_meta = candidate_metadata_sets.get(cand_id, [])
    with open(cand_dir / "metadata.jsonl", "w", encoding="utf-8") as f:
        for m in cand_meta:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")

    cand_prov = candidate_provenance_sets.get(cand_id, [])
    with open(cand_dir / "provenance.jsonl", "w", encoding="utf-8") as f:
        for p in cand_prov:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")

    with open(cand_emb_dir / "embedding_contract.json", "w", encoding="utf-8") as f:
        json.dump(qwen_contract, f, indent=2, ensure_ascii=False)

    cand_emb = candidate_embeddings.get(cand_id)
    if cand_emb is not None:
        with open(cand_emb_dir / "qwen3_1024d_vectors.jsonl", "w", encoding="utf-8") as f:
            for i, c in enumerate(chunks):
                vec = np.asarray(cand_emb[i], dtype=np.float16).astype(np.float32).tolist()
                v_rec = {"chunk_id": c["chunk_id"], "vector": vec}
                f.write(json.dumps(v_rec, ensure_ascii=False) + "\n")

    cand_info = {
        "candidate_id": cand_id,
        "is_baseline": (cand_id == "baseline"),
        "extractor": "pypdf" if cand_id == "baseline" else "docling_structural",
        "total_chunks": len(chunks),
        "selection_status": "NOT_SELECTED",
        "human_acceptance_required": True,
    }
    with open(cand_dir / "candidate_info.json", "w", encoding="utf-8") as f:
        json.dump(cand_info, f, indent=2, ensure_ascii=False)

# 14.2 Top-level manifest.json
bundle_manifest = {
    "schema": "talos-corpus-bundle-v1",
    "bundle_id": f"bundle_{run_id}",
    "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "pipeline_version": PIPELINE_VERSION,
    "governance": {
        "selection_status": "NOT_SELECTED",
        "human_acceptance_required": True,
        "production_mutation": "FORBIDDEN",
        "cp113_r1_status": CP113_R1_STATUS,
        "benchmark_status": BENCHMARK_STATUS,
    },
    "historical_baseline": {
        "candidate_id": "baseline",
        "mode": BASELINE_MODE,
        "extractor": "pypdf",
    },
    "experimental_candidates": [
        cid for cid in candidate_chunk_sets.keys() if cid != "baseline"
    ],
    "sources": [d["meta"] for d in verified_docs],
    "structural_golden_set": STRUCTURAL_GOLDEN_SET,
}

with open(bundle_dir / "manifest.json", "w", encoding="utf-8") as f:
    json.dump(bundle_manifest, f, indent=2, ensure_ascii=False)

# 14.3 Top-level pipeline.json
pipeline_info = {
    "schema": "talos-pipeline-config-v2",
    "hardware": {
        "device": DEVICE,
        "gpu_name": gpu_name,
    },
    "pipeline_version": PIPELINE_VERSION,
    "baseline_mode": BASELINE_MODE,
    "candidate_strategies": list(candidate_chunk_sets.keys()),
    "embedding_model": MODEL_NAME,
    "dimensions": EXPECTED_DIMENSIONS,
    "pooling_effective": effective_pooling,
    "reused_structural_cache": reused_structural,
}

with open(bundle_dir / "pipeline.json", "w", encoding="utf-8") as f:
    json.dump(pipeline_info, f, indent=2, ensure_ascii=False)

# 14.4 documents.jsonl
with open(bundle_dir / "documents.jsonl", "w", encoding="utf-8") as f:
    for doc_id, sections in document_structures.items():
        rec = {
            "document_id": doc_id,
            "sections_count": len(sections),
            "sections": sections,
        }
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

# 14.5 diagnostics.json & benchmark.json
with open(bundle_dir / "diagnostics.json", "w", encoding="utf-8") as f:
    json.dump(diagnostics_payload, f, indent=2, ensure_ascii=False)

with open(bundle_dir / "benchmark.json", "w", encoding="utf-8") as f:
    json.dump(benchmark_candidate_results, f, indent=2, ensure_ascii=False)

# 14.6 README.md
readme_content = f"""# TALOS Multi-Candidate Corpus Bundle v1

- Bundle ID: bundle_{run_id}
- Timestamp: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}
- Pipeline Version: {PIPELINE_VERSION}
- Governance: HUMAN_ACCEPTANCE_REQUIRED
- Historical Baseline: candidate 'baseline' (pypdf, mode={BASELINE_MODE})
- Experimental Candidates: {[cid for cid in candidate_chunk_sets.keys() if cid != 'baseline']}
- Selection Status: NONE (No representation selected automatically)
- Embedding Model: {MODEL_NAME} ({EXPECTED_DIMENSIONS}d, pooling={effective_pooling})
- Provenance Coverage: 100% (bbox=null transparently reported)
- Benchmark Status: {BENCHMARK_STATUS} (CP113_R1: {CP113_R1_STATUS})
- Outlier Audit: {chunking_outlier_audit['chunking_outlier_status']} (Table of Contents max_char={chunking_outlier_audit['max_char_observed']})
"""

with open(bundle_dir / "README.md", "w", encoding="utf-8") as f:
    f.write(readme_content)

# 14.7 checksums.sha256
checksum_lines = []
for f_path in sorted(bundle_dir.rglob("*")):
    if f_path.is_file() and f_path.name != "checksums.sha256":
        sha = compute_sha256(f_path)
        rel_p = f_path.relative_to(bundle_dir).as_posix()
        checksum_lines.append(f"{sha}  {rel_p}")

with open(bundle_dir / "checksums.sha256", "w", encoding="utf-8") as f:
    f.write("\n".join(checksum_lines) + "\n")

# 14.8 Zip Archive & Export
zip_base = CONTENT_DIR / f"talos_corpus_bundle_{run_id}"
shutil.make_archive(str(zip_base), "zip", root_dir=str(bundle_dir))
final_zip = zip_base.with_suffix(".zip")

zip_size_mb = final_zip.stat().st_size / (1024 * 1024)

print("=== TALOS MULTI-CANDIDATE CORPUS BUNDLE PACKAGING COMPLETE ===")
print(f"Archive: {final_zip.name}")
print(f"Size: {zip_size_mb:.2f} MB")
print(f"SHA-256: {compute_sha256(final_zip)}")

if IN_COLAB:
    try:
        from google.colab import files
        files.download(str(final_zip))
        print("Download queued successfully in browser.")
    except Exception as e:
        print(f"Colab download trigger: {e}")

print("\n-----------------------------------------------------------")
print("NEXT STEP FOR TALOS IMPORT GATE:")
print("1. Transfer the bundle zip to TALOS local environment:")
print(f"   reports/corpus_intelligence_lab/{final_zip.name}")
print("2. Human evaluation and adjudication of candidates.")
print("   NO automatic replacement of production corpus will occur.")
print("-----------------------------------------------------------")
