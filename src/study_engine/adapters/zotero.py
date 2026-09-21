"""Zotero library and collection metadata adapter.

Supports ingesting bibliographic records from:
- Zotero Web API (via user/group library endpoint)
- Local Zotero JSON/CSL export files
- Local SQLite database caches
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.parse

from study_engine.adapters.base import AcademicMetadata, BaseAcademicAdapter


class ZoteroAdapter(BaseAcademicAdapter):
    """Adapter for Zotero Web API and local export ingestion."""

    BASE_URL = "https://api.zotero.org"

    def __init__(
        self,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        cache_db_path: Optional[Path] = None,
        timeout_seconds: float = 5.0,
    ) -> None:
        super().__init__(cache_db_path=cache_db_path, timeout_seconds=timeout_seconds)
        self.user_id = user_id
        self.api_key = api_key

    def get_items(self, collection_id: Optional[str] = None, limit: int = 50) -> List[AcademicMetadata]:
        """Fetch items from Zotero user library or specific collection."""
        if not self.user_id:
            return []

        if collection_id:
            url = f"{self.BASE_URL}/users/{self.user_id}/collections/{collection_id}/items"
        else:
            url = f"{self.BASE_URL}/users/{self.user_id}/items"

        params = {"limit": limit, "format": "json"}
        headers = {}
        if self.api_key:
            headers["Zotero-API-Key"] = self.api_key

        payload = self.fetch_json(url, params=params, headers=headers)
        if not payload or not isinstance(payload, list):
            return []

        results = []
        for item in payload:
            meta = self._parse_zotero_item(item)
            if meta:
                results.append(meta)
        return results

    def parse_export_file(self, export_path: Path) -> List[AcademicMetadata]:
        """Parse local Zotero JSON / CSL export file."""
        if not export_path.exists():
            return []

        try:
            with open(export_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return []

        items = data if isinstance(data, list) else data.get("items", [data])
        results = []
        for item in items:
            meta = self._parse_zotero_item(item)
            if meta:
                results.append(meta)
        return results

    def _parse_zotero_item(self, item: Dict[str, Any]) -> Optional[AcademicMetadata]:
        """Parse Zotero item dictionary into AcademicMetadata."""
        data = item.get("data", item)  # Zotero API wraps fields in 'data'
        title = data.get("title")
        if not title:
            return None

        authors = []
        creators = data.get("creators", [])
        for c in creators:
            first = c.get("firstName", "")
            last = c.get("lastName", "")
            name = c.get("name", "")
            if first and last:
                authors.append(f"{first} {last}")
            elif last:
                authors.append(last)
            elif name:
                authors.append(name)

        year = None
        date_str = data.get("date", "")
        if date_str:
            for part in date_str.split("-"):
                part_clean = part.strip()
                if len(part_clean) == 4 and part_clean.isdigit():
                    year = int(part_clean)
                    break

        venue = data.get("publicationTitle") or data.get("publisher") or data.get("proceedingsTitle")
        doi = data.get("DOI")

        return AcademicMetadata(
            title=title,
            authors=authors,
            year=year,
            doi=doi,
            venue=venue,
            citation_count=None,
            source_adapter="zotero",
            raw_metadata=item,
        )
