"""Tests for PedagogicalContract validation, immutability, and storage persistence (Fase 5.8)."""

from datetime import datetime, timezone
import pytest
from pydantic import ValidationError

from study_engine.contracts.catalog import NotebookNotFoundError
from study_engine.contracts.notebook import Notebook
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT, get_default_contract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.storage.knowledge_store import KnowledgeStore


def test_pedagogical_contract_immutability_and_validation():
    """PedagogicalContract is frozen and strictly validated against invalid phases."""
    phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicá {concept} a fondo.",
        max_tokens=800,
        requires_user_approval=False,
        code_allowed=False,
    )
    contract = PedagogicalContract(
        notebook_id="nb_test",
        persona="socratic_rioplatense",
        base_system_prompt="Sos un tutor socrático riguroso.",
        forbidden_patterns=["```python"],
        safe_words=[":solve"],
        response_phases=[phase],
        required_analogies=["ram_table"],
        anti_errors=["no digas fácil"],
    )

    # Immutability
    with pytest.raises(ValidationError):
        contract.persona = "academic_strict"  # type: ignore

    # Duplicate phase_id rejection
    with pytest.raises(ValidationError):
        PedagogicalContract(
            notebook_id="nb_test",
            base_system_prompt="Sos un tutor socrático riguroso.",
            response_phases=[phase, phase],  # Duplicate phase_id 'conceptual'
        )


def test_knowledge_store_pedagogical_contract_crud(tmp_path):
    """KnowledgeStore stores, retrieves, updates and deletes custom pedagogical contracts."""
    db_file = tmp_path / "test_contracts.db"
    store = KnowledgeStore(db_file)
    store.initialize()

    # Create parent notebook
    nb = Notebook(id="nb_algo", name="Algoritmos y Estructuras de Datos")
    store.create_notebook(nb)

    # 1. Unset notebook defaults to canonical contract
    default_contract = store.get_pedagogical_contract("nb_algo")
    assert default_contract.notebook_id == "nb_algo"
    assert default_contract.persona == "socratic_rioplatense"
    assert len(default_contract.response_phases) >= 3
    assert store.contains_pedagogical_contract("nb_algo") is False

    # 2. Persist custom contract
    custom_phase = ResponsePhase(
        phase_id="conceptual",
        phase_prompt_template="Explicación táctica para ciberseguridad sobre {concept}.",
        max_tokens=1200,
        requires_user_approval=False,
        code_allowed=False,
    )
    custom_contract = PedagogicalContract(
        notebook_id="nb_algo",
        persona="cybersec_tactical",
        base_system_prompt="Operás como un instructor de operaciones defensivas y auditoría de código.",
        forbidden_patterns=["```c", "```python"],
        safe_words=[":override_exploit"],
        response_phases=[custom_phase],
        required_analogies=["buffer_as_towel"],
        anti_errors=["no omitir límites de memoria"],
    )
    store.save_pedagogical_contract(custom_contract)
    assert store.contains_pedagogical_contract("nb_algo") is True

    # 3. Retrieve and assert all fields preserved
    loaded = store.get_pedagogical_contract("nb_algo")
    assert loaded.notebook_id == "nb_algo"
    assert loaded.persona == "cybersec_tactical"
    assert loaded.forbidden_patterns == ["```c", "```python"]
    assert loaded.safe_words == [":override_exploit"]
    assert len(loaded.response_phases) == 1
    assert loaded.response_phases[0].phase_id == "conceptual"
    assert loaded.response_phases[0].max_tokens == 1200
    assert loaded.required_analogies == ["buffer_as_towel"]

    # 4. Delete custom contract falls back cleanly to default
    deleted = store.delete_pedagogical_contract("nb_algo")
    assert deleted is True
    assert store.contains_pedagogical_contract("nb_algo") is False
    fallback = store.get_pedagogical_contract("nb_algo")
    assert fallback.persona == "socratic_rioplatense"


def test_save_contract_for_nonexistent_notebook_fails_closed():
    """Attempting to bind a contract to a nonexistent notebook raises NotebookNotFoundError."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    contract = get_default_contract("nb_ghost")
    with pytest.raises(NotebookNotFoundError):
        store.save_pedagogical_contract(contract)
