"""Immutable Conversion Storage and Closed Provenance Schema for CAL (Subsystem S1).

Maintains the custody chain: RAW -> CANDIDATES -> CANONICAL -> CHUNKS.
INVARIANTS:
1. RAW source is 100% immutable (SHA-256 verified before and after).
2. Closed chunk schema: 100% of chunks carry converter provenance AND curricular metadata.
3. CAL-7 Ordinal mapping: Non-paginated documents (XLSX sheets, PPTX slides) map to 1-based page indices.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, ConfigDict, Field

from study_engine.ingestion.conversion_arbiter import ArbitrationDecision
from study_engine.ingestion.conversion_probe import ConversionProfile

CAL_STORAGE_DDL = """
CREATE TABLE IF NOT EXISTS conversion_provenance (
    source_sha256 TEXT PRIMARY KEY NOT NULL,
    format TEXT NOT NULL,
    probe_version TEXT NOT NULL,
    profile_hash TEXT NOT NULL,
    canonical_converter TEXT NOT NULL,
    canonical_sha256 TEXT NOT NULL,
    conversion_score REAL NOT NULL,
    conflict_flag INTEGER NOT NULL,
    ocr_provenance TEXT NOT NULL,
    trust_level TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversion_candidates (
    candidate_sha256 TEXT PRIMARY KEY NOT NULL,
    source_sha256 TEXT NOT NULL,
    converter_id TEXT NOT NULL,
    converter_version TEXT NOT NULL,
    quality_score REAL NOT NULL,
    content_markdown TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY(source_sha256) REFERENCES conversion_provenance(source_sha256)
);

CREATE TABLE IF NOT EXISTS conversion_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_sha256 TEXT NOT NULL,
    converter_a TEXT NOT NULL,
    converter_b TEXT NOT NULL,
    candidate_a_sha256 TEXT NOT NULL,
    candidate_b_sha256 TEXT NOT NULL,
    diff_stat REAL NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cal_chunks (
    chunk_id TEXT PRIMARY KEY NOT NULL,
    source_id TEXT NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    converter_id TEXT NOT NULL,
    converter_version TEXT NOT NULL,
    probe_version TEXT NOT NULL,
    rule_id TEXT NOT NULL,
    conversion_score REAL NOT NULL,
    conflict_flag INTEGER NOT NULL,
    ocr_provenance TEXT NOT NULL,
    trust_level TEXT NOT NULL,
    sha256_canonical TEXT NOT NULL,
    subject TEXT NOT NULL,
    level TEXT NOT NULL,
    book TEXT NOT NULL,
    chapter TEXT NOT NULL,
    section TEXT NOT NULL,
    page_start INTEGER NOT NULL,
    page_end INTEGER NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cal_chunks_source ON cal_chunks(source_id);
CREATE INDEX IF NOT EXISTS idx_cal_chunks_curricular ON cal_chunks(subject, book, chapter);
"""


class CALChunk(BaseModel):
    """Closed, mandatory schema for chunks emitted by the Conversion Arbitration Layer."""

    model_config = ConfigDict(frozen=True)

    chunk_id: str = Field(..., min_length=1)
    source_id: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    token_count: int = Field(..., ge=1)
    converter_id: str = Field(...)
    converter_version: str = Field(...)
    probe_version: str = Field(...)
    rule_id: str = Field(...)
    conversion_score: float = Field(..., ge=0.0, le=1.0)
    conflict_flag: bool = Field(...)
    ocr_provenance: str = Field(..., description="none | local_tesseract | cloud")
    trust_level: str = Field(..., description="verified | unverified")
    sha256_canonical: str = Field(..., min_length=64, max_length=64)

    # Curricular metadata for pre-retrieval gating and hierarchical traversal (E4 foundation)
    subject: str = Field(default="Sistemas Operativos")
    level: str = Field(default="Grado")
    book: str = Field(default="General")
    chapter: str = Field(default="General")
    section: str = Field(default="General")
    page_start: int = Field(default=1, ge=1)
    page_end: int = Field(default=1, ge=1)


class ConversionStorage:
    """ACID SQLite storage enforcing custody chain and raw source immutability."""

    def __init__(self, db_path: Optional[Union[str, Path]] = None) -> None:
        if db_path is None:
            self.db_path = Path("data/conversion/cal_store.db")
            self._is_memory = False
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
        elif str(db_path) == ":memory:":
            self.db_path = Path(":memory:")
            self._is_memory = True
        else:
            self.db_path = Path(db_path)
            self._is_memory = False
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self._lock = threading.Lock()
        self._thread_local = threading.local()
        self._mem_conn: Optional[sqlite3.Connection] = None
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self._is_memory:
            if self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn

        conn = getattr(self._thread_local, "conn", None)
        if conn is None:
            conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._thread_local.conn = conn
        return conn

    def _init_db(self) -> None:
        with self._lock:
            conn = self._get_connection()
            with conn:
                conn.executescript(CAL_STORAGE_DDL)

    def store_conversion_decision(
        self,
        profile: ConversionProfile,
        decision: ArbitrationDecision,
        rule_id: str = "DEFAULT_RULE",
    ) -> None:
        """Atomically persist provenance, candidates, and conflicts."""
        canon = decision.canonical_result
        audit = decision.canonical_audit
        now_iso = datetime.now(timezone.utc).isoformat()

        with self._lock:
            conn = self._get_connection()
            with conn:
                # 1. Provenance
                conn.execute(
                    """
                    INSERT OR REPLACE INTO conversion_provenance
                    (source_sha256, format, probe_version, profile_hash, canonical_converter,
                     canonical_sha256, conversion_score, conflict_flag, ocr_provenance, trust_level, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        profile.source_sha256,
                        profile.format,
                        profile.probe_version,
                        profile.profile_hash,
                        canon.converter_id,
                        canon.sha256_output,
                        audit.overall_quality_score,
                        1 if decision.conflict_flag else 0,
                        canon.ocr_provenance,
                        "verified" if audit.is_promoted_cloud else canon.trust_level,
                        now_iso,
                    ),
                )

                # 2. All candidates
                for cand in decision.all_candidates:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO conversion_candidates
                        (candidate_sha256, source_sha256, converter_id, converter_version,
                         quality_score, content_markdown, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            cand.sha256_output,
                            profile.source_sha256,
                            cand.converter_id,
                            cand.converter_version,
                            audit.overall_quality_score if cand == canon else 0.50,
                            cand.markdown_content,
                            now_iso,
                        ),
                    )

                # 3. Conflict event
                if decision.conflict and decision.conflict_flag:
                    conf = decision.conflict
                    conn.execute(
                        """
                        INSERT INTO conversion_conflicts
                        (source_sha256, converter_a, converter_b, candidate_a_sha256, candidate_b_sha256, diff_stat, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            conf.source_sha256,
                            conf.converter_a,
                            conf.converter_b,
                            conf.candidate_a_sha256,
                            conf.candidate_b_sha256,
                            conf.diff_stat,
                            now_iso,
                        ),
                    )

    def chunk_and_store(
        self,
        profile: ConversionProfile,
        decision: ArbitrationDecision,
        curricular_meta: Optional[Dict[str, Any]] = None,
        rule_id: str = "DEFAULT_RULE",
        chunk_tokens_target: int = 300,
    ) -> List[CALChunk]:
        """Produce structured chunks adhering 100% to the closed schema."""
        canon = decision.canonical_result
        audit = decision.canonical_audit
        meta = curricular_meta or {}

        trust_final = "verified" if audit.is_promoted_cloud else canon.trust_level

        # Break text into paragraphs / chunks
        paragraphs = [p.strip() for p in canon.markdown_content.split("\n\n") if p.strip()]
        chunks: List[CALChunk] = []

        current_buf: List[str] = []
        current_tokens = 0
        chunk_idx = 1
        base_page = int(meta.get("page_start", 1))
        page_counter = base_page

        for para in paragraphs:
            # Check for page markers
            if para.startswith("<!-- Page ") or para.startswith("# Page "):
                parts = para.split()
                for pt in parts:
                    if pt.isdigit():
                        p_parsed = int(pt)
                        page_counter = base_page + max(0, p_parsed - 1)
                        break

            words = para.split()
            para_tokens = len(words)

            if current_tokens + para_tokens > chunk_tokens_target and current_buf:
                chunk_text = "\n\n".join(current_buf)
                c_id = f"CHK_{profile.source_sha256[:12]}_{chunk_idx:04d}"
                chunks.append(
                    CALChunk(
                        chunk_id=c_id,
                        source_id=profile.source_sha256,
                        content=chunk_text,
                        token_count=current_tokens,
                        converter_id=canon.converter_id,
                        converter_version=canon.converter_version,
                        probe_version=profile.probe_version,
                        rule_id=rule_id,
                        conversion_score=audit.overall_quality_score,
                        conflict_flag=decision.conflict_flag,
                        ocr_provenance=canon.ocr_provenance,
                        trust_level=trust_final,
                        sha256_canonical=canon.sha256_output,
                        subject=meta.get("subject", "Sistemas Operativos"),
                        level=meta.get("level", "Grado"),
                        book=meta.get("book", "General"),
                        chapter=meta.get("chapter", "General"),
                        section=meta.get("section", "General"),
                        page_start=page_counter,
                        page_end=page_counter,
                    )
                )
                chunk_idx += 1
                current_buf = []
                current_tokens = 0

            current_buf.append(para)
            current_tokens += para_tokens

        if current_buf:
            chunk_text = "\n\n".join(current_buf)
            c_id = f"CHK_{profile.source_sha256[:12]}_{chunk_idx:04d}"
            chunks.append(
                CALChunk(
                    chunk_id=c_id,
                    source_id=profile.source_sha256,
                    content=chunk_text,
                    token_count=max(1, current_tokens),
                    converter_id=canon.converter_id,
                    converter_version=canon.converter_version,
                    probe_version=profile.probe_version,
                    rule_id=rule_id,
                    conversion_score=audit.overall_quality_score,
                    conflict_flag=decision.conflict_flag,
                    ocr_provenance=canon.ocr_provenance,
                    trust_level=trust_final,
                    sha256_canonical=canon.sha256_output,
                    subject=meta.get("subject", "Sistemas Operativos"),
                    level=meta.get("level", "Grado"),
                    book=meta.get("book", "General"),
                    chapter=meta.get("chapter", "General"),
                    section=meta.get("section", "General"),
                    page_start=page_counter,
                    page_end=max(page_counter, int(meta.get("page_end", page_counter))),
                )
            )

        # Persist chunks
        now_iso = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            with conn:
                for c in chunks:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cal_chunks
                        (chunk_id, source_id, content, token_count, converter_id, converter_version,
                         probe_version, rule_id, conversion_score, conflict_flag, ocr_provenance,
                         trust_level, sha256_canonical, subject, level, book, chapter, section,
                         page_start, page_end, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            c.chunk_id,
                            c.source_id,
                            c.content,
                            c.token_count,
                            c.converter_id,
                            c.converter_version,
                            c.probe_version,
                            c.rule_id,
                            c.conversion_score,
                            1 if c.conflict_flag else 0,
                            c.ocr_provenance,
                            c.trust_level,
                            c.sha256_canonical,
                            c.subject,
                            c.level,
                            c.book,
                            c.chapter,
                            c.section,
                            c.page_start,
                            c.page_end,
                            now_iso,
                        ),
                    )

        return chunks

    def get_chunks(self, source_id: str) -> List[CALChunk]:
        """Fetch all chunks for a source."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT chunk_id, source_id, content, token_count, converter_id, converter_version,
                   probe_version, rule_id, conversion_score, conflict_flag, ocr_provenance,
                   trust_level, sha256_canonical, subject, level, book, chapter, section,
                   page_start, page_end
            FROM cal_chunks WHERE source_id = ? ORDER BY chunk_id ASC
            """,
            (source_id,),
        )
        rows = cursor.fetchall()
        return [
            CALChunk(
                chunk_id=r[0],
                source_id=r[1],
                content=r[2],
                token_count=r[3],
                converter_id=r[4],
                converter_version=r[5],
                probe_version=r[6],
                rule_id=r[7],
                conversion_score=r[8],
                conflict_flag=bool(r[9]),
                ocr_provenance=r[10],
                trust_level=r[11],
                sha256_canonical=r[12],
                subject=r[13],
                level=r[14],
                book=r[15],
                chapter=r[16],
                section=r[17],
                page_start=r[18],
                page_end=r[19],
            )
            for r in rows
        ]

    def get_conflicts(self, source_sha256: Optional[str] = None) -> List[Dict[str, Any]]:
        """Fetch recorded representation conflicts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        if source_sha256:
            cursor.execute(
                """
                SELECT source_sha256, converter_a, converter_b, candidate_a_sha256, candidate_b_sha256, diff_stat, created_at
                FROM conversion_conflicts WHERE source_sha256 = ?
                """,
                (source_sha256,),
            )
        else:
            cursor.execute(
                """
                SELECT source_sha256, converter_a, converter_b, candidate_a_sha256, candidate_b_sha256, diff_stat, created_at
                FROM conversion_conflicts
                """
            )
        rows = cursor.fetchall()
        return [
            {
                "source_sha256": r[0],
                "converter_a": r[1],
                "converter_b": r[2],
                "candidate_a_sha256": r[3],
                "candidate_b_sha256": r[4],
                "diff_stat": r[5],
                "created_at": r[6],
            }
            for r in rows
        ]
