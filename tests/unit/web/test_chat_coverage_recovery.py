"""M1-03 §1: regresión del pase de recuperación dirigido por cobertura.

Defecto corregido (repro offline_chat_retrieval_repro.py, hallazgo live
M1-02chat): una query académica multi-aspecto con conjunción FTS estricta
resolvía 0 hits; el fallback disyuntivo seleccionaba por conteo de términos
incidentales (≥2) y dejaba fuera los pasajes tópicos que cubren el término
distintivo. El gate C5 abstuvo (QUERY_OUT_OF_SCOPE) con términos críticos
que el CORPUS AUTORIZADO sí contenía ('aritmética de punteros' en 66 chunks
vinculados de Joyanes). El pase corrige el recall con búsquedas léxicas
dirigidas por término sobre la MISMA allowlist y filtro anti-leakage.

Contrato probado:
- Los pasajes que cubren el término distintivo Sí existente en fuentes
  autorizadas alcanzan el conjunto (el gate C5 ya No abstendrá por huecos
  de seleccion — se prueba el helper directamente).
- Query genuinamente sin evidencia → el helper NO inventa chunks.
- Anti-leakage: chunks marcados como solución no entran al conjunto.
- Dedup determinista y techo acotado.
"""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))

from study_engine.context.c5_trust import (
    extract_critical_query_terms,
    retrieval_variants_for_term,
)
from study_engine.context.c5_trust import evaluate_term_coverage
from study_engine.web.routes.chat import (
    _COVERAGE_RECOVERY_MAX_TERMS,
    _COVERAGE_RECOVERY_PER_TERM_LIMIT,
    _recover_coverage_gaps,
)

QUERY = "¿Cómo funciona la aritmética de punteros y por qué p+1 avanza sizeof(T) bytes?"
OOS_QUERY = "¿Quién ganó la final del mundial de fútbol 2026 y qué sostuvo el arquero?"


class _FakeSearchResult:
    def __init__(self, content: str, src: str, chunk_id: str) -> None:
        self.content = content
        self.source_id = src
        self.chunk_id = chunk_id
        self.score = 5.0


class _FakeSolutionRegistry:
    """Registro mínimo imitando get_solution_chunk_ids (anti-leakage)."""

    def __init__(self, solution_ids):
        self._ids = set(solution_ids)

    def get_solution_chunk_ids(self):
        return self._ids


class _FakeStore:
    """Store FTS determinista con semántica de prefijos por token-pliegue.

    Imita los DOS defectos del índice real: la query conjuntiva
    multi-aspecto (token1 token2 ...) resuelve 0 hits cuando un solo pasaje
    no contiene TODOS los tokens, y los términos aislados sí matchean
    pasajes que la primera pasada no alcanzó.
    """

    def __init__(self, corpus, allowlist, solution_ids=()):
        self._corpus = corpus
        self._allowlist = allowlist
        self.content_registry = _FakeSolutionRegistry(solution_ids)
        self.search_calls: list[str] = []

    @staticmethod
    def _norm(w: str) -> str:
        w = w.lower()
        return "".join(
            c for c in __import__("unicodedata").normalize("NFD", w)
            if not __import__("unicodedata").category(c).startswith("Mn")
        )

    def search(self, query, notebook_id=None, limit=10, source_ids=None, **_):
        self.search_calls.append(query)
        tokens = [t for t in query.replace('"', "").replace("*", "").split() if t]
        conjuntiva = len(tokens) > 1
        out = []
        idx = 0
        for src, texts in self._corpus.items():
            if source_ids is not None and src not in source_ids:
                continue
            if src not in self._allowlist:
                continue
            for text in texts:
                idx += 1
                words = [self._norm(w) for w in text.split()]
                if conjuntiva:
                    ok = all(
                        any(w.startswith(t) for w in words)
                        for t in map(self._norm, tokens)
                    )
                else:
                    tok = self._norm(tokens[0]) if tokens else ""
                    ok = tok and any(w.startswith(tok) for w in words)
                if ok:
                    out.append(_FakeSearchResult(text, src, f"c{idx}"))
        return out[:limit]


TOPICA_JOYANES = (
    "la aritmética de punteros en C permite calcular la dirección base más el desplazamiento"
)
AVANZA_JOYANES = (
    "el índice 1 avanza sobre el arreglo y la aritmética de punteros calcula cada elemento"
)
TANGENCIAL_JOYANES = (
    "sizeof toma como valor el número de bytes que ocupa un tipo especificado en C"
)
TANGENCIAL_INGLES = "a pointer to the successor block indicates memory management for programs"
URL_CORPUS_FUERA_ALLOWLIST = "la aritmética de punteros avanza fuera de la allowlist"
CORPUS_SOLUCION = "SOLUCIÓN DEL EJERCICIO: el índice avanza con aritmética de punteros hacia n"


