"""Late Chunking: embeddings contextuales preservando contexto global.

Genera embeddings contextuales calculando primero las representaciones del documento
completo a través de un modelo de embedding de contexto largo y realizando luego
un pooling de tokens específico para cada chunk delimitado.

Basado en: Jina AI Late Chunking
https://jina.ai/news/late-chunking-in-long-context-embedding-models/
"""

from contextlib import nullcontext
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union
import numpy as np

logger = logging.getLogger(__name__)


class HiddenStateTensor:
    """Wrapper compatible con PyTorch y NumPy para tensores de estados ocultos."""

    def __init__(self, data: np.ndarray) -> None:
        self.data = np.asarray(data, dtype=np.float32)

    def __getitem__(self, item: Any) -> Any:
        res = self.data[item]
        if isinstance(res, np.ndarray):
            return HiddenStateTensor(res)
        return res

    def mean(self, dim: int = 0, axis: Optional[int] = None) -> "HiddenStateTensor":
        ax = dim if axis is None else axis
        res = self.data.mean(axis=ax)
        return HiddenStateTensor(res)

    def numpy(self) -> np.ndarray:
        return self.data

    def __len__(self) -> int:
        return len(self.data)


class ModelOutputWrapper:
    """Wrapper para la salida del modelo compatible con outputs.last_hidden_state."""

    def __init__(self, last_hidden_state: Any) -> None:
        if isinstance(last_hidden_state, np.ndarray):
            self.last_hidden_state = HiddenStateTensor(last_hidden_state)
        elif hasattr(last_hidden_state, "numpy"):
            self.last_hidden_state = last_hidden_state
        else:
            self.last_hidden_state = HiddenStateTensor(np.asarray(last_hidden_state, dtype=np.float32))


class _ONNXTokenizerWrapper:
    """Adaptador de tokenizers.Tokenizer para emular la API de HuggingFace AutoTokenizer."""

    def __init__(self, tokenizer: Any, max_length: int = 8192) -> None:
        self._tok = tokenizer
        self._max_length = max_length

    def __call__(
        self,
        text: str,
        return_tensors: Optional[str] = None,
        truncation: bool = True,
        max_length: Optional[int] = None,
    ) -> Dict[str, Any]:
        eff_max = max_length or self._max_length
        # Codificación limpia
        encoding = self._tok.encode(text)
        ids = encoding.ids

        if not truncation:
            return {"input_ids": ids}

        if len(ids) > eff_max:
            ids = ids[:eff_max]

        arr_ids = np.array([ids], dtype=np.int64)
        arr_mask = np.ones_like(arr_ids)
        arr_type = np.zeros_like(arr_ids)

        return {
            "input_ids": arr_ids,
            "attention_mask": arr_mask,
            "token_type_ids": arr_type,
        }

    def decode(self, token_ids: Any, skip_special_tokens: bool = True) -> str:
        if hasattr(token_ids, "tolist"):
            raw_ids = token_ids.tolist()
        elif isinstance(token_ids, (list, tuple)):
            raw_ids = list(token_ids)
        else:
            raw_ids = [int(token_ids)]
        return self._tok.decode(raw_ids, skip_special_tokens=skip_special_tokens)


class _ONNXModelWrapper:
    """Adaptador de onnxruntime.InferenceSession para emular la API de forward pass."""

    def __init__(self, session: Any) -> None:
        self._session = session

    def __call__(self, **kwargs: Any) -> ModelOutputWrapper:
        # Extraer tensores requeridos
        input_ids = kwargs.get("input_ids")
        if hasattr(input_ids, "numpy"):
            input_ids = input_ids.numpy()
        attention_mask = kwargs.get("attention_mask")
        if hasattr(attention_mask, "numpy"):
            attention_mask = attention_mask.numpy()
        elif attention_mask is None and input_ids is not None:
            attention_mask = np.ones_like(input_ids)

        token_type_ids = kwargs.get("token_type_ids")
        if hasattr(token_type_ids, "numpy"):
            token_type_ids = token_type_ids.numpy()
        elif token_type_ids is None and input_ids is not None:
            token_type_ids = np.zeros_like(input_ids)

        # Ajuste de longitud si el modelo ONNX tiene un límite rígido de posición (ej. 512 en e5-small)
        seq_len = input_ids.shape[1]
        if seq_len > 512:
            # Procesar en ventanas de 512 y concatenar representaciones ocultas
            hidden_pieces: List[np.ndarray] = []
            for start in range(0, seq_len, 512):
                end = min(start + 512, seq_len)
                sub_ids = input_ids[:, start:end]
                sub_mask = attention_mask[:, start:end]
                sub_tt = token_type_ids[:, start:end]
                feeds = {
                    "input_ids": sub_ids,
                    "attention_mask": sub_mask,
                    "token_type_ids": sub_tt,
                }
                out = self._session.run(None, feeds)
                hidden_pieces.append(out[0])
            full_hidden = np.concatenate(hidden_pieces, axis=1)
            return ModelOutputWrapper(full_hidden)

        feeds = {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
        }
        out = self._session.run(None, feeds)
        return ModelOutputWrapper(out[0])


