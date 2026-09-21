#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-03 (wrong_hash).

Demonstrates that an exit code of 0 with an MD5 hash (32 bytes < 64 bytes)
does not confer curricular mastery (fails S9.1 min_size_bytes postcondition).
"""

import hashlib
import sys


def main() -> int:
    payload = sys.stdin.buffer.read()
    digest = hashlib.md5(payload).hexdigest()  # 32 characters

    with open("output_hash.txt", "w", encoding="ascii", newline="") as fh:
        fh.write(digest)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
