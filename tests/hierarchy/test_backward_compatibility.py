from datetime import datetime, timezone
import sqlite3
import tempfile
from pathlib import Path
import pytest

from study_engine.contracts.notebook import Notebook
from study_engine.state.ledger import EvidenceLedger
from study_engine.state.policy_contracts import (
    ActorType,
    EpistemologicalAuthority,
    EvidenceOutcome,
    EvidenceRecord,
    EvidenceType,
)
from study_engine.hierarchy.folder_orchestrator import FolderOrchestrator
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.storage.sqlite_engine import SQLiteStorageEngine


def test_fase_0_notebook_instantiation_without_folder_id():
    """Fase 0 notebooks instantiated without folder_id default seamlessly to 'folder_root'."""
    nb = Notebook(id="fase_0_programacion", name="Fase 0 - Programación")
    assert nb.id == "fase_0_programacion"
    assert nb.name == "Fase 0 - Programación"
    assert nb.folder_id == "folder_root"


def test_legacy_database_migration_to_v3(tmp_path: Path):
    """A legacy SQLite database created under v2 schema migrates cleanly to v3 without data loss."""
    db_file = tmp_path / "legacy_study.db"

    # 1. Manually create v2 schema (no folders table, no folder_id column)
    conn = sqlite3.connect(str(db_file))
    conn.execute(
        """
        CREATE TABLE notebooks (
            id TEXT PRIMARY KEY NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            subject TEXT,
            curriculum_id TEXT,
            created_at TEXT,
            updated_at TEXT,
            metadata TEXT NOT NULL DEFAULT '{}'
        );
        """
    )
    conn.execute(
        """
        INSERT INTO notebooks (id, name, description, subject, curriculum_id, created_at, updated_at, metadata)
        VALUES ('fase_0_nb', 'Fase 0 Legacy', 'Notas previas', 'Sistemas', 'curr_legacy', '2026-01-01', '2026-01-01', '{"legacy": true}');
        """
    )
    conn.execute("PRAGMA user_version = 2;")
    conn.commit()
    conn.close()

    # 2. Open with modern SQLiteStorageEngine and initialize
    engine = SQLiteStorageEngine(db_path=db_file)
    assert engine.get_schema_version() == 2

    engine.initialize_schema()

    # Database migrates through v3 up to the live engine schema version
    assert engine.get_schema_version() == SQLiteStorageEngine.SCHEMA_VERSION
    assert engine.get_schema_version() >= 3

    # 3. Open with KnowledgeStore and verify legacy notebook survived and has folder_root
    store = KnowledgeStore(db_path=db_file)
    nb = store.get_notebook("fase_0_nb")
    assert nb.id == "fase_0_nb"
    assert nb.name == "Fase 0 Legacy"
    assert nb.folder_id == "folder_root"
    assert nb.metadata.get("legacy") is True

    # Check root folder provisioned
    root = store.get_folder("folder_root")
    assert root.id == "folder_root"


def test_legacy_evidence_ledger_migration_preserves_hashes(tmp_path: Path):
    """EvidenceLedger migrates legacy schema and preserves all cryptographic hashes."""
    ledger_db = tmp_path / "legacy_ledger.db"

    # Create old ledger table without folder_id
    conn = sqlite3.connect(str(ledger_db))
    conn.execute(
        """
        CREATE TABLE evidence_ledger (
            entry_index INTEGER PRIMARY KEY,
            record_id TEXT NOT NULL UNIQUE,
            student_id TEXT NOT NULL,
            node_id TEXT NOT NULL,
            evaluation_attempt_id TEXT NOT NULL,
            assessment_digest TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            parent_entry_hash TEXT NOT NULL,
            entry_hash TEXT NOT NULL UNIQUE,
            committed_at TEXT NOT NULL,
            UNIQUE(student_id, node_id, evaluation_attempt_id)
        );
        """
    )
    conn.commit()
    conn.close()

    # Open ledger with current class (triggers idempotent migration)
    ledger = EvidenceLedger(file_path=ledger_db)

    # Append evidence
    rec = EvidenceRecord(
        record_id="rec_compat_1",
        student_id="student_legacy",
        node_id="NODE-F0",
        evidence_type=EvidenceType.CONCEPTUAL_EXPLANATION,
        outcome=EvidenceOutcome.PASS,
        score=1.0,
        timestamp=datetime.now(timezone.utc),
        actor_type=ActorType.AI_TUTOR,
        actor_id="tutor_module",
        authority_id=EpistemologicalAuthority.EVIDENCE_POLICY,
    )
    entry = ledger.append_evidence(rec)
    assert entry.entry_index == 0

    # Verify cryptographic integrity
    report = ledger.verify_integrity()
    assert report.status.value == "VALID"
    # Verify FolderOrchestrator aggregates progress for legacy student in folder_root
    store = KnowledgeStore(":memory:")
    store.initialize()
    orch = FolderOrchestrator(folder_id="folder_root", knowledge_store=store, ledger=ledger)
    prog = orch.get_aggregated_progress("student_legacy")
    assert prog["total_evidence_entries"] == 1
    assert "NODE-F0" in prog["nodes_recorded"]
