import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "build_gate2_v2400_query_adjudication_queue.py"
)
SPEC = importlib.util.spec_from_file_location("gate2_v2400_adjudication_queue", SCRIPT)
assert SPEC and SPEC.loader
queue_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(queue_module)


def _inventory():
    return {
        "schema_version": "gate2-v2400-coverage-inventory-v1",
        "generated_at": "2026-09-28",
        "canonical_source": {
            "version": "v2.400",
            "dataset_sha256": "sha256:dataset",
            "qrels_sha256": "sha256:qrels",
        },
        "counts": {
            "query_status_counts": {"PENDING_ADJUDICATION": 2},
        },
        "queries": [
            {
                "query_id": "pending-with-qrel",
                "scope": "scope-a",
                "query": "What is being asked?",
                "category": "fundamentos",
                "oracle_type": "retrieval_citation",
                "expected_abstention": False,
                "historical_qrel_count": 2,
                "historical_qrel_status": "PARTIAL",
                "query_status": "PENDING_ADJUDICATION",
            },
            {
                "query_id": "pending-without-qrel",
                "scope": "scope-b",
                "query": "No historical qrel.",
                "category": "fundamentos",
                "oracle_type": "retrieval_citation",
                "expected_abstention": None,
                "historical_qrel_count": 0,
                "historical_qrel_status": "ABSENT",
                "query_status": "PENDING_ADJUDICATION",
            },
            {
                "query_id": "approved",
                "scope": "scope-a",
                "query": "Already reviewed.",
                "category": "fundamentos",
                "oracle_type": "retrieval_citation",
                "expected_abstention": False,
                "historical_qrel_count": 1,
                "historical_qrel_status": "VALID",
                "query_status": "APPROVED_POSITIVE",
            },
        ],
        "qrel_references": [
            {
                "query_id": "pending-with-qrel",
                "chunk_id": "chunk-pending",
                "qrel_grade": 2,
                "qrel_status": "PENDING",
                "acl_status": "IN_SCOPE",
                "semantic_status": "PENDING",
                "decision": "PENDING",
                "source_id": "source-a",
                "evidence_source": "pending_adjudication",
            },
            {
                "query_id": "pending-with-qrel",
                "chunk_id": "chunk-recorded",
                "qrel_grade": 1,
                "qrel_status": "INVALID",
                "acl_status": "IN_SCOPE",
                "semantic_status": "INVALID_SEMANTIC",
                "decision": "EXCLUDE",
                "source_id": "source-a",
                "evidence_source": "decision-register.json",
            },
            {
                "query_id": "approved",
                "chunk_id": "chunk-approved",
                "qrel_grade": 3,
                "qrel_status": "VALID",
                "acl_status": "IN_SCOPE",
                "semantic_status": "CONFIRMED",
                "decision": "KEEP",
                "source_id": "source-a",
                "evidence_source": "decision-register.json",
            },
        ],
    }


def test_queue_targets_pending_queries_with_qrels_and_keeps_decisions_separate():
    queue = queue_module.build_queue(_inventory())

    assert queue["counts"]["query_status_pending_total"] == 2
    assert queue["counts"]["pending_queries_with_historical_qrels"] == 1
    assert queue["counts"]["pending_queries_without_historical_qrels"] == 1
    assert queue["counts"]["qrel_references_for_queued_queries"] == 2
    assert queue["counts"]["qrel_status_counts"] == {"INVALID": 1, "PENDING": 1}
    assert len(queue["items"]) == 1
    item = queue["items"][0]
    assert item["query_id"] == "pending-with-qrel"
    assert item["query_decision"] is None
    assert [qrel["chunk_id"] for qrel in item["qrel_references"]] == [
        "chunk-pending",
        "chunk-recorded",
    ]
    assert [
        qrel["review_status"] for qrel in item["qrel_references"]
    ] == ["PENDING_ADJUDICATION", "ALREADY_RECORDED"]
    assert item["qrel_references"][1]["existing_decision"] == "EXCLUDE"
    assert queue["review_policy"]["no_automatic_negative_inference_from_absent_qrels"]


def test_queue_rejects_qrel_count_mismatches():
    inventory = _inventory()
    inventory["queries"][0]["historical_qrel_count"] = 1

    with pytest.raises(queue_module.QueueError, match="count mismatch"):
        queue_module.build_queue(inventory)


def test_writer_refuses_overwrite_unless_explicitly_enabled(tmp_path):
    queue = queue_module.build_queue(_inventory())
    output_json = tmp_path / "queue.json"
    output_markdown = tmp_path / "queue.md"
    output_json.write_text("preserve", encoding="utf-8")

    with pytest.raises(queue_module.QueueError, match="Refusing to overwrite"):
        queue_module.write_outputs(queue, output_json, output_markdown)

    assert output_json.read_text(encoding="utf-8") == "preserve"


def test_writer_cannot_replace_protected_inventory(tmp_path):
    queue = queue_module.build_queue(_inventory())
    inventory_path = tmp_path / "inventory.json"

    with pytest.raises(queue_module.QueueError, match="must not replace"):
        queue_module.write_outputs(
            queue,
            inventory_path,
            tmp_path / "queue.md",
            overwrite_existing=True,
            protected_paths=(inventory_path,),
        )

    assert not inventory_path.exists()
