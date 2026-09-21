"""Exercise Generator and S4.4 Integrity Verifier for Subsystem E3 / S4.

Responsible for generating candidate exercises from verified corpus chunks,
auditing them against S4.4 provenance invariants, and certifying them
as QUALIFIABLE when strictly deterministic.
"""

from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader


class ExerciseGenerator:
    """Generates and validates certified pedagogical exercises anchored in source chunks."""

    def __init__(self, verifier_identity: str = "TALOS-S4.4-ForensicVerifier-v2") -> None:
        self.verifier_identity = verifier_identity
        self.mc_grader = MultiChoiceGrader()
        self.exact_grader = ExactMatchGrader()

    def compute_content_hash(
        self,
        kc_id: str,
        prompt: str,
        expected_answer: str,
        exercise_type: ExerciseType,
        options: Optional[Sequence[str]] = None,
    ) -> str:
        """Compute SHA256 hash across exercise prompt, options, and expected answer."""
        opt_str = "|".join(options) if options else ""
        raw = f"{kc_id.strip()}::{prompt.strip()}::{exercise_type.value}::{opt_str}::{expected_answer.strip()}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def create_candidate(
        self,
        exercise_id: str,
        source_id: str,
        source_location: str,
        source_hash: str,
        kc_id: str,
        prompt: str,
        exercise_type: ExerciseType,
        expected_answer: str,
        options: Optional[Sequence[str]] = None,
        solution_explanation: Optional[str] = None,
        extraction_method: str = "corpus_grounded_synthesis",
    ) -> ExerciseCandidate:
        """Create a candidate with computed content hash."""
        opt_tuple = tuple(options) if options else None
        c_hash = self.compute_content_hash(
            kc_id=kc_id,
            prompt=prompt,
            expected_answer=expected_answer,
            exercise_type=exercise_type,
            options=opt_tuple,
        )

        return ExerciseCandidate(
            exercise_id=exercise_id,
            source_id=source_id,
            source_location=source_location,
            source_hash=source_hash or hashlib.sha256(source_id.encode("utf-8")).hexdigest(),
            extractor_version="v2.0.0-s44-certified",
            extraction_method=extraction_method,
            verification_status=ExerciseVerificationStatus.UNVERIFIED,
            verified_by=None,
            verification_timestamp=None,
            content_hash=c_hash,
            kc_id=kc_id,
            prompt=prompt,
            exercise_type=exercise_type,
            options=opt_tuple,
            expected_answer=expected_answer.strip(),
            solution_explanation=solution_explanation,
        )

    BANNED_MAD_LIBS_PATTERNS = [
        re.compile(r"¿cuál es el principio conceptual y la garantía formal fundamental", re.IGNORECASE),
        re.compile(r"¿cuál es la estructura de datos o contrato formal que desacopla", re.IGNORECASE),
        re.compile(r"Omitir la validación de límites para maximizar", re.IGNORECASE),
        re.compile(r"Sobrescribir registros de control de forma aleatoria", re.IGNORECASE),
        re.compile(r"Desactivar las interrupciones del hardware permanentemente", re.IGNORECASE),
        re.compile(r"Garantizar la consistencia determinista y la invariante de estado de", re.IGNORECASE),
        re.compile(r"si el parámetro de entrada base es 4 y el factor de escala es 8", re.IGNORECASE),
    ]

    def verify_distractor_quality(self, options: Sequence[str]) -> Tuple[bool, List[str]]:
        """Verify semantic diversity and plausibility of MC distractors (Fix S3.2)."""
        violations: List[str] = []
        if len(options) < 3:
            violations.append("High quality MC requires at least 3 distinct options.")

        cleaned: List[str] = []
        for opt in options:
            for pat in self.BANNED_MAD_LIBS_PATTERNS:
                if pat.search(opt):
                    violations.append(f"Option contains banned boilerplate pattern: '{opt[:40]}...'")

            text = re.sub(r"^[A-D]\.\s*", "", opt.strip()).lower()
            cleaned.append(text)

        if len(set(cleaned)) < len(cleaned):
            violations.append("MC options contain duplicate text.")

        for i in range(len(cleaned)):
            tokens_i = set(cleaned[i].split())
            for j in range(i + 1, len(cleaned)):
                tokens_j = set(cleaned[j].split())
                if tokens_i and tokens_j:
                    jaccard = len(tokens_i & tokens_j) / float(len(tokens_i | tokens_j))
                    if jaccard > 0.70:
                        violations.append(
                            f"Options {i} and {j} are too similar (Jaccard={jaccard:.2f}): '{cleaned[i]}' vs '{cleaned[j]}'"
                        )

        return len(violations) == 0, violations

    def verify_candidate_integrity(
        self,
        candidate: ExerciseCandidate,
        corpus_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[bool, List[str]]:
        """Audit candidate against S4.4 deterministic evaluation invariants and pedagogical quality."""
        violations: List[str] = []

        if not candidate.prompt or len(candidate.prompt.strip()) < 20:
            violations.append("Prompt is too brief or empty (< 20 characters).")

        # Check prompt against banned boilerplate
        for pat in self.BANNED_MAD_LIBS_PATTERNS:
            if pat.search(candidate.prompt):
                violations.append(f"Prompt contains banned mad-libs boilerplate: '{candidate.prompt[:50]}...'")

        if not candidate.expected_answer or not candidate.expected_answer.strip():
            violations.append("Expected answer cannot be empty.")

        if not candidate.kc_id or not candidate.kc_id.strip():
            violations.append("KC id cannot be empty.")

        if not candidate.source_id or not candidate.source_id.strip():
            violations.append("Source id cannot be empty.")

        # Re-verify hash integrity
        recomputed = self.compute_content_hash(
            kc_id=candidate.kc_id,
            prompt=candidate.prompt,
            expected_answer=candidate.expected_answer,
            exercise_type=candidate.exercise_type,
            options=candidate.options,
        )
        if recomputed != candidate.content_hash:
            violations.append(f"Content hash divergence: {recomputed} != {candidate.content_hash}")

        # Verification of format specific constraints
        if candidate.exercise_type == ExerciseType.MC:
            if not candidate.options or len(candidate.options) < 2:
                violations.append("MC exercise requires at least 2 distinct options.")
            else:
                is_dist_valid, dist_viols = self.verify_distractor_quality(candidate.options)
                if not is_dist_valid:
                    violations.extend(dist_viols)

                opt_keys = []
                for opt in candidate.options:
                    m = re.match(r"^([A-D])\.", opt.strip())
                    if m:
                        opt_keys.append(m.group(1))
                if opt_keys:
                    if candidate.expected_answer.upper() not in opt_keys and candidate.expected_answer not in candidate.options:
                        violations.append(f"Expected answer '{candidate.expected_answer}' not among MC option keys {opt_keys}.")
        elif candidate.exercise_type == ExerciseType.NUMERIC:
            try:
                float(candidate.expected_answer.replace(",", "."))
            except ValueError:
                violations.append(f"NUMERIC answer '{candidate.expected_answer}' cannot be parsed as a real number.")
        elif candidate.exercise_type == ExerciseType.EXACT_TEXT:
            if len(candidate.expected_answer.strip()) < 2:
                violations.append("EXACT_TEXT answer must be at least 2 characters long.")

        # Verification against grounding chunks if supplied
        if corpus_chunks is not None and len(corpus_chunks) > 0:
            candidate_src = candidate.source_id.lower()
            chunk_sources = [c.get("source_id", "").lower() for c in corpus_chunks]
            if candidate_src not in chunk_sources:
                violations.append(f"Candidate source_id '{candidate.source_id}' is absent from provided corpus chunks.")

        is_valid = len(violations) == 0
        return is_valid, violations

    def certify_candidate(
        self,
        candidate: ExerciseCandidate,
        corpus_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> Optional[ExerciseCandidate]:
        """Verify candidate and promote to QUALIFIABLE if 100% compliant with S4.4."""
        is_valid, violations = self.verify_candidate_integrity(candidate, corpus_chunks)
        if not is_valid:
            return None

        return ExerciseCandidate(
            exercise_id=candidate.exercise_id,
            source_id=candidate.source_id,
            source_location=candidate.source_location,
            source_hash=candidate.source_hash,
            extractor_version=candidate.extractor_version,
            extraction_method=candidate.extraction_method,
            verification_status=ExerciseVerificationStatus.QUALIFIABLE,
            verified_by=self.verifier_identity,
            verification_timestamp=datetime.now(timezone.utc),
            content_hash=candidate.content_hash,
            kc_id=candidate.kc_id,
            prompt=candidate.prompt,
            exercise_type=candidate.exercise_type,
            options=candidate.options,
            expected_answer=candidate.expected_answer,
            solution_explanation=candidate.solution_explanation,
        )
