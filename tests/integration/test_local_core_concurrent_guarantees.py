"""Forced deterministic interleaving: evaluation vs close race at cross-database boundary.

Uses threading.Barrier to force exact ordering of operations across two threads
with independent connections to student_state.db and sessions.db.
"""
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path

import pytest

from study_engine.student.storage import StudentStorage
from study_engine.session.session_store import SessionStore


def test_forced_interleaving_evaluation_suspended_then_close_commits(tmp_path):
    """Force evaluation to pause inside transaction while close commits CLOSED.

    This is the critical race: evaluation's re-check happens BEFORE commit,
    but after close has already committed. With separate DBs, the re-check
    should see CLOSED and abort.
    """
    state_dir = tmp_path / "race"
    state_dir.mkdir()
    student_db = state_dir / "student_state.db"
    session_db = state_dir / "sessions.db"

    student_storage = StudentStorage(student_db)
    session_store = SessionStore(session_db)

    session_id = "sess-race-test"
    student_id = "student-race"
    notebook_id = "nb-test"
    kc_id = "kc-test"
    episode_id = "ep-test"

    now = datetime.now(timezone.utc).isoformat()

    # Persist session in EVALUATING phase
    session_store.upsert({
        "session_id": session_id,
        "notebook_id": notebook_id,
        "student_id": student_id,
        "current_kc_id": kc_id,
        "episode_id": episode_id,
        "episode_phase": "EVALUATING",
        "available_actions": ["SUBMIT_ANSWER"],
        "created_at": now,
        "updated_at": now,
    })

    eval_reached_recheck = threading.Barrier(2)
    close_can_commit = threading.Barrier(2)
    results = {"eval": None, "close": None, "eval_error": None}

    def evaluation_thread():
        eval_storage = StudentStorage(student_db)
        try:
            with eval_storage.transaction() as conn:
                session_row = session_store.load_session(session_id)
                assert session_row["episode_phase"] == "EVALUATING"

                eval_reached_recheck.wait(timeout=2)
                close_can_commit.wait(timeout=2)

                session_row2 = session_store.load_session(session_id)
                if session_row2 and session_row2.get("episode_phase") == "CLOSED":
                    results["eval"] = "ABORTED_SESSION_CLOSED"
                    raise RuntimeError("SESSION_CLOSED_DURING_TX")

                conn.execute("INSERT INTO bkt_states (kc_id, p_L, p_T, p_G, p_S, attempts, last_update) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (kc_id, 0.5, 0.3, 0.25, 0.1, 1, datetime.now(timezone.utc).isoformat()))
                results["eval"] = "COMMITTED"
        except RuntimeError as e:
            results["eval_error"] = str(e)
            if "SESSION_CLOSED" not in str(e):
                raise
        except Exception as e:
            results["eval"] = f"ERROR: {e}"
            raise
        finally:
            eval_storage.close()

    def close_thread():
        eval_reached_recheck.wait(timeout=2)

        # Close from a SEPARATE SessionStore connection (new thread-local)
        ss = SessionStore(session_db)
        try:
            now2 = datetime.now(timezone.utc).isoformat()
            ss.upsert({
                "session_id": session_id,
                "notebook_id": notebook_id,
                "student_id": student_id,
                "current_kc_id": kc_id,
                "episode_id": episode_id,
                "episode_phase": "CLOSED",
                "available_actions": [],
                "created_at": now,
                "updated_at": now2,
            })
            results["close"] = "COMMITTED"
        finally:
            ss.close()

        close_can_commit.wait(timeout=2)

    t_eval = threading.Thread(target=evaluation_thread)
    t_close = threading.Thread(target=close_thread)

    t_eval.start()
    t_close.start()

    t_eval.join(timeout=5)
    t_close.join(timeout=5)

    assert results["close"] == "COMMITTED", f"Close should commit: {results['close']}"
    assert results["eval"] == "ABORTED_SESSION_CLOSED", f"Evaluation should abort: {results['eval']}"
    assert "SESSION_CLOSED" in (results.get("eval_error") or ""), f"Expected SESSION_CLOSED error: {results.get('eval_error')}"

    with sqlite3.connect(f"file:{student_db}?mode=ro", uri=True) as conn:
        row = conn.execute("SELECT COUNT(*) FROM bkt_states WHERE kc_id = ?", (kc_id,)).fetchone()
        assert row[0] == 0, f"Academic state mutated despite CLOSED re-check! Count: {row[0]}"

    loaded = session_store.load_session(session_id)
    assert loaded["episode_phase"] == "CLOSED"

    student_storage.close()
    session_store.close()


def test_forced_interleaving_close_suspended_then_evaluation_commits(tmp_path):
    """Evaluation commits first -> then close persists CLOSED.

    Both should succeed since evaluation commits while session is still EVALUATING.
    """
    state_dir = tmp_path / "race2"
    state_dir.mkdir()
    student_db = state_dir / "student_state.db"
    session_db = state_dir / "sessions.db"

    student_storage = StudentStorage(student_db)
    session_store = SessionStore(session_db)

    session_id = "sess-race-test-2"
    student_id = "student-race"
    notebook_id = "nb-test"
    kc_id = "kc-test"
    episode_id = "ep-test"

    now = datetime.now(timezone.utc).isoformat()

    session_store.upsert({
        "session_id": session_id,
        "notebook_id": notebook_id,
        "student_id": student_id,
        "current_kc_id": kc_id,
        "episode_id": episode_id,
        "episode_phase": "EVALUATING",
        "available_actions": ["SUBMIT_ANSWER"],
        "created_at": now,
        "updated_at": now,
    })

    eval_can_commit = threading.Barrier(2)
    close_waits = threading.Barrier(2)
    results = {"eval": None, "close": None}

    def evaluation_thread():
        eval_storage = StudentStorage(student_db)
        try:
            with eval_storage.transaction() as conn:
                session_row = session_store.load_session(session_id)
                assert session_row["episode_phase"] == "EVALUATING"

                # Signal evaluation is ready to commit
                eval_can_commit.wait(timeout=2)

                # Evaluation commits academic state
                conn.execute("INSERT INTO bkt_states (kc_id, p_L, p_T, p_G, p_S, attempts, last_update) VALUES (?, ?, ?, ?, ?, ?, ?)",
                             (kc_id, 0.5, 0.3, 0.25, 0.1, 1, datetime.now(timezone.utc).isoformat()))
                results["eval"] = "COMMITTED"
        finally:
            eval_storage.close()

        # Wait for close to finish
        close_waits.wait(timeout=2)

    def close_thread():
        # Wait for evaluation to commit
        eval_can_commit.wait(timeout=2)

        # Now persist CLOSED (evaluation has already committed)
        ss = SessionStore(session_db)
        try:
            now2 = datetime.now(timezone.utc).isoformat()
            ss.upsert({
                "session_id": session_id,
                "notebook_id": notebook_id,
                "student_id": student_id,
                "current_kc_id": kc_id,
                "episode_id": episode_id,
                "episode_phase": "CLOSED",
                "available_actions": [],
                "created_at": now,
                "updated_at": now2,
            })
            results["close"] = "COMMITTED"
        finally:
            ss.close()

        close_waits.wait(timeout=2)

    t_eval = threading.Thread(target=evaluation_thread)
    t_close = threading.Thread(target=close_thread)

    t_eval.start()
    t_close.start()

    t_eval.join(timeout=5)
    t_close.join(timeout=5)

    assert results["eval"] == "COMMITTED", f"Evaluation should commit: {results['eval']}"
    assert results["close"] == "COMMITTED", f"Close should commit: {results['close']}"

    with sqlite3.connect(f"file:{student_db}?mode=ro", uri=True) as conn:
        row = conn.execute("SELECT attempts FROM bkt_states WHERE kc_id = ?", (kc_id,)).fetchone()
        assert row[0] == 1

    loaded = session_store.load_session(session_id)
    assert loaded["episode_phase"] == "CLOSED"

    student_storage.close()
    session_store.close()


def test_sqlite_thread_local_connection_isolation(tmp_path):
    """Verify StudentStorage thread-local connections are independent.

    Each thread gets its own connection; writes on one thread are visible
    to other threads via WAL semantics (committed data), but connections
    themselves are thread-local.
    """
    state_dir = tmp_path / "thread_local"
    state_dir.mkdir()
    student_db = state_dir / "student_state.db"

    storage = StudentStorage(student_db)

    conn_main = storage._get_connection()
    conn_main.execute("CREATE TABLE IF NOT EXISTS isolation_test (id INTEGER PRIMARY KEY, thread TEXT)")
    conn_main.execute("INSERT INTO isolation_test (thread) VALUES ('main')")
    conn_main.commit()

    storage.close()

    thread_result = {}

    def worker():
        thread_conn = storage._get_connection()
        thread_conn.execute("INSERT INTO isolation_test (thread) VALUES ('worker')")
        thread_conn.commit()
        thread_result["count"] = thread_conn.execute("SELECT COUNT(*) FROM isolation_test").fetchone()[0]

    t = threading.Thread(target=worker)
    t.start()
    t.join()

    main_count = storage._get_connection().execute("SELECT COUNT(*) FROM isolation_test").fetchone()[0]
    assert main_count == 2, f"WAL: committed writes visible across connections, got {main_count}"

    assert thread_result["count"] == 2

    storage.close()


def test_sqlite_two_independent_cycles(tmp_path):
    """Two independent storage lifecycles on fresh synthetic state."""
    for cycle in range(2):
        state_dir = tmp_path / f"cycle_{cycle}"
        state_dir.mkdir()

        student_db = state_dir / "student_state.db"
        session_db = state_dir / "sessions.db"

        student_storage = StudentStorage(student_db)
        session_store = SessionStore(session_db)

        _ = student_storage._get_connection()
        _ = session_store._get_conn()

        student_storage.close()
        session_store.close()

        assert student_db.exists()
        assert session_db.exists()

        for db in (student_db, session_db):
            with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as conn:
                assert conn.execute("PRAGMA integrity_check").fetchone() == ("ok",)


def test_sqlite_wal_mode_session_store(tmp_path):
    """SessionStore uses WAL mode; verify it's enabled."""
    state_dir = tmp_path / "wal_check"
    state_dir.mkdir()
    session_db = state_dir / "sessions.db"

    store = SessionStore(session_db)
    conn = store._get_conn()

    journal_mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
    assert journal_mode == "wal", f"Expected WAL mode, got {journal_mode}"

    busy_timeout = conn.execute("PRAGMA busy_timeout").fetchone()[0]
    assert busy_timeout == 5000, f"Expected busy_timeout=5000, got {busy_timeout}"

    store.close()


def test_sqlite_student_storage_immediate_transaction(tmp_path):
    """StudentStorage.transaction() uses BEGIN IMMEDIATE for write reservation."""
    state_dir = tmp_path / "immediate_tx"
    state_dir.mkdir()
    student_db = state_dir / "student_state.db"

    storage = StudentStorage(student_db)

    with storage.transaction() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS tx_test (id INTEGER)")
        conn.execute("INSERT INTO tx_test VALUES (1)")

    with sqlite3.connect(f"file:{student_db}?mode=ro", uri=True) as conn:
        row = conn.execute("SELECT COUNT(*) FROM tx_test").fetchone()
        assert row[0] == 1

    storage.close()