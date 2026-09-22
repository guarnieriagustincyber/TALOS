"""Session Digest — Memoria de Esencia (perfil cognitivo entre sesiones).

Genera y persiste un resumen estructurado (JSON, nunca texto libre de LLM)
de la sesión de estudio: qué KCs se dominaron, cuáles activaron lucha y el
nivel de fricción. La próxima sesión lo inyecta en el prompt de TALOS.

Determinista: se construye SOLO de observaciones certificadas (evaluaciones
con grader + StruggleTracker). Nada de inferencia libre.

Contrato de la tabla (student_state.db):
    session_digests(student_id, session_id, digest_json, updated_at)
        PRIMARY KEY (student_id, session_id)

Reglas de clasificación de KC en el digest:
- struggled_kcs: >=2 errores en la sesión O el StruggleTracker llegó al umbral.
- mastered_kcs: >=2 aciertos y 0 errores en la sesión.
- friction_level: high si hay struggled_kcs; medium si hay errores sueltos; low si no.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS session_digests (
    student_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    digest_json TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (student_id, session_id)
);
"""

# Actividad cruda por KC dentro de la sesión (se acumula incrementalmente).
_ACTIVITY_DDL = """
CREATE TABLE IF NOT EXISTS session_kc_activity (
    student_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    kc_id TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    errors INTEGER NOT NULL DEFAULT 0,
    corrects INTEGER NOT NULL DEFAULT 0,
    struggled INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (student_id, session_id, kc_id)
);
"""


def _conn(storage: Any):
    """Conexión del StudentStorage (mismo patrón que chat.py usa)."""
    conn = storage._get_connection()
    conn.execute(_DDL)
    conn.execute(_ACTIVITY_DDL)
    conn.commit()
    return conn


def record_kc_attempt(
    storage: Any,
    student_id: str,
    session_id: str,
    kc_id: str,
    correct: bool,
    struggled: bool = False,
) -> None:
    """Registra un intento evaluado en la actividad de sesión (idempotente por UPDATE incremental)."""
    if not kc_id:
        return
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn(storage)
    with conn:
        conn.execute(
            """
            INSERT INTO session_kc_activity
                (student_id, session_id, kc_id, attempts, errors, corrects, struggled, updated_at)
            VALUES (?, ?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(student_id, session_id, kc_id) DO UPDATE SET
                attempts  = session_kc_activity.attempts + 1,
                errors    = session_kc_activity.errors + excluded.errors,
                corrects  = session_kc_activity.corrects + excluded.corrects,
                struggled = MAX(session_kc_activity.struggled, excluded.struggled),
                updated_at = excluded.updated_at;
            """,
            (student_id, session_id, kc_id,
             0 if correct else 1,
             1 if correct else 0,
             1 if struggled else 0,
             now),
        )

    # Regenerar y persistir el digest acumulado de la sesión
    digest = generate_session_digest(student_id, session_id, storage)
    save_digest(storage, student_id, session_id, digest)


def generate_session_digest(
    student_id: str,
    session_id: str,
    storage: Any,
) -> Dict[str, Any]:
    """Construye el digest estructurado desde la actividad KC de la sesión."""
    conn = _conn(storage)
    rows = conn.execute(
        """
        SELECT kc_id, attempts, errors, corrects, struggled
        FROM session_kc_activity
        WHERE student_id = ? AND session_id = ?;
        """,
        (student_id, session_id),
    ).fetchall()

    struggled_kcs: List[str] = []
    mastered_kcs: List[str] = []
    total_errors = 0
    for kc_id, attempts, errors, corrects, struggled in rows:
        if struggled or errors >= 2:
            struggled_kcs.append(kc_id)
        elif corrects >= 2 and errors == 0:
            mastered_kcs.append(kc_id)
        total_errors += errors

    if struggled_kcs:
        friction = "high"
    elif total_errors > 0:
        friction = "medium"
    else:
        friction = "low"

    return {
        "struggled_kcs": struggled_kcs,
        "mastered_kcs": mastered_kcs,
        "friction_level": friction,
        "kc_activity": {
            r[0]: {"attempts": r[1], "errors": r[2], "corrects": r[3], "struggled": bool(r[4])}
            for r in rows
        },
    }


def save_digest(storage: Any, student_id: str, session_id: str, digest: Dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    conn = _conn(storage)
    with conn:
        conn.execute(
            """
            INSERT INTO session_digests (student_id, session_id, digest_json, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(student_id, session_id) DO UPDATE SET
                digest_json = excluded.digest_json,
                updated_at = excluded.updated_at;
            """,
            (student_id, session_id, json.dumps(digest, ensure_ascii=False), now),
        )


def get_latest_digest(storage: Any, student_id: str) -> Optional[Dict[str, Any]]:
    """Último digest guardado del estudiante (de la sesión más reciente)."""
    try:
        conn = _conn(storage)
        row = conn.execute(
            """
            SELECT digest_json FROM session_digests
            WHERE student_id = ?
            ORDER BY updated_at DESC LIMIT 1;
            """,
            (student_id,),
        ).fetchone()
    except Exception as exc:
        logger.debug("No se pudo leer digest previo: %s", exc)
        return None
    if not row:
        return None
    try:
        return json.loads(row[0])
    except json.JSONDecodeError:
        return None


def digest_directive(digest: Dict[str, Any]) -> str:
    """Directiva de prompt a partir del digest de la sesión anterior."""
    if not digest or (not digest.get("struggled_kcs") and not digest.get("mastered_kcs")):
        return ""
    return (
        "=== RESUMEN DE SESIÓN ANTERIOR (adaptá tu estrategia) ===\n"
        f"{json.dumps(digest, ensure_ascii=False)}\n"
        "Si el usuario pregunta sobre un KC en 'struggled_kcs', empezá con una "
        "analogía simple y evitá la capa de silicio inicialmente. "
        "Si pregunta sobre un KC en 'mastered_kcs', andá directo al código o desafío."
    )
