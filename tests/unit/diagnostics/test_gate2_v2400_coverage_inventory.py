import importlib.util
import sqlite3
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "build_gate2_v2400_coverage_inventory.py"
)
SPEC = importlib.util.spec_from_file_location("gate2_v2400_inventory", SCRIPT)
assert SPEC and SPEC.loader
inventory_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inventory_module)


def _write_database(path: Path):
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT, content TEXT);
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO notebook_sources VALUES ('scope-b', 'source-b');
        INSERT INTO chunks VALUES ('chunk-a', 'source-a', 'Confirmed evidence');
        INSERT INTO chunks VALUES ('chunk-b', 'source-b', 'Other scope evidence');
        """
    )
    connection.commit()
    connection.close()


def _payloads():
    dataset = {
        "golden_set_version": "v2.400",
        "queries": [
            {
                "query_id": "positive-a",
                "query": "Explain the confirmed topic.",
                "category": "fundamentos",
                "notebook_scope": ["scope-a"],
                "oracle_type": "retrieval_citation",
                "kc_ids": ["kc-a"],
                "tags": ["positive"],
                "expected": {"abstention": False},
            },
            {
                "query_id": "ood-a",
                "query": "An unrelated question?",
                "category": "ood_trampas",
                "notebook_scope": ["scope-a"],
                "oracle_type": "abstention_oracle",
                "kc_ids": [],
                "tags": ["ood"],
                "expected": {"abstention": True},
            },
        ],
    }
    qrels = {
        "version": "v2.400",
        "qrels": {"positive-a": {"chunk-a": 3}, "ood-a": {}},
    }
    decisions = {
        "query_decisions": {
            "ood-a": {
                "query_status": "APPROVED_OOD",
                "reason": "Explicitly approved OOD fixture.",
                "evidence_source": "fixture-review",
            }
        },
        "qrel_decisions": [
            {
                "query_id": "positive-a",
                "chunk_id": "chunk-a",
                "decision": "KEEP",
                "semantic_status": "CONFIRMED",
                "approved_grade": 3,
                "reason": "Direct evidence approved.",
                "evidence_source": "user-adjudication",
            }
        ],
        "scope_decisions": {},
        "audit_reference": {
            "version": "v2.401",
            "canonical_for_repair": False,
            "historical_evidence": True,
            "scope_qrel_finding": "Historical scope changes audited.",
            "action": "NONE",
        },
    }
    audit_dataset = {
        "golden_set_version": "v2.401",
        "queries": [
            {**dataset["queries"][0], "notebook_scope": ["scope-b"]},
            dataset["queries"][1],
        ],
    }
    audit_qrels = {
        "version": "v2.401",
        "qrels": {
            "positive-a": {"chunk-b": 2},
            "ood-a": {},
        },
    }
    return dataset, qrels, decisions, audit_dataset, audit_qrels


def test_inventory_separates_query_and_qrel_decisions_and_records_scope_violation(
    tmp_path,
):
    database = tmp_path / "knowledge.db"
    _write_database(database)
    dataset, qrels, decisions, audit_dataset, audit_qrels = _payloads()

    inventory = inventory_module.build_inventory(
        dataset,
        qrels,
        decisions,
        v2401_dataset_payload=audit_dataset,
        v2401_qrels_payload=audit_qrels,
        dataset_sha256="sha256:v400",
        qrels_sha256="sha256:v400-qrels",
        knowledge_db=database,
        knowledge_db_sha256="sha256:db",
        v2401_dataset_sha256="sha256:v401",
        v2401_qrels_sha256="sha256:v401-qrels",
    )

    assert inventory["counts"]["query_count"] == 2
    assert inventory["counts"]["qrel_reference_count"] == 1
    assert inventory["counts"]["query_status_counts"]["APPROVED_OOD"] == 1
    assert inventory["counts"]["query_status_counts"]["APPROVED_POSITIVE"] == 1
    assert sum(inventory["counts"]["query_status_counts"].values()) == 2
    assert inventory["counts"]["qrel_status_counts"]["VALID"] == 1
    assert sum(inventory["counts"]["qrel_status_counts"].values()) == 1
    assert inventory["qrel_references"][0]["decision"] == "KEEP"
    assert inventory["qrel_references"][0]["acl_status"] == "IN_SCOPE"
    assert inventory["audit_reference"]["canonical_for_repair"] is False
    assert inventory["audit_reference"]["action"] == "NONE"
    assert inventory["counts"]["v2401_changed_scope_query_count"] == 1
    assert inventory["counts"]["v2401_changed_scope_qrel_reference_count"] == 1
    assert (
        inventory["counts"]["v2401_changed_scope_qrels_outside_v2400_acl"] == 1
    )
    imported_scope = next(
        row for row in inventory["scope_summaries"] if row["scope"] == "scope-b"
    )
    assert imported_scope["v2401_imported_query_count"] == 1
    assert imported_scope["historical_scope_integrity"] == "VIOLATION_DETECTED"
    assert inventory["counts"]["qrel_references_outside_acl"] == 0
    assert next(
        row
        for row in inventory["queries"]
        if row["query_id"] == "positive-a"
    )["v2401_scope_changed"] is True


def test_unadjudicated_qrel_stays_pending_even_when_acl_membership_is_valid(tmp_path):
    database = tmp_path / "knowledge.db"
    _write_database(database)
    dataset, qrels, decisions, audit_dataset, audit_qrels = _payloads()
    decisions["qrel_decisions"] = []

    inventory = inventory_module.build_inventory(
        dataset,
        qrels,
        decisions,
        v2401_dataset_payload=audit_dataset,
        v2401_qrels_payload=audit_qrels,
        dataset_sha256="sha256:v400",
        qrels_sha256="sha256:v400-qrels",
        knowledge_db=database,
        knowledge_db_sha256="sha256:db",
        v2401_dataset_sha256="sha256:v401",
        v2401_qrels_sha256="sha256:v401-qrels",
    )

    row = inventory["qrel_references"][0]
    assert row["acl_status"] == "IN_SCOPE"
    assert row["semantic_status"] == "PENDING"
    assert row["qrel_status"] == "PENDING"
    assert row["decision"] == "PENDING"
    assert inventory["queries"][0]["query_status"] == "PENDING_ADJUDICATION"


def test_rejects_decision_for_non_historical_qrel_pair(tmp_path):
    database = tmp_path / "knowledge.db"
    _write_database(database)
    dataset, qrels, decisions, audit_dataset, audit_qrels = _payloads()
    decisions["qrel_decisions"].append(
        {
            "query_id": "positive-a",
            "chunk_id": "not-a-historical-qrel",
            "decision": "KEEP",
            "semantic_status": "CONFIRMED",
            "reason": "Not present in historical qrels.",
            "evidence_source": "test",
        }
    )

    with pytest.raises(inventory_module.InventoryError, match="non-historical"):
        inventory_module.build_inventory(
            dataset,
            qrels,
            decisions,
            v2401_dataset_payload=audit_dataset,
            v2401_qrels_payload=audit_qrels,
            dataset_sha256="sha256:v400",
            qrels_sha256="sha256:v400-qrels",
            knowledge_db=database,
            knowledge_db_sha256="sha256:db",
            v2401_dataset_sha256="sha256:v401",
            v2401_qrels_sha256="sha256:v401-qrels",
        )


def test_non_ood_abstention_assertion_remains_pending_not_semantically_rejected():
    status, reason, _ = inventory_module._query_status(
        query_id="legacy-negative",
        category="fundamentos",
        oracle_type="abstention_oracle",
        qrel_rows=[],
        explicit_decision=None,
    )

    assert status == "PENDING_ADJUDICATION"
    assert "has not been adjudicated" in reason


def test_query_qrel_status_preserves_absent_and_mixed_reference_states():
    assert inventory_module._aggregate_qrel_status([]) == "ABSENT"
    assert (
        inventory_module._aggregate_qrel_status(
            [
                {"qrel_status": "VALID"},
                {"qrel_status": "INVALID"},
                {"qrel_status": "PENDING"},
            ]
        )
        == "PARTIAL"
    )
    assert (
        inventory_module._aggregate_qrel_status(
            [
                {"qrel_status": "INVALID"},
                {"qrel_status": "PENDING"},
            ]
        )
        == "PENDING"
    )


def test_query_with_kept_excluded_and_pending_qrels_is_partially_valid():
    status, _, _ = inventory_module._query_status(
        query_id="mixed",
        category="fundamentos",
        oracle_type="retrieval_citation",
        qrel_rows=[
            {"acl_status": "IN_SCOPE", "chunk_status": "VALID", "decision": "KEEP",
             "semantic_status": "CONFIRMED"},
            {"acl_status": "IN_SCOPE", "chunk_status": "INVALID_SEMANTIC",
             "decision": "EXCLUDE", "semantic_status": "INVALID_SEMANTIC"},
            {"acl_status": "IN_SCOPE", "chunk_status": "PENDING_ADJUDICATION",
             "decision": "PENDING", "semantic_status": "PENDING"},
        ],
        explicit_decision=None,
    )

    assert status == "PARTIALLY_VALID"


def test_output_paths_cannot_replace_an_inventory_input(tmp_path):
    input_path = tmp_path / "canonical.json"

    with pytest.raises(inventory_module.InventoryError, match="must not replace"):
        inventory_module.generate_inventory(
            dataset_path=input_path,
            qrels_path=tmp_path / "qrels.json",
            v2401_dataset_path=tmp_path / "v401.json",
            v2401_qrels_path=tmp_path / "v401.qrels.json",
            decision_register_path=tmp_path / "decisions.json",
            knowledge_db_path=tmp_path / "knowledge.db",
            output_json=input_path,
            output_markdown=tmp_path / "inventory.md",
            overwrite_existing=True,
        )
