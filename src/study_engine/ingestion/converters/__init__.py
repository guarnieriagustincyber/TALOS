"""Converters package for CAL."""

from study_engine.ingestion.converters.anydoc_adapter import AnyDocAdapter
from study_engine.ingestion.converters.base import BaseConverterAdapter, ConversionResult
from study_engine.ingestion.converters.credits_manager import ConversionCreditsManager
from study_engine.ingestion.converters.markitdown_adapter import MarkItDownAdapter
from study_engine.ingestion.converters.tesseract_fallback import TesseractFallbackAdapter

__all__ = [
    "AnyDocAdapter",
    "BaseConverterAdapter",
    "ConversionCreditsManager",
    "ConversionResult",
    "MarkItDownAdapter",
    "TesseractFallbackAdapter",
]
