"""Tests del CLI `talos kc` (Fase 5.2) — sobre DBs temporales, sin backend.

Contrato:
- list: muestra KCs (JSON + manuales) con estado BKT; vacío => mensaje amable.
- add: crea (exit 0), slug del título si no se pasa --kc-id; duplicado => 4/409-style;
  notebook inexistente => 1; dificultad inválida => 2.
- delete: solo elimina manuales (los del JSON canónico no viven en la DB).
"""

import json
import sqlite3

import pytest

from study_engine.cli import BKTStatusReadError, _kc_bkt_status, main
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore


def _env(tmp_path):
    kdb = tmp_path / "k.db"
    store = KnowledgeStore(kdb)
    store.initialize()
    store.create_notebook(Notebook(id="nb_test", name="NB test"))
    # DB de estudiante con un estado BKT
    sdb = tmp_path / "student.db"
    con = sqlite3.connect(sdb)
    con.execute("CREATE TABLE bkt_states (kc_id TEXT PRIMARY KEY, p_L REAL)")
    con.execute("INSERT INTO bkt_states VALUES ('kc_manual_1', 0.92)")
    con.commit()
    con.close()
    return kdb, sdb


def _run(tmp_path, args):
    return main(["--knowledge-db", str(tmp_path / "k.db")] + args)


def test_kc_list_vacio_mensaje_amable(tmp_path, capsys):
    kdb, sdb = _env(tmp_path)
    rc = _run(tmp_path, ["kc", "--student-db", str(sdb), "list", "nb_test"])
    assert rc == 0
    assert "No hay KCs definidos" in capsys.readouterr().out


def test_kc_add_crea_con_slug_y_list_muestra_estado(tmp_path, capsys):
    kdb, sdb = _env(tmp_path)
    rc = _run(tmp_path, [
        "kc", "add", "nb_test",
        "--title", "Memoria Virtual y Paginación",
        "--kc-id", "kc_manual_1",
        "--diff", "intermediate",
        "--time", "60",
    ])
    assert rc == 0
    capsys.readouterr()

    rc = _run(tmp_path, ["kc", "--student-db", str(sdb), "list", "nb_test"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "kc_manual_1" in out
    assert "mastered" in out  # p_L=0.92 en la DB de estudiante
    assert "manual" in out and "intermedio" in out


def test_kc_add_slug_automatico(tmp_path, capsys):
    _env(tmp_path)
    rc = _run(tmp_path, ["kc", "add", "nb_test", "--title", "Árboles B + Disco Duro"])
    assert rc == 0
    assert "✅ KC 'arboles_b_disco_duro' agregado" in capsys.readouterr().out


def test_kc_add_duplicado_devuelve_error_409_style(tmp_path, capsys):
    _env(tmp_path)
    assert _run(tmp_path, ["kc", "add", "nb_test", "--title", "Paginación", "--kc-id", "kc_dup"]) == 0
    capsys.readouterr()
    rc = _run(tmp_path, ["kc", "add", "nb_test", "--title", "Otra vez", "--kc-id", "kc_dup"])
    assert rc == 4
    assert "ya existe" in capsys.readouterr().out


def test_kc_add_notebook_inexistente(tmp_path, capsys):
    _env(tmp_path)
    rc = _run(tmp_path, ["kc", "add", "nb_fantasma", "--title", "X válido"])
    assert rc == 1
    assert "no existe" in capsys.readouterr().out


def test_kc_add_dificultad_invalida(tmp_path, capsys):
    _env(tmp_path)
    rc = _run(tmp_path, ["kc", "add", "nb_test", "--title", "Algo válido", "--diff", "easy"])
    assert rc == 2
    assert "inválida" in capsys.readouterr().out


def test_kc_bkt_status_missing_database_means_no_saved_progress(tmp_path):
    assert _kc_bkt_status(tmp_path / "not-created.db") == {}


def test_kc_bkt_status_invalid_schema_is_not_reported_as_absent(tmp_path):
    student_db = tmp_path / "student-invalid-schema.db"
    con = sqlite3.connect(student_db)
    con.execute("CREATE TABLE unrelated_state (id TEXT PRIMARY KEY)")
    con.close()

    with pytest.raises(BKTStatusReadError, match="estado BKT"):
        _kc_bkt_status(student_db)


def test_kc_bkt_status_corrupt_database_is_not_reported_as_absent(tmp_path):
    student_db = tmp_path / "student-corrupt.db"
    student_db.write_text("not a SQLite database", encoding="utf-8")

    with pytest.raises(BKTStatusReadError, match="estado BKT"):
        _kc_bkt_status(student_db)


def test_kc_list_marks_missing_student_database_as_not_started(tmp_path, capsys):
    _env(tmp_path)
    _run(
        tmp_path,
        [
            "kc",
            "add",
            "nb_test",
            "--title",
            "KC sin progreso",
            "--kc-id",
            "kc_without_progress",
        ],
    )
    capsys.readouterr()

    rc = _run(
        tmp_path,
        [
            "kc",
            "--student-db",
            str(tmp_path / "not-created.db"),
            "list",
            "nb_test",
        ],
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "kc_without_progress" in captured.out
    assert "not_started" in captured.out
    assert not captured.err


def test_kc_list_reports_bkt_read_error_instead_of_not_started(tmp_path, capsys):
    _env(tmp_path)
    _run(
        tmp_path,
        [
            "kc",
            "add",
            "nb_test",
            "--title",
            "KC para estado",
            "--kc-id",
            "kc_for_status",
        ],
    )
    capsys.readouterr()

    invalid_student_db = tmp_path / "student-invalid-schema.db"
    con = sqlite3.connect(invalid_student_db)
    con.execute("CREATE TABLE unrelated_state (id TEXT PRIMARY KEY)")
    con.close()

    rc = _run(
        tmp_path,
        [
            "kc",
            "--student-db",
            str(invalid_student_db),
            "list",
            "nb_test",
        ],
    )

    captured = capsys.readouterr()
    assert rc == 1
    assert "Error: No se pudo leer el estado BKT" in captured.err
    assert "not_started" not in captured.out


def test_kc_delete_solo_manuales(tmp_path, capsys):
    kdb, sdb = _env(tmp_path)
    assert _run(tmp_path, ["kc", "add", "nb_test", "--title", "KC borrable", "--kc-id", "kc_del"]) == 0
    capsys.readouterr()
    rc = _run(tmp_path, ["kc", "delete", "nb_test", "kc_del"])
    assert rc == 0
    assert "eliminado" in capsys.readouterr().out

    # Segundo delete: ya no existe
    rc = _run(tmp_path, ["kc", "delete", "nb_test", "kc_del"])
    assert rc == 4

    # Un KC canónico del JSON no es alcanzable (nunca estuvo en la tabla)
    rc = _run(tmp_path, ["kc", "delete", "fase0-soc", "fase0_tramo1_metodologia"])
    assert rc == 4
