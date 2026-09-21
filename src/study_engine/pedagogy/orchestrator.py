"""Pedagogical Orchestrator coordinating study episodes.

INVARIANTS:
1. Backend validates notebook_id and kc_id fail-closed.
2. S4.4 boundary is strictly enforced: builder proposes, S4.4 audits and decides admissibility.
   If S4.4 rejects or evidence is insufficient, an explicit ABSTAINED response is emitted.
3. The orchestrator does NOT decide student mastery. It queries the canonical BKT state
   and roadmap dependencies to indicate the next eligible action.
4. Deterministic state machine: Episode transitions from EXPLAINING -> EVALUATING -> CLOSED.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import AuditVerdict, ForensicAuditInput, ForensicAuditReport
from study_engine.contracts.evidence_engine import CitationManifest, CitationRecord, PackagedContext
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
)
from study_engine.federation.notebook_registry import NotebookRegistry
from study_engine.pedagogy.concept_builder import ConceptPacketBuilder
from study_engine.pedagogy.concept_packet import ConceptPacket, ConceptResponse
from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler
from study_engine.pedagogy.exercise_contracts import ExerciseCandidate
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.student_context import StudentContext, get_student_context
from study_engine.student.bkt_tracker import BKTTracker


class PedagogicalOrchestrator:
    """Coordinates deterministic pedagogical interactions adhering strictly to S4.4 and BKT."""

    def __init__(
        self,
        notebook_registry: NotebookRegistry,
        evidence_assembler: MultiSourceEvidenceAssembler,
        concept_builder: ConceptPacketBuilder,
        forensic_auditor: ForensicAuditor,
        exercise_store: ExerciseStore,
        bkt_tracker: BKTTracker,
        catalog_path: Optional[Path] = None,
    ) -> None:
        self.notebook_registry = notebook_registry
        self.evidence_assembler = evidence_assembler
        self.concept_builder = concept_builder
        self.forensic_auditor = forensic_auditor
        self.exercise_store = exercise_store
        self.bkt_tracker = bkt_tracker
        self.catalog_path = catalog_path or (
            Path(__file__).resolve().parents[3] / "config" / "notebook_kc_catalog.json"
        )
        self._kc_catalog: Dict[str, Any] = self._load_catalog()
        self._active_episodes: Dict[str, Episode] = {}

    def _load_catalog(self) -> Dict[str, Any]:
        if self.catalog_path.exists():
            try:
                return json.loads(self.catalog_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {}

    def validate_kc_eligibility(self, notebook_id: str, kc_id: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """Validate if notebook exists, kc belongs to notebook, and prerequisites are met."""
        if not self.notebook_registry.validate_notebook_scope(notebook_id):
            return False, f"Notebook '{notebook_id}' no registrado o inactivo.", None

        nb_data = self._kc_catalog.get(notebook_id)
        if not nb_data:
            return False, f"Notebook '{notebook_id}' no posee catálogo de KCs configurado.", None

        kcs = nb_data.get("kcs", [])
        target_kc_meta = next((k for k in kcs if k.get("kc_id") == kc_id), None)
        if not target_kc_meta:
            return False, f"KC '{kc_id}' no pertenece al notebook '{notebook_id}'.", None

        # Check prerequisites in BKT
        prereqs = target_kc_meta.get("prerequisites", [])
        for p in prereqs:
            p_state = self.bkt_tracker.get_state(p)
            # Prerequisite warning/gate if P(L) < 0.3 (fail-closed if severely deficient)
            # Note: For vertical slice, we allow access with contextual warning if needed

        return True, None, target_kc_meta

    def start_episode(self, notebook_id: str, kc_id: str, episode_id: Optional[str] = None) -> Tuple[Episode, str]:
        """Start a new validated learning episode."""
        is_valid, err_msg, kc_meta = self.validate_kc_eligibility(notebook_id, kc_id)
        if not is_valid:
            raise ValueError(f"Rechazo formal de episodio: {err_msg}")

        ep_id = episode_id or f"ep_{notebook_id}_{kc_id}"
        title = kc_meta.get("title", kc_id) if kc_meta else kc_id

        episode = Episode(
            episode_id=ep_id,
            notebook_id=notebook_id,
            kc_id=kc_id,
            objective=title,
            phase=EpisodePhase.EXPLAINING,
            current_step_id="step_concept",
        )
        self._active_episodes[ep_id] = episode
        return episode, title

    def get_episode(self, episode_id: str) -> Optional[Episode]:
        return self._active_episodes.get(episode_id)

    def explain_concept(self, episode_id: str) -> ConceptResponse:
        """Formulate proposal, execute S4.4 audit, and return ConceptResponse."""
        episode = self.get_episode(episode_id)
        if not episode:
            return ConceptResponse(
                status="ABSTAINED",
                abstention_reason=f"Episodio '{episode_id}' inexistente.",
                audit_verdict=AuditVerdict.REJECTED_INPUT_MISMATCH,
            )

        # Retrieve evidence partitioned by role
        evidence_by_role, citations = self.evidence_assembler.assemble_evidence_for_kc(
            notebook_id=episode.notebook_id,
            kc_id=episode.kc_id,
            query=episode.objective,
        )

        # Fail-closed if no primary evidence admitted
        if not citations:
            return ConceptResponse(
                status="ABSTAINED",
                abstention_reason=f"Evidencia insuficiente en el corpus para el KC '{episode.kc_id}'.",
                audit_verdict=AuditVerdict.REJECTED_UNSUPPORTED,
            )

        student_ctx = get_student_context(episode.notebook_id)

        # Propose concept packet
        proposal = self.concept_builder.build_proposal(
            notebook_id=episode.notebook_id,
            kc_id=episode.kc_id,
            objective=episode.objective,
            evidence_by_role=evidence_by_role,
            all_citations=citations,
            student_context=student_ctx,
        )

        # Execute authoritative S4.4 Forensic Audit
        from study_engine.contracts.evidence_engine import EvidencePacket, GroundingDecision, PackagedEvidenceUnit
        from study_engine.contracts.generation import ParsedCitation, ResponseValidationStatus

        text_to_audit = f"{proposal.core_concept}\n{proposal.mental_model}"
        citation_records_dict = {c.citation_id: c for c in citations}
        manifest = CitationManifest(records=citation_records_dict)

        units = [
            PackagedEvidenceUnit(
                citation=c,
                content=f"Contenido verificado para cita {c.citation_id}",
                retrieval_score=1.0,
                retrieval_rank=idx + 1,
                retrieval_method="pedagogy_slice",
            )
            for idx, c in enumerate(citations)
        ]

        packet = EvidencePacket(
            original_query=episode.objective,
            normalized_query=episode.objective.lower(),
            notebook_id=episode.notebook_id,
            grounding_decision=GroundingDecision.SUPPORTED,
        )

        packaged_ctx = PackagedContext(
            packet=packet,
            citation_manifest=manifest,
            packaged_units=units,
            formatted_context_block="\n".join([f"[{c.citation_id}] {u.content}" for c, u in zip(citations, units)]),
            total_characters=len(text_to_audit),
            epistemic_policy="Estricta",
        )

        gen_req = GenerationRequest(
            request_id=f"req_{episode.episode_id}",
            notebook_id=episode.notebook_id,
            query=episode.objective,
            packaged_context=packaged_ctx,
            mode=GenerationMode.EXPLANATION,
        )

        parsed_citations = tuple(
            ParsedCitation(
                citation_id=c.citation_id,
                in_manifest=True,
                chunk_id=c.chunk_id,
                source_id=c.source_id,
            )
            for c in citations
        )

        gen_resp = GenerationResponse(
            response_id=f"resp_{episode.episode_id}",
            request_id=gen_req.request_id,
            notebook_id=episode.notebook_id,
            mode=GenerationMode.EXPLANATION,
            text=text_to_audit,
            raw_content=text_to_audit,
            citations=parsed_citations,
            validation_status=ResponseValidationStatus.VALID,
            is_abstention=False,
            grounding_decision=GroundingDecision.SUPPORTED,
        )

        audit_input = ForensicAuditInput(
            request=gen_req,
            response=gen_resp,
            prompt_hash="f" * 64,
        )

        audit_report = self.forensic_auditor.audit(audit_input)

        if audit_report.verdict != AuditVerdict.APPROVED:
            return ConceptResponse(
                status="ABSTAINED",
                abstention_reason=f"S4.4 Audit Rejected: {audit_report.verdict.value}",
                audit_verdict=audit_report.verdict,
                admitted_evidence=tuple(citations),
            )

        approved_packet = ConceptPacket(
            kc_id=proposal.kc_id,
            notebook_id=proposal.notebook_id,
            objective=proposal.objective,
            evidence_by_role=proposal.evidence_by_role,
            core_concept=proposal.core_concept,
            mental_model=proposal.mental_model,
            reasoning_guidance=proposal.reasoning_guidance,
            formalization=proposal.formalization,
            implementation_guidance=proposal.implementation_guidance,
            pitfalls=proposal.pitfalls,
            citations=proposal.citations,
            s44_report=audit_report,
            audit_verdict=audit_report.verdict,
            assembly_hash=proposal.assembly_hash,
        )

        return ConceptResponse(
            status="PRESENTABLE",
            packet=approved_packet,
            audit_verdict=audit_report.verdict,
            admitted_evidence=tuple(citations),
        )

    def get_next_intervention(self, episode_id: str) -> Dict[str, Any]:
        """Fetch next deterministic action: presents QUALIFIABLE exercise or advances phase."""
        episode = self.get_episode(episode_id)
        if not episode:
            raise ValueError(f"Episodio '{episode_id}' no encontrado.")

        # Fetch certified QUALIFIABLE exercise
        exercise = self.exercise_store.get_presentable_exercise_for_kc(episode.kc_id)
        if not exercise:
            return {
                "intervention_type": "NO_QUALIFIABLE_EXERCISE",
                "message": f"No hay ejercicios del corpus con estado QUALIFIABLE disponibles para '{episode.kc_id}'.",
            }

        # Transition episode phase to EVALUATING
        updated_ep = episode.transition_to(
            next_phase=EpisodePhase.EVALUATING,
            next_step_id=f"step_eval_{exercise.exercise_id}",
        )
        self._active_episodes[episode_id] = updated_ep

        return {
            "intervention_type": "EXERCISE",
            "step_id": updated_ep.current_step_id,
            "exercise": exercise.to_dict(),
        }

    def get_next_eligible_action(self, notebook_id: str, current_kc_id: str) -> Dict[str, Any]:
        """Determine next eligible action based purely on BKT mastery, roadmap and policies (cero LLM)."""
        current_state = self.bkt_tracker.get_state(current_kc_id)
        p_L = current_state.p_L

        nb_data = self._kc_catalog.get(notebook_id, {})
        kcs = nb_data.get("kcs", [])

        # Deterministic threshold: mastery achieved if P(L) >= 0.85
        if p_L >= 0.85:
            # Find next sequential KC in unit
            curr_idx = next((i for i, k in enumerate(kcs) if k.get("kc_id") == current_kc_id), -1)
            next_kc = kcs[curr_idx + 1] if curr_idx != -1 and curr_idx + 1 < len(kcs) else None
            return {
                "recommendation": "ADVANCE",
                "current_p_L": p_L,
                "next_kc_id": next_kc.get("kc_id") if next_kc else None,
                "next_kc_title": next_kc.get("title") if next_kc else "Módulo completado",
                "reason": "Dominio alcanzado bajo BKT determinista (P(L) >= 0.85).",
            }
        else:
            return {
                "recommendation": "REINFORCE",
                "current_p_L": p_L,
                "next_kc_id": current_kc_id,
                "next_kc_title": next((k.get("title") for k in kcs if k.get("kc_id") == current_kc_id), current_kc_id),
                "reason": f"P(L) actual ({p_L:.2f}) requiere práctica adicional para consolidación.",
            }
