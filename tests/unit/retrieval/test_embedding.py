"""Unit tests for embedding providers and formatters in S3.4."""

import math
from pathlib import Path
import pytest

from study_engine.retrieval.embedding import (
    E5PrefixFormatter,
    EmbeddingProvider,
    LocalONNXEmbeddingProvider,
    MockEmbeddingProvider,
)


def test_e5_prefix_formatter():
    assert (
        E5PrefixFormatter.format_query("proceso zombie")
        == "query: proceso zombie"
    )
    assert E5PrefixFormatter.format_query("  espacios  ") == "query: espacios"
    assert (
        E5PrefixFormatter.format_passage("El algoritmo Round Robin")
        == "passage: El algoritmo Round Robin"
    )


def test_mock_embedding_provider_initialization():
    prov = MockEmbeddingProvider(dimensions=384)
    assert isinstance(prov, EmbeddingProvider)
    assert prov.dimensions == 384
    assert prov.provider_id == "mock"
    assert prov.model_id == "mock-sha256-v1"
    assert prov.is_test_mock is True


def test_mock_embedding_provider_properties():
    with pytest.raises(ValueError):
        MockEmbeddingProvider(dimensions=0)

    prov = MockEmbeddingProvider(dimensions=384)
    q_vec = prov.embed_query("proceso zombie")
    assert len(q_vec) == 384
    norm = math.sqrt(sum(x * x for x in q_vec))
    assert pytest.approx(norm, rel=1e-5) == 1.0

    p_vecs = prov.embed_passages(["p1", "p2"])
    assert len(p_vecs) == 2
    assert len(p_vecs[0]) == 384


def test_mock_embedding_provider_non_multiple_of_32_dimensions():
    # 50 is not a multiple of 32, which tests the inner break branch
    prov = MockEmbeddingProvider(dimensions=50)
    vec = prov.embed_query("test non multiple")
    assert len(vec) == 50
    norm = math.sqrt(sum(x * x for x in vec))
    assert pytest.approx(norm, rel=1e-5) == 1.0


def test_local_onnx_embedding_provider_initialization_and_inference():
    model_path = Path("models/multilingual-e5-small/onnx/model.onnx")
    tok_path = Path("models/multilingual-e5-small/onnx/tokenizer.json")
    if not (model_path.exists() and tok_path.exists()):
        pytest.skip("Local ONNX model files not downloaded.")

    provider = LocalONNXEmbeddingProvider(
        model_path=model_path,
        tokenizer_path=tok_path,
    )
    assert provider.provider_id == "local_onnx"
    assert provider.model_id == "multilingual-e5-small"
    assert provider.dimensions == 384
    assert provider.is_test_mock is False

    # Empty list
    assert provider.embed_passages([]) == []

    # Single query
    q_vec = provider.embed_query("¿Qué es un proceso zombie?")
    assert len(q_vec) == 384
    q_norm = math.sqrt(sum(x * x for x in q_vec))
    assert pytest.approx(q_norm, rel=1e-4) == 1.0

    # Multiple passages
    passages = [
        "Un proceso zombie es un proceso que ha finalizado su ejecución.",
        "Árbol binario de búsqueda en lenguaje C.",
    ]
    p_vecs = provider.embed_passages(passages)
    assert len(p_vecs) == 2
    assert len(p_vecs[0]) == 384
    assert len(p_vecs[1]) == 384


def test_local_onnx_embedding_provider_missing_files(tmp_path: Path):
    fake_model = tmp_path / "fake_model.onnx"
    fake_tok = tmp_path / "fake_tok.json"

    with pytest.raises(FileNotFoundError) as exc_model:
        LocalONNXEmbeddingProvider(
            model_path=fake_model, tokenizer_path=fake_tok
        )
    assert "ONNX model file not found" in str(exc_model.value)

    fake_model.write_text("dummy")
    with pytest.raises(FileNotFoundError) as exc_tok:
        LocalONNXEmbeddingProvider(
            model_path=fake_model, tokenizer_path=fake_tok
        )
    assert "Tokenizer file not found" in str(exc_tok.value)


def test_local_onnx_empty_infer_and_import_error(
    monkeypatch, tmp_path: Path
):
    model_path = Path("models/multilingual-e5-small/onnx/model.onnx")
    tok_path = Path("models/multilingual-e5-small/onnx/tokenizer.json")
    if not (model_path.exists() and tok_path.exists()):
        pytest.skip("Local ONNX model files not downloaded.")

    from study_engine.retrieval.embedding import LocalONNXEmbeddingProvider

    prov = LocalONNXEmbeddingProvider(
        model_path=model_path, tokenizer_path=tok_path
    )
    assert prov._infer([]) == []

    # Simulate missing dependency
    import builtins
    orig_import = builtins.__import__

    def mock_import(name, *args, **kwargs):
        if name == "onnxruntime":
            raise ImportError("No module named onnxruntime")
        return orig_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", mock_import)
    with pytest.raises(ImportError) as exc:
        LocalONNXEmbeddingProvider(
            model_path=model_path, tokenizer_path=tok_path
        )
    assert "LocalONNXEmbeddingProvider requires" in str(exc.value)
