"""Crossref metadata adapter for scholarly works.

Key Architectural Principles:
- DOI is NEVER mandatory for corpus admission.
- Enriches metadata when a DOI is available or through bibliographic title search.
- Hermetic: operates with caching and offline fallback.
"""

from typing import Any, Dict, List, Optional
import urllib.parse

from study_engine.adapters.base import AcademicMetadata, BaseAcademicAdapter


class CrossrefAdapter(BaseAcademicAdapter):
    """Adapter for Crossref REST API."""

    BASE_URL = "https://api.crossref.org/works"

    def resolve_doi(self, doi: str) -> Optional[AcademicMetadata]:
        """Resolve a DOI against Crossref to extract bibliographic metadata."""
        if not doi:
            return None

        clean_doi = doi.strip()
        if clean_doi.lower().startswith("https://doi.org/"):
            clean_doi = clean_doi[16:]
        elif clean_doi.lower().startswith("http://doi.org/"):
            clean_doi = clean_doi[15:]
        elif clean_doi.lower().startswith("doi:"):
            clean_doi = clean_doi[4:]

        encoded_doi = urllib.parse.quote(clean_doi, safe="")
        url = f"{self.BASE_URL}/{encoded_doi}"

        payload = self.fetch_json(url)
        if not payload or payload.get("status") != "ok":
            return None

        message = payload.get("message", {})
        return self._parse_crossref_message(message)

    def search_by_title(self, title: str, rows: int = 3) -> List[AcademicMetadata]:
        """Search Crossref works by bibliographic query string."""
        if not title or not title.strip():
            return []

        params = {
            "query.bibliographic": title.strip(),
            "rows": rows,
        }
        payload = self.fetch_json(self.BASE_URL, params=params)
        if not payload or payload.get("status") != "ok":
            return []

        items = payload.get("message", {}).get("items", [])
        results = []
        for item in items:
            meta = self._parse_crossref_message(item)
            if meta:
                results.append(meta)
        return results

    def _parse_crossref_message(self, message: Dict[str, Any]) -> Optional[AcademicMetadata]:
        """Extract standardized AcademicMetadata from Crossref message payload."""
        titles = message.get("title", [])
        title = titles[0] if titles else message.get("subtitle", [""])[0] if message.get("subtitle") else None

        authors = []
        for author in message.get("author", []):
            family = author.get("family", "")
            given = author.get("given", "")
            if family and given:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)

        year = None
        date_parts = (
            message.get("published-print", {}).get("date-parts")
            or message.get("published-online", {}).get("date-parts")
            or message.get("created", {}).get("date-parts")
        )
        if date_parts and len(date_parts) > 0 and len(date_parts[0]) > 0:
            year = date_parts[0][0]

        venue = None
        containers = message.get("container-title", [])
        if containers:
            venue = containers[0]

        return AcademicMetadata(
            title=title,
            authors=authors,
            year=year,
            doi=message.get("DOI"),
            venue=venue,
            citation_count=message.get("is-referenced-by-count"),
            source_adapter="crossref",
            raw_metadata=message,
        )
