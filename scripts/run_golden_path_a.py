"""Runner and telemetry harness for Golden Path A (Vertical Slice).

Scenario: GOLDEN-STUDY-V0-POINTERS v1.0.0
Pipeline:
  Frozen Evidence (prog:poin:20, prog:poin:21)
  -> ContextPacker
  -> LLMClient
  -> GenerationOutputParser
  -> ForensicAuditor (S4.4)
  -> ForensicAuditReport & Human Verification

Strict Invariant: Zero modification to student state, ledger, or curriculum.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional, Tuple

from study_engine.contracts.evidence_engine import (
    EvaluatedEvidenceItem,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    SourceRole,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationParameters,
    GenerationRequest,
)
from study_engine.context.packer import ContextPacker
from study_engine.generation.parser import GenerationOutputParser
from study_engine.generation.tutor import StructuredTutor
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    ClaimSupportVerdict,
    ForensicAuditInput,
)
from study_engine.audit.nli import (
    BaseNLIJudge,
    NLIInferenceResult,
)
from study_engine.llm.backends import HttpOpenAIBackend
from study_engine.llm.client import LLMClient


# ---------------------------------------------------------------------------
# Frozen Scenario Constants
# ---------------------------------------------------------------------------
SCENARIO_ID = "GOLDEN-STUDY-V0-POINTERS"
SCENARIO_VERSION = "1.0.0"
CANONICAL_QUERY = (
    "¿Por qué se requieren estructuras dinámicas en lugar de "
    "vectores estáticos en C?"
)
ORACLE_ID = "oracle-def-08"
EXPECTED_CHUNKS = ("prog:poin:20", "prog:poin:21")
PDF_FILENAME = "prog_punteros.pdf"
PDF_EXPECTED_SHA256 = (
    "4ece5c39d64e25953bac8df1f096f43df90662970f5e6225a2e7d6daa8dcaf9d"
)
PHYSICAL_PAGE = 234

EPISTEMIC_POLICY_GOLDEN = (
    "POLÍTICA EPISTÉMICA: ESTRICTA Y VERIFICABLE (NIVEL OBLIGATORIO).\n"
    "1. Responde de forma directa y concisa a la pregunta formulada.\n"
    "2. Basa cada una de tus afirmaciones factuales EXCLUSIVAMENTE en las "
    "evidencias identificadas con [E1] y [E2].\n"
    "3. Cita explícitamente [E1] o [E2] al final de cada oración o afirmación "
    "que contenga datos fácticos.\n"
    "4. NO introduzcas conceptos, terminología ni detalles externos que no "
    "figuren en los fragmentos provistos, aunque sean ciertos en el estándar "
    "de C.\n"
    "5. NO incluyas código de ejemplo a menos que esté presente en la "
    "evidencia.\n"
    "6. NO intentes evaluar al estudiante ni declarar avances en el curso."
)


# ---------------------------------------------------------------------------
# Atomic NLI Judge via HTTP backend
# ---------------------------------------------------------------------------
class LiveHttpNLIJudge(BaseNLIJudge):
    """Atomic NLI judge using the configured LLM backend for S4.4 Layer 2."""

    def __init__(
        self,
        base_url: str,
        api_key: Optional[str],
        model: str,
        timeout: float = 30.0,
    ) -> None:
        self._backend = HttpOpenAIBackend(
            base_url=base_url,
            api_key=api_key,
            default_model=model,
            timeout_seconds=timeout,
        )
        self._judge_id = f"live-nli-{model}"

    @property
    def judge_id(self) -> str:
        return self._judge_id

    def evaluate_claim(
        self, premise: str, hypothesis: str
    ) -> NLIInferenceResult:
        system = (
            "You are an atomic Natural Language Inference (NLI) evaluator for "
            "an academic tutoring system.\n"
            "Evaluate if the PREMISE strictly entails the HYPOTHESIS.\n"
            "Rules:\n"
            "- ENTAILED: The hypothesis is directly supported or logically "
            "deducible from the premise alone.\n"
            "- CONTRADICTED: The hypothesis states the opposite or directly "
            "conflicts with facts in the premise.\n"
            "- NOT_ENTAILED: The hypothesis introduces outside facts, extra "
            "claims, or details not present in the premise, even if "
            "plausible.\n"
            "Output JSON with keys: 'verdict' "
            "(ENTAILED|CONTRADICTED|NOT_ENTAILED), "
            "'confidence' (0.0 to 1.0), and 'rationale'."
        )
        user = (
            f"PREMISE:\n\"{premise}\"\n\n"
            f"HYPOTHESIS:\n\"{hypothesis}\"\n\n"
            "Provide the atomic NLI verdict."
        )

        from study_engine.contracts.generation import GenerationParameters
        from study_engine.generation.prompts import (
            PromptBundle,
            PromptMessage,
            PromptRole,
            compute_canonical_prompt_hash,
        )

        params = GenerationParameters(temperature=0.0, max_output_tokens=1024)
        msgs = (PromptMessage(role=PromptRole.USER, content=user),)
        p_hash = compute_canonical_prompt_hash(system, msgs, params)
        bundle = PromptBundle(
            system_prompt=system,
            messages=msgs,
            parameters=params,
            prompt_hash=p_hash,
        )

        for attempt in range(3):
            try:
                time.sleep(1.5)
                completion = self._backend.complete(bundle)
                text = completion.text.strip()
                # Robust extraction of JSON object
                start_brace = text.find("{")
                end_brace = text.rfind("}")
                if (
                    start_brace != -1
                    and end_brace != -1
                    and end_brace > start_brace
                ):
                    text = text[start_brace:end_brace + 1]

                parsed = json.loads(text)
                v_str = parsed.get("verdict", "").upper()
                if "CONTRADICT" in v_str:
                    verdict = ClaimSupportVerdict.CONTRADICTED
                elif "ENTAILED" in v_str and "NOT" not in v_str:
                    verdict = ClaimSupportVerdict.ENTAILED
                else:
                    verdict = ClaimSupportVerdict.NOT_ENTAILED

                return NLIInferenceResult(
                    verdict=verdict,
                    confidence=float(parsed.get("confidence", 0.9)),
                    rationale=parsed.get("rationale", text[:100]),
                )
            except Exception as e:
                if ("503" in str(e) or "429" in str(e)) and attempt < 2:
                    time.sleep(5.0)
                    continue
                return NLIInferenceResult(
                    verdict=ClaimSupportVerdict.UNASSESSED,
                    confidence=0.0,
                    rationale=f"Judge error: {e}",
                )

        return NLIInferenceResult(
            verdict=ClaimSupportVerdict.UNASSESSED,
            confidence=0.0,
            rationale="Judge exhausted retries without result",
        )


# ---------------------------------------------------------------------------
# Context Assembly Helper
# ---------------------------------------------------------------------------
def build_golden_request(
    repo_root: Path,
    model_name: str,
    oracle_id: str = "oracle-def-08",
    chunk_override: Optional[List[str]] = None,
    temperature: float = 0.0,
    seed: Optional[int] = 42,
    max_tokens: int = 2048,
) -> Tuple[GenerationRequest, Dict[str, Any]]:
    """Build deterministic GenerationRequest for any benchmark oracle."""
    # 1. Load benchmark oracle
    oracle_path = repo_root / "data" / "benchmark" / "benchmark_oracle.json"
    with open(oracle_path, "r", encoding="utf-8") as f:
        oracle_data = json.load(f)

    query_entry = next(
        (q for q in oracle_data.get("queries", []) if q["id"] == oracle_id),
        None,
    )
    if not query_entry:
        raise KeyError(f"Oracle ID '{oracle_id}' not found in {oracle_path}")

    query_text = query_entry["query"]
    notebook_id = query_entry["notebook_id"]
    if chunk_override:
        relevant_chunks = list(chunk_override)
    else:
        relevant_chunks = [
            r["chunk_id"] for r in query_entry.get("relevant", [])
        ]

    # 2. Load manifest for source verification
    manifest_path = (
        repo_root / "data" / "benchmark" / "benchmark_manifest.json"
    )
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    source_map = {s["source_id"]: s for s in manifest_data.get("sources", [])}

    # 3. Load corpus chunks
    corpus_path = repo_root / "data" / "benchmark" / "benchmark_corpus.json"
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)
    chunk_map = {c["id"]: c for c in corpus_data.get("chunks", [])}

    # 4. Verify sources and build EvaluatedEvidenceItems
    evidence_items = []
    pdf_info: Dict[str, Any] = {}
    for rank, cid in enumerate(relevant_chunks, start=1):
        if cid not in chunk_map:
            raise KeyError(f"Expected chunk '{cid}' not found in corpus!")
        c = chunk_map[cid]
        sid = c["source_id"]
        if sid not in source_map:
            raise KeyError(f"Source '{sid}' not in benchmark manifest!")
        src_meta = source_map[sid]

        pdf_path = (
            repo_root / "data" / "benchmark" / "sources" / src_meta["filename"]
        )
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF missing: {pdf_path}")
        actual_pdf_sha = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
        if actual_pdf_sha != src_meta["sha256"]:
            raise ValueError(
                f"PDF SHA-256 mismatch for {src_meta['filename']}: "
                f"{actual_pdf_sha} != {src_meta['sha256']}"
            )

        if not pdf_info:
            pdf_info = {
                "filename": src_meta["filename"],
                "expected_sha256": src_meta["sha256"],
                "physical_page": (
                    234
                    if oracle_id == "oracle-def-08" and not chunk_override
                    else c.get("page_start")
                ),
            }

        author = (
            "Andrés Marzal / Isabel Gracia"
            if "prog" in sid
            else "Andrew S. Tanenbaum / Herbert Bos"
        )
        title = (
            "Introducción a la programación con C"
            if "prog" in sid
            else "Sistemas Operativos Modernos"
        )
        page_start = (
            234
            if oracle_id == "oracle-def-08" and not chunk_override
            else c.get("page_start")
        )

        content_hash = hashlib.sha256(c["content"].encode("utf-8")).hexdigest()
        item = EvaluatedEvidenceItem(
            chunk_id=c["id"],
            document_id=c["document_id"],
            source_id=c["source_id"],
            source_title=title,
            author=author,
            page_start=page_start,
            source_role=SourceRole.PRIMARY,
            priority=1,
            grade=EvidenceGrade.DIRECT,
            content=c["content"],
            content_hash=content_hash,
            retrieval_score=1.0,
            retrieval_rank=rank,
            retrieval_method="benchmark_oracle_pinned",
        )
        evidence_items.append(item)

    # 5. Pack context
    packet = EvidencePacket(
        original_query=query_text,
        normalized_query=query_text.lower().strip(),
        notebook_id=notebook_id,
        evidence_items=evidence_items,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    packer = ContextPacker()
    context = packer.pack(packet=packet, max_characters=4000)

    params = GenerationParameters(
        temperature=temperature,
        max_output_tokens=max_tokens,
        seed=seed,
        suggested_model=model_name,
    )
    scenario_id = (
        SCENARIO_ID
        if oracle_id == "oracle-def-08" and not chunk_override
        else f"BENCHMARK-{oracle_id.upper()}"
    )
    req = GenerationRequest(
        request_id=f"req-{scenario_id.lower()}-01",
        notebook_id=notebook_id,
        query=query_text,
        packaged_context=context,
        mode=GenerationMode.EXPLANATION,
        parameters=params,
    )
    meta = {
        "scenario_id": scenario_id,
        "oracle_id": oracle_id,
        "canonical_query": query_text,
        "expected_chunks": relevant_chunks,
        "pdf_source": pdf_info,
    }
    return req, meta


# ---------------------------------------------------------------------------
# Runner Execution and Telemetry
# ---------------------------------------------------------------------------
def run_scenario(
    repo_root: Path,
    provider: str,
    model: str,
    base_url: str,
    api_key: Optional[str],
    oracle_id: str = "oracle-def-08",
    chunk_override: Optional[List[str]] = None,
    dry_run: bool = False,
    output_json: Optional[Path] = None,
    max_tokens: int = 2048,
) -> Dict[str, Any]:
    """Execute or dry-run Golden Path A."""
    seed = None if provider == "gemini" else 42
    req, meta = build_golden_request(
        repo_root=repo_root,
        model_name=model,
        oracle_id=oracle_id,
        chunk_override=chunk_override,
        temperature=0.0,
        seed=seed,
        max_tokens=max_tokens,
    )
    context_hash = hashlib.sha256(
        req.packaged_context.formatted_context_block.encode("utf-8")
    ).hexdigest()

    # Telemetry structure
    telemetry: Dict[str, Any] = {
        "scenario_id": meta["scenario_id"],
        "scenario_version": SCENARIO_VERSION,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "canonical_query": meta["canonical_query"],
        "oracle_id": meta["oracle_id"],
        "pdf_source": meta["pdf_source"],
        "evidence": {
            "chunks": list(meta["expected_chunks"]),
            "context_hash": context_hash,
            "epistemic_policy": EPISTEMIC_POLICY_GOLDEN,
        },
        "configuration": {
            "provider": provider,
            "base_url": base_url,
            "model": model,
            "temperature": req.parameters.temperature,
            "seed": req.parameters.seed,
            "max_tokens": req.parameters.max_output_tokens,
            "retries": 0,
            "cache": "disabled",
            "google_search": "OFF",
            "dynamic_retrieval": "OFF",
        },
        "execution": {},
    }

    # Prompt assembly to compute prompt_hash
    from study_engine.generation.prompts import PromptAssembler
    assembler = PromptAssembler()
    prompt_bundle = assembler.assemble(req)
    telemetry["configuration"]["prompt_hash"] = prompt_bundle.prompt_hash

    if dry_run:
        telemetry["status"] = "DRY_RUN_COMPLETED"
        telemetry["system_prompt"] = prompt_bundle.system_prompt
        telemetry["messages"] = [
            {"role": m.role.value, "content": m.content}
            for m in prompt_bundle.messages
        ]
        return telemetry

    # LIVE RUN
    backend = HttpOpenAIBackend(
        base_url=base_url,
        api_key=api_key,
        default_model=model,
        timeout_seconds=45.0,
    )
    client = LLMClient(backend=backend, assembler=assembler)
    tutor = StructuredTutor(generator=client, parser=GenerationOutputParser())

    t0 = time.perf_counter()
    gen_resp = tutor.answer(request=req)
    latency_ms = (time.perf_counter() - t0) * 1000.0

    # S4.4 Audit
    audit_input = ForensicAuditInput(
        request=req,
        response=gen_resp,
        prompt_hash=prompt_bundle.prompt_hash,
    )

    nli_judge = LiveHttpNLIJudge(
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=30.0,
    )
    auditor = ForensicAuditor(nli_judge=nli_judge)
    audit_report = auditor.audit(audit_input)

    # Compile telemetry
    telemetry["status"] = "COMPLETED"
    telemetry["execution"] = {
        "latency_ms": latency_ms,
        "raw_text": gen_resp.raw_content,
        "citations": [
            {
                "citation_id": c.citation_id,
                "in_manifest": c.in_manifest,
                "chunk_id": c.chunk_id,
            }
            for c in gen_resp.citations
        ],
        "validation_status": gen_resp.validation_status.value,
        "audit": {
            "overall_verdict": audit_report.overall_verdict.value,
            "nli_executed": audit_report.nli_executed,
            "nli_judge_id": audit_report.nli_judge_id,
            "deterministic_checks": [
                {
                    "id": ch.check_id,
                    "status": ch.status.value,
                    "severity": ch.severity.value,
                    "reason": ch.reason,
                }
                for ch in audit_report.deterministic_checks
            ],
            "claim_verifications": [
                {
                    "claim_index": cv.claim_index,
                    "claim_text": cv.claim_text,
                    "cited_tags": list(cv.cited_tags),
                    "nli_verdict": cv.nli_verdict.value,
                    "rationale": cv.nli_rationale,
                }
                for cv in audit_report.claim_verifications
            ],
        },
        "final_verdict": audit_report.overall_verdict.value,
    }

    if output_json:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(telemetry, f, indent=2, ensure_ascii=False)

    return telemetry


def main() -> int:
    parser = argparse.ArgumentParser(description="Golden Path A Runner")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print config and prompt without calling LLM",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute live call and S4.4 audit",
    )
    parser.add_argument(
        "--provider",
        default="openai",
        help="Provider name (openai, groq, ollama, gemini)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Explicit model identifier",
    )
    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL for provider endpoint",
    )
    parser.add_argument(
        "--output",
        default="data/experiments/golden_path_a_result.json",
        help="Path to save result JSON",
    )
    parser.add_argument(
        "--oracle-id",
        default="oracle-def-08",
        help="Canonical oracle ID from benchmark (default: oracle-def-08)",
    )
    parser.add_argument(
        "--chunks",
        default=None,
        help="Optional comma-separated chunk IDs to override evidence",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=2048,
        help="Maximum completion tokens (default: 2048)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent

    # Auto-load .env file if present
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

    # Resolve provider defaults
    provider = args.provider.lower()
    base_url = args.base_url
    model = args.model
    if provider == "gemini" and model == "gpt-4o-mini":
        model = "gemini-3.8-flash"
    api_key = None

    if provider == "openai":
        base_url = base_url or "https://api.openai.com"
        api_key = os.getenv("OPENAI_API_KEY")
    elif provider == "groq":
        base_url = base_url or "https://api.groq.com/openai"
        api_key = os.getenv("GROQ_API_KEY")
    elif provider == "gemini":
        base_url = (
            base_url
            or "https://generativelanguage.googleapis.com/v1beta/openai"
        )
        api_key = (
            os.getenv("GEMINI_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
            or os.getenv("OPENAI_API_KEY")
        )
    elif provider == "ollama":
        base_url = base_url or os.getenv(
            "OLLAMA_BASE_URL", "http://localhost:11434"
        )
    else:
        base_url = base_url or "http://localhost:11434"

    if args.execute and not api_key and provider != "ollama":
        print(
            f"Error: API key for provider '{provider}' not in environment!",
            file=sys.stderr,
        )
        return 1

    chunk_override = (
        [c.strip() for c in args.chunks.split(",") if c.strip()]
        if args.chunks
        else None
    )

    try:
        res = run_scenario(
            repo_root=repo_root,
            provider=provider,
            model=model,
            base_url=base_url,
            api_key=api_key,
            oracle_id=args.oracle_id,
            chunk_override=chunk_override,
            dry_run=not args.execute,
            output_json=Path(args.output) if args.execute else None,
            max_tokens=args.max_tokens,
        )
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0
    except Exception as e:
        print(f"ERROR executing scenario: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
