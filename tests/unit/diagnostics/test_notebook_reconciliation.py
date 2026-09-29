import hashlib
import json
import sqlite3
from types import SimpleNamespace

import pytest

from study_engine.diagnostics.notebook_reconciliation import reconcile_notebooks


@pytest.fixture()
def reconciliation_inputs(tmp_path):
    database = tmp_path / "knowledge.db"
    connection = sqlite3.connect(database)
    connection.executescript("""
        CREATE TABLE notebooks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            curriculum_id TEXT
        );
        CREATE TABLE sources (
            source_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            subject TEXT,
            course TEXT
        );
        CREATE TABLE notebook_sources (
            notebook_id TEXT NOT NULL,
            source_id TEXT NOT NULL,
            PRIMARY KEY (notebook_id, source_id)
        );
        INSERT INTO notebooks VALUES (
            'nb-one', 'Notebook One', 'Description', 'Subject One', 'legacy_v1'
        );
        INSERT INTO sources VALUES (
            'src-shared', 'Shared source', 'abc123', NULL, NULL
        );
        INSERT INTO sources VALUES (
            'src-local-only', 'Local source', 'def456', NULL, NULL
        );
        INSERT INTO notebook_sources VALUES ('nb-one', 'src-shared');
        INSERT INTO notebook_sources VALUES ('nb-one', 'src-local-only');
        """)
    connection.commit()
    connection.close()

    catalog = tmp_path / "catalog.json"
    catalog.write_text(
        json.dumps(
            {
                "nb-one": {"name": "Notebook One", "curriculum_id": "curriculum_v1"},
                "catalog-only": {"name": "Catalog Only", "curriculum_id": "catalog_v1"},
            }
        ),
        encoding="utf-8",
    )
    roles = tmp_path / "roles.json"
    roles.write_text(
        json.dumps(
            {
                "nb-one": {
                    "src-shared": {"roles": ["PRIMARY"]},
                    "src-role-only": {"roles": ["COMPLEMENTARY"]},
                },
                "roles-only": {"src-role-only": {"roles": ["PRIMARY"]}},
            }
        ),
        encoding="utf-8",
    )
    registry = [
        SimpleNamespace(
            notebook_id="nb-one",
            name="Notebook One",
            subject="Subject One",
            is_active=True,
            sources=["src-shared", "src-declared-missing"],
        ),
        SimpleNamespace(
            notebook_id="registry-only",
            name="Registry Only",
            subject="Subject",
            is_active=True,
            sources=[],
        ),
    ]
    return database, catalog, roles, registry


def test_reports_identity_and_source_discrepancies_without_writing(
    reconciliation_inputs,
):
    database, catalog, roles, registry = reconciliation_inputs
    before = (
        hashlib.sha256(database.read_bytes()).hexdigest(),
        database.stat().st_mtime_ns,
    )

    report = reconcile_notebooks(database, catalog, roles, registry)

    after = (
        hashlib.sha256(database.read_bytes()).hexdigest(),
        database.stat().st_mtime_ns,
    )
    assert after == before
    assert report["read_only"] is True
    assert report["identity_aliases"]["declared_alias_mapping"] is None
    rows = {row["notebook_id"]: row for row in report["notebooks"]}
    notebook = rows["nb-one"]
    assert "CURRICULUM_ID_MISMATCH" in notebook["issues"]
    assert "DECLARED_SOURCE_NOT_ASSOCIATED" in notebook["issues"]
    assert "ROLE_SOURCE_NOT_ASSOCIATED" in notebook["issues"]
    assert "ASSOCIATED_SOURCE_HAS_NO_ROLE" in notebook["issues"]
    assert "LOCAL_ASSOCIATION_NOT_DECLARED" in notebook["issues"]
    assert "DECLARED_SOURCE_MISSING_FROM_DATABASE" in notebook["issues"]
    assert notebook["source_roles"]["src-shared"]["roles"] == ["PRIMARY"]
    assert "NOTEBOOK_NOT_IN_REGISTRY" in rows["roles-only"]["issues"]
    assert "NOTEBOOK_NOT_IN_DATABASE" in rows["registry-only"]["issues"]


def test_registry_overlap_does_not_expand_the_persisted_acl(reconciliation_inputs):
    database, catalog, roles, registry = reconciliation_inputs
    registry.append(
        SimpleNamespace(
            notebook_id="nb-two",
            name="Notebook Two",
            subject="Subject Two",
            is_active=True,
            sources=["src-shared"],
        )
    )

    report = reconcile_notebooks(database, catalog, roles, registry)
    source = next(
        source
        for source in next(
            row for row in report["notebooks"] if row["notebook_id"] == "nb-one"
        )["sources"]
        if source["source_id"] == "src-shared"
    )
    assert source["associated_notebooks"] == ["nb-one"]
    assert source["associated"] is True


