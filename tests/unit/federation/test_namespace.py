"""Unit tests for Ontological Namespaces and Governance Validator (Phase E4, Amendment E4-3)."""

import pytest
from study_engine.federation.namespace import (
    NamespaceItem,
    NamespacePrefix,
    NamespaceTrust,
    NamespaceValidator,
)


def test_namespace_prefix_extraction() -> None:
    assert NamespaceValidator.extract_namespace_prefix("[E#]c123") == NamespacePrefix.CURRICULAR
    assert NamespaceValidator.extract_namespace_prefix("[TF#]ioc456") == NamespacePrefix.THREAT_INTEL
    assert NamespaceValidator.extract_namespace_prefix("[LAB#]lab789") == NamespacePrefix.LAB
    assert NamespaceValidator.extract_namespace_prefix("raw_chunk_01") is None


def test_claim_evidence_alignment() -> None:
    validator = NamespaceValidator()

    # Valid curricular claim supported by curricular evidence
    res = validator.validate_claim_evidence_namespace(
        claim_type="curricular",
        claim_namespace=NamespacePrefix.CURRICULAR,
        evidence_namespace=NamespacePrefix.CURRICULAR,
        evidence_trust=NamespaceTrust.VERIFIED,
    )
    assert res.valid is True
    assert res.status_code == "VALID"


def test_curricular_claim_supported_only_by_threat_intel_rejected() -> None:
    """Amendment E4-3: Curricular claims supported ONLY by [TF#] are strictly REJECTED, even if verified_human."""
    validator = NamespaceValidator()

    res = validator.validate_claim_evidence_namespace(
        claim_type="curricular",
        claim_namespace=NamespacePrefix.CURRICULAR,
        evidence_namespace=NamespacePrefix.THREAT_INTEL,
        evidence_trust=NamespaceTrust.VERIFIED_HUMAN,
    )
    assert res.valid is False
    assert res.status_code == "REJECTED_UNSUPPORTED_TF_CURRICULAR"


def test_threat_intel_cannot_migrate_to_curricular() -> None:
    """Amendment E4-3: [TF#] NEVER migrates to [E#]. Target namespace must remain [TF#]."""
    validator = NamespaceValidator()

    tf_item = NamespaceItem(
        item_id="ioc-malware-01",
        namespace=NamespacePrefix.THREAT_INTEL,
        trust=NamespaceTrust.UNVERIFIED,
        content="198.51.100.42 C2 server",
        feed_count=3,
        human_approved=True,
    )

    # Attempt to change namespace to CURRICULAR
    res = validator.validate_promotion(
        item=tf_item,
        target_trust=NamespaceTrust.VERIFIED_HUMAN,
        target_namespace=NamespacePrefix.CURRICULAR,
    )
    assert res.valid is False
    assert res.status_code == "MIGRATION_PROHIBITED"


def test_threat_intel_promotion_to_verified_human_requirements() -> None:
    validator = NamespaceValidator()

    # Case A: Single feed fails with UNSUPPORTED_SINGLE_FEED
    single_feed_item = NamespaceItem(
        item_id="ioc-01",
        namespace=NamespacePrefix.THREAT_INTEL,
        trust=NamespaceTrust.UNVERIFIED,
        content="evil.example.com",
        feed_count=1,
        human_approved=True,
    )
    res_a = validator.validate_promotion(single_feed_item, target_trust=NamespaceTrust.VERIFIED_HUMAN)
    assert res_a.valid is False
    assert res_a.status_code == "UNSUPPORTED_SINGLE_FEED"

    # Case B: Multi-feed without human review fails
    multi_no_human = NamespaceItem(
        item_id="ioc-02",
        namespace=NamespacePrefix.THREAT_INTEL,
        trust=NamespaceTrust.UNVERIFIED,
        content="evil.example.com",
        feed_count=2,
        human_approved=False,
    )
    res_b = validator.validate_promotion(multi_no_human, target_trust=NamespaceTrust.VERIFIED_HUMAN)
    assert res_b.valid is False
    assert res_b.status_code == "HUMAN_REVIEW_REQUIRED"

    # Case C: Multi-feed + human review passes
    promotable = NamespaceItem(
        item_id="ioc-03",
        namespace=NamespacePrefix.THREAT_INTEL,
        trust=NamespaceTrust.UNVERIFIED,
        content="evil.example.com",
        feed_count=2,
        human_approved=True,
    )
    res_c = validator.validate_promotion(promotable, target_trust=NamespaceTrust.VERIFIED_HUMAN)
    assert res_c.valid is True
    assert res_c.status_code == "PROMOTION_PERMITTED"
