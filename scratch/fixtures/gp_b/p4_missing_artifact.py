#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-06 (missing_artifact).

Exits with 0 but omits creating output_hash.txt entirely.
Verified absent during workspace scan, failing S9.1 postconditions.
"""

import sys


def main() -> int:
    _ = sys.stdin.buffer.read()
    # No file is written
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
