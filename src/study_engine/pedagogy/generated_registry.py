"""Registro y oráculo de ejercicios GENERADOS (Fase 6).

Los ejercicios sintetizados por Tipo 1 (multi-KC), Tipo 2 (debugging) y
Tipo 3 (trace) NO viven en el ExerciseStore certificado (ese queda intacto,
fail-closed a fuentes verificadas por humanos). Viven en su propia tabla
`generated_exercises` dentro de student_state.db:

- Cada ejercicio lleva `source='generated'` y un `oracle` estructurado que
  garantiza la calificación determinista sin LLM ni certificación humana.
- El grader de generados es `GeneratedOracleGrader` (nuevo; NO toca los
  graders existentes de MC/ExactMatch).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import re
import unicodedata
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DDL = """
CREATE TABLE IF NOT EXISTS generated_exercises (
    exercise_id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    kc_ids_json TEXT NOT NULL,
    prompt TEXT NOT NULL,
    oracle_json TEXT NOT NULL,
    difficulty TEXT,
    source TEXT NOT NULL DEFAULT 'generated',
    created_at TEXT NOT NULL
);
"""


def _normalize(text: str) -> str:
    """Normalización liviana para matching de respuestas determinista."""
    t = unicodedata.normalize("NFKD", text.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", t).strip()


class GeneratedOracleGrader:
    """Grader determinista para ejercicios generados.

    Tipos de oráculo:
    - keyword_coverage (Tipo 1): la respuesta debe cubrir >= umbral de los
      conceptos obligatorios (cada uno con sinonimos aceptables).
    - bug_class (Tipo 2): la respuesta debe nombrar la clase de bug (CWE o
      alguno de sus alias normalizados).
    - state_match (Tipo 3): la respuesta debe predecir exactamente el estado
      final de las variables observadas (valores simbólicos para direcciones).
    """

    def grade(self, user_answer: str, oracle: Dict[str, Any]) -> Dict[str, Any]:
        kind = oracle.get("type")
        normalized = _normalize(user_answer or "")

        if kind == "keyword_coverage":
            required: List[Dict[str, Any]] = oracle.get("required", [])
            coverage: List[str] = []
            for req in required:
                if any(_normalize(a) in normalized for a in req.get("accept", [])):
                    coverage.append(req["name"])
            threshold = float(oracle.get("min_coverage", 0.8))
            is_correct = (len(coverage) / max(len(required), 1)) >= threshold
            return {
                "is_correct": is_correct,
                "covered": coverage,
                "missing": [r["name"] for r in required if r["name"] not in coverage],
            }

        if kind == "bug_class":
            accept = [_normalize(a) for a in oracle.get("accept", [])]
            is_correct = any(a in normalized for a in accept)
            return {
                "is_correct": is_correct,
                "expected_class": oracle.get("cwe"),
                "matched_alias": next((a for a in accept if a in normalized), None),
            }

        if kind == "state_match":
            final_state: Dict[str, Any] = oracle.get("final_state", {})
            symbolic = set(oracle.get("symbolic_fields", []))
            wrong: List[str] = []
            compact = normalized.replace(" ", "")
            for var, expected in final_state.items():
                if var in symbolic:
                    # Campos simbólicos (direcciones/alias): no exigibles por
                    # comparación de texto — quedan fuera del veredicto.
                    continue
                expected_str = _normalize(str(expected))
                var_id = _normalize(str(var))
                patterns = [f"{var_id}={expected_str}", f"{var_id}:{expected_str}"]
                if isinstance(expected, int):
                    hex_str = hex(expected).lower()
                    patterns.extend([f"{var_id}={hex_str}", f"{var_id}:{hex_str}"])
                    if expected in (0, 1):
                        tf_str = "true" if expected == 1 else "false"
                        patterns.extend([f"{var_id}={tf_str}", f"{var_id}:{tf_str}"])
                if not any(p in compact for p in patterns):
                    wrong.append(var)
            return {
                "is_correct": not wrong,
                "expected": final_state,
                "wrong_fields": wrong,
            }

        raise ValueError(f"Tipo de oráculo desconocido: {kind}")


class GeneratedExerciseRegistry:
    """Persistencia de ejercicios generados en student_state.db."""

    def __init__(self, storage: Any) -> None:
        self.storage = storage
        conn = self.storage._get_connection()
        conn.execute(DDL)
        conn.commit()

    def save(self, exercise: Dict[str, Any]) -> str:
        now = datetime.now(timezone.utc).isoformat()
        conn = self.storage._get_connection()
        with conn:
            conn.execute(
                """
                INSERT INTO generated_exercises
                    (exercise_id, kind, kc_ids_json, prompt, oracle_json, difficulty, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 'generated', ?)
                ON CONFLICT(exercise_id) DO UPDATE SET
                    prompt = excluded.prompt,
                    oracle_json = excluded.oracle_json,
                    difficulty = excluded.difficulty;
                """,
                (
                    exercise["exercise_id"],
                    exercise["kind"],
                    json.dumps(exercise["kc_ids"]),
                    exercise["prompt"],
                    json.dumps(exercise["oracle"], ensure_ascii=False),
                    exercise.get("difficulty"),
                    now,
                ),
            )
        return exercise["exercise_id"]

    def get(self, exercise_id: str) -> Optional[Dict[str, Any]]:
        conn = self.storage._get_connection()
        row = conn.execute(
            "SELECT exercise_id, kind, kc_ids_json, prompt, oracle_json, difficulty, created_at "
            "FROM generated_exercises WHERE exercise_id = ?;",
            (exercise_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "exercise_id": row[0],
            "kind": row[1],
            "kc_ids": json.loads(row[2]),
            "prompt": row[3],
            "oracle": json.loads(row[4]),
            "difficulty": row[5],
            "source": "generated",
            "created_at": row[6],
        }

    def list_for_kc(self, kc_id: str) -> List[Dict[str, Any]]:
        conn = self.storage._get_connection()
        rows = conn.execute(
            "SELECT exercise_id FROM generated_exercises WHERE kc_ids_json LIKE ?;",
            (f'%"{kc_id}"%',),
        ).fetchall()
        out: List[Dict[str, Any]] = []
        for (ex_id,) in rows:
            rec = self.get(ex_id)
            if rec is not None:
                out.append(rec)
        return out
