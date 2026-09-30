#!/usr/bin/env python3
"""Run offline vector-space identity fixtures; does not inspect production data."""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    REPO_ROOT
    / "src"
    / "study_engine"
    / "diagnostics"
    / "vector_space_contract.py"
)
SPEC = importlib.util.spec_from_file_location("talos_vector_space_contract", VALIDATOR_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot load offline validator at {VALIDATOR_PATH}")
VALIDATOR = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = VALIDATOR
SPEC.loader.exec_module(VALIDATOR)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=REPO_ROOT / "tests" / "fixtures" / "vector_space_contract" / "cases.json",
    )
    args = parser.parse_args()
    fixtures = json.loads(args.fixtures.read_text(encoding="utf-8"))
    results = VALIDATOR.validate_fixture_suite(fixtures)
    for result in results:
        print(f"PASS {result['name']}: {result['status']}")
    print(f"Validated {len(results)} vector-space fixtures.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
