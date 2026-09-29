#!/usr/bin/env python3
"""Build a non-decisional review queue from the v2.400 coverage inventory."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
PENDING_QUERY_STATUS = "PENDING_ADJUDICATION"


class QueueError(ValueError):
    """Raised when the coverage inventory cannot safely produce a review queue."""


def build_queue(inventory: Mapping[str, Any]) -> dict[str, Any]:
    if inventory.get("schema_version") != "gate2-v2400-coverage-inventory-v1":
        raise QueueError("Input must be a Gate 2 v2.400 coverage inventory")
    queries = inventory.get("queries")
    qrel_references = inventory.get("qrel_references")
    if not isinstance(queries, list) or not isinstance(qrel_references, list):
        raise QueueError("Inventory must contain query and qrel reference lists")

    qrels_by_query: dict[str, list[dict[str, Any]]] = {}
    for qrel in qrel_references:
        if not isinstance(qrel, dict) or not isinstance(qrel.get("query_id"), str):
            raise QueueError("Inventory contains an invalid qrel reference")
        qrels_by_query.setdefault(qrel["query_id"], []).append(qrel)

    items = []
    for query in queries:
        if not isinstance(query, dict) or not isinstance(query.get("query_id"), str):
            raise QueueError("Inventory contains an invalid query record")
        query_qrels = qrels_by_query.get(query["query_id"], [])
        if (
            query.get("query_status") != PENDING_QUERY_STATUS
            or not query_qrels
        ):
            continue
        if query.get("historical_qrel_count") != len(query_qrels):
            raise QueueError(
                f"Qrel reference count mismatch for {query['query_id']!r}"
            )
        items.append(
            {
                "query_id": query["query_id"],
                "scope": query["scope"],
                "query": query["query"],
                "category": query["category"],
                "oracle_type": query["oracle_type"],
                "expected_abstention": query["expected_abstention"],
                "historical_qrel_count": query["historical_qrel_count"],
                "historical_qrel_status": query["historical_qrel_status"],
                "query_status": query["query_status"],
                "query_decision": None,
                "review_order": [
                    "adjudicate_query_intent_and_oracle",
                    "adjudicate_each_qrel_individually",
                ],
                "qrel_references": [
                    {
                        "chunk_id": row["chunk_id"],
                        "historical_grade": row["qrel_grade"],
                        "qrel_status": row["qrel_status"],
                        "acl_status": row["acl_status"],
                        "semantic_status": row["semantic_status"],
                        "existing_decision": row["decision"],
                        "source_id": row["source_id"],
                        "evidence_source": row["evidence_source"],
                        "review_status": (
                            "PENDING_ADJUDICATION"
                            if row["qrel_status"] == "PENDING"
                            else "ALREADY_RECORDED"
                        ),
                    }
                    for row in query_qrels
                ],
            }
        )

    items.sort(key=lambda row: (row["scope"], row["query_id"]))
    qrel_status_counts = Counter(
        qrel["qrel_status"]
        for item in items
        for qrel in item["qrel_references"]
    )
    scope_counts = Counter(item["scope"] for item in items)
    return {
        "schema_version": "gate2-v2400-query-adjudication-queue-v1",
        "generated_at": inventory.get("generated_at"),
        "source_inventory": {
            "version": inventory["canonical_source"]["version"],
            "path": "reports/gate2_v2400_coverage_inventory_2026-09-28.json",
            "dataset_sha256": inventory["canonical_source"]["dataset_sha256"],
            "qrels_sha256": inventory["canonical_source"]["qrels_sha256"],
        },
        "purpose": (
            "Non-decisional queue for human review. It does not modify or "
            "replace the explicit decision register or historical qrels."
        ),
        "review_policy": {
            "query_intent_and_oracle_first": True,
            "qrels_adjudicated_individually_after_query": True,
            "no_automatic_negative_inference_from_absent_qrels": True,
            "historical_files_modified": False,
            "retrieval_executed": False,
        },
        "counts": {
            "query_status_pending_total": inventory["counts"][
                "query_status_counts"
            ][PENDING_QUERY_STATUS],
            "pending_queries_with_historical_qrels": len(items),
            "pending_queries_without_historical_qrels": inventory["counts"][
                "query_status_counts"
            ][PENDING_QUERY_STATUS]
            - len(items),
            "qrel_references_for_queued_queries": sum(
                len(item["qrel_references"]) for item in items
            ),
            "qrel_status_counts": dict(sorted(qrel_status_counts.items())),
            "query_count_by_scope": dict(sorted(scope_counts.items())),
        },
        "items": items,
    }


def render_markdown(queue: Mapping[str, Any]) -> str:
    counts = queue["counts"]
    lines = [
        "# Gate 2 — Cola de adjudicación de consultas v2.400",
        "",
        f"**Fecha de inventario:** {queue['generated_at']}  ",
        "**Tipo:** paquete de revisión, no registro de decisiones.  ",
        f"**Fuente:** `{queue['source_inventory']['version']}` "
        f"(SHA-256 dataset `{queue['source_inventory']['dataset_sha256']}`).",
        "",
        "## Alcance",
        "",
        f"- Consultas en `PENDING_ADJUDICATION`: "
        f"**{counts['query_status_pending_total']}**.",
        f"- Primer lote con qrels históricos: "
        f"**{counts['pending_queries_with_historical_qrels']} consultas**, "
        f"**{counts['qrel_references_for_queued_queries']} referencias**.",
        f"- Consultas pendientes sin qrels, fuera de este lote: "
        f"**{counts['pending_queries_without_historical_qrels']}**.",
        f"- Referencias qrel por estado: "
        + ", ".join(
            f"`{status}` {count}"
            for status, count in counts["qrel_status_counts"].items()
        ),
        "",
        "## Procedimiento de revisión",
        "",
        "1. Adjudicar intención, scope curricular y tipo de oráculo de la consulta.",
        "2. Revisar cada referencia qrel por separado; no inferir validez de una "
        "referencia a partir de otra.",
        "3. Registrar las decisiones aceptadas en un registro separado; no editar "
        "los qrels históricos.",
        "4. `ABSENT` no equivale a una negativa. Las referencias con una decisión "
        "previa aparecen marcadas `ALREADY_RECORDED` y no se reabren aquí.",
        "",
        "El paquete no incluye texto de los chunks; `chunk_id` y `source_id` "
        "permiten inspección local de la evidencia sin copiar pasajes al reporte.",
        "",
        "## Conteo por scope",
        "",
        "| Scope | Consultas en lote |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{scope}` | {count} |"
        for scope, count in counts["query_count_by_scope"].items()
    )
    lines.extend(["", "## Cola", ""])
    for item in queue["items"]:
        lines.extend(
            [
                f"### `{item['query_id']}` — `{item['scope']}`",
                "",
                f"- **Consulta:** {item['query']}",
                f"- **Categoría / oráculo:** `{item['category']}` / "
                f"`{item['oracle_type']}`",
                f"- **Estado qrels agregado:** `{item['historical_qrel_status']}`",
                "- **Decisión de consulta:** pendiente; no inferida.",
                "",
                "| Chunk ID | Grado histórico | Estado qrel | ACL | Decisión existente | Revisión |",
                "|---|---:|---|---|---|---|",
            ]
        )
        for qrel in item["qrel_references"]:
            lines.append(
                f"| `{qrel['chunk_id']}` | {qrel['historical_grade']} | "
                f"`{qrel['qrel_status']}` | `{qrel['acl_status']}` | "
                f"`{qrel['existing_decision']}` | `{qrel['review_status']}` |"
            )
        lines.append("")
    return "\n".join(lines)


def write_outputs(
    queue: Mapping[str, Any],
    output_json: Path,
    output_markdown: Path,
    *,
    overwrite_existing: bool = False,
    protected_paths: tuple[Path, ...] = (),
) -> None:
    resolved_outputs = {output_json.resolve(), output_markdown.resolve()}
    if len(resolved_outputs) != 2:
        raise QueueError("JSON and Markdown outputs must be different paths")
    if resolved_outputs & {path.resolve() for path in protected_paths}:
        raise QueueError("Queue outputs must not replace the source inventory")
    existing = [path for path in (output_json, output_markdown) if path.exists()]
    if existing and not overwrite_existing:
        raise QueueError(f"Refusing to overwrite output: {existing[0]}")
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    output_markdown.write_text(render_markdown(queue), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--inventory",
        type=Path,
        default=ROOT / "reports/gate2_v2400_coverage_inventory_2026-09-28.json",
    )
    parser.add_argument(
        "--output-json",
        type=Path,
        default=ROOT
        / "reports/gate2_v2400_query_adjudication_queue_2026-09-28.json",
    )
    parser.add_argument(
        "--output-markdown",
        type=Path,
        default=ROOT
        / "reports/gate2_v2400_query_adjudication_queue_2026-09-28.md",
    )
    parser.add_argument("--overwrite-existing", action="store_true")
    args = parser.parse_args(argv)
    try:
        inventory = json.loads(args.inventory.read_text(encoding="utf-8"))
        queue = build_queue(inventory)
        write_outputs(
            queue,
            args.output_json,
            args.output_markdown,
            overwrite_existing=args.overwrite_existing,
            protected_paths=(args.inventory,),
        )
    except (OSError, json.JSONDecodeError, KeyError, QueueError) as exc:
        print(f"Cannot build adjudication queue: {exc}", file=sys.stderr)
        return 2
    print(
        f"Generated {args.output_json} and {args.output_markdown}: "
        f"{queue['counts']['pending_queries_with_historical_qrels']} queries, "
        f"{queue['counts']['qrel_references_for_queued_queries']} qrel references."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
