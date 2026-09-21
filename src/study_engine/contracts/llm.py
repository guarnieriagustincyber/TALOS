"""LLM request and response contracts (provider-agnostic)."""

from typing import Any, Dict, List, Optional
from pydantic import Field

from study_engine.contracts.base import BaseContract


class LLMRequest(BaseContract):
    """Stateless LLM request contract."""

    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    mode: str = Field(default="tutor", description="Interaction mode (e.g., 'tutor', 'tester', 'auditor', 'planner')")
    system_prompt: Optional[str] = Field(default=None, description="System instructions")
    messages: List[Dict[str, str]] = Field(default_factory=list, description="Conversation messages [{'role': '...', 'content': '...'}]")
    context: Optional[str] = Field(default=None, description="Packed context string")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="Maximum output tokens")
    stop_sequences: List[str] = Field(default_factory=list, description="Optional stop sequences")
    model: Optional[str] = Field(default=None, description="Optional target model identifier")
    provider: Optional[str] = Field(default=None, description="Optional target provider identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")


class LLMResponse(BaseContract):
    """Stateless LLM response contract."""

    request_id: str = Field(..., min_length=1, description="Request identifier matching LLMRequest")
    content: str = Field(..., description="Text output produced by LLM")
    mode: Optional[str] = Field(default=None, description="Mode under which response was generated")
    model: Optional[str] = Field(default=None, description="Model that produced the response")
    provider: Optional[str] = Field(default=None, description="Provider that executed the inference")
    tokens_used: Optional[Dict[str, int]] = Field(default=None, description="Token usage statistics (prompt, completion, total)")
    finish_reason: Optional[str] = Field(default=None, description="Reason for stopping (e.g., 'stop', 'length')")
    latency_ms: Optional[float] = Field(default=None, ge=0.0, description="Execution latency in milliseconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Extensible metadata")
