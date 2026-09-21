"""Unit tests for environment sanitization in Subsystem S6.1."""

from study_engine.contracts.execution import EnvironmentPolicy
from study_engine.execution.env_sanitizer import (
    build_sanitized_environment,
    is_pattern_blocked,
)


def test_is_pattern_blocked() -> None:
    """Verify pattern matching detects sensitive variable names."""
    patterns = ("*KEY*", "*TOKEN*", "AWS_*", "OPENAI_*")
    assert is_pattern_blocked("OPENAI_API_KEY", patterns) is True
    assert is_pattern_blocked("GITHUB_TOKEN", patterns) is True
    assert is_pattern_blocked("AWS_SECRET_ACCESS_KEY", patterns) is True
    assert is_pattern_blocked("PATH", patterns) is False
    assert is_pattern_blocked("LANG", patterns) is False


def test_build_sanitized_environment_primary_allowlist() -> None:
    """Verify only allowlisted variables pass from host to sanitized dict."""
    host_env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "en_US.UTF-8",
        "HOME": "/home/agustin",
        "USER": "agustin",
        "OPENAI_API_KEY": "sk-1234567890",
        "GEMINI_API_KEY": "gem-secret-token",
        "ANTHROPIC_API_KEY": "ant-secret-key",
        "DATABASE_URL": "sqlite:////secret.db",
    }
    policy = EnvironmentPolicy(
        allowed_names=("PATH", "LANG"),
        forbidden_patterns=("*KEY*", "*SECRET*", "*TOKEN*"),
    )
    clean_env = build_sanitized_environment(policy, host_env)

    # Allowlisted present
    assert clean_env["PATH"] == "/usr/bin:/bin"
    assert clean_env["LANG"] == "en_US.UTF-8"

    # Non-allowlisted absent
    assert "HOME" not in clean_env
    assert "USER" not in clean_env
    assert "DATABASE_URL" not in clean_env

    # Secrets strictly absent
    assert "OPENAI_API_KEY" not in clean_env
    assert "GEMINI_API_KEY" not in clean_env
    assert "ANTHROPIC_API_KEY" not in clean_env

    # Mandatory Python flags forced
    assert clean_env["PYTHONIOENCODING"] == "utf-8"
    assert clean_env["PYTHONUNBUFFERED"] == "1"
    assert clean_env["PYTHONDONTWRITEBYTECODE"] == "1"


def test_build_sanitized_environment_custom_allowlist() -> None:
    """Verify safe custom allowlist entries pass, while unsafe are blocked."""
    policy = EnvironmentPolicy(
        allowed_names=("PATH",),
        forbidden_patterns=("*KEY*", "*SECRET*"),
        custom_allowlist={
            "SAFE_LAB_VAR": "value1",
            "UNSAFE_API_KEY": "secret_leak",
        },
    )
    clean_env = build_sanitized_environment(policy, {"PATH": "/bin"})
    assert clean_env["SAFE_LAB_VAR"] == "value1"
    assert "UNSAFE_API_KEY" not in clean_env