def test_reports_sources_shared_by_explicit_database_associations(
    reconciliation_inputs,
):
    database, catalog, roles, registry = reconciliation_inputs
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO notebooks VALUES (?, ?, ?, ?, ?)",
        ("nb-two", "Notebook Two", "Description", "Subject Two", "curriculum_two"),
    )
    connection.execute(
        "INSERT INTO notebook_sources VALUES (?, ?)", ("nb-two", "src-shared")
    )
    connection.commit()
    connection.close()

    report = reconcile_notebooks(database, catalog, roles, registry)
    source = next(
        source
        for source in next(
            row for row in report["notebooks"] if row["notebook_id"] == "nb-one"
        )["sources"]
        if source["source_id"] == "src-shared"
    )
    assert source["associated_notebooks"] == ["nb-one", "nb-two"]


def test_fails_explicitly_for_invalid_catalog(reconciliation_inputs, tmp_path):
    database, _, roles, registry = reconciliation_inputs
    invalid_catalog = tmp_path / "invalid.json"
    invalid_catalog.write_text("{", encoding="utf-8")

    with pytest.raises(ValueError, match="Cannot read valid JSON"):
        reconcile_notebooks(database, invalid_catalog, roles, registry)


def test_fails_explicitly_for_missing_database(reconciliation_inputs, tmp_path):
    _, catalog, roles, registry = reconciliation_inputs

    with pytest.raises(ValueError, match="does not exist"):
        reconcile_notebooks(tmp_path / "missing.db", catalog, roles, registry)


def test_catalog_only_notebook_is_not_reported_as_curriculum_mismatch(
    reconciliation_inputs,
):
    database, catalog, roles, registry = reconciliation_inputs
    report = reconcile_notebooks(database, catalog, roles, registry)
    row = next(
        item for item in report["notebooks"] if item["notebook_id"] == "catalog-only"
    )

    assert row["identity_classification"] == "catalog_without_registry_unresolved"
    assert "NOTEBOOK_NOT_IN_REGISTRY" in row["issues"]
    assert "CURRICULUM_ID_MISMATCH" not in row["issues"]


def test_legacy_named_scopes_are_not_assumed_to_be_aliases(reconciliation_inputs):
    database, catalog, roles, registry = reconciliation_inputs
    for notebook_id in ("fadena-prog", "fadena-so"):
        registry.append(
            SimpleNamespace(
                notebook_id=notebook_id,
                name=f"{notebook_id} (Legacy Alias)",
                subject="Legacy subject",
                is_active=True,
                sources=[],
            )
        )

    report = reconcile_notebooks(database, catalog, roles, registry)
    rows = {row["notebook_id"]: row for row in report["notebooks"]}
    assert rows["fadena-prog"]["identity_classification"] == (
        "registered_without_curriculum_mapping"
    )
    assert rows["fadena-so"]["identity_classification"] == (
        "registered_without_curriculum_mapping"
    )
    assert rows["fadena-prog"]["registry"]["alias_target"] is None


def test_explicit_identity_decisions_are_reported_as_audit_only_metadata(
    reconciliation_inputs, tmp_path
):
    database, catalog, roles, registry = reconciliation_inputs
    decisions = tmp_path / "decisions.json"
    decisions.write_text(
        json.dumps(
            {
                "purpose": "audit-only",
                "decisions": {
                    "nb-one": {
                        "classification": "canonical_course_notebook",
                        "decision": "Keep exact ID",
                        "alias_target": None,
                        "evidence": ["exact catalog key"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    report = reconcile_notebooks(
        database, catalog, roles, registry, identity_decisions=decisions
    )
    row = next(item for item in report["notebooks"] if item["notebook_id"] == "nb-one")
    assert row["identity_classification"] == "canonical_course_notebook"
    assert row["identity_decision"]["alias_target"] is None


def test_role_catalog_requires_explicit_roles(reconciliation_inputs):
    database, catalog, roles, registry = reconciliation_inputs
    invalid_roles = roles.with_name("invalid-roles.json")
    invalid_roles.write_text(
        json.dumps({"nb-one": {"src-shared": {"authority": 1.0}}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="roles list"):
        reconcile_notebooks(database, catalog, invalid_roles, registry)
