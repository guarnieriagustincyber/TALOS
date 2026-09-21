"""Security TDD test for VULN-02: Unknown / Arbitrary Action Rejection.

Ensures DeterministicPolicyValidator rejects (RouteKind.REJECTED) any action
that is not strictly in the authorized whitelist for the given intent.
Never falls back silently to a canonical action.
"""

import pytest
from study_engine.tutor.semantic_router import IntentContract, IntentType
from study_engine.tutor.policy_validator import (
    AuthoritativeRoute,
    DeterministicPolicyValidator,
    RouteKind,
)

@pytest.fixture
def validator():
    return DeterministicPolicyValidator(roadmap=None, current_node=None)

@pytest.mark.parametrize(
    "bad_action",
    [
        "root_shell",
        "DROP TABLE",
        "",
        " ",
        "EXPLAIN_CONCEPT",  # wrong casing
        "explain_concept ",  # trailing whitespace
        "arbitrary_action_123",
        "execute_malware",
    ],
)
def test_policy_validator_rejects_unknown_action_fail_closed(validator, bad_action):
    contract = IntentContract(
        intent=IntentType.TECHNICAL_QUESTION,
        action=bad_action,
        needs_evidence=True,
        needs_curriculum=False,
        needs_execution=False,
        needs_clarification=False,
        confidence=0.99,
    )

    route = validator.resolve(contract)

    # Invariant: Must fail-closed to RouteKind.REJECTED with reason 'unauthorized_action' or similar
    assert route.route_kind == RouteKind.REJECTED, (
        f"Expected REJECTED for unauthorized action '{bad_action}', but got {route.route_kind} (action={route.action})"
    )
    assert route.action == "reject"
    assert not route.execution_allowed
    assert not route.mutation_allowed
