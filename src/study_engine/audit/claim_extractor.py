"""Deterministic claim extraction and structural classification for S4.4.

Segments response text into granular claims and maps cited evidence tags [E#]
with structural claim typing (FACTUAL, PEDAGOGICAL, QUESTION, CONVERSATIONAL,
STRUCTURAL).

Markdown awareness
------------------
Presentation is not knowledge.  A section heading used as a label, a bulleted
label, a horizontal rule, a table separator or a line of code without a
natural-language assertion is classified as ``STRUCTURAL``: it is not a claim,
so it does not require a citation and it does not consume the bounded NLI
budget.  The same syntactic element *is* a ``FACTUAL`` claim when it carries a
finite predicate (an assertion) or an explicit citation tag.  Lists and code
blocks are therefore never excluded wholesale from factual control: their
assertions keep the full grounding requirement.
"""

import re
import unicodedata
from typing import List, Optional, Tuple
from pydantic import ConfigDict, Field

from study_engine.contracts.base import BaseContract
from study_engine.audit.contracts import ClaimType


_CITATION_PATTERN = re.compile(r"\[(E[0-9]+)\]")

_CONVERSATIONAL_PATTERNS = [
    re.compile(
        r"^\s*(hola|buenos días|buenas tardes|buenas noches|"
        r"saludos|bienvenidos)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(de nada|un gusto|hasta luego|adiós|éxitos)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*(¡?excelente|¡?muy bien|¡?buen trabajo|¡?correcto)\b",
        re.IGNORECASE,
    ),
]


# Statements about the *provided evidence* (absence, insufficiency) are
# meta-claims, not academic facts about the world.  They implement the
# abstention policy ("the evidence does not define X") and must not require a
# citation for themselves.  The patterns are anchored to the start of the
# sentence and deliberately reject contrastive continuations, so a model
# cannot wrap an unsupported world claim in an evidence disclaimer.
_EVIDENCE_META_PATTERNS = [
    re.compile(
        r"^\s*(?:la|el)\s+(?:evidencia|contexto|información|material|fuente|fuentes)\b"
        r"[^.!?]{0,120}?\b(?:no\s+(?:menciona|define|contiene|incluye|"
        r"proporciona|permite|especifica|indica|aborda|trata|aclara|detalla)|"
        r"carece\s+de|es\s+insuficiente|resulta\s+insuficiente)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*no\s+(?:se\s+)?(?:menciona|define|contiene|incluye|proporciona|"
        r"especifica|indica|aborda|hay|existe)\b[^.!?]{0,80}\b"
        r"(?:evidencia|contexto|información|fuente|fuentes|dato|datos)\b",
        re.IGNORECASE,
    ),
    # M1-03 (análisis live 034510Z): declaración explícita de ausencia de
    # evidencia en primera persona ("No tengo evidencia en las fuentes
    # autorizadas de este cuaderno para ..."). Es un meta-enunciado sobre el
    # estado de la evidencia, no un hecho del dominio: reclasificarlo como
    # CONVERSATIONAL evita que la honestidad epistémica del generador
    # dispare el fail-closed global (CHECK_FACTUAL_GROUNDING REJECTED
    # UNSUPPORTED) en respuestas correctamente abstencionistas.
    re.compile(
        r"^\s*no\s+(?:tengo|cuento\s+con|poseo)\s+evidencia\b[^.!?]{0,160}\b"
        r"(?:fuentes?|autorizadas?|evidencia|cuaderno)\b",
        re.IGNORECASE,
    ),
]


_PEDAGOGICAL_PATTERNS = [

    re.compile(r"^\s*vamos a (analizar|revisar|ver|desglosar)", re.IGNORECASE),
    re.compile(
        r"^\s*a continuación (explicamos|responderé|analizamos)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^\s*considera (lo siguiente|la siguiente pregunta)",
        re.IGNORECASE,
    ),
    re.compile(r"^\s*paso \d+:", re.IGNORECASE),
    re.compile(
        r"(siguientes|siguiente|continuación|razones|motivos|aspectos):\s*$",
        re.IGNORECASE,
    ),
]


# --- Markdown structure detection -----------------------------------------
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.*)$")
_FENCE_RE = re.compile(r"^\s*(?:```|~~~)(.*)$")
_HR_RE = re.compile(r"^\s*(?:(?:-\s*){3,}|(?:\*\s*){3,}|(?:_\s*){3,})$")
_TABLE_SEP_RE = re.compile(r"^\s*\|?[\s:|-]*-{3,}[\s:|-]*\|?\s*$")
_ORDINAL_PREFIX_RE = re.compile(r"^\d+[.)]\s+")


