"""Escenario 14: Aislamiento Cross-Notebook (Fase 7.2 - Chaos Engineering).

Simular intentos de acceder o filtrar datos/sesiones entre cuadernos distintos (cross-tenant leakage).
Invariante: Aislamiento criptográfico y relacional estricto por notebook_id;
            0 fugas de memoria episódica o contexto entre cuadernos no autorizados.
Severidad: ALTO.
"""

import pytest

from study_engine.memory.session_history import SessionHistory, SessionRecord
from study_engine.memory.session_briefing import SessionBriefingGenerator
from study_engine.student.storage import StudentStorage


def test_cross_notebook_memory_strict_isolation() -> None:
    """Queries in notebook_defense strictly cannot access records from notebook_cryptography."""
    history = SessionHistory(":memory:")

    # 1. Record sensitive session in Notebook A (Defensa Nacional)
    history.record_session(
        SessionRecord(
            session_id="sess_def_01",
            notebook_id="fadena_ciberdefensa",
            student_id="agustin",
            topic="infraestructuras_criticas",
            next_topic="doctrina_defensa",
            turn_count=15,
            compressed_summary="Discusión secreta sobre doctrina de defensa y SCADA.",
            weak_kcs=["scada_isolation"],
            hints_requested=0,
        )
    )

    # 2. Record innocent session in Notebook B (Programación en C)
    history.record_session(
        SessionRecord(
            session_id="sess_prog_01",
            notebook_id="fadena_lenguajes_c",
            student_id="agustin",
            topic="malloc_free",
            next_topic="gestion_memoria",
            turn_count=8,
            compressed_summary="Práctica de apuntadores y malloc en C.",
            weak_kcs=["punteros_basicos"],
            hints_requested=1,
        )
    )

    # 3. Retrieve sessions for Notebook B
    b_records = history.get_history(notebook_id="fadena_lenguajes_c", student_id="agustin")
    assert len(b_records) == 1
    assert b_records[0].session_id == "sess_prog_01"
    assert "SCADA" not in b_records[0].compressed_summary
    assert "ciberdefensa" not in b_records[0].notebook_id

    # 4. Generate briefing for Notebook B
    storage = StudentStorage(":memory:")
    generator = SessionBriefingGenerator(student_storage=storage, session_history=history)
    briefing_b = generator.generate_briefing(student_id="agustin", notebook_id="fadena_lenguajes_c")

    # Invariant: Briefing for Notebook B contains ZERO mentions of Notebook A
    assert "ciberdefensa" not in briefing_b.lower()
    assert "scada" not in briefing_b.lower()
    assert "doctrina" not in briefing_b.lower()
