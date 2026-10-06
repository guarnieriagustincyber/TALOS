"""Three-way benchmark certification runner for S3.6.3."""

import argparse
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional

import numpy as np

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.oracle import OracleDataset
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalStrategy,
)
from study_engine.retrieval.dense import DenseRetriever
from study_engine.retrieval.embedding import (
    EmbeddingProvider,
    LocalONNXEmbeddingProvider,
)
from study_engine.retrieval.evaluator import OracleEvaluator
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


def compute_percentiles(values: List[float]) -> Dict[str, float]:
    """Calculate descriptive latency percentiles in ms."""
    if not values:
        return {
            "mean": 0.0,
            "p50": 0.0,
            "p95": 0.0,
            "min": 0.0,
            "max": 0.0,
        }
    return {
        "mean": float(np.mean(values)),
        "p50": float(np.median(values)),
        "p95": float(np.percentile(values, 95)),
        "min": float(np.min(values)),
        "max": float(np.max(values)),
    }


def setup_benchmark_environment(
    corpus_path: Path,
    store_db_path: Path,
    vec_db_path: Path,
    provider: EmbeddingProvider,
) -> KnowledgeStore:
    """Initialize and populate KnowledgeStore and SQLiteVectorStore."""
    store_db_path.parent.mkdir(parents=True, exist_ok=True)
    if store_db_path.exists():
        store_db_path.unlink()
    if vec_db_path.exists():
        vec_db_path.unlink()

    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    store = KnowledgeStore(store_db_path)
    store.initialize()

    for nb in corpus["notebooks"]:
        store.create_notebook(
            Notebook(
                id=nb["id"],
                name=nb["name"],
                description=nb["description"],
                subject=nb["subject"],
            )
        )

    for src in corpus["sources"]:
        manifest = SourceManifest(
            source_id=src["source_id"],
            filename=src["filename"],
            byte_size=src["byte_size"],
            sha256=src["sha256"],
        )
        store.save_source(
            SourceRecord(source_id=src["source_id"], manifest=manifest)
        )
        store.link_source_to_notebook(src["notebook_id"], src["source_id"])

    for doc in corpus["documents"]:
        store.save_document(
            Document(
                id=doc["id"],
                source_id=doc["source_id"],
                title=doc["title"],
                content=doc["content"],
            )
        )

    chunks = [
        Chunk(
            id=c["id"],
            document_id=c["document_id"],
            source_id=c["source_id"],
            content=c["content"],
            index=c["index"],
        )
        for c in corpus["chunks"]
    ]
    store.save_chunks(chunks)

    vec_store = SQLiteVectorStore(vec_db_path, read_only=False)
    index_notebook_chunks(store, vec_store, provider, "fadena-so")
    index_notebook_chunks(store, vec_store, provider, "fadena-prog")

    return store


