import json
import hashlib
import importlib.util
import unicodedata
from pathlib import Path
import sys

import pytest

from study_engine.diagnostics.vector_space_contract import (
    COMPATIBILITY_FIELDS,
    ContractValidationError,
    VectorSpaceIdentity,
    artifact_manifest_sha256,
    assess_vector_space,
    validate_contract,
    validate_fixture_suite,
    vector_space_id,
)


FIXTURE_PATH = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "vector_space_contract"
    / "cases.json"
)
REFERENCE_PATH = Path(__file__).with_name("reference_vector_space_contract.py")
REFERENCE_SPEC = importlib.util.spec_from_file_location(
    "talos_independent_vector_space_reference", REFERENCE_PATH
)
assert REFERENCE_SPEC is not None and REFERENCE_SPEC.loader is not None
REFERENCE = importlib.util.module_from_spec(REFERENCE_SPEC)
sys.modules[REFERENCE_SPEC.name] = REFERENCE
REFERENCE_SPEC.loader.exec_module(REFERENCE)


def test_offline_vector_space_fixtures():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    results = validate_fixture_suite(fixtures)

    assert len(results) == len(fixtures["cases"])
    assert {result["status"] for result in results} >= {
        "DENSE_ACTIVE",
        "DENSE_INCOMPATIBLE",
        "INDEX_LEGACY",
        "INDEX_MIXED",
        "INDEX_INVALID",
        "DENSE_NOT_CONFIGURED",
    }


def test_vector_space_id_uses_only_compatibility_fields():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    changed_provenance = {
        **contract,
        "provenance": {
            **contract["provenance"],
            "provider_id": "different-provider",
            "python_version": "different-python",
            "device": "different-device",
            "precision": "fp32",
        },
    }

    assert vector_space_id(contract) == vector_space_id(changed_provenance)
    assert VectorSpaceIdentity.from_contract(contract).value == vector_space_id(contract)
    assert vector_space_id(contract) == vector_space_id(
        {key: value for key, value in contract.items() if key != "provenance"}
    )


def test_vector_space_id_changes_with_input_transform():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    changed_transform = {**contract, "passage_prefix": "passage: "}

    assert vector_space_id(contract) != vector_space_id(changed_transform)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model_revision", "main"),
        ("model_artifact_sha256", "not-a-digest"),
        ("dimensions", True),
        ("dimensions", 1024.0),
        ("normalization", "cosine-ish"),
        ("pooling", "mean-but-unspecified"),
        ("query_preprocessing", "strip-unicode-whitespace-u15.0-v1"),
    ],
)
def test_v2_contract_rejects_unpinned_or_invalid_identity(field, value):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = {**fixtures["base_contract"], field: value}

    with pytest.raises(ContractValidationError):
        validate_contract(contract)


def _mutated_valid_value(field):
    return {
        "model_id": "different-model",
        "model_revision": "1123456789abcdef0123456789abcdef01234567",
        "model_artifact_sha256": "c" * 64,
        "dimensions": 2048,
        "max_length": 256,
        "truncation_side": "left",
        "pooling": "cls-token-v1",
        "normalization": "none",
        "tokenizer_id": "different-tokenizer",
        "tokenizer_revision": "2123456789abcdef0123456789abcdef01234567",
        "tokenizer_artifact_sha256": "d" * 64,
        "query_prefix": "query: ",
        "query_instruction": "different instruction",
        "query_preprocessing": ["strip-unicode-whitespace-u15.0-v1"],
        "passage_prefix": "passage: ",
        "passage_instruction": "different passage instruction",
        "passage_preprocessing": ["strip-unicode-whitespace-u15.0-v1"],
    }[field]


@pytest.mark.parametrize("field", COMPATIBILITY_FIELDS)
def test_changing_each_compatibility_field_changes_vector_space_id(field):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    changed = {**contract, field: _mutated_valid_value(field)}

    assert vector_space_id(contract) != vector_space_id(changed), field


