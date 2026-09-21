#!/usr/bin/env python3
"""Independent Oracle Generator for Golden Path B (GP-B-V0).

Generates the static oracle artifact at data/experiments/gp_b_oracle.json
defining expectations for scenarios B.1, B.2, B.3a, and B.3b.
"""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


CANONICAL_STDIN = "STUDY_ENGINE_CANONICAL_INPUT"


def compute_canonical_digest(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def generate_oracle() -> Dict[str, Any]:
    expected_digest = compute_canonical_digest(CANONICAL_STDIN)

    oracle_data: Dict[str, Any] = {
        "campaign_id": "GP-B-V0",
        "spec_version": "SPEC-GP-B-V0",
        "canonical_stdin": CANONICAL_STDIN,
        "expected_clean_digest_sha256": expected_digest,
        "scenarios": {
            "B1": {
                "fixture": "student_bad_artifact.py",
                "attempt_id": "attempt-prog01-b1",
                "observation": {
                    "exit_code": 0,
                    "duration_ms_max": 5000.0,
                    "artifact_filename": "output_hash.txt",
                    "artifact_size_bytes": 20,
                },
                "evaluation": {
                    "live_demo_passed": True,
                    "foundations_passed": False,
                    "overall_passed": False,
                    "overall_level": "N1_INSUFFICIENT",
                },
                "evidence": {
                    "outcome": "FAIL",
                    "score": 0.0,
                },
                "state_after": {
                    "PROG-01": "IN_PROGRESS",
                    "PROG-02": "LOCKED",
                },
            },
            "B2": {
                "fixture": "student_clean_solution.py",
                "attempt_id": "attempt-prog01-b2",
                "observation": {
                    "exit_code": 0,
                    "duration_ms_max": 5000.0,
                    "artifact_filename": "output_hash.txt",
                    "artifact_size_bytes": 64,
                },
                "evaluation": {
                    "live_demo_passed": True,
                    "foundations_passed": True,
                    "overall_passed": True,
                    "overall_level": "N3_COMPETENT",
                },
                "evidence": {
                    "outcome": "PASS",
                    "score": 1.0,
                },
                "state_after": {
                    "PROG-01": "ASSESSED_PROFICIENT",
                    "PROG-02": "AVAILABLE",
                },
            },
            "B3a": {
                "replay_of": "B2",
                "expected_error": "IdempotentReplayError",
                "ledger_cardinality_after": 1,
            },
            "B3b": {
                "replay_of": "B2",
                "expected_error": "InconsistentReplayError",
                "ledger_cardinality_after": 1,
            },
        },
    }

    # Validate oracle self-consistency
    assert len(expected_digest) == 64, "Digest must be 64 hex characters"
    assert oracle_data["scenarios"]["B1"]["observation"]["artifact_size_bytes"] == 20
    assert oracle_data["scenarios"]["B2"]["observation"]["artifact_size_bytes"] == 64
    assert oracle_data["scenarios"]["B1"]["evidence"]["outcome"] == "FAIL"
    assert oracle_data["scenarios"]["B2"]["evidence"]["outcome"] == "PASS"

    return oracle_data


def main() -> None:
    oracle = generate_oracle()
    output_path = Path("data/experiments/gp_b_oracle.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(oracle, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Oracle generated successfully at {output_path}")
    print(f"Canonical clean digest: {oracle['expected_clean_digest_sha256']}")


if __name__ == "__main__":
    main()