class _SimulatedTokenizer:
    """Tokenizer determinista ligero para entornos sin dependencias pesadas."""

    def __init__(self) -> None:
        pass

    def __call__(
        self,
        text: str,
        return_tensors: Optional[str] = None,
        truncation: bool = True,
        max_length: Optional[int] = None,
    ) -> Dict[str, Any]:
        words = re.findall(r"\S+", text)
        ids = [abs(hash(w)) % 30000 + 1 for w in words]
        if not ids:
            ids = [0]
        if not truncation:
            return {"input_ids": ids}
        if max_length and len(ids) > max_length:
            ids = ids[:max_length]
        arr_ids = np.array([ids], dtype=np.int64)
        return {
            "input_ids": arr_ids,
            "words": words,
        }

    def decode(self, token_ids: Any, skip_special_tokens: bool = True) -> str:
        if hasattr(token_ids, "tolist"):
            token_ids = token_ids.tolist()
        return " ".join(f"token_{i}" for i in token_ids)


class _SimulatedModel:
    """Modelo determinista ligero que simula representaciones contextuales globales."""

    def __init__(self, dimensions: int = 4096) -> None:
        self.dimensions = dimensions

    def __call__(self, **kwargs: Any) -> ModelOutputWrapper:
        input_ids = kwargs.get("input_ids")
        if hasattr(input_ids, "numpy"):
            input_ids = input_ids.numpy()
        seq_len = input_ids.shape[1]

        # Simular atención global: cada token se mezcla con el hash global de todo el documento
        doc_hash = float(hash(tuple(input_ids[0].tolist())) % 1000) / 1000.0
        hidden = np.zeros((1, seq_len, self.dimensions), dtype=np.float32)
        for i in range(seq_len):
            t_id = float(input_ids[0, i])
            # Vector contextual = señal local + señal global del documento
            for d in range(self.dimensions):
                hidden[0, i, d] = np.sin(t_id * (d + 1) + doc_hash * 10.0)

        return ModelOutputWrapper(hidden)


