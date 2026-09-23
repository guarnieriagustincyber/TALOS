"""Unit tests for talos content CLI (Slice 6.0.5 Tarea 6).

Asserts:
1. `talos content solution` without prior attempt and without --force exits with code 2.
2. `talos content solution` with --force succeeds (code 0) and records forced=1 in solution_access_log.
3. `talos content solution` with prior recorded attempt succeeds (code 0) and records forced=0.
4. `talos content show` displays statement text and statement chunks, never solutions.
"""

from pathlib import Path
import pytest

from study_engine.cli import main
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.content_registry import ContentItem, ContentStatus, UnitType
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source, SourceRole
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.student.storage import StudentStorage


@pytest.fixture
def setup_cli_dbs(tmp_path: Path):
    k_db = tmp_path / "knowledge_store.db"
    s_db = tmp_path / "student_state.db"

    # Setup knowledge store with 1 exercise having statement and solution
    store = KnowledgeStore(k_db)
    store.initialize()

    src_rec = SourceRecord(
        source_id="src-guia-4",
        manifest=SourceManifest(source_id="src-guia-4", filename="g4.pdf", byte_size=10, sha256="c" * 64),
        source=Source(source_id="src-guia-4", title="Guia 4", author="Catedra", role=SourceRole.PRIMARY),
    )
    doc = Document(id="doc-g4", source_id="src-guia-4", title="Guia 4")
    c_stmt = Chunk(
        id="chk-stmt-3",
        document_id="doc-g4",
        source_id="src-guia-4",
        content="Ejercicio 3: Implementar una cola con dos pilas en C.",
        page_start=4,
        token_count=12,
        index=0,
    )
    c_sol = Chunk(
        id="chk-sol-3",
        document_id="doc-g4",
        source_id="src-guia-4",
        content="Solución: struct Queue { Stack* s1; Stack* s2; }; void enqueue(...);",
        page_start=15,
        token_count=25,
        index=1,
    )
    store.store_ingestion_bundle(src_rec, [doc], [c_stmt, c_sol])

    item = ContentItem(
        content_id="guia_4:ej_3",
        source_id="src-guia-4",
        unit_type=UnitType.EXERCISE,
        statement_text="Ejercicio 3: Implementar una cola con dos pilas en C.",
        chunk_ids=["chk-stmt-3", "chk-sol-3"],
        solution_chunk_ids=["chk-sol-3"],
        status=ContentStatus.OK,
    )
    store.content_registry.save(item)

    # Setup student storage
    student_storage = StudentStorage(s_db)

    return str(k_db), str(s_db), student_storage


def test_cli_solution_denied_exit_code_2(setup_cli_dbs, capsys):
    """Attempting to see solution without attempt or force exits with code 2."""
    k_db, s_db, _ = setup_cli_dbs

    code = main([
        "--knowledge-db", k_db,
        "content",
        "--student-db", s_db,
        "solution",
        "guia_4:ej_3",
    ])
    assert code == 2
    err = capsys.readouterr().err
    assert "ACCESO DENEGADO" in err
    assert "--force" in err


def test_cli_solution_forced_success_and_audit(setup_cli_dbs, capsys):
    """Using --force allows viewing solution and logs forced=1 in audit."""
    k_db, s_db, student_storage = setup_cli_dbs

    code = main([
        "--knowledge-db", k_db,
        "content",
        "--student-db", s_db,
        "solution",
        "guia_4:ej_3",
        "--force",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "SOLUCIONARIO: guia_4:ej_3" in out
    assert "struct Queue" in out
    assert "FORZADO (SIN INTENTO PREVIO)" in out

    # Verify audit log
    logs = student_storage.get_solution_access_logs(content_id="guia_4:ej_3")
    assert len(logs) == 1
    assert logs[0]["forced"] is True


def test_cli_solution_authorized_by_attempt(setup_cli_dbs, capsys):
    """A prior student attempt authorizes viewing solution with forced=0."""
    k_db, s_db, student_storage = setup_cli_dbs

    # Record prior student attempt
    student_storage.record_exercise_attempt("guia_4:ej_3", student_id="agustin", success=False)

    code = main([
        "--knowledge-db", k_db,
        "content",
        "--student-db", s_db,
        "solution",
        "guia_4:ej_3",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "SOLUCIONARIO: guia_4:ej_3" in out
    assert "struct Queue" in out
    assert "AUTORIZADO (CON INTENTO PREVIO)" in out

    logs = student_storage.get_solution_access_logs(content_id="guia_4:ej_3")
    assert len(logs) == 1
    assert logs[0]["forced"] is False


def test_cli_show_filters_solutions(setup_cli_dbs, capsys):
    """talos content show presents statement and NEVER solution chunk."""
    k_db, s_db, _ = setup_cli_dbs

    code = main([
        "--knowledge-db", k_db,
        "content",
        "--student-db", s_db,
        "show",
        "guia 4 ejercicio 3",
    ])
    assert code == 0
    out = capsys.readouterr().out
    assert "guia_4:ej_3" in out
    assert "Implementar una cola con dos pilas en C." in out
    # Anti-leakage: solution chunk content MUST NEVER appear
    assert "struct Queue" not in out
    assert "chk-sol-3" not in out
    assert "chk-stmt-3" in out
