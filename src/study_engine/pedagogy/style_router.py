"""ConversationStyleRouter: Three-level deterministic routing for natural dialogue (Ola 6, Fase 6.2).

Classifies incoming student prompts without using an LLM:
Level 1: Explicit slash commands (/practicar, /ejercicio, /comparar, etc.).
Level 2: Semantic keywords & patterns (analogy, cross-source, verification, practice, casual signals, formal keywords).
Level 3: Length fallback (>12 words -> FORMAL_EXPLANATION, <= 12 words -> CASUAL_CHAT).

Invariants:
- INV-W5-3: Router NEVER decides KCs, pedagogical transitions, or BKT mastery.
- Anti-Recorte Rule: Explanations are never cut short to save tokens.
- Deterministic execution: <1ms latency, 0 LLM calls.
"""

from enum import Enum
import re
from typing import NamedTuple, Optional

from study_engine.pedagogy.style_contracts import (
    ConversationStyle,
    StyleContract,
    STYLE_CONTRACTS,
    STYLE_DIRECTIVES,
)


class StyleRouteResult(NamedTuple):
    style: ConversationStyle
    instruction_directive: str
    target_arg: Optional[str] = None
    contract: Optional[StyleContract] = None


class ConversationStyleRouter:
    """Deterministic, three-level conversational style router."""

    # Level 1: Slash Commands
    RE_PRACTICE_CMD = re.compile(r"^/(?:practicar|ejercicio|practice)\b(?:\s+(.*))?", re.IGNORECASE)
    RE_CROSS_CMD = re.compile(r"^/(?:comparar|contrastar|cross)\b(?:\s+(.*))?", re.IGNORECASE)
    RE_ANALOGY_CMD = re.compile(r"^/(?:analogia|analogy)\b(?:\s+(.*))?", re.IGNORECASE)
    RE_VERIFY_CMD = re.compile(r"^/(?:verificar|verify)\b(?:\s+(.*))?", re.IGNORECASE)

    # Level 2: Semantic Heuristics & Keywords
    RE_ANALOGY = re.compile(
        r"\b(analog[ií]a|como si fuera|imagin[aá]|ejemplo de la vida( real)?|met[aá]fora|haceme una analog[ií]a|explicame como a un)\b",
        re.IGNORECASE,
    )
    RE_CROSS_SOURCE = re.compile(
        r"\b(compar[aá]|diferencia entre|vs\.?|versus|qu[eé] dice .* vs|contrast[aá]|frente a)\b",
        re.IGNORECASE,
    )
    RE_VERIFICATION = re.compile(
        r"^(es (verdad|cierto|correcto) que|\u00bf?es (verdad|cierto|correcto)|\u00bf?se puede|\u00bf?est[aá] bien si|verdad que|\u00bf?(?:existe|hay))\b",
        re.IGNORECASE,
    )
    RE_PRACTICE_PHRASE = re.compile(
        r"\b(dame un ejercicio|quiero practicar|hacer un ejercicio|proponeme un ejercicio)\b",
        re.IGNORECASE,
    )
    RE_FORMAL_KEYWORDS = re.compile(
        r"\b(defin[ií]|demostr[aá]|desarroll[aá]|an[aá]lisis formal|teorema|prueba formal|c[oó]digo|algoritmo|funci[oó]n|"
        r"puntero\w*|memoria|segfault|crash|abi|implementa|explic\w*|c[oó]mo funciona|qu[eé] es|detall\w*|profundiz\w*|ampli\w*|"
        r"m[aá]s\s+detalles?|m[aá]s\s+a\s+detalle|conceptual(?:mente)?|"
        r"metadato\w*|integridad|stack|heap|bss|data|text|retorno|frame\s+pointer|direcci[oó]n|registro\w*|"
        r"ampersand|asterisco|operador\w*|desreferenci\w*)\b",
        re.IGNORECASE,
    )
    RE_CASUAL_SIGNALS = re.compile(
        r"\b(che|no entend[ií]|o sea|posta|dale|bueno|hola|buenas)\b",
        re.IGNORECASE,
    )

    @classmethod
    def detect_style(cls, query: str) -> StyleRouteResult:
        """Detects the appropriate conversation style deterministically (Levels 1 -> 2 -> 3)."""
        clean_q = query.strip()
        if not clean_q:
            return cls._build_result(ConversationStyle.FORMAL_EXPLANATION)

        # ---------------------------------------------------------
        # LEVEL 1: Explicit Slash Commands
        # ---------------------------------------------------------
        m_prac = cls.RE_PRACTICE_CMD.match(clean_q)
        if m_prac:
            target = m_prac.group(1).strip() if m_prac.group(1) else None
            return cls._build_result(ConversationStyle.PRACTICE, target_arg=target)

        m_cross = cls.RE_CROSS_CMD.match(clean_q)
        if m_cross:
            target = m_cross.group(1).strip() if m_cross.group(1) else None
            return cls._build_result(ConversationStyle.CROSS_SOURCE, target_arg=target)

        m_analogy = cls.RE_ANALOGY_CMD.match(clean_q)
        if m_analogy:
            target = m_analogy.group(1).strip() if m_analogy.group(1) else None
            return cls._build_result(ConversationStyle.ANALOGY_REQUEST, target_arg=target)

        m_verify = cls.RE_VERIFY_CMD.match(clean_q)
        if m_verify:
            target = m_verify.group(1).strip() if m_verify.group(1) else None
            return cls._build_result(ConversationStyle.VERIFICATION, target_arg=target)

        # ---------------------------------------------------------
        # LEVEL 2: Semantic Heuristics & Keywords
        # ---------------------------------------------------------
        # 2a. Practice phrase
        if cls.RE_PRACTICE_PHRASE.search(clean_q):
            return cls._build_result(ConversationStyle.PRACTICE)

        # 2b. Analogy request
        if cls.RE_ANALOGY.search(clean_q):
            return cls._build_result(ConversationStyle.ANALOGY_REQUEST)

        # 2c. Cross-source comparison
        if cls.RE_CROSS_SOURCE.search(clean_q):
            return cls._build_result(ConversationStyle.CROSS_SOURCE)

        # 2d. Verification query
        if cls.RE_VERIFICATION.search(clean_q):
            return cls._build_result(ConversationStyle.VERIFICATION)

        # 2e. Formal technical keywords
        if cls.RE_FORMAL_KEYWORDS.search(clean_q):
            return cls._build_result(ConversationStyle.FORMAL_EXPLANATION)

        # 2f. Casual signals (solo en texto no-código y en consultas breves)
        non_code_q = re.sub(r'```.*?```', '', clean_q, flags=re.DOTALL)
        non_code_q = re.sub(r'"[^"]*"', '', non_code_q)
        non_code_q = re.sub(r"'[^']*'", '', non_code_q)
        if len(clean_q.split()) <= 12 and cls.RE_CASUAL_SIGNALS.search(non_code_q):
            return cls._build_result(ConversationStyle.CASUAL_CHAT)

        # ---------------------------------------------------------
        # LEVEL 3: Length Fallback (Word Count)
        # ---------------------------------------------------------
        words = clean_q.split()
        if len(words) > 12:
            return cls._build_result(ConversationStyle.FORMAL_EXPLANATION)

        # Short / Casual prompt (<= 12 words)
        return cls._build_result(ConversationStyle.CASUAL_CHAT)

    @classmethod
    def _build_result(
        cls,
        style: ConversationStyle,
        target_arg: Optional[str] = None,
    ) -> StyleRouteResult:
        contract = STYLE_CONTRACTS.get(style)
        directive = STYLE_DIRECTIVES.get(style, "")
        return StyleRouteResult(
            style=style,
            instruction_directive=directive,
            target_arg=target_arg,
            contract=contract,
        )
