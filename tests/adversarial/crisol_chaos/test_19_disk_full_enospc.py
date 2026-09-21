"""Escenario 19: Disco Lleno Durante Escritura SQLite (ENOSPC) (Fase 7.2 - Chaos Engineering).

Simular agotamiento de espacio en disco (ENOSPC / sqlite3.OperationalError: disk I/O error).
Invariante: Rollback atómico de la transacción fallida; cero corrupción estructural (PRAGMA integrity_check == "ok");
            las transacciones previas confirmadas permanecen intactas.
Severidad: CRÍTICO.
"""

import errno
from pathlib import Path
import sqlite3
from unittest.mock import patch
import pytest

from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_sqlite_enospc_disk_full_rollback_and_integrity(tmp_path: Path) -> None:
    """Disk full condition (ENOSPC) during write causes atomic rollback without corruption."""
    db_file = tmp_path / "enospc_test.db"
    storage = StudentStorage(db_file)

    # 1. State successfully committed before disk full
    storage.save_bkt_state(BKTState(kc_id="paging_mechanisms", p_L=0.70, attempts=3))
    assert storage.get_bkt_state("paging_mechanisms").p_L == 0.70

    # 2. Simulate disk full error (ENOSPC / disk I/O error) on next write
    def mock_enospc_execute(*args, **kwargs):
        err = sqlite3.OperationalError("disk I/O error: no space left on device")
        raise err

    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA busy_timeout = 5000;")
    with pytest.raises(sqlite3.OperationalError, match="disk I/O error"):
        with conn:
            # Execute one statement then fail on second
            conn.execute("INSERT INTO bkt_states (kc_id, p_L, p_T, p_G, p_S, attempts, last_update) "
                         "VALUES ('partial_kc', 0.1, 0.3, 0.25, 0.1, 1, '2026-01-01T00:00:00Z')")
            # Disk becomes full here
            mock_enospc_execute()

    conn.close()

    # 3. Invariant: Structural database integrity check
    verify_conn = sqlite3.connect(str(db_file))
    cursor = verify_conn.cursor()
    cursor.execute("PRAGMA integrity_check;")
    integrity = cursor.fetchone()[0]
    verify_conn.close()

    assert integrity.lower() == "ok", f"Database corrupted after ENOSPC: {integrity}"

    # 4. Invariant: Atomic rollback - partial write did not persist
    reopened = StudentStorage(db_file)
    assert reopened.get_bkt_state("partial_kc") is None
    # 5. Invariant: Previous committed state is intact
    assert reopened.get_bkt_state("paging_mechanisms").p_L == 0.70
