"""F3: bkt_context honesto — matching de KC sin fallback silencioso a kcs_list[0].

Contrato:
- Query sin KC matcheable -> _match_kc_id devuelve None (el SSE marcará
  bkt_context.fallback=True con valores neutrales).
- Query con vocabulario del KC (título/display_name/subtopics) -> kc_id correcto.
- kc_id literal en la query gana siempre.
- El viejo fallback (atribuir todo al primer KC del catálogo) fue eliminado.
"""

import json
from pathlib import Path

from study_engine.web.routes.chat import _kc_search_terms, _match_kc_id

_CATALOG_PATH = Path("config/notebook_kc_catalog.json")


def _real_kcs(notebook_id: str = "fase0-soc"):
    data = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    return data[notebook_id]["kcs"]


def test_query_sin_kc_matcheable_devuelve_none():
    kcs = _real_kcs()
    assert _match_kc_id(kcs, "fotosintesis cloroplastos tilacoides celula vegetal") is None
    assert _match_kc_id(kcs, "¿cuál es la capital de Francia?") is None
    assert _match_kc_id(kcs, "") is None
    assert _match_kc_id([], "punteros") is None


def test_query_con_vocabulario_de_kc_matchea_el_correcto():
    kcs = _real_kcs()
    # 'malloc' + 'free' son subtopics específicos de aritmetica_punteros
    assert _match_kc_id(kcs, "¿cuándo conviene usar malloc y free en el heap?") == "aritmetica_punteros"
    # 'punteros' (término específico >= 6 chars, palabra completa)
    assert _match_kc_id(kcs, "explicame punteros a funciones") == "aritmetica_punteros"
    # 2+ términos de Big-O
    assert _match_kc_id(kcs, "notación asintótica y complejidad algorítmica") == "big_o_complejidad"


def test_kc_id_literal_en_query_gana_siempre():
    kcs = _real_kcs()
    assert _match_kc_id(kcs, "¿qué cubre fase0_tramo2_logica_control?") == "fase0_tramo2_logica_control"


def test_terminos_excluyen_stopwords_y_cortas():
    kc = {"kc_id": "x", "title": "Estructuras de Datos Lineales", "subtopics": ["Colas y pilas con arrays"]}
    terms = _kc_search_terms(kc)
    assert "de" not in terms and "con" not in terms and "una" not in terms
    assert "colas" in terms and "pilas" in terms


def test_matching_no_confunde_substring_por_palabra():
    # 'dado' dentro de 'dados' no cuenta; el matching es por palabra completa.
    kcs = [{"kc_id": "kc_dadas", "title": "Lanzamiento de Dado", "subtopics": []}]
    assert _match_kc_id(kcs, "tiré los dados ayer") is None
    assert _match_kc_id(kcs, "lanzamiento de un dado") == "kc_dadas"
