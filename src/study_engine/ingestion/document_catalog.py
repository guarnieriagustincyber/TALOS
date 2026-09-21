"""DocumentCatalog: in-memory deterministic catalog for registering and querying documents."""

from typing import Any, Dict, List, Optional

from study_engine.contracts.catalog import (
    DocumentConflictError,
    DocumentNotFoundError,
    SourceNotFoundError,
)
from study_engine.contracts.document import Document
from study_engine.ingestion.catalog import SourceCatalog


class DocumentCatalog:
    """Deterministic in-memory catalog managing document registration, identity, and queries."""

    def __init__(self, source_catalog: Optional[SourceCatalog] = None) -> None:
        self._documents: Dict[str, Document] = {}
        self._source_catalog: Optional[SourceCatalog] = source_catalog

    def register(self, document: Document) -> Document:
        """Register a Document into the catalog.

        Defensive Copying:
            Stores and returns independent deep copies of the Document to prevent
            external in-memory state mutation.

        Idempotency:
            If a document with the same id and semantically identical attributes already exists,
            an independent deep copy of the existing document is returned without duplication.

        Conflicts:
            If a document with the same id exists with differing attributes,
            DocumentConflictError is raised.

        Referential Integrity:
            If initialized with a source_catalog, validates that document.source_id is registered
            in the source catalog. Raises SourceNotFoundError if missing.

        Returns:
            Document: An independent deep copy of the registered Document.

        Raises:
            SourceNotFoundError: If source_catalog is configured and document.source_id is not found.
            DocumentConflictError: When incoming document conflicts with an existing registered document.
            ValueError: If document is not a valid Document instance.
        """
        if not isinstance(document, Document):
            raise ValueError("document must be an instance of Document contract.")

        if self._source_catalog is not None and not self._source_catalog.contains(document.source_id):
            raise SourceNotFoundError(document.source_id)

        document_id = document.id
        if document_id in self._documents:
            existing = self._documents[document_id]
            if existing == document:
                return existing.model_copy(deep=True)
            raise DocumentConflictError(
                document_id=document_id,
                reason="Semantic divergence detected for existing document: incoming attributes differ from registered document.",
            )

        stored = document.model_copy(deep=True)
        self._documents[document_id] = stored
        return stored.model_copy(deep=True)

    def get(self, document_id: str) -> Document:
        """Retrieve an independent deep copy of a registered Document by its logical id.

        Raises:
            DocumentNotFoundError: If document_id is not found in the catalog.
        """
        if document_id not in self._documents:
            raise DocumentNotFoundError(document_id)
        return self._documents[document_id].model_copy(deep=True)

    def get_optional(self, document_id: str) -> Optional[Document]:
        """Retrieve an independent deep copy of a registered Document or None if not found."""
        doc = self._documents.get(document_id)
        return doc.model_copy(deep=True) if doc is not None else None

    def contains(self, document_id: str) -> bool:
        """Return True if document_id is registered in the catalog."""
        return document_id in self._documents

    def find_by_source_id(self, source_id: str) -> List[Document]:
        """Find all registered documents belonging to a given source_id, sorted deterministically by document id."""
        return [
            doc.model_copy(deep=True)
            for doc in sorted(self._documents.values(), key=lambda d: d.id)
            if doc.source_id == source_id
        ]

    def list_documents(self) -> List[Document]:
        """Return all registered documents sorted deterministically by document id (deep copied)."""
        return [
            doc.model_copy(deep=True)
            for doc in sorted(self._documents.values(), key=lambda d: d.id)
        ]

    def count(self) -> int:
        """Return the number of documents currently registered in the catalog."""
        return len(self._documents)

    def clear(self) -> None:
        """Clear all registered documents from the in-memory catalog."""
        self._documents.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the catalog state to a dictionary."""
        return {
            "records": {
                doc_id: doc.model_dump()
                for doc_id, doc in sorted(self._documents.items())
            }
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        source_catalog: Optional[SourceCatalog] = None,
    ) -> "DocumentCatalog":
        """Reconstruct a DocumentCatalog from a serialized dictionary state.

        Validation Rules:
            - data must be a dictionary/mapping.
            - 'records' key must be present and must be a mapping.
            - Each record payload must be a valid Document representation.
            - outer_key must match doc.id exactly (identity invariant).
            - If source_catalog is provided, each doc.source_id must exist in source_catalog.

        Raises:
            ValueError: If data structure, outer key, or identity invariant is violated.
            SourceNotFoundError: If source_catalog is provided and a document references a missing source.
            pydantic.ValidationError: If record payload is structurally invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("Catalog snapshot data must be a dictionary/mapping.")

        if "records" not in data or not isinstance(data["records"], dict):
            raise ValueError("Catalog snapshot must contain a 'records' dictionary/mapping.")

        catalog = cls(source_catalog=source_catalog)
        records_data = data["records"]
        for outer_key, record_dict in sorted(records_data.items()):
            if not isinstance(outer_key, str) or not outer_key.strip():
                raise ValueError("Document record key must be a non-empty string.")
            if record_dict is None or not isinstance(record_dict, (dict, Document)):
                raise ValueError(f"Record payload for key '{outer_key}' must be a dictionary mapping.")

            doc = (
                record_dict.model_copy(deep=True)
                if isinstance(record_dict, Document)
                else Document.model_validate(record_dict)
            )

            if doc.id != outer_key:
                raise ValueError(
                    f"Snapshot identity mismatch: outer key '{outer_key}' does not match document id '{doc.id}'."
                )

            if source_catalog is not None and not source_catalog.contains(doc.source_id):
                raise SourceNotFoundError(doc.source_id)

            catalog._documents[outer_key] = doc.model_copy(deep=True)

        return catalog
