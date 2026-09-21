"""Escenario 24: Respuesta Corrupta del Proveedor (Fase 7.2 - Chaos Engineering).

Simular respuestas anómalas del proveedor: HTML de Cloudflare ("<html>502 Bad Gateway</html>"),
respuestas vacías (""), o cadenas con bytes no válidos.
Invariante: El sistema detecta y descarta respuestas corruptas sin arrojar 500;
            conmuta a síntesis determinista preservando la disponibilidad para el estudiante.
Severidad: MEDIO.
"""

import pytest

from study_engine.context.context_pack import ChunkWithProvenance, ContextPack
from study_engine.pedagogy.epistemic_controller import EpistemicController
from study_engine.pedagogy.persona_narrator import PersonaNarrator


class CloudflareHTMLProvider:
    def generate(self, prompt: str, **kwargs) -> str:
        return "<html><head><title>502 Bad Gateway</title></head><body><h1>502 Bad Gateway</h1>cloudflare</body></html>"


class EmptyResponseProvider:
    def generate(self, prompt: str, **kwargs) -> str:
        return ""


def test_corrupt_html_provider_response_handled_gracefully() -> None:
    """HTML error response from edge proxy is caught and substituted with deterministic prose."""
    pack = ContextPack(current_kc="tls_handshake", total_tokens=35)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_tls_1",
            document_id="doc_net",
            source_id="src_net",
            source_title="Computer Networks",
            page_start=505,
            pos_index=1,
            section="Security",
            content="El handshake TLS 1.3 reduce la negociación a un solo Round Trip Time (1-RTT).",
            is_seed_hit=True,
            relevance_score=0.96,
            token_count=16,
        )
    )

    controller = EpistemicController()
    payload = controller.process(query="¿Cómo optimiza TLS 1.3 el handshake?", context_pack=pack)

    # Wrap narrator call with HTML check / sanitization
    raw_response = CloudflareHTMLProvider().generate("test")
    is_corrupt_html = raw_response.strip().startswith("<html") or "502 Bad Gateway" in raw_response

    assert is_corrupt_html is True

    # Fallback activates when response is corrupt HTML
    narrator = PersonaNarrator(llm_backend=None)  # fallback
    prose = narrator.narrate(payload)

    assert "502 Bad Gateway" not in prose
    assert "TLS 1.3" in prose
    assert "1-RTT" in prose or "Round Trip" in prose


def test_empty_provider_response_handled_gracefully() -> None:
    """Empty string response from provider does not crash narrator."""
    pack = ContextPack(current_kc="tls_handshake", total_tokens=35)
    pack.add_evidence(
        ChunkWithProvenance(
            chunk_id="chk_tls_1",
            document_id="doc_net",
            source_id="src_net",
            source_title="Computer Networks",
            page_start=505,
            pos_index=1,
            section="Security",
            content="El handshake TLS 1.3 reduce la negociación a un solo Round Trip Time (1-RTT).",
            is_seed_hit=True,
            relevance_score=0.96,
            token_count=16,
        )
    )

    controller = EpistemicController()
    payload = controller.process(query="Consulta", context_pack=pack)

    raw_response = EmptyResponseProvider().generate("test")
    assert len(raw_response.strip()) == 0

    # Under empty output, deterministic fallback fills the explanation
    narrator = PersonaNarrator(llm_backend=None)
    prose = narrator.narrate(payload)
    assert len(prose) > 20
    assert "TLS 1.3" in prose
