"""Hoare contract formal specifications for Subsystem S5.4.

INVARIANTS:
1. S5.4 defines declarative formal specifications {P} S {Q};
   it NEVER executes or verifies them.
2. Formal expressions are purely static strings intended for
   consumption by downstream verifiers (S10).
3. Zero eval(), zero callables, zero execution interpreters
   (HG-S5.4-04, HG-S5.4-06).
4. All specifications are strictly immutable (frozen=True, extra="forbid").
"""

from typing import Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract


class Precondition(BaseContract):
    """Declarative precondition predicate {P} required before execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    predicate_id: str = Field(
        ..., min_length=1, description="Unique precondition identifier"
    )
    formal_expression: str = Field(
        ..., min_length=1, description="Declarative specification string"
    )
    description: str = Field(
        ..., min_length=1, description="Human readable explanation"
    )


class Postcondition(BaseContract):
    """Declarative postcondition predicate {Q} guaranteed after execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    predicate_id: str = Field(
        ..., min_length=1, description="Unique postcondition identifier"
    )
    formal_expression: str = Field(
        ..., min_length=1, description="Declarative specification string"
    )
    description: str = Field(
        ..., min_length=1, description="Human readable explanation"
    )


class Invariant(BaseContract):
    """Declarative system/loop invariant required throughout execution."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    invariant_id: str = Field(
        ..., min_length=1, description="Unique invariant identifier"
    )
    formal_expression: str = Field(
        ..., min_length=1, description="Declarative specification string"
    )
    description: str = Field(
        ..., min_length=1, description="Human readable explanation"
    )
    violation_consequence: str = Field(
        ..., min_length=1, description="Impact if invariant is violated"
    )


class TerminationVariant(BaseContract):
    """Declarative loop variant ensuring termination."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    variant_id: str = Field(
        ..., min_length=1, description="Unique variant identifier"
    )
    measure_expression: str = Field(
        ..., min_length=1, description="Well-founded decreasing measure"
    )
    description: str = Field(
        ..., min_length=1, description="Explanation of termination proof"
    )


class HoareContractSpecification(BaseContract):
    """Declarative Hoare contract specification {P} S {Q} for tasks.

    INVARIANTS:
    - Purely declarative; possesses NO verification methods or interpreters.
    - S10 receives this specification to verify execution against traces.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    contract_id: str = Field(
        ..., min_length=1, description="Unique contract identifier"
    )
    name: str = Field(
        ..., min_length=1, description="Human readable contract name"
    )
    target_component: str = Field(
        ..., min_length=1, description="Component under specification"
    )
    preconditions: Tuple[Precondition, ...] = Field(
        default_factory=tuple, description="Preconditions required before run"
    )
    postconditions: Tuple[Postcondition, ...] = Field(
        default_factory=tuple, description="Guaranteed postconditions"
    )
    invariants: Tuple[Invariant, ...] = Field(
        default_factory=tuple, description="Invariants required across run"
    )
    termination_variant: Optional[TerminationVariant] = Field(
        default=None, description="Optional termination variant"
    )
    description: str = Field(
        ..., min_length=1, description="Pedagogical description of contract"
    )
