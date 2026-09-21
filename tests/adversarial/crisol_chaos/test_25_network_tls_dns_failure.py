"""Escenario 25: TLS Cert Expiry y Fallo DNS NXDOMAIN (Fase 7.2 - Chaos Engineering).

Simular errores de red a nivel de transporte: certificado SSL vencido y fallo de resolución DNS.
Invariante: Los fallos son tratados como transitorios por el CircuitBreaker; el error queda
            registrado con claridad diagnóstica y la selección conmuta al siguiente proveedor.
Severidad: MEDIO.
"""

import socket
import ssl
from typing import Iterator
import pytest

from study_engine.llm.abstract_provider import AbstractLLMProvider, ProviderHealth
from study_engine.llm.circuit_breaker import CircuitBreaker, CircuitState
from study_engine.llm.registry import ModelRegistry


class MockNetworkFailingProvider(AbstractLLMProvider):
    def __init__(self, provider_id: str, error_type: str):
        self._provider_id = provider_id
        self._error_type = error_type

    @property
    def provider_id(self) -> str:
        return self._provider_id

    def generate(self, prompt: str, **kwargs) -> str:
        if self._error_type == "ssl":
            raise ssl.SSLCertVerificationError("certificate has expired (_ssl.c:1000)")
        elif self._error_type == "dns":
            raise socket.gaierror(-2, "Name or service not known (NXDOMAIN)")
        raise RuntimeError("Unknown error")

    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield self.generate(prompt, **kwargs)

    def health_check(self) -> ProviderHealth:
        return ProviderHealth(
            provider_id=self._provider_id,
            availability=0.8,
            avg_latency_ms=120.0,
            rate_limit_429_count=0,
            context_capacity=8000,
            multimodal_support=False,
            structured_output=True,
            is_healthy=True,
        )

    def max_context_tokens(self) -> int:
        return 8000

    def supports_multimodal(self) -> bool:
        return False


def test_tls_and_dns_failures_recorded_transiently() -> None:
    """SSL expiration and DNS failures are recorded as transience, tripping breaker safely."""
    registry = ModelRegistry()
    cb_ssl = CircuitBreaker(failure_threshold=2)
    cb_dns = CircuitBreaker(failure_threshold=2)

    prov_ssl = MockNetworkFailingProvider("groq_ssl_fail", "ssl")
    prov_dns = MockNetworkFailingProvider("cerebras_dns_fail", "dns")

    registry.register_provider(prov_ssl, cb_ssl)
    registry.register_provider(prov_dns, cb_dns)

    # 1. SSL failure
    with pytest.raises(ssl.SSLCertVerificationError, match="certificate has expired"):
        try:
            prov_ssl.generate("test")
        except Exception:
            registry.record_call_result("groq_ssl_fail", success=False)
            raise

    assert cb_ssl.consecutive_failures == 1

    # 2. DNS NXDOMAIN failure
    with pytest.raises(socket.gaierror, match="Name or service not known"):
        try:
            prov_dns.generate("test")
        except Exception:
            registry.record_call_result("cerebras_dns_fail", success=False)
            raise

    assert cb_dns.consecutive_failures == 1

    # Registry health cache reflects degradation without crash
    health_ssl = registry.get_provider_health("groq_ssl_fail")
    health_dns = registry.get_provider_health("cerebras_dns_fail")
    assert health_ssl is not None
    assert health_dns is not None
    assert health_ssl.availability < 0.8
    assert health_dns.availability < 0.8
