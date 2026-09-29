import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "generate_gate2_benchmark.py"
SPEC = importlib.util.spec_from_file_location("generate_gate2_benchmark", SCRIPT)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def _inputs(tmp_path: Path):
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "q-positive",
                        "query": "tema positivo",
                        "kc_ids": ["kc"],
                        "topic_anchors": ["tema"],
                    },
                    {"query_id": "q-ood", "query": "tema ajeno", "kc_ids": []},
                ]
            }
        ),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(
        json.dumps({"qrels": {"q-positive": {"chunk-a": 2}, "q-ood": {}}}),
        encoding="utf-8",
    )
    decisions = tmp_path / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "decisions": {
                    "q-positive": {
                        "scope": "scope-a",
                        "oracle_type": "positive_in_scope",
                        "status": "pending",
                    },
                    "q-ood": {
                        "scope": "scope-a",
                        "oracle_type": "ood_global",
                        "status": "approved",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return dataset, qrels, decisions


def test_fixture_mode_writes_versioned_outputs_without_retrieval(tmp_path):
    dataset, qrels, decisions = _inputs(tmp_path)
    output = tmp_path / "output"

    generator.generate_fixture(
        dataset, qrels, decisions, output, "v2.402-scope-contract"
    )

    files = sorted(path.name for path in output.iterdir())
    assert files == [
        "gate2_v2.402-scope-contract.dataset.json",
        "gate2_v2.402-scope-contract.decisions.json",
        "gate2_v2.402-scope-contract.manifest.json",
        "gate2_v2.402-scope-contract.qrels.json",
    ]
    manifest = json.loads(
        (output / "gate2_v2.402-scope-contract.manifest.json").read_text()
    )
    assert manifest["retrieval"] == {"executed": False}
    normalized_dataset = json.loads(
        (output / "gate2_v2.402-scope-contract.dataset.json").read_text()
    )
    assert normalized_dataset["queries"][0]["topic_anchors"] == ["tema"]
    normalized_qrels = json.loads(
        (output / "gate2_v2.402-scope-contract.qrels.json").read_text()
    )
    assert normalized_qrels["qrels"]["q-ood"] == {}


def test_missing_decision_blocks_record_and_does_not_promote_qrels(tmp_path):
    dataset, qrels, _ = _inputs(tmp_path)
    decisions = tmp_path / "missing-decisions.json"
    decisions.write_text(json.dumps({"decisions": {}}), encoding="utf-8")

    normalized, normalized_qrels, _ = generator.normalize_dataset(
        json.loads(dataset.read_text()),
        json.loads(qrels.read_text()),
        json.loads(decisions.read_text()),
        version="v2.402",
    )

    assert normalized["queries"][0]["qrels_status"] == "blocked"
    assert normalized["queries"][0]["oracle_type"] == "positive_in_scope"
    assert normalized_qrels["qrels"]["q-positive"] == {}


def test_human_verified_qrels_preserve_provenance(tmp_path):
    dataset, qrels, decisions = _inputs(tmp_path)
    payload = json.loads(decisions.read_text())
    payload["decisions"]["q-positive"].update(
        {
            "status": "approved",
            "qrels_provenance": "human_verified",
            "reviewer": "user-approved",
            "evidence": ["Explicit user acceptance of qrel membership and grades."],
        }
    )
    decisions.write_text(json.dumps(payload), encoding="utf-8")

    normalized, normalized_qrels, _ = generator.normalize_dataset(
        json.loads(dataset.read_text()),
        json.loads(qrels.read_text()),
        payload,
        version="v2.402-adjudicated",
    )

    positive = next(
        row for row in normalized["queries"] if row["query_id"] == "q-positive"
    )
    assert positive["qrels_status"] == "approved"
    assert positive["qrels_provenance"] == "human_verified"
    assert normalized_qrels["qrels"]["q-positive"] == {"chunk-a": 2}


def test_human_verified_qrels_require_reviewer_and_evidence(tmp_path):
    dataset, qrels, decisions = _inputs(tmp_path)
    payload = json.loads(decisions.read_text())
    payload["decisions"]["q-positive"].update(
        {"status": "approved", "qrels_provenance": "human_verified"}
    )

    with pytest.raises(
        generator.Gate2GeneratorError,
        match="need approved status, reviewer and evidence",
    ):
        generator.normalize_dataset(
            json.loads(dataset.read_text()),
            json.loads(qrels.read_text()),
            payload,
            version="v2.402-adjudicated",
        )


def test_scope_change_requires_explicit_decision_id(tmp_path):
    dataset, qrels, decisions = _inputs(tmp_path)
    payload = json.loads(decisions.read_text())
    payload["previous_queries"] = [
        {"query_id": "q-positive", "notebook_scope": ["scope-old"]}
    ]
    decisions.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(generator.Gate2GeneratorError, match="scope_decision_id"):
        generator.normalize_dataset(
            json.loads(dataset.read_text()),
            json.loads(qrels.read_text()),
            json.loads(decisions.read_text()),
            version="v2.402",
        )


def test_refuses_historical_version_and_existing_output(tmp_path):
    dataset, qrels, decisions = _inputs(tmp_path)
    with pytest.raises(generator.Gate2GeneratorError, match="cannot be overwritten"):
        generator.generate_fixture(
            dataset, qrels, decisions, tmp_path / "out", "v2.401"
        )

    output = tmp_path / "out"
    output.mkdir()
    with pytest.raises(generator.Gate2GeneratorError, match="already exists"):
        generator.generate_fixture(dataset, qrels, decisions, output, "v2.402")