def test_unknown_contract_fields_and_operations_are_rejected():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]

    with pytest.raises(ContractValidationError, match="unknown contract fields"):
        validate_contract({**contract, "pooling_semantics_v2": "other"})

    with pytest.raises(ContractValidationError, match="unregistered operations"):
        validate_contract(
            {**contract, "query_preprocessing": ["normalize-v9"]}
        )


def test_unknown_provenance_fields_and_null_provenance_are_rejected():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]

    with pytest.raises(ContractValidationError, match="unknown provenance fields"):
        validate_contract(
            {
                **contract,
                "provenance": {
                    **contract["provenance"],
                    "new_runtime_fact": "value",
                },
            }
        )

    with pytest.raises(ContractValidationError, match="provenance must be an object"):
        validate_contract({**contract, "provenance": None})


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("provider_id", "different-provider"),
        ("provider_version", "different-version"),
        ("python_version", "different-python"),
        ("framework_versions", {"other-framework": "different-version"}),
        ("device", "different-device"),
        ("precision", "fp32"),
        ("generated_at", "different-timestamp"),
        ("hostname", "different-host"),
    ],
)
def test_each_provenance_field_is_excluded_from_vector_space_id(field, replacement):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    provenance = {**contract["provenance"], field: replacement}

    assert vector_space_id(contract) == vector_space_id(
        {**contract, "provenance": provenance}
    )


@pytest.mark.parametrize("field", COMPATIBILITY_FIELDS)
def test_each_required_compatibility_field_rejects_null_and_absence(field):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    without_field = {key: value for key, value in contract.items() if key != field}

    with pytest.raises(ContractValidationError):
        validate_contract({**contract, field: None})
    with pytest.raises(ContractValidationError):
        validate_contract(without_field)


def test_unicode_strings_are_normalized_to_nfc_for_identity():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    composed = {**contract, "query_instruction": "café"}
    decomposed = {**contract, "query_instruction": "cafe\u0301"}

    assert vector_space_id(composed) == vector_space_id(decomposed)


def test_query_invalid_and_index_invalid_are_structured_and_fail_closed():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]

    query_result = assess_vector_space(
        {**contract, "dimensions": None},
        [contract],
    )
    index_result = assess_vector_space(
        contract,
        [None, {**contract, "dimensions": None}],
    )

    assert query_result["status"] == "QUERY_INVALID"
    assert index_result["status"] == "INDEX_INVALID"
    assert index_result["legacy_entries"] == 1
    assert index_result["invalid_entries"] == 1


def test_invalid_index_takes_precedence_over_mixed_index():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    different_space = {
        **contract,
        "model_id": "different-model",
        "model_revision": "1123456789abcdef0123456789abcdef01234567",
        "model_artifact_sha256": "c" * 64,
        "tokenizer_id": "different-tokenizer",
        "tokenizer_revision": "2123456789abcdef0123456789abcdef01234567",
        "tokenizer_artifact_sha256": "d" * 64,
    }

    result = assess_vector_space(
        contract,
        [contract, different_space, {**contract, "pooling_semantics_v2": "unknown"}],
    )

    assert result["status"] == "INDEX_INVALID"
    assert result["distinct_index_spaces"] == 2
    assert result["invalid_entries"] == 1


