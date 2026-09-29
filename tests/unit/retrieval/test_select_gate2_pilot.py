import importlib.util
import json
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "select_gate2_pilot.py"
SPEC = importlib.util.spec_from_file_location("select_gate2_pilot", SCRIPT)
assert SPEC and SPEC.loader
selector = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(selector)


def test_selection_keeps_negative_candidate_blocked(tmp_path):
    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "positive",
                        "category": "vulnerabilidades",
                        "notebook_scope": ["scope-a"],
                        "expected": {"abstention": False},
                    },
                    {
                        "query_id": "ood",
                        "category": "ood_trampas",
                        "notebook_scope": ["scope-a"],
                        "expected": {"abstention": True},
                    },
                    {
                        "query_id": "candidate",
                        "category": "vulnerabilidades",
                        "notebook_scope": ["scope-a"],
                        "expected": {"abstention": True},
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(
        json.dumps({"qrels": {"positive": {"chunk-a": 2}, "ood": {}, "candidate": {}}}),
        encoding="utf-8",
    )
    output = tmp_path / "selection.json"

    selector.select_candidates(dataset, qrels, output)

    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["pilot_authorized"] is False
    assert report["candidates"]["positive_in_scope"]["query_id"] == "positive"
    assert report["candidates"]["ood_global"]["query_id"] == "ood"
    assert report["candidates"]["negative_by_scope"]["approved"] is False
