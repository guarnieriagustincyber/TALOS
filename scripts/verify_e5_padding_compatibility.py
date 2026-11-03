#!/usr/bin/env python3
"""Reproduce the isolated E5 padding-ID comparison on synthetic text only."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path
from typing import Any

REVISION = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
UPSTREAM_REPOSITORY = "intfloat/multilingual-e5-small"
MODEL_SHA256 = "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
TOKENIZER_SHA256 = "0b44a9d7b51c3c62626640cda0e2c2f70fdacdc25bbbd68038369d14ebdf4c39"
MODEL_METADATA_SHA256 = (
    "01ef1b7cd4dda84f7a27a9af9621d4debaf06c76e27632aaaae4b6b380477687"
)
TOKENIZER_METADATA_SHA256 = (
    "16e5f97c7636dfcb0e4f1afd054c3cd2bb771497f24bbe6f7489df00fde6cb67"
)
UPSTREAM_TREE_API_URL = (
    "https://huggingface.co/api/models/intfloat/multilingual-e5-small/tree/"
    "614241f622f53c4eeff9890bdc4f31cfecc418b3?recursive=true&expand=false"
)
OUTPUT_DIMENSIONS = 384
NORM_TOLERANCE = 1e-5
VECTOR_TOLERANCE = 1e-6
FIXTURES = [
    "Synthetic short retrieval text.",
    (
        "Synthetic longer retrieval text with enough additional words to force "
        "batch padding while keeping every token inside the attention mask."
    ),
    (
        "A third deterministic synthetic passage exercises another length "
        "within the same padded batch."
    ),
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_hash(path: Path, expected: str) -> str:
    actual = sha256_file(path)
    if actual != expected:
        raise ValueError(f"Unexpected SHA-256 for {path}: {actual}")
    return actual


def read_cache_metadata(path: Path, artifact_sha256: str) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if len(lines) != 3:
        raise ValueError(f"Unexpected Hugging Face cache metadata format: {path}")
    revision, etag, timestamp = lines
    if revision != REVISION or etag != artifact_sha256:
        raise ValueError(f"Cache metadata does not bind expected artifact: {path}")
    return {
        "revision": revision,
        "etag": etag,
        "timestamp": timestamp,
        "metadata_sha256": sha256_file(path),
    }


def normalized_masked_mean(hidden_states: Any, attention_mask: Any, np: Any) -> Any:
    if hidden_states.ndim != 3 or hidden_states.shape[-1] != OUTPUT_DIMENSIONS:
        raise ValueError(f"Unexpected ONNX output shape: {hidden_states.shape}")
    if not np.isfinite(hidden_states).all():
        raise ValueError("ONNX output contains non-finite values")

    mask = attention_mask[..., None].astype(np.float32)
    pooled = (hidden_states.astype(np.float32) * mask).sum(axis=1)
    denominator = np.clip(mask.sum(axis=1), a_min=1e-9, a_max=None)
    pooled = pooled / denominator
    norms = np.linalg.norm(pooled, axis=1, keepdims=True)
    normalized = pooled / np.clip(norms, a_min=1e-9, a_max=None)
    if not np.isfinite(normalized).all():
        raise ValueError("Normalized embeddings contain non-finite values")
    return normalized


def infer_batch(session: Any, encodings: Any, np: Any) -> Any:
    input_ids = np.asarray([encoding.ids for encoding in encodings], dtype=np.int64)
    attention_mask = np.asarray(
        [encoding.attention_mask for encoding in encodings], dtype=np.int64
    )
    token_type_ids = np.asarray(
        [encoding.type_ids for encoding in encodings], dtype=np.int64
    )
    inputs = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "token_type_ids": token_type_ids,
    }
    required = {item.name for item in session.get_inputs()}
    if required != set(inputs):
        raise ValueError(f"Unexpected ONNX input names: {sorted(required)}")
    outputs = session.run(None, inputs)
    if not outputs:
        raise ValueError("ONNX session returned no outputs")
    return normalized_masked_mean(outputs[0], attention_mask, np)


def run() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    model_path = root / "models/multilingual-e5-small/onnx/model.onnx"
    tokenizer_path = root / "models/multilingual-e5-small/onnx/tokenizer.json"
    cache_dir = root / "models/multilingual-e5-small/.cache/huggingface/download/onnx"
    model_sha256 = require_hash(model_path, MODEL_SHA256)
    tokenizer_sha256 = require_hash(tokenizer_path, TOKENIZER_SHA256)
    model_metadata_path = cache_dir / "model.onnx.metadata"
    tokenizer_metadata_path = cache_dir / "tokenizer.json.metadata"
    model_metadata = read_cache_metadata(model_metadata_path, model_sha256)
    tokenizer_metadata = read_cache_metadata(tokenizer_metadata_path, tokenizer_sha256)
    if model_metadata["metadata_sha256"] != MODEL_METADATA_SHA256:
        raise ValueError("Unexpected model cache metadata hash")
    if tokenizer_metadata["metadata_sha256"] != TOKENIZER_METADATA_SHA256:
        raise ValueError("Unexpected tokenizer cache metadata hash")

    import numpy as np
    import onnxruntime as ort
    from tokenizers import Tokenizer

    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    tokenizer_pad_id = tokenizer.token_to_id("<pad>")
    if tokenizer_pad_id != 1:
        raise ValueError(f"Expected tokenizer <pad> id 1, found {tokenizer_pad_id}")
    if tokenizer.encode("<pad>").ids != [tokenizer_pad_id]:
        raise ValueError("Literal <pad> does not encode to the tokenizer pad ID")

    options = ort.SessionOptions()
    options.intra_op_num_threads = 4
    options.inter_op_num_threads = 1
    session = ort.InferenceSession(
        str(model_path),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    batches: dict[int, Any] = {}
    vectors: dict[int, Any] = {}
    for pad_id in (0, tokenizer_pad_id):
        tokenizer.enable_truncation(max_length=512)
        tokenizer.enable_padding(pad_id=pad_id, pad_token="<pad>", length=None)
        encodings = tokenizer.encode_batch(FIXTURES)
        ids = np.asarray([encoding.ids for encoding in encodings], dtype=np.int64)
        masks = np.asarray(
            [encoding.attention_mask for encoding in encodings], dtype=np.int64
        )
        batches[pad_id] = (ids, masks)
        vectors[pad_id] = infer_batch(session, encodings, np)

    ids_zero, mask_zero = batches[0]
    ids_tokenizer, mask_tokenizer = batches[tokenizer_pad_id]
    if ids_zero.shape != ids_tokenizer.shape:
        raise ValueError("Padding variants produced different input shapes")
    if not np.array_equal(mask_zero, mask_tokenizer):
        raise ValueError("Padding variants produced different attention masks")
    valid_ids_identical = np.array_equal(
        ids_zero[mask_zero == 1], ids_tokenizer[mask_tokenizer == 1]
    )
    if not valid_ids_identical:
        raise ValueError("Padding variants changed non-padding input IDs")

    padded_positions = mask_zero == 0
    if not padded_positions.any():
        raise ValueError("Fixtures did not produce any padded positions")
    if not np.all(ids_zero[padded_positions] == 0):
        raise ValueError("pad_id=0 batch does not contain ID 0 at padded positions")
    if not np.all(ids_tokenizer[padded_positions] == tokenizer_pad_id):
        raise ValueError("tokenizer-pad batch does not contain its pad ID")

    delta = np.abs(vectors[0] - vectors[tokenizer_pad_id])
    max_abs_delta = float(delta.max())
    norms = np.linalg.norm(vectors[tokenizer_pad_id], axis=1)
    if max_abs_delta > VECTOR_TOLERANCE:
        raise ValueError(f"Padding variants differ: max_abs_delta={max_abs_delta}")
    if not np.all(np.abs(norms - 1.0) <= NORM_TOLERANCE):
        raise ValueError(f"Unexpected normalized vector norms: {norms.tolist()}")

    return {
        "schema": "talos-e5-padding-compatibility-run-v1",
        "result": "PASS",
        "scope": "synthetic_text_only_no_corpus_no_index_no_production_writes",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_revision": REVISION,
        "artifact_identity_claim": (
            "local file hashes match the public Hub LFS records captured for "
            "the pinned repository commit; this script does not fetch or "
            "independently refresh the Hub API response"
        ),
        "upstream_registry_evidence": {
            "repository": UPSTREAM_REPOSITORY,
            "revision": REVISION,
            "tree_api_url": UPSTREAM_TREE_API_URL,
            "captured_on": "2026-09-29",
            "verification_mode": (
                "offline constants captured from the public Hub API; "
                "this run does not issue network requests"
            ),
            "files": {
                "onnx/model.onnx": {
                    "size_bytes": 470268510,
                    "lfs_sha256": MODEL_SHA256,
                },
                "onnx/tokenizer.json": {
                    "size_bytes": 17082730,
                    "lfs_sha256": TOKENIZER_SHA256,
                },
            },
            "onnx_config_url": (
                "https://huggingface.co/intfloat/multilingual-e5-small/resolve/"
                "614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/config.json"
            ),
            "onnx_config_pad_token_id": 0,
            "tokenizer_config_url": (
                "https://huggingface.co/intfloat/multilingual-e5-small/resolve/"
                "614241f622f53c4eeff9890bdc4f31cfecc418b3/onnx/tokenizer_config.json"
            ),
            "tokenizer_config_pad_token": "<pad>",
            "tokenizer_config_model_max_length": 512,
        },
        "artifacts": {
            "model": {
                "path": str(model_path.relative_to(root)),
                "size_bytes": model_path.stat().st_size,
                "sha256": model_sha256,
                "cache_metadata": model_metadata,
            },
            "tokenizer": {
                "path": str(tokenizer_path.relative_to(root)),
                "size_bytes": tokenizer_path.stat().st_size,
                "sha256": tokenizer_sha256,
                "cache_metadata": tokenizer_metadata,
            },
        },
        "implementation": {
            "script_sha256": sha256_file(Path(__file__).resolve()),
            "pooling": "mean-attention-mask-v1",
            "normalization": "l2",
            "max_length": 512,
            "truncation_side": "right",
            "ort_intra_op_num_threads": 4,
            "ort_inter_op_num_threads": 1,
            "provider": "CPUExecutionProvider",
            "vector_tolerance": VECTOR_TOLERANCE,
            "norm_tolerance": NORM_TOLERANCE,
        },
        "runtime": {
            "python": sys.version,
            "platform": platform.platform(),
            "numpy": version("numpy"),
            "onnxruntime": version("onnxruntime"),
            "tokenizers": version("tokenizers"),
        },
        "test": {
            "synthetic_fixtures": FIXTURES,
            "tokenizer_pad_id": tokenizer_pad_id,
            "literal_pad_encoding": tokenizer.encode("<pad>").ids,
            "attention_mask_identical": True,
            "valid_input_ids_identical": valid_ids_identical,
            "padded_positions": int(padded_positions.sum()),
            "max_abs_delta_pad0_vs_tokenizer_pad_id": max_abs_delta,
            "l2_norms": norms.tolist(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Explicit path for the JSON run manifest; parent directory must exist.",
    )
    args = parser.parse_args()
    if not args.output.parent.is_dir():
        raise FileNotFoundError(
            f"Output directory does not exist: {args.output.parent}"
        )
    if args.output.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing run manifest: {args.output}"
        )
    result = run()
    with args.output.open("x", encoding="utf-8") as output:
        output.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
