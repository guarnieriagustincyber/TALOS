"""Calibración BKT estricta (config/bkt_params.json, Fase 5.3b).

- load_bkt_params lee config y fusiona con defaults.
- strict_no_learn_on_incorrect=True: un error NO sube P(L) (puede bajar o quedar).
- Una respuesta correcta SIEMPRE mejora más que una incorrecta.
- Sin el flag, comportamiento histórico intacto (retro-compatibilidad).
"""

import json

from study_engine.student.bkt_tracker import (
    BKTTracker,
    DEFAULT_BKT_PARAMS,
    load_bkt_params,
)
from study_engine.student.contracts import ExerciseFormat, ObservationSource
from study_engine.student.storage import StudentStorage


def _tracker(params, tmp_path):
    return BKTTracker(
        StudentStorage(str(tmp_path / "s.db")),
        default_params=params,
    )


def test_load_bkt_params_desde_config():
    params = load_bkt_params()
    assert params["strict_no_learn_on_incorrect"] is True
    assert params["p_T"] > 0 and 0 < params["p_L0"] < 1


def test_load_bkt_params_fallback_si_archivo_falta(tmp_path):
    params = load_bkt_params(tmp_path / "no_existe.json")
    assert params == DEFAULT_BKT_PARAMS


def test_load_bkt_params_fusiona_parcial(tmp_path):
    p = tmp_path / "custom.json"
    p.write_text(json.dumps({"params": {"p_S": 0.22}}), encoding="utf-8")
    params = load_bkt_params(p)
    assert params["p_S"] == 0.22 and params["p_T"] == DEFAULT_BKT_PARAMS["p_T"]


def test_error_no_sube_p_L_en_modo_estricto(tmp_path):
    params = {**DEFAULT_BKT_PARAMS, "strict_no_learn_on_incorrect": True}
    bkt = _tracker(params, tmp_path)
    p0 = bkt.get_state("kc_x").p_L
    res = bkt.update(
        kc_id="kc_x",
        correct=False,
        source=ObservationSource.EXACT_CORRECTOR,
        format_type=ExerciseFormat.SYMBOLIC_OPEN,
    )
    assert res.p_L <= p0, f"p_L subió tras error: {p0} -> {res.p_L}"
    assert res.attempts == 1


def test_modo_legacy_mantiene_transition_historica(tmp_path):
    bkt = _tracker(dict(DEFAULT_BKT_PARAMS), tmp_path)  # sin flag strict
    p0 = bkt.get_state("kc_y").p_L
    res = bkt.update(
        kc_id="kc_y",
        correct=False,
        source=ObservationSource.EXACT_CORRECTOR,
        format_type=ExerciseFormat.SYMBOLIC_OPEN,
    )
    assert res.p_L > p0  # comportamiento histórico documentado


def test_correcta_mejora_mas_que_incorrecta_en_estricto(tmp_path):
    params = {**DEFAULT_BKT_PARAMS, "strict_no_learn_on_incorrect": True}
    bkt = _tracker(params, tmp_path)
    good = bkt.update(
        kc_id="kc_a", correct=True,
        source=ObservationSource.EXACT_CORRECTOR, format_type=ExerciseFormat.SYMBOLIC_OPEN,
    )
    bad = bkt.update(
        kc_id="kc_b", correct=False,
        source=ObservationSource.EXACT_CORRECTOR, format_type=ExerciseFormat.SYMBOLIC_OPEN,
    )
    assert good.p_L > bad.p_L
    assert good.p_L > DEFAULT_BKT_PARAMS["p_L0"]
