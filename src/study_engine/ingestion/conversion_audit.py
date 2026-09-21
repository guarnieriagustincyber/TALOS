"""Extended P4 Quality Audit for CAL (Subsystem S1).

Evaluates structural integrity, token yield, readability, and enforces cloud promotion thresholds (CAL-3).
INVARIANTS:
1. Purely deterministic and reproducible without LLMs.
2. Preserves legacy P4 low-OCR threshold (readable/total < 0.75 or length < 40).
3. Cloud OCR chunks require reinforced threshold (tau_cloud = 0.85 > tau_local = 0.75) for promotion (CAL-3).
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from study_engine.ingestion.converters.base import ConversionResult

DEFAULT_WEIGHTS = {
    "w_readability": 0.30,
    "w_tables": 0.25,
    "w_code": 0.20,
    "w_headers": 0.15,
    "w_yield": 0.10,
}

TAU_LOCAL_ADMISSION = 0.75
TAU_CLOUD_REINFORCED = 0.85
TAU_DEGRADED_MIN = 0.40


class AuditStatus(str, Enum):
    """Outcome status of the conversion audit."""

    PASSED = "PASSED"
    LOW_OCR = "LOW_OCR"
    SOURCE_DEGRADED = "SOURCE_DEGRADED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class ConversionAuditReport(BaseModel):
    """Comprehensive structural and lexical audit report for converted content."""

    model_config = ConfigDict(frozen=True)

    readability_score: float = Field(..., ge=0.0, le=1.0)
    table_integrity: float = Field(..., ge=0.0, le=1.0)
    code_integrity: float = Field(..., ge=0.0, le=1.0)
    header_hierarchy: float = Field(..., ge=0.0, le=1.0)
    yield_tokens_per_page: float = Field(..., ge=0.0, le=1.0)
    overall_quality_score: float = Field(..., ge=0.0, le=1.0)
    status: AuditStatus = Field(...)
    is_promoted_cloud: bool = Field(default=False)
    audit_notes: List[str] = Field(default_factory=list)


class ConversionAuditor:
    """Evaluates conversion output against structural and lexical standards."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        tau_local: float = TAU_LOCAL_ADMISSION,
        tau_cloud: float = TAU_CLOUD_REINFORCED,
        tau_min: float = TAU_DEGRADED_MIN,
    ) -> None:
        self.weights = weights or dict(DEFAULT_WEIGHTS)
        self.tau_local = tau_local
        self.tau_cloud = tau_cloud
        self.tau_min = tau_min

    def audit(
        self,
        conversion_result: ConversionResult,
        expected_pages: int = 1,
    ) -> ConversionAuditReport:
        text = conversion_result.markdown_content
        notes: List[str] = []

        # 1. Readability & Legacy P4 Check
        total_chars = len(text)
        if total_chars == 0 or total_chars < 40:
            return ConversionAuditReport(
                readability_score=0.0,
                table_integrity=1.0,
                code_integrity=1.0,
                header_hierarchy=1.0,
                yield_tokens_per_page=0.0,
                overall_quality_score=0.0,
                status=AuditStatus.LOW_OCR,
                is_promoted_cloud=False,
                audit_notes=["Total character count < 40 (Legacy P4 trigger)."],
            )

        printable_count = sum(1 for ch in text if ch.isalnum() or ch in " .,;:!?¡¿()[]{}'\"-_+=*/\\@#$%^&|~`\n\t")
        readability = printable_count / total_chars
        if readability < 0.75:
            notes.append(f"Readability ratio {readability:.2f} < 0.75 (Legacy P4 trigger).")

        # 2. Table Integrity
        table_score = self._evaluate_tables(text)

        # 3. Code Block Integrity
        code_score = self._evaluate_code_blocks(text)

        # 4. Header Hierarchy Integrity
        header_score = self._evaluate_headers(text)

        # 5. Token Yield per Page
        yield_score = self._evaluate_yield(len(text.split()), max(1, expected_pages))

        # Composite score
        w = self.weights
        overall_score = (
            w["w_readability"] * readability
            + w["w_tables"] * table_score
            + w["w_code"] * code_score
            + w["w_headers"] * header_score
            + w["w_yield"] * yield_score
        )
        overall_score = max(0.0, min(1.0, overall_score))

        # Determine status
        if readability < 0.75:
            status = AuditStatus.LOW_OCR
        elif overall_score < self.tau_min:
            status = AuditStatus.SOURCE_DEGRADED
        elif overall_score >= self.tau_local:
            status = AuditStatus.PASSED
        else:
            status = AuditStatus.SOURCE_DEGRADED

        # Cloud Promotion Rule (CAL-3)
        is_promoted = False
        if conversion_result.ocr_provenance == "cloud" and conversion_result.trust_level == "unverified":
            if (
                overall_score >= self.tau_cloud
                and table_score >= 0.90
                and code_score == 1.0
                and readability >= 0.85
            ):
                is_promoted = True
                notes.append("Cloud OCR passed reinforced P4 audit: promoted to trust=verified.")
            else:
                notes.append(f"Cloud OCR retained as unverified (score {overall_score:.2f} < tau_cloud {self.tau_cloud}).")

        return ConversionAuditReport(
            readability_score=round(readability, 4),
            table_integrity=round(table_score, 4),
            code_integrity=round(code_score, 4),
            header_hierarchy=round(header_score, 4),
            yield_tokens_per_page=round(yield_score, 4),
            overall_quality_score=round(overall_score, 4),
            status=status,
            is_promoted_cloud=is_promoted,
            audit_notes=notes,
        )

    def _evaluate_tables(self, text: str) -> float:
        """Check if Markdown tables are well-formed."""
        lines = text.splitlines()
        pipe_lines = [line.strip() for line in lines if line.strip().startswith("|") or line.count("|") >= 2]
        if not pipe_lines:
            return 1.0

        # Any line starting with '|' must also end with '|'
        if any(l.startswith("|") and not l.endswith("|") for l in pipe_lines):
            return 0.40

        table_lines = [l for l in pipe_lines if l.startswith("|") and l.endswith("|")]
        has_separator = any(re.match(r"^\|(\s*:?-+:?\s*\|)+$", l) for l in table_lines)
        return 1.0 if has_separator else 0.40

    def _evaluate_code_blocks(self, text: str) -> float:
        """Check if code fences are balanced."""
        fence_count = len(re.findall(r"^```", text, flags=re.MULTILINE))
        if fence_count % 2 != 0:
            return 0.0  # Unbalanced code block
        return 1.0

    def _evaluate_headers(self, text: str) -> float:
        """Check header progression without wild skips (e.g. # followed by ####)."""
        headers = re.findall(r"^(#{1,6})\s+", text, flags=re.MULTILINE)
        if not headers or len(headers) < 2:
            return 1.0

        depths = [len(h) for h in headers]
        penalties = 0
        for i in range(len(depths) - 1):
            if depths[i + 1] - depths[i] > 2:
                penalties += 1

        return max(0.0, 1.0 - (penalties * 0.20))

    def _evaluate_yield(self, tokens: int, pages: int) -> float:
        """Check token density per page in expected educational band [150, 1200]."""
        tokens_per_page = tokens / pages
        if 150 <= tokens_per_page <= 1200:
            return 1.0
        elif 50 <= tokens_per_page < 150:
            return 0.70
        elif tokens_per_page > 1200:
            return 0.85
        return 0.30
