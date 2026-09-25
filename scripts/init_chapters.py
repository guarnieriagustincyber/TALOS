#!/usr/bin/env python3
"""Script to initialize chapter mapping template for a notebook (Enmienda E-M2).

Scans chunks and sources in KnowledgeStore and produces config/notebooks/{notebook_id}/chapters.json.
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path
import re
import sqlite3
import sys

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def find_db_path(explicit_path: str | None = None) -> Path:
    if explicit_path:
        p = Path(explicit_path)
        if p.exists():
            return p
    candidates = [
        Path("data/web_state/knowledge_store.db"),
        Path("data/knowledge_store.db"),
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]


def init_chapters_for_notebook(notebook_id: str, db_path: Path, output_path: Path) -> dict:
    if not db_path.exists():
        logger.error("Database not found at %s", db_path)
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get sources associated with the notebook
    cursor.execute(
        """
        SELECT s.source_id, s.title, s.author
        FROM sources s
        JOIN notebook_sources ns ON ns.source_id = s.source_id
        WHERE ns.notebook_id = ?
        ORDER BY s.priority DESC, s.source_id ASC;
        """,
        (notebook_id,),
    )
    sources = cursor.fetchall()

    if not sources:
        # Fallback: get sources from chunks
        cursor.execute(
            """
            SELECT DISTINCT s.source_id, s.title, s.author
            FROM sources s
            JOIN chunks c ON c.source_id = s.source_id
            LIMIT 10;
            """
        )
        sources = cursor.fetchall()

    logger.info("Found %d sources for notebook %s", len(sources), notebook_id)

    # Load canonical KCs for this notebook if available
    kc_catalog_path = Path("config/notebook_kc_catalog.json")
    notebook_kcs = []
    if kc_catalog_path.exists():
        try:
            with open(kc_catalog_path, "r", encoding="utf-8") as f:
                kc_data = json.load(f)
                entry = kc_data.get(notebook_id, {})
                if isinstance(entry, dict):
                    notebook_kcs = entry.get("kcs", [])
                elif isinstance(entry, list):
                    notebook_kcs = entry
        except Exception as e:
            logger.debug("Error loading notebook_kc_catalog: %s", e)

    mapping: dict = {
        "notebook_id": notebook_id,
        "sources": {},
    }

    for source_id, source_title, author in sources:
        cursor.execute(
            """
            SELECT id, chapter, page_start, page_end, content, metadata
            FROM chunks
            WHERE source_id = ?
            ORDER BY page_start ASC, pos_index ASC;
            """,
            (source_id,),
        )
        chunks = cursor.fetchall()
        if not chunks:
            continue

        chapters_dict = {}
        for chk_id, chk_chapter, p_start, p_end, content, meta_str in chunks:
            chap_name = chk_chapter or "Capítulo General"
            if chap_name not in chapters_dict:
                chapters_dict[chap_name] = {
                    "chunks": [],
                    "p_start": p_start or 1,
                    "p_end": p_end or 1,
                }
            chapters_dict[chap_name]["chunks"].append((chk_id, content))
            if p_start and p_start < chapters_dict[chap_name]["p_start"]:
                chapters_dict[chap_name]["p_start"] = p_start
            if p_end and p_end > chapters_dict[chap_name]["p_end"]:
                chapters_dict[chap_name]["p_end"] = p_end

        # Convert to chapter entries
        chapters_list = []
        for idx, (c_name, c_data) in enumerate(chapters_dict.items(), start=1):
            combined_text = " ".join([txt for _, txt in c_data["chunks"]]).lower()
            matching_kcs = []
            for kc in notebook_kcs:
                if isinstance(kc, dict):
                    kc_id = kc.get("id") or kc.get("kc_id", "")
                    kc_title = kc.get("title", "")
                else:
                    kc_id = str(kc)
                    kc_title = str(kc)
                if kc_id.lower() in combined_text or (kc_title and kc_title.lower() in combined_text):
                    matching_kcs.append(kc_id)

            num_match = re.search(r"\b(\d+)\b", c_name)
            chap_num = int(num_match.group(1)) if num_match else idx

            chapters_list.append({
                "chapter_number": chap_num,
                "title": c_name if c_name != "Capítulo General" else f"Unidad {idx}: {source_title[:40]}",
                "page_start": c_data["p_start"],
                "page_end": c_data["p_end"],
                "primary_kcs": matching_kcs,
                "chunk_count": len(c_data["chunks"]),
            })

        mapping["sources"][source_id] = {
            "title": source_title,
            "author": author,
            "chapters": chapters_list,
        }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)

    logger.info("Saved chapter template to %s", output_path)
    return mapping


def main():
    parser = argparse.ArgumentParser(description="Initialize chapter mapping template for a notebook")
    parser.add_argument("--notebook", required=True, help="Notebook ID (e.g. fase0-soc)")
    parser.add_argument("--db-path", help="Path to knowledge_store.db")
    parser.add_argument("--output", help="Output JSON path")
    args = parser.parse_args()

    db_path = find_db_path(args.db_path)
    output_path = Path(args.output) if args.output else Path(f"config/notebooks/{args.notebook}/chapters.json")

    init_chapters_for_notebook(args.notebook, db_path, output_path)


if __name__ == "__main__":
    main()
