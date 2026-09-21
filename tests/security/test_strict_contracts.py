"""Security TDD test for VULN-04: Strict Pydantic Contracts.

Eliminates lax type coercion (e.g. 'YES' -> True, '1' -> 1) in
IntentContract and AuthoritativeRoute.
"""

import pytest
from pydantic import ValidationError

from study_engine.tutor.semantic_router import IntentContract, IntentType
from study_engine.tutor.policy_validator import AuthoritativeRoute, RouteKind


def test_intent_contract_rejects_string_for_bool():
    """String 'YES' must not be coerced to True; must raise ValidationError under strict mode."""
    with pytest.raises(ValidationError):
        IntentContract.model_validate({
            "intent": "technical_question",
            "action": "explain_concept",
            "confidence": 0.5,
            "needs_evidence": "YES",  # Lax coercion would turn this to True
            "needs_curriculum": False,
        })


def test_intent_contract_rejects_string_for_confidence():
    """String 'HIGH' must raise ValidationError under strict mode."""
    with pytest.raises(ValidationError):
        IntentContract.model_validate({
            "intent": "technical_question",
            "action": "explain_concept",
            "confidence": "HIGH",
            "needs_evidence": False,
            "needs_curriculum": False,
        })


def test_authoritative_route_strict():
    """AuthoritativeRoute must enforce strict typing."""
    with pytest.raises(ValidationError):
        AuthoritativeRoute.model_validate({
            "route_kind": "technical",
            "intent": "technical_question",
            "action": "explain_concept",
            "needs_evidence": "True",  # String instead of bool
            "needs_curriculum": False,
            "needs_execution": False,
            "needs_clarification": False,
        })
