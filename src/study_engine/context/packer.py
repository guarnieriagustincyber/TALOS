"""Context Packer for Subsystem S4.1.

Transforms an authorized EvidencePacket into a deterministic,
budget-constrained, and citation-indexed PackagedContext ready for LLM.
"""

from typing import Dict, List, Optional

from study_engine.contracts.evidence_engine import (
    BudgetError,
    CitationManifest,
    CitationRecord,
    CoverageStatus,
    EvaluatedEvidenceItem,
    EvidenceCoverageReport,
    EvidencePacket,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.retrieval import ScoredCandidate

DEFAULT_MAX_CHARACTERS = 4000

POLICY_HEADER = (
    "=== POLÍTICA EPISTÉMICA DE RESPUESTA (CONTRATO OBLIGATORIO) ===\n"
    "1. Basa tu respuesta EXCLUSIVAMENTE en las Evidencias Documentadas.\n"
    "2. Cita obligatoriamente la etiqueta [E#] al realizar cada afirmación.\n"
    "3. Si una evidencia es CONTEXTUAL o NO EVALUADA, califica tu "
    "respuesta (ej: 'según el contexto...') y no la presentes como "
    "definición canónica directa.\n"
    "4. Prohibido extrapolar o inventar datos fuera de las evidencias.\n"
)


class ContextPacker:

    """Deterministic context assembler and budget regulator."""

    def _generate_coverage_warnings(self, report: EvidenceCoverageReport) -> str:
        """Generate forced, inescapable coverage directives for the system prompt (Refinement 3)."""
        warnings = []
        for c in report.coverage:
            if c.status == CoverageStatus.MISSING:
                warnings.append(
                    f"⚠️ TEMA FALTANTE: '{c.sub_query_text}' - "
                    "NO HAY EVIDENCIA DISPONIBLE EN EL CUADERNO. PROHIBIDO GENERAR EXPLICACIÓN O INVENTAR. "
                    "Declara con total transparencia pedagógica que no dispones de fuentes documentadas para este tema."
                )
            elif c.status == CoverageStatus.PARTIAL:
                warnings.append(
                    f"⚠️ TEMA PARCIAL: '{c.sub_query_text}' - "
                    f"SOLO {c.chunks_count} FRAGMENTO(S) DISPONIBLE(S) (calidad {c.quality_score:.2f}). "
                    "LIMITA LA EXPLICACIÓN ESTRICTAMENTE A LO DISPONIBLE Y NO INVENTES DETALLES."
                )

        if not warnings:
            return ""

        return (
            "\n=== ADVERTENCIAS DE COBERTURA DE EVIDENCIA (DIRECTIVA OBLIGATORIA) ===\n"
            + "\n".join(warnings)
            + "\n\nSIGUE ESTAS REGLAS ESTRICTAMENTE:\n"
            "- SI UN TEMA ESTÁ MARCADO COMO 'MISSING', NO GENERES EXPLICACIÓN NI INVENTES DETALLES.\n"
            "- SI UN TEMA ESTÁ MARCADO COMO 'PARTIAL', LIMITA LA EXPLICACIÓN A LO DISPONIBLE.\n"
            "- SIEMPRE CITA LA FUENTE ESPECÍFICA DE CADA AFIRMACIÓN CON [E#].\n"
            "- NUNCA INVENTES DETALLES FALTANTES.\n"
        )

    def pack(
        self,
        packet: EvidencePacket,
        max_characters: int = DEFAULT_MAX_CHARACTERS,
        coverage_report: Optional[EvidenceCoverageReport] = None,
    ) -> PackagedContext:
        """Package an EvidencePacket into an immutable PackagedContext.

        Parameters
        ----------
        packet : EvidencePacket
            Immutable evaluated evidence packet from EvidenceEngine.
        max_characters : int
            Strict upper bound for the entire formatted context block.
        coverage_report : Optional[EvidenceCoverageReport]
            Optional coverage report detailing SUFFICIENT, PARTIAL, or MISSING sub-topics.

        Returns
        -------
        PackagedContext
            Immutable packaged prompt context with citation manifest.
        """
        if max_characters <= 0:
            raise ValueError(
                f"max_characters must be positive, got {max_characters}."
            )

        # Resolve effective coverage report and generate forced warnings (Refinement 3)
        effective_report = coverage_report or packet.coverage_report
        coverage_warnings = (
            self._generate_coverage_warnings(effective_report)
            if effective_report is not None
            else ""
        )
        effective_policy = (
            POLICY_HEADER + coverage_warnings if coverage_warnings else POLICY_HEADER
        )

        # Case 1: Abstention required
        if packet.abstention_required:
            reason_text = (
                packet.abstention_reason
                or "Sin evidencias suficientes en el cuaderno."
            )
            abstention_body = (
                "\n=== AVISO DE ABSTENCIÓN DOCUMENTAL ===\n"
                f"{reason_text}\n"
                "INSTRUCCIÓN AL TUTOR: Informa al estudiante que el "
                "contenido solicitado no forma parte de los documentos del "
                "cuaderno curricular actual."
            )
            full_abstention_block = effective_policy + abstention_body
            if len(full_abstention_block) > max_characters:
                raise BudgetError(
                    f"Budget {max_characters} is insufficient for mandatory "
                    f"abstention block ({len(full_abstention_block)} chars)."
                )

            return PackagedContext(
                packet=packet,
                citation_manifest=CitationManifest(records={}),
                packaged_units=[],
                formatted_context_block=full_abstention_block,
                total_characters=len(full_abstention_block),
                was_truncated=False,
                excluded_units_count=len(packet.evidence_items),
                epistemic_policy=effective_policy,
                coverage_report=effective_report,
            )

        # Case 2: Standard evidence packaging
        header_block = (
            effective_policy + "\n=== EVIDENCIAS DOCUMENTADAS DISPONIBLES ===\n"
        )
        if len(header_block) > max_characters:
            raise BudgetError(
                f"Budget {max_characters} is insufficient for mandatory "
                f"policy header ({len(header_block)} chars)."
            )

        # Step A: Budget Selection (First selection, then assignment of IDs)
        current_length = len(header_block)
        included_items: List[EvaluatedEvidenceItem] = []
        unit_formatted_blocks: List[str] = []
        excluded_count = 0
        was_truncated = False

        for item in packet.evidence_items:
            next_idx = len(included_items) + 1
            citation_tag = f"[E{next_idx}]"

            author_info = f" ({item.author})" if item.author else ""
            page_info = (
                f" | Pág. {item.page_start}"
                if item.page_start is not None
                else ""
            )
            role_info = (
                f" | Rol: {item.source_role.value}"
                if item.source_role is not None
                else ""
            )
            prio_info = (
                f" | Prioridad: {item.priority}"
                if item.priority is not None
                else ""
            )

            unit_block = (
                f"{citation_tag} Fuente: \"{item.source_title}\""
                f"{author_info}{page_info}{role_info}{prio_info} | "
                f"Grado: {item.grade.value}\n"
                f"Contenido: \"{item.content}\"\n"
            )

            # Check separator cost (1 newline between units)
            sep_cost = 1 if included_items else 0
            block_cost = len(unit_block) + sep_cost

            if current_length + block_cost <= max_characters:
                included_items.append(item)
                unit_formatted_blocks.append(unit_block)
                current_length += block_cost
            else:
                # Never slice chunks midway! Exclude whole unit.
                was_truncated = True
                excluded_count += 1

        # Step B: Strict Bijection Invariant (Manifest matches included units)
        citation_records: Dict[str, CitationRecord] = {}
        packaged_units: List[PackagedEvidenceUnit] = []

        for idx, item in enumerate(included_items, start=1):
            cid = f"E{idx}"
            record = CitationRecord(
                citation_id=cid,
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                source_id=item.source_id,
                source_title=item.source_title,
                author=item.author,
                page_start=item.page_start,
                page_end=item.page_end,
                source_role=item.source_role,
                priority=item.priority,
                grade=item.grade,
                trust_level=item.trust_level,
                content_hash=item.content_hash,
            )
            citation_records[cid] = record

            packaged_units.append(
                PackagedEvidenceUnit(
                    citation=record,
                    content=item.content,
                    retrieval_score=item.retrieval_score,
                    retrieval_rank=item.retrieval_rank,
                    retrieval_method=item.retrieval_method,
                )
            )

        citation_manifest = CitationManifest(records=citation_records)

        if unit_formatted_blocks:
            formatted_context = header_block + "\n".join(unit_formatted_blocks)
        else:
            formatted_context = (
                header_block
                + "(Ninguna evidencia cupo en el presupuesto disponible.)\n"
            )

        total_chars = len(formatted_context)
        if total_chars > max_characters:
            raise BudgetError(
                f"Packaging invariant failed: formatted context length "
                f"{total_chars} exceeds max_characters {max_characters}."
            )

        return PackagedContext(
            packet=packet,
            citation_manifest=citation_manifest,
            packaged_units=packaged_units,
            formatted_context_block=formatted_context,
            total_characters=total_chars,
            was_truncated=was_truncated,
            excluded_units_count=excluded_count,
            epistemic_policy=effective_policy,
            coverage_report=effective_report,
        )

    def format_candidate(
        self,
        candidate: ScoredCandidate,
        index: int = 1,
    ) -> str:
        """Format an individual ScoredCandidate with citation metadata.

        Format: [E#] (Fuente: document_id, pág. P) content
        """
        page = (
            candidate.page_start
            or candidate.metadata.get("page_number")
            or candidate.metadata.get("page_start")
        )
        page_info = f", pág. {page}" if page is not None else ""
        return f"[E{index}] (Fuente: {candidate.document_id}{page_info}) {candidate.content}"

    def pack_candidates(
        self,
        candidates: List[ScoredCandidate],
        max_characters: int = DEFAULT_MAX_CHARACTERS,
    ) -> str:
        """Format a list of ScoredCandidates within a strict character budget."""
        if max_characters <= 0:
            raise ValueError(
                f"max_characters must be positive, got {max_characters}."
            )

        header = POLICY_HEADER + "\n=== EVIDENCIAS DOCUMENTADAS DISPONIBLES ===\n"
        if len(header) > max_characters:
            raise BudgetError(
                f"Budget {max_characters} is insufficient for mandatory "
                f"policy header ({len(header)} chars)."
            )

        current_len = len(header)
        unit_blocks: List[str] = []

        for idx, cand in enumerate(candidates, start=1):
            block = self.format_candidate(cand, index=idx)
            sep_cost = 1 if unit_blocks else 0
            if current_len + len(block) + sep_cost <= max_characters:
                unit_blocks.append(block)
                current_len += len(block) + sep_cost
            else:
                break

        if not unit_blocks:
            return header + "(Ninguna evidencia cupo en el presupuesto disponible.)\n"

        return header + "\n".join(unit_blocks) + "\n"

