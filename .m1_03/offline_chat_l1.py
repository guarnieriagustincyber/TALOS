#!/usr/bin/env python3
"""M1-03 §2: reproducción OFFLINE del fallo L1 (S4.4) del chat live.

Toma las transcripciones EXACTAS del run live m1_02chat_20261021T034510Z
(archive `_audit_c*.txt` del driver) y els chunks del mismo retrieval
determinista (working3), y ejecuta el DeterministicAuditEngine SIN NLI
para identificar qué check L1 produce el fail-closed global.
"""
import hashlib
import re
import sqlite3
import sys
from pathlib import Path

REPO = Path("/media/agustin/Laboratorio/study-engie")
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.audit.contracts import ForensicAuditInput
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
from study_engine.audit.engine import DeterministicAuditEngine as ForensicAuditEngine

WORK_DB = REPO / ".m1_01" / "working3" / "knowledge_store.db"
EV = REPO / ".m1_02" / "evidence"


def load_transcript(tag: str):
    p = EV / f"m1_02chat_20261021T034510Z_audit_{tag}_conceptual.txt"
    raw = p.read_text(encoding="utf-8")
    text = raw.split("=== GENERATED TEXT ===\n")[1].split("\n\n=== VERDICT ===")[0]
    print(f"[{tag}] generado (live, sha-prefijo {hashlib.sha256(text.encode()).hexdigest()[:10]}):")
    print("   ", text[:200].replace("\n", " / "))
    return text


def retrieving_chunks(query: str):
    """Mismo retrieval determinista de la ruta del chat (allowlist fija)."""
    from study_engine.web.dependencies import AppContainer
    from study_engine.web.routes.chat import _assemble_epistemic_context

    container = AppContainer(
        repo_root=REPO,
        working_dir=(REPO / ".m1_01" / "working3").resolve(),
        use_mock=False,
        load_dotenv=False,
    )
    store = container.knowledge_store
    pack, _ = _assemble_epistemic_context(
        store=store,
        container=container,
        prompt_text=query,
        target_notebook_id="fase0-soc",
        active_sources=None,
        granularity_decision=None,
        global_folder_id=None,
        original_user_query=None,
    )
    chunks = []
    for c in pack.chunks:
        chunks.append({
            "id": c.get("chunk_id") or c.get("id"),
            "content": c.get("chunk_text", ""),
            "source_id": c.get("source_id", ""),
            "document_id": f"{c.get('source_id','')}_doc",
        })
    print(f"[query={query[:50]!r}] chunks del pack: {len(chunks)}, tags disponibles: E1..E{len(chunks)}")
    return chunks, pack


def build_audit_input(chunks, answer, query):
    manifest_records = {}
    packaged_units = []
    parsed_ids = {}
    for i, chk in enumerate(chunks):
        content = (chk["content"] or "").strip()
        if not content:
            continue
        c_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        rec = CitationRecord(
            citation_id=f"E{i+1}",
            chunk_id=str(chk["id"]),
            document_id=chk["document_id"],
            source_id=chk["source_id"],
            source_title=f"Fuente {chk['source_id']}",
            content_hash=c_hash,
        )
        manifest_records[f"E{i+1}"] = rec
        packaged_units.append(PackagedEvidenceUnit(
            citation=rec, content=content, retrieval_score=1.0,
            retrieval_rank=i + 1, retrieval_method="hybrid_fts_vector",
        ))
        parsed_ids[f"E{i+1}"] = rec

    manifest = CitationManifest(records=manifest_records)
    packet = EvidencePacket(
        original_query=query,
        normalized_query=query,
        notebook_id="fase0-soc",
        grounding_decision=GroundingDecision.SUPPORTED,
        abstention_required=False,
    )
    formatted_block = "\n\n".join(
        f"[{u.citation.citation_id}] {u.content}" for u in packaged_units
    )
    packaged_ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=packaged_units,
        formatted_context_block=formatted_block,
        total_characters=len(answer),
        epistemic_policy="Estricta",
    )
    gen_req = GenerationRequest(
        request_id="req_offline_chat_l1_repro",
        notebook_id="fase0-soc",
        query=query,
        packaged_context=packaged_ctx,
        mode=GenerationMode.EXPLANATION,
    )
    cited_tags = re.findall(r"\[(E[0-9]+)\]", answer)
    parsed = [
        ParsedCitation(
            citation_id=t,
            in_manifest=t in parsed_ids,
            chunk_id=parsed_ids[t].chunk_id if t in parsed_ids else None,
            source_id=parsed_ids[t].source_id if t in parsed_ids else None,
        )
        for t in dict.fromkeys(cited_tags)
    ]
    gen_resp = GenerationResponse(
        response_id="resp_offline_chat_l1_repro",
        request_id="req_offline_chat_l1_repro",
        notebook_id="fase0-soc",
        mode=GenerationMode.EXPLANATION,
        text=answer,
        raw_content=answer,
        citations=tuple(parsed),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(request=gen_req, response=gen_resp, prompt_hash="0" * 64)


QUERIES = {
    "c1": "¿Cómo funciona la aritmética de punteros y por qué p+1 avanza sizeof(T) bytes?",
    "c2": "Explicá qué es el comportamiento indefinido al acceder fuera de los límites de un arreglo en C.",
}


def main():
    engine = ForensicAuditEngine()
    for tag in ("c1", "c2"):
        text = load_transcript(tag)
        chunks, pack = retrieving_chunks(QUERIES[tag])
        audit_input = build_audit_input(chunks, text, QUERIES[tag])
        det = engine.evaluate(audit_input)
        print(f"\n=== {tag} | early_verdict={det.early_verdict} has_critical={det.has_critical_failure}")
        for c in det.checks:
            print(f"  {c.check_id}={c.status.value} sev={c.severity.name} :: {str(getattr(c, 'reason', ''))[:200]}")
        for cl in det.claims:
            d = det.lexical_diagnostics.get(cl.claim_index)
            st = getattr(d, "status", None)
            print(f"  claim[{cl.claim_index}] {cl.claim_type.value} tags={cl.cited_tags} lex={st}: {cl.claim_text[:80]!r}")
        print()


if __name__ == "__main__":
    main()
