"""DataSanitizer - Outbound Border Control for TalosLLMPool (Fase 5.9 / Pilar 3).

Detects sensitive information (IPs, system paths, credentials, tokens, emails)
in outbound prompts/contexts. Enforces fail-closed isolation to prevent data leaks
to public cloud free tiers.
"""

import re
from typing import List, Pattern, Tuple


class SensitiveDataLeakError(RuntimeError):
    """Raised when sensitive data is detected and cannot be processed safely (fail-closed)."""
    pass


class DataSanitizer:
    """Outbound data inspection and scrubbing engine."""

    # Regex patterns for sensitive data detection
    IPV4_PATTERN: Pattern[str] = re.compile(
        r"\b(?:(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\.){3}"
        r"(?:25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[1-9]?[0-9])\b"
    )
    IPV6_PATTERN: Pattern[str] = re.compile(
        r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b|"
        r"\b(?:[0-9a-fA-F]{1,4}:){1,7}:|"
        r"\b:(?::[0-9a-fA-F]{1,4}){1,7}\b|"
        r"\bfe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}\b"
    )
    SYSTEM_PATHS_LINUX: Pattern[str] = re.compile(
        r"(?:\s|^|\"|')/(?:etc|home|root|var|sys|proc|boot)/[^\s\"'<>]+"
    )
    SYSTEM_PATHS_WINDOWS: Pattern[str] = re.compile(
        r"[a-z]:\\(?:Windows|Users|Program Files|ProgramData)[^\s\"'<>]*|"
        r"\\Windows\\System32[^\s\"'<>]*",
        re.IGNORECASE,
    )
    AWS_KEY_PATTERN: Pattern[str] = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
    BEARER_TOKEN_PATTERN: Pattern[str] = re.compile(
        r"(?i)\bbearer\s+[a-zA-Z0-9_\-\.]{20,}\b"
    )
    JWT_PATTERN: Pattern[str] = re.compile(
        r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b"
    )
    PRIVATE_KEY_PATTERN: Pattern[str] = re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----"
    )
    PASSWORD_ASSIGN_PATTERN: Pattern[str] = re.compile(
        r"(?i)\b[a-zA-Z0-9_-]*(?:password|passwd|secret|api_key|apikey)\b\s*[:=]\s*[\"']?([^\s\"';,\n]+)"
    )
    EMAIL_PATTERN: Pattern[str] = re.compile(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
    )

    def find_sensitive_items(self, text: str) -> List[Tuple[str, str]]:
        """Identify all sensitive categories and matching fragments."""
        if not text:
            return []

        findings: List[Tuple[str, str]] = []

        for match in self.IPV4_PATTERN.finditer(text):
            findings.append(("ipv4", match.group(0)))

        for match in self.IPV6_PATTERN.finditer(text):
            findings.append(("ipv6", match.group(0)))

        for match in self.SYSTEM_PATHS_LINUX.finditer(text):
            findings.append(("system_path_linux", match.group(0).strip()))

        for match in self.SYSTEM_PATHS_WINDOWS.finditer(text):
            findings.append(("system_path_windows", match.group(0).strip()))

        for match in self.AWS_KEY_PATTERN.finditer(text):
            findings.append(("aws_key", match.group(0)))

        for match in self.BEARER_TOKEN_PATTERN.finditer(text):
            findings.append(("bearer_token", match.group(0)))

        for match in self.JWT_PATTERN.finditer(text):
            findings.append(("jwt_token", match.group(0)))

        for match in self.PRIVATE_KEY_PATTERN.finditer(text):
            findings.append(("private_key", match.group(0)))

        for match in self.PASSWORD_ASSIGN_PATTERN.finditer(text):
            findings.append(("credential", match.group(0)))

        for match in self.EMAIL_PATTERN.finditer(text):
            findings.append(("email", match.group(0)))

        return findings

    def is_sensitive(self, text: str) -> bool:
        """Return True if text contains any sensitive information."""
        if not text:
            return False
        return len(self.find_sensitive_items(text)) > 0

    def scrub(self, prompt: str, context: str = "") -> Tuple[str, str, bool]:
        """Inspect prompt and context. Returns (prompt, context, is_sensitive)."""
        combined = f"{prompt}\n{context}"
        sensitive = self.is_sensitive(combined)
        return prompt, context, sensitive

    def sanitize(self, text: str) -> str:
        """Sanitize text by redacting detected sensitive fragments (passwords, tokens, keys)."""
        if not text:
            return ""
        sanitized = text
        for category, item in self.find_sensitive_items(text):
            if category in ("credential", "bearer_token", "jwt_token", "private_key", "aws_key"):
                sanitized = sanitized.replace(item, f"[REDACTED_{category.upper()}]")
        return sanitized
