"""Offline validation helpers for embedding vector-space contracts.

This module is intentionally not wired into retrieval or persistence runtime.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import unicodedata
from pathlib import PurePosixPath
from typing import Any, Optional


CONTRACT_SCHEMA = "talos-embedding-contract-v2"
MANIFEST_SCHEMA = "talos-artifact-manifest-v1"
UNICODE_DATA_VERSION = "15.0.0"
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40,64}$")
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
OPERATION_REGISTRY = {
    "strip-unicode-whitespace-u15.0-v1": (
        "Remove leading/trailing code points in Unicode 15.0 White_Space."
    ),
    "unicode-nfc-u15.0-v1": (
        "Normalize text using Unicode 15.0 Normalization Form C."
    ),
}
POOLING_REGISTRY = {
    "mean-attention-mask-v1",
    "cls-token-v1",
    "last-attended-token-v1",
}

COMPATIBILITY_FIELDS = (
    "model_id",
    "model_revision",
    "model_artifact_sha256",
    "dimensions",
    "max_length",
    "truncation_side",
    "pooling",
    "normalization",
    "tokenizer_id",
    "tokenizer_revision",
    "tokenizer_artifact_sha256",
    "query_prefix",
    "query_instruction",
    "query_preprocessing",
    "passage_prefix",
    "passage_instruction",
    "passage_preprocessing",
)

PROVENANCE_FIELDS = frozenset(
    (
        "provider_id",
        "provider_version",
        "python_version",
        "framework_versions",
        "device",
        "precision",
        "generated_at",
        "hostname",
    )
)

CONTRACT_FIELDS = frozenset(
    ("schema", *COMPATIBILITY_FIELDS, "provenance")
)
REQUIRED_PROVENANCE_FIELDS = frozenset(
    ("provider_id", "provider_version", "python_version", "device", "precision")
)

INDEX_STATUSES = {
    "DENSE_NOT_CONFIGURED",
    "INDEX_LEGACY",
    "INDEX_MIXED",
    "INDEX_INVALID",
    "DENSE_ACTIVE",
    "DENSE_INCOMPATIBLE",
    "QUERY_INVALID",
}


class ContractValidationError(ValueError):
    """Raised when a contract lacks a valid compatibility identity."""


@dataclass(frozen=True)
class VectorSpaceIdentity:
    """Immutable compatibility identity derived from a validated v2 contract."""

    value: str

    @classmethod
    def from_contract(cls, contract: Mapping[str, Any]) -> "VectorSpaceIdentity":
        payload = compatibility_payload(contract)
        canonical = json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        return cls(hashlib.sha256(canonical).hexdigest())


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _canonical_string(value: str) -> str:
    if unicodedata.unidata_version != UNICODE_DATA_VERSION:
        raise ContractValidationError(
            "canonicalization requires Unicode data "
            f"{UNICODE_DATA_VERSION}; runtime provides {unicodedata.unidata_version}"
        )
    return unicodedata.normalize("NFC", value)


def _validate_provenance(contract: Mapping[str, Any]) -> None:
    if "provenance" not in contract:
        return
    provenance = contract["provenance"]
    if not isinstance(provenance, Mapping):
        raise ContractValidationError("provenance must be an object when present")
    unknown_fields = set(provenance) - PROVENANCE_FIELDS
    if unknown_fields:
        raise ContractValidationError(
            f"unknown provenance fields: {sorted(unknown_fields)}"
        )
    missing_fields = REQUIRED_PROVENANCE_FIELDS - set(provenance)
    if missing_fields:
        raise ContractValidationError(
            f"missing required provenance fields: {sorted(missing_fields)}"
        )
    for field, value in provenance.items():
        if field == "framework_versions":
            if not isinstance(value, Mapping) or any(
                not isinstance(key, str)
                or not key
                or not isinstance(version, str)
                or not version
                for key, version in value.items()
            ):
                raise ContractValidationError(
                    "framework_versions must map non-empty names to non-empty strings"
                )
        elif not isinstance(value, str) or not value:
            raise ContractValidationError(
                f"provenance.{field} must be a non-empty string"
            )


def validate_contract(contract: Mapping[str, Any]) -> None:
    """Validate the strict v2 compatibility fields without accepting legacy contracts."""
    if not isinstance(contract, Mapping):
        raise ContractValidationError("contract must be a JSON object")
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise ContractValidationError(f"schema must be {CONTRACT_SCHEMA!r}")
    unknown_fields = set(contract) - CONTRACT_FIELDS
    if unknown_fields:
        raise ContractValidationError(
            f"unknown contract fields: {sorted(unknown_fields)}"
        )

    required_strings = (
        "model_id",
        "tokenizer_id",
        "pooling",
        "normalization",
        "truncation_side",
    )
    for field in required_strings:
        if not isinstance(contract.get(field), str) or not contract[field].strip():
            raise ContractValidationError(f"{field} must be a non-empty string")

    for field in ("model_revision", "tokenizer_revision"):
        revision = contract.get(field)
        if not isinstance(revision, str) or not REVISION_PATTERN.fullmatch(revision):
            raise ContractValidationError(
                f"{field} must be a pinned 40-64 character lowercase hex revision"
            )

    for field in ("model_artifact_sha256", "tokenizer_artifact_sha256"):
        if not _is_sha256(contract.get(field)):
            raise ContractValidationError(f"{field} must be a lowercase SHA-256 digest")

    for field in ("dimensions", "max_length"):
        if not _is_positive_int(contract.get(field)):
            raise ContractValidationError(f"{field} must be a positive integer")

    if contract["truncation_side"] not in {"left", "right"}:
        raise ContractValidationError("truncation_side must be 'left' or 'right'")
    if contract["pooling"] not in POOLING_REGISTRY:
        raise ContractValidationError(
            f"pooling must be one of {sorted(POOLING_REGISTRY)}"
        )
    if contract["normalization"] not in {"l2", "none"}:
        raise ContractValidationError("normalization must be 'l2' or 'none'")

    for field in (
        "query_prefix",
        "query_instruction",
        "passage_prefix",
        "passage_instruction",
    ):
        if not isinstance(contract.get(field), str):
            raise ContractValidationError(
                f"{field} must be a string (use '' when absent)"
            )

    for field in ("query_preprocessing", "passage_preprocessing"):
        value = contract.get(field)
        if not isinstance(value, list) or any(
            not isinstance(item, str) or not item for item in value
        ):
            raise ContractValidationError(
                f"{field} must be an ordered list of non-empty operation identifiers"
            )
        unsupported = sorted(set(value) - OPERATION_REGISTRY.keys())
        if unsupported:
            raise ContractValidationError(
                f"{field} contains unregistered operations: {unsupported}"
            )

    _validate_provenance(contract)


def compatibility_payload(contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return only normative fields that define query/index comparability."""
    validate_contract(contract)
    payload: dict[str, Any] = {}
    for field in COMPATIBILITY_FIELDS:
        value = contract[field]
        if isinstance(value, str):
            payload[field] = _canonical_string(value)
        elif isinstance(value, list):
            payload[field] = [_canonical_string(item) for item in value]
        else:
            payload[field] = value
    return payload


