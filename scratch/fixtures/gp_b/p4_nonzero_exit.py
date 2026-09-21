#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-05 (nonzero_exit).

Exits with returncode 42, triggering FAILED_PROCESS status in S6.1
and fail-closed rejection prior to assessment.
"""

import sys


def main() -> int:
    _ = sys.stdin.buffer.read()
    sys.exit(42)


if __name__ == "__main__":
    raise SystemExit(main())
