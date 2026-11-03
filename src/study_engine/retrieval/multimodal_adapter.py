"""Multimodal Evidence Adapter.

Converts multimodal retrieval results into evidence engine compatible items
for integration with the pedagogical pipeline. All content remains PROVISIONAL_UNVERIFIED.
"""

from dataclasses import dataclass
import hashlib
from typing import Any, Dict, List, Optional

from study_engine.contracts.evidence_engine import (
    CoverageStatus,
    EvidenceCoverageReport,
    EvidenceGrade,
    EvaluatedEvidenceItem,
    EvidencePacket,
    GroundingDecision,
    SubQuery,
    SubQueryCoverage,
    SubQueryDecomposition,
)
from study_engine.contracts.multimodal import (
    DocumentClassification,
    RelationType,
)
from study_engine.retrieval.multimodal_retrieval import MultimodalHit
from study_engine.contracts.retrieval import ScoredCandidate


@dataclass(frozen=True)
class MultimodalEvidenceConfig:
    """Configuration for multimodal evidence packaging."""
    max_characters: int = 4000
    notebook_id: str = "multimodal-colab"
    default_grade: EvidenceGrade = EvidenceGrade.UNASSESSED
    default_trust_level: str = "unverified"
    default_priority: int = 1
    default_retrieval_method: str = "multimodal_search"
    default_retrieval_score: float = 0.5


