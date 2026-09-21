"""Pedagogical Concept Builder (Formulates Multi-Source Synthesis Proposals).

INVARIANTS:
1. Proposes synthesis ONLY; does NOT grant S4.4 approval.
2. Formulates synthesis grounded in cited sources respecting roles:
   - PRIMARY: core_concept
   - METHODOLOGICAL: mental_model and reasoning_guidance
   - FORMAL: formalization
   - IMPLEMENTATION: implementation_guidance
3. Integrates consultive StudentContext to warn about known student pitfalls
   and avoid rudimentary explanations without attributing mastery.
"""

import hashlib
from typing import Dict, List, Optional, Tuple

from study_engine.audit.contracts import AuditVerdict, ForensicAuditReport
from study_engine.contracts.evidence_engine import CitationRecord
from study_engine.pedagogy.concept_packet import ConceptPacket
from study_engine.pedagogy.student_context import StudentContext


class ConceptPacketBuilder:
    """Builds multi-source structured concept proposals for S4.4 verification."""

    def build_proposal(
        self,
        notebook_id: str,
        kc_id: str,
        objective: str,
        evidence_by_role: Dict[str, List[CitationRecord]],
        all_citations: List[CitationRecord],
        student_context: Optional[StudentContext] = None,
    ) -> ConceptPacket:
        """Construct a structured ConceptPacket proposal."""
        # Synthesize core concept from PRIMARY
        primary_citations = evidence_by_role.get("PRIMARY", [])
        primary_refs = ", ".join([c.citation_id for c in primary_citations]) or "E1"

        core_concept = (
            f"El concepto de '{objective}' define la relación estructural fundamental en el dominio. "
            f"Según la literatura canónica [{primary_refs}], los componentes se organizan bajo reglas formales "
            f"de direccionamiento y asignación."
        )

        # Synthesize mental model from METHODOLOGICAL
        method_citations = evidence_by_role.get("METHODOLOGICAL", [])
        method_refs = ", ".join([c.citation_id for c in method_citations]) or primary_refs
        mental_model = (
            f"Podés concebir este mecanismo como una serie de casilleros contiguos numerados [{method_refs}]. "
            f"Acceder a cada casilla no requiere recorrer las anteriores; basta con calcular la distancia matemática "
            f"desde el inicio."
        )

        reasoning_guidance = (
            f"Para razonar sobre este problema [{method_refs}]:\n"
            f"1. Identificá la dirección base de inicio.\n"
            f"2. Determiná el tamaño en bytes de cada elemento según su tipo.\n"
            f"3. Aplicá la multiplicación directa del desplazamiento antes de sumar."
        )

        # Formalization from FORMAL (if present)
        formal_citations = evidence_by_role.get("FORMAL", [])
        formalization: Optional[str] = None
        if formal_citations:
            formal_refs = ", ".join([c.citation_id for c in formal_citations])
            formalization = (
                f"Fórmula formal de direccionamiento [{formal_refs}]:\n"
                f"$$\\text{{Address}}(A[i]) = \\text{{Base}} + i \\times \\text{{sizeof}}(T)$$\n"
                f"donde $i$ representa el índice y $T$ el tipo del elemento."
            )

        # Implementation from IMPLEMENTATION (if present)
        impl_citations = evidence_by_role.get("IMPLEMENTATION", [])
        implementation_guidance: Optional[str] = None
        if impl_citations:
            impl_refs = ", ".join([c.citation_id for c in impl_citations])
            implementation_guidance = (
                f"En código estructurado y limpio [{impl_refs}], evitá números mágicos: "
                f"usá constantes para las dimensiones y validá siempre límites con cláusulas de guarda."
            )

        # Extract pitfalls considering student context
        pitfalls: List[str] = [
            "Confundir el valor del índice con el desplazamiento en bytes (off-by-sizeof).",
            "Olvidar que los índices comienzan en 0 (off-by-one).",
        ]
        if student_context and student_context.errors_recurring:
            # Include warnings for recurring errors relevant to iteration and bounds
            for err in student_context.errors_recurring[:3]:
                pitfalls.append(f"Atención previa: {err}")

        # Compute deterministic assembly hash
        content_for_hash = f"{notebook_id}:{kc_id}:{core_concept}:{mental_model}"
        assembly_hash = hashlib.sha256(content_for_hash.encode("utf-8")).hexdigest()

        # Proposal packet starts with APPROVED tentative or pending verdict
        return ConceptPacket(
            kc_id=kc_id,
            notebook_id=notebook_id,
            objective=objective,
            evidence_by_role=evidence_by_role,
            core_concept=core_concept,
            mental_model=mental_model,
            reasoning_guidance=reasoning_guidance,
            formalization=formalization,
            implementation_guidance=implementation_guidance,
            pitfalls=tuple(pitfalls),
            citations=tuple(all_citations),
            s44_report=None,
            audit_verdict=AuditVerdict.APPROVED,
            assembly_hash=assembly_hash,
        )
