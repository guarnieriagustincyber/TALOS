"""T04: only server-resolved exercise identity and type can reach grading/BKT."""

import asyncio
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from study_engine.pedagogy.exercise_contracts import (
    ExerciseCandidate,
    ExerciseType,
    ExerciseVerificationStatus,
)
from study_engine.pedagogy.exercise_store import ExerciseStore
from study_engine.pedagogy.graders import ExactMatchGrader, MultiChoiceGrader
from study_engine.student.bkt_tracker import BKTTracker
from study_engine.web.routes.chat import ExerciseEvaluateRequest, evaluate_exercise_answer


def _exercise(*, kind=ExerciseType.NUMERIC, status=ExerciseVerificationStatus.QUALIFIABLE):
    return ExerciseCandidate(
        exercise_id="ex-current",
        source_id="synthetic-source",
        source_location="p.1",
        source_hash="a" * 64,
        extractor_version="test",
        extraction_method="manual",
        verification_status=status,
        verified_by="synthetic-reviewer",
        verification_timestamp=None,
        content_hash="b" * 64,
        kc_id="kc-current",
        prompt="Synthetic exercise",
        exercise_type=kind,
        options=("A", "B", "C") if kind == ExerciseType.MC else None,
        expected_answer="B" if kind == ExerciseType.MC else "-5",
    )


def _container(tmp_path, exercise=None, generated=None):
    store = ExerciseStore(storage_path=tmp_path / "exercises.json")
    if exercise is not None:
        store.add_exercise(exercise, persist=False)
    return SimpleNamespace(
        exercise_store=store,
        generated_registry=SimpleNamespace(get=lambda _id: generated),
        pedagogical_orchestrator=SimpleNamespace(
            _kc_catalog={"nb-current": {"kcs": [{"kc_id": "kc-current"}]}}
        ),
        bkt_tracker=BKTTracker(),
        mc_grader=MultiChoiceGrader(),
        exact_grader=ExactMatchGrader(),
        struggle_tracker=None,
        student_storage=None,
    )


def _evaluate(container, **overrides):
    payload = {"exercise_id": "ex-current", "user_answer": "-5"}
    payload.update(overrides)
    return asyncio.run(evaluate_exercise_answer(ExerciseEvaluateRequest(**payload), container))


def test_numeric_exercise_uses_certified_type_and_kc(tmp_path):
    container = _container(tmp_path, _exercise())
    result = _evaluate(container, user_answer="valor -5", notebook_id="nb-current")
    assert result["status"] == "GRADED"
    assert result["is_correct"] is True
    assert result["kc_id"] == "kc-current"
    assert container.bkt_tracker.get_state("kc-current").attempts == 1


@pytest.mark.parametrize(
    "exercise, request_changes",
    [
        (None, {}),
        (_exercise(status=ExerciseVerificationStatus.UNVERIFIED), {}),
        (_exercise(), {"exercise_id": "missing-exercise"}),
        (_exercise(), {"notebook_id": "other-notebook"}),
        (replace(_exercise(), expected_answer=""), {}),
        (replace(_exercise(kind=ExerciseType.MC), options=None), {}),
    ],
)
def test_rejected_certified_identity_or_definition_cannot_mutate_bkt(
    tmp_path, exercise, request_changes
):
    container = _container(tmp_path, exercise)
    result = _evaluate(container, **request_changes)
    assert result["status"] == "UNGRADED"
    assert container.bkt_tracker.get_state("kc-current").attempts == 0


def test_client_option_count_cannot_override_certified_count(tmp_path):
    container = _container(tmp_path, _exercise(kind=ExerciseType.MC))
    container.bkt_tracker.update = Mock(wraps=container.bkt_tracker.update)
    request = ExerciseEvaluateRequest.model_validate({
        "exercise_id": "ex-current", "user_answer": "B", "options_count": 99,
    })
    result = asyncio.run(evaluate_exercise_answer(request, container))
    assert result["status"] == "GRADED"
    assert result["is_correct"] is True
    assert container.bkt_tracker.get_state("kc-current").attempts == 1
    assert container.bkt_tracker.update.call_args.kwargs["n_options"] == 3


def test_uncertified_id_cannot_fall_through_to_generated_registry(tmp_path):
    generated = {
        "exercise_id": "ex-current", "source": "generated", "kind": "trace",
        "kc_ids": ["kc-current"], "oracle": {"type": "state_match", "final_state": {}},
    }
    container = _container(
        tmp_path, _exercise(status=ExerciseVerificationStatus.UNVERIFIED), generated
    )
    result = _evaluate(container)
    assert result["status"] == "UNGRADED"
    assert container.bkt_tracker.get_state("kc-current").attempts == 0


def test_generated_registry_rejects_kind_or_kc_mismatch_before_mutation(tmp_path):
    generated = {
        "exercise_id": "ex-current", "source": "generated", "kind": "trace",
        "kc_ids": ["kc-foreign"], "oracle": {"type": "bug_class", "accept": ["x"]},
    }
    container = _container(tmp_path, generated=generated)
    result = _evaluate(container, notebook_id="nb-current")
    assert result["status"] == "UNGRADED"
    assert container.bkt_tracker.get_state("kc-current").attempts == 0
    assert container.bkt_tracker.get_state("kc-foreign").attempts == 0


def test_registered_generated_exercise_preserves_valid_flow(tmp_path):
    generated = {
        "exercise_id": "ex-current", "source": "generated", "kind": "debugging",
        "kc_ids": ["kc-current"], "prompt": "Describe the bug",
        "oracle": {"type": "bug_class", "accept": ["overflow"], "cwe": "CWE-120"},
    }
    container = _container(tmp_path, generated=generated)
    result = _evaluate(container, user_answer="overflow", notebook_id="nb-current")
    assert result["status"] == "GRADED"
    assert result["source"] == "generated"
    assert result["is_correct"] is True
    assert container.bkt_tracker.get_state("kc-current").attempts == 1


@pytest.mark.parametrize(
    "change",
    [
        {"exercise_id": "other-id"},
        {"source": "unverified"},
        {"kind": "trace"},
        {"oracle": {"type": "bug_class", "accept": []}},
        {"kc_ids": ["kc-foreign"]},
    ],
)
def test_generated_identity_and_definition_fail_closed(tmp_path, change):
    generated = {
        "exercise_id": "ex-current", "source": "generated", "kind": "debugging",
        "kc_ids": ["kc-current"], "prompt": "Describe the bug",
        "oracle": {"type": "bug_class", "accept": ["overflow"]},
    }
    generated.update(change)
    container = _container(tmp_path, generated=generated)
    result = _evaluate(container, notebook_id="nb-current")
    assert result["status"] == "UNGRADED"
    assert container.bkt_tracker.get_state("kc-current").attempts == 0
