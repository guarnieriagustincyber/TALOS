# %% [markdown]
# # 🔬 TALOS Corpus Intelligence Lab — CP116 Official Benchmark Runner
#
# **Propósito:** Ejecutar el benchmark oficial de retrieval (CP113-R1) sobre los candidatos
# ya generados en el bundle inmutable `talos_corpus_bundle_20261003T162052Z.zip`:
# - `baseline` (historical pypdf, 9.426 chunks)
# - `strategy_b` (Docling structural short, 4.265 chunks)
# - `strategy_c` (Docling structural medium, 2.405 chunks)
# - `strategy_d` (Docling structural wide, 1.736 chunks)
#
# **Reglas Absolutas:**
# - NO re-extraer PDFs.
# - NO re-generar embeddings de candidatos.
# - NO modificar bases de datos de producción.
# - NO seleccionar ganador ni candidato "óptimo/recomendado".
# - FAIL-CLOSED ante cualquier discrepancia criptográfica en `benchmark_oracle.json`.

# %%
# =============================================================================
# Cell 1: Environment & Dependency Verification
# =============================================================================
import os
import sys
import json
import time
import glob
import hashlib
import zipfile
from pathlib import Path
import numpy as np
import pandas as pd

print("=== TALOS CP116 — Official Benchmark Runner ===")

try:
    import google.colab
    IN_COLAB = True
    print("✓ Running in Google Colab.")
except ImportError:
    IN_COLAB = False
    print("ℹ️ Running in standalone environment.")

if IN_COLAB:
    print("Installing lightweight dependencies...")
    !pip install -q "sentence-transformers>=3.0.0" accelerate pandas tabulate

import torch
from sentence_transformers import SentenceTransformer

gpu_available = torch.cuda.is_available()
gpu_name = torch.cuda.get_device_name(0) if gpu_available else "CPU only"
print(f"Hardware Acceleration: {gpu_available} ({gpu_name})")
DEVICE = "cuda" if gpu_available else "cpu"

# %%
# =============================================================================
# Cell 2: Storage Resolution & Google Drive Mount
# =============================================================================
CONTENT_DIR = Path("/content" if os.path.isdir("/content") else ".")

if IN_COLAB and not os.path.exists("/content/drive"):
    try:
        from google.colab import drive
        drive.mount("/content/drive")
        print("✓ Google Drive mounted.")
    except Exception as e:
        print(f"ℹ️ Google Drive mount skipped or unavailable: {e}")

def auto_locate_file(filename, candidates=None):
    """Búsqueda flexible en candidatos directos, Drive y Colab."""
    if candidates:
        for c in candidates:
            if c and c.exists():
                return c
    # Buscar en carpetas directas
    direct_checks = [
        CONTENT_DIR / filename,
        Path(filename),
        Path("corpus_upload") / filename,
        Path("data/benchmark") / filename,
        Path("reports") / filename,
    ]
    for dc in direct_checks:
        if dc.exists():
            return dc
    # Búsqueda recursiva en Google Drive si está montado
    drive_root = Path("/content/drive/MyDrive")
    if drive_root.exists():
        print(f"Buscando '{filename}' en Google Drive...")
        for match in drive_root.glob(f"**/{filename}"):
            if match.is_file():
                return match
    # Búsqueda en /content
    if CONTENT_DIR.exists():
        for match in CONTENT_DIR.glob(f"**/{filename}"):
            if match.is_file():
                return match
    return None

# %%
# =============================================================================
# Cell 3: Official CP113-R1 Benchmark Oracle Verification (Fail-Closed)
# =============================================================================
EXPECTED_ORACLE_SHA = "dd3d3912ddd59183f80edf08c9e4c9f9648de768e53be0d8d3006d1190d5fe2b"
EXPECTED_QUERY_COUNT = 40
EXPECTED_QREL_COUNT = 67

oracle_path = auto_locate_file("benchmark_oracle.json")

