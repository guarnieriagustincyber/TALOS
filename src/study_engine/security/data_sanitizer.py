"""DataSanitizer: Pre-flight detection and blocking of accidental PII and credentials (Ola 5, Fase 5.1).

Detects API keys, passwords, emails, and DNIs without falsely blocking technical
computer science concepts (hex addresses, buffer sizes, clock frequencies, inumbers).
"""

import logging
import re
from typing import List, NamedTuple, Tuple
import unicodedata

logger = logging.getLogger(__name__)


class ScrubResult(NamedTuple):
    clean_prompt: str
    has_pii: bool
    detected_patterns: List[str]


class DataSanitizer:
    """Pre-flight security filter inspecting prompts before external provider egress."""

    # 1. Hard matching patterns (ALWAYS blocked regardless of context)
    HARD_PII_PATTERNS = [
        # API Keys & Tokens
        (r"\bsk-[a-zA-Z0-9]{20,}\b", "OPENAI_API_KEY"),
        (r"\bghp_[a-zA-Z0-9]{36}\b", "GITHUB_PERSONAL_TOKEN"),
        (r"\bAKIA[0-9A-Z]{16}\b", "AWS_ACCESS_KEY"),
        (r"\beyJ[a-zA-Z0-9_-]{10,}\.eyJ[a-zA-Z0-9_-]{10,}\.[a-zA-Z0-9_-]{10,}\b", "JWT_TOKEN"),
        (r"\bAIza[a-zA-Z0-9_-]{35}\b", "GOOGLE_API_KEY"),

        # Credentials
        (r"(?i)\bpassword\s*[:=]\s*\S+", "PASSWORD_CREDENTIAL"),
        (r"(?i)\bcontrase[ñn]a\s*[:=]\s*\S+", "PASSWORD_CREDENTIAL"),

        # Emails
        (r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b", "EMAIL_ADDRESS"),

        # DNI Formato Punteado Inequívoco (ej: 12.345.678)
        (r"\b\d{2}\.\d{3}\.\d{3}\b", "DNI_PUNTEADO"),

        # DNI sin puntos con contexto personal explícito (ej: "DNI: 34567890", "legajo = 12345678")
        (r"(?i)\b(dni|documento|legajo|cuil|cuit)\s*[:=]?\s*\d{7,8}\b", "DNI_CONTEXTUAL"),
    ]

    # 2. Technical Whitelist (Technical terms, units, hex addresses that MUST NEVER be flagged as PII)
    TECHNICAL_WHITELIST_REGEX = re.compile(
        r"(0x[0-9a-fA-F]+|\b\d+\s*(bytes?|hz|khz|mhz|ghz|ms|ns|s|us|ciclos?|inodos?|puertos?|offset|buffer|bits?|kb|mb|gb|tb)\b)",
        re.IGNORECASE,
    )

    # 3. Generic 7-8 digits pattern (requires context check to avoid false positives)
    GENERIC_7_8_DIGITS = re.compile(r"\b\d{7,8}\b")

    def scrub(self, prompt: str) -> ScrubResult:
        """Scan input prompt for sensitive credentials and personal data.

        Returns:
            ScrubResult: (prompt, has_pii, detected_patterns)
        """
        if not prompt or not prompt.strip():
            return ScrubResult(clean_prompt="", has_pii=False, detected_patterns=[])

        detected: List[str] = []

        # NFKC normalization and strip invisible zero-width chars to prevent token smuggling
        normalized_prompt = unicodedata.normalize("NFKC", prompt)
        clean_prompt = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", normalized_prompt)

        # 1. Check hard matching patterns against both raw and sanitized variations
        for pattern, label in self.HARD_PII_PATTERNS:
            if re.search(pattern, prompt) or re.search(pattern, clean_prompt):
                detected.append(label)

        # 2. Check for isolated 7-8 digits
        # If found, verify it is not covered by technical whitelist
        for match in self.GENERIC_7_8_DIGITS.finditer(prompt):
            matched_str = match.group(0)
            start_pos = max(0, match.start() - 20)
            end_pos = min(len(prompt), match.end() + 20)
            surrounding_context = prompt[start_pos:end_pos]

            if self.TECHNICAL_WHITELIST_REGEX.search(surrounding_context):
                # Valid technical number (e.g. 10000000 bytes or offset), skip
                continue

            # If isolated 7-8 digit without personal context keyword, log warning but do not block
            logger.info("Informational warning: Uncontextualized 7-8 digit number observed: %s", matched_str)

        has_pii = len(detected) > 0
        return ScrubResult(
            clean_prompt=prompt,
            has_pii=has_pii,
            detected_patterns=list(set(detected)),
        )
