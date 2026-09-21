#!/usr/bin/env python3
"""
RED TEAM ATTACK SCRIPT 02B: Schrödinger Crash & Desync Simulation
Target: SQLite vs JSONL desync, interrupted export, corrupted byte injection.
"""

import sys
import os
import json
import tempfile
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath("src"))

from study_engine.contracts.epistemology import EpistemologicalAuthority
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.ledger_contracts import (
    LedgerIntegrityViolationError,
    DuplicateEvidenceError,
)
from study_engine.state.policy_contracts import (
    EvidenceRecord,
    EvidenceType,
    EvidenceOutcome,
    ActorType,
)

def make_test_record(record_id: str, seed: str) -> EvidenceRecord:
    digest_hash = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return EvidenceRecord(
        record_id=record_id,
        student_id="student_crash",
        node_id="node_crash",
        evidence_type=EvidenceType.CODE_EXECUTION,
        outcome=EvidenceOutcome.PASS,
        actor_type=ActorType.TOOL_VERIFIER,
        actor_id="tool_evaluator_v1",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        metadata={"evaluation_attempt_id": record_id},
        assessment_digest=digest_hash,
    )

def run_attack_02b():
    print("=" * 70)
    print("RED TEAM ATTACK 02B: SCHRÖDINGER CRASH & STORAGE CORRUPTION")
    print("=" * 70)

    findings = []
    tmp_dir = Path(tempfile.mkdtemp(prefix="kasiu_redteam_crash_"))

    try:
        db_path = tmp_dir / "crash_ledger.db"
        jsonl_path = tmp_dir / "crash_ledger.jsonl"
        ledger = EvidenceLedger(file_path=db_path)

        for i in range(5):
            ledger.append_record(make_test_record(f"rec_crash_{i}", f"seed_{i}"))

        # Scenario 1: Inject corrupted JSON line into .jsonl
        print("\n[VECTOR 2B.1] Tampering with JSONL file (bit flip in payload)...")
        lines = jsonl_path.read_text().splitlines()
        # Alter entry 2
        bad_entry = json.loads(lines[2])
        bad_entry["record"]["score"] = 0.5 # unauthorized score tampering
        lines[2] = json.dumps(bad_entry)
        jsonl_path.write_text("\n".join(lines) + "\n")

        print("  Attempting to load ledger with tampered JSONL...")
        try:
            tampered_ledger = EvidenceLedger(file_path=jsonl_path)
            print("  [CRITICAL] Tampered ledger was loaded without raising LedgerIntegrityViolationError!")
            findings.append({
                "vector": "Tamper Detection Bypass",
                "result": "Corrupted JSONL loaded silently",
                "severity": "CRITICAL"
            })
        except LedgerIntegrityViolationError as e:
            print(f"  [PASS] Tamper correctly caught: {e}")

        # Scenario 2: Truncated JSONL file (crash during write)
        print("\n[VECTOR 2B.2] Truncating JSONL file mid-entry...")
        jsonl_path.write_text(lines[0] + "\n" + lines[1][:len(lines[1])//2])
        try:
            truncated_ledger = EvidenceLedger(file_path=jsonl_path)
            print("  [CRITICAL] Truncated JSONL loaded without error!")
            findings.append({
                "vector": "Crash Consistency Bypass",
                "result": "Truncated JSONL loaded silently",
                "severity": "CRITICAL"
            })
        except LedgerIntegrityViolationError as e:
            print(f"  [PASS] Truncated JSONL rejected: {e}")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n" + "=" * 70)
    print(f"ATTACK 02B COMPLETED: {len(findings)} findings recorded.")
    print("=" * 70)
    with open("red_team/repro/findings_attack_02b.json", "w") as f:
        json.dump(findings, f, indent=2)

if __name__ == "__main__":
    run_attack_02b()
