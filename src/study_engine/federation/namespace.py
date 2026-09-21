"""Ontological Namespaces and Governance Validator (Phase E4, Amendment E4-3).

Enforces strict boundaries across:
- [E#]: Curricular canonical evidence (CAL verified/unverified corpus).
- [TF#]: Threat Intelligence feeds (VirusTotal, OTX, Abuse.ch). Always unverified by default.
         Can be promoted to 'verified_human' via >= 2 feeds cross-check + human approval.
         NEVER migrates to [E#]. Curricular claims supported ONLY by [TF#] are strictly REJECTED.
- [LAB#]: Deterministic practical lab grader observations (Juice Shop, VAmPI). Zero LLM updates.
"""

from enum import Enum
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, ConfigDict, Field


class NamespacePrefix(str, Enum):
    """Ontological namespace prefixes."""
    CURRICULAR = "[E#]"
    THREAT_INTEL = "[TF#]"
    LAB = "[LAB#]"


class NamespaceTrust(str, Enum):
    """Trust levels for evidence items."""
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    VERIFIED_HUMAN = "verified_human"


class NamespaceItem(BaseModel):
    """Representation of an item bound to an ontological namespace."""

    model_config = ConfigDict(frozen=True)

    item_id: str = Field(..., min_length=1)
    namespace: NamespacePrefix
    trust: NamespaceTrust
    content: str = Field(..., min_length=1)
    feed_count: int = Field(default=1, ge=1)
    human_approved: bool = Field(default=False)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NamespaceValidationResult(BaseModel):
    """Result of namespace governance and claim-evidence verification."""

    valid: bool
    status_code: str
    message: str
    item_id: Optional[str] = None
    namespace: Optional[NamespacePrefix] = None


