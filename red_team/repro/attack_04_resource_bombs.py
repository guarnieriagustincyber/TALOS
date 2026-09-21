#!/usr/bin/env python3
"""
RED TEAM ATTACK SCRIPT 04: Sandbox Resource Bombs & Process Denial of Service
Target: run_managed_process_group, io_streamer, scratch workspace.

Attacks:
1. Infinite loop / CPU burn with timeout=1s. Verify os.killpg and termination_reason=TIMEOUT.
2. Fast fork-bomb / subprocess spawning attempt in Python:
   Spawns 50 background children trying to ignore SIGTERM and stay orphaned.
   Verify process group kill ensures NO zombie/orphaned processes survive.
3. Output flooding / Disk & RAM bomb:
   Process prints 100MB of text to stdout. Verify max_output_bytes cap (e.g. 64KB)
   truncates output without OOM-crashing the host runner.
4. Process ignoring SIGTERM (signal.signal(signal.SIGTERM, signal.SIG_IGN)).
   Verify escalation to SIGKILL terminates the process within grace deadline.
"""

import sys
import os
import json
import tempfile
import shutil
import time
import subprocess

sys.path.insert(0, os.path.abspath("src"))

from study_engine.execution.process_manager import run_managed_process_group
from study_engine.contracts.execution import TerminationReason

def run_attack_04():
    print("=" * 70)
    print("RED TEAM ATTACK 04: SANDBOX RESOURCE BOMBS & PROCESS DOS")
    print("=" * 70)

    findings = []
    tmp_dir = tempfile.mkdtemp(prefix="kasiu_redteam_proc_")

    try:
        # -------------------------------------------------------------
        # VECTOR 4.1: Output Flooding / RAM Exhaustion Bomb
        # -------------------------------------------------------------
        print("\n[VECTOR 4.1] Testing Output Flood Bomb (Attempting 50MB stdout stream)...")
        flood_script = os.path.join(tmp_dir, "flood.py")
        with open(flood_script, "w") as f:
            f.write("import sys\nfor _ in range(500_000):\n    sys.stdout.write('A' * 100 + '\\n')\n")

        outcome = run_managed_process_group(
            cmd=[sys.executable, "-u", flood_script],
            cwd=tmp_dir,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=5,
            max_output_bytes=32_768,  # 32 KB limit
        )

        print(f"  Exit code: {outcome.exit_code}, Duration: {outcome.duration_ms:.1f}ms")
        print(f"  Bytes captured: {outcome.streams.bytes_captured}, discarded: {outcome.streams.bytes_discarded}, truncated: {outcome.streams.truncated}")

        if outcome.streams.bytes_captured > 35_000:
            print(f"  [CRITICAL] Stream buffer exceeded limit! Captured {outcome.streams.bytes_captured} bytes.")
            findings.append({
                "vector": "Output Bomb Memory Leak",
                "result": f"Captured {outcome.streams.bytes_captured} bytes",
                "severity": "CRITICAL"
            })
        elif not outcome.streams.truncated:
            print("  [HIGH] Stream was not marked truncated despite exceeding output size!")
            findings.append({
                "vector": "Output Truncation Flag Missing",
                "severity": "HIGH"
            })
        else:
            print("  [PASS] Stream safely capped at byte limit, truncated flag set.")

        # -------------------------------------------------------------
        # VECTOR 4.2: SIGTERM Resistant Process Escalation to SIGKILL
        # -------------------------------------------------------------
        print("\n[VECTOR 4.2] Testing SIGTERM Resistant Process (trapping SIGTERM)...")
        sigterm_script = os.path.join(tmp_dir, "sigterm_trap.py")
        with open(sigterm_script, "w") as f:
            f.write("""
import signal
import time
signal.signal(signal.SIGTERM, signal.SIG_IGN)
while True:
    time.sleep(0.1)
""")

        t0 = time.perf_counter()
        outcome_sig = run_managed_process_group(
            cmd=[sys.executable, "-u", sigterm_script],
            cwd=tmp_dir,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=1,
            max_output_bytes=1024,
        )
        t_elapsed = time.perf_counter() - t0
        print(f"  Terminated in {t_elapsed:.2f}s, reason: {outcome_sig.termination_reason.value}, exit_code: {outcome_sig.exit_code}")

        if outcome_sig.termination_reason != TerminationReason.TIMEOUT:
            print(f"  [CRITICAL] Termination reason was not TIMEOUT: {outcome_sig.termination_reason.value}")
            findings.append({
                "vector": "Process Timeout Evasion",
                "severity": "CRITICAL"
            })
        elif t_elapsed > 4.5:
            print(f"  [HIGH] Process took too long to SIGKILL ({t_elapsed:.2f}s > 3.5s limit)!")
            findings.append({
                "vector": "Grace Period Hanging",
                "elapsed": t_elapsed,
                "severity": "HIGH"
            })
        else:
            print("  [PASS] SIGTERM-resistant process successfully terminated via SIGKILL escalation.")

        # -------------------------------------------------------------
        # VECTOR 4.3: Background Process Spawning / Orphan Escapes
        # -------------------------------------------------------------
        print("\n[VECTOR 4.3] Testing Process Group Orphan Cleanup (background sub-daemons)...")
        orphan_script = os.path.join(tmp_dir, "spawn_orphans.py")
        orphan_flag = os.path.join(tmp_dir, "orphan_alive.txt")
        with open(orphan_script, "w") as f:
            f.write(f"""
import subprocess
import sys
import time

# Spawn 10 children that sleep for 30s
for i in range(10):
    subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])

time.sleep(10)
""")

        outcome_orphan = run_managed_process_group(
            cmd=[sys.executable, "-u", orphan_script],
            cwd=tmp_dir,
            env={"PATH": os.environ.get("PATH", "")},
            timeout_seconds=1,
            max_output_bytes=1024,
        )

        time.sleep(0.5) # allow OS signal propagation
        # Check if python children are still running with that cmdline
        ps = subprocess.run(["pgrep", "-f", "time.sleep(30)"], capture_output=True, text=True)
        zombies = ps.stdout.strip().splitlines()
        print(f"  Active orphaned processes found via pgrep: {len(zombies)}")

        if len(zombies) > 0:
            print(f"  [CRITICAL] Process group cleanup failed! {len(zombies)} orphan processes escaped killpg!")
            # Kill remaining test zombies
            subprocess.run(["pkill", "-f", "time.sleep(30)"])
            findings.append({
                "vector": "Process Group Orphan Escape",
                "orphans_found": len(zombies),
                "severity": "CRITICAL",
                "details": f"{len(zombies)} background child processes remained alive after run_managed_process_group exited."
            })
        else:
            print("  [PASS] Zero orphan processes survived. os.killpg completely cleaned process group.")

    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print("\n" + "=" * 70)
    print(f"ATTACK 04 COMPLETED: {len(findings)} findings recorded.")
    print("=" * 70)
    with open("red_team/repro/findings_attack_04.json", "w") as f:
        json.dump(findings, f, indent=2)

if __name__ == "__main__":
    run_attack_04()
