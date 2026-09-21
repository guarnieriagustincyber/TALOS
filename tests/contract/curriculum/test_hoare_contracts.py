"""Contract tests for Hoare formal specifications (S5.4)."""

import pytest
from pydantic import ValidationError

from study_engine.curriculum.hoare_contracts import (
    HoareContractSpecification,
    Invariant,
    Postcondition,
    Precondition,
    TerminationVariant,
)


def test_hoare_contract_immutability_and_extra_forbidden() -> None:
    """Hoare contracts must be immutable and reject extra attributes."""
    pre = Precondition(
        predicate_id="pre-1",
        formal_expression="len(packet_bytes) >= 20",
        description="Packet contains at least minimal IPv4 header",
    )
    with pytest.raises(ValidationError):
        pre.formal_expression = "mutated"

    with pytest.raises(ValidationError):
        Precondition(
            predicate_id="pre-bad",
            formal_expression="x > 0",
            description="desc",
            executable_fn=lambda x: True,  # type: ignore[call-arg]
        )


def test_hoare_contract_declarative_purity() -> None:
    """HG-S5.4-04 & HG-S5.4-06: Formal expressions are static data."""
    malicious = '__import__("os").system("echo should_not_run") == 0'

    inv = Invariant(
        invariant_id="inv-purity",
        formal_expression=malicious,
        description="Test declarative purity",
        violation_consequence="No execution occurs in S5.4",
    )

    # Must be stored verbatim without execution
    assert inv.formal_expression == malicious
    # Invariant object possesses zero evaluation or call methods
    assert not callable(inv)
    assert not hasattr(inv, "evaluate")
    assert not hasattr(inv, "verify")


def test_hoare_contract_g4_4_soar_playbook_representation() -> None:
    """Demonstrate representation of G4.4 (P12 Ransomware Playbook)."""
    pre = Precondition(
        predicate_id="pre-g44-containment",
        formal_expression="threat_score(host) >= 80 and not is_whitelisted",
        description="Host is confirmed compromised and not whitelisted",
    )
    post = Postcondition(
        predicate_id="post-g44-isolation",
        formal_expression="network_isolated(host) and ticket_created(hive)",
        description="Host traffic blocked and ticket opened",
    )
    inv = Invariant(
        invariant_id="inv-g44-whitelist",
        formal_expression="forall h in domain_controllers: not isolated(h)",
        description="Domain Controllers and DNS roots are never severed",
        violation_consequence="Catastrophic infrastructure outage (P1)",
    )
    term = TerminationVariant(
        variant_id="term-g44-playbook",
        measure_expression="pending_containment_queue.length",
        description="Queue of affected endpoints strictly decreases",
    )

    spec = HoareContractSpecification(
        contract_id="hoare-p12-ransomware-playbook",
        name="Ransomware Automated Containment Playbook Contract",
        target_component="soar.playbooks.ransomware",
        preconditions=(pre,),
        postconditions=(post,),
        invariants=(inv,),
        termination_variant=term,
        description="Hoare specification for Gateway G4.4",
    )

    assert spec.contract_id == "hoare-p12-ransomware-playbook"
    assert len(spec.preconditions) == 1
    assert len(spec.postconditions) == 1
    assert len(spec.invariants) == 1
    assert spec.termination_variant is not None
