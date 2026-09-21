"""Escenario 11: Crash de Transacción SQLite e Integridad Estructural (Fase 7.2 - Chaos Engineering).

Simular interrupción abrupta de proceso / excepción a mitad de escritura en bases de datos SQLite.
Invariante: PRAGMA integrity_check == "ok", rollback atómico estricto (0 estados zombi o a medias),
            y reanudación normal de operaciones de lectura y escritura.
Severidad: CRÍTICO.
"""

import sqlite3
from pathlib import Path
import pytest

from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_sqlite_transaction_crash_rollback_and_integrity(tmp_path: Path) -> None:
    """Simulated crash during multi-row write rolls back atomically; PRAGMA integrity_check passes."""
    db_file = tmp_path / "test_student_crash.db"
    storage = StudentStorage(db_file)

    # 1. State before crash
    storage.save_bkt_state(BKTState(kc_id="signals_unix", p_L=0.55, attempts=2))
    assert storage.get_bkt_state("signals_unix").p_L == 0.55

    # 2. Simulate interrupted transaction (crash mid-flight)
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA busy_timeout = 5000;")
    try:
        with conn:
            conn.execute(
                "INSERT INTO bkt_states (kc_id, p_L, p_T, p_G, p_S, attempts, last_update) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("temp_corrupt", 0.99, 0.3, 0.25, 0.1, 1, "2026-01-01T00:00:00Z"),
            )
            # Simulated catastrophic unhandled process crash / power cut
            raise SystemExit("Catastrophic process kill simulation")
    except SystemExit:
        pass
    finally:
        conn.close()

    # 3. Post-crash verification
    # Re-open storage and verify structural integrity
    verify_conn = sqlite3.connect(str(db_file))
    cursor = verify_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    status = cursor.fetchone()[0]
    verify_conn.close()

    assert status.lower() == "ok", f"Integrity check failed: {status}"

    # 4. Atomic verification: partial write was rolled back completely
    storage_reopen = StudentStorage(db_file)
    assert storage_reopen.get_bkt_state("temp_corrupt") is None
    assert storage_reopen.get_bkt_state("signals_unix").p_L == 0.55

    # 5. Recovery verification: new writes proceed without error
    storage_reopen.save_bkt_state(BKTState(kc_id="recovered_kc", p_L=0.75, attempts=1))
    assert storage_reopen.get_bkt_state("recovered_kc").p_L == 0.75
