"""Contract tests for Subsystem S4.3 LLM Client and Backends."""

import pytest
from pydantic import ValidationError

from study_engine.contracts.generation import (
    GenerationParameters,
    TokenUsage,
)
from study_engine.generation.base import BaseGenerator
from study_engine.generation.prompts import (
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.backends import (
    HttpOpenAIBackend,
    MockBackend,
    ProviderBackend,
    ProviderCompletion,
    RuleBasedBackend,
)
from study_engine.llm.client import LLMClient


def test_prompt_models_immutability():
    """Verify PromptMessage and PromptBundle are strictly frozen."""
    # 1. PromptMessage
    msg = PromptMessage(role=PromptRole.USER, content="Pregunta")
    with pytest.raises((ValidationError, TypeError)):
        msg.content = "Modificado"  # type: ignore[misc]

    # 2. PromptBundle
    params = GenerationParameters(temperature=0.7, max_output_tokens=300)
    bundle = PromptBundle(
        system_prompt="System policy",
        messages=(msg,),
        parameters=params,
        prompt_hash="a" * 64,
    )
    with pytest.raises((ValidationError, TypeError)):
        bundle.system_prompt = "Otra policy"  # type: ignore[misc]


def test_provider_completion_immutability():
    """Verify ProviderCompletion is strictly frozen."""
    comp = ProviderCompletion(
        text="Respuesta",
        latency_ms=15.5,
        tokens_used=TokenUsage(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        ),
        model="mock-v1",
    )

    with pytest.raises((ValidationError, TypeError)):
        comp.text = "Alterado"  # type: ignore[misc]


def test_llm_client_satisfies_base_generator():
    """Verify HG-S4.3-01: LLMClient implements BaseGenerator protocol."""
    client = LLMClient(backend=MockBackend())
    assert isinstance(client, BaseGenerator)


def test_provider_backends_runtime_checkable():
    """Verify all backends implement runtime-checkable ProviderBackend."""
    assert isinstance(MockBackend(), ProviderBackend)
    assert isinstance(RuleBasedBackend(), ProviderBackend)
    assert isinstance(HttpOpenAIBackend(), ProviderBackend)


def test_prompt_hash_never_includes_secrets():
    """Verify HG-S4.3-08: PromptBundle and prompt_hash contain no secrets."""
    params = GenerationParameters(temperature=0.2, max_output_tokens=200)
    msg = PromptMessage(role=PromptRole.USER, content="Consulta de prueba")
    p_hash = compute_canonical_prompt_hash(
        system_prompt="System instructions",
        messages=(msg,),
        parameters=params,
    )
    assert len(p_hash) == 64
    assert isinstance(p_hash, str)

    bundle = PromptBundle(
        system_prompt="System instructions",
        messages=(msg,),
        parameters=params,
        prompt_hash=p_hash,
    )

    dumped = bundle.model_dump()
    dumped_str = str(dumped)
    forbidden_terms = ["api_key", "secret", "bearer", "token_auth", "password"]
    for term in forbidden_terms:
        assert term not in dumped_str.lower()


def test_prompt_roles_restricted():
    """Verify PromptRole only contains USER and ASSISTANT."""
    assert set(PromptRole) == {PromptRole.USER, PromptRole.ASSISTANT}

    assert PromptRole.USER.value == "user"
    assert PromptRole.ASSISTANT.value == "assistant"
