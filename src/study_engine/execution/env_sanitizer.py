"""Environment sanitization and safe variable construction for S6.1.

INVARIANTS:
1. Primary Defense: Only allowlisted environment variables pass to child.
2. Secondary Defense: Pattern matching blocks any residual secrets/keys/tokens.
3. Strict Sanitization: Zero LLM keys, DB credentials, or host secrets leak.
4. Python Unbuffered: Forced UTF-8 encoding and unbuffered I/O.
"""

import fnmatch
import os
from typing import Dict, Optional

from study_engine.contracts.execution import EnvironmentPolicy


def is_pattern_blocked(key: str, forbidden_patterns: tuple[str, ...]) -> bool:
    """Check if variable name matches any forbidden glob pattern."""
    key_upper = key.upper()
    for pattern in forbidden_patterns:
        if fnmatch.fnmatch(key_upper, pattern.upper()):
            return True
    return False


def build_sanitized_environment(
    policy: EnvironmentPolicy,
    host_env: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Construct pristine, safe environment dictionary for student subprocess.

    Args:
        policy: Authoritative EnvironmentPolicy defining allowed variables.
        host_env: Optional host environment dict (defaults to os.environ).

    Returns:
        Isolated, sanitized environment dictionary.
    """
    source = host_env if host_env is not None else dict(os.environ)
    sanitized: Dict[str, str] = {}

    # 1. Transfer strictly allowlisted variables from source
    for name in policy.allowed_names:
        if name in source:
            val = source[name]
            # Verify secondary pattern check
            if not is_pattern_blocked(name, policy.forbidden_patterns):
                if len(val.encode("utf-8")) <= policy.max_value_bytes:
                    sanitized[name] = val

    # 2. Add custom allowlist if not matching forbidden patterns
    for name, val in policy.custom_allowlist.items():
        if not is_pattern_blocked(name, policy.forbidden_patterns):
            if len(val.encode("utf-8")) <= policy.max_value_bytes:
                sanitized[name] = val

    # 3. Force mandatory Python execution hygiene flags
    sanitized["PYTHONIOENCODING"] = "utf-8"
    sanitized["PYTHONUNBUFFERED"] = "1"
    sanitized["PYTHONDONTWRITEBYTECODE"] = "1"

    return sanitized
