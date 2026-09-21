"""Deterministic output parser for Subsystem S4.2.

Transforms RawGenerationResult into an authoritative, validated, and
citation-indexed GenerationResponse against request PackagedContext.
"""

import re
from typing import List, Optional, Tuple
import uuid

from study_engine.contracts.generation import (
    AbstentionDetails,
    AbstentionOrigin,
    AbstentionType,
    GenerationRequest,
    GenerationResponse,
    MalformedOutputError,
    ParsedCitation,
    RawGenerationResult,
    ResponseValidationStatus,
)

_CITATION_REGEX = re.compile(r"\[(E[0-9]+)\]")


class GenerationOutputParser:
    """Deterministic parser and citation auditor for raw generation output."""

    @staticmethod
    def extract_citations(text: str) -> Tuple[str, ...]:
        """Extract citation tags in order of appearance without reformatting.

        Purely lexical extraction. Does NOT perform normalization:
        '[E01]' is extracted verbatim as 'E01' and not coerced into 'E1'.
        """
        seen = set()
        citations: List[str] = []
        for block in re.finditer(r"\[([^\]]+)\]", text):
            for match in re.finditer(r"\b(E[0-9]+)\b", block.group(1)):
                cid = match.group(1)
                if cid not in seen:
                    seen.add(cid)
                    citations.append(cid)
        return tuple(citations)

    def parse(
        self,
        raw_result: RawGenerationResult,
        request: GenerationRequest,
        response_id: Optional[str] = None,
    ) -> GenerationResponse:
        """Parse, validate, and certify a raw generation result.

        Parameters
        ----------
        raw_result : RawGenerationResult
            Verbatim output emitted by an S4.3 generator.
        request : GenerationRequest
            Authoritative request containing frozen PackagedContext.
        response_id : Optional[str]
            Optional response identifier (auto-generated if omitted).

        Returns
        -------
        GenerationResponse
            Frozen, certified response record.

        Raises
        ------
        MalformedOutputError
            If raw_content is blank or whitespace-only.
        """
        raw_content = raw_result.raw_content
        if not raw_content or not raw_content.strip():
            raise MalformedOutputError(
                "Generator produced empty or whitespace-only output."
            )

        # 1. Purely lexical citation extraction
        extracted_cids = self.extract_citations(raw_content)

        # 2. Cross-check against CitationManifest
        manifest_records = request.packaged_context.citation_manifest.records
        parsed_citations: List[ParsedCitation] = []
        phantom_citations: List[str] = []

        for cid in extracted_cids:
            if cid in manifest_records:
                record = manifest_records[cid]
                parsed_citations.append(
                    ParsedCitation(
                        citation_id=cid,
                        in_manifest=True,
                        chunk_id=record.chunk_id,
                        source_id=record.source_id,
                        grade=record.grade,
                    )
                )
            else:
                parsed_citations.append(
                    ParsedCitation(
                        citation_id=cid,
                        in_manifest=False,
                    )
                )
                phantom_citations.append(cid)

        # 3. Determine structural validation status
        if phantom_citations:
            validation_status = (
                ResponseValidationStatus.INVALID_CITATION_DETECTED
            )
        else:
            validation_status = ResponseValidationStatus.VALID

        # 4. Resolve abstention status and authoritative origin
        is_abstention = (
            request.packaged_context.packet.abstention_required
            or raw_result.generator_abstained
        )
        abstention_details: Optional[AbstentionDetails] = None

        if is_abstention:
            if request.packaged_context.packet.abstention_required:
                origin = AbstentionOrigin.EVIDENCE_POLICY
                abstention_type = AbstentionType.NO_EVIDENCE
                reason = (
                    request.packaged_context.packet.abstention_reason
                    or "Abstención obligatoria por política de evidencias."
                )
            else:
                origin = AbstentionOrigin.GENERATOR
                abstention_type = AbstentionType.INSUFFICIENT_CONTEXT
                reason = (
                    "El generador determinó abstención por insuficiencia "
                    "contextual en los documentos provistos."
                )

            abstention_details = AbstentionDetails(
                origin=origin,
                abstention_type=abstention_type,
                reason=reason,
                suggested_action="Consultar el cuaderno curricular sugerido.",
            )

        resp_id = response_id or str(uuid.uuid4())
        return GenerationResponse(
            response_id=resp_id,
            request_id=request.request_id,
            notebook_id=request.notebook_id,
            mode=request.mode,
            text=raw_content.strip(),
            raw_content=raw_content,
            citations=tuple(parsed_citations),
            phantom_citations=tuple(phantom_citations),
            validation_status=validation_status,
            is_abstention=is_abstention,
            abstention_details=abstention_details,
            grounding_decision=(
                request.packaged_context.packet.grounding_decision
            ),
            tokens_used=raw_result.tokens_used,
            latency_ms=raw_result.latency_ms,
            model=raw_result.model,
        )