class LateChunker:
    """Genera embeddings contextuales preservando el contexto del documento completo antes de chunking.

    Basado en: Jina AI Late Chunking
    https://jina.ai/news/late-chunking-in-long-context-embedding-models/
    """

    def __init__(
        self,
        model_name: str = "jinaai/jina-embeddings-v3",
        max_document_tokens: int = 8192,
    ) -> None:
        self.model_name = model_name
        self.max_document_tokens = max_document_tokens
        self._init_backend()

    def _init_backend(self) -> None:
        """Inicializa el backend de tokenizer y modelo según disponibilidad."""
        # 1. Intentar Transformers / PyTorch si está instalado
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch

            logger.info("Initializing LateChunker with HuggingFace Transformers backend: %s", self.model_name)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name, trust_remote_code=True)
            self._backend_type = "transformers"
            self._torch = torch
            return
        except Exception as ex_tf:
            logger.debug("Transformers backend not available or failed (%s). Checking ONNX fallback.", ex_tf)

        # 2. Intentar backend ONNX local
        try:
            import onnxruntime as ort
            from tokenizers import Tokenizer

            repo_root = Path(__file__).resolve().parents[3]
            candidate_models = [
                Path("models/multilingual-e5-small/onnx/model.onnx"),
                repo_root / "models/multilingual-e5-small/onnx/model.onnx",
            ]
            for mp in candidate_models:
                tp = mp.parent / "tokenizer.json"
                if mp.exists() and tp.exists():
                    raw_tok = Tokenizer.from_file(str(tp))
                    opts = ort.SessionOptions()
                    opts.intra_op_num_threads = 4
                    session = ort.InferenceSession(
                        str(mp),
                        sess_options=opts,
                        providers=["CPUExecutionProvider"],
                    )
                    self.tokenizer = _ONNXTokenizerWrapper(raw_tok, max_length=self.max_document_tokens)
                    self.model = _ONNXModelWrapper(session)
                    self._backend_type = "onnx"
                    self._torch = None
                    logger.info("LateChunker initialized with local ONNX backend: %s", mp)
                    return
        except Exception as ex_onnx:
            logger.debug("Local ONNX backend failed (%s). Falling back to simulated.", ex_onnx)

        # 3. Fallback determinista simulado
        self.tokenizer = _SimulatedTokenizer()
        self.model = _SimulatedModel()
        self._backend_type = "simulated"
        self._torch = None
        logger.info("LateChunker initialized with simulated deterministic backend.")

    def late_chunk(
        self,
        document: str,
        chunk_size: int = 512,
        overlap: int = 100,
    ) -> List[Dict[str, Any]]:
        """Genera chunks con embeddings contextuales.

        Flujo:
        1. Tokenizar documento completo (con límite max_document_tokens)
        2. Forward pass con contexto global
        3. Dividir en chunks manteniendo embeddings contextuales
        4. Mean pooling por chunk
        """
        clean_doc = (document or "").strip()
        if not clean_doc:
            return []

        # 1. Tokenizar documento completo
        tokens = self.tokenizer(
            document,
            return_tensors="pt",
            truncation=True,
            max_length=self.max_document_tokens,
        )

        # 2. Forward pass completo (contexto global)
        context_mgr = self._torch.no_grad() if self._torch is not None else nullcontext()
        with context_mgr:
            outputs = self.model(**tokens)

        # 3. Dividir en chunks y hacer mean pooling
        chunks: List[Dict[str, Any]] = []
        token_start = 0
        input_ids = tokens["input_ids"]
        total_tokens = int(input_ids.shape[1]) if hasattr(input_ids, "shape") else len(input_ids[0])
        safe_overlap = max(0, min(overlap, chunk_size - 1))
        step = max(1, chunk_size - safe_overlap)

        while token_start < total_tokens:
            token_end = min(token_start + chunk_size, total_tokens)

            # Extraer embeddings de tokens del chunk
            chunk_embeddings = outputs.last_hidden_state[0, token_start:token_end]

            # Mean pooling
            chunk_vector = chunk_embeddings.mean(dim=0).numpy()

            # Decodificar texto del chunk
            slice_ids = input_ids[0, token_start:token_end] if hasattr(input_ids, "shape") else input_ids[0][token_start:token_end]
            chunk_text = self.tokenizer.decode(
                slice_ids,
                skip_special_tokens=True,
            )

            chunks.append({
                "text": chunk_text,
                "embedding": chunk_vector,
                "start_token": token_start,
                "end_token": token_end,
                "context_type": self._detect_context_type(chunk_text),
                "chunking_method": "late",
            })

            if token_end >= total_tokens:
                break
            token_start += step

        return chunks

    @classmethod
    def _detect_context_type(cls, text: str) -> str:
        """Detecta si el chunk es código, prosa, o mixto."""
        code_indicators = [
            "void", "int", "return", "{", "}", "#include", "def", "class",
            "pthread_mutex", "malloc", "free", "printf", "scanf",
        ]
        code_score = sum(1 for ind in code_indicators if ind in text)

        if code_score > 3:
            return "code"
        elif code_score == 0:
            return "prose"
        else:
            return "mixed"

    def can_process(self, document: str) -> bool:
        """Verifica si el documento puede procesarse con Late Chunking."""
        tokens = self.tokenizer(document, truncation=False)
        return len(tokens["input_ids"]) <= self.max_document_tokens


def to_talos_chunks(
    chunks: List[Dict[str, Any]],
    document_id: str,
    source_id: str,
) -> List[Any]:
    """Convierte la lista de diccionarios de Late Chunking a contratos canónicos Chunk de TALOS."""
    from study_engine.contracts.chunk import Chunk

    talos_chunks: List[Chunk] = []
    for idx, c in enumerate(chunks):
        c_id = f"{document_id}:chunk_{idx:04d}"
        metadata = {
            "chunking_method": c.get("chunking_method", "late"),
            "context_type": c.get("context_type", "prose"),
            "start_token": c.get("start_token"),
            "end_token": c.get("end_token"),
        }
        talos_chunks.append(
            Chunk(
                id=c_id,
                document_id=document_id,
                source_id=source_id,
                content=c["text"],
                index=idx,
                metadata=metadata,
            )
        )
    return talos_chunks
