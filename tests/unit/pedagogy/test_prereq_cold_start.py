from types import SimpleNamespace

from study_engine.pedagogy.student_context import determine_pedagogical_context_mode


def _determine_mode(prereq_state, target_state):
    states = {"target": target_state, "prereq": prereq_state}
    tracker = SimpleNamespace(
        params={"cold_start_mode": "basic"},
        get_state=lambda kc_id: states[kc_id],
    )
    catalog = {
        "nb": {
            "kcs": [{"kc_id": "target", "prerequisites": ["prereq"]}],
        },
    }
    return determine_pedagogical_context_mode(
        target_kc_id="target",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="nb",
    )[0]


def test_prereq_no_evaluado_no_bloquea_cold_start():
    assert _determine_mode(
        SimpleNamespace(attempts=0, p_L=0.1),
        SimpleNamespace(attempts=0, p_L=0.1),
    ) == "basic"


def test_prereq_reprobado_bloquea_cold_start():
    assert _determine_mode(
        SimpleNamespace(attempts=2, p_L=0.2),
        SimpleNamespace(attempts=0, p_L=0.1),
    ) == "prerequisite_reinforcement"


def test_prereq_aprobado_no_bloquea():
    assert _determine_mode(
        SimpleNamespace(attempts=2, p_L=0.8),
        SimpleNamespace(attempts=1, p_L=0.65),
    ) == "intermediate"
