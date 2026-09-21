"""Contract tests for Artifacts and Forensic Provenance (S5.4)."""

import hashlib
from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.curriculum.artifact_contracts import (
    ArtifactProvenance,
    ArtifactRecord,
    ArtifactRequirement,
    ArtifactType,
)


def test_artifact_operational_uuid_vs_cryptographic_sha256() -> None:
    """R1.6: Same bytes produce same sha256 with distinct artifact_ids."""
    content_bytes_1 = b"TCP SYN packet capture payload mock data"
    content_bytes_2 = b"Malicious memory dump bytes injection"

    hash_1 = hashlib.sha256(content_bytes_1).hexdigest()
    hash_2 = hashlib.sha256(content_bytes_2).hexdigest()

    now = datetime.now(timezone.utc)
    prov = ArtifactProvenance(
        source_lab_id="lab-net-01",
        tool_name="tcpdump",
        captured_at=now,
    )

    art_run_1 = ArtifactRecord(
        artifact_id="exec-run-uuid-001",
        sha256=hash_1,
        artifact_type=ArtifactType.PCAP_CAPTURE,
        filename="capture.pcap",
        size_bytes=len(content_bytes_1),
        mime_type="application/vnd.tcpdump.pcap",
        provenance=prov,
    )

    # Identical content bytes but distinct operational execution instance
    art_run_2 = ArtifactRecord(
        artifact_id="exec-run-uuid-002",
        sha256=hash_1,
        artifact_type=ArtifactType.PCAP_CAPTURE,
        filename="capture.pcap",
        size_bytes=len(content_bytes_1),
        mime_type="application/vnd.tcpdump.pcap",
        provenance=prov,
    )

    art_run_3 = ArtifactRecord(
        artifact_id="exec-run-uuid-003",
        sha256=hash_2,
        artifact_type=ArtifactType.MEMORY_DUMP,
        filename="mem.raw",
        size_bytes=len(content_bytes_2),
        mime_type="application/octet-stream",
        provenance=prov,
    )

    assert art_run_1.artifact_id != art_run_2.artifact_id
    assert art_run_1.sha256 == art_run_2.sha256
    assert art_run_1.sha256 != art_run_3.sha256


def test_artifact_record_has_zero_competence_attributes() -> None:
    """HG-S5.4-02: ArtifactRecord != EvidenceRecord.

    Zero competence verdicts, student levels, or learning outcomes.
    """
    now = datetime.now(timezone.utc)
    prov = ArtifactProvenance(
        source_lab_id="lab-soc-01",
        tool_name="suricata",
        captured_at=now,
    )

    art = ArtifactRecord(
        artifact_id="art-100",
        sha256="a" * 64,
        artifact_type=ArtifactType.LOG_BUNDLE,
        filename="eve.json",
        size_bytes=1024,
        mime_type="application/json",
        provenance=prov,
    )

    assert not hasattr(art, "competence_level")
    assert not hasattr(art, "performance_level")
    assert not hasattr(art, "is_competent")
    assert not hasattr(art, "verdict")
    assert not hasattr(art, "learning_outcome_id")

    with pytest.raises(ValidationError):
        art.sha256 = "b" * 64


def test_artifact_requirement_specification() -> None:
    """Verify declarative ArtifactRequirement specification."""
    req = ArtifactRequirement(
        requirement_id="req-pcap",
        artifact_type=ArtifactType.PCAP_CAPTURE,
        min_size_bytes=100,
        expected_mime_types=("application/vnd.tcpdump.pcap",),
        required_provenance_tools=("tcpdump", "tshark"),
        description="Raw PCAP capture of C2 beaconing session",
    )
    assert req.artifact_type == ArtifactType.PCAP_CAPTURE
    assert req.min_size_bytes == 100
    assert "tshark" in req.required_provenance_tools
