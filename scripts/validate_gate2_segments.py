#!/usr/bin/env python3
"""Validate Gate 2 dataset/qrels by scope and oracle without retrieval."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_engine.diagnostics.gate2_segment_validation import (
    Gate2SegmentValidationError,
    validate_gate2_segments,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--knowledge-db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise Gate2SegmentValidationError(f"Output already exists: {args.output}")
    report = validate_gate2_segments(args.dataset, args.qrels, args.knowledge_db)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Gate2SegmentValidationError, OSError) as exc:
        print(f"Gate 2 segment validation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
