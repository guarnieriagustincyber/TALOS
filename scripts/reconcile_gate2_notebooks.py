#!/usr/bin/env python3
"""Generate a read-only Gate 2 identity/source reconciliation report."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from study_engine.diagnostics.notebook_reconciliation import (  # noqa: E402
    load_registry_notebooks,
    reconcile_notebooks,
)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--knowledge-db",
        type=Path,
        default=ROOT / "data" / "web_state" / "knowledge_store.db",
        help="Knowledge SQLite database to inspect (opened read-only).",
    )
    parser.add_argument(
        "--curriculum-catalog",
        type=Path,
        default=ROOT / "config" / "notebook_kc_catalog.json",
    )
    parser.add_argument(
        "--source-roles",
        type=Path,
        default=ROOT / "config" / "notebook_source_roles.json",
    )
    parser.add_argument(
        "--identity-decisions",
        type=Path,
        default=ROOT / "config" / "notebook_identity_decisions.json",
        help="Audit-only identity decisions; never used to authorize retrieval.",
    )
    parser.add_argument(
        "--format",
        choices=("summary", "json"),
        default="summary",
        help="Print a concise issue summary or the complete deterministic JSON report.",
    )
    return parser.parse_args()


def main() -> int:
    args = _arguments()
    report = reconcile_notebooks(
        knowledge_db=args.knowledge_db,
        curriculum_catalog=args.curriculum_catalog,
        source_roles=args.source_roles,
        declared_notebooks=load_registry_notebooks(),
        identity_decisions=args.identity_decisions,
    )
    if args.format == "json":
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    issue_counts = Counter(
        issue for notebook in report["notebooks"] for issue in notebook["issues"]
    )
    print(json.dumps(report["counts"], ensure_ascii=False, sort_keys=True))
    print(
        f"notebooks_with_issues: {sum(bool(row['issues']) for row in report['notebooks'])}"
    )
    print("issues:")
    for issue, count in sorted(issue_counts.items()):
        print(f"  {issue}: {count}")
    print(
        f"identity_alias_mapping: {report['identity_aliases']['declared_alias_mapping']}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        print(f"Gate 2 reconciliation failed: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