def test_independent_reference_canonicalizer_matches_validator():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    reference_fields = (
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

    def normalize(value):
        if isinstance(value, str):
            return unicodedata.normalize("NFC", value)
        if isinstance(value, list):
            return [normalize(item) for item in value]
        return value

    reference_payload = {
        field: normalize(contract[field])
        for field in reference_fields
    }
    reference_bytes = json.dumps(
        reference_payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    independent_id = hashlib.sha256(reference_bytes).hexdigest()

    assert vector_space_id(contract) == independent_id


def test_second_implementation_reproduces_all_fixture_ids_and_states():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    base = fixtures["base_contract"]

    for case in fixtures["cases"]:
        query = {**base, **case.get("query_overrides", {})}
        index_contracts = [
            None if item is None else {**base, **item}
            for item in case.get("index_contracts", [])
        ]
        actual = assess_vector_space(query, index_contracts)
        reference = REFERENCE.reference_assessment(query, index_contracts)

        assert {
            key: value for key, value in actual.items() if key != "reason"
        } == {
            key: value for key, value in reference.items() if key != "reason"
        }, case["name"]
        assert actual["status"] == case["expected_status"], case["name"]
        if actual["query_vector_space_id"] is not None:
            assert actual["query_vector_space_id"] == REFERENCE.reference_space_id(
                query
            )


@pytest.mark.parametrize("field", COMPATIBILITY_FIELDS)
def test_second_implementation_agrees_when_each_compatibility_field_changes(field):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    base = fixtures["base_contract"]
    changed = {**base, field: _mutated_valid_value(field)}

    assert vector_space_id(base) == REFERENCE.reference_space_id(base)
    assert vector_space_id(changed) == REFERENCE.reference_space_id(changed)


@pytest.mark.parametrize(
    ("field", "replacement"),
    [
        ("provider_id", "other-provider"),
        ("provider_version", "other-version"),
        ("python_version", "other-python"),
        ("framework_versions", {"other": "version"}),
        ("device", "other-device"),
        ("precision", "fp32"),
        ("generated_at", "other-time"),
        ("hostname", "other-host"),
    ],
)
def test_second_implementation_excludes_each_provenance_field(field, replacement):
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    changed = {
        **contract,
        "provenance": {**contract["provenance"], field: replacement},
    }

    assert vector_space_id(contract) == REFERENCE.reference_space_id(contract)
    assert vector_space_id(changed) == REFERENCE.reference_space_id(changed)
    assert vector_space_id(contract) == vector_space_id(changed)


def test_artifact_manifest_hash_is_order_independent_and_normalized():
    entries = [
        {"path": "tokenizer/config.json", "sha256": "a" * 64},
        {"path": "weights/model.bin", "sha256": "b" * 64},
    ]
    reversed_entries = list(reversed(entries))

    assert artifact_manifest_sha256(entries) == artifact_manifest_sha256(
        reversed_entries
    )
    reference_manifest = {
        "schema": "talos-artifact-manifest-v1",
        "files": [
            {"path": "tokenizer/config.json", "sha256": "a" * 64},
            {"path": "weights/model.bin", "sha256": "b" * 64},
        ],
    }
    reference_bytes = json.dumps(
        reference_manifest,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert artifact_manifest_sha256(entries) == hashlib.sha256(
        reference_bytes
    ).hexdigest()
    assert artifact_manifest_sha256(entries) == REFERENCE.reference_manifest_id(
        entries
    )
    assert artifact_manifest_sha256(
        [{"path": "model/café.bin", "sha256": "a" * 64}]
    ) == artifact_manifest_sha256(
        [{"path": "model/cafe\u0301.bin", "sha256": "a" * 64}]
    )


@pytest.mark.parametrize(
    "path",
    [
        "/absolute/model.bin",
        "../model.bin",
        "model/../weights.bin",
        "model\\weights.bin",
        "model//weights.bin",
    ],
)
def test_artifact_manifest_rejects_noncanonical_paths(path):
    with pytest.raises(ContractValidationError):
        artifact_manifest_sha256([{"path": path, "sha256": "a" * 64}])


def test_preprocessing_order_is_semantically_significant():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    contract = fixtures["base_contract"]
    reordered = {
        **contract,
        "query_preprocessing": list(reversed(contract["query_preprocessing"])),
    }

    assert vector_space_id(contract) != vector_space_id(reordered)


def test_artifact_manifest_rejects_duplicate_paths_after_nfc():
    with pytest.raises(ContractValidationError, match="duplicate manifest path"):
        artifact_manifest_sha256(
            [
                {"path": "café.bin", "sha256": "a" * 64},
                {"path": "cafe\u0301.bin", "sha256": "b" * 64},
            ]
        )


def test_legacy_index_never_authorizes_dense_comparison():
    fixtures = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    result = assess_vector_space(fixtures["base_contract"], [None])

    assert result["status"] == "INDEX_LEGACY"
    assert result["legacy_entries"] == 1
