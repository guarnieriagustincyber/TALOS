"""Authoritative generation facade for the Study Engine (Subsystem S4.3).

Coordinates generator execution and S4.2 output parser validation.
"""

from typing import Optional

from study_engine.contracts.generation import (
    GenerationRequest,
    GenerationResponse,
)
from study_engine.generation.base import BaseGenerator
from study_engine.generation.parser import GenerationOutputParser


class StructuredTutor:
    """Authoritative generation facade for the Study Engine.

    Coordinates BaseGenerator execution and strictly delegates response
    construction to GenerationOutputParser.parse() to guarantee that
    callers receive a validated GenerationResponse.
    """

    def __init__(
        self,
        generator: BaseGenerator,
        parser: Optional[GenerationOutputParser] = None,
    ) -> None:
        """Initialize StructuredTutor with generator and optional parser."""
        self._generator = generator
        self._parser = parser or GenerationOutputParser()

    @property
    def generator(self) -> BaseGenerator:
        """Access the underlying generator."""
        return self._generator

    @property
    def parser(self) -> GenerationOutputParser:
        """Access the output parser."""
        return self._parser

    def answer(
        self,
        request: GenerationRequest,
        response_id: Optional[str] = None,
    ) -> GenerationResponse:
        """Answer request by executing generator and parsing output.

        Enforces HG-S4.3-06 (Parser-Only Response Construction):
        StructuredTutor MUST NOT instantiate, mutate, reconstruct, or otherwise
        manufacture GenerationResponse. The sole construction path is
        GenerationOutputParser.parse(raw_result, request).
        """
        raw_result = self._generator.generate(request)
        return self._parser.parse(
            raw_result=raw_result,
            request=request,
            response_id=response_id,
        )
