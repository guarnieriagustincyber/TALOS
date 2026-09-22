"""Administración manual de Knowledge Components (Fase 5.1).

Los KCs viven en dos fuentes: el catálogo canónico JSON
(``config/notebook_kc_catalog.json``, versionado) y la tabla
``notebook_kcs`` (agregados manuales del usuario). Este módulo:

- Persiste KCs manuales en knowledge_store.db (tabla notebook_kcs).
- Funde ambas fuentes para que el orquestador pedagógico, el matcher de
  chat y el motor BKT vean el syllabus completo.

Contrato de fusión: el JSON es base; los KCs de DB se agregan al final.
Un kc_id existente en JSON nunca se pisa por uno manual (duplicado = 409).
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

KC_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,62}$")
VALID_DIFFICULTIES = {"basico", "intermedio", "avanzado"}


class DuplicateKCError(ValueError):
    """El kc_id ya existe en el catálogo efectivo del notebook (JSON o DB)."""


class KCAdminStore:
    """CRUD de Knowledge Components manuales sobre el engine de knowledge_store."""

    def __init__(self, engine: Any) -> None:
        self.engine = engine

    # ------------------------------------------------------------------ reads

    def list_manual_kcs(self, notebook_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lista KCs manuales (todos o filtrados por notebook)."""
        sql = (
            "SELECT notebook_id, kc_id, title, prerequisites_json, subtopics_json,"
            " estimated_time_min, difficulty, origin, created_at FROM notebook_kcs"
        )
        params: tuple = ()
        if notebook_id is not None:
            sql += " WHERE notebook_id = ?"
            params = (notebook_id,)
        sql += " ORDER BY notebook_id, kc_id;"
        with self.engine.transaction() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [
            {
                "kc_id": r[1],
                "title": r[2],
                "prerequisites": json.loads(r[3]),
                "subtopics": json.loads(r[4]),
                "estimated_time": r[5],
                "difficulty": r[6],
                "origin": r[7],
                "created_at": r[8],
                "notebook_id": r[0],
            }
            for r in rows
        ]

    def catalog_dump(self) -> Dict[str, List[Dict[str, Any]]]:
        """Todos los KCs manuales agrupados por notebook (para fundamentar el merge)."""
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for kc in self.list_manual_kcs():
            grouped.setdefault(kc["notebook_id"], []).append(
                {k: v for k, v in kc.items() if k != "notebook_id"}
            )
        return grouped

    # ------------------------------------------------------------------ writes

    def add_kc(
        self,
        notebook_id: str,
        kc_id: str,
        title: str,
        prerequisites: Optional[List[str]] = None,
        subtopics: Optional[List[str]] = None,
        estimated_time: Optional[int] = None,
        difficulty: Optional[str] = None,
        existing_kcs: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Inserta un KC manual. Levanta DuplicateKCError si ya existe."""
        kc_id = kc_id.strip()
        if not KC_ID_RE.match(kc_id):
            raise ValueError(
                f"kc_id inválido '{kc_id}': minúsculas, dígitos, guiones (3-64 chars)."
            )
        title = (title or "").strip()
        if not title:
            raise ValueError("title es obligatorio.")
        if difficulty is not None and difficulty not in VALID_DIFFICULTIES:
            raise ValueError(f"difficulty debe ser una de {sorted(VALID_DIFFICULTIES)}")

        if existing_kcs is not None and any(k.get("kc_id") == kc_id for k in existing_kcs):
            raise DuplicateKCError(f"kc_id '{kc_id}' ya existe en el notebook '{notebook_id}'.")

        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.engine.transaction() as conn:
                conn.execute(
                    """
                    INSERT INTO notebook_kcs (
                        notebook_id, kc_id, title, prerequisites_json, subtopics_json,
                        estimated_time_min, difficulty, origin, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'manual', ?);
                    """,
                    (
                        notebook_id, kc_id, title,
                        json.dumps(prerequisites or []),
                        json.dumps(subtopics or []),
                        estimated_time, difficulty, now,
                    ),
                )
        except Exception as exc:
            # PK compuesta (notebook_id, kc_id): doble POST -> 409 semántico
            if "UNIQUE" in str(exc).upper() or "PRIMARY KEY" in str(exc).upper():
                raise DuplicateKCError(
                    f"kc_id '{kc_id}' ya existe en el notebook '{notebook_id}'."
                ) from exc
            raise
        return {
            "kc_id": kc_id,
            "title": title,
            "prerequisites": prerequisites or [],
            "subtopics": subtopics or [],
            "estimated_time": estimated_time,
            "difficulty": difficulty,
            "origin": "manual",
            "created_at": now,
        }


def merge_manual_kcs(catalog: Dict[str, Any], db_kcs: Dict[str, List[Dict[str, Any]]]) -> None:
    """Funde KCs manuales (DB) dentro del catálogo in-place.

    No pisa entradas del JSON canónico; los duplicados se previenen en el
    endpoint (la DB es append-only por PK). Idempotente: si un kc_id ya está
    presente, no se agrega otra vez.
    """
    for notebook_id, kcs in db_kcs.items():
        entry = catalog.setdefault(notebook_id, {"kcs": []})
        if not isinstance(entry.get("kcs"), list):
            entry["kcs"] = []
        present = {k.get("kc_id") for k in entry["kcs"]}
        for kc in kcs:
            if kc["kc_id"] not in present:
                entry["kcs"].append(kc)
                present.add(kc["kc_id"])
