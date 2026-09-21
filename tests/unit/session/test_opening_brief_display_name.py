"""Unit tests for OpeningBriefFacts selected_kc_display_name."""

import pytest
from study_engine.federation.notebook_registry import Notebook as SovereignNotebook
from study_engine.session.opening_brief_builder import OpeningBriefBuilder
from study_engine.student.contracts import BKTState


def test_opening_brief_includes_display_name():
    """OpeningBriefFacts incluye selected_kc_display_name poblado desde catálogo o title."""
    builder = OpeningBriefBuilder()
    nb = SovereignNotebook(
        notebook_id="fadena-so2",
        name="Sistemas Operativos II",
        subject="Sistemas Operativos II",
        sources=[],
    )
    curriculum_kcs = [
        {
            "kc_id": "so2_gestion_procesos_pcb",
            "title": "Gestión de procesos e hilos: PCB, estados y cambio de contexto",
            "display_name": "Gestión de procesos e hilos: PCB, estados y cambio de contexto",
            "unit": 1,
            "prerequisites": [],
        }
    ]
    bkt_states = {
        "so2_gestion_procesos_pcb": BKTState(kc_id="so2_gestion_procesos_pcb", p_L=0.1, attempts=1)
    }

    facts = builder.build_facts(
        notebook=nb,
        curriculum_kcs=curriculum_kcs,
        bkt_states=bkt_states,
    )

    assert facts.selected_kc == "so2_gestion_procesos_pcb"
    assert facts.selected_kc_display_name == "Gestión de procesos e hilos: PCB, estados y cambio de contexto"


def test_opening_brief_fallback_to_id():
    """Si no hay display_name ni title, usa el kc_id como fallback seguro."""
    builder = OpeningBriefBuilder()
    nb = SovereignNotebook(
        notebook_id="fadena-so2",
        name="Sistemas Operativos II",
        subject="Sistemas Operativos II",
        sources=[],
    )
    curriculum_kcs = [
        {
            "kc_id": "so2_raw_kc",
            "unit": 1,
            "prerequisites": [],
        }
    ]
    bkt_states = {}

    facts = builder.build_facts(
        notebook=nb,
        curriculum_kcs=curriculum_kcs,
        bkt_states=bkt_states,
    )

    assert facts.selected_kc == "so2_raw_kc"
    assert facts.selected_kc_display_name == "so2_raw_kc"
