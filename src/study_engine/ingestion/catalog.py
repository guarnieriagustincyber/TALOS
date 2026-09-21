"""SourceCatalog: in-memory deterministic catalog for registering and querying knowledge sources."""

from typing import Any, Dict, List, Optional

from study_engine.contracts.catalog import (
    SourceConflictError,
    SourceNotFoundError,
    SourceRecord,
)
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source


def _is_semantically_equivalent(r1: SourceRecord, r2: SourceRecord) -> bool:
    """Check full semantic equivalence between two records, allowing case-insensitive SHA comparison."""
    if r1.source_id != r2.source_id:
        return False
    if r1.source != r2.source:
        return False
    if r1.metadata != r2.metadata:
        return False
    m1, m2 = r1.manifest, r2.manifest
    return (
        m1.source_id == m2.source_id
        and m1.filename == m2.filename
        and m1.byte_size == m2.byte_size
        and m1.file_path == m2.file_path
        and m1.media_type == m2.media_type
        and m1.metadata == m2.metadata
        and m1.sha256.lower() == m2.sha256.lower()
    )


class SourceCatalog:
    """Deterministic catalog managing logical source registration, identity, and physical manifests."""

    def __init__(self) -> None:
        self._records: Dict[str, SourceRecord] = {}

    def register(
        self,
        manifest: SourceManifest,
        source: Optional[Source] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SourceRecord:
        """Register a source manifest into the catalog.

        Defensive Copying:
            Stores and returns independent deep copies of the records to prevent external
            state corruption.

        Idempotency:
            If an equivalent record with the same source_id and SHA-256 already exists,
            an independent deep copy of the existing record is returned without duplication.

        Conflicts and Semantic Divergence:
            - If source_id exists with a different SHA-256 hash, SourceConflictError is raised.
            - If source_id exists with identical SHA-256 but divergent manifest metadata,
              conceptual Source entity, or catalog metadata, SourceConflictError is raised.

        Returns:
            SourceRecord: An independent deep copy of the registered catalog entry.

        Raises:
            SourceConflictError: When incoming SHA-256 conflicts or semantic divergence is detected.
            ValueError: If manifest is invalid or source_id mismatched.
        """
        source_id = manifest.source_id
        candidate = SourceRecord(
            source_id=source_id,
            manifest=manifest.model_copy(deep=True),
            source=source.model_copy(deep=True) if source is not None else None,
            metadata=dict(metadata) if metadata else {},
        )

        if source_id in self._records:
            existing = self._records[source_id]
            if existing.manifest.sha256.lower() != manifest.sha256.lower():
                raise SourceConflictError(
                    source_id=source_id,
                    existing_sha256=existing.manifest.sha256,
                    new_sha256=manifest.sha256,
                )
            if _is_semantically_equivalent(candidate, existing):
                return existing.model_copy(deep=True)

            raise SourceConflictError(
                source_id=source_id,
                existing_sha256=existing.manifest.sha256,
                new_sha256=manifest.sha256,
                reason=(
                    "Semantic divergence detected for existing source: incoming metadata, "
                    "conceptual source, or manifest attributes differ from registered record."
                ),
            )

        stored = candidate.model_copy(deep=True)
        self._records[source_id] = stored
        return stored.model_copy(deep=True)

    def register_manifest(
        self,
        manifest: SourceManifest,
        source: Optional[Source] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> SourceRecord:
        """Convenience alias for register."""
        return self.register(manifest=manifest, source=source, metadata=metadata)

    def get(self, source_id: str) -> SourceRecord:
        """Retrieve an independent deep copy of a registered SourceRecord by its logical source_id.

        Raises:
            SourceNotFoundError: If source_id is not in the catalog.
        """
        if source_id not in self._records:
            raise SourceNotFoundError(source_id)
        return self._records[source_id].model_copy(deep=True)

    def get_optional(self, source_id: str) -> Optional[SourceRecord]:
        """Retrieve an independent deep copy of a registered SourceRecord or None if not found."""
        record = self._records.get(source_id)
        return record.model_copy(deep=True) if record is not None else None

    def contains(self, source_id: str) -> bool:
        """Return True if source_id is registered in the catalog."""
        return source_id in self._records

    def find_by_sha256(self, sha256: str) -> List[SourceRecord]:
        """Find all registered sources matching a given physical SHA-256 hash (deep copied)."""
        target_hash = sha256.lower()
        return [
            record.model_copy(deep=True)
            for record in sorted(self._records.values(), key=lambda r: r.source_id)
            if record.manifest.sha256.lower() == target_hash
        ]

    def list_sources(self) -> List[SourceRecord]:
        """Return all registered source records sorted deterministically by source_id (deep copied)."""
        return [
            record.model_copy(deep=True)
            for record in sorted(self._records.values(), key=lambda r: r.source_id)
        ]

    def count(self) -> int:
        """Return the number of sources currently registered in the catalog."""
        return len(self._records)

    def clear(self) -> None:
        """Clear all registered sources from the in-memory catalog."""
        self._records.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the catalog state to a dictionary."""
        return {
            "records": {
                source_id: record.model_dump()
                for source_id, record in sorted(self._records.items())
            }
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SourceCatalog":
        """Reconstruct a SourceCatalog from a serialized dictionary state.

        Validation Rules:
            - data must be a dictionary/mapping.
            - 'records' key must be present and must be a mapping.
            - Each record payload must be a valid SourceRecord representation.
            - outer_key must match record.source_id exactly (identity invariant).

        Raises:
            ValueError: If data structure or identity invariant is violated.
            pydantic.ValidationError: If record payload is structurally invalid.
        """
        if not isinstance(data, dict):
            raise ValueError("Catalog snapshot data must be a dictionary/mapping.")

        if "records" not in data or not isinstance(data["records"], dict):
            raise ValueError("Catalog snapshot must contain a 'records' dictionary/mapping.")

        catalog = cls()
        records_data = data["records"]
        for outer_key, record_dict in sorted(records_data.items()):
            if not isinstance(outer_key, str) or not outer_key.strip():
                raise ValueError("Catalog record key must be a non-empty string.")
            if record_dict is None or not isinstance(record_dict, (dict, SourceRecord)):
                raise ValueError(f"Record payload for key '{outer_key}' must be a dictionary mapping.")

            record = (
                record_dict.model_copy(deep=True)
                if isinstance(record_dict, SourceRecord)
                else SourceRecord.model_validate(record_dict)
            )

            if record.source_id != outer_key:
                raise ValueError(
                    f"Snapshot identity mismatch: outer key '{outer_key}' does not match record source_id '{record.source_id}'."
                )

            catalog._records[outer_key] = record.model_copy(deep=True)

        return catalog
