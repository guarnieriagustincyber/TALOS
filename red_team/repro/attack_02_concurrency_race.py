#!/usr/bin/env python3
"""
RED TEAM ATTACK SCRIPT 02: Concurrency Hell & State Corruption
Target: EvidenceLedger, SQLite WAL journal, JSONL sync, hash chaining.
"""

import sys
import os
import json
import tempfile
import shutil
import threading
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("src"))

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    DuplicateEvidenceError,
    IdempotentReplayError,
    InconsistentReplayError,
    LedgerIntegrityStatus,
)
from study_engine.state.policy_contracts import (
    EvidenceRecord,
    EvidenceType,
    EvidenceOutcome,
    ActorType,
)

def make_test_record(
    record_id: str,
    eval_attempt_id: str,
    digest_seed: str,
    student_id: str = "student_redteam",
    node_id: str = "node_redteam"
) -> EvidenceRecord:
    digest_hash = hashlib.sha256(digest_seed.encode("utf-8")).hexdigest()
    return EvidenceRecord(
        record_id=record_id,
        student_id=student_id,
        node_id=node_id,
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="tool_evaluator_v1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        metadata={"evaluation_attempt_id": eval_attempt_id},
        assessment_digest=digest_hash,
    )

def run_attack_02():
    print("=" * 70)
    print("RED TEAM ATTACK 02: CONCURRENCY HELL & STATE CORRUPTION")
    print("=" * 70)

    findings = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="kasiu_redteam_ledger_"))

    try:
        db_path = tmp_dir / "adversarial_ledger.db"
        ledger = EvidenceLedger(file_path=db_path)

        # -------------------------------------------------------------
        # VECTOR 2.1: 100 Threads Racing on Same Attempt with Conflicting Digests
        # -------------------------------------------------------------
        print("\n[VECTOR 2.1] 100 concurrent threads racing on same evaluation attempt with conflicting digests...")
        attempt_id = "attempt_race_conflict_001"
        num_threads = 100

        results = {
            "success": [],
            "inconsistent_replay": [],
            "idempotent_replay": [],
            "duplicate_error": [],
            "locked_or_error": [],
        }

        start_event = threading.Event()

        def worker(thread_idx: int):
            start_event.wait()
            rec = make_test_record(
                record_id=f"rec_race_{thread_idx:03d}",
                eval_attempt_id=attempt_id,
                digest_seed=f"digest_seed_{thread_idx:03d}",
            )
            try:
                ledger.append_record(rec)
                results["success"].append(thread_idx)
            except InconsistentReplayError as e:
                results["inconsistent_replay"].append((thread_idx, str(e)))
            except IdempotentReplayError as e:
                results["idempotent_replay"].append((thread_idx, str(e)))
            except DuplicateEvidenceError as e:
                results["duplicate_error"].append((thread_idx, str(e)))
            except Exception as e:
                results["locked_or_error"].append((thread_idx, type(e).__name__, str(e)))

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(num_threads)]
        for t in threads:
            t.start()

        start_event.set()

        for t in threads:
            t.join()

        print(f"  Results after 100-thread race:")
        print(f"    Successes: {len(results['success'])}")
        print(f"    InconsistentReplayError: {len(results['inconsistent_replay'])}")
        print(f"    IdempotentReplayError: {len(results['idempotent_replay'])}")
        print(f"    DuplicateEvidenceError: {len(results['duplicate_error'])}")
        print(f"    Locked / Exceptions: {len(results['locked_or_error'])}")

        if len(results["success"]) != 1:
            print(f"  [CRITICAL] Expected exactly 1 success, got {len(results['success'])}!")
            findings.append({
                "vector": "Concurrency Race Condition",
                "attack": "100 threads conflicting attempt",
                "result": f"{len(results['success'])} concurrent writes succeeded",
                "severity": "CRITICAL"
            })
        else:
            print("  [PASS] Invariant D(K, R) held: exactly 1 write committed, remaining rejected.")

        if results["locked_or_error"]:
            print(f"  [HIGH] Thread locking/operational errors encountered: {results['locked_or_error'][:3]}")
            findings.append({
                "vector": "SQLite Locking Under Concurrency",
                "attack": "100 concurrent threads",
                "result": f"{len(results['locked_or_error'])} errors",
                "details": str(results['locked_or_error'][:5]),
                "severity": "HIGH"
            })

        # Verify integrity immediately
        report = ledger.verify_integrity()
        print(f"  Ledger integrity status: {report.status.value}")
        if report.status != LedgerIntegrityStatus.VALID:
            print(f"  [CRITICAL] Ledger integrity corrupted! Details: {report.details}")
            findings.append({
                "vector": "Ledger Corruption",
                "result": f"Integrity status: {report.status.value}",
                "details": report.details,
                "severity": "CRITICAL"
            })

        # -------------------------------------------------------------
        # VECTOR 2.2: Concurrent Appends vs Export/Read Hammering
        # -------------------------------------------------------------
        print("\n[VECTOR 2.2] Concurrent Read/Export Hammering vs Appends...")
        stop_hammer = threading.Event()
        read_errors = []

        def reader_hammer(reader_id: int):
            while not stop_hammer.is_set():
                try:
                    ledger.verify_integrity()
                    ledger.get_all_records()
                    ledger.export_jsonl()
                except Exception as e:
                    read_errors.append((reader_id, type(e).__name__, str(e)))
                time.sleep(0.001)

        readers = [threading.Thread(target=reader_hammer, args=(r,)) for r in range(5)]
        for r in readers:
            r.start()

        append_errors = []
        for i in range(50):
            try:
                rec = make_test_record(
                    record_id=f"rec_hammer_{i:03d}",
                    eval_attempt_id=f"attempt_hammer_{i:03d}",
                    digest_seed=f"digest_hammer_seed_{i:03d}",
                )
                ledger.append_record(rec)
            except Exception as e:
                append_errors.append((i, type(e).__name__, str(e)))

        stop_hammer.set()
        for r in readers:
            r.join()

        print(f"  Completed 50 appends while 5 reader threads hammered verify/export.")
        print(f"    Append errors: {len(append_errors)}")
        print(f"    Reader errors: {len(read_errors)}")

        if append_errors or read_errors:
            print(f"  [HIGH] Concurrency contention errors detected:")
            if append_errors:
                print(f"    Appends: {append_errors[:3]}")
            if read_errors:
                print(f"    Readers: {read_errors[:3]}")
            findings.append({
                "vector": "Concurrent Read/Write Contention",
                "append_errors": len(append_errors),
                "read_errors": len(read_errors),
                "details": str((append_errors + read_errors)[:5]),
                "severity": "HIGH"
            })
        else:
            print("  [PASS] Zero errors during concurrent read/export hammer.")

        # -------------------------------------------------------------
        # VECTOR 2.3: Re-opening Ledger from Disk & JSONL Verification
        # -------------------------------------------------------------
        print("\n[VECTOR 2.3] Testing Ledger re-opening and cross-file verification...")
        reopened_ledger = EvidenceLedger(file_path=db_path)
        reopened_report = reopened_ledger.verify_integrity()
        print(f"  Re-opened ledger integrity: {reopened_report.status.value}, entries: {reopened_ledger.total_entries}")

        if reopened_report.status != LedgerIntegrityStatus.VALID:
            print(f"  [CRITICAL] Re-opened ledger integrity invalid: {reopened_report.details}")
            findings.append({
                "vector": "Ledger Persistence Integrity",
                "result": reopened_report.status.value,
                "severity": "CRITICAL"
            })
        else:
            print("  [PASS] Reopened ledger verified successfully.")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n" + "=" * 70)
    print(f"ATTACK 02 COMPLETED: {len(findings)} findings recorded.")
    print("=" * 70)
    with open("red_team/repro/findings_attack_02.json", "w") as f:
        json.dump(findings, f, indent=2)

if __name__ == "__main__":
    run_attack_02()
