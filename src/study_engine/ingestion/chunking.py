"""Deterministic document chunking engine based on recursive delimiter splitting."""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import Field, model_validator

from study_engine.contracts.base import BaseContract
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document

DEFAULT_DELIMITERS: List[str] = ["\n\n", "\n", ". ", "? ", "! ", "; ", " ", ""]


class ChunkConfig(BaseContract):
    """Configuration for deterministic document chunking."""

    chunk_size: int = Field(default=1000, gt=0, description="Maximum character size per chunk")
    chunk_overlap: int = Field(default=150, ge=0, description="Target character overlap between adjacent chunks")
    delimiters: List[str] = Field(
        default_factory=lambda: list(DEFAULT_DELIMITERS),
        description="Priority list of delimiters for recursive splitting",
    )

    @model_validator(mode="after")
    def validate_overlap(self) -> "ChunkConfig":
        """Enforce strictly positive progress invariant (overlap < chunk_size)."""
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be strictly less than chunk_size.")
        return self


def _recursive_split_with_offsets(
    text: str,
    delimiters: List[str],
    chunk_size: int,
    chunk_overlap: int = 0,
    offset: int = 0,
) -> List[Tuple[str, int, int]]:
    """Split text recursively by delimiter hierarchy, tracking global character offsets."""
    if not delimiters or delimiters[0] == "":
        slices: List[Tuple[str, int, int]] = []
        step = max(1, chunk_size - chunk_overlap) if chunk_overlap > 0 else chunk_size
        for i in range(0, len(text), step):
            slice_text = text[i : i + chunk_size]
            if slice_text:
                slices.append((slice_text, offset + i, offset + i + len(slice_text)))
        return slices

    sep = delimiters[0]
    if sep in text:
        splits = text.split(sep)
        splits_with_sep: List[Tuple[str, int, int]] = []
        curr_offset = offset
        for i, s in enumerate(splits):
            piece_str = s + sep if i < len(splits) - 1 else s
            if piece_str:
                splits_with_sep.append((piece_str, curr_offset, curr_offset + len(piece_str)))
                curr_offset += len(piece_str)
    else:
        splits_with_sep = [(text, offset, offset + len(text))]

    final_pieces: List[Tuple[str, int, int]] = []
    for piece_str, p_start, p_end in splits_with_sep:
        if len(piece_str) > chunk_size:
            final_pieces.extend(
                _recursive_split_with_offsets(
                    piece_str,
                    delimiters[1:],
                    chunk_size,
                    chunk_overlap=chunk_overlap,
                    offset=p_start,
                )
            )
        else:
            if piece_str:
                final_pieces.append((piece_str, p_start, p_end))

    return final_pieces


def _merge_pieces_with_offsets(
    pieces: List[Tuple[str, int, int]],
    chunk_size: int,
    chunk_overlap: int,
) -> List[Tuple[str, int, int]]:
    """Merge small text pieces into bounded chunks with deterministic overlap."""
    chunks: List[Tuple[str, int, int]] = []
    current_doc: List[Tuple[str, int, int]] = []
    total_len = 0

    for piece in pieces:
        piece_str, _, _ = piece
        piece_len = len(piece_str)

        # If piece itself is already chunk_size (from hard slicing), flush current and add piece directly
        if piece_len >= chunk_size:
            if current_doc:
                doc_str = "".join(p[0] for p in current_doc)
                if doc_str:
                    chunks.append((doc_str, current_doc[0][1], current_doc[-1][2]))
                current_doc = []
                total_len = 0
            chunks.append(piece)
            continue

        if total_len + piece_len > chunk_size and current_doc:
            doc_str = "".join(p[0] for p in current_doc)
            if doc_str:
                chunks.append((doc_str, current_doc[0][1], current_doc[-1][2]))

            while current_doc and total_len > chunk_overlap:
                popped = current_doc.pop(0)
                total_len -= len(popped[0])

        current_doc.append(piece)
        total_len += piece_len

    if current_doc:
        doc_str = "".join(p[0] for p in current_doc)
        if doc_str:
            chunks.append((doc_str, current_doc[0][1], current_doc[-1][2]))

    return chunks


