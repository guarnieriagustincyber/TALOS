#!/usr/bin/env python3
"""Runner for S4.4 V0 Robustness Campaign: Phase P3.

Evaluates Contradiction and Semantic Misalignment.
Frozen configuration with reference model gemini-3.5-flash-lite.
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


def run_p3() -> Dict[str, Any]:
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
        if c["family"] == "P3_CONTRADICTION_MISALIGNMENT"
    ]

    results: List[Dict[str, Any]] = []

    print(
        f"--> Starting Robustness execution for {len(cases_to_run)} "
        "cases (Phase P3)..."
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

        # Build context with single cited chunk E1
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

        # Safety outcome: all P3 cases are expected to be blocked
        is_safe_actual = (actual_verdict != "APPROVED")
        safety_outcome = (
            "PASS" if is_safe_actual else "FAIL_OVER_ACCEPTANCE"
        )

        # Claim details and rationale
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

        # Anomaly classification
        if actual_verdict == "APPROVED":
            anomaly_class = (
                "Judge over-acceptance (failed to detect contradiction/alien)"
            )
        elif not matches_verdict:
            anomaly_class = (
                f"Distinction mismatch ({actual_verdict} vs "
                f"{expected_verdict})"
            )
        else:
            anomaly_class = "NONE"

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
            f"[{status_str}] | Latency: {latency_ms:.1f}ms"
        )
        if claim_details:
            print(f"    -> NLI Label: {claim_details[0]['nli_verdict']}")
            print(f"    -> Rationale: {claim_details[0]['rationale']}")

    # Metrics computation
    total = len(results)
    exact_matched = sum(1 for r in results if r["matches_verdict"])
    exact_verdict_accuracy = exact_matched / total if total else 0.0

    # Contradiction metrics
    expected_contradictions = [
        r for r in results if r["expected_label"] == "CONTRADICTED"
    ]
    detected_contradictions = [
        r for r in expected_contradictions
        if r["claim_details"]
        and r["claim_details"][0]["nli_verdict"] == "CONTRADICTED"
    ]
    contradiction_detection_rate = (
        len(detected_contradictions) / len(expected_contradictions)
        if expected_contradictions else 0.0
    )

    non_contradictions = [
        r for r in results if r["expected_label"] != "CONTRADICTED"
    ]
    false_contradictions = [
        r for r in non_contradictions
        if r["claim_details"]
        and r["claim_details"][0]["nli_verdict"] == "CONTRADICTED"
    ]
    false_contradiction_rate = (
        len(false_contradictions) / len(non_contradictions)
        if non_contradictions else 0.0
    )

    # Not-entailed discrimination
    expected_not_entailed = [
        r for r in results if r["expected_label"] == "NOT_ENTAILED"
    ]
    correct_not_entailed = [
        r for r in expected_not_entailed
        if r["claim_details"]
        and r["claim_details"][0]["nli_verdict"] == "NOT_ENTAILED"
    ]
    not_entailed_discrimination_rate = (
        len(correct_not_entailed) / len(expected_not_entailed)
        if expected_not_entailed else 0.0
    )

    # Safety containment
    unsafe_targets = results  # all 3 cases are unsafe
    contained_cases = sum(
        1 for r in unsafe_targets if r["final_verdict"] != "APPROVED"
    )
    safety_containment_rate = (
        contained_cases / len(unsafe_targets) if unsafe_targets else 1.0
    )

    over_accepted_cases = sum(
        1 for r in unsafe_targets if r["final_verdict"] == "APPROVED"
    )
    over_acceptance_rate = (
        over_accepted_cases / len(unsafe_targets) if unsafe_targets else 0.0
    )

    summary = {
        "campaign": "S4.4 V0 ROBUSTNESS P3",
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
            "contradiction_detection_rate": contradiction_detection_rate,
            "false_contradiction_rate": false_contradiction_rate,
            "not_entailed_discrimination_rate": (
                not_entailed_discrimination_rate
            ),
            "metric_definitions": {
                "exact_verdict_accuracy": (
                    "Casos con coincidencia exacta de veredicto sobre "
                    "Total de casos P3 (matches / 3)"
                ),
                "safety_containment_rate": (
                    "Casos bloqueados sobre Casos cuyo ground truth exige "
                    "bloqueo (contained / 3)"
                ),
                "over_acceptance_rate": (
                    "Casos indebidamente aprobados sobre Casos cuyo "
                    "ground truth exige bloqueo (over_accepted / 3)"
                ),
                "contradiction_detection_rate": (
                    "Casos con veredicto CONTRADICTED sobre casos con "
                    "ground truth CONTRADICTED (detected / 2)"
                ),
                "false_contradiction_rate": (
                    "Casos clasificados erróneamente como CONTRADICTED "
                    "sobre casos no contradictorios (false / 1)"
                ),
                "not_entailed_discrimination_rate": (
                    "Casos con veredicto NOT_ENTAILED sobre casos con "
                    "ground truth NOT_ENTAILED (correct / 1)"
                ),
            },
        },
        "cases": results,
    }

    out_path = (
        repo_root
        / "data"
        / "experiments"
        / "robustness"
        / "p3_results.json"
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"--> Done. Wrote results to {out_path}")
    return summary


if __name__ == "__main__":
    run_p3()
