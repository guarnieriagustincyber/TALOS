"""Multi-Source Evidence Assembler partitioned by configured roles per notebook.

Retrieves candidate text from knowledge store / vector store and segments evidence
according to config/notebook_source_roles.json.
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import CitationRecord

logger = logging.getLogger(__name__)


class MultiSourceEvidenceAssembler:
    """Retrieves and partitions citations according to notebook source role configuration."""

    def __init__(
        self,
        knowledge_store: Optional[Any] = None,
        roles_config_path: Optional[Path] = None,
        l3_manifest_path: Optional[Path] = None,
    ) -> None:
        self.knowledge_store = knowledge_store
        self.roles_config_path = roles_config_path or (
            Path(__file__).resolve().parents[3] / "config" / "notebook_source_roles.json"
        )
        if l3_manifest_path is not None:
            self.l3_manifest_path: Optional[Path] = l3_manifest_path
        elif roles_config_path is None:
            self.l3_manifest_path = (
                Path(__file__).resolve().parents[3] / "config" / "l3_authorization_manifest.json"
            )
        else:
            self.l3_manifest_path = None
        self._roles_config: Dict[str, Dict[str, Any]] = self._load_roles_config()

    def _load_roles_config(self) -> Dict[str, Dict[str, Any]]:
        if self.roles_config_path.exists():
            try:
                return json.loads(self.roles_config_path.read_text(encoding="utf-8"))
            except Exception:
                logger.exception(
                    "Cannot load source-role configuration from %s; evidence assembly is disabled",
                    self.roles_config_path,
                )
        return {}

    def get_notebook_source_roles(self, notebook_id: str) -> Dict[str, Any]:
        """Fetch configured source roles for a notebook."""
        return self._roles_config.get(notebook_id, {})

    def assemble_evidence_for_kc(
        self,
        notebook_id: str,
        kc_id: str,
        query: str,
    ) -> Tuple[Dict[str, List[CitationRecord]], List[CitationRecord]]:
        """Retrieve and bucket citations by source role for the target KC."""
        nb_roles = self.get_notebook_source_roles(notebook_id)
        evidence_by_role: Dict[str, List[CitationRecord]] = {
            "PRIMARY": [],
            "METHODOLOGICAL": [],
            "FORMAL": [],
            "IMPLEMENTATION": [],
            "COMPLEMENTARY": [],
        }
        all_citations: List[CitationRecord] = []
        citation_counter = 1

        MIN_EVIDENCE_THRESHOLD = 2

        # 1. Retrieval en fuentes prioritarias del notebook (según roles configurados)
        if self.knowledge_store is not None:
            try:
                notebook = self.knowledge_store.get_notebook(notebook_id)
            except Exception:
                logger.exception(
                    "Cannot resolve authorized sources for notebook %s; evidence assembly is closed",
                    notebook_id,
                )
                return evidence_by_role, all_citations

            authorized_sources = set(notebook.sources)
            if self.l3_manifest_path is not None:
                from study_engine.contracts.l3_manifest import get_l3_authorized_sources

                l3_sources = get_l3_authorized_sources(
                    notebook_id, manifest_path=self.l3_manifest_path
                )
                authorized_sources = authorized_sources.intersection(l3_sources)

            active_sources = [
                source_id for source_id in nb_roles if source_id in authorized_sources
            ]
            for src_id in active_sources:
                src_conf = nb_roles.get(src_id, {})
                assigned_roles = src_conf.get("roles", ["COMPLEMENTARY"])
                title = src_conf.get("title", src_id)

                try:
                    chunks = self.knowledge_store.get_chunks_for_source(src_id)
                except Exception:
                    logger.exception(
                        "Cannot retrieve authorized source %s for notebook %s",
                        src_id,
                        notebook_id,
                    )
                    chunks = []

                for chunk in chunks[:2]:
                    chunk_text = getattr(chunk, "content", "")
                    if query.lower() in chunk_text.lower() or not query:
                        cit_key = f"E{citation_counter}"
                        citation_counter += 1
                        rec = CitationRecord(
                            citation_id=cit_key,
                            chunk_id=getattr(chunk, "chunk_id", getattr(chunk, "id", f"{src_id}_chk")),
                            document_id=getattr(chunk, "document_id", f"{src_id}_doc"),
                            source_id=src_id,
                            source_title=title,
                            page_start=getattr(chunk, "page_start", getattr(chunk, "page", 1)),
                            page_end=getattr(chunk, "page_end", getattr(chunk, "page", 1)),
                            source_role=SourceRole.PRIMARY if "PRIMARY" in assigned_roles else SourceRole.REFERENCE,
                            content_hash=hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
                        )
                        for r in assigned_roles:
                            evidence_by_role.setdefault(r, []).append(rec)
                        all_citations.append(rec)

            if len(all_citations) < MIN_EVIDENCE_THRESHOLD:
                logger.info(
                    "Insufficient authorized evidence for notebook %s, KC %s: %d citations",
                    notebook_id,
                    kc_id,
                    len(all_citations),
                )
                return {role: [] for role in evidence_by_role}, []

        return evidence_by_role, all_citations
