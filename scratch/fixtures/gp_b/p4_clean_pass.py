#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-08 (baseline_clean_pass).

Canonical clean solution computing SHA-256 of stdin in lowercase hex (64 chars)
and writing to output_hash.txt, satisfying all S9.1 rubric criteria.
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
