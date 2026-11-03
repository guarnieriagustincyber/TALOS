"""EP-04B: synthetic fault injection and real process serialization, no production data.

Oracles: raw SQLite rows, unchanged historical bytes, published JSONL hashes,
stable K/R replay decisions, and process events (not an in-memory lock mock).
These tests do not establish physical power-loss durability.
"""

import hashlib
import json
import multiprocessing
import os
from pathlib import Path
import sqlite3
import stat
from unittest.mock import patch

import pytest

from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    IdempotentReplayError, InconsistentReplayError, LedgerIntegrityStatus,
    LedgerIntegrityViolationError,
)
from tests.unit.state.test_ledger import _make_record


def record(key):
    return _make_record(key).model_copy(update={
        "student_id": "student-synthetic",
        "metadata": {"evaluation_attempt_id": key},
        "assessment_digest": hashlib.sha256(key.encode()).hexdigest(),
    })


def count_rows(path):
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        return conn.execute("SELECT COUNT(*) FROM evidence_ledger").fetchone()[0]
    finally:
        conn.close()


def published(path):
    return [json.loads(line) for line in path.with_suffix(".jsonl").read_text().splitlines()]


def check_consistent(path, count):
    ledger = EvidenceLedger(path)
    try:
        assert ledger.total_entries == count
        assert ledger.verify_integrity().status == LedgerIntegrityStatus.VALID
        assert [entry["entry_hash"] for entry in published(path)] == [
            ledger.get_entry_by_index(i).entry_hash for i in range(count)
        ]
    finally:
        ledger._conn.close()


class CommitFailure:
    def __init__(self, connection, before_failure=lambda: None):
        self.connection = connection
        self.before_failure = before_failure

    def __getattr__(self, name):
        return getattr(self.connection, name)

    def execute(self, sql, *args):
        if sql == "COMMIT":
            self.before_failure()
            raise OSError("injected pre-commit failure")
        return self.connection.execute(sql, *args)


@pytest.mark.parametrize("legacy_artifact", ["absent", "complete", "partial"])
def test_rollback_never_resurrects_even_with_legacy_precommit_jsonl(tmp_path, legacy_artifact):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    connection = ledger._conn
    jsonl = path.with_suffix(".jsonl")

    def legacy_write():
        if legacy_artifact != "absent":
            payload = connection.execute("SELECT payload_json FROM evidence_ledger").fetchone()[0]
            jsonl.write_text(payload + "\n" if legacy_artifact == "complete" else payload[:40])

    ledger._conn = CommitFailure(connection, legacy_write)
    with pytest.raises(OSError, match="pre-commit"):
        ledger.append_record(record("reverted"))
    connection.close()
    assert count_rows(path) == 0
    if legacy_artifact == "absent":
        reopened = EvidenceLedger(path)
        assert reopened.total_entries == 0
        assert not jsonl.exists()
        reopened._conn.close()
    else:
        original = jsonl.read_bytes()
        with pytest.raises(LedgerIntegrityViolationError):
            EvidenceLedger(path)
        assert count_rows(path) == 0 and jsonl.read_bytes() == original


def test_commit_survives_export_failure_and_replay_conflict(tmp_path, caplog):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    original = record("confirmed")
    with patch.object(ledger, "export_jsonl", side_effect=OSError("injected export failure")):
        entry = ledger.append_record(original)
    assert ledger.export_pending and ledger.total_entries == 1
    assert "commit confirmed" in caplog.text and "export pending" in caplog.text
    ledger._conn.close()
    for _ in range(2):
        ledger = EvidenceLedger(path)
        assert ledger.export_pending
        assert ledger.get_entry_by_index(0).entry_hash == entry.entry_hash
        with pytest.raises(IdempotentReplayError):
            ledger.append_record(original)
        with pytest.raises(InconsistentReplayError):
            ledger.append_record(original.model_copy(update={"assessment_digest": "f" * 64}))
        assert ledger.total_entries == 1
        ledger._conn.close()
    ledger = EvidenceLedger(path)
    ledger.export_jsonl()
    assert not ledger.export_pending
    ledger._conn.close()
    check_consistent(path, 1)


