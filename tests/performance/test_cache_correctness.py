"""Auditoría de Rendimiento: Cache Correctness y Cache Hit Rate (Fase 7.3, Métricas 8 y 9).

Métricas Evaluadas:
- Métrica 8: Cache correctness 100% (6/6 propiedades verificadas formalmente):
    1. Prefijo idéntico -> mismo hash
    2. Corpus modificado -> hash diferente
    3. Notebook diferente -> namespace diferente
    4. Source filter diferente -> namespace/prefix diferente
    5. Corpus rollback -> hash reproducible
    6. Nunca se sirve contexto de otra versión (aislamiento estricto)
- Métrica 9: Cache hit rate operativo > 70% bajo workload de referencia de 100 consultas.
"""

import hashlib
from typing import Dict, List, Optional
import pytest

from study_engine.pedagogy.prompt_assembler import CanonicalPromptAssembler
from study_engine.generation.prompts import PromptBundle


class ProviderPromptCache:
    """Simulates an enterprise LLM provider's deterministic KV-cache / prefix-cache."""

    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, str]] = {}
        self.hits: int = 0
        self.misses: int = 0

    def query(self, bundle: PromptBundle) -> Dict[str, str]:
        prefix_hash = getattr(bundle, "prefix_hash", None)
        if not prefix_hash:
            h = hashlib.sha256(bundle.system_prompt.encode("utf-8")).hexdigest()
            prefix_hash = h

        if prefix_hash in self._cache:
            self.hits += 1
            return {
                "status": "hit",
                "cached_prefix_hash": prefix_hash,
                "cached_data": self._cache[prefix_hash]["content"],
            }
        else:
            self.misses += 1
            self._cache[prefix_hash] = {
                "content": bundle.system_prompt,
                "version": prefix_hash[:8],
            }
            return {
                "status": "miss",
                "cached_prefix_hash": prefix_hash,
                "cached_data": bundle.system_prompt,
            }

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0


def test_metric_8_cache_correctness_all_6_properties() -> None:
    """Verifica formalmente las 6 propiedades de corrección de caché de prefijo requeridas por Fase 7.3."""
    base_prompt = "Sos TALOS, tutor socrático soberano en ciencias de la computación."
    assembler_nb1 = CanonicalPromptAssembler(notebook_id="fadena-redes", base_system_prompt=base_prompt)
    assembler_nb2 = CanonicalPromptAssembler(notebook_id="fadena-sistemas", base_system_prompt=base_prompt)

    corpus_v1 = (
        "[CHUNK 1 | Pág 10 | Kurose] TCP es un protocolo orientado a conexión que provee entrega confiable.\n"
        "[CHUNK 2 | Pág 12 | Kurose] El handshake de 3 vías establece los números de secuencia iniciales."
    )
    corpus_v2_modified = (
        "[CHUNK 1 | Pág 10 | Kurose] TCP es un protocolo orientado a conexión que provee entrega confiable.\n"
        "[CHUNK 2 | Pág 12 | Kurose] El handshake de 3 vías establece los números de secuencia iniciales.\n"
        "[CHUNK 3 | Pág 15 | Kurose] TCP Reno introduce Fast Recovery al detectar tres ACKs duplicados."
    )
    corpus_filtered_sources = (
        "[CHUNK 1 | Pág 10 | Kurose] TCP es un protocolo orientado a conexión que provee entrega confiable."
    )

    # 1. Propiedad 1: Prefijo idéntico -> mismo hash (invarianza ante variaciones en historial/briefing)
    bundle_1a = assembler_nb1.assemble(
        user_query="¿Cómo inicia TCP?",
        corpus_pack=corpus_v1,
        dynamic_instructions="MODO CONVERSACIONAL",
        session_briefing="Sesión previa sobre capas OSI.",
        chat_history=[],
    )
    bundle_1b = assembler_nb1.assemble(
        user_query="¿Y qué número de secuencia usa el cliente?",
        corpus_pack=corpus_v1,
        dynamic_instructions="MODO FORMAL",
        session_briefing="Revisión de ISN.",
        chat_history=[{"role": "user", "content": "¿Cómo inicia TCP?"}],
    )
    assert bundle_1a.prefix_hash == bundle_1b.prefix_hash, (
        f"Falla Propiedad 1: Prefijos idénticos produjeron hashes distintos ({bundle_1a.prefix_hash} != {bundle_1b.prefix_hash})"
    )

    # 2. Propiedad 2: Corpus modificado -> hash diferente
    bundle_mod = assembler_nb1.assemble(
        user_query="¿Cómo inicia TCP?",
        corpus_pack=corpus_v2_modified,
    )
    assert bundle_1a.prefix_hash != bundle_mod.prefix_hash, (
        "Falla Propiedad 2: Corpus modificado produjo colisión con hash previo!"
    )

    # 3. Propiedad 3: Notebook diferente -> namespace diferente
    bundle_nb2 = assembler_nb2.assemble(
        user_query="¿Cómo inicia TCP?",
        corpus_pack=corpus_v1,
    )
    assert bundle_1a.prefix_hash != bundle_nb2.prefix_hash, (
        "Falla Propiedad 3: Diferentes notebooks produjeron el mismo hash de prefijo!"
    )

    # 4. Propiedad 4: Source filter diferente -> namespace/prefix diferente
    bundle_filtered = assembler_nb1.assemble(
        user_query="¿Cómo inicia TCP?",
        corpus_pack=corpus_filtered_sources,
    )
    assert bundle_1a.prefix_hash != bundle_filtered.prefix_hash, (
        "Falla Propiedad 4: Filtro de fuentes diferente produjo el mismo hash de prefijo!"
    )

    # 5. Propiedad 5: Corpus rollback -> hash reproducible
    bundle_rollback = assembler_nb1.assemble(
        user_query="¿Pregunta post-rollback?",
        corpus_pack=corpus_v1,
    )
    assert bundle_1a.prefix_hash == bundle_rollback.prefix_hash, (
        "Falla Propiedad 5: Rollback de corpus no reprodujo el hash idéntico original!"
    )

    # 6. Propiedad 6: Nunca se sirve contexto de otra versión (Aislamiento e integridad)
    cache = ProviderPromptCache()
    res_initial = cache.query(bundle_1a)
    assert res_initial["status"] == "miss"

    # Segunda consulta con idéntico prefijo -> hit
    res_hit = cache.query(bundle_1b)
    assert res_hit["status"] == "hit"
    assert res_hit["cached_prefix_hash"] == bundle_1a.prefix_hash
    assert res_hit["cached_data"] == bundle_1a.system_prompt

    # Consulta con corpus modificado -> miss obligatorio (nunca sirve v1 para v2)
    res_mod = cache.query(bundle_mod)
    assert res_mod["status"] == "miss"
    assert res_mod["cached_prefix_hash"] != bundle_1a.prefix_hash
    assert res_mod["cached_data"] == bundle_mod.system_prompt
    assert "Fast Recovery" in res_mod["cached_data"]

    # Consulta cruzada a otro notebook -> miss obligatorio (nunca sirve nb1 para nb2)
    res_nb2 = cache.query(bundle_nb2)
    assert res_nb2["status"] == "miss"
    assert res_nb2["cached_prefix_hash"] != bundle_1a.prefix_hash


