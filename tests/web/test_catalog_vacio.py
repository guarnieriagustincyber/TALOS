from types import SimpleNamespace

from study_engine.web.routes.ingestion import get_ingestion_catalog


def _container(sources):
    store = SimpleNamespace(sources=SimpleNamespace(list_all=lambda: sources))
    return SimpleNamespace(knowledge_store=store)


def test_catalogo_vacio_sin_fuente_fantasma():
    catalog = get_ingestion_catalog(_container([]))
    assert catalog == []
    assert all(item.source_id != "src-prog-punteros" for item in catalog)
    assert all(item.trust_level != "verified" for item in catalog)


def test_catalogo_con_fuentes_reales():
    source = SimpleNamespace(
        source_id="src-real",
        metadata={},
        manifest=SimpleNamespace(sha256="a" * 64),
        source=SimpleNamespace(title="Fuente real", author="Autor", created_at=None),
    )
    catalog = get_ingestion_catalog(_container([source]))
    assert len(catalog) == 1
    assert catalog[0].source_id == "src-real"
    assert catalog[0].title == "Fuente real"
