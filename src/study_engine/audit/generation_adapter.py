"""Canonical generation adapter for ForensicAuditor (Enmienda E3).

Preserves the normatively frozen S4.4 auditor perimeter (auditor.py) by decoupling
the GenerationRequest/GenerationResponse translation layer into this dedicated module.
"""

import hashlib
import re
from typing import Any, List, Optional
import uuid

from study_engine.audit.contracts import ForensicAuditInput, ForensicAuditReport
from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)


def audit_generation_payload(
    auditor: Any,
    *,
    generated_text: str,
    context_chunks: list,
    query: str,
    notebook_id: str,
    provider_id: str = "talos-llm",
    prompt_hash: Optional[str] = None,
    request_id: Optional[str] = None,
) -> ForensicAuditReport:
    """Adapter satisfying Enmienda E3: builds verified GenerationRequest and GenerationResponse.

    Preserves HG-S4.4 forensic traceability across prompt_hash, provider_id, and evidence hashes.
    """
    manifest_records = {}
    packaged_units = []

    if not context_chunks:
        raise ValueError("At least one evidence chunk is required for forensic audit.")

    for i, chk in enumerate(context_chunks):
        def get_value(key: str, default: Any = None) -> Any:
            if isinstance(chk, dict):
                return chk.get(key, default)
            return getattr(chk, key, default)

        c_id = get_value("citation_id") or get_value("id") or f"E{i+1}"
        chunk_id = get_value("chunk_id")
        doc_id = get_value("document_id")
        src_id = get_value("source_id")
        src_title = get_value("source_title")
        missing_fields = [
            name
            for name, value in (
                ("chunk_id", chunk_id),
                ("document_id", doc_id),
                ("source_id", src_id),
                ("source_title", src_title),
            )
            if not isinstance(value, str) or not value.strip()
        ]
        if missing_fields:
            raise ValueError(
                f"context_chunks[{i}] is missing provenance fields: {', '.join(missing_fields)}."
            )

        content = get_value("chunk_text") or get_value("content") or ""
        if not isinstance(content, str) or not content.strip():
            raise ValueError(f"context_chunks[{i}] has no usable evidence content.")
        content_clean = content.strip()
        provided_hash = get_value("content_hash")
        expected_hash = hashlib.sha256(content_clean.encode("utf-8")).hexdigest()
        if provided_hash is not None:
            if not isinstance(provided_hash, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", provided_hash.strip()):
                raise ValueError(f"context_chunks[{i}] has invalid content_hash: {provided_hash!r}.")
            normalized_hash = provided_hash.strip().lower()
            if normalized_hash == "0" * 64:
                raise ValueError(f"context_chunks[{i}] content_hash is a zero placeholder and not evidence.")
            if normalized_hash != expected_hash:
                raise ValueError(
                    f"context_chunks[{i}] content_hash does not match the retrieved content digest."
                )
        c_hash = expected_hash
        author = get_value("author") or ""
        p_start = get_value("page_start")
        if p_start is None:
            p_start = get_value("page")
        p_end = get_value("page_end")
        if p_end is None:
            p_end = p_start
        trust_level = get_value("trust_level")
        if not isinstance(trust_level, str) or not trust_level.strip():
            trust_level = "unverified"
        elif trust_level not in {"canonical", "unverified"}:
            raise ValueError(
                f"context_chunks[{i}] has unsupported trust_level: {trust_level!r}."
            )

        rec = CitationRecord(
            citation_id=c_id,
            chunk_id=chunk_id,
            document_id=doc_id,
            source_id=src_id,
            source_title=src_title,
            author=author or None,
            page_start=int(p_start) if p_start is not None else None,
            page_end=int(p_end) if p_end is not None else None,
            content_hash=c_hash,
            trust_level=trust_level,
        )
        manifest_records[c_id] = rec

        unit = PackagedEvidenceUnit(
            citation=rec,
            content=content_clean,
            # shortcut: adapter receives already-selected chunks from different
            # callers (chat epistemic context, dialogue ConceptPacket); it cannot
            # know the retrieval modality, so it must not claim one. Upgrade to
            # propagate the actual method from annotated chunks when retrieval
            # starts attaching it.
            retrieval_score=float(get_value("relevance_score") or 0.0),
            retrieval_rank=i + 1,
            retrieval_method=str(get_value("retrieval_method") or "adapter_packaged"),
        )
        packaged_units.append(unit)

    manifest = CitationManifest(records=manifest_records)
    packet = EvidencePacket(
        original_query=query,
        normalized_query=query.lower().strip(),
        notebook_id=notebook_id,
        grounding_decision=GroundingDecision.SUPPORTED if packaged_units else GroundingDecision.NO_CANDIDATES,
        abstention_required=len(packaged_units) == 0,
    )

    formatted_block = "\n\n".join([f"[{u.citation.citation_id}] {u.content}" for u in packaged_units])
    packaged_ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=packaged_units,
        formatted_context_block=formatted_block,
        total_characters=len(generated_text),
        epistemic_policy="Estricta",
    )

    if request_id is not None and (not isinstance(request_id, str) or not request_id.strip()):
        raise ValueError("request_id must be a non-empty string when supplied")
    req_id = request_id if request_id is not None else f"req_{uuid.uuid4().hex[:8]}"
    gen_req = GenerationRequest(
        request_id=req_id,
        notebook_id=notebook_id,
        query=query,
        packaged_context=packaged_ctx,
        mode=GenerationMode.EXPLANATION,
    )

    # Parse citations from generated text
    cited_tags = re.findall(r"\[(E[0-9]+)\]", generated_text)
    parsed_cites = []
    for t in dict.fromkeys(cited_tags):
        in_man = t in manifest_records
        parsed_cites.append(
            ParsedCitation(
                citation_id=t,
                in_manifest=in_man,
                chunk_id=manifest_records[t].chunk_id if in_man else None,
                source_id=manifest_records[t].source_id if in_man else None,
            )
        )

    gen_resp = GenerationResponse(
        response_id=f"resp_{uuid.uuid4().hex[:8]}",
        request_id=req_id,
        notebook_id=notebook_id,
        mode=GenerationMode.EXPLANATION,
        text=generated_text,
        raw_content=generated_text,
        citations=tuple(parsed_cites),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED if packaged_units else GroundingDecision.NO_CANDIDATES,
    )

    effective_prompt_hash = prompt_hash or hashlib.sha256(f"{query}::{notebook_id}::{provider_id}".encode("utf-8")).hexdigest()
    audit_input = ForensicAuditInput(
        request=gen_req,
        response=gen_resp,
        prompt_hash=effective_prompt_hash,
    )

    return auditor.audit(audit_input)
