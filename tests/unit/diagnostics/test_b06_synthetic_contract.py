"""B06-only synthetic exception: no captured SQL input or general redirection."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

from scripts import quality_gate as gate
from tests.conftest import _build_b06_synthetic_state, b06_synthetic_state
from study_engine.retrieval.embedding import DeterministicHashEmbedder
from study_engine.retrieval.vector_identity import vector_space_id
from study_engine.retrieval.vector_store import SQLiteVectorStore

ROOT = Path(__file__).resolve().parents[3]


def profile():
    return json.loads((ROOT / "config/test_perimeter.json").read_text())[
        "focal_execution_profiles"]["b06-snapshot-v1"]


def test_b06_contract_retains_captured_inputs_and_checks_explicit_exception():
    value = profile()
    assert value["fixture_constraints"]["working_directory"] == "derived_snapshot_only"
    assert value["fixture_constraints"]["database_identities"] == [
        "knowledge_store", "vector_store", "student_state"]
    assert value["b06_synthetic_exception"] == gate.B06_SYNTHETIC_EXCEPTION
    gate._validate_focal_fixture_contract(ROOT, value)


@pytest.mark.parametrize("field,value", [
    ("nodeid", "tests/other.py::test_other"),
    ("fixture", "web_state_test_copy"),
    ("working_directory", "/arbitrary"),
    ("captured_inputs", "optional"),
])
def test_exception_cannot_be_generalized(field, value):
    config = deepcopy(profile())
    config["b06_synthetic_exception"][field] = value
    with pytest.raises(gate.FocalExecutionError, match="restricted"):
        gate._validate_focal_fixture_contract(ROOT, config)


def test_other_profile_node_cannot_reuse_exception():
    config = deepcopy(profile())
    config["nodeid"] = "tests/other.py::test_other"
    with pytest.raises(gate.FocalExecutionError, match="restricted"):
        gate._validate_focal_fixture_contract(ROOT, config)


def isolated(monkeypatch, tmp_path):
    captured = tmp_path / "captured"
    captured.mkdir()
    monkeypatch.setenv("TALOS_TEST_ISOLATED", "1")
    monkeypatch.setenv("TALOS_TEST_WORKSPACE_ROOT", str(captured))
    monkeypatch.setenv("TALOS_TEST_WORKSPACE_IDENTITY", str(captured))
    run_id = str(uuid4())
    monkeypatch.setenv("TALOS_TEST_RUN_ID", run_id)
    (captured / ".talos-test-workspace.json").write_text(json.dumps({
        "manifest_sha256": "sha256:" + "a" * 64,
        "run_identity": run_id, "workspace_identity": str(captured),
    }))
    return captured


def test_b06_workspace_is_fixed_sibling_not_arbitrary(monkeypatch, tmp_path):
    captured = isolated(monkeypatch, tmp_path)
    assert gate.b06_synthetic_workspace(captured, gate.FOCAL_B06_NODEID) == tmp_path / "b06-synthetic"
    with pytest.raises(gate.FocalExecutionError, match="arbitrary"):
        gate.b06_synthetic_workspace(tmp_path / "elsewhere", gate.FOCAL_B06_NODEID)
    (tmp_path / "b06-synthetic").symlink_to(captured, target_is_directory=True)
    with pytest.raises(gate.FocalExecutionError, match="symlink"):
        gate.b06_synthetic_workspace(captured, gate.FOCAL_B06_NODEID)


def test_other_suite_cannot_use_exception(monkeypatch, tmp_path):
    captured = isolated(monkeypatch, tmp_path)
    with pytest.raises(gate.FocalExecutionError, match="exact B06"):
        gate.b06_synthetic_workspace(captured, "tests/audit/test_other.py::test_other")
    request = SimpleNamespace(node=SimpleNamespace(nodeid="tests/other.py::test_other"))
    fixture = b06_synthetic_state.__wrapped__(request, tmp_path)
    with pytest.raises(pytest.UsageError, match="exact B06"):
        next(fixture)


def test_synthetic_schema_and_vectors_have_known_canonical_identity(tmp_path):
    workspace = _build_b06_synthetic_state(tmp_path / "b06-synthetic")
    store = SQLiteVectorStore(workspace / "vector_store.db")
    try:
        expected = vector_space_id(DeterministicHashEmbedder(dimensions=128))
        assert expected is not None
        assert store.list_space_ids("fase0-soc") == {expected}
        records = store.get_by_notebook("fase0-soc")
        assert len(records) == 1
        assert records[0].space_id == expected
        assert records[0].source_id == "b06-synthetic-pointers"
        assert records[0].vector == pytest.approx(
            DeterministicHashEmbedder(dimensions=128).embed_passages([
                "Los punteros en C contienen direcciones de memoria."])[0])
    finally:
        store._conn.close()


def test_isolated_fixture_never_opens_captured_sql(monkeypatch, tmp_path):
    captured = isolated(monkeypatch, tmp_path)
    names = ("knowledge_store.db", "vector_store.db", "student_state.db")
    for name in names:
        (captured / name).write_bytes(b"synthetic-not-a-SQLite-database")
    before = {name: (captured / name).read_bytes() for name in names}
    request = SimpleNamespace(node=SimpleNamespace(nodeid=gate.FOCAL_B06_NODEID),
                              getfixturevalue=lambda name: captured)
    fixture = b06_synthetic_state.__wrapped__(request, tmp_path)
    workspace = next(fixture)
    # This unit test represents the later container-created student DB only.
    (workspace / "student_state.db").touch()
    with pytest.raises(StopIteration):
        next(fixture)
    assert {name: (captured / name).read_bytes() for name in names} == before
    marker = workspace / ".b06-synthetic.json"
    value = json.loads(marker.read_text())
    value["space_id"] = "UNKNOWN"
    marker.write_text(json.dumps(value))
    with pytest.raises(gate.FocalExecutionError, match="provenance mismatch"):
        gate.validate_b06_synthetic_state(captured, gate.FOCAL_B06_NODEID)
