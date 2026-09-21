import os, sys, time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
import hashlib

# Ensure we import from the project src directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from study_engine.state.ledger import EvidenceLedger, LedgerIntegrityReport
from study_engine.state.policy_contracts import EvidenceRecord, EvidenceType, EvidenceOutcome, ActorType, EpistemologicalAuthority

def make_entry(i: int) -> EvidenceRecord:
    """Create a deterministic EvidenceRecord for stress testing.

    The ledger will compute entry_index, parent_entry_hash, entry_hash, and
    committed_at internally. We only need to supply the fields required by
    ``EvidenceRecord``.
    """
    from datetime import datetime
    return EvidenceRecord(
        record_id=f"rec-{i}",
        student_id="student",
        node_id="node",
        competency_id=None,
        evidence_type=EvidenceType.DIAGNOSTIC_QUIZ,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.utcnow(),
        actor_type=ActorType.HUMAN,
        actor_id="human-1",
        audit_verdict=None,
        tool_backend=None,
        verifier_id=None,
        rationale=None,
        roadmap_revision_id=None,
        policy_revision_id=None,
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        assessment_digest=hashlib.sha256(f"digest-{i}".encode()).hexdigest(),
        spine_id=None,
        overall_level=None,
        metadata={"evaluation_attempt_id": f"attempt-{i}"},
    )

def worker(start: int, count: int) -> dict:
    ledger_path = Path("tmp/ledger_stress.db")
    if ledger_path.exists():
        ledger_path.unlink()
    ledger = EvidenceLedger(file_path=ledger_path)
    successes = 0
    failures = 0
    for i in range(start, start + count):
        try:
            ledger.append_record(make_entry(i))
            successes += 1
        except Exception as e:
            failures += 1
            print(f"Error appending record {i}: {e}")
    # Export JSONL to verify integrity
    ledger.export_jsonl()
    report = ledger.verify_integrity()
    ledger.close()
    return {"successes": successes, "failures": failures, "report": report}

if __name__ == "__main__":
    TOTAL = 1000
    WORKERS = 1
    per_worker = TOTAL // WORKERS
    with ProcessPoolExecutor(max_workers=WORKERS) as executor:
        futures = [executor.submit(worker, i * per_worker, per_worker) for i in range(WORKERS)]
        total_success = total_fail = 0
        for fut in as_completed(futures):
            res = fut.result()
            total_success += res["successes"]
            total_fail += res["failures"]
        print(f"Inserted {total_success} records with {total_fail} failures across workers")
        # Simple sanity check – run a final integrity verification on one ledger file
        final_ledger = EvidenceLedger(file_path=Path("tmp/ledger_stress.db"))
        final_report = final_ledger.verify_integrity()
        print("Final integrity report:", final_report)
        final_ledger.close()
