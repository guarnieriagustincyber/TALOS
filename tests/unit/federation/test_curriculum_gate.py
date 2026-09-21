"""Unit tests for CurriculumGate Pre-Retrieval Gating (Phase E4, CHSR-RRF Pattern)."""

import pytest
from study_engine.federation.curriculum_gate import CurriculumGate, ScopeConstraint


def test_scope_constraint_validation() -> None:
    # Valid
    valid = ScopeConstraint(notebook_id="fadena-prog", page_start=10, page_end=20)
    assert CurriculumGate.validate_constraint(valid) is True

    # Invalid page bounds: page_start > page_end
    invalid = ScopeConstraint(notebook_id="fadena-prog", page_start=50, page_end=20)
    assert CurriculumGate.validate_constraint(invalid) is False


def test_build_fts5_where_clause_confinement() -> None:
    gate = CurriculumGate()
    c = ScopeConstraint(notebook_id="fadena-so")
    sql, params = gate.build_fts5_where_clause(c)

    assert "ns.notebook_id = ?" in sql
    assert params == ["fadena-so"]


def test_build_fts5_where_clause_full_hierarchy() -> None:
    gate = CurriculumGate()
    c = ScopeConstraint(
        notebook_id="NB-CYBERSECURITY-V1",
        subject="Seguridad",
        level="Grado",
        book="Kurose",
        chapter="Capítulo 3: Capa de Transporte",
        section="3.5 Conexión TCP",
        page_start=210,
        page_end=245,
    )
    sql, params = gate.build_fts5_where_clause(c)

    assert "ns.notebook_id = ?" in sql
    assert "c.chapter = ?" in sql
    assert "c.section = ?" in sql
    assert "c.page_end >= ?" in sql
    assert "c.page_start <= ?" in sql
    assert "json_extract(c.metadata, '$.subject') = ?" in sql
    assert "json_extract(c.metadata, '$.level') = ?" in sql
    assert "json_extract(c.metadata, '$.book') = ?" in sql

    assert "NB-CYBERSECURITY-V1" in params
    assert "Capítulo 3: Capa de Transporte" in params
    assert "3.5 Conexión TCP" in params
    assert 210 in params
    assert 245 in params
    assert "Seguridad" in params
    assert "Grado" in params
    assert "Kurose" in params


def test_build_fts5_where_clause_invalid_fails_closed() -> None:
    gate = CurriculumGate()
    c = ScopeConstraint(notebook_id="fadena-prog", page_start=100, page_end=50)
    sql, params = gate.build_fts5_where_clause(c)
    assert sql == "1 = 0"
    assert params == []


def test_build_dense_filter() -> None:
    gate = CurriculumGate()
    c = ScopeConstraint(
        notebook_id="fadena-prog",
        subject="Programación",
        chapter="Árboles Binarios",
    )
    d_filter = gate.build_dense_filter(c)
    assert d_filter["notebook_id"] == "fadena-prog"
    assert d_filter["subject"] == "Programación"
    assert d_filter["chapter"] == "Árboles Binarios"
