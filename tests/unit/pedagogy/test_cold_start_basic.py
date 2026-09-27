from types import SimpleNamespace

from study_engine.pedagogy.student_context import determine_pedagogical_context_mode


def _tracker(states):
    return SimpleNamespace(
        params={"cold_start_mode": "basic"},
        get_state=lambda kc_id: states[kc_id],
    )


def test_cold_start_returns_basic():
    tracker = _tracker({"kc": SimpleNamespace(attempts=0, p_L=None)})

    mode, meta = determine_pedagogical_context_mode(
        target_kc_id="kc",
        bkt_tracker=tracker,
    )

    assert mode == "basic"
    assert meta["attempts"] == 0


def test_prereq_priority_over_cold_start():
    tracker = _tracker({
        "target": SimpleNamespace(attempts=0, p_L=0.1),
        "prereq": SimpleNamespace(attempts=2, p_L=0.1),
    })
    catalog = {
        "nb": {
            "kcs": [
                {"kc_id": "target", "prerequisites": ["prereq"]},
            ],
        },
    }

    mode, _ = determine_pedagogical_context_mode(
        target_kc_id="target",
        bkt_tracker=tracker,
        kc_catalog=catalog,
        notebook_id="nb",
    )

    assert mode == "prerequisite_reinforcement"


def test_kc_no_identificado_neutral():
    mode, meta = determine_pedagogical_context_mode(
        target_kc_id=None,
        bkt_tracker=None,
    )

    assert mode == "intermediate"
    assert meta["context_mode"] == "intermediate"
