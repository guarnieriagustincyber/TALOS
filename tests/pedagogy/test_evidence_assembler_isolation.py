"""Evidence assembly must stay inside registered notebook-source links."""

import json
from pathlib import Path
from types import SimpleNamespace

from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler


class _Store:
    def __init__(self, chunk_count: int = 2) -> None:
        self.source_reads: list[str] = []
        self.chunk_count = chunk_count

    def get_notebook(self, notebook_id: str) -> SimpleNamespace:
        assert notebook_id == "roadmap"
        return SimpleNamespace(sources=["source-authorized"])

    def get_chunks_for_source(self, source_id: str) -> list[SimpleNamespace]:
        self.source_reads.append(source_id)
        return [
            SimpleNamespace(
                id=f"chunk-{source_id}-{index}",
                document_id=f"doc-{source_id}",
                content="authorized curriculum evidence",
                page_start=2,
                page_end=2,
            )
            for index in range(self.chunk_count)
        ]

    def list_sources(self) -> list[SimpleNamespace]:
        raise AssertionError("Evidence fallback must not enumerate global sources")


def test_evidence_assembly_intersects_roles_with_notebook_source_allowlist(
    tmp_path: Path,
) -> None:
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
    store = _Store()
    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store,
        roles_config_path=roles_path,
    )

    evidence_by_role, citations = assembler.assemble_evidence_for_kc(
        notebook_id="roadmap",
        kc_id="kc-1",
        query="authorized",
    )

    assert store.source_reads == ["source-authorized"]
    assert len(citations) == 2
    assert {citation.source_id for citation in citations} == {"source-authorized"}
    assert [citation.source_id for citation in evidence_by_role["PRIMARY"]] == [
        "source-authorized",
        "source-authorized",
    ]


def test_insufficient_authorized_evidence_does_not_fall_back_globally(
    tmp_path: Path,
) -> None:
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
    store = _Store(chunk_count=1)
    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store,
        roles_config_path=roles_path,
    )

    evidence_by_role, citations = assembler.assemble_evidence_for_kc(
        notebook_id="roadmap",
        kc_id="kc-1",
        query="authorized",
    )

    assert store.source_reads == ["source-authorized"]
    assert citations == []
    assert all(not evidence for evidence in evidence_by_role.values())
