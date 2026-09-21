"""Layer L0: Repository State & Baseline Pinning Verification.

Part of SYSTEM SURVIVAL AUDIT — SSA-0.
Modalidad: Read-Only / Red Team / No Patch.
"""

import hashlib
import json
from pathlib import Path
import subprocess
import sys


def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent.parent
    src_dir = repo_root / "src" / "study_engine"

    # 1. Git HEAD & Tree verification
    try:
        head_commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo_root, text=True
        ).strip()
        tree_hash = subprocess.check_output(
            ["git", "rev-parse", "HEAD^{tree}"], cwd=repo_root, text=True
        ).strip()
        diff_src = subprocess.check_output(
            ["git", "diff", "HEAD", "--", "src/study_engine/"],
            cwd=repo_root,
            text=True,
        ).strip()
    except Exception as e:
        print(f"[ERROR] Failed to query git state: {e}")
        return 1

    expected_baseline = "e3fc4422665a778bdcce302f2a760c3e5c82a056"

    # 2. Compute file-level SHA-256 for all source files
    src_files = sorted(list(src_dir.rglob("*.py")))
    file_hashes = {}
    combined_hasher = hashlib.sha256()

    for p in src_files:
        rel_path = str(p.relative_to(repo_root))
        h = compute_sha256(p)
        file_hashes[rel_path] = h
        combined_hasher.update(f"{rel_path}:{h}\n".encode("utf-8"))

    source_manifest_sha256 = combined_hasher.hexdigest()

    # 3. Disambiguation logic: BASELINE_MATCH vs MISMATCH vs TRUST_ROOT
    if head_commit == expected_baseline and not diff_src:
        baseline_status = "BASELINE_MATCH"
    else:
        baseline_status = "BASELINE_MISMATCH"

    # Trust root cannot be proven solely by self-inspection without external hardware/PKI
    trust_root_status = "TRUST_ROOT_UNVERIFIED"

    result = {
        "layer": "L0",
        "description": "Repository State & Baseline Pinning",
        "head_commit": head_commit,
        "tree_hash": tree_hash,
        "expected_baseline": expected_baseline,
        "baseline_status": baseline_status,
        "trust_root_status": trust_root_status,
        "src_diff_empty": len(diff_src) == 0,
        "total_source_files": len(src_files),
        "source_manifest_sha256": source_manifest_sha256,
        "epistemic_note": (
            "BASELINE_MATCH confirms repository matches reference baseline string. "
            "TRUST_ROOT_UNVERIFIED explicitly notes that internal hashing does not "
            "constitute an immutable hardware trust root."
        ),
    }

    out_file = repo_root / "data" / "experiments" / "survival" / "l0_baseline_report.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"L0 Status: {baseline_status} | Trust Root: {trust_root_status}")
    print(f"HEAD: {head_commit} (tree: {tree_hash[:16]}...)")
    print(f"Total source files: {len(src_files)}, manifest SHA: {source_manifest_sha256[:16]}...")
    print(f"Report written to: {out_file.relative_to(repo_root)}")
    return 0 if baseline_status == "BASELINE_MATCH" else 1


if __name__ == "__main__":
    sys.exit(main())
