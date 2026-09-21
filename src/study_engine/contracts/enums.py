"""Domain enums for Study Engine contracts."""

from enum import Enum


class SourceRole(str, Enum):
    """Permitted roles for a knowledge source."""

    PRIMARY = "PRIMARY"
    SECONDARY = "SECONDARY"
    REFERENCE = "REFERENCE"
    OFFICIAL = "OFFICIAL"
    COURSE = "COURSE"
    PRACTICAL = "PRACTICAL"
    COMPLEMENTARY = "COMPLEMENTARY"


class EvidenceStatus(str, Enum):
    """Permitted statuses for retrieved evidence."""

    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    COMPLEMENT = "COMPLEMENT"
    INFERENCE = "INFERENCE"
    NO_EVIDENCE = "NO_EVIDENCE"


class IngestionStatus(str, Enum):
    """Permitted statuses for physical source ingestion."""

    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