def artifact_manifest_sha256(entries: Sequence[Mapping[str, str]]) -> str:
    """Hash a canonical manifest of relative POSIX paths and file SHA-256 values."""
    if not entries:
        raise ContractValidationError("artifact manifest must contain at least one file")

    normalized_entries = []
    seen_paths = set()
    for entry in entries:
        if not isinstance(entry, Mapping) or set(entry) != {"path", "sha256"}:
            raise ContractValidationError(
                "each manifest entry must contain exactly 'path' and 'sha256'"
            )
        path = entry["path"]
        digest = entry["sha256"]
        if not isinstance(path, str) or not path:
            raise ContractValidationError("manifest path must be a non-empty string")
        path = _canonical_string(path)
        posix_path = PurePosixPath(path)
        if (
            path.startswith("/")
            or "\\" in path
            or "\x00" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
            or posix_path.as_posix() != path
        ):
            raise ContractValidationError(
                f"manifest path must be normalized and relative: {path!r}"
            )
        if path in seen_paths:
            raise ContractValidationError(f"duplicate manifest path: {path!r}")
        if not _is_sha256(digest):
            raise ContractValidationError(
                f"manifest digest for {path!r} must be lowercase SHA-256"
            )
        seen_paths.add(path)
        normalized_entries.append(
            {"path": _canonical_string(path), "sha256": digest}
        )

    normalized_entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
    manifest = {
        "schema": MANIFEST_SCHEMA,
        "files": normalized_entries,
    }
    encoded = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def vector_space_id(contract: Mapping[str, Any]) -> str:
    """Calculate the stable SHA-256 identity of a v2 vector space."""
    return VectorSpaceIdentity.from_contract(contract).value


