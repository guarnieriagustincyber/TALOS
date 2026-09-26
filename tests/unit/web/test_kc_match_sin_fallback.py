from study_engine.pedagogy.student_context import (
    build_bkt_adaptation_directive,
    determine_pedagogical_context_mode,
)


def test_determine_context_mode_con_kc_none():
    """Cuando matched_kc_id es None, devuelve modo neutro sin crashear."""
    context_mode, bkt_meta = determine_pedagogical_context_mode(
        target_kc_id=None,
        bkt_tracker=None,
        kc_catalog={},
        notebook_id=None,
    )
    assert context_mode == "intermediate"
    assert bkt_meta["target_kc_id"] is None
    assert bkt_meta["p_L"] == 0.5
    assert bkt_meta["prerequisites"] == []
    assert bkt_meta["unmet_prerequisites"] == []


def test_build_bkt_directive_con_meta_neutro():
    """La directiva BKT se construye sin excepción con meta neutro."""
    directive = build_bkt_adaptation_directive("intermediate", {})
    assert directive is None or isinstance(directive, str)


def test_match_kc_id_sin_match_devuelve_none():
    """_match_kc_id devuelve None cuando ningún KC califica."""
    from study_engine.web.routes.chat import _match_kc_id

    kcs = [
        {"kc_id": "teleco_transmision_datos", "title": "Transmisión de datos"},
        {"kc_id": "teleco_protocolos_ip", "title": "Protocolos IP y subredes"},
    ]
    result = _match_kc_id(kcs, "¿Cómo funciona un motor de combustión interna?")
    assert result is None
