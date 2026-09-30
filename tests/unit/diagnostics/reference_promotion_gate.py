"""Independent decision implementation for vector-space promotion fixtures."""

import importlib.util
from pathlib import Path
import re
import sys
from collections.abc import Mapping


REFERENCE_PATH = Path(__file__).with_name("reference_vector_space_contract.py")
REFERENCE_SPEC = importlib.util.spec_from_file_location(
    "talos_promotion_identity_reference", REFERENCE_PATH
)
if REFERENCE_SPEC is None or REFERENCE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load reference identity from {REFERENCE_PATH}")
REFERENCE_IDENTITY = importlib.util.module_from_spec(REFERENCE_SPEC)
sys.modules[REFERENCE_SPEC.name] = REFERENCE_IDENTITY
REFERENCE_SPEC.loader.exec_module(REFERENCE_IDENTITY)

VALID_STATES = {
    "UNKNOWN",
    "UNVERIFIED",
    "UNBOUND",
    "CONTRADICTORY",
    "INVALID",
    "VERIFIED",
}
HEX_ID = re.compile(r"[0-9a-f]{64}\Z")


def _outcome(status, reason, identity):
    return {
        "status": status,
        "reason": reason,
        "vector_space_id": identity,
    }


def _exact_object(value, keys):
    return isinstance(value, Mapping) and set(value) == set(keys)


def _incomplete_status(subject):
    return "CANDIDATE" if subject == "prospective" else "LEGACY / UNRESOLVED"


def _identity(candidate):
    contract = candidate.get("contract")
    try:
        identity = REFERENCE_IDENTITY.reference_space_id(contract)
    except REFERENCE_IDENTITY.ReferenceContractError:
        if isinstance(contract, Mapping) and any(
            isinstance(contract.get(key), str)
            and re.fullmatch(r"[0-9a-f]{40,64}", contract[key]) is None
            for key in ("model_revision", "tokenizer_revision")
        ):
            return None, "MUTABLE_REVISION"
        return None, "INVALID_CONTRACT"
    return identity, None