class MultimodalEvidenceAdapter:
    """Converts multimodal retrieval results into evidence engine compatible items."""

    def __init__(self, config: Optional[MultimodalEvidenceConfig] = None):
        self.config = config or MultimodalEvidenceConfig()

    def _compute_content_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content for integrity."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _classify_grade(self, hit: MultimodalHit) -> EvidenceGrade:
        """Map multimodal classification to evidence grade."""
        if hit.page_evidence and hit.page_evidence.classification:
            if hit.page_evidence.classification == "body":
                return EvidenceGrade.SUFFICIENT
            elif hit.page_evidence.classification in ("exercise", "reference"):
                return EvidenceGrade.PARTIAL
            elif hit.page_evidence.classification in ("toc_or_front_matter",):
                return EvidenceGrade.PARTIAL
        return EvidenceGrade.UNASSESSED

    def _determine_trust_level(self, hit: MultimodalHit) -> str:
        """Determine trust level based on content type and verification status."""
        if hit.trusted_for_rag:
            return "canonical"
        if hit.fidelity_certified:
            return "verified"
        return "unverified"

    def _create_chunk_evidence(
        self,
        hit: MultimodalHit,
        index: int,
    ) -> Optional[EvaluatedEvidenceItem]:
        """Create evidence item from the text chunk in a multimodal hit."""
        if not hit.chunk:
            return None

        chunk = hit.chunk
        content = getattr(chunk, "content", "")
        if not content:
            return None

        doc_id = getattr(chunk, "document_id", "unknown")
        source_id = getattr(chunk, "source_id", "unknown")
        page_start = getattr(chunk, "page_start", None)

        # Build element references summary
        element_refs = []
        for elem in hit.multimodal_elements:
            elem_type = elem.get("type", "unknown")
            elem_id = elem.get("data", {}).get("element_id", "unknown")
            relation = elem.get("relation", "unknown")
            element_refs.append(f"{elem_type}:{elem_id}({relation})")

        enriched_content = content
        if element_refs:
            enriched_content += f"\n\n[Elementos multimodales en esta página: {', '.join(element_refs)}]"

        return EvaluatedEvidenceItem(
            chunk_id=getattr(chunk, "id", f"chunk-{index}"),
            document_id=doc_id,
            source_id=source_id,
            source_title=f"Documento {doc_id}",
            author=None,
            page_start=page_start,
            page_end=page_start,
            source_role=None,
            priority=self.config.default_priority,
            grade=self._classify_grade(hit),
            trust_level=self._determine_trust_level(hit),
            content_hash=self._compute_content_hash(enriched_content),
            content=enriched_content,
            retrieval_score=hit.combined_score or self.config.default_retrieval_score,
            retrieval_rank=index + 1,
            retrieval_method=self.config.default_retrieval_method,
        )

    def _create_element_evidence(
        self,
        hit: MultimodalHit,
        element: Dict[str, Any],
        index: int,
    ) -> Optional[EvaluatedEvidenceItem]:
        """Create evidence item from a multimodal element (table/figure/formula)."""
        elem_data = element.get("data", {})
        elem_type = element.get("type", "unknown")
        elem_id = elem_data.get("element_id", f"elem-{index}")

        if elem_type == "table":
            caption = elem_data.get("caption", "")
            headers = elem_data.get("headers", [])
            rows = elem_data.get("rows", [])
            content = f"Tabla: {caption}\n"
            if headers:
                content += f"Cabeceras: {', '.join(headers)}\n"
            if rows:
                content += f"Filas: {len(rows)}\n"
                for i, row in enumerate(rows[:3]):
                    content += f"  Fila {i}: {', '.join(map(str, row))}\n"
                if len(rows) > 3:
                    content += f"  ... ({len(rows) - 3} filas más)\n"

        elif elem_type == "figure":
            caption = elem_data.get("caption", "")
            alt_text = elem_data.get("alt_text", "")
            content = f"Figura: {caption}\n"
            if alt_text:
                content += f"Descripción: {alt_text}\n"

        elif elem_type == "formula":
            latex = elem_data.get("latex", "")
            plain_text = elem_data.get("plain_text", "")
            variables = elem_data.get("variables", [])
            content = f"Fórmula: {latex}\n"
            if plain_text:
                content += f"Texto: {plain_text}\n"
            if variables:
                content += f"Variables: {', '.join(variables)}\n"

        else:
            content = f"Elemento {elem_type}: {elem_id}"

        if not content.strip():
            return None

        doc_id = elem_data.get("document_id", "unknown")
        source_id = elem_data.get("source_id", "unknown")
        page = elem_data.get("page", None)

        # Add relation info
        relation = element.get("relation", "unknown")
        content += f"\n[Relación con fragmento: {relation}]"

        return EvaluatedEvidenceItem(
            chunk_id=f"{elem_type}-{elem_id}",
            document_id=doc_id,
            source_id=source_id,
            source_title=f"Elemento {elem_type} en {doc_id}",
            author=None,
            page_start=page,
            page_end=page,
            source_role=None,
            priority=self.config.default_priority,
            grade=EvidenceGrade.UNASSESSED,
            trust_level="unverified",
            content_hash=self._compute_content_hash(content),
            content=content,
            retrieval_score=hit.combined_score or self.config.default_retrieval_score,
            retrieval_rank=index + 1,
            retrieval_method=self.config.default_retrieval_method,
        )

    def convert_hits_to_evidence_items(
        self,
        hits: List[MultimodalHit],
        query: str = "",
    ) -> List[EvaluatedEvidenceItem]:
        """Convert multimodal hits to evaluated evidence items."""
        evidence_items: List[EvaluatedEvidenceItem] = []

        for index, hit in enumerate(hits):
            # Create chunk evidence
            chunk_item = self._create_chunk_evidence(hit, index)
            if chunk_item:
                evidence_items.append(chunk_item)

            # Create element evidence for each multimodal element
            for elem_index, element in enumerate(hit.multimodal_elements):
                elem_item = self._create_element_evidence(hit, element, elem_index)
                if elem_item:
                    evidence_items.append(elem_item)

        return evidence_items

    def create_evidence_packet(
        self,
        hits: List[MultimodalHit],
        query: str,
        sub_queries: Optional[List[SubQuery]] = None,
    ) -> EvidencePacket:
        """Create an EvidencePacket from multimodal hits."""
        evidence_items = self.convert_hits_to_evidence_items(hits, query)

        # Determine grounding decision based on evidence quality
        has_sufficient = any(item.grade == "SUFFICIENT" for item in evidence_items)
        grounding_decision = GroundingDecision.SUPPORTED if has_sufficient else GroundingDecision.PARTIALLY_SUPPORTED

        # Build coverage report if sub_queries provided
        coverage_report = None
        if sub_queries:
            coverage = []
            for sq in sub_queries:
                # Count items matching this sub-query (simplified)
                matching = [item for item in evidence_items if sq.text.lower() in item.content.lower()]
                if not matching:
                    status = CoverageStatus.MISSING
                elif len(matching) >= 2:
                    status = CoverageStatus.SUFFICIENT
                else:
                    status = CoverageStatus.PARTIAL

                coverage.append(SubQueryCoverage(
                    sub_query_id=sq.sub_query_id,
                    sub_query_text=sq.text,
                    status=status,
                    quality_score=1.0 if status == CoverageStatus.SUFFICIENT else 0.5,
                    chunks_count=len(matching),
                    source_ids=list(set(item.source_id for item in matching)),
                ))

            coverage_report = EvidenceCoverageReport(
                sub_queries=sub_queries,
                coverage=coverage,
                overall_coverage_ratio=sum(1 for c in coverage if c.status == CoverageStatus.SUFFICIENT) / max(len(coverage), 1),
            )

        # Determine if abstention is required
        abstention_required = len(evidence_items) == 0
        abstention_reason = "No hay evidencia multimodal disponible en el cuaderno." if abstention_required else None

        return EvidencePacket(
            original_query=query,
            normalized_query=query.lower().strip(),
            notebook_id=self.config.notebook_id,
            grounding_decision=grounding_decision,
            evidence_items=evidence_items,
            allowed_claims=[],
            unsupported_claims=[],
            abstention_required=abstention_required,
            abstention_reason=abstention_reason,
            has_full_provenance=False,
            coverage_report=coverage_report,
        )

    def decompose_query(self, query: str) -> SubQueryDecomposition:
        """Decompose a query into pedagogical sub-queries."""
        # Simple decomposition based on multimodal patterns
        sub_queries = []
        sq_id = 1

        # Check for explicit element references
        import re
        table_refs = re.findall(r"(?:Table|TABLE|tabla)\s+(\d+\.\d+)", query, re.IGNORECASE)
        figure_refs = re.findall(r"(?:Figure|FIGURE|figura)\s+(\d+\.\d+)", query, re.IGNORECASE)
        formula_refs = re.findall(r"(?:Formula|FORMULA|fórmula|ecuación)\s+(\d+\.\d+)", query, re.IGNORECASE)

        for ref in table_refs:
            sub_queries.append(SubQuery(
                sub_query_id=f"sq-{sq_id}",
                text=f"Table {ref}",
                intent="table_reference",
                priority_score=0.9,
            ))
            sq_id += 1

        for ref in figure_refs:
            sub_queries.append(SubQuery(
                sub_query_id=f"sq-{sq_id}",
                text=f"Figure {ref}",
                intent="figure_reference",
                priority_score=0.9,
            ))
            sq_id += 1

        for ref in formula_refs:
            sub_queries.append(SubQuery(
                sub_query_id=f"sq-{sq_id}",
                text=f"Formula {ref}",
                intent="formula_reference",
                priority_score=0.9,
            ))
            sq_id += 1

        # If no explicit references, decompose by concept
        if not sub_queries:
            # Simple keyword-based decomposition
            concepts = []
            if "3NF" in query.upper() or "tercera forma normal" in query.lower():
                concepts.append("third normal form (3NF)")
            if "select" in query.lower() or "sql" in query.lower():
                concepts.append("SQL SELECT syntax")
            if "dependencia" in query.lower() or "dependencia funcional" in query.lower() or "functional dependenc" in query.lower():
                concepts.append("functional dependencies")
            if "transitiva" in query.lower() or "transitive dependenc" in query.lower():
                concepts.append("transitive dependencies")

            for concept in concepts:
                sub_queries.append(SubQuery(
                    sub_query_id=f"sq-{sq_id}",
                    text=concept,
                    intent="concept_explanation",
                    priority_score=0.7,
                ))
                sq_id += 1

        return SubQueryDecomposition(
            original_query=query,
            sub_queries=sub_queries,
            is_fallback=not sub_queries,
            confidence=1.0 if sub_queries else 0.5,
        )