def test_metric_9_cache_hit_rate_exceeds_70_percent() -> None:
    """Verifica que el cache hit rate operativo supere el 70% en un workload representativo de 100 consultas."""
    cache = ProviderPromptCache()
    assembler = CanonicalPromptAssembler(notebook_id="fadena-redes", base_system_prompt="Sos TALOS.")

    topics_corpus = {
        "tcp_handshake": "[CHUNK 1 | Pág 10 | Kurose] TCP handshake SYN, SYN-ACK, ACK.",
        "dns_security": "[CHUNK 2 | Pág 40 | Kurose] DNSSEC utiliza firmas RRSIG y claves DNSKEY.",
        "tls_crypto": "[CHUNK 3 | Pág 80 | Stallings] TLS 1.3 elimina RSA key transport y usa ECDHE.",
        "bgp_routing": "[CHUNK 4 | Pág 120 | Kurose] BGP utiliza AS-PATH para prevenir loops de enrutamiento.",
    }

    queries_trace = []
    for i in range(30):
        queries_trace.append(("tcp_handshake", f"Duda TCP #{i}"))
    for i in range(25):
        queries_trace.append(("tls_crypto", f"Duda TLS #{i}"))
    for i in range(25):
        queries_trace.append(("dns_security", f"Duda DNS #{i}"))
    for i in range(20):
        queries_trace.append(("bgp_routing", f"Duda BGP #{i}"))

    assert len(queries_trace) == 100

    chat_history = []
    for topic_key, query_text in queries_trace:
        corpus = topics_corpus[topic_key]
        bundle = assembler.assemble(
            user_query=query_text,
            corpus_pack=corpus,
            dynamic_instructions="MODO SOCRÁTICO",
            session_briefing=f"Enfocado en {topic_key}",
            chat_history=chat_history[-4:],
        )
        cache.query(bundle)
        chat_history.append({"role": "user", "content": query_text})
        chat_history.append({"role": "assistant", "content": f"Explicación sobre {topic_key}"})

    assert cache.hits == 96
    assert cache.misses == 4
    hit_rate = cache.hit_rate
    assert hit_rate >= 0.70, f"Cache hit rate {hit_rate:.2%} está por debajo del objetivo > 70%"
    assert hit_rate == 0.96
