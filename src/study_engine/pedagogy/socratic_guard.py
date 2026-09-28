"""Socratic Guard with rolling buffer for deterministic code block interception (Fase 5.8 / Refinamiento 2)."""

from dataclasses import dataclass
import re
from typing import List, Optional
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase


@dataclass(frozen=True)
class GuardResult:
    """Result of validating an incoming token or string chunk through SocraticGuard."""

    allowed: bool
    blocked_reason: Optional[str] = None
    emitted_token: str = ""
    replacement_message: Optional[str] = None


class SocraticGuard:
    """Deterministic token-streaming inspector enforcing pedagogical code restrictions."""

    _EXECUTABLE_FENCE_PATTERN = re.compile(
        r"```[ \t]*(c\+\+|c|h|cpp|python|py|java|javascript|js|rust|go|sql|"
        r"bash|sh|shell|php|ruby|perl|powershell)\b",
        re.IGNORECASE,
    )
    _FENCE_LABEL_PATTERN = re.compile(r"```[ \t]*([a-z][a-z0-9_+-]*)[ \t]*\r?\n", re.IGNORECASE)
    _UNLABELED_FENCE_PATTERN = re.compile(r"```[ \t]*\r?\n")
    _NON_EXECUTABLE_FENCE_LABELS = {
        "diff", "json", "markdown", "mermaid", "plain", "plaintext",
        "pseudocode", "text", "xml", "yaml", "yml",
    }
    _LANGUAGE_ALIASES = {"py": "python", "js": "javascript", "cpp": "c++"}

    DEFAULT_REPLACEMENT_MESSAGE = (
        "\n\n🛑 **[TALOS SocraticGuard]**\n\n"
        "Detuve un bloque ejecutable que no corresponde a las restricciones de este turno. "
        "Continúo con la explicación en el formato solicitado, sin agregar componentes extra."
    )

    def __init__(self, contract: PedagogicalContract, window_size: int = 150) -> None:
        self.contract = contract
        self.forbidden_patterns: List[str] = list(contract.forbidden_patterns)
        self.safe_words: List[str] = list(contract.safe_words)
        self.window_size = window_size
        self.buffer: str = ""
        self.pending_fence_prefix: str = ""
        self.is_blocked: bool = False

    def check_user_override(self, user_query: str) -> bool:
        """Check whether the user explicitly used any configured safe word or explicitly requested code/tests."""
        if not user_query:
            return False
        query_upper = user_query.strip().upper()
        for sw in self.safe_words:
            if sw.upper() in query_upper:
                return True

        # Permitir código si el estudiante solicitó expresamente código ejecutable o tests
        code_request_patterns = [
            r"\b(?:C[OÓ]DIGO|IMPLEMENTACI[OÓ]N|SCRIPT)\s+(?:EN\s+|DE\s+)?(?:PYTHON|C|RUST|BASH)\b",
            r"\b(?:CON\s+)?(?:TESTS?|PYTEST|PRUEBAS?\s+UNITARIAS)\b",
            r"\bC[OÓ]DIGO\s+(?:EN\s+PYTHON\s+)?CON\s+TESTS\b",
            r"\bC[OÓ]DIGO\s+PYTHON\b",
        ]
        for pat in code_request_patterns:
            if re.search(pat, query_upper):
                return True

        return False

    def validate_token(
        self,
        token: str,
        current_phase: ResponsePhase,
        user_query: str,
        allow_user_override: Optional[bool] = None,
        expected_code_language: Optional[str] = None,
    ) -> GuardResult:
        """Inspect an incoming token stream.
        
        Maintains a rolling buffer to catch patterns split across arbitrary token boundaries.
        Truncates the stream and injects a socratic intervention upon violation.
        """
        if self.is_blocked:
            return GuardResult(
                allowed=False,
                blocked_reason="STREAM_TERMINATED_AFTER_CODE_BLOCK",
            )

        user_override = (
            self.check_user_override(user_query)
            if allow_user_override is None
            else allow_user_override
        )
        code_allowed = current_phase.code_allowed or user_override
        candidate = self.pending_fence_prefix + token
        self.pending_fence_prefix = ""
        self.buffer += token

        fence_match = self._EXECUTABLE_FENCE_PATTERN.search(candidate)
        fence_label_match = self._FENCE_LABEL_PATTERN.search(candidate)
        invalid_label = (
            fence_label_match
            and self._canonical_language(fence_label_match.group(1))
            not in self._NON_EXECUTABLE_FENCE_LABELS
            and not self._EXECUTABLE_FENCE_PATTERN.search(fence_label_match.group(0))
        )
        unlabeled_fence = self._UNLABELED_FENCE_PATTERN.search(candidate)
        forbidden_pattern = not code_allowed and any(
            pattern in self.buffer for pattern in self.forbidden_patterns
        )
        if not code_allowed and (fence_match or invalid_label or unlabeled_fence or forbidden_pattern):
            self.is_blocked = True
            self.pending_fence_prefix = ""
            reason = (
                "UNSUPPORTED_CODE_FENCE_LABEL"
                if invalid_label or unlabeled_fence
                else "CODE_BLOCK_DETECTED_IN_NON_CODE_PHASE"
            )
            return GuardResult(
                allowed=False,
                blocked_reason=reason,
                emitted_token=candidate[: fence_match.start()] if fence_match else "",
                replacement_message=self.DEFAULT_REPLACEMENT_MESSAGE,
            )

        if code_allowed and fence_match and expected_code_language:
            actual_language = self._canonical_language(fence_match.group(1))
            expected_language = self._canonical_language(expected_code_language)
            if actual_language != expected_language:
                self.is_blocked = True
                return GuardResult(
                    allowed=False,
                    blocked_reason="REQUESTED_CODE_LANGUAGE_MISMATCH",
                    emitted_token=candidate[: fence_match.start()],
                    replacement_message=(
                        f"Detuve un bloque en {actual_language}; el pedido especifica "
                        f"{expected_language}. Respondé usando el lenguaje solicitado."
                    ),
                )

        if code_allowed and (invalid_label or unlabeled_fence):
            self.is_blocked = True
            return GuardResult(
                allowed=False,
                blocked_reason="UNSUPPORTED_CODE_FENCE_LABEL",
                emitted_token=candidate[: fence_label_match.start()] if fence_label_match else "",
                replacement_message=(
                    "Detuve un bloque con etiqueta Markdown no admitida. "
                    "Usá una etiqueta válida para el contenido solicitado."
                ),
            )

        pending_start = self._partial_fence_start(candidate)
        if pending_start is not None:
            self.pending_fence_prefix = candidate[pending_start:]
            candidate = candidate[:pending_start]

        return GuardResult(allowed=True, emitted_token=candidate)

    @classmethod
    def _canonical_language(cls, language: str) -> str:
        normalized = language.strip().lower()
        return cls._LANGUAGE_ALIASES.get(normalized, normalized)

    @staticmethod
    def _partial_fence_start(text: str) -> Optional[int]:
        """Hold an unfinished opening fence until its label can be validated."""
        for start in range(max(0, len(text) - 16), len(text)):
            suffix = text[start:]
            if suffix in ("`", "``"):
                return start
            if not suffix.startswith("```") or "\n" in suffix or "\r" in suffix:
                continue
            return start
        return None

    def flush_pending(self) -> str:
        """Release an incomplete trailing fence prefix after the model stream ends."""
        pending = self.pending_fence_prefix
        self.pending_fence_prefix = ""
        return pending

    def validate_text(
        self,
        full_text: str,
        current_phase: ResponsePhase,
        user_query: str,
        allow_user_override: Optional[bool] = None,
        expected_code_language: Optional[str] = None,
    ) -> GuardResult:
        """Convenience method to inspect a non-streamed full text block."""
        self.reset()
        return self.validate_token(
            full_text,
            current_phase,
            user_query,
            allow_user_override=allow_user_override,
            expected_code_language=expected_code_language,
        )

    def reset(self) -> None:
        """Reset internal buffer state for a fresh phase or query."""
        self.buffer = ""
        self.pending_fence_prefix = ""
        self.is_blocked = False