# --- Finite-verb (assertion) detection ------------------------------------
# Curated verb *stems* conjugated with finite (indicative/subjunctive) endings.
# Participles (ado/ido), gerunds (ando/iendo) and infinitives (ar/er/ir) are
# deliberately excluded: a heading such as "Tareas por realizar" or a comment
# such as "TODO: COMPLETAR LÓGICA" must stay STRUCTURAL.
_VERB_STEMS = (
    "asign|desaloj|ejecut|interrump|permit|requer|contien|tien|ten|almacen|"
    "represent|defin|describ|garantiz|preven|evit|provoc|caus|gener|produc|"
    "ocur|occurr|suced|exist|depend|pertenec|correspond|aument|reduc|mejor|"
    "optimiz|acced|escrib|modific|cre|destru|liber|reserv|bloque|esper|expir|"
    "comunic|sincroniz|sincron|compet|colaps|utiliz|us|emple|funcion|oper|"
    "devolv|administr|gestion|planific|coordin|calcul|compar|"
    "seleccion|elimin|insert|extra|recuper|valid|verific|autentic|cifr|descifr|"
    "proces|transfer|multiplex|intercal|prioriz|aloj|ubic|muestr|mostr|indica|"
    "señal|manip|declar|invoc|llam|aplic|convert|transform|solicit|necesit|"
    "impuls|arrastr|condicion|afect|impact|restring|limit|resolv|resuelv|cambi|"
    "control|analiz|explic|soport|model|compil|distribuy|empaquet|encapsul|"
    "implement|inicializ|finaliz|traduc|envi|recib|abstra|"
    "simplific|reutiliz|deleg|garant|habilit|deshabilit|consum|proporcion"
)
_FINITE_SUFFIX = (
    "aron|ieron|aban|ían|arán|erán|irán|aría|ería|iría|"
    "aba|ía|ará|erá|irá|aste|iste|emos|amos|"
    "an|en|as|es|ió|ó|a|e"
)
_FINITE_VERB_RE = re.compile(
    rf"\b(?:{_VERB_STEMS})(?:{_FINITE_SUFFIX})\b",
    re.IGNORECASE,
)

# Copulas and existential verbs (irregular forms) count as finite predicates.
_COPULA_TOKENS = frozenset(
    {
        "es",
        "son",
        "era",
        "eran",
        "fue",
        "fueron",
        "sera",
        "seran",
        "será",
        "serán",
        "esta",
        "estan",
        "está",
        "están",
        "estaba",
        "estaban",
        "estuvo",
        "estuvieron",
        "hay",
        "habia",
        "habian",
        "había",
        "habían",
        "tiene",
        "tienen",
        "existe",
        "existen",
    }
)

_TOKEN_RE = re.compile(r"[0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ_]+")

# Nominal assertions: a heading or bullet without a finite verb can still state
# a knowledge claim ("Mayor eficiencia", "Resultados siempre correctos",
# "Clave primaria obligatoriamente numérica").  Purely presentational labels
# ("Introducción", "Uso de memoria", "Ventajas") contain none of these
# markers.  The list is deliberately finite and conservative: it covers
# quantifiers, deontic/modal adverbs and evaluative/comparative adjectives,
# which change a noun phrase into an assertion about the world.
_ASSERTIVE_NOMINAL_TOKENS = frozenset(
    {
        # Quantifiers / absolute scope
        "siempre", "nunca", "jamas", "todos", "todas", "ningun", "ninguna",
        "ninguno", "cada", "cualquier", "cualquiera", "unicamente", "solo",
        "solamente", "exclusivamente",
        # Deontic / modal
        "obligatoriamente", "obligatorio", "obligatoria", "obligatorios",
        "obligatorias", "necesariamente", "necesario", "necesaria",
        "necesarios", "necesarias", "debe", "deben", "deberia", "deberian",
        "puede", "pueden", "podria", "podrian", "posible", "imposible",
        "requerido", "requerida", "requeridos", "requeridas", "prohibido",
        "prohibida", "permitido", "permitida",
        # Comparative / evaluative
        "mayor", "mayores", "menor", "menores", "mejor", "mejores", "peor",
        "peores", "superior", "superiores", "inferior", "inferiores",
        "optimo", "optima", "optimos", "optimas", "maximo", "maxima",
        "maximos", "maximas", "minimo", "minima", "minimos", "minimas",
        "correcto", "correcta", "correctos", "correctas", "incorrecto",
        "incorrecta", "incorrectos", "incorrectas", "falso", "falsa",
        "falsos", "falsas", "verdadero", "verdadera", "verdaderos",
        "verdaderas", "seguro", "segura", "seguros", "seguras", "inseguro",
        "insegura", "eficiente", "eficientes", "eficaz", "eficaces",
        "rapido", "rapida", "rapidos", "rapidas", "lento", "lenta", "lentos",
        "lentas", "alto", "alta", "altos", "altas", "bajo", "baja", "bajos",
        "bajas", "grande", "grandes", "pequeno", "pequena", "pequenos",
        "pequenas", "importante", "importantes", "critico", "critica",
        "criticos", "criticas", "esencial", "esenciales", "fundamental",
        "fundamentales", "vulnerable", "vulnerables", "valido", "valida",
        "validos", "validas", "invalido", "invalida", "invalidos",
        "invalidas", "probable", "probables", "improbable", "improbables",
        "peligroso", "peligrosa", "riesgoso", "riesgosa", "estable",
        "inestable", "consistente", "inconsistente", "numerico", "numerica",
        "numericos", "numericas",
    }
)

