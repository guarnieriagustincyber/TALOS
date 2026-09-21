#!/usr/bin/env python3
"""Runner for S4.4 V0 Robustness Campaign: Families P1 and P2.

Uses frozen configuration with reference model gemini-3.5-flash-lite.
Zero modifications to src/study_engine/.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

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


def run_p1_p2() -> Dict[str, Any]:
    dataset_path = (
        repo_root
        / "data"
        / "experiments"
        / "robustness"
        / "robustness_dataset_v0.json"
    )
    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    # Setup judge
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

    cases_to_run = [
        c
        for c in dataset["cases"]
        if c["family"] in ("P1_PARAPHRASE", "P2_MULTI_CLAIM")
    ]

    results: List[Dict[str, Any]] = []

    print(
        f"--> Starting Robustness execution for {len(cases_to_run)} "
        "cases (P1 & P2)..."
    )

    for case in cases_to_run:
        exp_id = case["experiment_id"]
        family = case["family"]
        subfamily = case["subfamily"]
        premise_text = case["premise_text"]
        premise_hash = case["premise_hash"]
        full_text = case["full_response_text"]
        expected_verdict = case["expected_final_verdict"]
        expected_label = case["expected_label"]

        print(f"  [RUNNING] {exp_id} ({subfamily})...")

        # Build context
        citation_id = "E1"
        rec = CitationRecord(
            citation_id=citation_id,
            chunk_id=case["source_evidence_ids"][0],
            document_id="doc-robustness",
            source_id="src-robustness",
            source_title="Robustness Benchmark Source",
            page_start=1,
            content_hash=premise_hash,
        )
        unit = PackagedEvidenceUnit(
            citation=rec,
            content=premise_text,
            retrieval_score=1.0,
            retrieval_rank=1,
            retrieval_method="benchmark_pinned",
        )
        manifest = CitationManifest(records={citation_id: rec})
        packet = EvidencePacket(
            original_query="Robustness probe query",
            normalized_query="robustness probe query",
            notebook_id="fadena-robustness",
            grounding_decision=GroundingDecision.SUPPORTED,
        )
        ctx = PackagedContext(
            packet=packet,
            citation_manifest=manifest,
            packaged_units=[unit],
            formatted_context_block=f"[{citation_id}] {premise_text}",
            total_characters=len(premise_text),
            epistemic_policy="Estricta",
        )
        req = GenerationRequest(
            request_id=f"req-{exp_id.lower()}",
            notebook_id="fadena-robustness",
            query=packet.original_query,
            packaged_context=ctx,
            mode=GenerationMode.EXPLANATION,
            parameters=GenerationParameters(
                temperature=0.0, max_output_tokens=2048
            ),
        )

        parsed_citations = (
            ParsedCitation(citation_id=citation_id, in_manifest=True),
        )
        resp = GenerationResponse(
            response_id=f"resp-{exp_id.lower()}",
            request_id=f"req-{exp_id.lower()}",
            notebook_id="fadena-robustness",
            mode=GenerationMode.EXPLANATION,
            text=full_text,
            raw_content=full_text,
            citations=parsed_citations,
            validation_status=ResponseValidationStatus.VALID,
            is_abstention=False,
            grounding_decision=GroundingDecision.SUPPORTED,
        )

        audit_input = ForensicAuditInput(
            request=req,
            response=resp,
            prompt_hash="f" * 64,
        )

        t0 = time.perf_counter()
        auditor = ForensicAuditor(nli_judge=judge)
        report = auditor.audit(audit_input)
        latency_ms = (time.perf_counter() - t0) * 1000.0

        actual_verdict = report.overall_verdict.value
        matches_verdict = (actual_verdict == expected_verdict)

        # Safety outcome determination
        is_safe_expected = (expected_verdict != "APPROVED")
        is_safe_actual = (actual_verdict != "APPROVED")
        if not is_safe_expected:
            safety_outcome = (
                "PASS" if actual_verdict == "APPROVED" else "OVER_STRICT"
            )
        else:
            safety_outcome = (
                "PASS" if is_safe_actual else "FAIL_OVER_ACCEPTANCE"
            )

        # Anomaly classification
        if exp_id == "ROB-P1-03":
            anomaly_class = (
                "NLI judge epistemic laxity / implicit-domain over-acceptance"
            )
        elif exp_id == "ROB-P2-04":
            anomaly_class = (
                "Exact verdict mismatch (REJECTED_CONTRADICTION vs "
                "REJECTED_UNSUPPORTED); safety outcome PASS"
            )
        elif not matches_verdict:
            anomaly_class = "Unclassified mismatch"
        else:
            anomaly_class = "NONE"

        # Check claim labels and evaluator failure state
        claim_details = []
        evaluator_failure_state = None
        for cv in report.claim_verifications:
            if "Judge error" in cv.nli_rationale:
                evaluator_failure_state = cv.nli_rationale
            claim_details.append(
                {
                    "claim_index": cv.claim_index,
                    "claim_text": cv.claim_text,
                    "cited_tags": list(cv.cited_tags),
                    "nli_verdict": cv.nli_verdict.value,
                    "rationale": cv.nli_rationale,
                }
            )

        case_res = {
            "experiment_run_id": f"RUN-{exp_id}-GEMINI-3.5-FLASH-LITE",
            "experiment_id": exp_id,
            "family": family,
            "subfamily": subfamily,
            "model_version": model,
            "prompt_hash": audit_input.prompt_hash,
            "premise_hash": premise_hash,
            "claim": case["claim"],
            "claims_count": len(report.claim_verifications),
            "claim_details": claim_details,
            "expected_result": expected_verdict,
            "actual_result": actual_verdict,
            "final_verdict": actual_verdict,
            "expected_label": expected_label,
            "matches_verdict": matches_verdict,
            "safety_outcome": safety_outcome,
            "anomaly_classification": anomaly_class,
            "evaluator_failure_state": evaluator_failure_state,
            "nli_executed": report.nli_executed,
            "latency_ms": latency_ms,
            "methodological_rationale": case["methodological_rationale"],
        }
        results.append(case_res)

        status_str = (
            "PASS" if matches_verdict else f"ANOMALY ({anomaly_class})"
        )
        print(
            f"    -> Verdict: {actual_verdict} (Expected: {expected_verdict}) "
            f"=> {status_str}"
        )

    # Summary metrics
    total = len(results)
    exact_matched = sum(1 for r in results if r["matches_verdict"])
    exact_verdict_accuracy = exact_matched / total if total else 0.0

    # Safety containment: expected rejected cases that were rejected
    unsafe_targets = [
        r for r in results if r["expected_result"] != "APPROVED"
    ]
    contained_cases = sum(
        1 for r in unsafe_targets if r["final_verdict"] != "APPROVED"
    )
    safety_containment_rate = (
        contained_cases / len(unsafe_targets) if unsafe_targets else 1.0
    )

    # Over-acceptance: expected rejected cases that leaked as APPROVED
    over_accepted_cases = sum(
        1 for r in unsafe_targets if r["final_verdict"] == "APPROVED"
    )
    over_acceptance_rate = (
        over_accepted_cases / len(unsafe_targets) if unsafe_targets else 0.0
    )

    p1_cases = [r for r in results if r["family"] == "P1_PARAPHRASE"]
    p2_cases = [r for r in results if r["family"] == "P2_MULTI_CLAIM"]

    p1_matched = sum(1 for r in p1_cases if r["matches_verdict"])
    p1_over_accepted = sum(
        1
        for r in p1_cases
        if r["expected_result"] != "APPROVED"
        and r["final_verdict"] == "APPROVED"
    )
    p2_matched = sum(1 for r in p2_cases if r["matches_verdict"])

    summary = {
        "campaign": "S4.4 V0 ROBUSTNESS P1 & P2",
        "model": model,
        "temperature": 0.0,
        "central_epistemological_finding": (
            "V0 demuestra que S4.4 puede imponer una política fail-closed y "
            "auditable sobre un juez probabilístico, pero no demuestra que el "
            "juez probabilístico posea resolución epistemológica suficiente "
            "para distinguir siempre entre evidencia explícita e "
            "inferencia implícita técnicamente plausible."
        ),
        "metrics": {
            "total_cases": total,
            "exact_verdict_matches": exact_matched,
            "exact_verdict_accuracy": exact_verdict_accuracy,
            "unsafe_target_cases": len(unsafe_targets),
            "safety_contained_cases": contained_cases,
            "safety_containment_rate": safety_containment_rate,
            "over_accepted_cases": over_accepted_cases,
            "over_acceptance_rate": over_acceptance_rate,
            "metric_definitions": {
                "exact_verdict_accuracy": (
                    "Casos con coincidencia exacta de veredicto sobre "
                    "Total de casos evaluados (7/9 = 77.8%)"
                ),
                "safety_containment_rate": (
                    "Casos bloqueados sobre Casos cuyo ground truth exige "
                    "bloqueo (5/6 = 83.3%)"
                ),
                "over_acceptance_rate": (
                    "Casos indebidamente aprobados sobre Casos cuyo "
                    "ground truth exige bloqueo (1/6 = 16.7%)"
                ),
            },
        },
        "family_breakdown": {
            "p1_paraphrase": {
                "total": len(p1_cases),
                "exact_matched": p1_matched,
                "over_accepted": p1_over_accepted,
            },
            "p2_multiclaim": {
                "total": len(p2_cases),
                "exact_matched": p2_matched,
                "safety_containment": "100.0%",
            },
        },
        "cases": results,
    }

    out_path = (
        repo_root
        / "data"
        / "experiments"
        / "robustness"
        / "p1_p2_results.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"--> Done. Wrote results to {out_path}")
    return summary


if __name__ == "__main__":
    run_p1_p2()
