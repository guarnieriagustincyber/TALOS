"""Shared fail-closed validation for administrative route tokens."""

import hmac
import os
from typing import Optional

from fastapi import HTTPException, status

_ADMIN_TOKEN_MIN_LENGTH = 32
_PREDICTABLE_ADMIN_TOKENS = frozenset(
    {"admin", "changeme", "change-me", "password", "secret", "test"}
)
_PREDICTABLE_ADMIN_MARKERS = ("changeme", "change-me", "example", "placeholder")


def require_admin_token(
    supplied_token: Optional[str],
    *,
    forbidden_detail: str,
) -> None:
    """Require a configured, non-placeholder token with a minimally safe shape."""
    expected_token = os.getenv("TALOS_ADMIN_TOKEN")
    if (
        expected_token is None
        or len(expected_token) < _ADMIN_TOKEN_MIN_LENGTH
        or not expected_token.isascii()
        or not expected_token.isprintable()
        or any(character.isspace() for character in expected_token)
        or len(set(expected_token)) < 8
        or expected_token.casefold() in _PREDICTABLE_ADMIN_TOKENS
        or any(
            marker in expected_token.casefold()
            for marker in _PREDICTABLE_ADMIN_MARKERS
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Autorización administrativa no configurada de forma segura.",
        )

    if (
        not supplied_token
        or not hmac.compare_digest(
            supplied_token.encode("utf-8"),
            expected_token.encode("utf-8"),
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=forbidden_detail,
        )