def chunk_document(
    document: Document,
    config: Optional[ChunkConfig] = None,
) -> List[Chunk]:
    """Deterministically segment a Document into an ordered list of Chunks.

    Invariants:
        1. Pure function: no side effects, no mutation of input Document.
        2. Returns [] if document content is None or empty/whitespace.
        3. len(chunk.content) <= config.chunk_size for every Chunk.
        4. chunk.token_count is always None.
        5. chunk.id is strictly f"{document.id}:chunk_{index:04d}".
        6. page_start and page_end are None unless explicitly verifiable.
    """
    if not isinstance(document, Document):
        raise TypeError(f"document must be an instance of Document, got {type(document).__name__}")

    if not document.id or not document.id.strip():
        raise ValueError("document.id must be a non-empty string identifier.")

    if not document.source_id or not document.source_id.strip():
        raise ValueError("document.source_id must be a non-empty string identifier.")

    raw_content = document.content
    if raw_content is None or not raw_content or not raw_content.strip():
        return []

    active_config = config if config is not None else ChunkConfig()

    chapter_val: Optional[str] = None
    if "chapter" in document.metadata and isinstance(document.metadata["chapter"], str):
        c_str = document.metadata["chapter"].strip()
        if c_str:
            chapter_val = c_str

    section_val: Optional[str] = None
    if "section" in document.metadata and isinstance(document.metadata["section"], str):
        s_str = document.metadata["section"].strip()
        if s_str:
            section_val = s_str

    # Extract page boundaries if present in metadata
    page_boundaries = []
    if "pdf_metadata" in document.metadata and isinstance(document.metadata["pdf_metadata"], dict):
        page_boundaries = document.metadata["pdf_metadata"].get("page_boundaries", [])
    elif "page_boundaries" in document.metadata and isinstance(document.metadata["page_boundaries"], list):
        page_boundaries = document.metadata["page_boundaries"]

    def _resolve_page_range(c_start: int, c_end: int) -> Tuple[Optional[int], Optional[int]]:
        if not page_boundaries:
            return None, None
        matched_pages = []
        for p in page_boundaries:
            p_num = p.get("page_number")
            p_start = p.get("char_start", 0)
            p_end = p.get("char_end", 0)
            # Check overlap between [c_start, c_end] and [p_start, p_end]
            if max(c_start, p_start) < min(c_end, p_end):
                matched_pages.append(p_num)
        if matched_pages:
            return min(matched_pages), max(matched_pages)
        # Fallback to nearest page if exact overlap is zero-width boundary
        for p in page_boundaries:
            if p.get("char_start", 0) <= c_start <= p.get("char_end", 0):
                return p.get("page_number"), p.get("page_number")
        return None, None

    # Fast path: content fits in a single chunk
    if len(raw_content) <= active_config.chunk_size:
        p_s, p_e = _resolve_page_range(0, len(raw_content))
        single_chunk = Chunk(
            id=f"{document.id}:chunk_0000",
            document_id=document.id,
            source_id=document.source_id,
            content=raw_content,
            page_start=p_s,
            page_end=p_e,
            chapter=chapter_val,
            section=section_val,
            token_count=None,
            index=0,
            metadata={
                "chunking_strategy": "recursive_delimiter",
                "chunk_size": active_config.chunk_size,
                "chunk_overlap": active_config.chunk_overlap,
                "char_start": 0,
                "char_end": len(raw_content),
            },
        )
        return [single_chunk]

    # Recursive split and merge
    pieces = _recursive_split_with_offsets(
        raw_content,
        active_config.delimiters,
        active_config.chunk_size,
        chunk_overlap=active_config.chunk_overlap,
        offset=0,
    )

    merged_chunks = _merge_pieces_with_offsets(
        pieces,
        active_config.chunk_size,
        active_config.chunk_overlap,
    )

    result_chunks: List[Chunk] = []
    for idx, (chunk_text, c_start, c_end) in enumerate(merged_chunks):
        p_s, p_e = _resolve_page_range(c_start, c_end)
        chunk = Chunk(
            id=f"{document.id}:chunk_{idx:04d}",
            document_id=document.id,
            source_id=document.source_id,
            content=chunk_text,
            page_start=p_s,
            page_end=p_e,
            chapter=chapter_val,
            section=section_val,
            token_count=None,
            index=idx,
            metadata={
                "chunking_strategy": "recursive_delimiter",
                "chunk_size": active_config.chunk_size,
                "chunk_overlap": active_config.chunk_overlap,
                "char_start": c_start,
                "char_end": c_end,
            },
        )
        result_chunks.append(chunk)

    return result_chunks


