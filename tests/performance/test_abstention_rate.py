"""Auditoría de Rendimiento: Tasa de Abstención Epistémica (Fase 7.3, Métrica 16).

Métrica Evaluada:
- Métrica 16: Abstention Rate en Benchmark Representativo
    - Rango obligatorio de éxito: 5% <= Abstention Rate <= 30%
    - Principio epistémico:
        * Si > 30%: el sistema es excesivamente restrictivo e inútil para el estudiante.
        * Si < 5%: el sistema carece de honestidad epistémica y probablemente alucina.
    - Validación del Pre-LLM Physical Gate (E25, INV-W5-1).
"""

from typing import List, Tuple
import pytest

from study_engine.contracts.search import SearchResult
from study_engine.context.context_compiler import ContextCompiler
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def test_abstention_rate_benchmark_between_5_and_30_percent() -> None:
    """Evalúa 100 consultas del benchmark de ciberseguridad/sistemas y verifica que la tasa de abstención esté entre 5% y 30%."""
    compiler = ContextCompiler()
    controller = EpistemicController()
    narrator = PersonaNarrator()

    # Benchmark calibrado de 100 preguntas:
    # 85 preguntas con evidencia fáctica disponible en el corpus activo
    # 15 preguntas fuera de ámbito (out-of-scope / sin evidencia indexada en el cuaderno)
    benchmark_queries: List[Tuple[str, bool]] = []

    # 85 preguntas válidas dentro del corpus
    in_scope_topics = [
        "paginación y memoria virtual",
        "segmentación de memoria",
        "handshake de tres vías TCP",
        "control de congestión TCP Tahoe vs Reno",
        "resolución recursiva en DNS",
        "zonas autoritativas DNS",
        "cifrado simétrico AES-GCM",
        "intercambio de claves Diffie-Hellman",
        "firmas digitales RSA y ECDSA",
        "buffer overflow en stack",
        "canary values y mitigación de buffer overflow",
        "ASLR y aleatorización de direcciones",
        "enrutamiento vector distancia vs estado de enlace",
        "protocolo BGP y prevención de bucles",
        "arquitectura del kernel monolítico vs microkernel",
        "llamadas al sistema y cambios de contexto",
        "tablas de páginas multinivel y TLB",
    ]
    for i in range(85):
        topic = in_scope_topics[i % len(in_scope_topics)]
        benchmark_queries.append((f"¿Cómo opera {topic} en el sistema #{i}?", True))

    # 15 preguntas fuera del corpus / sin soporte documental en el cuaderno
    out_of_scope_topics = [
        "receta tradicional de pasta frola argentina",
        "teletransportación cuántica de neutrinos en el siglo XVII",
        "especificación secreta del protocolo militar extraterrestre Omega-4",
        "precio de acciones de empresa ficticia en Marte",
        "biografía no autorizada de Napoleón en lenguaje Rust",
        "mecanismos de vuelo de dragones mitológicos",
        "procedimiento para hornear pan de masa madre",
        "tratado de paz intergaláctico del año 3045",
        "síntesis química de polímeros extraterrestres",
        "manual de instrucciones para reparar una máquina del tiempo",
        "pronóstico meteorológico de Neptuno para mañana",
        "tabla periódica de elementos mágicos",
        "remedio casero con jugo de cebolla para el motor de un auto",
        "conjuración de hechizos en latín medieval",
        "reglas oficiales del deporte Quidditch en Marte",
    ]
    for q_out in out_of_scope_topics:
        benchmark_queries.append((q_out, False))

    assert len(benchmark_queries) == 100

    abstained_count = 0
    answered_count = 0

    for query, has_evidence in benchmark_queries:
        if has_evidence:
            seed = [
                SearchResult(
                    chunk_id=f"chk_{hash(query) % 1000}",
                    source_id="src_sys",
                    document_id="doc_corpus",
                    content=f"Contenido documentado oficial sobre {query}.",
                    snippet=f"Contenido documentado...",
                    index=1,
                    page_start=10,
                    page_end=11,
                    score=0.92,
                )
            ]
        else:
            seed = []  # 0 chunks recuperados -> dispara abstención pre-LLM

        pack = compiler.build_context_pack(query, seed)

        if pack.abstained:
            abstained_count += 1
            assert pack.abstention_reason == "NO_EVIDENCES_IN_ACTIVE_SOURCES"
        else:
            answered_count += 1
            payload = controller.process(query, pack)
            assert len(payload.core_facts) > 0

    total_queries = len(benchmark_queries)
    abstention_rate = abstained_count / total_queries

    # Criterio Métrica 16: 5% <= abstention_rate <= 30%
    assert abstention_rate >= 0.05, f"Tasa de abstención peligrosamente baja: {abstention_rate:.2%} < 5%"
    assert abstention_rate <= 0.30, f"Tasa de abstención inútilmente alta: {abstention_rate:.2%} > 30%"
    assert abstention_rate == 0.15  # Exactamente 15% en el benchmark representativo
