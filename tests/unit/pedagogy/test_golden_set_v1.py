"""Golden Set v1 — validación estructural y coherencia con el catálogo (offline).

Estos tests NO tocan red ni LLM: garantizan que el golden set es ejecutable
(schema completo, casos válidos) y que las expectativas de kc_id son
alcanzables por el matcher actual (`_match_kc_id`). Si el matching cambia y
deja de poder alcanzar una expectativa K2, este test lo detecta antes de
quemar cuota de LLM corriendo el runner en vivo.
"""

import json
from pathlib import Path

from study_engine.web.routes.chat import _match_kc_id

GOLDEN_SET_PATH = Path("data/eval/golden_set_v1.json")
CATALOG_PATH = Path("config/notebook_kc_catalog.json")


def _golden():
    return json.loads(GOLDEN_SET_PATH.read_text(encoding="utf-8"))


def _kcs(notebook_id):
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    return catalog[notebook_id]["kcs"]


def test_schema_completo():
    gs = _golden()
    assert gs["schema"] == "talos-golden-set-v1"
    assert gs["queries"], "el set no puede estar vacío"
    for q in gs["queries"]:
        for field in ("id", "case", "query", "expected_abstain", "expected_kc_id",
                      "expected_fallback", "min_citations"):
            assert field in q, f"{q.get('id')}: falta campo {field}"
        assert q["case"] in ("K1", "K2", "OOD")


def test_casos_k1_k2_ood_presentes():
    cases = {q["case"] for q in _golden()["queries"]}
    assert {"K1", "K2", "OOD"} <= cases


def test_k2_expected_kc_existe_en_catalogo():
    gs = _golden()
    kcs = _kcs(gs["notebook_id"])
    valid = {k["kc_id"] for k in kcs}
    for q in gs["queries"]:
        if q["expected_kc_id"] is not None:
            assert q["expected_kc_id"] in valid, f"{q['id']}: kc esperado no existe"


def test_k2_expectativa_alcanzable_por_el_matcher():
    """El matcher actual debe poder producir el kc_id esperado para cada caso K2."""
    gs = _golden()
    kcs = _kcs(gs["notebook_id"])
    for q in gs["queries"]:
        if q["case"] != "K2":
            continue
        matched = _match_kc_id(kcs, q["query"])
        assert matched == q["expected_kc_id"], (
            f"{q['id']}: matcher devuelve {matched}, esperado {q['expected_kc_id']}"
        )


def test_k1_expectativa_fallback_honesto():
    """Casos K1: el matcher NO debe matchear ningún KC (fallback honesto)."""
    gs = _golden()
    kcs = _kcs(gs["notebook_id"])
    for q in gs["queries"]:
        if q["case"] != "K1":
            continue
        matched = _match_kc_id(kcs, q["query"])
        assert matched is None, (
            f"{q['id']}: matcher devuelve {matched} pero K1 espera fallback=True"
        )


def test_coherencia_interna_expectativas():
    for q in _golden()["queries"]:
        if q["expected_abstain"]:
            assert q["min_citations"] == 0, f"{q['id']}: OOD no debe exigir citas"
        else:
            assert q["min_citations"] >= 1, f"{q['id']}: respuesta grounded exige citas"
        if q["case"] == "K2":
            assert q["expected_fallback"] is False and q["expected_kc_id"]
        if q["case"] == "K1":
            assert q["expected_fallback"] is True and q["expected_kc_id"] is None