class HierarchicalSemanticChunker:
    """AST/Layout-aware semantic chunker preserving section headers, tables, code, and formulas."""

    def __init__(self, config: Optional[ChunkConfig] = None) -> None:
        self.config = config or ChunkConfig()

    def chunk(self, document: Document) -> List[Chunk]:
        """Chunk document along section boundaries, keeping tables, code and formulas indivisible."""
        if not document.content or not document.content.strip():
            return []

        from study_engine.ingestion.converters.layout_adapter import FormulaDetector
        formula_detector = FormulaDetector()
        raw_text = document.content
        max_size = self.config.chunk_size

        # Regex definitions for indivisible structures and headings
        table_pattern = re.compile(r"(\|[^\n]+\|\n\|[-:\s|]+\|\n(?:\|[^\n]+\|\n?)+)")
        code_pattern = re.compile(r"(```[a-zA-Z0-9_\-]*\n[\s\S]*?```)")
        heading_pattern = re.compile(r"^(#{1,6})\s+([^\n]+)", re.MULTILINE)

        # Split text into structural blocks preserving offsets
        # Identify special ranges: tables, code blocks
        protected_spans: List[Tuple[int, int, str]] = []  # (start, end, type)

        for m in table_pattern.finditer(raw_text):
            protected_spans.append((m.start(), m.end(), "table"))

        for m in code_pattern.finditer(raw_text):
            protected_spans.append((m.start(), m.end(), "code"))

        # Sort spans by start offset
        protected_spans.sort(key=lambda s: s[0])

        # Slice raw_text into chunks of plain text and protected blocks
        segments: List[Tuple[str, str]] = []  # (text, type: "plain" | "table" | "code")
        curr_pos = 0

        for start, end, s_type in protected_spans:
            if start > curr_pos:
                segments.append((raw_text[curr_pos:start], "plain"))
            segments.append((raw_text[start:end], s_type))
            curr_pos = end

        if curr_pos < len(raw_text):
            segments.append((raw_text[curr_pos:], "plain"))

        # Now group segments into section-aware units
        units: List[Dict[str, Any]] = []
        current_h1: Optional[str] = document.metadata.get("chapter")
        current_h2: Optional[str] = document.metadata.get("section")
        current_path: List[str] = []
        if current_h1:
            current_path.append(current_h1)
        if current_h2:
            current_path.append(current_h2)

        for seg_text, seg_type in segments:
            if seg_type in ("table", "code"):
                units.append({
                    "text": seg_text.strip(),
                    "type": seg_type,
                    "indivisible": True,
                    "section_path": " > ".join(current_path) if current_path else None,
                    "chapter": current_h1,
                    "section": current_h2,
                })
            else:
                # Plain text: parse headings and paragraphs
                lines = seg_text.split("\n")
                para_buf: List[str] = []

                for line in lines:
                    h_match = heading_pattern.match(line)
                    if h_match:
                        # Flush existing paragraph
                        if para_buf:
                            p_text = "\n".join(para_buf).strip()
                            if p_text:
                                units.append({
                                    "text": p_text,
                                    "type": "formula" if formula_detector.has_formula(p_text) else "text",
                                    "indivisible": False,
                                    "section_path": " > ".join(current_path) if current_path else None,
                                    "chapter": current_h1,
                                    "section": current_h2,
                                })
                            para_buf = []

                        level = len(h_match.group(1))
                        title = h_match.group(2).strip()

                        if level == 1:
                            current_h1 = title
                            current_path = [title]
                        elif level == 2:
                            current_h2 = title
                            current_path = [current_h1 or "", title] if current_h1 else [title]
                        elif level >= 3:
                            current_path = [p for p in [current_h1, current_h2, title] if p]

                        # Treat heading as transition
                        units.append({
                            "text": line.strip(),
                            "type": "heading",
                            "indivisible": True,
                            "section_path": " > ".join(current_path) if current_path else None,
                            "chapter": current_h1,
                            "section": current_h2,
                        })
                    else:
                        para_buf.append(line)

                if para_buf:
                    p_text = "\n".join(para_buf).strip()
                    if p_text:
                        units.append({
                            "text": p_text,
                            "type": "formula" if formula_detector.has_formula(p_text) else "text",
                            "indivisible": False,
                            "section_path": " > ".join(current_path) if current_path else None,
                            "chapter": current_h1,
                            "section": current_h2,
                        })

        # Assemble units into bounded chunks <= max_size
        chunks_out: List[Chunk] = []
        curr_chunk_texts: List[str] = []
        curr_chunk_len = 0
        curr_chunk_meta: Dict[str, Any] = {
            "has_table": False,
            "has_code": False,
            "has_formula": False,
            "section_path": None,
            "chapter": None,
            "section": None,
        }

        def _flush():
            nonlocal curr_chunk_texts, curr_chunk_len, curr_chunk_meta
            if not curr_chunk_texts:
                return
            full_content = "\n\n".join(curr_chunk_texts).strip()
            if not full_content:
                curr_chunk_texts = []
                curr_chunk_len = 0
                return

            # If content exceeds max_size (e.g. from an oversized indivisible block),
            # split with fallback so invariant len <= max_size is strictly maintained
            if len(full_content) > max_size:
                fallback_pieces = _recursive_split_with_offsets(
                    full_content,
                    self.config.delimiters,
                    max_size,
                    chunk_overlap=self.config.chunk_overlap,
                    offset=0,
                )
                for f_text, _, _ in fallback_pieces:
                    if f_text.strip():
                        idx = len(chunks_out)
                        chunks_out.append(Chunk(
                            id=f"{document.id}:chunk_{idx:04d}",
                            document_id=document.id,
                            source_id=document.source_id,
                            content=f_text.strip(),
                            page_start=None,
                            page_end=None,
                            chapter=curr_chunk_meta["chapter"],
                            section=curr_chunk_meta["section"],
                            token_count=None,
                            index=idx,
                            metadata={
                                "chunking_strategy": "hierarchical_semantic",
                                "chunk_size": max_size,
                                "chunk_overlap": self.config.chunk_overlap,
                                "section_path": curr_chunk_meta["section_path"],
                                "has_table": curr_chunk_meta["has_table"],
                                "has_code": curr_chunk_meta["has_code"],
                                "has_formula": curr_chunk_meta["has_formula"],
                            },
                        ))
            else:
                idx = len(chunks_out)
                chunks_out.append(Chunk(
                    id=f"{document.id}:chunk_{idx:04d}",
                    document_id=document.id,
                    source_id=document.source_id,
                    content=full_content,
                    page_start=None,
                    page_end=None,
                    chapter=curr_chunk_meta["chapter"],
                    section=curr_chunk_meta["section"],
                    token_count=None,
                    index=idx,
                    metadata={
                        "chunking_strategy": "hierarchical_semantic",
                        "chunk_size": max_size,
                        "chunk_overlap": self.config.chunk_overlap,
                        "section_path": curr_chunk_meta["section_path"],
                        "has_table": curr_chunk_meta["has_table"],
                        "has_code": curr_chunk_meta["has_code"],
                        "has_formula": curr_chunk_meta["has_formula"],
                    },
                ))

            curr_chunk_texts = []
            curr_chunk_len = 0
            curr_chunk_meta = {
                "has_table": False,
                "has_code": False,
                "has_formula": False,
                "section_path": None,
                "chapter": None,
                "section": None,
            }

        for u in units:
            u_text = u["text"]
            u_len = len(u_text)
            if not u_text:
                continue

            # Check if heading starts a major new section and we already have content
            if u["type"] == "heading" and curr_chunk_len > max_size // 2:
                _flush()

            # Check if adding this unit exceeds chunk_size
            if curr_chunk_len + u_len + 2 > max_size and curr_chunk_texts:
                _flush()

            curr_chunk_texts.append(u_text)
            curr_chunk_len += u_len + 2

            if u["type"] == "table":
                curr_chunk_meta["has_table"] = True
            elif u["type"] == "code":
                curr_chunk_meta["has_code"] = True
            elif u["type"] == "formula" or formula_detector.has_formula(u_text):
                curr_chunk_meta["has_formula"] = True

            if u.get("section_path"):
                curr_chunk_meta["section_path"] = u["section_path"]
            if u.get("chapter"):
                curr_chunk_meta["chapter"] = u["chapter"]
            if u.get("section"):
                curr_chunk_meta["section"] = u["section"]

        _flush()
        return chunks_out


def chunk_document_hierarchical(
    document: Document,
    config: Optional[ChunkConfig] = None,
) -> List[Chunk]:
    """Convenience entry point for AST and layout-aware hierarchical semantic chunking."""
    return HierarchicalSemanticChunker(config).chunk(document)
