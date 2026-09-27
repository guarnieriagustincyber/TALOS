from study_engine.pedagogy.structured_pipeline import build_mode_specific_instruction


def test_basic_explain_concept_es_introductorio():
    out = build_mode_specific_instruction("explain_concept", None, "nb-test", context_mode="basic")
    assert "INTRODUCTORIA" in out
    for prohibido in ("silicio", "registros", "FLAGS", "MMU", "transistores"):
        assert prohibido.lower() not in out.lower()


def test_sin_context_mode_preserva_tri_capa():
    """Sin context_mode, el gate introductorio no se activa."""
    out = build_mode_specific_instruction("explain_concept", None, "nb-test")
    assert "INTRODUCTORIA" not in out


def test_advanced_mantiene_profundidad():
    out = build_mode_specific_instruction("explain_concept", None, "nb-test", context_mode="advanced")
    assert "silicio" in out.lower() or "máquina" in out.lower()


def test_intermediate_no_activa_gate_introductorio():
    out = build_mode_specific_instruction("explain_concept", None, "nb-test", context_mode="intermediate")
    assert "INTRODUCTORIA" not in out