class NamespaceValidator:
    """Validates ontological namespace integrity, claim-evidence consistency, and promotion rules."""

    def __init__(self, registry_path: Optional[str] = "config/namespace_registry.json") -> None:
        self.registry_path = Path(registry_path) if registry_path else None
        self._registry_data: Dict[str, Any] = {}
        self._registry_hash: str = ""
        self._lock = threading.Lock()

        if self.registry_path and self.registry_path.exists():
            self._load_registry()

    def _load_registry(self) -> None:
        raw_bytes = self.registry_path.read_bytes()
        self._registry_hash = hashlib.sha256(raw_bytes).hexdigest()
        self._registry_data = json.loads(raw_bytes.decode("utf-8"))

    def get_registry_hash(self) -> str:
        with self._lock:
            return self._registry_hash

    @staticmethod
    def extract_namespace_prefix(identifier: str) -> Optional[NamespacePrefix]:
        """Extract ontological prefix from an identifier (e.g. '[TF#]123' -> NamespacePrefix.THREAT_INTEL)."""
        clean = identifier.strip()
        for prefix in NamespacePrefix:
            if clean.startswith(prefix.value):
                return prefix
        return None

    def validate_claim_evidence_namespace(
        self,
        claim_type: str,
        claim_namespace: NamespacePrefix,
        evidence_namespace: NamespacePrefix,
        evidence_trust: NamespaceTrust,
    ) -> NamespaceValidationResult:
        """S4.4 forensic audit: Ensure claim namespace and evidence namespace are valid and compatible.

        Critical Invariant:
        1. Curricular claims supported ONLY by [TF#] are strictly REJECTED (Amendment E4-3).
        2. Threat claims cannot be supported by [E#] without explicit cross-domain bridge.
        3. [TF#] never migrates to [E#].
        """
        # Rule 1: Curricular claims cannot be justified solely by [TF#], even if verified_human
        if claim_namespace == NamespacePrefix.CURRICULAR and evidence_namespace == NamespacePrefix.THREAT_INTEL:
            return NamespaceValidationResult(
                valid=False,
                status_code="REJECTED_UNSUPPORTED_TF_CURRICULAR",
                message="Curricular claims cannot be supported solely by Threat Intel [TF#] evidence, even if verified_human.",
                namespace=claim_namespace,
            )

        # Rule 2: Claim namespace must match evidence namespace unless authorized
        if claim_namespace != evidence_namespace:
            return NamespaceValidationResult(
                valid=False,
                status_code="NAMESPACE_MISMATCH",
                message=f"Claim namespace {claim_namespace.value} mismatches evidence namespace {evidence_namespace.value}.",
                namespace=claim_namespace,
            )

        # Rule 3: LAB evidence is strictly for practical/lab competency claims
        if claim_namespace == NamespacePrefix.LAB and claim_type not in ("lab_competency", "exercise_completion"):
            return NamespaceValidationResult(
                valid=False,
                status_code="INVALID_LAB_CLAIM_TYPE",
                message=f"Claim type '{claim_type}' not permitted for [LAB#] namespace.",
                namespace=claim_namespace,
            )

        return NamespaceValidationResult(
            valid=True,
            status_code="VALID",
            message="Claim and evidence namespace alignment verified.",
            namespace=claim_namespace,
        )

    def validate_promotion(
        self,
        item: NamespaceItem,
        target_trust: NamespaceTrust,
        target_namespace: Optional[NamespacePrefix] = None,
    ) -> NamespaceValidationResult:
        """Verify whether an evidence item can transition trust or namespace.

        Amendment E4-3:
        [TF#] NEVER migrates to [E#]. Target namespace must remain [TF#].
        To reach 'verified_human', requires:
        - feed_count >= 2 (cross-checked)
        - human_approved == True
        """
        # Invariant 1: Namespace migration prohibition
        if target_namespace is not None and target_namespace != item.namespace:
            return NamespaceValidationResult(
                valid=False,
                status_code="MIGRATION_PROHIBITED",
                message=f"Direct ontological migration from {item.namespace.value} to {target_namespace.value} is strictly prohibited.",
                item_id=item.item_id,
                namespace=item.namespace,
            )

        # Invariant 2: Curricular items are already verified or unverified (OCR degraded), cannot promote
        if item.namespace == NamespacePrefix.CURRICULAR:
            if target_trust == NamespaceTrust.VERIFIED_HUMAN:
                return NamespaceValidationResult(
                    valid=False,
                    status_code="INVALID_PROMOTION_TARGET",
                    message="Curricular items do not use verified_human promotion (governed by CAL pipeline).",
                    item_id=item.item_id,
                    namespace=item.namespace,
                )

        # Invariant 3: [TF#] promotion rules
        if item.namespace == NamespacePrefix.THREAT_INTEL:
            if target_trust == NamespaceTrust.VERIFIED:
                return NamespaceValidationResult(
                    valid=False,
                    status_code="INVALID_TRUST_TARGET",
                    message="[TF#] items cannot be promoted to raw 'verified'. Only 'verified_human' is permissible.",
                    item_id=item.item_id,
                    namespace=item.namespace,
                )

            if target_trust == NamespaceTrust.VERIFIED_HUMAN:
                if item.feed_count < 2:
                    return NamespaceValidationResult(
                        valid=False,
                        status_code="UNSUPPORTED_SINGLE_FEED",
                        message=f"Threat intel promotion requires >= 2 corroborated feeds. Found {item.feed_count}.",
                        item_id=item.item_id,
                        namespace=item.namespace,
                    )
                if not item.human_approved:
                    return NamespaceValidationResult(
                        valid=False,
                        status_code="HUMAN_REVIEW_REQUIRED",
                        message="Promotion to verified_human requires human reviewer approval.",
                        item_id=item.item_id,
                        namespace=item.namespace,
                    )

        # Invariant 4: LAB items cannot be manually promoted (they are deterministic)
        if item.namespace == NamespacePrefix.LAB:
            if target_trust != NamespaceTrust.VERIFIED:
                return NamespaceValidationResult(
                    valid=False,
                    status_code="IMMUTABLE_LAB_TRUST",
                    message="[LAB#] evidence trust is strictly deterministic and immutable.",
                    item_id=item.item_id,
                    namespace=item.namespace,
                )

        return NamespaceValidationResult(
            valid=True,
            status_code="PROMOTION_PERMITTED",
            message=f"Promotion of {item.item_id} to {target_trust.value} is authorized.",
            item_id=item.item_id,
            namespace=item.namespace,
        )
