"""Exercise Store managing certified and unverified exercise candidates.

INVARIANTS:
1. Fail-closed: get_presentable_exercise_for_kc() returns ONLY QUALIFIABLE items.
2. If only UNVERIFIED items exist for a KC, it returns None.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional

from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)


class ExerciseStore:
    """Storage and registry for verified and candidate exercises."""

    def __init__(self, storage_path: Optional[Path] = None) -> None:
        self.storage_path = storage_path or (
            Path(__file__).resolve().parents[3]
            / "data"
            / "pedagogy"
            / "exercises"
            / "qualifiable_exercises.json"
        )
        self._exercises: Dict[str, ExerciseCandidate] = {}
        self._load()

    def _load(self) -> None:
        if not self.storage_path.exists():
            return
        try:
            raw_data = json.loads(self.storage_path.read_text(encoding="utf-8"))
            for item in raw_data:
                cand = ExerciseCandidate(
                    exercise_id=item["exercise_id"],
                    source_id=item["source_id"],
                    source_location=item["source_location"],
                    source_hash=item["source_hash"],
                    extractor_version=item["extractor_version"],
                    extraction_method=item["extraction_method"],
                    verification_status=ExerciseVerificationStatus(item["verification_status"]),
                    verified_by=item.get("verified_by"),
                    verification_timestamp=(
                        datetime.fromisoformat(item["verification_timestamp"].replace("Z", "+00:00"))
                        if item.get("verification_timestamp")
                        else None
                    ),
                    content_hash=item["content_hash"],
                    kc_id=item["kc_id"],
                    prompt=item["prompt"],
                    exercise_type=ExerciseType(item["exercise_type"]),
                    options=tuple(item["options"]) if item.get("options") else None,
                    expected_answer=item.get("expected_answer", ""),
                    solution_explanation=item.get("solution_explanation"),
                )
                self._exercises[cand.exercise_id] = cand
        except Exception:
            pass

    def get_presentable_exercise_for_kc(self, kc_id: str) -> Optional[ExerciseCandidate]:
        """Fetch the first certified QUALIFIABLE exercise for the KC."""
        for ex in self._exercises.values():
            if ex.kc_id == kc_id and ex.is_presentable():
                return ex
        return None

    def get_exercises_for_kc(self, kc_id: str) -> List[ExerciseCandidate]:
        """Fetch all exercises matching a given KC."""
        return [ex for ex in self._exercises.values() if ex.kc_id == kc_id]

    def get_covered_kcs(self) -> set[str]:
        """Return the set of unique KC identifiers covered by qualifiable exercises."""
        return {ex.kc_id for ex in self._exercises.values() if ex.is_presentable()}

    def get_exercise_by_id(self, exercise_id: str) -> Optional[ExerciseCandidate]:
        """Fetch exercise by ID."""
        return self._exercises.get(exercise_id)

    def add_exercise(self, candidate: ExerciseCandidate, persist: bool = True) -> bool:
        """Register an exercise candidate and optionally persist to disk."""
        self._exercises[candidate.exercise_id] = candidate
        if persist:
            try:
                self.storage_path.parent.mkdir(parents=True, exist_ok=True)
                serialized = [ex.to_dict() for ex in self._exercises.values()]
                self.storage_path.write_text(json.dumps(serialized, indent=2, ensure_ascii=False), encoding="utf-8")
                return True
            except Exception:
                return False
        return True

    def list_all(self) -> List[ExerciseCandidate]:
        """List all stored exercise candidates."""
        return list(self._exercises.values())