def run_certification(
    corpus_path: Path = Path("data/benchmark/benchmark_corpus.json"),
    oracle_path: Path = Path("data/benchmark/benchmark_oracle.json"),
    output_path: Path = Path("data/benchmark/benchmark_results.json"),
    db_dir: Path = Path("data/benchmark/db"),
    provider: Optional[EmbeddingProvider] = None,
) -> Dict[str, Any]:
    """Execute complete 3-way certification benchmark."""
    if provider is None:
        provider = LocalONNXEmbeddingProvider()

    store_db = db_dir / "benchmark_store.db"
    vec_db = db_dir / "benchmark_vectors.db"

    t_setup0 = time.perf_counter()
    store = setup_benchmark_environment(
        corpus_path, store_db, vec_db, provider
    )
    vec_store = SQLiteVectorStore(vec_db)
    setup_ms = (time.perf_counter() - t_setup0) * 1000.0

    lex = LexicalRetriever(store)
    dense = DenseRetriever(store, vec_store, provider)
    hybrid = HybridRetriever(store, lex, dense)

    with open(oracle_path, "r", encoding="utf-8") as f:
        dataset = OracleDataset.model_validate(json.load(f))

    evaluator = OracleEvaluator(store)

    rep_lex = evaluator.evaluate(
        lex, dataset, strategy=RetrievalStrategy.LEXICAL
    )
    rep_dense = evaluator.evaluate(
        dense, dataset, strategy=RetrievalStrategy.DENSE
    )
    rep_hyb = evaluator.evaluate(
        hybrid, dataset, strategy=RetrievalStrategy.HYBRID
    )

    # Detailed query-level divergence analysis
    q_map_l = {r.query_id: r for r in rep_lex.query_results}
    q_map_d = {r.query_id: r for r in rep_dense.query_results}
    q_map_h = {r.query_id: r for r in rep_hyb.query_results}

    query_divergence: List[Dict[str, Any]] = []
    latencies: Dict[str, Dict[str, List[float]]] = {
        "lexical": {"total": []},
        "dense": {
            "total": [],
            "query_embedding": [],
            "similarity": [],
            "hydration": [],
        },
        "hybrid": {
            "total": [],
            "lexical": [],
            "dense": [],
            "fusion": [],
        },
    }

    counts = {
        "consensus_wins": 0,
        "dense_only_wins": 0,
        "bm25_only_wins": 0,
        "rrf_complementary_wins": 0,
        "rrf_degradations": 0,
        "mutual_failures": 0,
        "leakage_controls_passed": 0,
    }

    for q in dataset.queries:
        ql = q_map_l[q.id]
        qd = q_map_d[q.id]
        qh = q_map_h[q.id]

        # Collect latency traces
        req_l = RetrievalRequest(
            query=q.query,
            notebook_id=q.notebook_id,
            top_k=5,
            strategy=RetrievalStrategy.LEXICAL,
        )
        resp_l = lex.retrieve(req_l)
        latencies["lexical"]["total"].append(
            resp_l.diagnostics.latencies_ms.get("retrieval_ms", 0.0)
        )

        req_d = RetrievalRequest(
            query=q.query,
            notebook_id=q.notebook_id,
            top_k=5,
            strategy=RetrievalStrategy.DENSE,
        )
        resp_d = dense.retrieve(req_d)
        d_diag = resp_d.diagnostics.latencies_ms
        latencies["dense"]["total"].append(d_diag.get("retrieval_ms", 0.0))
        latencies["dense"]["query_embedding"].append(
            d_diag.get("query_embedding_ms", 0.0)
        )
        latencies["dense"]["similarity"].append(
            d_diag.get("similarity_ms", 0.0)
        )
        latencies["dense"]["hydration"].append(d_diag.get("hydration_ms", 0.0))

        req_h = RetrievalRequest(

            query=q.query,
            notebook_id=q.notebook_id,
            top_k=5,
            strategy=RetrievalStrategy.HYBRID,
        )
        resp_h = hybrid.retrieve(req_h)
        h_diag = resp_h.diagnostics.latencies_ms
        latencies["hybrid"]["total"].append(h_diag.get("retrieval_ms", 0.0))
        latencies["hybrid"]["lexical"].append(h_diag.get("lexical_ms", 0.0))
        latencies["hybrid"]["dense"].append(h_diag.get("dense_ms", 0.0))
        latencies["hybrid"]["fusion"].append(h_diag.get("fusion_ms", 0.0))

        if q.category.value == "CURRICULAR_LEAKAGE":
            passed = (
                ql.illegal_candidates_count == 0
                and qd.illegal_candidates_count == 0
                and qh.illegal_candidates_count == 0
            )
            if passed:
                counts["leakage_controls_passed"] += 1
            query_divergence.append(
                {
                    "query_id": q.id,
                    "category": q.category.value,
                    "notebook_id": q.notebook_id,
                    "query": q.query,
                    "behavior": "LEAKAGE_CONTROL",
                    "bm25_passed": ql.illegal_candidates_count == 0,
                    "dense_passed": qd.illegal_candidates_count == 0,
                    "rrf_passed": qh.illegal_candidates_count == 0,
                }
            )
            continue

        bl = ql.direct_recall_at_5 > 0
        bd = qd.direct_recall_at_5 > 0
        bh = qh.direct_recall_at_5 > 0

        behavior = "OTHER"
        if bl and bd and bh:
            behavior = "CONSENSUS_WIN"
            counts["consensus_wins"] += 1
        elif not bl and bd and bh:
            behavior = "DENSE_ONLY_WIN"
            counts["dense_only_wins"] += 1
        elif bl and not bd and bh:
            behavior = "BM25_ONLY_WIN"
            counts["bm25_only_wins"] += 1
        elif not bl and not bd and bh:
            behavior = "RRF_COMPLEMENTARY_WIN"
            counts["rrf_complementary_wins"] += 1
        elif (bl or bd) and not bh:
            behavior = "RRF_DEGRADATION"
            counts["rrf_degradations"] += 1
        elif not bl and not bd and not bh:
            behavior = "MUTUAL_FAILURE"
            counts["mutual_failures"] += 1

        query_divergence.append(
            {
                "query_id": q.id,
                "category": q.category.value,
                "notebook_id": q.notebook_id,
                "query": q.query,
                "behavior": behavior,
                "bm25": {
                    "direct_r1": ql.direct_recall_at_1,
                    "direct_r5": ql.direct_recall_at_5,
                    "overall_r5": ql.overall_recall_at_5,
                    "mrr": ql.reciprocal_rank,
                },
                "dense": {
                    "direct_r1": qd.direct_recall_at_1,
                    "direct_r5": qd.direct_recall_at_5,
                    "overall_r5": qd.overall_recall_at_5,
                    "mrr": qd.reciprocal_rank,
                },
                "hybrid_rrf": {
                    "direct_r1": qh.direct_recall_at_1,
                    "direct_r5": qh.direct_recall_at_5,
                    "overall_r5": qh.overall_recall_at_5,
                    "mrr": qh.reciprocal_rank,
                },
            }
        )

    # Compile latency stats
    latency_stats = {
        "lexical": {
            "total_ms": compute_percentiles(latencies["lexical"]["total"])
        },
        "dense": {
            "total_ms": compute_percentiles(latencies["dense"]["total"]),
            "query_embedding_ms": compute_percentiles(
                latencies["dense"]["query_embedding"]
            ),
            "similarity_ms": compute_percentiles(
                latencies["dense"]["similarity"]
            ),
            "hydration_ms": compute_percentiles(
                latencies["dense"]["hydration"]
            ),
        },
        "hybrid": {
            "total_ms": compute_percentiles(latencies["hybrid"]["total"]),
            "lexical_ms": compute_percentiles(latencies["hybrid"]["lexical"]),
            "dense_ms": compute_percentiles(latencies["hybrid"]["dense"]),
            "fusion_ms": compute_percentiles(latencies["hybrid"]["fusion"]),
        },
    }

    # Notebook breakdowns
    notebook_stats: Dict[str, Any] = {}
    for nb in ["fadena-so", "fadena-prog"]:
        q_nb = [
            q.id
            for q in dataset.queries
            if q.notebook_id == nb and q.category.value != "CURRICULAR_LEAKAGE"
        ]
        res_l = [r for r in rep_lex.query_results if r.query_id in q_nb]
        res_d = [r for r in rep_dense.query_results if r.query_id in q_nb]
        res_h = [r for r in rep_hyb.query_results if r.query_id in q_nb]
        n_cnt = len(q_nb)
        notebook_stats[nb] = {
            "query_count": n_cnt,
            "bm25": {
                "direct_r1": sum(r.direct_recall_at_1 for r in res_l) / n_cnt,
                "direct_r5": sum(r.direct_recall_at_5 for r in res_l) / n_cnt,
                "overall_r5": (
                    sum(r.overall_recall_at_5 for r in res_l) / n_cnt
                ),
                "mrr": sum(r.reciprocal_rank for r in res_l) / n_cnt,
            },
            "dense": {
                "direct_r1": sum(r.direct_recall_at_1 for r in res_d) / n_cnt,
                "direct_r5": sum(r.direct_recall_at_5 for r in res_d) / n_cnt,
                "overall_r5": (
                    sum(r.overall_recall_at_5 for r in res_d) / n_cnt
                ),
                "mrr": sum(r.reciprocal_rank for r in res_d) / n_cnt,
            },
            "hybrid_rrf": {
                "direct_r1": sum(r.direct_recall_at_1 for r in res_h) / n_cnt,
                "direct_r5": sum(r.direct_recall_at_5 for r in res_h) / n_cnt,
                "overall_r5": (
                    sum(r.overall_recall_at_5 for r in res_h) / n_cnt
                ),
                "mrr": sum(r.reciprocal_rank for r in res_h) / n_cnt,
            },
        }

    # Final certification artifact
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": "S3.6.3",
        "oracle_version": dataset.version,
        "total_queries": len(dataset.queries),
        "setup_ms": setup_ms,
        "summary_counts": counts,
        "global_metrics": {
            "bm25": rep_lex.global_metrics.model_dump(),
            "dense": rep_dense.global_metrics.model_dump(),
            "hybrid_rrf": rep_hyb.global_metrics.model_dump(),
        },
        "by_category": {
            "bm25": {
                k: v.model_dump() for k, v in rep_lex.by_category.items()
            },
            "dense": {
                k: v.model_dump() for k, v in rep_dense.by_category.items()
            },
            "hybrid_rrf": {
                k: v.model_dump() for k, v in rep_hyb.by_category.items()
            },
        },
        "by_notebook": notebook_stats,
        "latency_stats": latency_stats,
        "query_divergence": query_divergence,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run S3.6.3 Three-Way Benchmark Certification."
    )
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path("data/benchmark/benchmark_corpus.json"),
        help="Path to benchmark_corpus.json",
    )
    parser.add_argument(
        "--oracle",
        type=Path,
        default=Path("data/benchmark/benchmark_oracle.json"),
        help="Path to benchmark_oracle.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/benchmark/benchmark_results.json"),
        help="Path to save benchmark_results.json",
    )
    args = parser.parse_args()

    try:
        print("=" * 60)
        print("STARTING S3.6.3 THREE-WAY BENCHMARK CERTIFICATION")
        print("=" * 60)
        data = run_certification(
            corpus_path=args.corpus,
            oracle_path=args.oracle,
            output_path=args.output,
        )
        counts = data["summary_counts"]
        print("\n" + "=" * 60)
        print("S3.6.3 THREE-WAY CERTIFICATION EXECUTION FINISHED")
        print("=" * 60)
        print(f"Total Queries Evaluated: {data['total_queries']}")
        print(f"Consensus Wins (All):           {counts['consensus_wins']}")
        print(f"Dense-Only Wins (Dense+RRF):    {counts['dense_only_wins']}")
        print(f"BM25-Only Wins  (BM25+RRF):     {counts['bm25_only_wins']}")
        print(f"RRF Complementary Wins:         "
              f"{counts['rrf_complementary_wins']}")
        print(f"RRF Degradations:               {counts['rrf_degradations']}")
        print(f"Mutual Failures:                {counts['mutual_failures']}")
        print(f"Leakage Controls:               "
              f"{counts['leakage_controls_passed']}/6")
        print(f"\nResults Saved to: {args.output}")
        print("=" * 60)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
