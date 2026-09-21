#!/usr/bin/env python3
# CONTROLLED EXPERIMENT FIXTURE - NOT STUDENT MASTERY EVIDENCE
"""Phase 4 fixture: P4-EXEC-04 (timeout).

Sleeps for 15 seconds, exceeding the 2.0s sandbox timeout policy,
triggering SIGTERM/SIGKILL escalation in S6.1 process manager.
"""

import sys
import time


def main() -> int:
    _ = sys.stdin.buffer.read()
    time.sleep(15)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
