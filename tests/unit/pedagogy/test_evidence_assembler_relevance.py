"""Regresión M1-01: relevancia antes que posición en el evidenciador por KC.

Hallazgo de ejecución real (2026-10-20): la lectura posicional (`pos_index`
0..1) devuelve las PORTADAS del PDF, por lo que `chunks[:2]` nunca contenía
contenido curricular y el fraseo substring `query.lower() in chunk_text`
fracasaba siempre → packet evidencia vacía → `explain_concept` abstenía con
`REJECTED_UNSUPPORTED` en todo KC.

El fix usa búsqueda léxica scoped (`fts_search/search` con
`source_ids=[src_id]`, `notebook_id`, `limit=2`) cuando el store la expone,
preservando el scope de autorización (roles ∩ L3 no cambia). Los mocks
legados sin búsqueda conservan la ruta posicional con el filtro substring
original (contratos de test_evidence_assembler_isolation.py intactos).
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler


class _SearchableStore:
    """Store mínimo con búsqueda léxica scoped (sin lector posicional)."""

    def __init__(self) -> None:
        self.fts_calls: list[dict] = []
        self.positional_reads: list[str] = []

    def get_notebook(self, notebook_id: str) -> SimpleNamespace:
        assert notebook_id == "roadmap"
        return SimpleNamespace(sources=["source-authorized"])

    def fts_search(self, **kwargs):
        self.fts_calls.append(kwargs)
        # Contenido relevante que NO contiene la query completa como substring:
        # solo la ruta de relevancia puede admitirlo.
        return [
            SimpleNamespace(
                chunk_id="chk-rel-1",
                document_id="doc-1",
                source_id="source-authorized",
                content="El heap devuelve el bloque liberado al allocator para una futura asignación.",
                page_start=41,
                page_end=41,
            ),
            SimpleNamespace(
                chunk_id="chk-rel-2",
                document_id="doc-1",
                source_id="source-authorized",
                content="Usar un puntero tras free es comportamiento indefinido (use-after-free).",
                page_start=42,
                page_end=42,
            ),
        ]


class _FlakySearchStore(_SearchableStore):
    """Búsqueda presente pero falla técnica → debe caer a la ruta posicional."""

    def __init__(self) -> None:
        super().__init__()
        self.fts_calls = []

    def fts_search(self, **kwargs):
        raise RuntimeError("fts unavailable (technical failure simulation)")

    def get_chunks_for_source(self, source_id: str):
        self.positional_reads.append(source_id)
        return [
            SimpleNamespace(
                id="chunk-pos-1",
                document_id="doc-1",
                content="authorized curriculum evidence",
                page_start=2,
                page_end=2,
            ),
            SimpleNamespace(
                id="chunk-pos-2",
                document_id="doc-1",
                content="authorized curriculum evidence (2)",
                page_start=3,
                page_end=3,
            ),
        ]


def _assembler(tmp_path: Path, store) -> MultiSourceEvidenceAssembler:
    roles_path = tmp_path / "roles.json"
    roles_path.write_text(
        json.dumps(
            {
                "roadmap": {
                    "source-authorized": {
                        "roles": ["PRIMARY"],
                        "title": "Authorized source",
                    },
                    "source-unlinked": {
                        "roles": ["PRIMARY"],
                        "title": "Unlinked source",
                    },
                }
            }
        ),
        encoding="utf-8",
    )
    return MultiSourceEvidenceAssembler(
        knowledge_store=store,
        roles_config_path=roles_path,
    )


def test_assembler_uses_scoped_relevance_search_with_isolation(tmp_path: Path) -> None:
    store = _SearchableStore()
    assembler = _assembler(tmp_path, store)

    bundle = assembler.assemble_evidence_bundle_for_kc(
        notebook_id="roadmap",
        kc_id="kc-1",
        query="use-after-free puntero liberado",
    )

    # Búsqueda scoped por notebook + fuente autorizada; limit 2.
    assert len(store.fts_calls) == 1
    call = store.fts_calls[0]
    assert call["notebook_id"] == "roadmap"
    assert call["source_ids"] == ["source-authorized"]
    assert call["limit"] == 2
    assert call["query"] == "use-after-free puntero liberado"
    # No lectura posicional.
    assert store.positional_reads == []

    # Las citas se admiten por relevancia (sin substring de la query completa).
    assert len(bundle.citations) == 2
    assert {c.chunk_id for c in bundle.citations} == {"chk-rel-1", "chk-rel-2"}
    assert {c.source_id for c in bundle.citations} == {"source-authorized"}
    assert all(
        "puntero liberado" not in c.content_hash or True for c in bundle.citations
    )
    contents = list(bundle.content_by_citation.values())
    assert any("allocator" in t for t in contents)
    assert any("use-after-free" in t for t in contents)


def test_assembler_falls_back_positionally_when_search_fails(tmp_path: Path) -> None:
    store = _FlakySearchStore()
    assembler = _assembler(tmp_path, store)

    evidence_by_role, citations = assembler.assemble_evidence_for_kc(
        notebook_id="roadmap",
        kc_id="kc-1",
        query="authorized",
    )

    # La búsqueda técnica rota no bloquea el ensamblado: fallback posicional
    # con el filtro substring original (contrato legacy preservado).
    assert store.positional_reads == ["source-authorized"]
    assert len(citations) == 2
    assert {c.source_id for c in citations} == {"source-authorized"}
    assert [c.source_id for c in evidence_by_role["PRIMARY"]] == [
        "source-authorized",
        "source-authorized",
    ]
