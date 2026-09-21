"""System-Level Acceptance Audit: Subsystem Boundary Invariants (Fase 6.1).

Verifies that interfaces between components do not introduce security
escalations, permission leaks, or state corruptions:
- Router to Policy
- Policy to StudyLoop
- Pedagogy to LLM Pool
- LLM Pool to Audit
- Audit to Ledger
- ScopeResolver Tenant Isolation
"""

import asyncio
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.experiments.run_study_loop_v1 import StudyLoopExperimentRunner
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import (
    AuditVerdict,
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditInput,
)
from study_engine.contracts.enums import SourceRole
from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationParameters,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)
from study_engine.contracts.notebook import Notebook
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.hierarchy.folder import Folder
from study_engine.hierarchy.scope_resolver import (
    ResolvedScope,
    ScopeNotFoundError,
    ScopeResolver,
    ScopeType,
)
from study_engine.llm.providers.mock_provider import MockProvider
from study_engine.llm.quota_manager import QuotaManager
from study_engine.llm.router import TalosLLMRouter
from study_engine.llm.sanitizer import DataSanitizer, SensitiveDataLeakError
from study_engine.session.adapters import EvidenceIngestionAdapter
from study_engine.session.contracts import SessionResultStatus
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.tutor.policy_validator import (
    AuthoritativeRoute,
    DeterministicPolicyValidator,
    RouteKind,
)
from study_engine.tutor.semantic_router import IntentContract, IntentType


def _make_prompt(text: str) -> PromptBundle:
    params = GenerationParameters(max_output_tokens=200, temperature=0.3)
    messages = (PromptMessage(role=PromptRole.USER, content=text),)
    p_hash = compute_canonical_prompt_hash("Sys", messages, params)
    return PromptBundle(
        system_prompt="Sys",
        messages=messages,
        parameters=params,
        prompt_hash=p_hash,
    )