def reference_promotion_assessment(candidate):
    required = {
        "subject",
        "contract",
        "claimed_vector_space_id",
        "artifact_evidence",
        "pipeline_evidence",
        "binding_evidence",
        "coverage_evidence",
        "consistency_state",
        "index_records",
    }
    if not isinstance(candidate, Mapping) or set(candidate) != required:
        return _outcome("REJECTED", "INVALID_EVIDENCE", None)
    if candidate["subject"] not in {"prospective", "stored_index"}:
        return _outcome("REJECTED", "INVALID_EVIDENCE", None)

    identity, identity_error = _identity(candidate)
    if identity_error:
        return _outcome("REJECTED", identity_error, None)

    artifacts = candidate["artifact_evidence"]
    pipeline = candidate["pipeline_evidence"]
    binding = candidate["binding_evidence"]
    coverage = candidate["coverage_evidence"]
    if not _exact_object(
        artifacts, ("state", "model_artifact_sha256", "tokenizer_artifact_sha256")
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if not _exact_object(pipeline, ("state", "vector_space_id")):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if not _exact_object(binding, ("state", "vector_space_id", "snapshot_id")):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if not _exact_object(coverage, ("state", "total_records", "bound_records")):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)

    states = (
        artifacts["state"],
        pipeline["state"],
        binding["state"],
        coverage["state"],
        candidate["consistency_state"],
    )
    if any(not isinstance(item, str) or item not in VALID_STATES for item in states):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    claimed = candidate["claimed_vector_space_id"]
    if claimed is not None and (
        not isinstance(claimed, str) or HEX_ID.fullmatch(claimed) is None
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    artifact_digests = (
        artifacts["model_artifact_sha256"],
        artifacts["tokenizer_artifact_sha256"],
    )
    if any(
        item is not None
        and (not isinstance(item, str) or HEX_ID.fullmatch(item) is None)
        for item in artifact_digests
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if artifacts["state"] == "VERIFIED" and any(
        not isinstance(item, str) or HEX_ID.fullmatch(item) is None
        for item in artifact_digests
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    for item in (pipeline, binding):
        evidence_id = item["vector_space_id"]
        if evidence_id is not None and (
            not isinstance(evidence_id, str) or HEX_ID.fullmatch(evidence_id) is None
        ):
            return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if binding["snapshot_id"] is not None and (
        not isinstance(binding["snapshot_id"], str) or not binding["snapshot_id"]
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if binding["state"] == "VERIFIED" and (
        binding["vector_space_id"] is None or binding["snapshot_id"] is None
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)
    if any(type(item) is not int or item < 0 for item in (
        coverage["total_records"],
        coverage["bound_records"],
    )) or coverage["bound_records"] > coverage["total_records"]:
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)

    rows = candidate["index_records"]
    if not isinstance(rows, list):
        return _outcome("REJECTED", "INVALID_INDEX", identity)
    ids = set()
    for row in rows:
        if not _exact_object(row, ("vector_space_id", "dimensions")):
            return _outcome("REJECTED", "INVALID_INDEX", identity)
        current_id = row["vector_space_id"]
        dims = row["dimensions"]
        if (
            not isinstance(current_id, str)
            or HEX_ID.fullmatch(current_id) is None
            or type(dims) is not int
            or dims < 1
        ):
            return _outcome("REJECTED", "INVALID_INDEX", identity)
        ids.add(current_id)
    if len(ids) > 1:
        return _outcome("HETEROGENEOUS", "MIXED_VECTOR_SPACES", identity)

    if candidate["consistency_state"] == "CONTRADICTORY" or any(
        evidence["state"] == "CONTRADICTORY"
        for evidence in (artifacts, pipeline, binding)
    ):
        return _outcome("REJECTED", "CONTRADICTORY_EVIDENCE", identity)
    if candidate["consistency_state"] == "INVALID" or any(
        evidence["state"] == "INVALID"
        for evidence in (artifacts, pipeline, binding)
    ):
        return _outcome("REJECTED", "INVALID_EVIDENCE", identity)

    if claimed is not None and claimed != identity:
        return _outcome("REJECTED", "IDENTITY_CLAIM_MISMATCH", identity)
    for evidence in (pipeline, binding):
        if evidence["state"] == "VERIFIED" and evidence["vector_space_id"] != identity:
            return _outcome("REJECTED", "IDENTITY_BINDING_MISMATCH", identity)

    if artifacts["state"] == "VERIFIED" and (
        artifacts["model_artifact_sha256"]
        != candidate["contract"].get("model_artifact_sha256")
        or artifacts["tokenizer_artifact_sha256"]
        != candidate["contract"].get("tokenizer_artifact_sha256")
    ):
        return _outcome("REJECTED", "MANIFEST_MISMATCH", identity)

    for row in rows:
        if (
            row["vector_space_id"] != identity
            or row["dimensions"] != candidate["contract"].get("dimensions")
        ):
            return _outcome("REJECTED", "INVALID_INDEX", identity)

    evidence_states = states
    if not rows and candidate["subject"] == "prospective":
        if all(value == "UNKNOWN" for value in evidence_states):
            return _outcome("CANDIDATE", "CONTRACT_ONLY", identity)
        if artifacts["state"] != "VERIFIED":
            return _outcome("CANDIDATE", "ARTIFACT_UNVERIFIED", identity)
        if pipeline["state"] != "VERIFIED":
            return _outcome("CANDIDATE", "PIPELINE_UNVERIFIED", identity)
        return _outcome("CANDIDATE", "INDEX_NOT_MATERIALIZED", identity)

    scope_exists = bool(rows) or bool(binding["snapshot_id"])
    if not scope_exists:
        return _outcome("CANDIDATE", "CONTRACT_ONLY", identity)
    if artifacts["state"] != "VERIFIED":
        status = _incomplete_status(candidate["subject"])
        return _outcome(status, "ARTIFACT_UNVERIFIED", identity)
    if pipeline["state"] != "VERIFIED" or binding["state"] != "VERIFIED":
        status = _incomplete_status(candidate["subject"])
        return _outcome(status, "PROVENANCE_MISSING", identity)

    total = coverage["total_records"]
    bound = coverage["bound_records"]
    if (
        coverage["state"] != "VERIFIED"
        or type(total) is not int
        or type(bound) is not int
        or total <= 0
        or bound != total
        or len(rows) != total
    ):
        status = _incomplete_status(candidate["subject"])
        return _outcome(status, "PARTIAL_COVERAGE", identity)
    if candidate["consistency_state"] != "VERIFIED":
        status = _incomplete_status(candidate["subject"])
        return _outcome(status, "CONSISTENCY_UNVERIFIED", identity)
    if (
        not rows
        or not binding["snapshot_id"]
        or candidate["claimed_vector_space_id"] != identity
    ):
        status = _incomplete_status(candidate["subject"])
        return _outcome(status, "PROVENANCE_MISSING", identity)
    return _outcome("PROMOTABLE", "ALL_PROMOTION_PREDICATES_VERIFIED", identity)
