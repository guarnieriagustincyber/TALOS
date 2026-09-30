#!/usr/bin/env python3
"""Compare independent offline promotion decisions against synthetic fixtures."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "src/study_engine/diagnostics/vector_space_contract.py"
CONTRACT_SPEC = importlib.util.spec_from_file_location(
    "talos_offline_vector_space_contract", CONTRACT_PATH
)
if CONTRACT_SPEC is None or CONTRACT_SPEC.loader is None:
    raise RuntimeError(f"Cannot load offline contract helper at {CONTRACT_PATH}")
CONTRACT = importlib.util.module_from_spec(CONTRACT_SPEC)
sys.modules[CONTRACT_SPEC.name] = CONTRACT
CONTRACT_SPEC.loader.exec_module(CONTRACT)

vector_space_id = CONTRACT.vector_space_id
assess_promotion = CONTRACT.assess_promotion

REFERENCE_PATH = ROOT / "tests/unit/diagnostics/reference_promotion_gate.py"
REFERENCE_SPEC = importlib.util.spec_from_file_location(
    "talos_reference_promotion_gate", REFERENCE_PATH
)
if REFERENCE_SPEC is None or REFERENCE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load independent reference at {REFERENCE_PATH}")
REFERENCE = importlib.util.module_from_spec(REFERENCE_SPEC)
sys.modules[REFERENCE_SPEC.name] = REFERENCE
REFERENCE_SPEC.loader.exec_module(REFERENCE)

FIXTURE_PATH = ROOT / "tests/fixtures/vector_space_promotion/cases.json"


def _replace_markers(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, dict):
        return {
            key: _replace_markers(item, replacements)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_replace_markers(item, replacements) for item in value]
    if isinstance(value, str) and value in replacements:
        return replacements[value]
    return value


def validate_fixtures(fixtures: dict[str, Any]) -> list[dict[str, str]]:
    if fixtures.get("schema") != "talos-vector-space-promotion-fixtures-v1":
        raise ValueError("unknown vector-space promotion fixture schema")
    base_contract = fixtures.get("base_contract")
    base_candidate = fixtures.get("base_candidate")
    cases = fixtures.get("cases")
    if not isinstance(base_contract, dict) or not isinstance(base_candidate, dict):
        raise ValueError("base_contract and base_candidate must be objects")
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")

    identity_a = vector_space_id(base_contract)
    identity_b = REFERENCE.REFERENCE_IDENTITY.reference_space_id(base_contract)
    if identity_a != identity_b:
        raise AssertionError(
            f"identity implementations disagree: {identity_a} != {identity_b}"
        )
    replacements = {
        "$VECTOR_SPACE_ID": identity_a,
        "$MODEL_ARTIFACT_SHA256": base_contract["model_artifact_sha256"],
        "$TOKENIZER_ARTIFACT_SHA256": base_contract["tokenizer_artifact_sha256"],
    }
    resolved_base = _replace_markers(
        {**base_candidate, "contract": base_contract}, replacements
    )

    results = []
    seen_names = set()
    for case in cases:
        name = case.get("name")
        if not isinstance(name, str) or not name or name in seen_names:
            raise ValueError(f"fixture name is missing or duplicated: {name!r}")
        seen_names.add(name)
        candidate = copy.deepcopy(resolved_base)
        candidate.update(_replace_markers(case.get("overrides", {}), replacements))
        contract = dict(candidate["contract"])
        contract.update(case.get("contract_overrides", {}))
        candidate["contract"] = contract

        actual_a = assess_promotion(candidate)
        actual_b = REFERENCE.reference_promotion_assessment(candidate)
        if actual_a != actual_b:
            raise AssertionError(
                f"{name}: independent decisions disagree:\n"
                f"A={actual_a}\nB={actual_b}"
            )
        if actual_a["status"] != case.get("expected_status"):
            raise AssertionError(
                f"{name}: expected status {case.get('expected_status')}, "
                f"got {actual_a['status']}"
            )
        if actual_a["reason"] != case.get("expected_reason"):
            raise AssertionError(
                f"{name}: expected reason {case.get('expected_reason')}, "
                f"got {actual_a['reason']}"
            )
        expected_identity = (
            None
            if actual_a["status"] == "REJECTED"
            and actual_a["reason"] in {"INVALID_CONTRACT", "MUTABLE_REVISION"}
            else REFERENCE.REFERENCE_IDENTITY.reference_space_id(contract)
        )
        if actual_a["vector_space_id"] != expected_identity:
            raise AssertionError(
                f"{name}: expected identity {expected_identity}, "
                f"got {actual_a['vector_space_id']}"
            )
        results.append(
            {"name": name, "status": actual_a["status"], "reason": actual_a["reason"]}
        )
    return results


def main() -> int:
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    results = validate_fixtures(fixtures)
    for result in results:
        print(
            f"PASS {result['name']}: "
            f"{result['status']} ({result['reason']})"
        )
    print(f"Validated {len(results)} promotion fixtures with implementations A/B.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
