import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "summarize_gate2_pilot.py"
SPEC = importlib.util.spec_from_file_location("summarize_gate2_pilot", SCRIPT)
assert SPEC and SPEC.loader
summarizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(summarizer)


def test_report_marks_failed_negative_checks_inconclusive(tmp_path):
    pilot = tmp_path / "pilot"
    pilot.mkdir()
    source = tmp_path / "db.sqlite"
    source.write_bytes(b"fixture-db")
    source_hash = "sha256:" + __import__("hashlib").sha256(b"fixture-db").hexdigest()
    stem = "gate2_v2.402"
    (pilot / f"{stem}.manifest.json").write_text(
        json.dumps(
            {
                "snapshots": {
                    "sources": {
                        "knowledge_db": {"sha256": source_hash},
                        "vector_db": {"sha256": source_hash},
                    },
                    "snapshots": {
                        "knowledge_db": {"path": str(tmp_path / "cleaned-k.db")},
                        "vector_db": {"path": str(tmp_path / "cleaned-v.db")},
                    },
                }
            }
        )
    )
    (pilot / f"{stem}.dataset.json").write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "qpos",
                        "scope": "scope-a",
                        "oracle_type": "positive_in_scope",
                    },
                    {
                        "query_id": "qneg",
                        "scope": "scope-a",
                        "oracle_type": "negative_by_scope",
                    },
                ]
            }
        )
    )
    (pilot / f"{stem}.qrels.json").write_text(
        json.dumps(
            {
                "version": "v2.402",
                "qrels": {"qpos": {"chunk-a": 1}, "qneg": {}},
                "metadata": {
                    "qrels_provenance": "retrieval_proposal",
                    "approved": False,
                },
            }
        )
    )
    (pilot / f"{stem}.observations.json").write_text(
        json.dumps(
            {
                "observations": {
                    "qpos": {"retrieved_chunk_ids": ["chunk-a"], "candidate_count": 1},
                    "qneg": {
                        "retrieved_chunk_ids": ["noise"],
                        "candidate_count": 1,
                        "candidate_absence_passed": False,
                    },
                },
                "candidate_proposals": {},
            }
        )
    )
    thermal = tmp_path / "thermal.json"
    thermal.write_text(
        json.dumps(
            {
                "baseline": {"cpu_tctl_c": 60.0},
                "max_cpu_tctl_c": 61.0,
                "max_gpu_edge_c": 50.0,
                "max_load_1m": 1.0,
                "stop_reason": None,
                "return_code": 0,
                "samples": [{"elapsed_s": 2.0}],
            }
        )
    )

    report_path = summarizer.summarize_pilot(pilot, thermal, source, source)
    report = json.loads(report_path.read_text())

    assert report["status"] == "INCONCLUSIVE"
    assert report["negative_candidate_absence"] == {"passed": 0, "total": 1}
    assert report["active_database_hashes"]["knowledge_db"]["unchanged"] is True
