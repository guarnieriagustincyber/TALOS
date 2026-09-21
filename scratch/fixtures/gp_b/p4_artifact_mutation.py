#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-07 (artifact_mutation).

Legitimate script submitted with an expected_sha256 mismatch,
triggering pre-execution rejection in SessionOrchestrator.
"""

import hashlib
import sys


def main() -> int:
    payload = sys.stdin.buffer.read()
    digest = hashlib.sha256(payload).hexdigest()

    with open("output_hash.txt", "w", encoding="ascii", newline="") as fh:
        fh.write(digest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
