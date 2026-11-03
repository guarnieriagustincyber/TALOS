"""Second, standalone implementation of the vector-space draft rules.

This module intentionally does not import the implementation under test.
"""

import hashlib
import json
import re
import unicodedata


class ReferenceContractError(ValueError):
    pass


def reference_space_id(contract):
    compatibility_fields = (
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
    provenance_fields = {
        "provider_id",
        "provider_version",
        "python_version",
        "framework_versions",
        "device",
        "precision",
        "generated_at",
        "hostname",
    }
    mandatory_provenance = {
        "provider_id",
        "provider_version",
        "python_version",
        "device",
        "precision",
    }
    operations = {
        "unicode-nfc-u15.0-v1",
        "strip-unicode-whitespace-u15.0-v1",
    }
    pooling_algorithms = {
        "mean-attention-mask-v1",
        "cls-token-v1",
        "last-attended-token-v1",
    }
    permitted_top_level = {"schema", "provenance", *compatibility_fields}
    digest_pattern = re.compile(r"[0-9a-f]{64}\Z")
    revision_pattern = re.compile(r"[0-9a-f]{40,64}\Z")

    if not isinstance(contract, dict):
        raise ReferenceContractError("contract must be an object")
    if contract.get("schema") != "talos-embedding-contract-v2":
        raise ReferenceContractError("unsupported contract schema")
    extra = set(contract) - permitted_top_level
    if extra:
        raise ReferenceContractError("unknown top-level contract member")

    for key in ("model_id", "tokenizer_id", "normalization", "truncation_side"):
        value = contract.get(key)
        if not isinstance(value, str) or not value.strip():
            raise ReferenceContractError(f"invalid required string: {key}")

    if contract.get("pooling") not in pooling_algorithms:
        raise ReferenceContractError("unknown pooling algorithm")
    if contract.get("normalization") not in {"l2", "none"}:
        raise ReferenceContractError("unknown normalization")
    if contract.get("truncation_side") not in {"left", "right"}:
        raise ReferenceContractError("unknown truncation side")

    for key in ("model_revision", "tokenizer_revision"):
        value = contract.get(key)
        if not isinstance(value, str) or revision_pattern.fullmatch(value) is None:
            raise ReferenceContractError(f"invalid immutable revision: {key}")
    for key in ("model_artifact_sha256", "tokenizer_artifact_sha256"):
        value = contract.get(key)
        if not isinstance(value, str) or digest_pattern.fullmatch(value) is None:
            raise ReferenceContractError(f"invalid artifact digest: {key}")
    for key in ("dimensions", "max_length"):
        value = contract.get(key)
        if type(value) is not int or value <= 0:
            raise ReferenceContractError(f"invalid positive integer: {key}")

    for key in (
        "query_prefix",
        "query_instruction",
        "passage_prefix",
        "passage_instruction",
    ):
        if not isinstance(contract.get(key), str):
            raise ReferenceContractError(f"missing or invalid string: {key}")

    for key in ("query_preprocessing", "passage_preprocessing"):
        value = contract.get(key)
        if (
            not isinstance(value, list)
            or any(not isinstance(operation, str) for operation in value)
            or not set(value) <= operations
        ):
            raise ReferenceContractError(f"invalid operation pipeline: {key}")

    if "provenance" in contract:
        provenance = contract["provenance"]
        if not isinstance(provenance, dict):
            raise ReferenceContractError("provenance must be an object")
        if set(provenance) - provenance_fields:
            raise ReferenceContractError("unknown provenance member")
        if not mandatory_provenance <= set(provenance):
            raise ReferenceContractError("required provenance member absent")
        for key, value in provenance.items():
            if key == "framework_versions":
                if not isinstance(value, dict) or any(
                    not isinstance(name, str)
                    or not name
                    or not isinstance(version, str)
                    or not version
                    for name, version in value.items()
                ):
                    raise ReferenceContractError("invalid framework version map")
            elif not isinstance(value, str) or not value:
                raise ReferenceContractError(f"invalid provenance value: {key}")

    if unicodedata.unidata_version != "15.0.0":
        raise ReferenceContractError("requires Unicode 15.0.0 normalization data")

    payload = {}
    for field in compatibility_fields:
        value = contract[field]
        if isinstance(value, str):
            payload[field] = unicodedata.normalize("NFC", value)
        elif isinstance(value, list):
            payload[field] = [
                unicodedata.normalize("NFC", operation) for operation in value
            ]
        else:
            payload[field] = value

    canonical_json = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()


def reference_manifest_id(entries):
    """Independent canonical digest for the documented artifact manifest."""
    if not isinstance(entries, list) or len(entries) == 0:
        raise ReferenceContractError("manifest requires at least one file")
    files = []
    paths = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise ReferenceContractError("invalid manifest row")
        path = entry["path"]
        digest = entry["sha256"]
        if not isinstance(path, str) or not path:
            raise ReferenceContractError("invalid manifest path")
        if unicodedata.unidata_version != "15.0.0":
            raise ReferenceContractError("requires Unicode 15.0.0 normalization data")
        path = unicodedata.normalize("NFC", path)
        if (
            path.startswith("/")
            or "\\" in path
            or "\x00" in path
            or any(part in {"", ".", ".."} for part in path.split("/"))
        ):
            raise ReferenceContractError("manifest path must be normalized relative POSIX")
        if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ReferenceContractError("invalid manifest digest")
        if path in paths:
            raise ReferenceContractError("duplicate normalized path")
        paths.add(path)
        files.append({"path": path, "sha256": digest})
    files.sort(key=lambda row: row["path"].encode("utf-8"))
    serialized = json.dumps(
        {"schema": "talos-artifact-manifest-v1", "files": files},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def reference_assessment(query_contract, index_contracts):
    try:
        query_id = reference_space_id(query_contract)
    except ReferenceContractError as error:
        return {
            "status": "QUERY_INVALID",
            "query_vector_space_id": None,
            "index_vector_space_id": None,
            "distinct_index_spaces": 0,
            "legacy_entries": 0,
            "invalid_entries": 0,
            "reason": str(error),
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

    ids = set()
    legacy = 0
    invalid = 0
    for item in index_contracts:
        if item is None:
            legacy += 1
            continue
        if not isinstance(item, dict):
            invalid += 1
            continue
        if item.get("schema") == "talos-embedding-contract-v1":
            legacy += 1
            continue
        try:
            ids.add(reference_space_id(item))
        except ReferenceContractError:
            invalid += 1

    if invalid:
        status = "INDEX_INVALID"
    elif len(ids) > 1:
        status = "INDEX_MIXED"
    elif legacy:
        status = "INDEX_LEGACY"
    elif ids == {query_id}:
        status = "DENSE_ACTIVE"
    else:
        status = "DENSE_INCOMPATIBLE"

    return {
        "status": status,
        "query_vector_space_id": query_id,
        "index_vector_space_id": next(iter(ids)) if len(ids) == 1 else None,
        "distinct_index_spaces": len(ids),
        "legacy_entries": legacy,
        "invalid_entries": invalid,
    }
