"""CLI wrapper for S3.6.1 benchmark corpus builder."""

import argparse
from pathlib import Path
import sys

from study_engine.retrieval.benchmark_builder import build_benchmark_corpus

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Build S3.6.1 Benchmark Corpus via S1."
    )
    parser.add_argument(
        "--sources-dir",
        type=Path,
        default=Path("data/benchmark/sources"),
        help="Path to authentic physical source files",
    )
    parser.add_argument(
        "--output-corpus",
        type=Path,
        default=Path("data/benchmark/benchmark_corpus.json"),
        help="Path to save benchmark_corpus.json",
    )
    parser.add_argument(
        "--output-manifest",
        type=Path,
        default=Path("data/benchmark/benchmark_manifest.json"),
        help="Path to save benchmark_manifest.json",
    )
    args = parser.parse_args()

    try:
        manifest = build_benchmark_corpus(
            sources_dir=args.sources_dir,
            output_corpus_path=args.output_corpus,
            output_manifest_path=args.output_manifest,
        )
        print("============================================================")
        print("S3.6.1 BENCHMARK CORPUS BUILD SUCCESSFUL")
        print("============================================================")
        print(f"Total Source Files: {manifest['total_source_files']}")
        print(f"Total Documents:    {manifest['total_documents']}")
        print(f"Total Chunks:       {manifest['total_chunks']}")
        print("Notebook Distribution:")
        for nb, count in manifest["notebook_chunk_counts"].items():
            print(f"  - {nb}: {count} chunks")
        print("Thematic Breakdown:")
        for nb, topics in manifest["thematic_breakdown"].items():
            print(f"  [{nb}]")
            for top, cnt in topics.items():
                print(f"    - {top:15s}: {cnt} chunks")
        print(f"\nSaved Corpus:   {args.output_corpus}")
        print(f"Saved Manifest: {args.output_manifest}")
        print("============================================================")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