def assess_vector_space(
    query_contract: Mapping[str, Any],
    index_contracts: Sequence[Optional[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Assess compatibility against an index inventory without touching runtime state."""
    try:
        query_id = vector_space_id(query_contract)
    except ContractValidationError as exc:
        return {
            "status": "QUERY_INVALID",
            "query_vector_space_id": None,
            "index_vector_space_id": None,
            "distinct_index_spaces": 0,
            "legacy_entries": 0,
            "invalid_entries": 0,
            "reason": str(exc),
        }
    if not index_contracts:
        return {
            "status": "DENSE_NOT_CONFIGURED",
            "query_vector_space_id": query_id,
            "index_vector_space_id": None,
            "distinct_index_spaces": 0,
            "legacy_entries": 0,
            "invalid_entries": 0,
        }

    legacy_entries = 0
    invalid_entries = 0
    known_ids = set()
    for contract in index_contracts:
        if contract is None:
            legacy_entries += 1
            continue
        if not isinstance(contract, Mapping):
            invalid_entries += 1
            continue
        schema = contract.get("schema")
        if schema == "talos-embedding-contract-v1":
            legacy_entries += 1
            continue
        if schema != CONTRACT_SCHEMA:
            invalid_entries += 1
            continue
        try:
            known_ids.add(vector_space_id(contract))
        except ContractValidationError:
            invalid_entries += 1

    if invalid_entries:
        status = "INDEX_INVALID"
    elif len(known_ids) > 1:
        status = "INDEX_MIXED"
    elif legacy_entries:
        status = "INDEX_LEGACY"
    elif known_ids == {query_id}:
        status = "DENSE_ACTIVE"
    else:
        status = "DENSE_INCOMPATIBLE"

    index_id = next(iter(known_ids)) if len(known_ids) == 1 else None
    return {
        "status": status,
        "query_vector_space_id": query_id,
        "index_vector_space_id": index_id,
        "distinct_index_spaces": len(known_ids),
        "legacy_entries": legacy_entries,
        "invalid_entries": invalid_entries,
    }


def validate_fixture_suite(fixtures: Mapping[str, Any]) -> list[dict[str, str]]:
    """Run declared fixture cases and raise if any expected status is not produced."""
    if fixtures.get("schema") != "talos-vector-space-fixtures-v1":
        raise ValueError("unknown vector-space fixture schema")
    base_contract = fixtures.get("base_contract")
    if not isinstance(base_contract, dict):
        raise ValueError("base_contract must be an object")

    results: list[dict[str, str]] = []
    cases = fixtures.get("cases")
    if not isinstance(cases, list):
        raise ValueError("cases must be a list")

    for case in cases:
        name = case.get("name")
        if not isinstance(name, str) or not name:
            raise ValueError("every fixture case must have a name")

        query_contract = dict(base_contract)
        query_contract.update(case.get("query_overrides", {}))
        expected = case.get("expected_status")
        if expected not in INDEX_STATUSES:
            raise ValueError(f"{name}: invalid expected_status {expected!r}")

        index_specs = case.get("index_contracts", [])
        if not isinstance(index_specs, list):
            raise ValueError(f"{name}: index_contracts must be a list")
        index_contracts: list[Optional[Mapping[str, Any]]] = []
        for index_spec in index_specs:
            if index_spec is None:
                index_contracts.append(None)
            else:
                contract = dict(base_contract)
                contract.update(index_spec)
                index_contracts.append(contract)

        actual = assess_vector_space(query_contract, index_contracts)["status"]
        if actual != expected:
            raise AssertionError(f"{name}: expected {expected}, got {actual}")
        results.append({"name": name, "status": actual})

    return results


PROMOTION_EVIDENCE_STATES = {
    "UNKNOWN",
    "UNVERIFIED",
    "UNBOUND",
    "CONTRADICTORY",
    "INVALID",
    "VERIFIED",
}
_PROMOTION_DIGEST_PATTERN = re.compile(r"^[0-9a-f]{64}$")


def _promotion_decision(
    status: str, reason: str, identity: Optional[str]
) -> dict[str, Any]:
    return {
        "status": status,
        "reason": reason,
        "vector_space_id": identity,
    }


def _promotion_mapping(value: Any, fields: set[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == fields


def assess_promotion(candidate: Mapping[str, Any]) -> dict[str, Any]:
    """Assess one synthetic promotion candidate without accessing index storage."""
    if not isinstance(candidate, Mapping) or set(candidate) != {
        "subject",
        "contract",
        "claimed_vector_space_id",
        "artifact_evidence",
        "pipeline_evidence",
        "binding_evidence",
        "coverage_evidence",
        "consistency_state",
        "index_records",
    }:
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", None)

    subject = candidate["subject"]
    if subject not in {"prospective", "stored_index"}:
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", None)

    contract = candidate["contract"]
    try:
        identity = vector_space_id(contract)
    except ContractValidationError:
        if isinstance(contract, Mapping) and any(
            isinstance(contract.get(field), str)
            and REVISION_PATTERN.fullmatch(contract[field]) is None
            for field in ("model_revision", "tokenizer_revision")
        ):
            return _promotion_decision("REJECTED", "MUTABLE_REVISION", None)
        return _promotion_decision("REJECTED", "INVALID_CONTRACT", None)

    artifact = candidate["artifact_evidence"]
    pipeline = candidate["pipeline_evidence"]
    binding = candidate["binding_evidence"]
    coverage = candidate["coverage_evidence"]
    if not _promotion_mapping(
        artifact, {"state", "model_artifact_sha256", "tokenizer_artifact_sha256"}
    ) or not _promotion_mapping(
        pipeline, {"state", "vector_space_id"}
    ) or not _promotion_mapping(
        binding, {"state", "vector_space_id", "snapshot_id"}
    ) or not _promotion_mapping(
        coverage, {"state", "total_records", "bound_records"}
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)

    evidence_states = (
        artifact["state"],
        pipeline["state"],
        binding["state"],
        coverage["state"],
        candidate["consistency_state"],
    )
    if any(
        not isinstance(state, str) or state not in PROMOTION_EVIDENCE_STATES
        for state in evidence_states
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    claimed_id = candidate["claimed_vector_space_id"]
    if claimed_id is not None and (
        not isinstance(claimed_id, str)
        or _PROMOTION_DIGEST_PATTERN.fullmatch(claimed_id) is None
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    for digest in (
        artifact["model_artifact_sha256"],
        artifact["tokenizer_artifact_sha256"],
    ):
        if digest is not None and (
            not isinstance(digest, str)
            or _PROMOTION_DIGEST_PATTERN.fullmatch(digest) is None
        ):
            return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    if artifact["state"] == "VERIFIED" and any(
        not isinstance(digest, str)
        or _PROMOTION_DIGEST_PATTERN.fullmatch(digest) is None
        for digest in (
            artifact["model_artifact_sha256"],
            artifact["tokenizer_artifact_sha256"],
        )
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    for evidence in (pipeline, binding):
        evidence_id = evidence["vector_space_id"]
        if evidence_id is not None and (
            not isinstance(evidence_id, str)
            or _PROMOTION_DIGEST_PATTERN.fullmatch(evidence_id) is None
        ):
            return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    if binding["snapshot_id"] is not None and (
        not isinstance(binding["snapshot_id"], str) or not binding["snapshot_id"]
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    if binding["state"] == "VERIFIED" and (
        binding["vector_space_id"] is None or binding["snapshot_id"] is None
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    for count in (coverage["total_records"], coverage["bound_records"]):
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)
    if coverage["bound_records"] > coverage["total_records"]:
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)

    records = candidate["index_records"]
    if not isinstance(records, list):
        return _promotion_decision("REJECTED", "INVALID_INDEX", identity)
    for record in records:
        if not _promotion_mapping(record, {"vector_space_id", "dimensions"}):
            return _promotion_decision("REJECTED", "INVALID_INDEX", identity)
        record_id = record["vector_space_id"]
        dimensions = record["dimensions"]
        if (
            not isinstance(record_id, str)
            or _PROMOTION_DIGEST_PATTERN.fullmatch(record_id) is None
            or not isinstance(dimensions, int)
            or isinstance(dimensions, bool)
            or dimensions <= 0
        ):
            return _promotion_decision("REJECTED", "INVALID_INDEX", identity)

    if len({record["vector_space_id"] for record in records}) > 1:
        return _promotion_decision("HETEROGENEOUS", "MIXED_VECTOR_SPACES", identity)

    if candidate["consistency_state"] == "CONTRADICTORY" or any(
        evidence["state"] == "CONTRADICTORY"
        for evidence in (artifact, pipeline, binding)
    ):
        return _promotion_decision("REJECTED", "CONTRADICTORY_EVIDENCE", identity)
    if candidate["consistency_state"] == "INVALID" or any(
        evidence["state"] == "INVALID"
        for evidence in (artifact, pipeline, binding)
    ):
        return _promotion_decision("REJECTED", "INVALID_EVIDENCE", identity)

    if claimed_id is not None and claimed_id != identity:
        return _promotion_decision("REJECTED", "IDENTITY_CLAIM_MISMATCH", identity)
    if any(
        evidence["state"] == "VERIFIED" and evidence["vector_space_id"] != identity
        for evidence in (pipeline, binding)
    ):
        return _promotion_decision("REJECTED", "IDENTITY_BINDING_MISMATCH", identity)

    if artifact["state"] == "VERIFIED" and (
        artifact["model_artifact_sha256"]
        != contract.get("model_artifact_sha256")
        or artifact["tokenizer_artifact_sha256"]
        != contract.get("tokenizer_artifact_sha256")
    ):
        return _promotion_decision("REJECTED", "MANIFEST_MISMATCH", identity)

    if any(
        record["vector_space_id"] != identity
        or record["dimensions"] != contract.get("dimensions")
        for record in records
    ):
        return _promotion_decision("REJECTED", "INVALID_INDEX", identity)

    if not records and subject == "prospective":
        if all(state == "UNKNOWN" for state in evidence_states):
            return _promotion_decision("CANDIDATE", "CONTRACT_ONLY", identity)
        if artifact["state"] != "VERIFIED":
            return _promotion_decision("CANDIDATE", "ARTIFACT_UNVERIFIED", identity)
        if pipeline["state"] != "VERIFIED":
            return _promotion_decision("CANDIDATE", "PIPELINE_UNVERIFIED", identity)
        return _promotion_decision("CANDIDATE", "INDEX_NOT_MATERIALIZED", identity)

    if not records and not binding["snapshot_id"]:
        return _promotion_decision("CANDIDATE", "CONTRACT_ONLY", identity)
    if artifact["state"] != "VERIFIED":
        status = "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"
        return _promotion_decision(status, "ARTIFACT_UNVERIFIED", identity)
    if pipeline["state"] != "VERIFIED" or binding["state"] != "VERIFIED":
        status = "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"
        return _promotion_decision(status, "PROVENANCE_MISSING", identity)
    if (
        coverage["state"] != "VERIFIED"
        or not isinstance(coverage["total_records"], int)
        or isinstance(coverage["total_records"], bool)
        or not isinstance(coverage["bound_records"], int)
        or isinstance(coverage["bound_records"], bool)
        or coverage["total_records"] <= 0
        or coverage["bound_records"] != coverage["total_records"]
        or len(records) != coverage["total_records"]
    ):
        status = "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"
        return _promotion_decision(status, "PARTIAL_COVERAGE", identity)
    if candidate["consistency_state"] != "VERIFIED":
        status = "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"
        return _promotion_decision(status, "CONSISTENCY_UNVERIFIED", identity)
    if not records or not binding["snapshot_id"] or claimed_id != identity:
        status = "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"
        return _promotion_decision(status, "PROVENANCE_MISSING", identity)

    return _promotion_decision(
        "PROMOTABLE", "ALL_PROMOTION_PREDICATES_VERIFIED", identity
    )
