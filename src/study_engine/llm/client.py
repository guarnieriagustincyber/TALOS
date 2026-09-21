"""Authoritative LLMClient generator implementation for Subsystem S4.3.

Coordinates prompt assembly and provider backend execution, strictly
returning RawGenerationResult to guarantee parser isolation.
"""

from typing import Optional, Union

from study_engine.contracts.generation import (
    GenerationParameters,
    GenerationRequest,
    RawGenerationResult,
)
from study_engine.generation.base import BaseGenerator
from study_engine.generation.prompts import (
    PromptAssembler,
    PromptBundle,
    PromptMessage,
    PromptRole,
    compute_canonical_prompt_hash,
)
from study_engine.llm.backends import ProviderBackend


class LLMClient(BaseGenerator):
    """Authoritative generator adapter coordinating assembly and backend.

    RULE: LLMClient implements BaseGenerator and returns RawGenerationResult.
    It MUST NOT parse citations or build GenerationResponse instances.
    """

    def __init__(
        self,
        backend: ProviderBackend,
        assembler: Optional[PromptAssembler] = None,
    ) -> None:
        """Initialize LLMClient.

        Parameters
        ----------
        backend : ProviderBackend
            The generation backend (Mock, RuleBased, HttpOpenAI).
        assembler : Optional[PromptAssembler]
            The deterministic prompt assembler (defaults to standard instance).
        """
        self._backend = backend
        self._assembler = assembler or PromptAssembler()

    @property
    def backend(self) -> ProviderBackend:
        """Access the underlying ProviderBackend."""
        return self._backend

    @property
    def assembler(self) -> PromptAssembler:
        """Access the prompt assembler."""
        return self._assembler

    def generate(
        self,
        request: Union[GenerationRequest, str],
        max_tokens: Optional[int] = None,
    ) -> RawGenerationResult:
        """Generate raw output for the given GenerationRequest or prompt string.

        Executes:
        1. Deterministic prompt assembly.
        2. Backend completion.
        3. Packaging into RawGenerationResult.

        Raises
        ------
        LLMBackendError
            If backend execution or transport fails (fail-closed).
        """
        if isinstance(request, str):
            params = GenerationParameters(
                max_output_tokens=max_tokens if max_tokens is not None else 1024
            )
            messages = (PromptMessage(role=PromptRole.USER, content=request),)
            system_prompt = "You are a helpful assistant."
            bundle = PromptBundle(
                system_prompt=system_prompt,
                messages=messages,
                parameters=params,
                prompt_hash=compute_canonical_prompt_hash(
                    system_prompt, messages, params
                ),
            )
        else:
            # 1. Assemble deterministic PromptBundle
            bundle = self._assembler.assemble(request)

        # 2. Complete prompt via backend
        completion = self._backend.complete(bundle)

        # 3. Return unvalidated RawGenerationResult
        return RawGenerationResult(
            raw_content=completion.text,
            generator_abstained=completion.generator_abstained,
            latency_ms=completion.latency_ms,
            tokens_used=completion.tokens_used,
            model=completion.model,
        )
