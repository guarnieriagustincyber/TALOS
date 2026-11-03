"""Synthetic SQLite contract tests for T13a session and episode identity."""

from datetime import datetime, timezone
import dataclasses
import json
from pathlib import Path
import sqlite3
from types import SimpleNamespace

import pytest

from study_engine.pedagogy.episode_contracts import Episode, EpisodePhase
from study_engine.session.session_store import SessionStore
from study_engine.session.study_session_contracts import (
    AuthoritativeSessionState,
    CurriculumPosition,
    OpeningBriefFacts,
)
from study_engine.session.study_session_orchestrator import StudySessionOrchestrator


def _session_blob(session_id: str, notebook_id: str, student_id: str) -> dict:
    return {
        "session_id": session_id,
        "notebook_id": notebook_id,
        "student_id": student_id,
        "curriculum_id": f"curr-{notebook_id}",
        "current_kc_id": f"{notebook_id}-kc-1",
        "episode_id": f"episode-{session_id}",
        "episode_phase": "EVALUATING",
        "available_actions": ["SUBMIT_ANSWER"],
        "created_at": datetime(2026, 10, 19, tzinfo=timezone.utc).isoformat(),
        "state_hash": "a" * 64,
    }


def test_session_and_episode_identity_survive_sqlite_reopen(tmp_path: Path) -> None:
    db_path = tmp_path / "synthetic" / "sessions.db"
    store = SessionStore(db_path)
    store.upsert(_session_blob("session-1", "notebook-a", "student-a"))
    episode = Episode(
        episode_id="episode-session-1",
        notebook_id="notebook-a",
        kc_id="notebook-a-kc-1",
        objective="synthetic objective",
        phase=EpisodePhase.EVALUATING,
        current_step_id="step-exercise-1",
        session_id="session-1",
        created_at=datetime(2026, 10, 19, tzinfo=timezone.utc),
        idempotency_keys_consumed=frozenset({"attempt-previous"}),
        metadata={"origin": "synthetic-test"},
    )
    store.save_episode(episode)
    store.close()

    reopened = SessionStore(db_path)
    sessions = reopened.load_all_active()
    restored_episode = reopened.load_episode("episode-session-1")

    assert len(sessions) == 1
    assert sessions[0]["session_id"] == "session-1"
    assert sessions[0]["notebook_id"] == "notebook-a"
    assert sessions[0]["episode_id"] == episode.episode_id
    assert restored_episode == episode
    assert restored_episode.session_id == "session-1"
    reopened.close()


