import importlib.util
import json
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "preflight_gate2_pilot.py"
SPEC = importlib.util.spec_from_file_location("preflight_gate2_pilot", SCRIPT)
assert SPEC and SPEC.loader
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


def test_creates_blocked_review_template_without_approving_oracles(tmp_path):
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps({"queries": [{"query_id": "q1", "query": "tema"}]}),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(json.dumps({"qrels": {"q1": {}}}), encoding="utf-8")
    output = tmp_path / "review" / "decisions.json"

    preflight.prepare_decision_template(dataset, qrels, output)

    result = json.loads(output.read_text(encoding="utf-8"))
    assert result["status"] == "blocked_pending_curricular_review"
    assert result["decisions"]["q1"]["status"] == "blocked"
    assert result["decisions"]["q1"]["oracle_type"] is None
    assert result["coverage"] == {
        "total_queries": 1,
        "qrels_entries": 1,
        "missing_qrels": [],
        "unknown_qrels": [],
    }


def test_rejects_dataset_qrels_id_mismatch(tmp_path):
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps({"queries": [{"query_id": "q1", "query": "tema"}]}),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(json.dumps({"qrels": {"q2": {}}}), encoding="utf-8")

    with pytest.raises(preflight.Gate2PreflightError, match="do not match"):
        preflight.prepare_decision_template(dataset, qrels, tmp_path / "out.json")
