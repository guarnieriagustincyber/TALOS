"""Concurrency and Thread Safety Tests for BKTTracker (Fix S1.3)."""

from concurrent.futures import ThreadPoolExecutor
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.student.storage import StudentStorage


def test_bkt_tracker_concurrent_updates_and_reads():
    """Verify that multiple threads concurrently updating and reading BKT state maintain consistency."""
    storage = StudentStorage(db_path=":memory:")
    tracker = BKTTracker(storage=storage)
    kc = "test_concurrent_kc"

    tracker.reset(kc)
    num_threads = 8
    updates_per_thread = 20

    def worker_update(correct: bool):
        for _ in range(updates_per_thread):
            tracker.update(kc_id=kc, correct=correct)
            state = tracker.get_state(kc)
            assert state.attempts > 0
            assert 0.0 <= state.p_L <= 1.0

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(num_threads):
            futures.append(executor.submit(worker_update, i % 2 == 0))
        for f in futures:
            f.result()

    final_state = tracker.get_state(kc)
    assert final_state.attempts == num_threads * updates_per_thread
    assert 0.0 <= final_state.p_L <= 1.0
