#!/usr/bin/env python3
"""Reproduction and Epistemological Verification of RUN-004 Finding.

Evaluates the exact Claim 4 from RUN-004 against chunk prog:poin:21 using
the certified reference model gemini-3.5-flash-lite under frozen protocol.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

repo_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(repo_root / "scripts"))

# Auto-load .env
env_file = repo_root / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'").strip('"')
            if k and k not in os.environ:
                os.environ[k] = v

from run_golden_path_a import LiveHttpNLIJudge  # type: ignore[import-not-found] # noqa: E402,E501
from study_engine.audit.auditor import ForensicAuditor  # noqa: E402
from study_engine.audit.contracts import (  # noqa: E402
    AuditVerdict,
    ClaimSupportVerdict,
    ForensicAuditInput,
)
from study_engine.contracts.evidence_engine import (  # noqa: E402
    CitationManifest,
    CitationRecord,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.generation import (  # noqa: E402
    GenerationMode,
    GenerationParameters,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)


def reproduce_run_004() -> Dict[str, Any]:
    # 1. Load exact premise from benchmark_corpus.json
    corpus_path = repo_root / "data" / "benchmark" / "benchmark_corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    chunk_21 = next(
        c for c in corpus_data["chunks"] if c["id"] == "prog:poin:21"
    )
    premise_text = chunk_21["content"]
    premise_hash = hashlib.sha256(premise_text.encode("utf-8")).hexdigest()

    # 2. Reconstruct exact Claim 4 from RUN-004
    # Claim text from golden_path_a_result.json:
    # "Para resolver estos inconvenientes de tamaño mediante la gestión
    # dinámica de memoria, C hace uso de punteros a través de dos
    # aproximaciones principales..."
    claim_text = (
        "Para resolver estos inconvenientes de tamaño mediante la gestión "
        "dinámica de memoria, C hace uso de punteros a través de dos "
        "aproximaciones principales"
    )
    full_response_text = f"{claim_text} [E1]."

    # 3. Setup NLI Judge
    api_key = (
        os.getenv("GEMINI_API_KEY")
        or os.getenv("GOOGLE_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    base_url = "https://generativelanguage.googleapis.com/v1beta/openai"
    model = "gemini-3.5-flash-lite"

    judge = LiveHttpNLIJudge(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=30.0,
    )

    # 4. Atomic claim evaluation
    atomic_nli_result = judge.evaluate_claim(
        premise=premise_text, hypothesis=claim_text
    )

    # 5. Full S4.4 Auditor invocation
    citation_record = CitationRecord(
        citation_id="E1",
        chunk_id="prog:poin:21",
        document_id="doc-prog-punteros",
        source_id="src-prog-punteros",
        source_title="Introducción a la programación con C",
        author="Andrés Marzal / Isabel Gracia",
        page_start=234,
        content_hash=premise_hash,
    )
    unit = PackagedEvidenceUnit(
        citation=citation_record,
        content=premise_text,
        retrieval_score=1.0,
        retrieval_rank=1,
        retrieval_method="benchmark_pinned",
    )
    manifest = CitationManifest(records={"E1": citation_record})
    norm_query = (
        "¿por qué se requieren estructuras dinámicas en lugar "
        "de vectores estáticos en c?"
    )
    packet = EvidencePacket(
        original_query=(
            "¿Por qué se requieren estructuras dinámicas en lugar "
            "de vectores estáticos en C?"
        ),
        normalized_query=norm_query,
        notebook_id="fadena-prog",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[unit],
        formatted_context_block=f"[E1] {premise_text}",
        total_characters=len(premise_text),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-run-004-repro",
        notebook_id="fadena-prog",
        query=packet.original_query,
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
        parameters=GenerationParameters(
            temperature=0.0, max_output_tokens=2048
        ),
    )
    resp = GenerationResponse(
        response_id="resp-run-004-repro",
        request_id="req-run-004-repro",
        notebook_id="fadena-prog",
        mode=GenerationMode.EXPLANATION,
        text=full_response_text,
        raw_content=full_response_text,
        citations=(ParsedCitation(citation_id="E1", in_manifest=True),),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    audit_input = ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="f" * 64,
    )

    auditor = ForensicAuditor(nli_judge=judge)
    report = auditor.audit(audit_input)

    reproduction_telemetry = {
        "experiment_id": "ROBUSTNESS-RUN-004-REPRO",
        "description": (
            "Reproduction of subtle unsupported concept finding from RUN-004"
        ),
        "model": model,
        "temperature": 0.0,
        "premise_chunk_id": "prog:poin:21",
        "premise_hash": premise_hash,
        "premise_snippet": premise_text[:150] + "...",
        "claim_text": claim_text,
        "cited_tag": "E1",
        "atomic_nli_verdict": atomic_nli_result.verdict.value,
        "atomic_nli_rationale": atomic_nli_result.rationale,
        "atomic_nli_confidence": atomic_nli_result.confidence,
        "overall_s4_verdict": report.overall_verdict.value,
        "reproduction_successful": (
            atomic_nli_result.verdict == ClaimSupportVerdict.NOT_ENTAILED
            and report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
        ),
    }

    out_file = (
        repo_root
        / "data"
        / "experiments"
        / "robustness"
        / "run_004_reproduction.json"
    )
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(reproduction_telemetry, f, indent=2, ensure_ascii=False)

    return reproduction_telemetry


if __name__ == "__main__":
    res = reproduce_run_004()
    print(json.dumps(res, indent=2, ensure_ascii=False))
    if not res["reproduction_successful"]:
        sys.exit(1)
    sys.exit(0)
