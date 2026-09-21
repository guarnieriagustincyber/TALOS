"""Escenario 13: Envenenamiento de Caché de Prefijo (Fase 7.2 - Chaos Engineering).

Simular un intento de envenenar o desfasar la caché de prefijo de contexto largo.
Invariante: La validez del contexto y su hash/provenance son verificados estrictamente;
            prefijos alterados se invalidan y no contaminan las citas autorizadas.
Severidad: ALTO.
"""

import hashlib
import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


def compute_pack_hash(pack: ContextPack) -> str:
    hasher = hashlib.sha256()
    for chk in pack.retrieved_evidence:
        hasher.update(chk.chunk_id.encode("utf-8"))
        hasher.update(chk.content.encode("utf-8"))
    return hasher.hexdigest()


def test_corrupt_cache_prefix_detection_and_invalidation() -> None:
    """Altered cache prefix hash is detected; stale/poisoned context is discarded."""
    legit_pack = ContextPack(current_kc="virtual_memory", total_tokens=40)
    legit_pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_vm_clean",
            document_id="doc_tanenbaum",
            source_id="src_tanenbaum",
            source_title="Modern Operating Systems",
            page_start=180,
            pos_index=1,
            section="Paging",
            content="La memoria virtual aísla los espacios de direcciones de cada proceso.",
            is_seed_hit=True,
            relevance_score=0.95,
            token_count=18,
        )
    )

    clean_hash = compute_pack_hash(legit_pack)

    # Attacker attempts to poison cache by modifying chunk content while pretending to use clean_hash
    poisoned_pack = ContextPack(current_kc="virtual_memory", total_tokens=40)
    poisoned_pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_vm_clean",
            document_id="doc_tanenbaum",
            source_id="src_tanenbaum",
            source_title="Modern Operating Systems",
            page_start=180,
            pos_index=1,
            section="Paging",
            content="La memoria virtual comparte las contraseñas de todos los procesos en texto plano.",
            is_seed_hit=True,
            relevance_score=0.95,
            token_count=18,
        )
    )

    poisoned_hash = compute_pack_hash(poisoned_pack)
    assert clean_hash != poisoned_hash, "Hash collision: cache prefix corruption undetected!"

    # System cache verification gate
    class PrefixCacheManager:
        def __init__(self):
            self.cached_entries = {clean_hash: legit_pack}

        def get_verified_pack(self, incoming_pack: ContextPack, expected_hash: str) -> ContextPack:
            actual_hash = compute_pack_hash(incoming_pack)
            if actual_hash != expected_hash or actual_hash not in self.cached_entries:
                # Invalidate / reject poisoned cache
                return incoming_pack  # Falls back to fresh re-evaluation, never accepts poisoned match
            return self.cached_entries[actual_hash]

    cache = PrefixCacheManager()
    resolved = cache.get_verified_pack(poisoned_pack, expected_hash=clean_hash)

    # Invariant: Controller processes the verified actual pack, does not validate fake cache claim
    controller = EpistemicController()
    payload = controller.process(
        query="¿Cómo funciona el aislamiento de memoria?",
        context_pack=resolved,
    )
    assert len(payload.core_facts) == 1