# Code punctuation: a residual line that still contains any of these is code,
# not natural-language prose, and is not treated as an assertion candidate.
_CODE_PUNCT_RE = re.compile(r"[=;(){}[\]<>:,]")

_CODE_KEYWORDS = frozenset(
    {
        "int",
        "return",
        "if",
        "else",
        "elif",
        "for",
        "while",
        "def",
        "class",
        "print",
        "const",
        "let",
        "var",
        "function",
        "void",
        "char",
        "float",
        "double",
        "true",
        "false",
        "null",
        "none",
        "import",
        "from",
        "struct",
        "enum",
        "switch",
        "case",
        "break",
        "continue",
        "try",
        "except",
        "pass",
        "lambda",
        "public",
        "private",
        "static",
        "final",
        "end",
        "begin",
    }
)

_STRING_RE = re.compile(r"(?:\"([^\"]*)\"|'([^']*)')")
_LINE_COMMENT_RE = re.compile(r"//\s*(.*)$")
_HASH_COMMENT_RE = re.compile(r"#\s*(.*)$")
_BLOCK_COMMENT_RE = re.compile(r"/\*+(.*?)\*+/")
_BLOCK_CONT_RE = re.compile(r"^\s*\*+\s*(.*)$")


def _has_finite_predicate(text: str) -> bool:
    """Return True when *text* contains a finite verb (an assertion).

    Participles, gerunds and infinitives are *not* finite verbs, so labels and
    noun phrases such as "Estado del proceso" or "Tareas por realizar" are not
    treated as assertions.
    """
    lowered = text.lower()
    for token in _TOKEN_RE.findall(lowered):
        if token in _COPULA_TOKENS:
            return True
    return bool(_FINITE_VERB_RE.search(lowered))


def _has_nominal_assertion(text: str) -> bool:
    """Return True when a verbless phrase still asserts something about the world.

    This is a finite, curated marker check (quantifiers, deontic modals and
    evaluative/comparative adjectives).  It does *not* turn every noun phrase
    into a claim: "Uso de memoria" or "Introducción" remain labels, while
    "Mayor eficiencia" or "Resultados siempre correctos" require grounding.
    """
    for token in _TOKEN_RE.findall(text.lower()):
        normalized = "".join(
            char
            for char in unicodedata.normalize("NFKD", token)
            if not unicodedata.combining(char)
        )
        if normalized in _ASSERTIVE_NOMINAL_TOKENS:
            return True
    return False


def _is_evidence_meta_statement(text: str) -> bool:
    """Return True for a statement about the absence/insufficiency of evidence.

    This is an abstention/meta-claim ("the provided evidence does not mention
    X"), not an academic fact.  A contrastive or consequential continuation is
    never exempt, because it can smuggle an unsupported world claim after the
    disclaimer.
    """
    if re.search(
        r"\b(pero|sin embargo|no obstante|aunque|por lo tanto|por ende|"
        r"en consecuencia|as[ií] que|entonces|porque|ya que|puesto que|"
        r"de modo que|de manera que|lo que (?:significa|implica)|es decir)\b",
        text,
        re.IGNORECASE,
    ):
        return False
    return any(pattern.search(text) for pattern in _EVIDENCE_META_PATTERNS)


