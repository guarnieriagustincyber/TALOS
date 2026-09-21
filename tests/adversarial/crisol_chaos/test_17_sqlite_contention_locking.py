"""Escenario 17: Contención y Bloqueo en SQLite (Fase 7.2 - Chaos Engineering).

Simular escrituras masivas concurrentes en paralelo a lecturas analíticas sostenidas.
Invariante: PRAGMA busy_timeout = 5000; previene sqlite3.OperationalError: database is locked.
            0 bloqueos fatales, 100% transacciones confirmadas.
Severidad: CRÍTICO.
"""

import concurrent.futures
from pathlib import Path
import time
import pytest

from study_engine.student.contracts import BKTState
from study_engine.student.storage import StudentStorage


def test_sqlite_contention_heavy_writes_with_busy_timeout(tmp_path: Path) -> None:
    """Heavy concurrent writes and reads do not throw 'database is locked' errors."""
    db_file = tmp_path / "contention_test.db"
    storage = StudentStorage(db_file)

    # Initialize KCs
    for i in range(10):
        storage.save_bkt_state(BKTState(kc_id=f"kc_{i}", p_L=0.10, attempts=1))

    errors = []

    def writer_task(worker_id: int, iterations: int = 15):
        try:
            worker_storage = StudentStorage(db_file)
            for j in range(iterations):
                kc = f"kc_{j % 10}"
                # Frequent atomic updates
                st = worker_storage.get_bkt_state(kc)
                if st:
                    st.p_L = min(1.0, st.p_L + 0.01)
                    st.attempts += 1
                    worker_storage.save_bkt_state(st)
                time.sleep(0.005)
        except Exception as exc:
            errors.append(exc)

    def reader_task(worker_id: int, iterations: int = 25):
        try:
            worker_storage = StudentStorage(db_file)
            for j in range(iterations):
                kc = f"kc_{j % 10}"
                _ = worker_storage.get_bkt_state(kc)
                time.sleep(0.002)
        except Exception as exc:
            errors.append(exc)

    # Run 5 writers and 5 readers concurrently against the single SQLite database
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        writer_futures = [executor.submit(writer_task, i) for i in range(5)]
        reader_futures = [executor.submit(reader_task, i) for i in range(5)]
        concurrent.futures.wait(writer_futures + reader_futures)

    # Invariant: ZERO database is locked errors occurred thanks to busy_timeout
    assert len(errors) == 0, f"Encountered SQLite contention errors: {errors}"

    # Verify final integrity
    for i in range(10):
        st = storage.get_bkt_state(f"kc_{i}")
        assert st is not None
        assert st.attempts > 1
