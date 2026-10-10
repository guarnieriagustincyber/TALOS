"""Fail-closed admin authorization tests for student exercise oracle routes."""

import pytest
from fastapi import HTTPException

from study_engine.web.dependencies import AppContainer
from study_engine.web.routes.student_exercises import _check_admin_token

_SYNTHETIC_ADMIN_TOKEN = "synthetic-admin-token-for-focused-tests-012345"


def test_admin_authorization_requires_configured_synthetic_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("TALOS_ADMIN_TOKEN", raising=False)
    with pytest.raises(HTTPException) as missing_configuration:
        _check_admin_token(_SYNTHETIC_ADMIN_TOKEN)
    assert missing_configuration.value.status_code == 503

    monkeypatch.setenv("TALOS_ADMIN_TOKEN", _SYNTHETIC_ADMIN_TOKEN)
    _check_admin_token(_SYNTHETIC_ADMIN_TOKEN)

    with pytest.raises(HTTPException) as missing_header:
        _check_admin_token(None)
    assert missing_header.value.status_code == 403

    with pytest.raises(HTTPException) as invalid_token:
        _check_admin_token("synthetic-wrong-token")
    assert invalid_token.value.status_code == 403


@pytest.mark.parametrize(
    "insecure_token",
    [
        "short",
        "x" * 40,
        "synthetic-placeholder-token-value",
    ],
)
def test_admin_authorization_rejects_weak_configuration(
    monkeypatch: pytest.MonkeyPatch,
    insecure_token: str,
) -> None:
    monkeypatch.setenv("TALOS_ADMIN_TOKEN", insecure_token)

    with pytest.raises(HTTPException) as insecure_configuration:
        _check_admin_token(insecure_token)

    assert insecure_configuration.value.status_code == 503


def test_dotenv_loaded_after_route_import_is_used_dynamically(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    monkeypatch.delenv("TALOS_ADMIN_TOKEN", raising=False)
    (tmp_path / ".env").write_text(
        "TALOS_ADMIN_TOKEN=synthetic-dotenv-admin-token-value-for-tests-012345\n",
        encoding="utf-8",
    )

    container = AppContainer.__new__(AppContainer)
    container.repo_root = tmp_path
    container._load_dotenv()

    _check_admin_token("synthetic-dotenv-admin-token-value-for-tests-012345")
