"""Staging-only inspection. L3 grants never promote provisional content to RAG."""
from dataclasses import dataclass, field
import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional, List

from study_engine.contracts.l3_manifest import get_effective_sources
from study_engine.contracts.multimodal import (
    DocumentClassification,
    PageEvidence,
    RelationType,
    TRUST,
    check_provisional,
)
from study_engine.ingestion.multimodal_importer import STAGING_SCHEMA, temporary_path


@dataclass
class MultimodalHit:
    chunk: Any
    multimodal_elements: list = field(default_factory=list)
    page_evidence: Optional[PageEvidence] = None
    combined_score: float = 0.0
    trusted_for_rag: bool = False
    fidelity_certified: bool = False
    production_import_authorized: bool = False


class MultimodalRetriever:
    def __init__(self, knowledge_store, notebook_id="multimodal-colab", *, manifest_path=None, source_ids=None, document_id=None):
        self.store = knowledge_store
        self.notebook_id = notebook_id
        self.manifest_path = manifest_path or getattr(knowledge_store, "l3_manifest_path", None)
        self.source_ids = None if source_ids is None else frozenset(source_ids)
        self.document_id = document_id
        self._require_staging()

    def _require_staging(self):
        temporary_path(self.store.engine.db_path)
        with self.store.engine.transaction(mode="DEFERRED") as conn:
            row = conn.execute("SELECT schema FROM mm_staging").fetchone()
        if row != (STAGING_SCHEMA,):
            raise ValueError("Multimodal inspection requires isolated staging")

    def _classify_page(self, page_evidence: PageEvidence, chunk_text: str = "") -> DocumentClassification:
        """Conservative page classification based on available evidence."""
        # Use explicit classification if present
        if page_evidence.classification:
            return page_evidence.classification
        
        # Check is_preliminary flag
        if page_evidence.is_preliminary:
            return DocumentClassification.TOC_OR_FRONT_MATTER
        
        # Check text content for TOC/front matter indicators
        text = (page_evidence.text_content or "") + " " + chunk_text
        text_lower = text.lower()
        
        # TOC/front matter patterns
        toc_patterns = [
            r"^\s*table of contents\s*$",
            r"^\s*contents\s*$",
            r"^\s*index\s*$",
            r"^\s*preface\s*$",
            r"^\s*acknowledgments?\s*$",
            r"^\s*about (this )?book\s*$",
            r"^\s*how to use (this )?book\s*$",
            r"^\s*chapter \d+\s*$",  # Chapter list in TOC
        ]
        for pattern in toc_patterns:
            if re.search(pattern, text_lower, re.MULTILINE):
                return DocumentClassification.TOC_OR_FRONT_MATTER
        
        # Exercise patterns
        exercise_patterns = [
            r"^\s*exercise\s+\d+",
            r"^\s*problem\s+\d+",
            r"^\s*review question\s+\d+",
            r"^\s*practice problem\s+\d+",
            r"^\s*assignment\s+\d+",
        ]
        for pattern in exercise_patterns:
            if re.search(pattern, text_lower, re.MULTILINE):
                return DocumentClassification.EXERCISE
        
        # Reference patterns (appendices, bibliographies, glossaries)
        ref_patterns = [
            r"^\s*appendix\s+[A-Z]",
            r"^\s*bibliography\s*$",
            r"^\s*references\s*$",
            r"^\s*glossary\s*$",
            r"^\s*index\s*$",
        ]
        for pattern in ref_patterns:
            if re.search(pattern, text_lower, re.MULTILINE):
                return DocumentClassification.REFERENCE
        
        # Default to BODY for content pages
        return DocumentClassification.BODY

    def _detect_explicit_reference(self, chunk_text: str, elements: list) -> bool:
        """Detect if chunk text explicitly references multimodal elements.
        
        Checks for:
        - Direct element ID mentions
        - Numbered references like "Table 6.2", "Figure 3.32", "Formula 4.5"
        - Caption references
        """
        if not chunk_text or not elements:
            return False
        text = chunk_text.lower()
        
        for elem in elements:
            data = elem.get("data", {})
            eid = data.get("element_id", "")
            kind = elem.get("type", "")
            
            # Direct element ID mention
            if eid and eid.lower() in text:
                return True
            
            # Check for numbered references based on element type and ID
            # Extract table/figure/formula number from element metadata
            ref_patterns = []
            if kind == "table":
                table_id = data.get("table_id", "")
                caption = data.get("caption", "")
                if table_id:
                    # Table 6.2, Table 1.1, etc.
                    ref_patterns.append(f"table {table_id.lower()}")
                    ref_patterns.append(f"table {table_id.lower().replace('_', '.')}")
                if caption:
                    # Extract table number from caption like "TABLE 6.2 Normal Forms"
                    import re
                    match = re.search(r'table\s+(\d+\.\d+)', caption.lower())
                    if match:
                        ref_patterns.append(f"table {match.group(1)}")
            elif kind == "figure":
                figure_id = data.get("figure_id", "")
                caption = data.get("caption", "")
                if figure_id:
                    ref_patterns.append(f"figure {figure_id.lower()}")
                    ref_patterns.append(f"figure {figure_id.lower().replace('_', '.')}")
                if caption:
                    import re
                    match = re.search(r'figure\s+(\d+\.\d+)', caption.lower())
                    if match:
                        ref_patterns.append(f"figure {match.group(1)}")
            elif kind == "formula":
                formula_id = data.get("formula_id", "")
                if formula_id:
                    ref_patterns.append(f"formula {formula_id.lower()}")
                    ref_patterns.append(f"formula {formula_id.lower().replace('_', '.')}")
                caption = data.get("caption", "")
                if caption:
                    import re
                    match = re.search(r'formula\s+(\d+\.\d+)', caption.lower())
                    if match:
                        ref_patterns.append(f"formula {match.group(1)}")
            
            for pattern in ref_patterns:
                if pattern in text:
                    return True
            
            # Check for numbered references in element ID hash (fallback)
            if eid:
                parts = eid.split(":")[-1]
                if len(parts) > 8 and parts[:8] in text:
                    return True
        return False

    def _is_explicit_reference_match(self, query: str, data: dict) -> bool:
        """Check if query contains an explicit reference matching this element's metadata.
        
        Checks for numbered references like "Table 6.2", "Figure 3.32", "Formula 4.5"
        in the query that match the element's caption or ID.
        """
        if not query or not data:
            return False
        query_lower = query.lower()
        kind = data.get("element_type", data.get("kind", ""))
        
        if kind == "table":
            caption = data.get("caption", "")
            # Extract table number from caption like "TABLE 6.2 Normal Forms"
            import re
            match = re.search(r'table\s+(\d+\.\d+)', caption.lower()) if caption else None
            if match:
                pattern = f"table {match.group(1)}"
                if pattern in query_lower:
                    return True
            # Also check for direct caption match
            if caption and caption.lower() in query_lower:
                return True
        elif kind == "figure":
            caption = data.get("caption", "")
            import re
            match = re.search(r'figure\s+(\d+\.\d+)', caption.lower()) if caption else None
            if match:
                pattern = f"figure {match.group(1)}"
                if pattern in query_lower:
                    return True
            if caption and caption.lower() in query_lower:
                return True
        elif kind == "formula":
            formula_id = data.get("formula_id", "")
            if formula_id:
                if f"formula {formula_id.lower()}" in query_lower or \
                   f"formula {formula_id.lower().replace('_', '.')}" in query_lower:
                    return True
            caption = data.get("caption", "")
            if caption:
                import re
                match = re.search(r'formula\s+(\d+\.\d+)', caption.lower())
                if match:
                    pattern = f"formula {match.group(1)}"
                    if pattern in query_lower:
                        return True
                if caption.lower() in query_lower:
                    return True
        return False

    def _extract_explicit_reference_patterns(self, query: str) -> list:
        """Extract explicit reference patterns from query like 'Table 6.2', 'Figure 3.32'."""
        import re
        patterns = []
        query_lower = query.lower()
        
        # Table references: "Table 6.2", "TABLE 6.2", "table 6.2"
        table_matches = re.finditer(r'(?:table|tabla)\s+(\d+\.\d+)', query.lower())
        for m in table_matches:
            patterns.append(("table", m.group(1)))
        
        # Figure references: "Figure 3.32", "FIGURE 3.32", "figure 3.32"
        figure_matches = re.finditer(r'(?:figure|figura)\s+(\d+\.\d+)', query.lower())
        for m in figure_matches:
            patterns.append(("figure", m.group(1)))
        
        # Formula references: "Formula 4.5", "FORMULA 4.5", "formula 4.5"
        formula_matches = re.finditer(r'(?:formula|fórmula)\s+(\d+\.\d+)', query.lower())
        for m in formula_matches:
            patterns.append(("formula", m.group(1)))
        
        return patterns

    def _matches_explicit_patterns(self, data: dict, patterns: list) -> bool:
        """Check if element data matches any of the explicit reference patterns."""
        if not patterns:
            return False
        
        kind = data.get("element_type", data.get("kind", ""))
        
        for elem_kind, pattern_num in patterns:
            if kind != elem_kind:
                continue
            
            if elem_kind == "table":
                caption = data.get("caption", "")
                import re
                match = re.search(r'table\s+(\d+\.\d+)', caption.lower()) if caption else None
                if match and match.group(1) == pattern_num:
                    return True
                # Also check direct caption match
                if caption and f"table {pattern_num}" in caption.lower():
                    return True
            elif elem_kind == "figure":
                caption = data.get("caption", "")
                import re
                match = re.search(r'figure\s+(\d+\.\d+)', caption.lower()) if caption else None
                if match and match.group(1) == pattern_num:
                    return True
                if caption and f"figure {pattern_num}" in caption.lower():
                    return True
            elif elem_kind == "formula":
                formula_id = data.get("formula_id", "")
                if formula_id and (f"formula {formula_id.lower()}" == f"formula {pattern_num}" or \
                                   f"formula {formula_id.lower().replace('_', '.')}" == f"formula {pattern_num}"):
                    return True
                caption = data.get("caption", "")
                import re
                match = re.search(r'formula\s+(\d+\.\d+)', caption.lower()) if caption else None
                if match and match.group(1) == pattern_num:
                    return True
                if caption and f"formula {pattern_num}" in caption.lower():
                    return True
        return False

    def _search_explicit_references(self, patterns: list, limit: int, element_types: Optional[list], did: Optional[str], allowed: set) -> list:
        """Search for elements matching explicit reference patterns directly in the database.
        
        This bypasses the FTS index and searches directly in mm_elements for elements
        matching the explicit reference patterns (e.g., "Table 6.2", "Figure 3.32").
        """
        if not patterns:
            return []
        
        hits = []
        # Build SQL query to find elements matching explicit patterns
        # We search in mm_elements for captions/IDs matching the patterns
        placeholders = ",".join("?" for _ in allowed)
        base_sql = f"""
            SELECT c.* FROM mm_elements c 
            JOIN documents d ON d.id=c.document_id AND d.source_id=c.source_id 
            JOIN notebook_sources ns ON ns.source_id=c.source_id 
            WHERE ns.notebook_id=? AND c.source_id IN ({placeholders})
        """
        
        params_base = [self.notebook_id, *allowed]
        
        for elem_kind, pattern_num in patterns:
            # Build query for this specific pattern
            if elem_kind == "table":
                # Search for tables with caption containing the pattern
                sql = f"""
                    SELECT c.* FROM mm_elements c 
                    JOIN documents d ON d.id=c.document_id AND d.source_id=c.source_id 
                    JOIN notebook_sources ns ON ns.source_id=c.source_id 
                    WHERE ns.notebook_id=? AND c.source_id IN ({placeholders})
                    AND c.kind='table'
                    AND (json_extract(c.data, '$.caption') LIKE ? OR json_extract(c.data, '$.table_id') LIKE ?)
                """
                params = [self.notebook_id, *allowed, f"%{pattern_num}%", f"%{pattern_num}%"]
            elif elem_kind == "figure":
                sql = f"""
                    SELECT c.* FROM mm_elements c 
                    JOIN documents d ON d.id=c.document_id AND d.source_id=c.source_id 
                    JOIN notebook_sources ns ON ns.source_id=c.source_id 
                    WHERE ns.notebook_id=? AND c.source_id IN ({placeholders})
                    AND c.kind='figure'
                    AND json_extract(c.data, '$.caption') LIKE ?
                """
                params = [self.notebook_id, *allowed, f"%{pattern_num}%"]
            elif elem_kind == "formula":
                sql = f"""
                    SELECT c.* FROM mm_elements c 
                    JOIN documents d ON d.id=c.document_id AND d.source_id=c.source_id 
                    JOIN notebook_sources ns ON ns.source_id=c.source_id 
                    WHERE ns.notebook_id=? AND c.source_id IN ({placeholders})
                    AND c.kind='formula'
                    AND (json_extract(c.data, '$.caption') LIKE ? OR json_extract(c.data, '$.formula_id') LIKE ?)
                """
                params = [self.notebook_id, *allowed, f"%{pattern_num}%", f"%{pattern_num}%"]
            else:
                continue
            
            if did:
                sql += " AND c.document_id=?"
                params.append(did)
            
            if element_types and elem_kind not in element_types:
                continue
            
            sql += " LIMIT ?"
            params.append(limit)
            
            with self.store.engine.transaction(mode="DEFERRED") as conn:
                cursor = conn.cursor()
                cursor.row_factory = sqlite3.Row
                rows = cursor.execute(sql, params).fetchall()
                
                for row in rows:
                    data = check_provisional(json.loads(row["data"]))
                    relation = "candidate_match"
                    if self._is_explicit_reference_match(f"{row['kind'].capitalize()} {pattern_num}", data):
                        relation = RelationType.EXPLICIT_REFERENCE_CANDIDATE
                    hits.append(MultimodalHit(None, [dict(type=row["kind"], data=data, relation=relation)], combined_score=1.0))
        
        return hits

    def _deduplicate_multimodal(self, hits: list, limit: int) -> list:
        """Deduplicate multimodal elements by (document_id, kind, element_id) within each hit source."""
        # Track seen elements per hit source to avoid cross-source deduplication
        # Priority: chunk-based hits (with context) > direct element matches
        seen_per_source = {}
        deduped = []
        
        for hit in hits:
            source_key = "chunk" if hit.chunk else "direct"
            if source_key not in seen_per_source:
                seen_per_source[source_key] = set()
            
            new_elements = []
            for elem in hit.multimodal_elements:
                data = elem.get("data", {})
                key = (data.get("document_id"), elem.get("type"), data.get("element_id"))
                if key and key not in seen_per_source[source_key]:
                    seen_per_source[source_key].add(key)
                    new_elements.append(elem)
            if new_elements:
                hit.multimodal_elements = new_elements
                deduped.append(hit)
            elif hit.chunk and not hit.multimodal_elements:
                # Keep text-only hits
                deduped.append(hit)
            if len(deduped) >= limit:
                break
        return deduped

    def _scope(self, document_id=None):
        self._require_staging()
        # No fallback to installed sources or the production/default manifest.
        # Fail-closed: if no manifest_path configured, deny all access.
        if not self.manifest_path:
            return [], None
        allowed = get_effective_sources(self.store, self.notebook_id, manifest_path=Path(self.manifest_path))
        if self.source_ids is not None:
            allowed.intersection_update(self.source_ids)
        if self.document_id and document_id and document_id != self.document_id:
            return [], None
        return sorted(allowed), document_id or self.document_id

    def _rows(self, table, document_id=None, page=None, query=None, limit=None):
        allowed, did = self._scope(document_id)
        if not allowed:
            return []
        placeholders = ",".join("?" for _ in allowed)
        sql = f"SELECT c.* FROM {table} c JOIN documents d ON d.id=c.document_id AND d.source_id=c.source_id JOIN notebook_sources ns ON ns.source_id=c.source_id WHERE ns.notebook_id=? AND c.source_id IN ({placeholders})"
        params = [self.notebook_id, *allowed]
        if did:
            sql += " AND c.document_id=?"
            params.append(did)
        if page is not None:
            if type(page) is not int or page < 1:
                raise ValueError("Invalid physical page")
            sql += " AND c.page=?" if table != "chunks" else " AND c.page_start<=? AND c.page_end>=?"
            params.extend([page] if table != "chunks" else [page, page])
        if query is not None:
            sanitized = self.store.lexical_index.sanitize_query(query)
            if not sanitized:
                return []
            sql += " AND c.id IN (SELECT id FROM mm_fts WHERE mm_fts MATCH ?)"
            params.append(sanitized)
        sql += " ORDER BY c.document_id, c.rowid"
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        with self.store.engine.transaction(mode="DEFERRED") as conn:
            cursor = conn.cursor()
            cursor.row_factory = sqlite3.Row
            return [dict(r) for r in cursor.execute(sql, params).fetchall()]

    def _find_elements_on_page(self, page, element_types=None, *, document_id=None):
        # Find elements on a specific page within a specific document
        # If document_id is provided, only search within that document
        # If document_id is None, return empty list (no cross-document search)
        rows = self._rows("mm_elements", document_id, page)
        if not rows:
            return []
        if len({r["document_id"] for r in rows}) > 1:
            return []
        elements = []
        for r in rows:
            if element_types and r["kind"] not in element_types:
                continue
            data = check_provisional(json.loads(r["data"]))
            elem = dict(data, multimodal_type=r["kind"], **TRUST)
            elements.append(elem)
        return elements

    def _get_page_evidence(self, page_number, *, document_id=None):
        rows = self._rows("mm_pages", document_id, page_number)
        if len(rows) != 1:
            return None
        return PageEvidence.model_validate_json(rows[0]["data"])

    def get_page_context(self, page_number, include_chunks=True, include_elements=True, *, document_id=None):
        # Allow querying by page/document even without PageEvidence
        doc_id = document_id
        if doc_id is None:
            # Try to infer document_id from chunks on this page
            with self.store.engine.transaction(mode="DEFERRED") as conn:
                rows = conn.execute(
                    "SELECT DISTINCT document_id FROM chunks WHERE page_start<=? AND page_end>=?",
                    (page_number, page_number)
                ).fetchall()
            if len(rows) == 1:
                doc_id = rows[0][0]
            elif len(rows) > 1:
                # Ambiguous: multiple documents have chunks on this page
                return None
            else:
                return None
        
        # Respect retriever-level document_id restriction
        if self.document_id and doc_id != self.document_id:
            return None
        
        # Check if this document is accessible under current ACL
        # Get the document's source_id
        with self.store.engine.transaction(mode="DEFERRED") as conn:
            row = conn.execute("SELECT source_id FROM documents WHERE id=?", (doc_id,)).fetchone()
        if not row:
            return None
        doc_source_id = row[0]
        
        # Check ACL
        allowed = get_effective_sources(self.store, self.notebook_id, manifest_path=Path(self.manifest_path)) if self.manifest_path else set()
        if self.source_ids is not None:
            allowed = allowed.intersection(self.source_ids)
        # Fail-closed: if no allowed sources, deny access
        if not allowed:
            return None
        if doc_source_id not in allowed:
            return None
        
        # Get page evidence if it exists
        pe = self._get_page_evidence(page_number, document_id=doc_id)
        
        context = dict(page_evidence=pe, chunks=[], tables=[], figures=[], formulas=[], **TRUST)
        if include_chunks:
            context["chunks"] = [self.store.get_chunk(r["id"]) for r in self._rows("chunks", doc_id, page_number)]
        if include_elements:
            elements = self._find_elements_on_page(page_number, document_id=doc_id)
            for elem in elements:
                context[elem["multimodal_type"] + "s"].append(elem)
        return context

    def _expand_with_multimodal(self, result, element_types=None, include_pages=True, filter_preliminary=True):
        elements = self._find_elements_on_page(result.page_start, element_types, document_id=result.document_id) if result.page_start else []
        pe = self._get_page_evidence(result.page_start, document_id=result.document_id) if include_pages and result.page_start else None
        if pe and filter_preliminary and pe.is_preliminary:
            pe = None
        
        # Classify page and detect explicit references
        chunk_text = getattr(result, 'content', '') or ''
        has_explicit_ref = self._detect_explicit_reference(chunk_text, elements)
        
        enriched_elements = []
        for e in elements:
            relation = e.get("relation", "on_same_page")
            if has_explicit_ref and relation == "on_same_page":
                relation = RelationType.EXPLICIT_REFERENCE_CANDIDATE
            enriched_elements.append(dict(type=e["multimodal_type"], data=e, relation=relation))
        
        return MultimodalHit(result, enriched_elements, pe, result.score)

    def search_multimodal(self, query, limit=10, element_types=None, include_pages=True, filter_preliminary=True, document_id=None):
        if limit <= 0:
            return []
        # Use provided document_id or fall back to retriever's document_id
        did = document_id or self.document_id
        allowed, _ = self._scope(did)
        if not allowed:
            return []
        hits = []
        
        # Check for explicit reference patterns in query
        explicit_patterns = self._extract_explicit_reference_patterns(query)
        
        # If explicit patterns found, do a targeted search for those specific elements
        if explicit_patterns:
            explicit_hits = self._search_explicit_references(explicit_patterns, limit, element_types, did, allowed)
            for h in explicit_hits:
                hits.append(h)
        
        # Direct element matches - scoped by allowed sources and document
        for row in self._rows("mm_elements", query=query, limit=limit, document_id=did):
            if element_types and row["kind"] not in element_types:
                continue
            data = check_provisional(json.loads(row["data"]))
            relation = "candidate_match"
            # Check for explicit reference in query matching this element
            if self._is_explicit_reference_match(query, data):
                relation = RelationType.EXPLICIT_REFERENCE_CANDIDATE
            # Boost score for explicit reference pattern matches
            combined_score = 1.0 if explicit_patterns and self._matches_explicit_patterns(data, self._extract_explicit_reference_patterns(query)) else 0.0
            hits.append(MultimodalHit(None, [dict(type=row["kind"], data=data, relation=relation)], combined_score=combined_score))
        # Text chunk matches with multimodal expansion
        for result in self.store.fts_search(query, notebook_id=self.notebook_id, source_ids=allowed, document_id=did, limit=limit * 2):
            hits.append(self._expand_with_multimodal(result, element_types, include_pages, filter_preliminary))
        
        # Apply classification penalties (BODY > UNKNOWN > EXERCISE > REFERENCE > TOC)
        classification_penalty = {
            DocumentClassification.BODY: 0.0,
            DocumentClassification.UNKNOWN: 0.05,
            DocumentClassification.EXERCISE: 0.15,
            DocumentClassification.REFERENCE: 0.20,
            DocumentClassification.TOC_OR_FRONT_MATTER: 0.30,
        }
        for hit in hits:
            # Determine page classification from page_evidence or chunk
            penalty = 0.0
            if hit.page_evidence:
                penalty = classification_penalty.get(hit.page_evidence.classification or DocumentClassification.UNKNOWN, 0.05)
            elif hit.chunk and hit.chunk.page_start:
                # Try to get page evidence for chunk's page
                pe = self._get_page_evidence(hit.chunk.page_start, document_id=getattr(hit.chunk, 'document_id', None))
                if pe:
                    penalty = classification_penalty.get(pe.classification or DocumentClassification.UNKNOWN, 0.05)
            hit.combined_score = max(0.0, hit.combined_score - penalty)
        
        # SQL-specific ranking: boost actual SQL syntax, penalize reference tables
        sql_keywords = {"select", "from", "where", "join", "inner", "left", "right", "outer", "group by", "order by", "having", "union", "insert", "update", "delete", "create table", "alter table", "drop table", "foreign key", "primary key", "references", "constraint"}
        ref_table_indicators = {"table 8.", "table 7.", "table 9.", "table 10.", "selected string functions", "selected date/time functions", "sql data manipulation", "sql join expression", "data types", "reserved words"}
        
        for hit in hits:
            if hit.chunk:
                text = (hit.chunk.content or "").lower()
                # Check for SQL syntax patterns
                sql_syntax_score = sum(1 for kw in sql_keywords if kw in text)
                # Check for reference table indicators
                ref_table_score = sum(1 for ind in ref_table_indicators if ind in text)
                
                # Boost for actual SQL syntax
                if sql_syntax_score > 0:
                    hit.combined_score += min(sql_syntax_score * 0.15, 0.6)
                # Penalize reference tables
                if ref_table_score > 0 and sql_syntax_score == 0:
                    hit.combined_score = max(0.0, hit.combined_score - ref_table_score * 0.2)
        
        # Deduplicate multimodal elements before applying limit
        hits = self._deduplicate_multimodal(hits, limit)
        return sorted(hits, key=lambda h: h.combined_score, reverse=True)[:limit]

    def search_with_context(self, query, limit=10, context_window=1):
        # Context expansion remains within the same document and effective L3 scope.
        return self.search_multimodal(query, limit=limit)