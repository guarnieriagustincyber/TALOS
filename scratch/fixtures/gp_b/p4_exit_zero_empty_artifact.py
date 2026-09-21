#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-02 (exit_zero_empty_artifact).

Demonstrates that an exit code of 0 with an empty artifact file (0 bytes < 64 bytes)
does not confer curricular mastery (fails S9.1 min_size_bytes postcondition).
"""

import sys


def main() -> int:
    _ = sys.stdin.buffer.read()

    with open("output_hash.txt", "w", encoding="ascii", newline="") as fh:
        pass  # 0 bytes

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
