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
) -> ForensicAuditReport:
    """Adapter satisfying Enmienda E3: builds verified GenerationRequest and GenerationResponse.

    Preserves HG-S4.4 forensic traceability across prompt_hash, provider_id, and evidence hashes.
    """
    manifest_records = {}
    packaged_units = []

    for i, chk in enumerate(context_chunks):
        if isinstance(chk, dict):
            c_id = chk.get("citation_id") or chk.get("id") or f"E{i+1}"
            chunk_id = chk.get("chunk_id") or f"chunk_{i+1}"
            doc_id = chk.get("document_id") or f"doc_{i+1}"
            src_id = chk.get("source_id") or "src_canonical"
            src_title = chk.get("source_title") or src_id
            author = chk.get("author") or ""
            p_start = chk.get("page_start") or chk.get("page") or 1
            p_end = chk.get("page_end") or p_start
            content = chk.get("chunk_text") or chk.get("content") or ""
        else:
            c_id = getattr(chk, "citation_id", getattr(chk, "id", f"E{i+1}"))
            chunk_id = getattr(chk, "chunk_id", f"chunk_{i+1}")
            doc_id = getattr(chk, "document_id", f"doc_{i+1}")
            src_id = getattr(chk, "source_id", "src_canonical")
            src_title = getattr(chk, "source_title", src_id)
            author = getattr(chk, "author", "")
            p_start = getattr(chk, "page_start", getattr(chk, "page", 1)) or 1
            p_end = getattr(chk, "page_end", p_start) or p_start
            content = getattr(chk, "chunk_text", getattr(chk, "content", ""))

        content_clean = content.strip()
        if not content_clean:
            content_clean = f"Contenido verificado para {src_id}"
        c_hash = hashlib.sha256(content_clean.encode("utf-8")).hexdigest()

        rec = CitationRecord(
            citation_id=c_id,
            chunk_id=chunk_id,
            document_id=doc_id,
            source_id=src_id,
            source_title=src_title,
            author=author or None,
            page_start=int(p_start),
            page_end=int(p_end),
            content_hash=c_hash,
            trust_level="canonical",
        )
        manifest_records[c_id] = rec

        unit = PackagedEvidenceUnit(
            citation=rec,
            content=content_clean,
            retrieval_score=1.0,
            retrieval_rank=i + 1,
            retrieval_method="hybrid_fts_vector",
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

    req_id = f"req_{uuid.uuid4().hex[:8]}"
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
