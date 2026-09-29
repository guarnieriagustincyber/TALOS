import importlib.util
import json
import sqlite3
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "generate_gate2_benchmark.py"
SPEC = importlib.util.spec_from_file_location(
    "generate_gate2_benchmark_integration", SCRIPT
)
assert SPEC and SPEC.loader
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


def test_snapshot_proposal_integration_writes_unapproved_qrels(tmp_path):
    knowledge = tmp_path / "knowledge.db"
    vector = tmp_path / "vector.db"
    connection = sqlite3.connect(knowledge)
    connection.executescript("""
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT);
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO chunks VALUES ('chunk-a', 'source-a');
        """)
    connection.commit()
    connection.close()
    connection = sqlite3.connect(vector)
    connection.execute("CREATE TABLE vectors (id TEXT)")
    connection.commit()
    connection.close()

    dataset = tmp_path / "dataset.json"
    dataset.write_text(
        json.dumps(
            {
                "queries": [
                    {
                        "query_id": "positive",
                        "query": "tema",
                        "kc_ids": [],
                    },
                    {
                        "query_id": "ood",
                        "query": "ajeno",
                        "kc_ids": [],
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    qrels = tmp_path / "qrels.json"
    qrels.write_text(
        json.dumps({"qrels": {"positive": {}, "ood": {}}}),
        encoding="utf-8",
    )
    decisions = tmp_path / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "decisions": {
                    "positive": {
                        "scope": "scope-a",
                        "oracle_type": "positive_in_scope",
                        "status": "approved",
                    },
                    "ood": {
                        "scope": "scope-a",
                        "oracle_type": "ood_global",
                        "status": "approved",
                    },
                }
            }
        ),
        encoding="utf-8",
    )

    def retriever(query, scope, source_ids, top_k):
        assert (scope, source_ids, top_k) == ("scope-a", ["source-a"], 3)
        if query == "tema":
            return [{"chunk_id": "chunk-a", "source_id": "source-a", "score": 2}]
        return []

    output = tmp_path / "proposal-output"
    generator.generate_snapshot_proposal(
        dataset,
        qrels,
        decisions,
        output,
        "v2.402-proposal-fixture",
        knowledge,
        vector,
        retriever,
        top_k=3,
    )

    generated = json.loads(
        (output / "gate2_v2.402-proposal-fixture.qrels.json").read_text()
    )
    manifest = json.loads(
        (output / "gate2_v2.402-proposal-fixture.manifest.json").read_text()
    )
    assert generated["qrels"] == {"positive": {"chunk-a": 1}, "ood": {}}
    assert generated["metadata"]["approved"] is False
    assert manifest["retrieval"]["qrels_provenance"] == "retrieval_proposal"
    observations = json.loads(
        (output / "gate2_v2.402-proposal-fixture.observations.json").read_text()
    )
    assert observations["observations"]["ood"]["status"] == "global_ood_check"
    assert observations["observations"]["ood"]["candidate_absence_passed"] is True
    assert not list(tmp_path.glob("talos-g2-snapshot-*"))
