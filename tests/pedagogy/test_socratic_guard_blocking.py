"""Tests for SocraticGuard rolling buffer and code blocking invariants (Fase 5.8 / Refinamiento 2)."""

import pytest

from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.socratic_guard import SocraticGuard


@pytest.fixture
def conceptual_phase() -> ResponsePhase:
    return ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicación conceptual de {concept}.",
        max_tokens=1000,
        requires_user_approval=False,
        code_allowed=False,
    )


@pytest.fixture
def code_phase() -> ResponsePhase:
    return ResponsePhase(
        phase_id="python_code",
        phase_prompt_template="Traducción a Python de {concept}.",
        max_tokens=800,
        requires_user_approval=True,
        code_allowed=True,
    )


def test_socratic_guard_blocks_exact_forbidden_pattern(conceptual_phase):
    """SocraticGuard immediately blocks code pattern and emits pedagogical message."""
    guard = SocraticGuard(contract=FASE0_CONTRACT)

    res1 = guard.validate_token("Para entender la pila, veamos esto: ", conceptual_phase, "explicame stack")
    assert res1.allowed is True
    assert res1.emitted_token == "Para entender la pila, veamos esto: "

    res2 = guard.validate_token("```python\nimport sys", conceptual_phase, "explicame stack")
    assert res2.allowed is False
    assert res2.blocked_reason == "CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE"
    assert "🛑 **[TALOS SocraticGuard]**" in res2.replacement_message
    assert "bloque ejecutable" in res2.replacement_message
    assert "diagrama" not in res2.replacement_message


def test_socratic_guard_rolling_buffer_catches_split_tokens(conceptual_phase):
    """Refinamiento 2: Rolling buffer detects patterns split across arbitrary token boundaries."""
    guard = SocraticGuard(contract=FASE0_CONTRACT)

    # Stream broken into bizarre token slices: ["`", "``", "py", "thon\n", "x = 1"]
    tokens = ["`", "``", "py", "thon\n", "x = 1"]
    results = []
    for tok in tokens:
        res = guard.validate_token(tok, conceptual_phase, "¿Cómo se usa un puntero?")
        results.append(res)

    # Up to token 3 ("py"), the rolling buffer is "```py", which matches forbidden pattern "```py"
    # It must trigger blocking on or before the full pattern is reached!
    blocked_results = [r for r in results if not r.allowed]
    assert len(blocked_results) > 0
    first_blocked = blocked_results[0]
    assert first_blocked.blocked_reason == "CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE"


def test_socratic_guard_safe_word_override_allows_code(conceptual_phase):
    """If user uses explicit safe_word in query, SocraticGuard unblocks code even in non-code phase."""
    guard = SocraticGuard(contract=FASE0_CONTRACT)

    # Query contains safe word ':solve'
    res = guard.validate_token(
        "```python\ndef solve(): pass",
        conceptual_phase,
        "No entiendo nada, :solve por favor",
    )
    assert res.allowed is True
    assert res.emitted_token == "```python\ndef solve(): pass"

    # Query contains safe word 'DAME LA SOLUCIÓN COMPLETA'
    guard.reset()
    res2 = guard.validate_token(
        "import os\ndef test(): pass",
        conceptual_phase,
        "DAME LA SOLUCIÓN COMPLETA de este ejercicio",
    )
    assert res2.allowed is True


def test_socratic_guard_allows_code_when_code_allowed_is_true(code_phase):
    """When phase explicitly authorizes code (code_allowed=True), code patterns pass freely."""
    guard = SocraticGuard(contract=FASE0_CONTRACT)

    res = guard.validate_token(
        "```python\ndef invertir_lista(l):\n    return l[::-1]\n```",
        code_phase,
        "Generá el código en Python",
    )
    assert res.allowed is True
    assert "def invertir_lista" in res.emitted_token