@pytest.mark.parametrize("fault", ["partial_write", "file_sync", "replace", "directory_sync"])
def test_publication_failures_never_revert_commit_or_publish_partial_jsonl(tmp_path, fault):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    ledger.append_record(record("first"))
    old_export = path.with_suffix(".jsonl").read_bytes()
    real_sync = os.fsync

    def fail_sync(fd):
        directory = stat.S_ISDIR(os.fstat(fd).st_mode)
        if directory == (fault == "directory_sync"):
            raise OSError("injected sync failure")
        return real_sync(fd)

    from study_engine.state import ledger as module
    real_temporary = module.tempfile.NamedTemporaryFile

    class PartialWrite:
        def __init__(self, stream):
            self.stream = stream

        def __getattr__(self, name):
            return getattr(self.stream, name)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def write(self, text):
            self.stream.write(text[:30])
            raise OSError("injected partial write")

    if fault == "partial_write":
        injection = patch.object(module.tempfile, "NamedTemporaryFile", side_effect=lambda **kw: PartialWrite(real_temporary(**kw)))
    elif fault == "replace":
        injection = patch.object(module.os, "replace", side_effect=OSError("injected replace failure"))
    else:
        injection = patch.object(module.os, "fsync", fail_sync)
    with injection:
        entry = ledger.append_record(record("second"))
    assert entry.entry_index == 1 and count_rows(path) == 2 and ledger.export_pending
    assert not list(tmp_path.glob("*.tmp"))
    assert len(published(path)) == (2 if fault == "directory_sync" else 1)
    if fault != "directory_sync":
        assert path.with_suffix(".jsonl").read_bytes() == old_export
    ledger._conn.close()
    # Opening detects status without rewriting a stale but compatible export.
    before = path.with_suffix(".jsonl").read_bytes()
    reopened = EvidenceLedger(path)
    assert reopened.total_entries == 2
    assert path.with_suffix(".jsonl").read_bytes() == before
    reopened.export_jsonl()
    reopened._conn.close()
    check_consistent(path, 2)


@pytest.mark.parametrize("artifact", ["extra", "partial", "corrupt", "valid_but_different"])
def test_historical_discrepancies_are_preserved_not_repaired(tmp_path, artifact):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    first = ledger.append_record(record("first"))
    ledger._conn.close()
    jsonl = path.with_suffix(".jsonl")
    if artifact in {"extra", "valid_but_different"}:
        unrelated = EvidenceLedger()
        if artifact == "extra":
            unrelated.append_record(first.record, override_committed_at=first.committed_at)
        else:
            unrelated.append_record(record("other"))
        if artifact == "extra":
            unrelated.append_record(record("extra"))
        replacement = "".join(e.model_dump_json() + "\n" for e in unrelated._entries)
        unrelated._conn.close()
        jsonl.write_text(replacement)
    elif artifact == "partial":
        with jsonl.open("a") as stream:
            stream.write('{"entry_index":1')
    else:
        jsonl.write_text("not-json\n")
    original = jsonl.read_bytes()
    with pytest.raises(LedgerIntegrityViolationError):
        EvidenceLedger(path)
    assert count_rows(path) == 1 and jsonl.read_bytes() == original


def test_jsonl_only_cannot_create_authoritative_sqlite(tmp_path):
    scratch = EvidenceLedger()
    entry = scratch.append_record(record("historical"))
    scratch._conn.close()
    path = tmp_path / "history.jsonl"
    path.write_text(entry.model_dump_json() + "\n")
    before = path.read_bytes()
    with pytest.raises(LedgerIntegrityViolationError, match="without authoritative SQLite"):
        EvidenceLedger(path)
    assert not path.with_suffix(".db").exists() and path.read_bytes() == before


def test_existing_non_ledger_database_is_not_initialized_or_migrated(tmp_path):
    path = tmp_path / "other.db"
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE unrelated (id INTEGER)")
    connection.commit()
    connection.close()
    before = path.read_bytes()
    with pytest.raises(LedgerIntegrityViolationError, match="no authoritative ledger table"):
        EvidenceLedger(path)
    assert path.read_bytes() == before


@pytest.mark.parametrize("suffix", ["", "-wal", "-shm"])
def test_export_rejects_discrepant_destination_and_database_target(tmp_path, suffix):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    ledger.append_record(record("first"))
    target = tmp_path / "historical.jsonl"
    target.write_text("historical conflicting bytes\n")
    before = target.read_bytes()
    with pytest.raises(LedgerIntegrityViolationError):
        ledger.export_jsonl(target)
    assert target.read_bytes() == before
    with pytest.raises(ValueError, match="authoritative SQLite"):
        ledger.export_jsonl(Path(str(path) + suffix))
    assert ledger.total_entries == 1
    ledger._conn.close()


def test_sqlite_identity_corruption_cannot_be_repaired_from_jsonl(tmp_path):
    path = tmp_path / "synthetic.db"
    ledger = EvidenceLedger(path)
    ledger.append_record(record("first"))
    before = path.with_suffix(".jsonl").read_bytes()
    ledger._conn.execute("UPDATE evidence_ledger SET student_id='conflicting-student'")
    ledger._conn.close()
    with pytest.raises(LedgerIntegrityViolationError, match="identity/payload mismatch"):
        EvidenceLedger(path)
    assert path.with_suffix(".jsonl").read_bytes() == before
    assert count_rows(path) == 1


def _crash_after_commit(path):
    ledger = EvidenceLedger(Path(path))
    ledger.export_jsonl = lambda: os._exit(0)
    ledger.append_record(record("crashed-after-commit"))