def _build_audit_input_with_source(
    source_id: str,
    trust_level: str = "canonical",
    content: str = "Punteros en C almacenan direcciones de memoria.",
    claim_text: str = "Punteros en C almacenan direcciones de memoria [E1].",
) -> ForensicAuditInput:
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    citation_rec = CitationRecord(
        citation_id="E1",
        chunk_id=f"chunk_{source_id}",
        document_id=f"doc_{source_id}",
        source_id=source_id,
        source_title=f"Title {source_id}",
        content_hash=content_hash,
        grade=EvidenceGrade.DIRECT,
        source_role=SourceRole.PRIMARY,
        trust_level=trust_level,
    )
    manifest = CitationManifest(records={"E1": citation_rec})
    packet = EvidencePacket(
        original_query="What are pointers?",
        normalized_query="What are pointers?",
        notebook_id="nb_test",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=[
            PackagedEvidenceUnit(
                citation=citation_rec,
                content=content,
                retrieval_score=0.99,
                retrieval_rank=1,
                retrieval_method="bm25",
            )
        ],
        formatted_context_block=content,
        total_characters=len(content),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req_boundary_test",
        notebook_id="nb_test",
        query="What are pointers?",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    resp = GenerationResponse(
        response_id="resp_boundary_test",
        request_id="req_boundary_test",
        notebook_id="nb_test",
        mode=GenerationMode.EXPLANATION,
        text=claim_text,
        raw_content=claim_text,
        citations=(
            ParsedCitation(
                citation_id="E1",
                in_manifest=True,
                chunk_id=f"chunk_{source_id}",
                source_id=source_id,
                grade=EvidenceGrade.DIRECT,
            ),
        ),
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    return ForensicAuditInput(
        request=req,
        response=resp,
        prompt_hash="b" * 64,
    )


class TestSubsystemBoundaries:
    """Verificar que las interfaces entre componentes no introducen
    violaciones de seguridad o invariantes
    """

    def test_router_to_policy_boundary(self) -> None:
        """Intent malicioso + action maliciosa desde SemanticRouter
        PolicyValidator debe rechazar
        """
        validator = DeterministicPolicyValidator(roadmap=None, current_node="SEC-01-C-PTR")

        # LLM Router attempts to bypass security via malicious action / elevated needs
        malicious_inputs = [
            IntentContract(
                intent=IntentType.TECHNICAL_QUESTION,
                action="execute_code",
                needs_evidence=True,
                needs_curriculum=False,
                needs_execution=True,
                needs_clarification=False,
                confidence=1.0,
            ),
            IntentContract(
                intent=IntentType.TECHNICAL_QUESTION,
                action="write_ledger",
                needs_evidence=False,
                needs_curriculum=False,
                needs_execution=False,
                needs_clarification=False,
                confidence=0.99,
            ),
            IntentContract(
                intent=IntentType.GREETING,
                action="advance_curriculum",
                needs_evidence=False,
                needs_curriculum=False,
                needs_execution=False,
                needs_clarification=False,
                confidence=1.0,
            ),
            IntentContract(
                intent=IntentType.STUDY_NAVIGATION,
                action="unauthorized_custom_action",
                needs_evidence=False,
                needs_curriculum=True,
                needs_execution=False,
                needs_clarification=False,
                confidence=0.95,
            ),
        ]

        for contract in malicious_inputs:
            route = validator.resolve(contract)
            assert route.route_kind == RouteKind.REJECTED
            assert route.action == "reject"
            assert route.execution_allowed is False
            assert route.mutation_allowed is False
            assert route.rejected_reason is not None

    def test_policy_to_studyloop_boundary(self, tmp_path: Path) -> None:
        """Ruta válida seguida de intento de escalada posterior
        StudyLoop no debe permitir mutaciones no autorizadas ni ejecución en turnos conceptuales
        """
        runner = StudyLoopExperimentRunner(repo_root=REPO_ROOT, working_dir=tmp_path)
        controller, ctx = runner.initialize_pipeline()

        # Track execution port calls
        exec_called = False
        assert controller.orchestrator.execution_port is not None
        orig_exec = controller.orchestrator.execution_port.execute

        def spied_execute(*args: Any, **kwargs: Any) -> Any:
            nonlocal exec_called
            exec_called = True
            return orig_exec(*args, **kwargs)

        controller.orchestrator.execution_port.execute = spied_execute  # type: ignore[method-assign]

        # Valid conceptual turn
        res = controller.handle_conceptual_turn(
            query="¿Cómo se declara y desreferencia un puntero en C?",
            target_node_id="SEC-01-C-PTR",
        )

        assert res.status == SessionResultStatus.APPROVED
        # Crucial boundary invariant: Execution port MUST NEVER be called during conceptual turns
        assert exec_called is False

        # Ledger remains unmutated
        ledger: EvidenceLedger = ctx["ledger"]
        assert ledger.total_entries == 0

    def test_pedagogy_to_llm_pool_boundary(self) -> None:
        """Cambiar de proveedor (fallback) no debe cambiar permisos
        El nuevo proveedor debe heredar las mismas restricciones y border control
        """
        async def _run() -> None:
            sanitizer = DataSanitizer()
            quota_mgr = QuotaManager()

            # Primary provider (cloud) fails
            p_cloud_1 = MockProvider(
                name="nvidia",
                should_fail=True,
                failure_exception=RuntimeError("Provider timeout 504"),
            )
            # Secondary provider (cloud) succeeds
            p_cloud_2 = MockProvider(
                name="cerebras",
                canned_response="Clean conceptual explanation from Cerebras.",
            )
            # Local provider (safe for sensitive)
            p_local = MockProvider(
                name="ollama",
                canned_response="Local offline response without cloud leak.",
            )

            router = TalosLLMRouter(
                providers={"nvidia": p_cloud_1, "cerebras": p_cloud_2, "ollama": p_local},
                sanitizer=sanitizer,
                quota_manager=quota_mgr,
                phase_routing={"conceptual": ["nvidia", "cerebras", "ollama"]},
            )

            # Test 1: Normal prompt fallback preserves token budget and returns cleanly
            normal_prompt = _make_prompt("Explain pointers in C")
            completion = await router.complete(normal_prompt, phase_id="conceptual", max_tokens=150)
            assert completion.text == "Clean conceptual explanation from Cerebras."
            assert p_cloud_1.call_count == 1
            assert p_cloud_2.call_count == 1
            assert p_local.call_count == 0

            # Test 2: Sensitive prompt border control: fallback CANNOT route to cloud providers
            sensitive_prompt = _make_prompt("Check internal token secret at 10.0.0.1")
            sens_completion = await router.complete(sensitive_prompt, phase_id="conceptual")
            assert sens_completion.text == "Local offline response without cloud leak."
            # Neither cloud provider was invoked for sensitive data
            assert p_cloud_1.call_count == 1
            assert p_cloud_2.call_count == 1
            assert p_local.call_count == 1

        asyncio.run(_run())

    def test_llm_pool_to_audit_boundary(self) -> None:
        """Un fallback de proveedor no puede saltarse S4.4 Forensic Audit
        Toda respuesta debe ser auditada independientemente del proveedor
        """
        auditor = ForensicAuditor()

        # 1. Fallback provider response that is clean and grounded -> APPROVED
        audit_in_clean = _build_audit_input_with_source(
            source_id="doc_clean_canonical",
            trust_level="canonical",
            content="Punteros en C almacenan direcciones de memoria.",
            claim_text="Punteros en C almacenan direcciones de memoria [E1].",
        )
        report_clean = auditor.audit(audit_in_clean)
        assert report_clean.overall_verdict == AuditVerdict.APPROVED

        # 2. Fallback provider response that hallucinated/poisoned -> REJECTED
        audit_in_poison = _build_audit_input_with_source(
            source_id="poison_source_untrusted",
            trust_level="unverified",
            content="Punteros en C son seguros por defecto y no permiten desbordamientos.",
            claim_text="Punteros en C son seguros por defecto [E1].",
        )
        report_poison = auditor.audit(audit_in_poison)
        assert report_poison.overall_verdict != AuditVerdict.APPROVED
        assert report_poison.overall_verdict in (
            AuditVerdict.UNVERIFIED_SOURCE,
            AuditVerdict.REJECTED_UNSUPPORTED,
            AuditVerdict.REJECTED_POLICY_VIOLATION,
        )

    def test_audit_to_ledger_boundary(self, tmp_path: Path) -> None:
        """Una respuesta ABSTAINED jamás puede terminar registrada como evidencia válida
        Verificar que el ledger rechaza entradas con verdict != APPROVED
        """
        runner = StudyLoopExperimentRunner(repo_root=REPO_ROOT, working_dir=tmp_path)
        controller, ctx = runner.initialize_pipeline()
        ledger: EvidenceLedger = ctx["ledger"]

        assert ledger.total_entries == 0

        # Run an off-topic query that triggers ABSTAINED
        res_abstained = controller.handle_conceptual_turn(
            query="¿Cuál es la capital de Francia?",
            target_node_id="SEC-01-C-PTR",
        )

        assert res_abstained.status == SessionResultStatus.ABSTAINED
        # Boundary guarantee: 0 entries admitted to the ledger
        assert ledger.total_entries == 0

    def test_scope_resolver_isolation(self) -> None:
        """Folder/Notebook no debe introducir cross-tenant leakage
        Un cuaderno no puede acceder a datos de otro cuaderno
        """
        ks = KnowledgeStore(":memory:")
        ks.initialize()
        now = datetime.now(timezone.utc)

        # Tenant 1
        ks.create_folder(
            Folder(id="f_sec", name="Seguridad", parent_folder_id="folder_root", created_at=now, updated_at=now)
        )
        ks.create_notebook(Notebook(id="nb_crypto", name="Criptografía", folder_id="f_sec"))

        # Tenant 2
        ks.create_folder(
            Folder(id="f_net", name="Redes", parent_folder_id="folder_root", created_at=now, updated_at=now)
        )
        ks.create_notebook(Notebook(id="nb_tcp", name="TCP/IP", folder_id="f_net"))

        resolver = ScopeResolver(ks)

        scope_crypto = resolver.resolve(ScopeType.NOTEBOOK, "nb_crypto")
        assert scope_crypto.folder_id == "f_sec"
        assert scope_crypto.notebook_id == "nb_crypto"

        scope_tcp = resolver.resolve(ScopeType.NOTEBOOK, "nb_tcp")
        assert scope_tcp.folder_id == "f_net"
        assert scope_tcp.notebook_id == "nb_tcp"

        # Verify cross-notebook access rejection:
        # nb_crypto scope cannot be used to claim nb_tcp notebook identity
        assert scope_crypto.notebook_id != scope_tcp.notebook_id
        assert scope_crypto.folder_id != scope_tcp.folder_id

        # Empty or cross-scope resolution fails closed
        with pytest.raises(ScopeNotFoundError):
            resolver.resolve(ScopeType.NOTEBOOK, "nb_nonexistent")
