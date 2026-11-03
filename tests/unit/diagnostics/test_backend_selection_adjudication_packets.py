import importlib.util
import json
import sqlite3
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[3]
    / "scripts"
    / "build_backend_selection_adjudication_packets.py"
)
SPEC = importlib.util.spec_from_file_location("backend_adjudication_packets", SCRIPT)
assert SPEC and SPEC.loader
packet_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(packet_module)


def _database():
    connection = sqlite3.connect(":memory:")
    connection.executescript(
        """
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        CREATE TABLE sources (
            source_id TEXT, sha256 TEXT, manifest_json TEXT, source_json TEXT,
            title TEXT, author TEXT, type TEXT, language TEXT, role TEXT,
            priority INTEGER, subject TEXT, course TEXT, phase TEXT, chapter TEXT,
            section TEXT, page INTEGER, created_at TEXT, metadata TEXT
        );
        CREATE TABLE chunks (
            id TEXT, document_id TEXT, source_id TEXT, content TEXT,
            page_start INTEGER, page_end INTEGER, chapter TEXT, section TEXT,
            token_count INTEGER, pos_index INTEGER, metadata TEXT,
            parent_chapter_id TEXT
        );
        INSERT INTO notebook_sources VALUES ('scope-a', 'source-a');
        INSERT INTO sources VALUES (
            'source-a', 'source-hash', '{}', '{}', 'Book', NULL, 'pdf',
            'es', 'PRIMARY', 1, NULL, NULL, NULL, NULL, NULL, NULL, NULL, '{}'
        );
        INSERT INTO chunks VALUES (
            'chunk-a', 'doc-a', 'source-a', 'Evidence', 1, 1, 'chapter',
            'section', 2, 0, '{}', NULL
        );
        """
    )
    return connection


def _inputs():
    dataset = {
        "version": "v2.400",
        "queries": [
            {
                "query_id": "GS2-OOD-001",
                "query": "Question text",
                "notebook_scope": ["scope-a"],
                "category": "ood_trampas",
                "tags": ["ood"],
                "expected": {"relevant_chunks": [], "abstention": True},
            }
        ],
    }
    qrels = {"version": "v2.400", "qrels": {"GS2-OOD-001": {}}}
    return dataset, qrels


def test_packets_blind_legacy_labels_and_keep_unjudged_explicit():
    dataset, qrels = _inputs()
    bundle = packet_module.build_bundle(
        dataset, qrels, _database(), "dataset-hash", "qrels-hash"
    )

    assert bundle["counts"]["query_count"] == 1
    assert bundle["counts"]["queries_without_legacy_qrels"] == 1
    assert bundle["review_policy"]["historical_qrels_are_not_disclosed"]
    packet_a = bundle["reviewer_packets"]["reviewer_a"][0]
    packet_b = bundle["reviewer_packets"]["reviewer_b"][0]
    assert packet_a["query"] == packet_b["query"] == "Question text"
    assert packet_a["case_id"] != packet_b["case_id"]
    assert packet_a["judgment_status"] == "UNJUDGED"
    assert packet_a["pair_judgments"] == []
    assert packet_a["scope_exhaustively_reviewed"] is False
    assert packet_a["case_id"] != "GS2-OOD-001"
    assert "category" not in packet_a
    assert "expected" not in packet_a
    assert "tags" not in packet_a
    assert "qrels" not in json.dumps(bundle["reviewer_packets"])


def test_rejects_qrel_chunk_outside_current_scope():
    dataset, qrels = _inputs()
    qrels["qrels"]["GS2-OOD-001"] = {"outside-chunk": 3}

    with pytest.raises(packet_module.PacketError, match="missing or outside"):
        packet_module.build_bundle(
            dataset, qrels, _database(), "dataset-hash", "qrels-hash"
        )


def test_rejects_qrel_query_id_mismatch():
    dataset, qrels = _inputs()
    qrels["qrels"] = {"other-query": {}}

    with pytest.raises(packet_module.PacketError, match="IDs do not exactly match"):
        packet_module.build_bundle(
            dataset, qrels, _database(), "dataset-hash", "qrels-hash"
        )


def test_writer_refuses_to_replace_existing_packet_bundle(tmp_path):
    output = tmp_path / "packet"
    output.mkdir()

    with pytest.raises(packet_module.PacketError, match="Refusing to overwrite"):
        packet_module._write_bundle({}, output)


def test_cli_generated_packets_do_not_contain_legacy_qrel_values(tmp_path):
    dataset, qrels = _inputs()
    dataset_path = tmp_path / "dataset.json"
    qrels_path = tmp_path / "qrels.json"
    database_path = tmp_path / "knowledge.db"
    dataset_path.write_text(json.dumps(dataset), encoding="utf-8")
    qrels_path.write_text(json.dumps(qrels), encoding="utf-8")

    connection = _database()
    disk_connection = sqlite3.connect(database_path)
    connection.backup(disk_connection)
    disk_connection.close()
    connection.close()
    output = tmp_path / "bundle"
    code = packet_module.main(
        [
            "--dataset",
            str(dataset_path),
            "--qrels",
            str(qrels_path),
            "--database",
            str(database_path),
            "--output-dir",
            str(output),
        ]
    )

    assert code == 0
    reviewer_a = json.loads((output / "reviewer_a.json").read_text())
    assert reviewer_a["cases"][0]["judgment_status"] == "UNJUDGED"
    assert reviewer_a["cases"][0]["pair_judgments"] == []
    assert "GS2-OOD-001" not in (output / "reviewer_a.json").read_text()
    assert reviewer_a["source"] == {
        "adjudication_batch": "backend-selection-v1"
    }
    assert (output / "restricted_reconciliation_map.json").exists()
    manifest = json.loads((output / "evidence_manifest.json").read_text())
    assert manifest["status"] == "READY_FOR_HUMAN_ADJUDICATION"
    assert manifest["source"]["dataset_version"] == "v2.400"
    assert manifest["source"]["qrels_sha256"] == packet_module._sha256_file(
        qrels_path
    )
