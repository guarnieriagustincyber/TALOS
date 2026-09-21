#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""GP-B-V0 scenario B.2 fixture.

This fixture computes the canonical SHA-256 hexadecimal digest of the
stdin payload and writes exactly 64 lowercase hexadecimal characters
to output_hash.txt.
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
