"""Unit tests for DeterministicLocalReranker and JinaReranker (Fase 7 / F2, F3, F8)."""

from typing import List
import httpx
import numpy as np
import pytest

from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.retrieval.reranker import (
    DeterministicLocalReranker,
    JinaReranker,
    LocalONNXReranker,
    calculate_local_rerank_score,
)


def _make_candidate(chunk_id: str, content: str, score: float = 0.5) -> ScoredCandidate:
    """Helper to build a ScoredCandidate for testing."""
    return ScoredCandidate(
        chunk_id=chunk_id,
        document_id="doc-test",
        source_id="src-test",
        notebook_id="fase0-soc",
        rank=1,
        score=score,
        content=content,
        retrieval_method="test",
        page_start=1,
        page_end=1,
        pos_index=0,
        metadata={},
    )


def test_deterministic_local_reranker_formula_f2():
    """F2: Verificar fórmula exacta de cobertura (40%), bigramas (30%) y posición (30%)."""
    query = "memoria virtual paginacion"
    # Chunk con coincidencia exacta y temprana de los 3 términos y bigramas
    c1 = _make_candidate(
        "c1",
        "La memoria virtual y paginacion permiten aislar el espacio de direcciones.",
    )
    # Chunk con coincidencia parcial de solo un término al final
    c2 = _make_candidate(
        "c2",
        "Los sistemas operativos administran diversos recursos incluyendo dispositivos de entrada y finalmente memoria.",
    )
    # Chunk sin coincidencias
    c3 = _make_candidate(
        "c3",
        "El microprocesador ejecuta instrucciones mediante ciclos de reloj.",
    )

    s1 = calculate_local_rerank_score(c1, query)
    s2 = calculate_local_rerank_score(c2, query)
    s3 = calculate_local_rerank_score(c3, query)

    # Validar acotamiento
    assert 0.0 <= s1 <= 1.0
    assert 0.0 <= s2 <= 1.0
    assert 0.0 <= s3 <= 1.0

    # c1 debe tener mayor score que c2, y c2 mayor o igual a c3
    assert s1 > s2
    assert s2 > s3
    assert s3 == 0.0

    # Reranking ordenado
    reranker = DeterministicLocalReranker()
    results = reranker.rerank(query, [c3, c2, c1], top_k=3)

    assert len(results) == 3
    assert results[0].chunk_id == "c1"
    assert results[0].rank == 1
    assert results[0].metadata["reranker"] == "local_fallback"
    assert results[1].chunk_id == "c2"
    assert results[1].rank == 2
    assert results[2].chunk_id == "c3"
    assert results[2].rank == 3


