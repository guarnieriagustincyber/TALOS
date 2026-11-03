#!/usr/bin/env python3
"""Compare two independent offline implementations against synthetic fixtures."""

import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/vector_space_contract/cases.json"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def expand(base_contract, override):
    result = dict(base_contract)
    for key, value in override.items():
        if key == "provenance" and isinstance(value, dict):
            result[key] = {**result.get(key, {}), **value}
        else:
            result[key] = value
    return result


def main():
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    production = load_module(
        "vector_space_contract_under_test",
        ROOT / "src/study_engine/diagnostics/vector_space_contract.py",
    )
    reference = load_module(
        "vector_space_contract_reference",
        ROOT
        / "tests/unit/diagnostics/reference_vector_space_contract.py",
    )

    base = fixtures["base_contract"]
    manifest_entries = [
        {"path": "tokenizer/config.json", "sha256": "a" * 64},
        {"path": "weights/model.bin", "sha256": "b" * 64},
    ]
    production_manifest_id = production.artifact_manifest_sha256(manifest_entries)
    reference_manifest_id = reference.reference_manifest_id(manifest_entries)
    if production_manifest_id != reference_manifest_id:
        raise AssertionError(
            "artifact manifest disagreement: "
            f"{production_manifest_id} != {reference_manifest_id}"
        )

    passed = 0
    for case in fixtures["cases"]:
        query = expand(base, case.get("query_overrides", {}))
        index_contracts = [
            None if item is None else expand(base, item)
            for item in case.get("index_contracts", [])
        ]

        production_assessment = production.assess_vector_space(
            query, index_contracts
        )
        reference_assessment = reference.reference_assessment(
            query, index_contracts
        )
        comparable_production = {
            key: value
            for key, value in production_assessment.items()
            if key != "reason"
        }
        comparable_reference = {
            key: value
            for key, value in reference_assessment.items()
            if key != "reason"
        }
        if comparable_production != comparable_reference:
            raise AssertionError(
                f"{case['name']}: assessment disagreement:\n"
                f"production={comparable_production}\n"
                f"reference={comparable_reference}"
            )
        if production_assessment["status"] != case["expected_status"]:
            raise AssertionError(
                f"{case['name']}: expected {case['expected_status']}, "
                f"got {production_assessment['status']}"
            )

        if production_assessment["query_vector_space_id"] is not None:
            production_id = production.vector_space_id(query)
            reference_id = reference.reference_space_id(query)
            if production_id != reference_id:
                raise AssertionError(
                    f"{case['name']}: identity disagreement: "
                    f"{production_id} != {reference_id}"
                )
        passed += 1

    print(
        "PASS independent vector-space identities, manifest digest, "
        f"and assessments: {passed} fixture cases"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
