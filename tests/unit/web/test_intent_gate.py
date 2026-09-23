"""COMMIT 3 fix(scope): intención no curricular independiente del match de contenido.

Bug: "¿Qué opinás de Star Wars?" matcheaba chunks reales del corpus (una nota
de Star Wars usada como ejemplo didáctico de arreglos) y por eso no abstenía.

Contrato:
- patrón no curricular + cero match KC -> abstención (sin siquiera correr retrieval)
- patrón no curricular + vocabulario curricular -> continúa normal
- la palabra clave del chat SSO no se ve afectada
"""

from datetime import datetime, timezone
from types import SimpleNamespace

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.hierarchy.scope_resolver import ScopeResolver
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.routes.chat import (
    ChatQueryRequest,
    _is_non_curricular_intent,
    _prepare_chat_context,
)

_KCS = [
    {"kc_id": "big_o_complejidad", "title": "Análisis Asintótico",
     "subtopics": ["Algoritmos de búsqueda: lineal vs. búsqueda binaria", "Ordenamiento Burbuja"]},
    {"kc_id": "fase0_tramo4_estructuras_lineales", "title": "Estructuras Lineales",
     "subtopics": ["Arrays y direccionamiento contiguo"]},
]


def test_star_wars_es_no_curricular():
    assert _is_non_curricular_intent("¿Qué opinás de Star Wars?", _KCS) is True


def test_mezcla_con_vocabulario_curricular_continua():
    assert _is_non_curricular_intent("¿qué opinás de la búsqueda binaria en arreglos?", _KCS) is False


def test_query_curricular_clasica_no_afectada():
    assert _is_non_curricular_intent("¿cómo funciona la búsqueda binaria?", _KCS) is False


def _store_with_starwars_chunk():
    store = KnowledgeStore(":memory:")
    store.initialize()
    now = datetime.now(timezone.utc)
    store.create_notebook(Notebook(id="nb1", name="NB1"))
    rec = SourceRecord(
        source_id="src1",
        manifest=SourceManifest(source_id="src1", filename="a.pdf", byte_size=1, sha256="1" * 64),
    )
    doc = Document(id="d1", source_id="src1", title="Doc", content="")
    chunks = [
        Chunk(id="c_sw", document_id="d1", source_id="src1",
              content="Ejemplo de arreglo: Thrawn es el estratega del imperio galáctico de Star Wars.", index=0),
        Chunk(id="c_bb", document_id="d1", source_id="src1",
              content="La búsqueda binaria en un arreglo divide el espacio de búsqueda a la mitad en cada paso.", index=1),
    ]
    store.store_ingestion_bundle(rec, [doc], chunks, notebook_id="nb1")
    return store


def test_prepare_abstains_star_wars_despite_content_match():
    """El chunk de Star Wars ESTÁ en el corpus; la abstención es por intención."""
    store = _store_with_starwars_chunk()
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={"nb1": {"kcs": _KCS}}),
        bkt_tracker=None,
        mem0_manager=None,
        pedagogical_memory_tracker=None,
    )
    request = ChatQueryRequest(
        prompt="¿Qué opinás de Star Wars?", notebook_id="nb1", requested_phase="conceptual"
    )
    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="notebook",
        target_scope_id="nb1",
    )
    context_pack = result[2]
    assert context_pack is not None and context_pack.abstained is True
    assert "curricular" in (context_pack.abstention_reason or "").lower()


def test_prepare_grounded_for_curricular_opinion_query():
    store = _store_with_starwars_chunk()
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={"nb1": {"kcs": _KCS}}),
        bkt_tracker=None,
        mem0_manager=None,
        pedagogical_memory_tracker=None,
    )
    request = ChatQueryRequest(
        prompt="¿qué opinás de la búsqueda binaria en arreglos?",
        notebook_id="nb1",
        requested_phase="conceptual",
    )
    result = _prepare_chat_context(
        store=store,
        resolver=ScopeResolver(store),
        container=container,
        prompt_text=request.prompt,
        request=request,
        target_scope_type="notebook",
        target_scope_id="nb1",
    )
    context_pack = result[2]
    assert context_pack is not None and not context_pack.abstained
    assert context_pack.chunks, "debió recuperar el chunk de búsqueda binaria"


def test_explicit_opinion_verbs_without_curricular_terms_abstain():
    """Verbos explícitos de opinión ('opino que', 'creo que') sin KC son no curriculares."""
    assert _is_non_curricular_intent("opino que las empanadas de carne son las mejores", _KCS) is True
    assert _is_non_curricular_intent("creo que va a llover esta tarde", _KCS) is True


def test_explicit_opinion_verbs_with_curricular_terms_continue():
    """Verbos explícitos de opinión con vocabulario curricular continúan normalmente."""
    assert _is_non_curricular_intent("opino que la búsqueda binaria divide el espacio a la mitad", _KCS) is False
    assert _is_non_curricular_intent("creo que los arrays usan direccionamiento contiguo", _KCS) is False


def test_short_ood_query_with_conversational_verbs_yields_zero_candidates():
    """da9d18d: stopwords de opinión conversacional no reabren la guarda de Commit 6 en queries OOD cortas."""
    store = _store_with_starwars_chunk()
    # 1. Query OOD corta con verbo de opinión + término ausente
    res1 = store.search("¿Qué opinás de las empanadas?", notebook_id="nb1")
    assert len(res1) == 0, f"Query OOD no debe admitir candidatos post-gate, obtuvo {len(res1)}"

    # 2. Query OOD con verbo conversacional de opinión
    res2 = store.search("¿Opinás que el clima está lindo?", notebook_id="nb1")
    assert len(res2) == 0, f"Query OOD de clima no debe admitir candidatos post-gate, obtuvo {len(res2)}"

    # 3. Query puramente conversacional/stopwords
    res3 = store.search("¿Qué opinás?", notebook_id="nb1")
    assert len(res3) == 0, f"Query solo stopwords no debe admitir candidatos post-gate, obtuvo {len(res3)}"
