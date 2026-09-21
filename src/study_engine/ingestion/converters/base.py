"""Base contracts and interfaces for CAL document converters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, ConfigDict, Field


class ConversionResult(BaseModel):
    """Normalized output produced by any CAL converter adapter."""

    model_config = ConfigDict(frozen=True)

    converter_id: str = Field(..., description="Identifier of the converter adapter")
    converter_version: str = Field(default="1.0.0", description="Semver of the converter")
    markdown_content: str = Field(..., description="Canonical extracted markdown text")
    tables_count: int = Field(default=0, ge=0)
    code_blocks_count: int = Field(default=0, ge=0)
    headers_count: int = Field(default=0, ge=0)
    tokens_count: int = Field(default=0, ge=0)
    page_count: int = Field(default=1, ge=1)
    page_map: Dict[int, str] = Field(default_factory=dict, description="Extracted text per page index")
    has_ocr: bool = Field(default=False)
    ocr_provenance: str = Field(default="none", description="none | local_tesseract | cloud")
    trust_level: str = Field(default="verified", description="verified | unverified")
    formulas_detected: bool = Field(default=False)
    formulas_unextracted: bool = Field(default=False, description="True if formula_density high but no LaTeX/MathML (CAL-5)")
    sha256_output: str = Field(..., description="SHA-256 digest of markdown_content")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseConverterAdapter(ABC):
    """Abstract converter adapter interface."""

    def __init__(self, converter_id: str, version: str = "1.0.0") -> None:
        self.converter_id = converter_id
        self.version = version

    @abstractmethod
    def convert(
        self,
        file_path: Union[str, Path],
        profile: Optional[Any] = None,
        page_range: Optional[Tuple[int, int]] = None,
    ) -> ConversionResult:
        """Convert raw file to standardized ConversionResult."""
        pass
