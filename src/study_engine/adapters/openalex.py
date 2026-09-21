"""OpenAlex metadata adapter for academic works and telemetry.

Key Epistemic Principle:
- Citation count != Epistemic Authority.
- Citation counts and concept tags collected here are purely descriptive telemetry metadata.
- Never used to override syllabus authority or document admission gates.
"""

from typing import Any, Dict, List, Optional
import urllib.parse

from study_engine.adapters.base import AcademicMetadata, BaseAcademicAdapter


class OpenAlexAdapter(BaseAcademicAdapter):
    """Adapter for OpenAlex REST API."""

    BASE_URL = "https://api.openalex.org/works"

    def get_work(self, work_id_or_doi: str) -> Optional[AcademicMetadata]:
        """Fetch work metadata by OpenAlex ID (e.g. W2741809807) or DOI."""
        if not work_id_or_doi:
            return None

        clean_id = work_id_or_doi.strip()
        if clean_id.lower().startswith("https://openalex.org/"):
            clean_id = clean_id[21:]

        # If DOI format, OpenAlex accepts "https://doi.org/..." as an identifier
        if "10." in clean_id and not clean_id.startswith("w") and not clean_id.startswith("W"):
            if not clean_id.startswith("https://doi.org/"):
                clean_id = f"https://doi.org/{clean_id}"

        encoded_id = urllib.parse.quote(clean_id, safe="")
        url = f"{self.BASE_URL}/{encoded_id}"

        payload = self.fetch_json(url)
        if not payload:
            return None

        return self._parse_openalex_work(payload)

    def search_works(self, query: str, limit: int = 3) -> List[AcademicMetadata]:
        """Search OpenAlex works by text query."""
        if not query or not query.strip():
            return []

        params = {
            "search": query.strip(),
            "per_page": limit,
        }
        payload = self.fetch_json(self.BASE_URL, params=params)
        if not payload:
            return []

        results = []
        for item in payload.get("results", []):
            meta = self._parse_openalex_work(item)
            if meta:
                results.append(meta)
        return results

    def _parse_openalex_work(self, item: Dict[str, Any]) -> Optional[AcademicMetadata]:
        """Parse OpenAlex JSON item into AcademicMetadata container."""
        title = item.get("display_name") or item.get("title")
        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        year = item.get("publication_year")
        doi = item.get("doi")
        if doi and doi.startswith("https://doi.org/"):
            doi = doi[16:]

        venue = None
        host_venue = item.get("primary_location", {}).get("source", {}) if item.get("primary_location") else {}
        if host_venue:
            venue = host_venue.get("display_name")

        # Telemetry: citation count recorded strictly as metadata
        cited_count = item.get("cited_by_count")

        return AcademicMetadata(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            venue=venue,
            citation_count=cited_count,
            source_adapter="openalex",
            raw_metadata=item,
        )
