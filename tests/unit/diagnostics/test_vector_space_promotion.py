import importlib.util
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
SCRIPT_PATH = ROOT / "scripts/check_vector_space_promotion_fixtures.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location(
    "talos_vector_space_promotion_fixture_runner", SCRIPT_PATH
)
assert SCRIPT_SPEC is not None and SCRIPT_SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = RUNNER
SCRIPT_SPEC.loader.exec_module(RUNNER)

FIXTURE_PATH = ROOT / "tests/fixtures/vector_space_promotion/cases.json"


def test_independent_promotion_implementations_match_all_fixture_decisions():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    results = RUNNER.validate_fixtures(fixtures)

    assert len(results) == 15
    assert {item["name"] for item in results} >= {
        "PROMOTABLE",
        "NEW_V2_INDEX",
        "CONTRACT_ONLY",
        "PROVENANCE_MISSING",
        "ARTIFACT_UNVERIFIED",
        "PARTIAL_COVERAGE",
        "INVENTORY_COUNT_MISMATCH",
        "MANIFEST_MISMATCH",
        "MIXED_VECTOR_SPACES",
        "CONTRADICTORY_EVIDENCE",
        "MUTABLE_REVISION",
        "INVALID_INDEX",
        "DIMENSION_MISMATCH",
        "INVALID_CONTRACT",
        "HISTORICAL_PLAUSIBLE_ID_WITHOUT_PROVENANCE",
    }


def test_plausible_identity_does_not_promote_historical_incomplete_index():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    results = RUNNER.validate_fixtures(fixtures)
    historical = next(
        item
        for item in results
        if item["name"] == "HISTORICAL_PLAUSIBLE_ID_WITHOUT_PROVENANCE"
    )

    assert historical == {
        "name": "HISTORICAL_PLAUSIBLE_ID_WITHOUT_PROVENANCE",
        "status": "LEGACY / UNRESOLVED",
        "reason": "PROVENANCE_MISSING",
    }
