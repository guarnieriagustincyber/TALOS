"""Academic API Adapters package (Phase E2.8).

Decoupled metadata enrichment adapters for Crossref, OpenAlex, and Zotero.
These tools are auxiliary and strictly outside the generation/verification critical path.
"""

from study_engine.adapters.base import AcademicMetadata, BaseAcademicAdapter
from study_engine.adapters.crossref import CrossrefAdapter
from study_engine.adapters.openalex import OpenAlexAdapter
from study_engine.adapters.zotero import ZoteroAdapter

__all__ = [
    "AcademicMetadata",
    "BaseAcademicAdapter",
    "CrossrefAdapter",
    "OpenAlexAdapter",
    "ZoteroAdapter",
]
