#!/usr/bin/env python3
"""Inspect ONNX protobuf tensor types without importing ONNX Runtime."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from mmap import ACCESS_READ, mmap
from pathlib import Path
from typing import Iterator

EXPECTED_MODEL_SHA256 = (
    "ca456c06b3a9505ddfd9131408916dd79290368331e7d76bb621f1cba6bc8665"
)
ONNX_DATA_TYPES = {
    1: "FLOAT",
    2: "UINT8",
    3: "INT8",
    4: "UINT16",
    5: "INT16",
    6: "INT32",
    7: "INT64",
    8: "STRING",
    9: "BOOL",
    10: "FLOAT16",
    11: "DOUBLE",
    12: "UINT32",
    13: "UINT64",
    14: "COMPLEX64",
    15: "COMPLEX128",
    16: "BFLOAT16",
    17: "FLOAT8E4M3FN",
    18: "FLOAT8E4M3FNUZ",
    19: "FLOAT8E5M2",
    20: "FLOAT8E5M2FNUZ",
    21: "UINT4",
    22: "INT4",
    23: "FLOAT4E2M1",
}


def read_varint(data: mmap, position: int, end: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while position < end:
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if byte < 0x80:
            return value, position
        shift += 7
        if shift >= 70:
            raise ValueError("Invalid protobuf varint")
    raise ValueError("Truncated protobuf varint")


def protobuf_fields(
    data: mmap, start: int, end: int
) -> Iterator[tuple[int, int, int | tuple[int, int]]]:
    position = start
    while position < end:
        tag, position = read_varint(data, position, end)
        number, wire_type = tag >> 3, tag & 7
        if number == 0:
            raise ValueError("Invalid protobuf field number 0")
        if wire_type == 0:
            value, position = read_varint(data, position, end)
        elif wire_type == 1:
            if position + 8 > end:
                raise ValueError("Truncated protobuf fixed64 field")
            value = position
            position += 8
        elif wire_type == 2:
            size, position = read_varint(data, position, end)
            if position + size > end:
                raise ValueError("Truncated protobuf length-delimited field")
            value = (position, position + size)
            position += size
        elif wire_type == 5:
            if position + 4 > end:
                raise ValueError("Truncated protobuf fixed32 field")
            value = position
            position += 4
        else:
            raise ValueError(f"Unsupported protobuf wire type {wire_type}")
        yield number, wire_type, value


def nested_fields(
    data: mmap, span: tuple[int, int]
) -> Iterator[tuple[int, int, int | tuple[int, int]]]:
    return protobuf_fields(data, span[0], span[1])


def decode_text(data: mmap, span: tuple[int, int]) -> str:
    return bytes(data[span[0] : span[1]]).decode("utf-8", errors="replace")


def tensor_data_types(data: mmap, span: tuple[int, int]) -> list[int]:
    return [
        value
        for number, wire_type, value in nested_fields(data, span)
        if number == 2 and wire_type == 0 and isinstance(value, int)
    ]


def sparse_tensor_data_types(data: mmap, span: tuple[int, int]) -> list[int]:
    result: list[int] = []
    for number, wire_type, value in nested_fields(data, span):
        if number == 1 and wire_type == 2 and isinstance(value, tuple):
            result.extend(tensor_data_types(data, value))
    return result


def value_info_type(data: mmap, span: tuple[int, int]) -> tuple[str | None, list[int]]:
    name: str | None = None
    element_types: list[int] = []
    for number, wire_type, value in nested_fields(data, span):
        if wire_type != 2 or not isinstance(value, tuple):
            continue
        if number == 1:
            name = decode_text(data, value)
        elif number == 2:
            for type_number, type_wire, type_value in nested_fields(data, value):
                if (
                    type_number != 1
                    or type_wire != 2
                    or not isinstance(type_value, tuple)
                ):
                    continue
                element_types.extend(
                    type_value_value
                    for element_number, element_wire, type_value_value in nested_fields(
                        data, type_value
                    )
                    if element_number == 1
                    and element_wire == 0
                    and isinstance(type_value_value, int)
                )
    return name, element_types


def collect_graph(data: mmap, span: tuple[int, int], result: dict[str, object]) -> None:
    for number, wire_type, value in nested_fields(data, span):
        if wire_type != 2 or not isinstance(value, tuple):
            continue
        if number == 1:
            collect_node(data, value, result)
        elif number == 5:
            result["initializers"].extend(tensor_data_types(data, value))  # type: ignore[union-attr]
        elif number == 15:
            result["sparse_initializers"].extend(  # type: ignore[union-attr]
                sparse_tensor_data_types(data, value)
            )
        elif number in (11, 12, 13):
            name, element_types = value_info_type(data, value)
            bucket = {11: "inputs", 12: "outputs", 13: "value_info"}[number]
            result[bucket].append({"name": name, "element_types": element_types})  # type: ignore[union-attr]


def collect_node(data: mmap, span: tuple[int, int], result: dict[str, object]) -> None:
    op_type: str | None = None
    node_name: str | None = None
    attributes: list[tuple[int, int]] = []
    for number, wire_type, value in nested_fields(data, span):
        if wire_type != 2 or not isinstance(value, tuple):
            continue
        if number == 3:
            node_name = decode_text(data, value)
        elif number == 4:
            op_type = decode_text(data, value)
        elif number == 5:
            attributes.append(value)
    result["node_types"].append(op_type)  # type: ignore[union-attr]
    if op_type == "Cast":
        for attribute in attributes:
            for number, wire_type, value in nested_fields(data, attribute):
                if number == 3 and wire_type == 0 and isinstance(value, int):
                    result["cast_targets"].append(  # type: ignore[union-attr]
                        {"node": node_name, "element_type": value}
                    )
    for attribute in attributes:
        collect_attribute(data, attribute, result)


def collect_attribute(
    data: mmap, span: tuple[int, int], result: dict[str, object]
) -> None:
    for number, wire_type, value in nested_fields(data, span):
        if wire_type != 2 or not isinstance(value, tuple):
            continue
        if number == 5:
            result["tensor_attributes"].extend(  # type: ignore[union-attr]
                tensor_data_types(data, value)
            )
        elif number == 10:
            result["tensor_attributes"].extend(  # type: ignore[union-attr]
                tensor_data_types(data, value)
            )
        elif number in (6, 11):
            collect_graph(data, value, result)
        elif number == 22:
            result["sparse_tensor_attributes"].extend(  # type: ignore[union-attr]
                sparse_tensor_data_types(data, value)
            )
        elif number == 23:
            result["sparse_tensor_attributes"].extend(  # type: ignore[union-attr]
                sparse_tensor_data_types(data, value)
            )


def summarize_types(values: list[int]) -> dict[str, int]:
    counts = Counter(values)
    return {
        ONNX_DATA_TYPES.get(element_type, f"UNKNOWN_{element_type}"): count
        for element_type, count in sorted(counts.items())
    }


def inspect_model(model_path: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with model_path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    model_sha256 = digest.hexdigest()
    if model_sha256 != EXPECTED_MODEL_SHA256:
        raise ValueError(f"Unexpected ONNX SHA-256: {model_sha256}")

    result: dict[str, object] = {
        "initializers": [],
        "sparse_initializers": [],
        "tensor_attributes": [],
        "sparse_tensor_attributes": [],
        "inputs": [],
        "outputs": [],
        "value_info": [],
        "node_types": [],
        "cast_targets": [],
    }
    with model_path.open("rb") as stream:
        with mmap(stream.fileno(), 0, access=ACCESS_READ) as data:
            model_fields = list(protobuf_fields(data, 0, len(data)))
            graph_span = next(
                value
                for number, wire_type, value in model_fields
                if number == 7 and wire_type == 2 and isinstance(value, tuple)
            )
            producer_name = next(
                (
                    decode_text(data, value)
                    for number, wire_type, value in model_fields
                    if number == 2 and wire_type == 2 and isinstance(value, tuple)
                ),
                None,
            )
            producer_version = next(
                (
                    decode_text(data, value)
                    for number, wire_type, value in model_fields
                    if number == 3 and wire_type == 2 and isinstance(value, tuple)
                ),
                None,
            )
            opsets = []
            for number, wire_type, value in model_fields:
                if number != 8 or wire_type != 2 or not isinstance(value, tuple):
                    continue
                domain = ""
                version = None
                for opset_number, opset_wire, opset_value in nested_fields(data, value):
                    if (
                        opset_number == 1
                        and opset_wire == 2
                        and isinstance(opset_value, tuple)
                    ):
                        domain = decode_text(data, opset_value)
                    elif (
                        opset_number == 2
                        and opset_wire == 0
                        and isinstance(opset_value, int)
                    ):
                        version = opset_value
                opsets.append({"domain": domain, "version": version})
            collect_graph(data, graph_span, result)

    tensor_groups = {
        key: result[key]
        for key in (
            "initializers",
            "sparse_initializers",
            "tensor_attributes",
            "sparse_tensor_attributes",
        )
    }
    all_tensor_types = [
        element_type
        for values in tensor_groups.values()
        for element_type in values  # type: ignore[union-attr]
    ]
    floating_types = [
        element_type
        for element_type in all_tensor_types
        if element_type in (1, 10, 11, 14, 15, 16, 17, 18, 19, 20, 23)
    ]
    non_float32_casts = [
        cast
        for cast in result["cast_targets"]  # type: ignore[union-attr]
        if cast["element_type"] != 1
    ]
    input_types = {
        item["name"]: item["element_types"] for item in result["inputs"]  # type: ignore[union-attr]
    }
    output_types = {
        item["name"]: item["element_types"] for item in result["outputs"]  # type: ignore[union-attr]
    }

    return {
        "schema": "talos-onnx-static-dtype-inspection-v1",
        "inspection_mode": "protobuf_static_read_only_no_onnx_runtime_session",
        "artifact": {
            "path": str(model_path),
            "size_bytes": model_path.stat().st_size,
            "sha256": model_sha256,
        },
        "model_metadata": {
            "producer_name": producer_name,
            "producer_version": producer_version,
            "opsets": opsets,
        },
        "tensor_data_type_counts": {
            key: summarize_types(values)  # type: ignore[arg-type]
            for key, values in tensor_groups.items()
        },
        "floating_tensor_data_types": sorted(set(floating_types)),
        "input_element_types": input_types,
        "output_element_types": output_types,
        "cast_targets": result["cast_targets"],
        "graph_node_count": len(result["node_types"]),  # type: ignore[arg-type]
        "graph_value_info_count": len(result["value_info"]),  # type: ignore[arg-type]
        "static_fp32_conclusion": bool(floating_types)
        and set(floating_types) == {1}
        and not non_float32_casts
        and output_types.get("last_hidden_state") == [1],
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    print(
        json.dumps(
            inspect_model(root / "models/multilingual-e5-small/onnx/model.onnx"),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