def make_store() -> _FakeStore:
    return _FakeStore(
        {
            "src_joyanes": [TOPICA_JOYANES, AVANZA_JOYANES, TANGENCIAL_JOYANES],
            "src_ingles_tangencial": [TANGENCIAL_INGLES],
            "src_fuera": [URL_CORPUS_FUERA_ALLOWLIST],
        },
        allowlist=["src_joyanes", "src_ingles_tangencial"],
    )


AUTHORITATES = {"src_joyanes", "src_ingles_tangencial"}


def test_retrieval_variants_bilingual_and_plural():
    v_pointer = retrieval_variants_for_term("pointer")
    assert v_pointer[0] == "pointer"
    assert any(v.startswith("puntero") for v in v_pointer), v_pointer  # par bilingüe declarado
    # término sin mapa bilingüe ni plurales
    assert retrieval_variants_for_term("sizeof") == ["sizeof"]
    # pliegue de acentos determinista
    assert retrieval_variants_for_term("aritmética") == ["aritmética"]


def test_recover_adds_missing_distinctive_topic_chunk():
    store = make_store()
    base = [
        _FakeSearchResult(TANGENCIAL_JOYANES, "src_joyanes", "base_c20"),
        _FakeSearchResult(TANGENCIAL_INGLES, "src_ingles_tangencial", "base_c21"),
    ]
    terms = extract_critical_query_terms(QUERY)
    _, missing_inicial = evaluate_term_coverage(terms, base)
    assert missing_inicial, "el escenario base debe reproducir el hueco de cobertura"

    extra = _recover_coverage_gaps(
        store=store,
        results=base,
        coverage_query=QUERY,
        authorized_source_ids=AUTHORITATES,
        notebook_id="nb",
    )
    join = " ".join(getattr(r, "content", "") for r in extra)
    assert "aritmética de punteros" in join, "debe aportar el pasaje tópico ausente"
    _, missing_final = evaluate_term_coverage(terms, list(base) + extra)
    assert missing_final == [], missing_final
    # sólo fuentes autorizadas
    assert all(r.source_id in AUTHORITATES for r in extra)


def test_recover_never_invents_when_corpus_lacks_term():
    store = make_store()
    base = [
        _FakeSearchResult(TANGENCIAL_JOYANES, "src_joyanes", "base_c20"),
    ]
    extra = _recover_coverage_gaps(
        store=store,
        results=base,
        coverage_query=OOS_QUERY,
        authorized_source_ids=AUTHORITATES,
        notebook_id="nb",
    )
    assert extra == [], "términos sin evidencia: no se aporta nada (sin inventar)"


def test_recover_excludes_solution_chunks_and_out_of_allowlist():
    store = _FakeStore(
        {
            "src_autorizada": [CORPUS_SOLUCION],
            "src_fuera": [URL_CORPUS_FUERA_ALLOWLIST],
        },
        allowlist=["src_autorizada"],
        solution_ids={"c1"},  # el primer chunk de src_autorizada es solución
    )
    extra = _recover_coverage_gaps(
        store=store,
        results=[],
        coverage_query=QUERY,
        authorized_source_ids={"src_autorizada"},
        notebook_id="nb",
    )
    join = " ".join(getattr(r, "content", "") for r in extra)
    assert "SOLUCIÓN DEL EJERCICIO" not in join, "anti-leakage: la solución no entra"
    assert "fuera de la allowlist" not in join


def test_recover_is_deterministic_and_bounded():
    store = make_store()
    base = [
        _FakeSearchResult(TANGENCIAL_JOYANES, "src_joyanes", "base_c20"),
    ]
    kwargs = dict(
        store=store,
        results=base,
        coverage_query=QUERY,
        authorized_source_ids=AUTHORITATES,
        notebook_id="nb",
    )
    r1 = _recover_coverage_gaps(**kwargs)
    r2 = _recover_coverage_gaps(**kwargs)
    assert [r.chunk_id for r in r1] == [r.chunk_id for r in r2]
    # techo defensivo: límite por término * sectores de términos
    assert len(r1) <= _COVERAGE_RECOVERY_PER_TERM_LIMIT * _COVERAGE_RECOVERY_MAX_TERMS