def test_sessions_are_isolated_and_session_identity_cannot_change(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions.db")
    store.upsert(_session_blob("session-a", "notebook-a", "student-a"))
    store.upsert(_session_blob("session-b", "notebook-b", "student-a"))

    with pytest.raises(ValueError, match="Session identity conflict"):
        store.upsert(_session_blob("session-a", "notebook-b", "student-a"))

    rows = {row["session_id"]: row for row in store.load_all_active()}
    assert set(rows) == {"session-a", "session-b"}
    assert rows["session-a"]["notebook_id"] == "notebook-a"
    assert rows["session-b"]["notebook_id"] == "notebook-b"
    store.close()


def test_episode_identity_cannot_be_rebound_to_another_notebook_or_kc(
    tmp_path: Path,
) -> None:
    store = SessionStore(tmp_path / "sessions.db")
    episode = Episode(
        episode_id="episode-fixed",
        notebook_id="notebook-a",
        kc_id="kc-a",
        objective="objective",
    )
    store.save_episode(episode)

    with pytest.raises(ValueError, match="Episode identity conflict"):
        store.save_episode(
            Episode(
                episode_id="episode-fixed",
                notebook_id="notebook-b",
                kc_id="kc-b",
                objective="tampered objective",
            )
        )

    assert store.load_episode("episode-fixed") == episode
    store.close()


def test_legacy_session_and_episode_rows_remain_readable(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-sessions.db"
    store = SessionStore(db_path)
    session = _session_blob("legacy-session", "legacy-notebook", "legacy-student")
    store.upsert(session)
    store.close()

    conn = sqlite3.connect(db_path)
    legacy_state = dict(session)
    legacy_state.pop("student_id")
    conn.execute(
        "UPDATE study_sessions SET state_blob=? WHERE session_id=?",
        (json.dumps(legacy_state), "legacy-session"),
    )
    conn.execute("DROP TABLE study_episodes")
    conn.execute(
        """CREATE TABLE study_episodes (
             episode_id TEXT PRIMARY KEY NOT NULL,
             notebook_id TEXT NOT NULL,
             kc_id TEXT NOT NULL,
             episode_blob TEXT NOT NULL,
             updated_at TEXT NOT NULL
           )"""
    )
    legacy_episode = {
        "episode_id": "legacy-episode",
        "notebook_id": "legacy-notebook",
        "kc_id": "legacy-kc",
        "objective": "legacy objective",
        "phase": "EVALUATING",
        "current_step_id": "legacy-step",
        "created_at": "2026-10-19T00:00:00+00:00",
        "idempotency_keys_consumed": [],
        "metadata": {},
    }
    conn.execute(
        "INSERT INTO study_episodes VALUES (?, ?, ?, ?, ?)",
        (
            "legacy-episode",
            "legacy-notebook",
            "legacy-kc",
            json.dumps(legacy_episode),
            "2026-10-19T00:00:00+00:00",
        ),
    )
    conn.commit()
    conn.close()

    migrated = SessionStore(db_path)
    loaded_sessions = migrated.load_all_active()
    loaded_episode = migrated.load_episode("legacy-episode")
    assert loaded_sessions[0]["student_id"] == "legacy-student"
    assert loaded_episode is not None
    assert loaded_episode.session_id is None
    migrated.close()


def test_study_session_orchestrator_rehydrates_authoritative_state(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "sessions.db"
    store = SessionStore(db_path)
    created_at = datetime(2026, 10, 19, tzinfo=timezone.utc)
    position = CurriculumPosition(
        unit_or_module="unit-1",
        unit_name="synthetic unit",
        kcs_in_unit=("kc-1",),
        kcs_completed=(),
        kcs_in_progress=(),
        kcs_pending=("kc-1",),
    )
    facts = OpeningBriefFacts(
        notebook_id="notebook-a",
        notebook_name="synthetic notebook",
        notebook_purpose="isolation test",
        curriculum_position=position,
        eligible_kcs=("kc-1",),
        selected_kc="kc-1",
        selected_kc_rationale="synthetic selection",
        bkt_estimate=0.1,
        bkt_note="synthetic estimate",
        student_context=None,
        student_context_note="no student context",
        proposed_action="CONTINUE",
        proposed_action_rationale="synthetic policy",
    )
    state_hash = AuthoritativeSessionState.compute_hash(
        session_id="session-a",
        notebook_id="notebook-a",
        student_id="student-a",
        current_kc_id="kc-1",
        episode_id="episode-a",
        episode_phase="EVALUATING",
        available_actions=("SUBMIT_ANSWER",),
    )
    state = AuthoritativeSessionState(
        session_id="session-a",
        notebook_id="notebook-a",
        student_id="student-a",
        created_at=created_at,
        curriculum_id="curriculum-a",
        current_kc_id="kc-1",
        episode_id="episode-a",
        episode_phase="EVALUATING",
        available_actions=("SUBMIT_ANSWER",),
        bkt_state_ref="kc-1",
        student_context_ref=None,
        opening_brief_facts=facts,
        opening_brief_narrative="synthetic narrative",
        state_hash=state_hash,
    )
    episode = Episode(
        episode_id="episode-a",
        notebook_id="notebook-a",
        kc_id="kc-1",
        objective="synthetic objective",
        phase=EpisodePhase.EVALUATING,
        current_step_id="step-exercise-a",
        created_at=created_at,
    )
    store.upsert(StudySessionOrchestrator._serialize_state(None, state))
    store.save_episode(episode)
    store.close()

    reopened = SessionStore(db_path)

    class _Registry:
        @staticmethod
        def get_sources_for_notebook(notebook_id: str) -> list[str]:
            return ["synthetic-source"] if notebook_id == "notebook-a" else []

    class _Pedagogy:
        _kc_catalog = {"notebook-a": {"kcs": [{"kc_id": "kc-1", "title": "KC one"}]}}
        bkt_tracker = None

        def get_episode(self, episode_id: str):
            return reopened.load_episode(episode_id)

    orchestrator = StudySessionOrchestrator(
        notebook_registry=_Registry(),
        pedagogical_orchestrator=_Pedagogy(),
        progression_policy=SimpleNamespace(policy_version="synthetic-v1"),
        session_store=reopened,
    )
    snapshot = orchestrator.get_snapshot("session-a")

    assert snapshot.session_id == "session-a"
    assert snapshot.notebook_id == "notebook-a"
    assert snapshot.student_id == "student-a"
    assert snapshot.current_kc_id == "kc-1"
    assert snapshot.episode_id == "episode-a"
    assert snapshot.episode_phase == EpisodePhase.EVALUATING.value
    assert snapshot.exercise_available is True
    assert dataclasses.asdict(snapshot.curriculum_position) == dataclasses.asdict(position)
    reopened.close()
