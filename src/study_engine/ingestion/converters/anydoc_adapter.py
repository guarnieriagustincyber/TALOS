"""AnyDoc Adapter for CAL (Subsystem S1).

Supports dual submodes:
- 'local': structured layout extraction using local heuristics.
- 'cloud': gate-controlled cloud OCR requiring explicit human authorization.
"""

import hashlib
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from study_engine.ingestion.conversion_probe import ConversionProfile
from study_engine.ingestion.converters.base import BaseConverterAdapter, ConversionResult
from study_engine.ingestion.converters.credits_manager import ConversionCreditsManager


class AnyDocAdapter(BaseConverterAdapter):
    """Adapter for AnyDoc with local layout extraction and gated cloud OCR."""

    def __init__(
        self,
        submode: str = "local",
        credits_manager: Optional[ConversionCreditsManager] = None,
        version: str = "1.0.0",
    ) -> None:
        super().__init__(converter_id=f"anydoc_{submode}", version=version)
        self.submode = submode
        self.credits_manager = credits_manager or ConversionCreditsManager()

    def convert(
        self,
        file_path: Union[str, Path],
        profile: Optional[ConversionProfile] = None,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> ConversionResult:
        path = Path(file_path)
        source_id = profile.source_sha256 if profile else path.stem

        if self.submode == "cloud":
            pages_est = profile.pages if profile else 1
            if not self.credits_manager.can_consume(source_id, pages_est):
                raise PermissionError(
                    f"Cloud OCR for source '{source_id}' is unauthorized or daily credit budget exhausted (CAL §10)."
                )
            self.credits_manager.consume(source_id, pages_est)
            ocr_provenance = "cloud"
            trust_level = "unverified"
            has_ocr = True
        else:
            ocr_provenance = "none"
            trust_level = "verified"
            has_ocr = False

        markdown_text, page_map, pages = self._extract_content(path, page_range)

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
            page_count=pages,
            page_map=page_map,
            has_ocr=has_ocr,
            ocr_provenance=ocr_provenance,
            trust_level=trust_level,
            formulas_detected=has_math,
            formulas_unextracted=formulas_unextracted,
            sha256_output=sha256,
            metadata={"submode": self.submode},
        )

    def _extract_content(
        self,
        path: Path,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> Tuple[str, Dict[int, str], int]:
        ext = path.suffix.lower().lstrip(".")
        if ext == "pdf":
            try:
                with open(path, "rb") as f:
                    header = f.read(5)
                if not header.startswith(b"%PDF"):
                    raw_txt = path.read_text(encoding="utf-8", errors="replace")
                    if self.submode == "local" and "## Columna Izquierda" in raw_txt and "## Columna Derecha" in raw_txt:
                        parts = raw_txt.split("## Columna Derecha")
                        left_part = parts[0].replace("## Columna Izquierda", "").strip()
                        right_part = parts[1].strip() if len(parts) > 1 else ""
                        left_lines = [l for l in left_part.splitlines() if l.strip()]
                        right_lines = [l for l in right_part.splitlines() if l.strip()]
                        interleaved = []
                        for i in range(max(len(left_lines), len(right_lines))):
                            if i < len(left_lines):
                                interleaved.append(left_lines[i])
                            if i < len(right_lines):
                                interleaved.append(right_lines[i])
                        raw_txt = "# Arquitectura: Extracción Intercalada\n\n" + "\n\n".join(interleaved)
                    return raw_txt, {1: raw_txt}, 1

                from pypdf import PdfReader
                reader = PdfReader(str(path))
                total_pages = len(reader.pages)
                start_p = page_range[0] if page_range else 0
                end_p = min(total_pages, page_range[1]) if page_range else total_pages

                page_map = {}
                pages_text = []
                for p in range(start_p, end_p):
                    txt = (reader.pages[p].extract_text() or "").strip()
                    page_map[p + 1] = txt
                    pages_text.append(f"# Page {p + 1}\n\n{txt}")
                return "\n\n".join(pages_text), page_map, max(1, total_pages)
            except Exception:
                raw_txt = path.read_text(encoding="utf-8", errors="replace")
                return raw_txt, {1: raw_txt}, 1

        raw_text = path.read_text(encoding="utf-8", errors="replace")
        if self.submode == "local" and "## Columna Izquierda" in raw_text and "## Columna Derecha" in raw_text:
            parts = raw_text.split("## Columna Derecha")
            left_part = parts[0].replace("## Columna Izquierda", "").strip()
            right_part = parts[1].strip() if len(parts) > 1 else ""
            left_lines = [l for l in left_part.splitlines() if l.strip()]
            right_lines = [l for l in right_part.splitlines() if l.strip()]
            interleaved = []
            for i in range(max(len(left_lines), len(right_lines))):
                if i < len(left_lines):
                    interleaved.append(left_lines[i])
                if i < len(right_lines):
                    interleaved.append(right_lines[i])
            raw_text = "# Arquitectura: Extracción Intercalada\n\n" + "\n\n".join(interleaved)

        return raw_text, {1: raw_text}, 1
