"""Quality gate to enforce certification and safety standards."""


import subprocess
import sys


def run_gate(title: str, test_path: str) -> bool:
    print(f"--> Running {title} [{test_path}]...")
    cmd = [sys.executable, "-m", "pytest", test_path, "-q"]
    result = subprocess.run(cmd)
    return result.returncode == 0


def main() -> int:
    print("=" * 60)
    print("STUDY ENGINE QUALITY GATE — GLOBAL")
    print("=" * 60)

    # Pre-Flight: Independent Cryptographic Trust Root Verification
    from pathlib import Path
    from study_engine.contracts.trust_root import verify_manifest_trust_root
    try:
        manifest_path = Path("tests/protected/manifest.json")
        verify_manifest_trust_root(manifest_path)
        print("--> [TRUST ROOT OK] Manifest matches external anchor.")
    except Exception as e:
        print(f"--> [CRITICAL SECURITY BREACH] Trust root violation: {e}")
        return 1

    gates = [
        ("Unit Tests", "tests/unit"),
        ("Contract Tests", "tests/contract"),
        ("Adversarial Tests", "tests/adversarial"),
        ("Protected Tests", "tests/protected"),
        ("Integration Tests", "tests/integration"),
    ]

    results = {}
    for name, path in gates:
        passed = run_gate(name, path)
        results[name] = "PASS" if passed else "FAIL"

    print("\n" + "=" * 60)
    print("QUALITY GATE REPORT")
    print("=" * 60)
    all_passed = True
    for name, status in results.items():
        print(f"{name:<20}: {status}")
        if status != "PASS":
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("RESULT: ALL HARD GATES PASSED")
        return 0
    else:
        print("RESULT: HARD GATE FAILURE — NOT CERTIFIED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