class ExtractedClaim(BaseContract):
    """Immutable segmented claim extracted from response text."""

    model_config = ConfigDict(frozen=True)

    claim_index: int = Field(
        ..., ge=0, description="Sequential index of claim"
    )
    claim_text: str = Field(
        ..., min_length=1, description="Claim sentence text"
    )
    claim_type: ClaimType = Field(..., description="Structural classification")
    cited_tags: Tuple[str, ...] = Field(
        default_factory=tuple,
        description="Evidence tags [E#] cited in this sentence",
    )


class ClaimExtractor:
    """Deterministic extractor segmenting text and extracting claim-cites.

    The extractor is markdown-aware: it distinguishes purely presentational
    elements (``STRUCTURAL``) from knowledge-communicating claims (``FACTUAL``
    and friends).  Structural elements are not claims.
    """

    def extract_claims(self, text: str) -> Tuple[ExtractedClaim, ...]:
        """Segment text into claims and extract citations and claim types."""
        cleaned = text.strip()
        if not cleaned:
            return ()

        segments = self._split_with_roles(cleaned)
        claims: List[ExtractedClaim] = []

        for role, raw_segment in segments:
            segment = raw_segment.strip()
            if not segment:
                continue
            if role == "code":
                content = self._code_assertion(segment)
                if content is None:
                    claims.append(
                        ExtractedClaim(
                            claim_index=len(claims),
                            claim_text=segment,
                            claim_type=ClaimType.STRUCTURAL,
                            cited_tags=(),
                        )
                    )
                    continue
            else:
                content = self._segment_content(role, segment)
                if not content:
                    continue

            cited_tags = self._extract_citations(content)
            claim_type = self._classify_claim_type(content, role, cited_tags)

            claims.append(
                ExtractedClaim(
                    claim_index=len(claims),
                    claim_text=content,
                    claim_type=claim_type,
                    cited_tags=cited_tags,
                )
            )

        return tuple(claims)

    # -- structure ---------------------------------------------------------
    def _split_with_roles(self, text: str) -> List[Tuple[str, str]]:
        """Split *text* into ``(role, segment)`` pairs.

        Roles: ``fence``, ``code``, ``heading``, ``list_item``, ``structural``
        and ``prose``.
        """
        segments: List[Tuple[str, str]] = []
        in_fence = False

        for raw_line in text.split("\n"):
            line = raw_line.rstrip()
            fence_match = _FENCE_RE.match(line)

            if in_fence:
                if fence_match:
                    in_fence = False
                    segments.append(("structural", line.strip()))
                else:
                    segments.append(("code", line))
                continue

            if fence_match:
                in_fence = True
                segments.append(("fence", line.strip()))
                continue

            stripped = line.strip()
            if not stripped:
                continue
            if _HR_RE.match(stripped) or _TABLE_SEP_RE.match(stripped):
                segments.append(("structural", stripped))
                continue
            if _HEADING_RE.match(stripped):
                segments.append(("heading", stripped))
                continue
            if _LIST_ITEM_RE.match(stripped):
                segments.append(("list_item", stripped))
                continue

            for sentence in self._split_sentences(stripped):
                if sentence:
                    segments.append(("prose", sentence))

        return segments

    def _segment_content(self, role: str, segment: str) -> str:
        """Strip presentational markers from a structural segment."""
        if role == "heading":
            match = _HEADING_RE.match(segment)
            content = match.group(2) if match else segment
        elif role == "list_item":
            match = _LIST_ITEM_RE.match(segment)
            content = match.group(1) if match else segment
        else:
            content = segment
        content = _ORDINAL_PREFIX_RE.sub("", content).strip()
        return content

    def _code_assertion(self, line: str) -> Optional[str]:
        """Return the natural-language assertion inside a code line, if any.

        Only comments and string literals are scanned (code punctuation such as
        ``=``, ``;`` or ``()`` is never natural-language prose).  A candidate
        must contain a finite verb or a citation tag to be an assertion, so
        directives like ``#include``, keywords like ``return`` or TODO markers
        stay STRUCTURAL.
        """
        candidates: List[str] = []

        without_strings = line
        for match in _STRING_RE.finditer(line):
            literal = match.group(1) or match.group(2) or ""
            if literal.strip():
                candidates.append(literal.strip())
            without_strings = without_strings.replace(match.group(0), " ")

        block = _BLOCK_COMMENT_RE.search(without_strings)
        if block:
            candidates.append(block.group(1).strip())
            without_strings = _BLOCK_COMMENT_RE.sub(" ", without_strings)
        elif line.lstrip().startswith("*"):
            cont = _BLOCK_CONT_RE.match(line)
            if cont:
                candidates.append(cont.group(1).strip())

        comment = _LINE_COMMENT_RE.search(without_strings)
        if comment:
            candidates.append(comment.group(1).strip())
            without_strings = _LINE_COMMENT_RE.sub(" ", without_strings)

        if without_strings.lstrip().startswith("#"):
            hash_comment = _HASH_COMMENT_RE.search(without_strings)
            if hash_comment and not without_strings.lstrip().startswith(
                ("#include", "#define", "#pragma", "#if", "#endif", "#else",
                 "#elif", "#ifdef", "#ifndef")
            ):
                candidates.append(hash_comment.group(1).strip())

        # Residual natural-language line inside a fence (no code punctuation).
        residual = without_strings
        residual = _LINE_COMMENT_RE.sub(" ", residual)
        residual = _HASH_COMMENT_RE.sub(" ", residual)
        if not _CODE_PUNCT_RE.search(residual):
            tokens = [
                t for t in _TOKEN_RE.findall(residual)
                if t.isalpha() and len(t) >= 2 and t.lower() not in _CODE_KEYWORDS
            ]
            if len(tokens) >= 3:
                candidates.append(" ".join(tokens))

        for candidate in candidates:
            words = [w for w in _TOKEN_RE.findall(candidate) if w.isalpha()]
            if self._extract_citations(candidate):
                return candidate
            # Keep the pre-existing finite-predicate threshold for code
            # comments (>= 4 words) and add a slightly higher threshold for
            # verbless nominal assertions, so short labels such as
            # "// Mejor esfuerzo" do not become academic claims.
            if len(words) >= 4 and _has_finite_predicate(candidate):
                return candidate
            if len(words) >= 3 and _has_nominal_assertion(candidate):
                return candidate
        return None

    # -- segmentation ------------------------------------------------------
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences preserving technical symbols/numbers."""
        # Normalize double newlines as sentence breaks
        normalized = re.sub(r"\n+", "\n", text)
        # Split on sentence terminals followed by space/newline, or on newlines
        # Lookbehind for terminal punctuation (. ? ! :) or newline,
        # ignoring numbered lists (e.g. 1.)
        splits = re.split(r"(?<!\d\.)(?<=[.?!;])\s+|\n+", normalized)
        # Filter out empty or whitespace segments
        return [s.strip() for s in splits if s.strip()]

    def _extract_citations(self, text: str) -> Tuple[str, ...]:
        """Extract [E#] citations preserving first-seen lexical order."""
        seen = set()
        cites = []
        for block in re.finditer(r"\[([^\]]+)\]", text):
            for match in re.finditer(r"\b(E[0-9]+)\b", block.group(1)):
                tag = match.group(1)
                if tag not in seen:
                    seen.add(tag)
                    cites.append(tag)
        return tuple(cites)

    def _classify_claim_type(
        self,
        text: str,
        role: str = "prose",
        cited_tags: Tuple[str, ...] = (),
    ) -> ClaimType:
        """Classify claim structurally into ClaimType."""
        # 1. Check if question
        if "?" in text or "¿" in text:
            return ClaimType.QUESTION

        # 2. Check conversational phrases
        for pattern in _CONVERSATIONAL_PATTERNS:
            if pattern.search(text):
                return ClaimType.CONVERSATIONAL

        # 2b. Evidence-insufficiency statements are abstention meta-claims.
        if _is_evidence_meta_statement(text):
            return ClaimType.CONVERSATIONAL

        # 3. Check pedagogical framing
        for pattern in _PEDAGOGICAL_PATTERNS:
            if pattern.search(text):
                return ClaimType.PEDAGOGICAL

        # 4. Check colon lead-in framing (introduces subsequent explanation)
        if text.rstrip().endswith(":"):
            return ClaimType.PEDAGOGICAL

        # 5. Structural roles are claims only when they assert something
        if role in ("fence", "structural"):
            return ClaimType.STRUCTURAL
        if role in ("heading", "list_item"):
            if (
                cited_tags
                or _has_finite_predicate(text)
                or _has_nominal_assertion(text)
            ):
                return ClaimType.FACTUAL
            return ClaimType.STRUCTURAL

        # 6. Code assertions reached this point already carry a predicate or a
        #    citation; a citation is enough to require grounding.
        if role == "code":
            return ClaimType.FACTUAL

        # 7. Prose: a substantive sentence (>= 2 words) is a factual claim.
        words = [w for w in re.split(r"\s+", text) if len(w) > 1]
        if len(words) >= 2:
            return ClaimType.FACTUAL

        return ClaimType.UNCLASSIFIED
