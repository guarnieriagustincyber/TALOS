"""TALOS L3 Authorization Manifest & Effective Source Resolution.

Defines the single source of normative truth for source authorization in TALOS Gate B:
- L3 Manifest (config/l3_authorization_manifest.json): De jure normative authority.
- notebook_sources (SQLite table): De facto installed technical capability / link.
- effective_sources(scope) = notebook_sources(scope) ∩ l3_authorized_sources(scope):
  Operational sources allowed to enter retrieval, expansion, pedagogical context, and prompts.

Fail-Closed Principle: If effective_sources(scope) is empty, retrieval, expansion,
and evidence assembly must return empty sets with zero leakage and no fallback.
"""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

DEFAULT_MANIFEST_PATH = (
    Path(__file__).resolve().parents[3] / "config" / "l3_authorization_manifest.json"
)

# In-memory manifest cache: path -> (mtime, manifest_dict)
_MANIFEST_CACHE: Dict[str, tuple[float, Dict[str, Any]]] = {}


def load_l3_manifest(manifest_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load and parse the authoritative L3 release manifest with fail-closed semantics.

    Args:
        manifest_path: Optional path to manifest file. Defaults to config/l3_authorization_manifest.json.

    Returns:
        Dict representing parsed manifest.

    Raises:
        FileNotFoundError: If manifest does not exist.
        ValueError: If manifest JSON is invalid or missing required keys.
    """
    if manifest_path is not None and isinstance(manifest_path, (str, Path)):
        path = Path(manifest_path)
    else:
        path = DEFAULT_MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Authoritative L3 manifest not found at: {path}")


    mtime = path.stat().st_mtime
    cache_key = str(path.resolve())

    if cache_key in _MANIFEST_CACHE:
        cached_mtime, cached_data = _MANIFEST_CACHE[cache_key]
        if cached_mtime == mtime:
            return cached_data

    try:
        content = path.read_text(encoding="utf-8")
        data = json.loads(content)
    except Exception as err:
        logger.error("Failed to read or parse L3 manifest at %s: %s", path, err)
        raise ValueError(f"Corrupted L3 manifest at {path}: {err}") from err

    if "grants" not in data or not isinstance(data["grants"], list):
        raise ValueError(f"Invalid L3 manifest structure at {path}: missing 'grants' list")

    _MANIFEST_CACHE[cache_key] = (mtime, data)
    return data


def get_l3_authorized_sources(
    notebook_id: str,
    manifest_path: Optional[Path] = None,
) -> Set[str]:
    """Return the set of source_ids with positive AUTHORIZED status for a notebook scope.

    Args:
        notebook_id: Target notebook identifier (e.g. 'fase0-soc', 'fadena-lenguajes').
        manifest_path: Optional path to manifest file.

    Returns:
        Set of authorized source_id strings. Empty set if none authorized (fail-closed).
    """
    try:
        manifest = load_l3_manifest(manifest_path)
    except Exception as err:
        logger.warning(
            "L3 Manifest resolution failed for notebook '%s' (failing closed): %s",
            notebook_id,
            err,
        )
        return set()

    authorized: Set[str] = set()
    for grant in manifest.get("grants", []):
        if (
            grant.get("notebook_id") == notebook_id
            and grant.get("status") == "AUTHORIZED"
        ):
            sid = grant.get("source_id")
            if sid:
                authorized.add(sid)

    return authorized


def get_effective_sources(
    store: Any,
    notebook_id: str,
    global_folder_id: Optional[str] = None,
    manifest_path: Optional[Path] = None,
) -> Set[str]:
    """Compute the operational source allowlist: notebook_sources ∩ L3_authorized_sources.

    Args:
        store: KnowledgeStore or object with engine.transaction() providing notebook_sources.
        notebook_id: Target notebook identifier or '__global__'.
        global_folder_id: Folder scope if notebook_id == '__global__'.
        manifest_path: Optional path to manifest file.

    Returns:
        Effective operational source allowlist. Strict fail-closed (returns set() if either side is empty).
    """
    from study_engine.contracts.notebook import GLOBAL_SCOPE_ID

    if notebook_id == GLOBAL_SCOPE_ID:
        # Global retrieval resolves all notebooks under folder
        if not global_folder_id:
            logger.warning("Global retrieval requested without global_folder_id; failing closed")
            return set()
        # Query notebooks under folder
        with store.engine.transaction() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM notebooks WHERE folder_id = ? ORDER BY id;",
                (global_folder_id,),
            )
            notebook_ids = [row[0] for row in cur.fetchall()]
    else:
        notebook_ids = [notebook_id]

    if not notebook_ids:
        return set()

    # 1. Technical capacity from SQLite
    placeholders = ", ".join("?" for _ in notebook_ids)
    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT DISTINCT source_id FROM notebook_sources WHERE notebook_id IN ({placeholders});",
            tuple(notebook_ids),
        )
        technical_sources = {row[0] for row in cursor.fetchall()}

    if not technical_sources:
        return set()

    # 2. De jure normative authority from L3 manifest
    l3_authorized: Set[str] = set()
    for nb_id in notebook_ids:
        l3_authorized.update(get_l3_authorized_sources(nb_id, manifest_path=manifest_path))

    if not l3_authorized:
        return set()

    # 3. Effective operational sources = technical ∩ normative
    return technical_sources.intersection(l3_authorized)
