#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""GP-B-V0 scenario B.1 fixture.

This fixture intentionally produces a malformed artifact while exiting
with status code zero. Its purpose is to demonstrate that execution
success is not equivalent to curricular mastery.
"""

import sys

BAD_OUTPUT = "ERROR: INVALID_INPUT"


def main() -> int:
    # Consumimos la entrada canónica para respetar el contrato de tarea.
    _ = sys.stdin.buffer.read()

    with open("output_hash.txt", "w", encoding="ascii", newline="") as fh:
        fh.write(BAD_OUTPUT)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
