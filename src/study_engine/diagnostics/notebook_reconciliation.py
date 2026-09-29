"""Read-only reconciliation of notebook identities and source associations."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Set

LEGACY_SCOPE_IDS = {"fadena-prog", "fadena-so"}


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read valid JSON from {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object in {path}")
    return value


def _read_only_connection(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise ValueError(f"Knowledge database does not exist: {path}")
    connection = sqlite3.connect(f"{path.resolve().as_uri()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> Set[str]:
    return {row[1] for row in connection.execute(f"PRAGMA table_info({table})")}


def _require_columns(
    connection: sqlite3.Connection, table: str, required: Iterable[str]
) -> None:
    available = _table_columns(connection, table)
    missing = sorted(set(required) - available)
    if missing:
        raise ValueError(
            f"Knowledge database table {table!r} is missing columns: {', '.join(missing)}"
        )


def _parse_roles(
    raw: Mapping[str, Any], notebook_id: str, path: Path
) -> Dict[str, Dict[str, Any]]:
    notebook_roles = raw.get(notebook_id, {})
    if not isinstance(notebook_roles, dict):
        raise ValueError(
            f"Expected source-role object for notebook {notebook_id!r} in {path}"
        )

    source_roles: Dict[str, Dict[str, Any]] = {}
    for source_id, entry in notebook_roles.items():
        if not isinstance(source_id, str) or not source_id.strip():
            raise ValueError(f"Invalid source ID in role catalog for {notebook_id!r}")
        if not isinstance(entry, dict) or not isinstance(entry.get("roles"), list):
            raise ValueError(
                f"Expected a roles list for source {source_id!r} in notebook {notebook_id!r}"
            )
        if not all(isinstance(role, str) and role.strip() for role in entry["roles"]):
            raise ValueError(
                f"Invalid role value for source {source_id!r} in notebook {notebook_id!r}"
            )
        details = {
            key: entry[key]
            for key in ("title", "status", "authority", "note")
            if key in entry
        }
        details["roles"] = sorted(set(entry["roles"]))
        source_roles[source_id] = details
    return source_roles


def reconcile_notebooks(
    knowledge_db: Path,
    curriculum_catalog: Path,
    source_roles: Path,
    declared_notebooks: Iterable[Any],
    identity_decisions: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare declarations and persisted associations without writing to SQLite."""
    knowledge_db = Path(knowledge_db)
    curriculum_catalog = Path(curriculum_catalog)
    source_roles = Path(source_roles)
    catalog = _read_json(curriculum_catalog)
    roles = _read_json(source_roles)
    decisions_raw = (
        _read_json(Path(identity_decisions)) if identity_decisions is not None else {}
    )
    decisions = decisions_raw.get("decisions", {})
    if not isinstance(decisions, dict):
        raise ValueError("Identity decisions must contain a 'decisions' object")
    for notebook_id, decision in decisions.items():
        if (
            not isinstance(notebook_id, str)
            or not notebook_id.strip()
            or not isinstance(decision, dict)
            or not isinstance(decision.get("classification"), str)
            or not isinstance(decision.get("decision"), str)
            or not isinstance(decision.get("evidence"), list)
            or not all(isinstance(item, str) for item in decision["evidence"])
        ):
            raise ValueError(f"Invalid identity decision for {notebook_id!r}")

    registry: Dict[str, Any] = {}
    for notebook in declared_notebooks:
        notebook_id = getattr(notebook, "notebook_id", None)
        if not isinstance(notebook_id, str) or not notebook_id.strip():
            raise ValueError("Declared notebooks must have a non-empty notebook_id")
        if notebook_id in registry:
            raise ValueError(f"Duplicate notebook ID in registry: {notebook_id}")
        registry[notebook_id] = notebook

    for notebook_id, entry in catalog.items():
        if (
            not isinstance(notebook_id, str)
            or not notebook_id.strip()
            or not isinstance(entry, dict)
        ):
            raise ValueError(
                f"Invalid notebook entry in curriculum catalog: {notebook_id!r}"
            )
        if "curriculum_id" in entry and not isinstance(entry["curriculum_id"], str):
            raise ValueError(f"Invalid curriculum_id for notebook {notebook_id!r}")
    for notebook_id, entry in roles.items():
        if (
            not isinstance(notebook_id, str)
            or not notebook_id.strip()
            or not isinstance(entry, dict)
        ):
            raise ValueError(
                f"Invalid notebook entry in source-role catalog: {notebook_id!r}"
            )

    connection = _read_only_connection(knowledge_db)
    try:
        _require_columns(
            connection,
            "notebooks",
            ("id", "name", "description", "subject", "curriculum_id"),
        )
        _require_columns(
            connection,
            "sources",
            ("source_id", "title", "sha256", "subject", "course"),
        )
        _require_columns(connection, "notebook_sources", ("notebook_id", "source_id"))

        persisted_notebooks = {
            row["id"]: dict(row)
            for row in connection.execute(
                "SELECT id, name, description, subject, curriculum_id "
                "FROM notebooks ORDER BY id"
            ).fetchall()
        }
        source_records = {
            row["source_id"]: {
                "title": row["title"],
                "sha256": row["sha256"],
                "subject": row["subject"],
                "course": row["course"],
            }
            for row in connection.execute(
                "SELECT source_id, title, sha256, subject, course "
                "FROM sources ORDER BY source_id"
            ).fetchall()
        }
        persisted_associations: Dict[str, Set[str]] = {}
        for notebook_id, source_id in connection.execute(
            "SELECT notebook_id, source_id FROM notebook_sources "
            "ORDER BY notebook_id, source_id"
        ):
            persisted_associations.setdefault(notebook_id, set()).add(source_id)
    finally:
        connection.close()

    notebook_ids = sorted(
        set(registry)
        | set(catalog)
        | set(roles)
        | set(persisted_notebooks)
        | set(persisted_associations)
    )
    source_notebooks: Dict[str, Set[str]] = {}
    for notebook_id, source_ids in persisted_associations.items():
        for source_id in source_ids:
            source_notebooks.setdefault(source_id, set()).add(notebook_id)

    rows = []
    for notebook_id in notebook_ids:
        declared = registry.get(notebook_id)
        catalog_entry = catalog.get(notebook_id)
        source_role_map = _parse_roles(roles, notebook_id, source_roles)
        role_source_ids = set(source_role_map)
        declared_source_ids = set(getattr(declared, "sources", []) or [])
        associated_source_ids = persisted_associations.get(notebook_id, set())
        persisted = persisted_notebooks.get(notebook_id)
        configured_curriculum = (
            catalog_entry.get("curriculum_id") if catalog_entry else None
        )
        persisted_curriculum = persisted.get("curriculum_id") if persisted else None
        issues = []

        if declared is None:
            issues.append("NOTEBOOK_NOT_IN_REGISTRY")
        if catalog_entry is None:
            issues.append("NOTEBOOK_NOT_IN_CURRICULUM_CATALOG")
        if notebook_id not in roles:
            issues.append("NOTEBOOK_NOT_IN_SOURCE_ROLE_CATALOG")
        if persisted is None:
            issues.append("NOTEBOOK_NOT_IN_DATABASE")
        if declared is not None and (
            catalog_entry is None or not configured_curriculum
        ):
            issues.append("CURRICULUM_UNMAPPED")
        if (
            catalog_entry
            and persisted
            and configured_curriculum != persisted_curriculum
        ):
            issues.append("CURRICULUM_ID_MISMATCH")
        if declared is not None and not associated_source_ids:
            issues.append("NO_PERSISTED_SOURCE_ASSOCIATIONS")
        if declared_source_ids - associated_source_ids:
            issues.append("DECLARED_SOURCE_NOT_ASSOCIATED")
        if role_source_ids - associated_source_ids:
            issues.append("ROLE_SOURCE_NOT_ASSOCIATED")
        if associated_source_ids - role_source_ids:
            issues.append("ASSOCIATED_SOURCE_HAS_NO_ROLE")
        if associated_source_ids - declared_source_ids:
            issues.append("LOCAL_ASSOCIATION_NOT_DECLARED")
        if declared_source_ids - source_records.keys():
            issues.append("DECLARED_SOURCE_MISSING_FROM_DATABASE")
        if role_source_ids - source_records.keys():
            issues.append("ROLE_SOURCE_MISSING_FROM_DATABASE")
        if associated_source_ids - source_records.keys():
            issues.append("ASSOCIATED_SOURCE_MISSING_FROM_DATABASE")

        all_source_ids = sorted(
            declared_source_ids | role_source_ids | associated_source_ids
        )
        sources = []
        for source_id in all_source_ids:
            sources.append(
                {
                    "source_id": source_id,
                    "declared": source_id in declared_source_ids,
                    "has_role": source_id in role_source_ids,
                    "associated": source_id in associated_source_ids,
                    "exists_in_database": source_id in source_records,
                    "database_record": source_records.get(source_id),
                    "associated_notebooks": sorted(
                        source_notebooks.get(source_id, set())
                    ),
                }
            )

        if declared is not None and catalog_entry is not None:
            identity_classification = "catalogued_canonical_candidate"
        elif declared is not None:
            identity_classification = "registered_without_curriculum_mapping"
        elif catalog_entry is not None:
            identity_classification = "catalog_without_registry_unresolved"
        elif persisted is not None:
            identity_classification = "database_only_unresolved"
        else:
            identity_classification = "configuration_only_unresolved"
        identity_decision = decisions.get(notebook_id)
        if identity_decision is not None:
            identity_classification = identity_decision["classification"]

        rows.append(
            {
                "notebook_id": notebook_id,
                "identity_classification": identity_classification,
                "identity_decision": identity_decision,
                "registry": (
                    {
                        "name": declared.name,
                        "subject": declared.subject,
                        "active": declared.is_active,
                        "declared_source_ids": sorted(declared_source_ids),
                        "legacy_label": "Legacy Alias" in declared.name,
                        "alias_target": None,
                    }
                    if declared is not None
                    else None
                ),
                "curriculum_catalog": (
                    {
                        "name": catalog_entry.get("name"),
                        "curriculum_id": configured_curriculum,
                    }
                    if catalog_entry is not None
                    else None
                ),
                "source_roles": {
                    source_id: source_role_map[source_id]
                    for source_id in sorted(source_role_map)
                },
                "database": (
                    {
                        "name": persisted["name"],
                        "description": persisted["description"],
                        "subject": persisted["subject"],
                        "curriculum_id": persisted_curriculum,
                        "associated_source_ids": sorted(associated_source_ids),
                    }
                    if persisted is not None
                    else None
                ),
                "sources": sources,
                "issues": sorted(issues),
            }
        )

    return {
        "schema": "talos-gate2-notebook-reconciliation-v1",
        "read_only": True,
        "identity_aliases": {
            "declared_alias_mapping": None,
            "note": (
                "No notebook identity-alias mapping is defined by these inputs. "
                "Legacy labels and cross-notebook bridges are not treated as aliases."
            ),
        },
        "counts": {
            "registry_notebooks": len(registry),
            "curriculum_catalog_notebooks": len(catalog),
            "source_role_notebooks": len(roles),
            "database_notebooks": len(persisted_notebooks),
            "database_sources": len(source_records),
            "database_associations": sum(
                len(value) for value in persisted_associations.values()
            ),
        },
        "notebooks": rows,
    }


def load_registry_notebooks() -> list[Any]:
    """Load static registry declarations without starting the application."""
    from study_engine.federation.notebook_registry import DEFAULT_NOTEBOOKS

    return DEFAULT_NOTEBOOKS
