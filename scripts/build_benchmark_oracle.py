"""Build, validate and report the S3.6.2 Benchmark Oracle Dataset."""

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Dict

from study_engine.contracts.oracle import OracleDataset
from study_engine.retrieval.oracle import validate_oracle_dataset


def load_and_validate_oracle(
    oracle_path: Path = Path("data/benchmark/benchmark_oracle.json"),
) -> Dict[str, Any]:
    """Load, validate, and verify the benchmark Oracle dataset."""
    if not oracle_path.exists():
        raise FileNotFoundError(f"Oracle file not found at: {oracle_path}")

    with open(oracle_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    dataset = OracleDataset.model_validate(data)
    validate_oracle_dataset(dataset)
    return dataset.model_dump()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate and report S3.6.2 Benchmark Oracle Dataset."
    )
    parser.add_argument(
        "--oracle-path",
        type=Path,
        default=Path("data/benchmark/benchmark_oracle.json"),
        help="Path to benchmark_oracle.json",
    )
    args = parser.parse_args()

    try:
        data = load_and_validate_oracle(oracle_path=args.oracle_path)
        meta = data["metadata"]
        print("============================================================")
        print("S3.6.2 BENCHMARK ORACLE VALIDATION SUCCESSFUL")
        print("============================================================")
        print(f"Total Queries: {meta['total_queries']}")
        print("Notebook Balance:")
        for nb, cnt in meta["notebooks"].items():
            print(f"  - {nb}: {cnt} queries")
        print("Category Breakdown:")
        for cat, cnt in meta["categories"].items():
            print(f"  - {cat:20s}: {cnt} queries")
        print(f"\nOracle Verified: {args.oracle_path}")
        print("============================================================")
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
