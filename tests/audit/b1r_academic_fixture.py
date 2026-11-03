"""Memory-only IVG-06C academic input for B1-R; no container, DB or provider.

Retrieval is a scoped fixture, not a test of the storage/ACL implementation.
C5, generation adapter, StructuredResponsePipeline and ForensicAuditor are real.
Only generation (MockBackend) and the typed NLI port are controlled.
"""
import hashlib
from concurrent.futures import Future
from unittest.mock import patch

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import ClaimSupportVerdict
from study_engine.audit.nli import NLIInferenceResult
from study_engine.context.c5_trust import evaluate_epistemic_trust
from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import (
    PromptBundle, PromptMessage, PromptRole, compute_canonical_prompt_hash,
)
from study_engine.llm.backends import MockBackend
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase

QUERY = "Explicá las direcciones IPv4"
SOURCE = "IPv4 utiliza direcciones de 32 bits."
TEXT = "IPv4 utiliza direcciones de 32 bits [E1]."
NOTEBOOK = "b1r-notebook"
CHUNK = {
    "citation_id": "E1", "chunk_id": "b1r-chunk", "document_id": "b1r-document",
    "source_id": "b1r-source", "source_title": "Synthetic IPv4",
    "chunk_text": SOURCE, "trust_level": "canonical", "relevance_score": 0.85,
    "page_start": 1, "page_end": 1,
    "doc_hash": hashlib.sha256(SOURCE.encode()).hexdigest(),
}


class TypedJudge:
    judge_id = "b1r-ivg06c-synthetic-no-model"

    def evaluate_claim(self, premise, hypothesis):
        assert premise == SOURCE
        assert "IPv4" in hypothesis
        verdict = (ClaimSupportVerdict.CONTRADICTED if "128" in hypothesis
                   else ClaimSupportVerdict.ENTAILED)
        return NLIInferenceResult(verdict=verdict, rationale="Typed fixture, not model inference")


class AcademicAuditor:
    def __init__(self):
        self.real = ForensicAuditor(nli_judge=TypedJudge(), nli_reuse_cache=False)
        self.inputs = []
        self.reports = []

    def audit(self, payload):
        self.inputs.append(payload)
        # Scheduling double only: run the typed NLI call inline, never disable
        # the worker's thread guard or replace S4.4's evaluation/validation.
        with patch("study_engine.audit.auditor.ThreadPoolExecutor", InlineExecutor):
            report = self.real.audit(payload)
        self.reports.append(report)
        return report


class InlineExecutor:
    """No concurrency coverage: completed Futures for the synthetic NLI port."""
    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def submit(self, function, *args):
        future = Future()
        try:
            future.set_result(function(*args))
        except Exception as error:
            future.set_exception(error)
        return future


class AcademicBackend:
    name = "b1r-MockBackend"

    async def stream(self, **kwargs):
        parameters = GenerationParameters()
        system = kwargs.get("system_prompt") or "Synthetic fixture"
        messages = (PromptMessage(role=PromptRole.USER, content=QUERY),)
        bundle = PromptBundle(
            system_prompt=system, messages=messages, parameters=parameters,
            prompt_hash=compute_canonical_prompt_hash(system, messages, parameters),
        )
        text = MockBackend(canned_text=TEXT).complete(bundle).text
        for offset in range(0, len(text), 8):
            yield text[offset:offset + 8]


def context(chat, *, empty=False, clarification=False):
    chunks = [] if empty else [dict(CHUNK)]
    trust = evaluate_epistemic_trust(QUERY, chunks)
    assert trust.abstained == empty
    pack = chat.EpistemicContextPack(
        "[E1] " + SOURCE if chunks else "", [], chunks,
        abstained=trust.abstained, is_sufficient=trust.is_sufficient,
        trust_status=trust.status, abstention_reason=trust.abstention_reason,
        clarification_message="Synthetic clarification required." if clarification else None,
    )
    contract = PedagogicalContract(
        notebook_id=NOTEBOOK, base_system_prompt="Synthetic evidence only",
        forbidden_patterns=[], safe_words=[],
        response_phases=[ResponsePhase(
            phase_id="conceptual", phase_prompt_template="Explicá {concept}.", max_tokens=120,
        )],
    )
    return contract, pack, chunks