def test_process_exit_after_commit_before_ack_is_recoverable(tmp_path):
    path = tmp_path / "synthetic.db"
    ctx = multiprocessing.get_context("spawn")
    child = ctx.Process(target=_crash_after_commit, args=(str(path),))
    child.start()
    child.join(15)
    assert child.exitcode == 0
    ledger = EvidenceLedger(path)
    assert ledger.total_entries == 1 and ledger.export_pending
    # Recover identity/result from SQLite rather than regrading with a new identity.
    original = ledger.get_entry_by_index(0).record
    with pytest.raises(IdempotentReplayError):
        ledger.append_record(original)
    with pytest.raises(InconsistentReplayError):
        ledger.append_record(original.model_copy(update={"assessment_digest": "e" * 64}))
    ledger.export_jsonl()
    ledger._conn.close()
    check_consistent(path, 1)


def _export_process(path, barrier):
    ledger = EvidenceLedger(Path(path))
    barrier.wait(timeout=10)
    ledger.export_jsonl()
    ledger._conn.close()


def _write_process(path, key, barrier):
    ledger = EvidenceLedger(Path(path))
    barrier.wait(timeout=10)
    ledger.append_record(record(key))
    ledger._conn.close()


def _join(children):
    for child in children:
        child.join(15)
        if child.is_alive():
            child.terminate()
            child.join(5)
        assert child.exitcode == 0


@pytest.mark.parametrize("operation", ["export", "write"])
def test_two_processes_export_or_commit_without_regressing_projection(tmp_path, operation):
    path = tmp_path / "synthetic.db"
    seed = EvidenceLedger(path)
    seed.append_record(record("seed"))
    seed._conn.close()
    ctx = multiprocessing.get_context("spawn")
    barrier = ctx.Barrier(3)
    children = [
        ctx.Process(target=_export_process, args=(str(path), barrier)) if operation == "export"
        else ctx.Process(target=_write_process, args=(str(path), f"independent-{i}", barrier))
        for i in range(2)
    ]
    for child in children:
        child.start()
    barrier.wait(timeout=10)
    _join(children)
    check_consistent(path, 1 if operation == "export" else 3)


def _paused_export(path, ready, release):
    from study_engine.state import ledger as module
    ledger = EvidenceLedger(Path(path))
    replace = module.os.replace

    def pause(source, target):
        ready.set()
        if not release.wait(10):
            raise TimeoutError("export release missing")
        replace(source, target)

    with patch.object(module.os, "replace", pause):
        ledger.export_jsonl()
    ledger._conn.close()


def _writer_during_export(path, started, done):
    started.set()
    ledger = EvidenceLedger(Path(path))
    ledger.append_record(record("concurrent-writer"))
    ledger._conn.close()
    done.set()


def test_slow_export_holds_sqlite_reservation_until_publication(tmp_path):
    path = tmp_path / "synthetic.db"
    seed = EvidenceLedger(path)
    seed.append_record(record("seed"))
    seed._conn.close()
    ctx = multiprocessing.get_context("spawn")
    ready, release, started, done = (ctx.Event() for _ in range(4))
    exporter = ctx.Process(target=_paused_export, args=(str(path), ready, release))
    writer = ctx.Process(target=_writer_during_export, args=(str(path), started, done))
    exporter.start()
    try:
        assert ready.wait(10)
        writer.start()
        assert started.wait(10)
        assert not done.wait(0.2)
    finally:
        release.set()
    _join([exporter, writer])
    check_consistent(path, 2)


def test_late_export_from_stale_instance_reads_new_committed_snapshot(tmp_path):
    path = tmp_path / "synthetic.db"
    writer = EvidenceLedger(path)
    writer.append_record(record("first"))
    stale = EvidenceLedger(path)
    writer.append_record(record("second"))
    assert len(stale._entries) == 1
    stale.export_jsonl()
    stale._conn.close()
    writer._conn.close()
    check_consistent(path, 2)


def _export_with_delayed_preparation(path, ready, release):
    from study_engine.state import ledger as module
    ledger = EvidenceLedger(Path(path))
    sync = module.os.fsync

    def delay_after_file_sync(fd):
        sync(fd)
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            ready.set()
            if not release.wait(10):
                raise TimeoutError("preparation release missing")

    with patch.object(module.os, "fsync", delay_after_file_sync):
        try:
            ledger.export_jsonl()
        except RuntimeError as error:
            assert "superseded" in str(error)
            assert ledger.export_pending
        else:
            raise AssertionError("A stale prepared snapshot must not be published")
    ledger._conn.close()


def test_prepared_old_snapshot_cannot_replace_newer_export_across_processes(tmp_path):
    path = tmp_path / "synthetic.db"
    writer = EvidenceLedger(path)
    writer.append_record(record("seed"))
    ctx = multiprocessing.get_context("spawn")
    ready, release = ctx.Event(), ctx.Event()
    exporter = ctx.Process(target=_export_with_delayed_preparation, args=(str(path), ready, release))
    exporter.start()
    try:
        assert ready.wait(10)
        # Preparation holds no writer reservation: this can commit before release.
        writer.append_record(record("newer"))
        assert len(published(path)) == 2
    finally:
        release.set()
    _join([exporter])
    writer._conn.close()
    check_consistent(path, 2)
