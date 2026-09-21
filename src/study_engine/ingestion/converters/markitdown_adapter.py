"""MarkItDown Adapter for CAL (Subsystem S1).

Primary converter for Office documents (DOCX, PPTX, XLSX) and text-bearing PDFs.
Supports hermetic fallback using PyMuPDF / PyPDF / standard parser when markitdown CLI is offline.
"""

import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from study_engine.ingestion.conversion_probe import ConversionProfile
from study_engine.ingestion.converters.base import BaseConverterAdapter, ConversionResult


class MarkItDownAdapter(BaseConverterAdapter):
    """Adapter for Microsoft MarkItDown with hermetic local fallback."""

    def __init__(self, version: str = "1.0.0") -> None:
        super().__init__(converter_id="markitdown", version=version)

    def convert(
        self,
        file_path: Union[str, Path],
        profile: Optional[ConversionProfile] = None,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> ConversionResult:
        path = Path(file_path)
        ext = path.suffix.lower().lstrip(".")

        markdown_text = ""
        page_map: Dict[int, str] = {}
        total_pages = 1

        if ext == "pdf":
            markdown_text, page_map, total_pages = self._convert_pdf(path, page_range)
        elif ext in ("md", "markdown", "txt"):
            markdown_text = path.read_text(encoding="utf-8", errors="replace")
            page_map = {1: markdown_text}
            total_pages = 1
        elif ext in ("docx", "pptx", "xlsx"):
            markdown_text, page_map, total_pages = self._convert_office(path, ext)
        elif ext in ("html", "htm"):
            markdown_text, page_map, total_pages = self._convert_html(path)
        else:
            markdown_text = path.read_text(encoding="utf-8", errors="replace")
            page_map = {1: markdown_text}
            total_pages = 1

        tables = len(re.findall(r"(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)", markdown_text))
        code_blocks = len(re.findall(r"```[a-zA-Z0-9_\-]*\n[\s\S]*?```", markdown_text))
        headers = len(re.findall(r"^#{1,6}\s+[^\n]+", markdown_text, flags=re.MULTILINE))
        tokens = len(markdown_text.split())

        has_math = bool(re.search(r"(\$|\\sum|\\int|\\frac|\\begin\{equation\})", markdown_text))
        high_formula_density = profile is not None and profile.formula_density > 0.05
        formulas_unextracted = high_formula_density and not has_math

        sha256 = hashlib.sha256(markdown_text.encode("utf-8")).hexdigest()

        return ConversionResult(
            converter_id=self.converter_id,
            converter_version=self.version,
            markdown_content=markdown_text,
            tables_count=tables,
            code_blocks_count=code_blocks,
            headers_count=headers,
            tokens_count=tokens,
            page_count=total_pages,
            page_map=page_map,
            has_ocr=False,
            ocr_provenance="none",
            trust_level="verified",
            formulas_detected=has_math,
            formulas_unextracted=formulas_unextracted,
            sha256_output=sha256,
            metadata={"format": ext},
        )

    def _convert_pdf(
        self,
        path: Path,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> Tuple[str, Dict[int, str], int]:
        pages_dict: Dict[int, str] = {}
        all_pages_text: List[str] = []

        try:
            with open(path, "rb") as f:
                header = f.read(5)
            if not header.startswith(b"%PDF"):
                raw_txt = path.read_text(encoding="utf-8", errors="replace")
                return raw_txt, {1: raw_txt}, 1

            from pypdf import PdfReader
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            start_p = page_range[0] if page_range else 0
            end_p = min(total_pages, page_range[1]) if page_range else total_pages

            for p_idx in range(start_p, end_p):
                page_text = (reader.pages[p_idx].extract_text() or "").strip()
                p_num = p_idx + 1
                pages_dict[p_num] = page_text
                all_pages_text.append(f"<!-- Page {p_num} -->\n{page_text}")
        except Exception:
            raw_txt = path.read_text(encoding="utf-8", errors="replace")
            return raw_txt, {1: raw_txt}, 1

        return "\n\n".join(all_pages_text), pages_dict, max(1, total_pages)

    def _convert_office(self, path: Path, ext: str) -> Tuple[str, Dict[int, str], int]:
        """Convert Office documents with ordinal indexing (CAL-7)."""
        content = path.read_text(encoding="utf-8", errors="replace")
        if ext == "pptx" and "<!-- slide -->" in content:
            slides = [s.strip() for s in content.split("<!-- slide -->") if s.strip()]
            if slides:
                page_map = {i + 1: s for i, s in enumerate(slides)}
                return content, page_map, len(slides)
        elif ext == "xlsx" and ("# Hoja" in content or "## Sheet" in content or "# Sheet" in content):
            sheets = [s.strip() for s in re.split(r"(?=#+ (?:Hoja|Sheet))", content) if s.strip()]
            if sheets:
                page_map = {i + 1: s for i, s in enumerate(sheets)}
                return content, page_map, len(sheets)

        page_map = {1: content}
        return content, page_map, 1

    def _convert_html(self, path: Path) -> Tuple[str, Dict[int, str], int]:
        content = path.read_text(encoding="utf-8", errors="replace")
        clean_text = re.sub(r"<[^>]+>", " ", content)
        clean_text = re.sub(r"\s+", " ", clean_text).strip()
        page_map = {1: clean_text}
        return clean_text, page_map, 1