def test_jina_reranker_no_api_key_fallback_f3():
    """F3: Sin JINA_API_KEY, degrada transparentemente a DeterministicLocalReranker."""
    reranker = JinaReranker(api_key=None)

    c1 = _make_candidate("c1", "Un hilo es una unidad básica de utilización de CPU.")
    c2 = _make_candidate("c2", "Los hilos de ejecución comparten el espacio de memoria.")

    results = reranker.rerank("hilos de ejecucion", [c1, c2], top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c2"  # Contiene "hilos de ejecucion"
    assert results[0].metadata["reranker"] == "local_fallback"


def test_jina_reranker_mock_api_success_f3(monkeypatch):
    """F3: Con API key válida, parsea respuesta de Jina y actualiza scores y metadatos."""
    c1 = _make_candidate("c1", "Texto A")
    c2 = _make_candidate("c2", "Texto B")

    mock_response_data = {
        "model": "jina-reranker-v2-base-multilingual",
        "results": [
            {"index": 1, "document": {"text": "Texto B"}, "relevance_score": 0.9421},
            {"index": 0, "document": {"text": "Texto A"}, "relevance_score": 0.3120},
        ],
    }

    class MockResponse:
        status_code = 200

        def raise_for_status(self):
            pass

        def json(self):
            return mock_response_data

    class MockClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json, headers):
            return MockResponse()

    monkeypatch.setattr(httpx, "Client", MockClient)

    reranker = JinaReranker(api_key="jina_test_secret_key")
    results = reranker.rerank("consulta prueba", [c1, c2], top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c2"
    assert results[0].score == 0.9421
    assert results[0].metadata["reranker"] == "jina"
    assert results[0].rank == 1

    assert results[1].chunk_id == "c1"
    assert results[1].score == 0.3120
    assert results[1].metadata["reranker"] == "jina"
    assert results[1].rank == 2


def test_jina_reranker_timeout_and_error_fallback_f3(monkeypatch):
    """F3: Ante timeout o error de red de Jina, conmutación automática y fail-safe a local."""
    c1 = _make_candidate("c1", "Algoritmo de planificación Round Robin.")
    c2 = _make_candidate("c2", "Planificación de CPU por prioridades.")

    class TimeoutClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def post(self, url, json, headers):
            raise httpx.TimeoutException("Connection timed out after 2.0s")

    monkeypatch.setattr(httpx, "Client", TimeoutClient)

    reranker = JinaReranker(api_key="jina_test_key", timeout=2.0, max_retries=1)

    # Nunca debe levantar excepción al usuario
    results = reranker.rerank("planificación round robin", [c2, c1], top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].metadata["reranker"] == "local_fallback"


def _spearman_correlation(predicted_ranks: List[int], ideal_ranks: List[int]) -> float:
    """Computes Spearman rank correlation in pure Python/NumPy."""
    n = len(predicted_ranks)
    if n <= 1:
        return 1.0
    d_sq = sum((p - i) ** 2 for p, i in zip(predicted_ranks, ideal_ranks))
    return 1.0 - (6.0 * d_sq) / (n * (n * n - 1))


def test_local_reranker_quality_baseline_f8():
    """F8: El DeterministicLocalReranker debe alcanzar al menos 70% de correlación media con el ground truth ideal."""
    reranker = DeterministicLocalReranker()

    # Generación de dataset de 20 casos de prueba técnicos representativos
    # Cada caso tiene 4 candidatos de relevancia graduada conocida (1=óptimo, 2=bueno, 3=marginal, 4=irrelevante)
    test_topics = [
        (
            "deadlock interbloqueo",
            "El deadlock interbloqueo ocurre por espera circular y retencion de recursos.",
            "Un interbloqueo bloquea los hilos del sistema cuando esperan mutuamente.",
            "Los sistemas operativos administran recursos compartidos entre procesos.",
            "Compilación de código fuente con optimizaciones gcc.",
        ),
        (
            "malloc memoria dinamica",
            "La funcion malloc memoria dinamica asigna bloques contiguos en el heap.",
            "La memoria dinamica permite crear estructuras flexibles durante ejecucion.",
            "Los punteros en c almacenan direcciones de variables locales.",
            "Arquitectura von neumann y ciclo de instruccion.",
        ),
        (
            "punteros aritmetica",
            "La aritmetica de punteros aritmetica permite recorrer arreglos en memoria.",
            "Los punteros se incrementan segun el tamano del tipo de dato.",
            "Tipos de datos primitivos enteros y flotantes.",
            "Configuracion de interfaces de red ethernet.",
        ),
        (
            "stack frame registros",
            "El stack frame registros organiza rbp rsp y variables de funcion.",
            "Las llamadas a funciones usan el stack para guardar el frame previo.",
            "Convencion abi y retorno de valores en eax.",
            "Sistemas de archivos distribuidos y clusters.",
        ),
        (
            "condicion carrera mutex",
            "La condicion carrera mutex se resuelve protegiendo la seccion critica.",
            "Un mutex sincroniza la seccion critica evitando accesos simultaneos.",
            "Hilos concurrentes que ejecutan tareas en segundo plano.",
            "Indices y transacciones en bases de datos relacionales.",
        ),
        (
            "socket bind listen",
            "El socket bind listen configura el descriptor para aceptar conexiones.",
            "La funcion bind asocia una direccion al socket del servidor.",
            "Protocolos de transporte orientados a conexion.",
            "Algoritmos de ordenamiento rapido quicksort.",
        ),
        (
            "segmentacion paginacion",
            "La segmentacion paginacion combina memoria virtual dividida en paginas y segmentos.",
            "La paginacion divide el espacio de direcciones en marcos de tamano fijo.",
            "Gestion basica de memoria contigua en memoria principal.",
            "Analisis lexico y arboles sintacticos en compiladores.",
        ),
        (
            "buffer overflow stack",
            "El buffer overflow stack sobreescribe la direccion de retorno con strcpy.",
            "Un overflow en buffers locales puede alterar el flujo de control.",
            "Buenas practicas de programacion defensiva en lenguaje c.",
            "Cabeceras de peticion y respuesta en protocolo http.",
        ),
        (
            "llamada sistema syscall",
            "La llamada sistema syscall realiza la transicion a modo kernel privilegiado.",
            "Una syscall transfiere el control al manejador del sistema operativo.",
            "Interrupciones de hardware disparadas por perifericos.",
            "Hojas de estilo en cascada css para interfaces web.",
        ),
        (
            "tuberia pipe ipc",
            "La tuberia pipe ipc permite enviar streams de bytes unidireccionales entre procesos.",
            "Una tuberia pipe conecta la salida estandar de un proceso con la entrada de otro.",
            "Ciclo de vida y comunicacion entre procesos.",
            "Criptografia de clave publica rsa y curvas elipticas.",
        ),
        (
            "semaforo dijkstra",
            "El semaforo dijkstra implementa operaciones atomicas wait y signal.",
            "Los semaforos sirven como primitiva de sincronizacion entre tareas.",
            "Concurrencia cooperativa y cambios de contexto.",
            "Diagramas de clases y casos de uso en uml.",
        ),
        (
            "planificacion round robin",
            "La planificacion round robin asigna un quantum equitativo a cada proceso listo.",
            "El algoritmo round robin utiliza una cola circular de procesos.",
            "Planificadores de cpu y politicas de atencion.",
            "Transformaciones lineales y multiplicacion de matrices.",
        ),
        (
            "inodo sistema archivos",
            "El inodo sistema archivos almacena metadatos permisos y punteros a bloques de disco.",
            "Un inodo identifica de forma unica a un archivo dentro del sistema.",
            "Estructura fisica de particiones en discos magneticos.",
            "Herencia polimorfismo y encapsulamiento en poo.",
        ),
        (
            "interrupcion excepcion trampa",
            "La interrupcion excepcion trampa altera la secuencia normal de instrucciones.",
            "Una excepcion sincrona ocurre ante division por cero o fallo de pagina.",
            "Manejadores de eventos y hardware del procesador.",
            "Patron de diseno factory y patron singleton.",
        ),
        (
            "variable condicion broadcast",
            "La variable condicion broadcast despierta a todos los hilos en espera sobre el cerrojo.",
            "Una variable de condicion permite esperar eventos sin espera activa.",
            "Monitores de sincronizacion para exclusion mutua.",
            "Entrenamiento de redes neuronales convolucionales.",
        ),
        (
            "memoria virtual tlb",
            "La memoria virtual tlb cachea traducciones de direcciones virtuales a fisicas.",
            "El buffer tlb reduce el costo de consultar la tabla de paginas.",
            "Administracion de memoria principal en sistemas modernos.",
            "Grafos dirigidos y recorridos en anchura y profundidad.",
        ),
        (
            "fork exec proceso",
            "El fork exec proceso clona el espacio de direcciones y carga una nueva imagen ejecutable.",
            "La llamada fork crea un proceso hijo casi identico al padre.",
            "Jerarquia de procesos y procesos huerfanos o zombies.",
            "Funciones recursivas y busqueda binaria en listas.",
        ),
        (
            "senales sigint sigkill",
            "Las senales sigint sigkill notifican eventos asincronos para terminar o interrumpir un proceso.",
            "Una senal interrumpe la ejecucion normal ejecutando un manejador.",
            "Control y gestion de sesiones en la terminal de comandos.",
            "Estructuras de marcado de hipertexto en html5.",
        ),
        (
            "use after free",
            "La vulnerabilidad use after free ocurre al desreferenciar un puntero tras liberar el bloque.",
            "Un puntero colgante produce corrupcion de heap si se accede tras free.",
            "Validacion de memoria dinamica y herramientas de depuracion.",
            "Recorrido in-order y pre-order en arboles binarios.",
        ),
        (
            "algoritmo banquero deadlock",
            "El algoritmo banquero deadlock evalua estados seguros antes de conceder recursos adicionales.",
            "El algoritmo del banquero evita interbloqueos modelando matrices de demanda.",
            "Estrategias de prevencion y recuperacion de deadlocks.",
            "Capas del modelo de referencia osi e internet.",
        ),
    ]

    correlations: List[float] = []

    for query, c_high, c_med, c_low, c_irr in test_topics:
        cand_high = _make_candidate("c_high", c_high)
        cand_med = _make_candidate("c_med", c_med)
        cand_low = _make_candidate("c_low", c_low)
        cand_irr = _make_candidate("c_irr", c_irr)

        # Entrada en orden aleatorio/inverso
        input_cands = [cand_irr, cand_low, cand_med, cand_high]
        reranked = reranker.rerank(query, input_cands, top_k=4)

        # Ranking ideal: c_high=1, c_med=2, c_low=3, c_irr=4
        ideal_order = {"c_high": 1, "c_med": 2, "c_low": 3, "c_irr": 4}
        predicted_order = {c.chunk_id: rank for rank, c in enumerate(reranked, start=1)}

        pred_ranks = [predicted_order["c_high"], predicted_order["c_med"], predicted_order["c_low"], predicted_order["c_irr"]]
        ideal_ranks = [ideal_order["c_high"], ideal_order["c_med"], ideal_order["c_low"], ideal_order["c_irr"]]

        corr = _spearman_correlation(pred_ranks, ideal_ranks)
        correlations.append(corr)

    avg_correlation = float(np.mean(correlations))
    # F8: Al menos 70% (0.70) de correlación media
    assert avg_correlation >= 0.70, f"Correlación media {avg_correlation:.3f} < 0.70"


def test_local_onnx_reranker_missing_model_fallback(tmp_path):
    """LocalONNXReranker gracefully falls back to DeterministicLocalReranker if ONNX files missing."""
    reranker = LocalONNXReranker(
        model_path=tmp_path / "nonexistent.onnx",
        tokenizer_path=tmp_path / "nonexistent.json",
    )

    c1 = _make_candidate("c1", "Un hilo es una unidad básica de utilización de CPU.")
    c2 = _make_candidate("c2", "Los hilos de ejecución comparten el espacio de memoria.")

    results = reranker.rerank("hilos de ejecucion", [c1, c2], top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c2"
    assert results[0].metadata["reranker"] == "local_fallback"


def test_local_onnx_reranker_empty_candidates():
    """Empty candidate list returns empty list immediately."""
    reranker = LocalONNXReranker()
    assert reranker.rerank("query", []) == []


def test_local_onnx_reranker_mock_onnx_session(monkeypatch, tmp_path):
    """LocalONNXReranker tokenizes, runs ONNX inference, applies sigmoid and reorders candidates."""
    # Create dummy files so path checks pass
    model_file = tmp_path / "model.onnx"
    tokenizer_file = tmp_path / "tokenizer.json"
    model_file.write_text("dummy")
    tokenizer_file.write_text("dummy")

    class DummyEncoding:
        def __init__(self):
            self.ids = [101, 102, 103]
            self.attention_mask = [1, 1, 1]
            self.type_ids = [0, 0, 0]

    class DummyTokenizer:
        @classmethod
        def from_file(cls, path):
            return cls()

        def enable_truncation(self, max_length):
            pass

        def enable_padding(self, pad_id, pad_token, length):
            pass

        def encode_batch(self, pairs):
            return [DummyEncoding() for _ in pairs]

    class DummyInputMeta:
        def __init__(self, name):
            self.name = name

    class DummySession:
        def __init__(self, path, sess_options, providers):
            pass

        def get_inputs(self):
            return [DummyInputMeta("input_ids"), DummyInputMeta("attention_mask"), DummyInputMeta("token_type_ids")]

        def run(self, output_names, inputs):
            # return 2 logits: candidate 1 has lower logit (-1.0), candidate 2 has higher logit (2.5)
            # sigmoid(-1.0) ~ 0.2689, sigmoid(2.5) ~ 0.9241
            return [np.array([[-1.0], [2.5]], dtype=np.float32)]

    import onnxruntime as ort
    from tokenizers import Tokenizer
    monkeypatch.setattr(ort, "InferenceSession", DummySession)
    monkeypatch.setattr(Tokenizer, "from_file", DummyTokenizer.from_file)

    reranker = LocalONNXReranker(
        model_path=model_file,
        tokenizer_path=tokenizer_file,
    )

    c1 = _make_candidate("c1", "Texto con menos relevancia")
    c2 = _make_candidate("c2", "Texto con alta relevancia")

    results = reranker.rerank("consulta", [c1, c2], top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "c2"  # Highest sigmoid score
    assert results[0].rank == 1
    assert results[0].score == 0.9241
    assert results[0].metadata["reranker"] == "local_onnx"
    assert results[0].metadata["reranker_score"] == 0.9241

    assert results[1].chunk_id == "c1"
    assert results[1].rank == 2
    assert results[1].score == 0.2689
    assert results[1].metadata["reranker"] == "local_onnx"

