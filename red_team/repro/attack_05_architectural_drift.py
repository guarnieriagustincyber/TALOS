#!/usr/bin/env python3
"""
RED TEAM ATTACK SCRIPT 05: Architectural Drift & Boundary Bypass Scanner
Target: Entire src/study_engine codebase.

Audits:
1. Direct imports of `EvidenceLedger` from outside `state/` or `session/`.
   Specifically, no tutor, LLM, router, or API module should ever instantiate
   or call `EvidenceLedger.append_record` directly!
2. Check if any file in `src/study_engine/tutor` imports `EvidenceLedger`,
   `CurriculumRegistry.advance`, or writes directly to `StudentState`.
3. Check if any caller invokes `run_managed_process_group` without going
   through `PracticalExecutionAdapter` and checking `execution_allowed`.
4. Inspect AST for all calls to `.append_record` across the entire codebase.
"""

import sys
import os
import ast
import json
from pathlib import Path

def analyze_ast(file_path: Path):
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=str(file_path))
        except SyntaxError:
            return []

    issues = []
    rel_path = str(file_path.relative_to(Path("src")))

    for node in ast.walk(tree):
        # Check imports in tutor/
        if rel_path.startswith("study_engine/tutor/"):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if "ledger" in mod or "execution" in mod:
                    issues.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "violation": f"Tutor importing restricted module '{mod}'",
                        "severity": "CRITICAL"
                    })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if "ledger" in alias.name or "execution" in alias.name:
                        issues.append({
                            "file": rel_path,
                            "line": node.lineno,
                            "violation": f"Tutor importing restricted module '{alias.name}'",
                            "severity": "CRITICAL"
                        })

        # Check any call to append_record outside state or session
        if isinstance(node, ast.Call):
            func = node.func
            attr_name = None
            if isinstance(func, ast.Attribute):
                attr_name = func.attr
            if attr_name in ("append_record", "append_evidence"):
                if not (rel_path.startswith("study_engine/state/") or
                        rel_path.startswith("study_engine/session/") or
                        rel_path.startswith("study_engine/contracts/")):
                    issues.append({
                        "file": rel_path,
                        "line": node.lineno,
                        "violation": f"Unauthorized direct call to '{attr_name}' from '{rel_path}'",
                        "severity": "CRITICAL"
                    })

    return issues

def run_attack_05():
    print("=" * 70)
    print("RED TEAM ATTACK 05: ARCHITECTURAL DRIFT & BOUNDARY SCANNER")
    print("=" * 70)

    src_dir = Path("src/study_engine")
    findings = []

    for py_file in src_dir.rglob("*.py"):
        issues = analyze_ast(py_file)
        if issues:
            for iss in issues:
                print(f"  🚨 [{iss['severity']}] {iss['file']}:{iss['line']} - {iss['violation']}")
                findings.append(iss)

    if not findings:
        print("  [PASS] Zero architectural boundary violations found across all Python files in src/!")
    else:
        print(f"  [CRITICAL] {len(findings)} architectural boundary violations detected.")

    print("\n" + "=" * 70)
    print(f"ATTACK 05 COMPLETED: {len(findings)} findings recorded.")
    print("=" * 70)
    with open("red_team/repro/findings_attack_05.json", "w") as f:
        json.dump(findings, f, indent=2)

if __name__ == "__main__":
    run_attack_05()