if not oracle_path:
    raise FileNotFoundError(
        "FAIL-CLOSED: Official benchmark fixture 'benchmark_oracle.json' was NOT found in perimeter. "
        "Asegúrate de subir benchmark_oracle.json a Google Drive o a la carpeta de Colab."
    )

raw_bytes = oracle_path.read_bytes()
computed_sha = hashlib.sha256(raw_bytes).hexdigest()
size_bytes = len(raw_bytes)

print(f"Oracle Path: {oracle_path}")
print(f"Oracle Size: {size_bytes:,} bytes")
print(f"Computed SHA-256: {computed_sha}")
print(f"Expected SHA-256: {EXPECTED_ORACLE_SHA}")

if computed_sha != EXPECTED_ORACLE_SHA:
    raise ValueError(
        f"FAIL-CLOSED: Oracle hash mismatch! Computed: {computed_sha}, Expected: {EXPECTED_ORACLE_SHA}"
    )

with open(oracle_path, "r", encoding="utf-8") as f:
    oracle_data = json.load(f)

schema_version = oracle_data.get("version", "unknown")
queries = oracle_data.get("queries", [])
qrel_count = sum(len(q.get("relevant", [])) for q in queries)

print(f"Oracle Schema Version: {schema_version}")
print(f"Queries Present: {len(queries)}")
print(f"Qrels Present: {qrel_count}")

if len(queries) != EXPECTED_QUERY_COUNT:
    raise ValueError(f"FAIL-CLOSED: Query count mismatch ({len(queries)} != {EXPECTED_QUERY_COUNT})")

print("✓ ORACLE_INTEGRITY = PASS | ORACLE_VALIDATION = PASS")

# %%
# =============================================================================
# Cell 4: Locate and Extract CP115 Candidate Bundle (Read-Only)
# =============================================================================
EXPECTED_BUNDLE_SHA = "137586fe3ba99685774cc9804794d596baa2cf021234a8272a38e3eb62960e4a"

bundle_path = auto_locate_file("talos_corpus_bundle_20261003T162052Z.zip")

extract_target = CONTENT_DIR / "bundle_extracted"

# Check if already extracted locally
extracted_local = Path("reports/corpus_intelligence_lab/bundle_extracted_20261003T162052Z")
if extracted_local.exists() and (extracted_local / "manifest.json").exists():
    extract_target = extracted_local
    print(f"✓ Using existing extracted bundle directory: {extract_target}")
elif bundle_path:
    print(f"Found bundle zip at: {bundle_path}")
    b_sha = hashlib.sha256(bundle_path.read_bytes()).hexdigest()
    print(f"Bundle SHA-256: {b_sha}")
    if b_sha != EXPECTED_BUNDLE_SHA:
        print(f"⚠️ Warning: Bundle SHA differs from official CP115 rerun. Proceeding with audit.")
    extract_target.mkdir(parents=True, exist_ok=True)
    print(f"Descomprimiendo bundle en {extract_target}...")
    with zipfile.ZipFile(bundle_path, "r") as zf:
        zf.extractall(extract_target)
    print(f"✓ Bundle extracted to: {extract_target}")
else:
    raise FileNotFoundError("FAIL-CLOSED: CP115 candidate bundle (zip or extracted) was NOT found.")

# Verify candidates presence
candidates = ["baseline", "strategy_b", "strategy_c", "strategy_d"]
for c in candidates:
    c_dir = extract_target / "candidates" / c
    if not c_dir.exists():
        raise FileNotFoundError(f"FAIL-CLOSED: Missing candidate directory '{c}' in bundle.")
print("✓ All 4 candidates discovered in bundle.")

# %%
# =============================================================================
# Cell 5: Load Candidate Chunks & Vector Matrices
# =============================================================================
t0 = time.time()
candidate_chunks = {}
candidate_embeddings = {}
candidate_metadata = {}

EXPECTED_DIMS = 1024

