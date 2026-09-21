#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-01 (exit_zero_wrong_artifact).

Demonstrates that an exit code of 0 with malformed artifact content (20 bytes)
does not confer curricular mastery (fails S9.1 assessment postcondition).
"""

import sys

BAD_OUTPUT = "ERROR: INVALID_INPUT"


def main() -> int:
    _ = sys.stdin.buffer.read()

    with open("output_hash.txt", "w", encoding="ascii", newline="") as fh:
        fh.write(BAD_OUTPUT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