class MultimodalContextPacker:
    """Packs multimodal evidence into context for pedagogical pipeline."""

    def __init__(self, config: Optional[MultimodalEvidenceConfig] = None):
        self.adapter = MultimodalEvidenceAdapter(config)
        self.config = config or MultimodalEvidenceConfig()

    def pack_for_pedagogy(
        self,
        hits: List[MultimodalHit],
        query: str,
        max_characters: int = 4000,
    ) -> Dict[str, Any]:
        """Pack multimodal hits into a pedagogical context dictionary."""
        # Decompose query for coverage tracking
        decomposition = self.adapter.decompose_query(query)

        # Create evidence packet
        packet = self.adapter.create_evidence_packet(hits, query, decomposition.sub_queries)

        # Pack into context
        from study_engine.context.packer import ContextPacker
        packer = ContextPacker()
        packaged = packer.pack(packet, max_characters=max_characters, coverage_report=packet.coverage_report)

        # Extract multimodal elements summary for pedagogical use
        multimodal_summary = self._build_multimodal_summary(hits)

        return {
            "packaged_context": packaged,
            "evidence_packet": packet,
            "multimodal_summary": multimodal_summary,
            "sub_query_decomposition": decomposition,
            "provenance": {
                "source": "multimodal_staging",
                "trust_status": "PROVISIONAL_UNVERIFIED",
                "hits_count": len(hits),
                "elements_total": sum(len(h.multimodal_elements) for h in hits),
            },
        }

    def _build_multimodal_summary(self, hits: List[MultimodalHit]) -> Dict[str, Any]:
        """Build a summary of multimodal elements for pedagogical context."""
        tables = []
        figures = []
        formulas = []
        pages_with_elements = set()

        for hit in hits:
            for element in hit.multimodal_elements:
                elem_data = element.get("data", {})
                elem_type = element.get("type", "unknown")
                relation = element.get("relation", "unknown")

                summary = {
                    "element_id": elem_data.get("element_id"),
                    "type": elem_type,
                    "relation": relation,
                    "document_id": elem_data.get("document_id"),
                    "page": elem_data.get("page"),
                    "caption": elem_data.get("caption"),
                    "latex": elem_data.get("latex"),
                }

                if elem_type == "table":
                    tables.append(summary)
                elif elem_type == "figure":
                    figures.append(summary)
                elif elem_type == "formula":
                    formulas.append(summary)

                if elem_data.get("page"):
                    pages_with_elements.add(elem_data.get("page"))

            if hit.page_evidence:
                pages_with_elements.add(hit.page_evidence.page_number)

        return {
            "tables": tables,
            "figures": figures,
            "formulas": formulas,
            "pages_with_elements": sorted(pages_with_elements),
            "total_tables": len(tables),
            "total_figures": len(figures),
            "total_formulas": len(formulas),
        }

    def format_for_llm(self, packed: Dict[str, Any]) -> str:
        """Format the packed context for LLM consumption."""
        context_block = packed["packaged_context"].formatted_context_block

        # Add multimodal summary
        summary = packed["multimodal_summary"]
        multimodal_block = "\n=== ELEMENTOS MULTIMODALES DETECTADOS ===\n"
        if summary["tables"]:
            multimodal_block += f"Tablas: {summary['total_tables']}\n"
            for t in summary["tables"][:5]:
                multimodal_block += f"  - Tabla {t['element_id']} (pág. {t['page']}): {t['caption'][:60] if t['caption'] else 'Sin caption'}\n"
        if summary["figures"]:
            multimodal_block += f"Figuras: {summary['total_figures']}\n"
            for f in summary["figures"][:5]:
                multimodal_block += f"  - Figura {f['element_id']} (pág. {f['page']}): {f['caption'][:60] if f['caption'] else 'Sin caption'}\n"
        if summary["formulas"]:
            multimodal_block += f"Fórmulas: {summary['total_formulas']}\n"
            for f in summary["formulas"][:5]:
                multimodal_block += f"  - Fórmula {f['element_id']} (pág. {f['page']}): {f['latex'][:60] if f['latex'] else 'Sin LaTeX'}\n"

        return context_block + "\n" + multimodal_block