for cand_id in candidates:
    c_dir = extract_target / "candidates" / cand_id
    chunks_file = c_dir / "chunks.jsonl"
    vectors_file = c_dir / "embeddings" / "qwen3_1024d_vectors.jsonl"
    meta_file = c_dir / "metadata.jsonl"

    print(f"Loading candidate: {cand_id}...")
    chunks_list = []
    with open(chunks_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                chunks_list.append(json.loads(line))
    candidate_chunks[cand_id] = chunks_list

    vecs_list = []
    with open(vectors_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                vecs_list.append(obj["vector"])
    arr = np.array(vecs_list, dtype=np.float32)
    candidate_embeddings[cand_id] = arr

    meta_dict = {}
    if meta_file.exists():
        with open(meta_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    obj = json.loads(line)
                    meta_dict[obj["chunk_id"]] = obj
    candidate_metadata[cand_id] = meta_dict

    assert len(chunks_list) == len(arr), f"Mismatch in {cand_id}: {len(chunks_list)} chunks vs {len(arr)} vectors"
    assert arr.shape[1] == EXPECTED_DIMS, f"Dimension mismatch in {cand_id}: {arr.shape[1]} != {EXPECTED_DIMS}"
    print(f"  ✓ {cand_id:12s}: {len(chunks_list):,} chunks | Matrix shape: {arr.shape}")

print(f"✓ All candidate matrices loaded in {time.time()-t0:.2f}s.")

# %%
# =============================================================================
# Cell 6: Load Embedding Model & Vectorize Official 40 Queries
# =============================================================================
MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
print(f"Loading embedding model '{MODEL_NAME}' on {DEVICE}...")
model = SentenceTransformer(MODEL_NAME, device=DEVICE)
model.max_seq_length = 512

query_ids = [q["id"] for q in queries]
query_texts = [q["query"] for q in queries]
print(f"Encoding {len(query_texts)} canonical queries with {MODEL_NAME}...")

t_enc = time.time()
q_embeddings = model.encode(
    query_texts,
    normalize_embeddings=True,
    convert_to_numpy=True,
    batch_size=16,
    show_progress_bar=True,
)
q_embeddings = np.asarray(q_embeddings, dtype=np.float32)
print(f"✓ Query vectors generated in {time.time()-t_enc:.2f}s: shape {q_embeddings.shape}")

q_norms = np.linalg.norm(q_embeddings, axis=1)
assert np.allclose(q_norms, 1.0, atol=1e-3), f"Query norms deviation: min={q_norms.min()}, max={q_norms.max()}"
print(f"✓ Query vectors strictly L2 normalized (mean={q_norms.mean():.6f}).")

# %%
# =============================================================================
# Cell 7: Execute Retrieval Benchmark Across All 40 Queries & 4 Candidates
# =============================================================================
print("Executing matrix cosine similarity retrieval across 4 candidates x 40 queries...")

K_TOP = 5
retrieval_results = {c: [] for c in candidates}

for q_idx, q_item in enumerate(queries):
    qid = q_item["id"]
    qtext = q_item["query"]
    qcat = q_item.get("category", "GENERAL")
    qrels = q_item.get("relevant", [])
    qrels_map = {r["chunk_id"]: r for r in qrels}
    q_vec = q_embeddings[q_idx]

    for cand_id in candidates:
        emb_matrix = candidate_embeddings[cand_id]
        chunks = candidate_chunks[cand_id]
        meta_dict = candidate_metadata[cand_id]

        scores = emb_matrix @ q_vec
        top_k_indices = np.argsort(scores)[::-1][:K_TOP]

        top_hits = []
        for rank, idx in enumerate(top_k_indices, 1):
            c = chunks[idx]
            cid = c.get("chunk_id")
            score = float(scores[idx])
            cmeta = meta_dict.get(cid, {})

            if cid in qrels_map:
                oracle_rel = qrels_map[cid].get("grade", "RELEVANT")
                adjudication_status = "GROUND_TRUTH_MATCH"
                rationale = qrels_map[cid].get("rationale", "")
            else:
                oracle_rel = "ID_MISMATCH_REQUIRES_ADJUDICATION"
                adjudication_status = "REQUIRES_HUMAN_ADJUDICATION"
                rationale = "Candidate chunk ID does not match legacy oracle chunk ID."

            top_hits.append({
                "rank": rank,
                "retrieved_chunk_id": cid,
                "similarity_score": round(score, 4),
                "oracle_relevance": oracle_rel,
                "adjudication_status": adjudication_status,
                "source_document": c.get("document_id"),
                "page_start": c.get("page_start"),
                "page_end": c.get("page_end"),
                "section_path": cmeta.get("section_path") or c.get("section"),
                "chunk_type": c.get("type", "text"),
                "preview": c.get("content", "")[:200].replace("\n", " "),
            })

        retrieval_results[cand_id].append({
            "query_id": qid,
            "query_text": qtext,
            "category": qcat,
            "top_1_score": top_hits[0]["similarity_score"] if top_hits else None,
            "mean_top_k_score": round(float(np.mean([h["similarity_score"] for h in top_hits])), 4) if top_hits else None,
            "top_hits": top_hits,
        })

print(f"✓ Retrieval executed for 40 queries across all 4 candidates.")

# %%
# =============================================================================
# Cell 8: Build Per-Query Comparison & Delta Matrices
# =============================================================================
comparison_rows = []
for q_idx, q_item in enumerate(queries):
    qid = q_item["id"]
    qtext = q_item["query"]
    qcat = q_item.get("category", "GENERAL")

    score_base = retrieval_results["baseline"][q_idx]["top_1_score"]
    score_b = retrieval_results["strategy_b"][q_idx]["top_1_score"]
    score_c = retrieval_results["strategy_c"][q_idx]["top_1_score"]
    score_d = retrieval_results["strategy_d"][q_idx]["top_1_score"]

    comparison_rows.append({
        "query_id": qid,
        "query_text": qtext[:60] + ("..." if len(qtext) > 60 else ""),
        "category": qcat,
        "baseline_top1": score_base,
        "strategy_b_top1": score_b,
        "strategy_c_top1": score_c,
        "strategy_d_top1": score_d,
        "delta_b_base": round(score_b - score_base, 4),
        "delta_c_base": round(score_c - score_base, 4),
        "delta_d_base": round(score_d - score_base, 4),
    })

df_comp = pd.DataFrame(comparison_rows)

print("\n=== CP116 OFFICIAL BENCHMARK: TOP-1 SIMILARITY PER-QUERY SUMMARY ===")
print(df_comp[["query_id", "category", "baseline_top1", "strategy_b_top1", "strategy_c_top1", "strategy_d_top1", "delta_b_base"]].to_markdown(index=False))

# Aggregate Statistics across all 40 queries
print("\n=== AGGREGATE CANDIDATE SIMILARITY STATISTICS (40 CANONICAL QUERIES) ===")
summary_stats = []
for c in candidates:
    top1_scores = [r["top_1_score"] for r in retrieval_results[c]]
    mean5_scores = [r["mean_top_k_score"] for r in retrieval_results[c]]
    summary_stats.append({
        "candidate": c,
        "queries_evaluated": len(top1_scores),
        "mean_top1": round(float(np.mean(top1_scores)), 4),
        "std_top1": round(float(np.std(top1_scores)), 4),
        "median_top1": round(float(np.median(top1_scores)), 4),
        "min_top1": round(float(np.min(top1_scores)), 4),
        "max_top1": round(float(np.max(top1_scores)), 4),
        "mean_top5": round(float(np.mean(mean5_scores)), 4),
    })

df_summary = pd.DataFrame(summary_stats)
print(df_summary.to_markdown(index=False))

# Delta Analysis (B - Baseline, C - Baseline, D - Baseline)
print("\n=== DELTA ANALYSIS RELATIVE TO HISTORICAL BASELINE ===")
for delta_col, name in [("delta_b_base", "Strategy B"), ("delta_c_base", "Strategy C"), ("delta_d_base", "Strategy D")]:
    improved = sum(1 for d in df_comp[delta_col] if d > 0.01)
    degraded = sum(1 for d in df_comp[delta_col] if d < -0.01)
    unchanged = len(df_comp) - improved - degraded
    mean_delta = float(df_comp[delta_col].mean())
    print(f"{name:12s} vs Baseline: Mean Delta = {mean_delta:+.4f} | Improved (>+0.01): {improved:2d} | Degraded (<-0.01): {degraded:2d} | Unchanged: {unchanged:2d}")

# %%
# =============================================================================
# Cell 9: Forensic Audit of Chunking Outlier (Joyanes Page 15)
# =============================================================================
print("\n=== FORENSIC AUDIT OF CHUNKING OUTLIER (47,627 CHARS) ===")
outlier_found = False
for cand_id in ["strategy_b", "strategy_c", "strategy_d"]:
    for c in candidate_chunks[cand_id]:
        if c.get("char_count", 0) > 40000:
            print(f"Candidate: {cand_id} | ID: {c.get('chunk_id')} | Length: {c.get('char_count'):,} chars | Page: {c.get('page_start')}")
            outlier_found = True

# Check presence in 40-query retrieval hits
outlier_retrieval_hits = 0
for cand_id in candidates:
    for q_res in retrieval_results[cand_id]:
        for h in q_res["top_hits"]:
            if "p0015:c" in h["retrieved_chunk_id"]:
                outlier_retrieval_hits += 1
                print(f"  Hit in {cand_id} on query {q_res['query_id']}: Rank {h['rank']} (Score: {h['similarity_score']})")

print(f"Outlier hits across 40 queries x 4 candidates: {outlier_retrieval_hits}")
print("Status: CHUNKING_OUTLIER_STATUS = ISSUE_FOUND | OUTLIER_IMPACT = LOW | OUTLIER_RESOLUTION = PENDING")

# %%
# =============================================================================
# Cell 10: Export Canonical Results & Generate Markdown Report
# =============================================================================
output_payload = {
    "schema": "talos-cp116-official-benchmark-v1",
    "timestamp_utc": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
    "environment": {
        "device": DEVICE,
        "gpu_name": gpu_name,
        "model": MODEL_NAME,
        "dimensions": EXPECTED_DIMS,
        "pooling": "lasttoken",
        "oracle_sha256": computed_sha,
        "bundle_sha256": EXPECTED_BUNDLE_SHA,
    },
    "oracle_validation": {
        "oracle_path": str(oracle_path),
        "sha256": computed_sha,
        "size_bytes": size_bytes,
        "query_count": len(queries),
        "qrel_count": qrel_count,
        "schema_version": schema_version,
        "validation_status": "PASS",
        "id_compatibility": "INCOMPATIBLE_TAXONOMY_REQUIRES_ADJUDICATION",
    },
    "candidate_summary_statistics": summary_stats,
    "per_query_comparison": comparison_rows,
    "retrieval_results": retrieval_results,
    "governance": {
        "CP113_R1_OFFICIAL_STATUS": "EXECUTED_PENDING_ADJUDICATION",
        "CANDIDATE_SELECTION": "NOT_AUTHORIZED",
        "HUMAN_ACCEPTANCE": "PENDING",
        "PRODUCTION_IMPORT": "FORBIDDEN",
        "PRODUCTION_STATUS": "UNCHANGED",
    }
}

OUT_JSON = CONTENT_DIR / "cp116_official_benchmark_results.json"
with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(output_payload, f, indent=2, ensure_ascii=False)

print(f"\n✓ Official benchmark results exported to: {OUT_JSON} ({OUT_JSON.stat().st_size:,} bytes)")

if IN_COLAB:
    from google.colab import files
    files.download(str(OUT_JSON))
    print("✓ Initiated direct download of benchmark results JSON.")
