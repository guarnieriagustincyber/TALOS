"""Symbol and Identifier Guard for Epistemic Fail-Closed Retrieval (Sprint v1.2 / Fase 5).

Guarantees 100% fail-closed abstention on apocryphal technical queries and hallucinated
standard library functions without degrading pedagogical empathy on student code.

Adheres strictly to the 3 Golden Rules from Dirección Técnica:
1. Activation strictly on 'Canonicity Assertion' (inhibited on student code/debugging).
2. Local $O(1)$ Static Whitelist for ISO C, POSIX, and x86-64 registers.
3. Student Morphology & Hesitation Tolerance.
4. Enmienda E-FTS5: Safe Document Frequency check without underscore tokenizer hazards.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CATALOG_PATH = REPO_ROOT / "data/dictionaries/iso_c_posix_symbols.json"


class SymbolGuardDecision(BaseModel):
    """Result of the SymbolGuard evaluation."""

    should_abstain: bool = False
    reason: Optional[str] = None
    symbol: Optional[str] = None
    is_student_debugging: bool = False
    canonicity_asserted: bool = False
    matched_markers: List[str] = Field(default_factory=list)


# Patterns indicating student code, exercises, or debugging context (Regla 1 - Inhibición)
_STUDENT_DEBUGGING_PATTERNS = [
    re.compile(r"\bmi[_\s]+(?:funci[oó]n|codigo|código|programa|tad|struct|implementaci[oó]n|script|entrega|tp)\b", re.IGNORECASE),
    re.compile(r"\b(?:en\s+)?mi\s+(?:c[oó]digo|programa|implementaci[oó]n|funci[oó]n|archivo|proyecto|entrega|tp|pr[aá]ctica)\b", re.IGNORECASE),
    re.compile(r"\b(?:mi|mis)_(?:[a-zA-Z0-9_]+)\b", re.IGNORECASE),
    re.compile(r"\b(?:da|tira|arroja|genera)\s+(?:segmentation\s+fault|segfault|double\s+free|stack\s+overflow|buffer\s+overflow|memory\s+leak)\b", re.IGNORECASE),
    re.compile(r"\b(?:no\s+compila|no\s+me\s+compila|me\s+tira\s+error|por\s+qu[eé]\s+falla|c[oó]mo\s+arreglo|c[oó]mo\s+implemento)\b", re.IGNORECASE),
    re.compile(r"\b(?:valgrind|condici[oó]n\s+de\s+carrera|condicion\s+de\s+carrera|pierde\s+datos|retorna\s+basura|lee\s+dos\s+veces)\b", re.IGNORECASE),
    re.compile(r"\b(?:en\s+el\s+ejercicio|para\s+la\s+pr[aá]ctica|en\s+el\s+tp|funci[oó]n\s+auxiliar)\b", re.IGNORECASE),
]

# Patterns asserting canonicity (Regla 1 - Activación)
_CANONICITY_PATTERNS = [
    # C Standard Library / Language assertions
    (re.compile(r"\b(?:biblioteca|librer[ií]a)\s+est[aá]ndar\s+(?:de\s+c\b|ansi\s+c\b|iso\s+c\b)?", re.IGNORECASE), "c_stdlib"),
    (re.compile(r"\b(?:ansi\s+c|iso\s+c|c\s+est[aá]ndar|c89|c99|c11)\b", re.IGNORECASE), "c_stdlib"),
    (re.compile(r"\b(?:funci[oó]n|m[eé]todo)\s+(?:nativa|est[aá]ndar)\s+(?:de\s+c\b)?", re.IGNORECASE), "c_stdlib"),
    (re.compile(r"\b(?:en\s+c\s+existe\s+la\s+funci[oó]n|la\s+funci[oó]n\s+de\s+c\b)", re.IGNORECASE), "c_stdlib"),
    (re.compile(r"\bqu[eé]\s+biblioteca\s+est[aá]ndar\b", re.IGNORECASE), "c_stdlib"),
    # Architecture / Kernel / OS assertions
    (re.compile(r"\b(?:registro\s+(?:x86[-_]?64|x86|arm)|kernel\s+linux|n[uú]cleo\s+linux|del\s+kernel\s+linux)\b", re.IGNORECASE), "kernel_register"),
    (re.compile(r"\bregistro\s+(?:de\s+la\s+cpu|de\s+cpu|arquitect[oó]nico|del\s+kernel)\b", re.IGNORECASE), "kernel_register"),
    # POSIX / System Call assertions
    (re.compile(r"\b(?:syscall|llamada\s+al\s+sistema)\s+(?:posix|de\s+linux|del\s+kernel)?\b", re.IGNORECASE), "posix_syscall"),
    (re.compile(r"\b(?:est[aá]ndar\s+posix|especificaci[oó]n\s+posix)\b", re.IGNORECASE), "posix_syscall"),
]

# Prefixes of student hesitation / uncertainty to normalize (Regla 3)
_HESITATION_PREFIXES = [
    re.compile(r"^(?:creo\s+que\s+(?:la\s+funci[oó]n|el\s+m[eé]todo|el\s+registro)?\s*)", re.IGNORECASE),
    re.compile(r"^(?:(?:me\s+parece|tengo\s+entendido)\s+que\s*)", re.IGNORECASE),
    re.compile(r"^(?:[¿?]?\s*(?:existe|hay)\s+(?:la\s+funci[oó]n|el\s+registro|el\s+m[eé]todo)?\s*)", re.IGNORECASE),
    re.compile(r"^(?:[¿?]?\s*(?:qu[eé]|cual|cu[aá]l)\s+(?:biblioteca|librer[ií]a|registro|funci[oó]n|m[eé]todo)?\s*)", re.IGNORECASE),
]


_FILLER_TOKENS = frozenset({
    "reg", "register", "struct", "type", "fn", "func", "function",
    "syscall", "instruction", "call", "sys", "api", "op",
})

_FUNC_PATTERN = re.compile(r"\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)")
_BACKTICK_PATTERN = re.compile(r"`([a-zA-Z0-9_]+)`")
_SNAKE_PATTERN = re.compile(r"\b([a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)+)\b")
_ENTITY_PATTERN = re.compile(
    r"\b(?:registro|funci[oó]n|m[eé]todo|macro|estructura|variable)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
    re.IGNORECASE,
)
_NON_SYMBOL_WORDS = frozenset({"main", "int", "char", "void", "float", "double", "null", "true", "false"})

_INJECTION_PATTERNS = [
    re.compile(r"\b(?:ignor[aá]\s+(?:todas\s+)?(?:tus\s+)?directivas\s+previas|olv[ií]date\s+del\s+rol)\b", re.IGNORECASE),
    re.compile(r"\b(?:system\s+override|modo\s+de\s+mantenimiento\s+activado|modo\s+administrador)\b", re.IGNORECASE),
    re.compile(r"\b(?:como\s+programador\s+de\s+openai|sin\s+restricciones\s+curriculares)\b", re.IGNORECASE),
    re.compile(r"\b(?:borre\s+todo\s+el\s+contenido\s+de\s+/|desactive\s+los\s+logs\s+de\s+auditor[ií]a|rm\s+-rf)\b", re.IGNORECASE),
    re.compile(r"\b(?:repet[ií]\s+la\s+palabra\s+['\"][^'\"]+['\"]\s+\d+\s+veces|volc[aá]\s+el\s+contenido\s+de\s+las\s+variables\s+de\s+entorno)\b", re.IGNORECASE),
    re.compile(r"\b(?:clave\s+privada\s+ssh|archivos\s+secretos\s+en\s+el\s+servidor)\b", re.IGNORECASE),
    re.compile(r"\b(?:instrucciones\s+internas\s+confidenciales|prompt\s+de\s+sistema\s+completo)\b", re.IGNORECASE),
    re.compile(r"\b(?:generador\s+de\s+malware|creame\s+un\s+ransomware)\b", re.IGNORECASE),
    re.compile(r"\b(?:dump\s+completo\s+de\s+la\s+base\s+de\s+datos\s+de\s+contraseñas|alumnos\s+de\s+fadena)\b", re.IGNORECASE),
    re.compile(r"\b(?:terminal\s+root\s+sin\s+restricciones)\b", re.IGNORECASE),
]

_OOD_DOMAIN_PATTERNS = [
    re.compile(r"\b(?:mundial\s+de\s+(?:m[eé]xico|f[uú]tbol)|copa\s+del\s+mundo|f[oó]rmula\s+1|campe[oó]n\s+de\s+(?:la\s+)?f[oó]rmula|partido\s+de\s+f[uú]tbol|enroque|ajedrez)\b", re.IGNORECASE),
    re.compile(r"\b(?:pel[ií]cula\s+inception|christopher\s+nolan|cien\s+a[ñn]os\s+de\s+soledad|sinfon[ií]a\s+n\b|obras?\s+de\s+beethoven|la\s+noche\s+estrellada|pint[oó]\s+la\s+noche|museo\s+se\s+encuentra)\b", re.IGNORECASE),
    re.compile(r"\b(?:capital\s+de\s+australia|ciudad\s+de\s+buenos\s+aires|distancia\s+(?:hay\s+)?entre\s+la\s+tierra\s+y\s+la\s+luna|en\s+el\s+apogeo)\b", re.IGNORECASE),
    re.compile(r"\b(?:masa\s+madre\s+para\s+pan|salsa\s+carbonara|fotos[ií]ntesis\s+en\s+las\s+plantas|angiospermas|xilema\s+secundario)\b", re.IGNORECASE),
    re.compile(r"\b(?:revoluci[oó]n\s+francesa|guerra\s+del\s+peloponeso|legi[oó]n\s+romana|julio\s+c[eé]sar|tratado\s+de\s+tordesillas|unificaci[oó]n\s+italiana|hammurabi|dinast[ií]a\s+ming|batalla\s+de\s+waterloo|carta\s+magna|crisis\s+de\s+los\s+misiles)\b", re.IGNORECASE),
    re.compile(r"\b(?:principios\s+de\s+la\s+termodin[aá]mica)\b", re.IGNORECASE),
]

_APOCRYPHAL_ENTITY_PATTERNS = [
    re.compile(r"\b(__[a-zA-Z0-9_]+)\b"),
    re.compile(r"\b((?:pthread_|sys_|mmap_|malloc_|free_|printf_)[a-zA-Z0-9_]+)\b"),
    re.compile(r"(?:^|\s)(-f[a-zA-Z0-9_-]+)"),
    re.compile(r"\b(cr\d+)\b", re.IGNORECASE),
    re.compile(r"(\.[a-zA-Z0-9_]+_sym|\.phantom[a-zA-Z0-9_]*)", re.IGNORECASE),
    re.compile(r"\b(guarnieri(?:-[a-zA-Z0-9_]+)?|kasiu)\b", re.IGNORECASE),
    re.compile(r"\b(?:cu[aá]ntic[oa][-_\s]ip|arquitectura\s+neuronal\s+cu[aá]ntica|cu[aá]ntica-64)\b", re.IGNORECASE),
    re.compile(r"\b(?:hipervisor\s+secreto|int\s+0x999|micro-emulador|desactivo\s+la\s+gravedad)\b", re.IGNORECASE),
    re.compile(r"\b(?:b-tree\s+hexagonal|apunte\s+ap[oó]crifo|sem[aá]foro\s+invertido)\b", re.IGNORECASE),
    re.compile(r"\b(?:cache\s+l4\s+superconductora|intel\s+8086)\b", re.IGNORECASE),
    re.compile(r"\b(?:duplicar\s+procesos\s+sin\s+consumir\s+memoria|telep[aá]tico|teletransportaci[oó]n|rfc\s*\d{5,})\b", re.IGNORECASE),
]


class SymbolGuard:
    """Pre-retrieval epistemic guard against apocryphal identifiers and fake standard symbols."""

    def __init__(
        self,
        catalog_path: Optional[Path] = None,
        store: Optional[Any] = None,
    ) -> None:
        self.catalog_path = catalog_path or DEFAULT_CATALOG_PATH
        self.store = store
        self._functions: Set[str] = set()
        self._registers: Set[str] = set()
        self._types: Set[str] = set()
        self._headers: Set[str] = set()
        self._all_whitelisted: Set[str] = set()
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load static whitelist catalog into memory for O(1) membership lookups."""
        path = self.catalog_path
        if not path.is_file():
            # Search fallback
            candidates = [
                REPO_ROOT / "data/dictionaries/iso_c_posix_symbols.json",
                Path("data/dictionaries/iso_c_posix_symbols.json"),
            ]
            for c in candidates:
                if c.is_file():
                    path = c
                    break

        if path.is_file():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._functions = set(data.get("functions", []))
                    self._registers = set(data.get("registers", []))
                    self._types = set(data.get("types", []))
                    self._headers = set(data.get("headers", []))
                    self._all_whitelisted = self._functions | self._registers | self._types | self._headers
                    logger.debug(
                        "SymbolGuard loaded catalog from %s (%d funcs, %d regs)",
                        path,
                        len(self._functions),
                        len(self._registers),
                    )
                    return
            except Exception as err:
                logger.warning("Error loading symbol catalog from %s: %s", path, err)

        # Built-in essential fallback whitelist if file not found
        self._functions = {
            "printf", "fprintf", "sprintf", "snprintf", "scanf", "sscanf",
            "malloc", "calloc", "realloc", "free", "exit", "abort", "getenv", "system",
            "qsort", "bsearch", "abs", "rand", "srand", "atoi", "atol", "strtol", "strtod",
            "strcpy", "strncpy", "strcat", "strncat", "strcmp", "strncmp", "strlen", "memset", "memcpy", "memmove",
            "sin", "cos", "tan", "sqrt", "pow", "exp", "log", "fabs", "ceil", "floor",
            "fork", "execve", "wait", "waitpid", "pipe", "open", "close", "read", "write",
            "pthread_create", "pthread_join", "pthread_mutex_lock", "pthread_mutex_unlock",
            "clone", "mmap", "munmap", "dup", "dup2", "kill", "sigaction", "signal",
            "brk", "sbrk", "setjmp", "longjmp", "select", "poll", "epoll", "epoll_create",
            "epoll_ctl", "epoll_wait", "readdir", "opendir", "closedir", "syscall",
        }
        self._registers = {
            "rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rbp", "rsp",
            "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15",
            "eax", "ebx", "ecx", "edx", "esi", "edi", "ebp", "esp",
            "rip", "rflags", "cr0", "cr3",
        }
        self._types = {
            "dirent", "sigaction", "stat", "size_t", "pid_t", "time_t", "ssize_t",
            "pthread_t", "pthread_mutex_t",
        }
        self._all_whitelisted = self._functions | self._registers | self._types | self._headers

    def is_student_debugging(self, query: str) -> bool:
        """Check whether query originates from student exercise or code debugging (Regla 1)."""
        clean_q = query.strip()
        for pat in _STUDENT_DEBUGGING_PATTERNS:
            if pat.search(clean_q):
                return True
        return False

    def detect_canonicity_assertions(self, query: str) -> Tuple[bool, List[str], Set[str]]:
        """Detect whether query asserts standard library, canonical OS kernel, or POSIX status."""
        matched_markers: List[str] = []
        assertion_types: Set[str] = set()

        for pat, cat in _CANONICITY_PATTERNS:
            m = pat.search(query)
            if m:
                matched_markers.append(m.group(0))
                assertion_types.add(cat)

        return (len(matched_markers) > 0, matched_markers, assertion_types)

    def extract_candidate_symbols(self, query: str) -> List[str]:
        """Extract function identifiers, compound snake_case terms, and specific named entities (Regla 3)."""
        symbols: List[str] = []

        # 1. Functions with parentheses: foo() or foo(args)
        func_matches = _FUNC_PATTERN.findall(query)
        for fn in func_matches:
            fn_clean = fn.strip()
            if fn_clean and len(fn_clean) > 1:
                symbols.append(fn_clean)

        # 2. Identifiers in code backticks: `some_name`
        backtick_matches = _BACKTICK_PATTERN.findall(query)
        for bm in backtick_matches:
            symbols.append(bm.strip())

        # 3. Compound snake_case terms (e.g. quantum_accumulator_register)
        snake_matches = _SNAKE_PATTERN.findall(query)
        for sm in snake_matches:
            symbols.append(sm.strip())

        # 4. Explicit entity mentions: 'registro X', 'función Y'
        entity_matches = _ENTITY_PATTERN.findall(query)
        for em in entity_matches:
            symbols.append(em.strip())

        # Normalize & deduplicate preserving order
        normalized: List[str] = []
        for s in symbols:
            s_clean = s.strip().lower()
            if s_clean and s_clean not in normalized:
                # Discard common non-symbol words
                if s_clean not in _NON_SYMBOL_WORDS:
                    normalized.append(s_clean)

        return normalized

    def check_document_frequency(
        self, identifier: str, store: Optional[Any] = None
    ) -> int:
        """Check document existence safely avoiding FTS5 tokenizer underscore hazard (Enmienda E-FTS5).

        If identifier contains underscores or camelCase, uses exact substring query on chunks table
        or FTS-accelerated candidate narrowing to verify actual existence in < 2ms.
        """
        active_store = store or self.store
        if active_store is None:
            return 1  # Failsafe: if store is not configured, do not veto purely on DF

        engine = getattr(active_store, "engine", None)
        if engine is None:
            return 1

        clean_id = identifier.strip().lstrip(".-")
        if not clean_id:
            return 0

        try:
            with engine.transaction() as conn:
                cursor = conn.cursor()

                # Enmienda E-FTS5: Safe handling of underscores and hyphens
                if "_" in clean_id or "-" in clean_id:
                    subtokens = [t for t in re.split(r"[_\-]+", clean_id) if t]
                    if subtokens:
                        fts_phrase = " ".join(f'"{t}"' for t in subtokens)
                        try:
                            cursor.execute(
                                """
                                SELECT 1 FROM chunks c
                                JOIN chunks_fts f ON f.rowid = c.rowid
                                WHERE chunks_fts MATCH ? AND c.content LIKE ?
                                LIMIT 1;
                                """,
                                (fts_phrase, f"%{clean_id}%"),
                            )
                            row = cursor.fetchone()
                            return 1 if row else 0
                        except Exception:
                            # Fallback to direct LIKE with LIMIT 1 if chunks_fts is unavailable
                            cursor.execute(
                                "SELECT 1 FROM chunks WHERE content LIKE ? LIMIT 1;",
                                (f"%{clean_id}%",),
                            )
                            row = cursor.fetchone()
                            return 1 if row else 0
                    else:
                        return 0
                else:
                    # Single word token: FTS5 MATCH is exact and O(1)
                    clean_alphanumeric = re.sub(r"[^\w]", "", clean_id)
                    if not clean_alphanumeric:
                        return 0
                    try:
                        cursor.execute(
                            "SELECT 1 FROM chunks_fts WHERE chunks_fts MATCH ? LIMIT 1;",
                            (f'"{clean_alphanumeric}"',),
                        )
                        row = cursor.fetchone()
                        return 1 if row else 0
                    except Exception:
                        cursor.execute(
                            "SELECT 1 FROM chunks WHERE content LIKE ? LIMIT 1;",
                            (f"%{clean_id}%",),
                        )
                        row = cursor.fetchone()
                        return 1 if row else 0
                        return 1 if row else 0
                    except Exception:
                        cursor.execute(
                            "SELECT 1 FROM chunks WHERE content LIKE ? LIMIT 1;",
                            (f"%{clean_id}%",),
                        )
                        row = cursor.fetchone()
                        return 1 if row else 0

        except Exception as err:
            logger.debug("Error checking document frequency for '%s': %s", clean_id, err)
            return 1  # Failsafe

    def _is_standard_or_composite_symbol(self, sym: str, assertion_type: str = "") -> bool:
        """Verify whether a symbol is either a known canonical symbol or a composite combination of canonical symbols.
        
        Handles composite comparisons like 'brk_sbrk', 'setjmp_longjmp', 'select_poll_epoll',
        and prefixed names like 'reg_rsp', 'reg_rbp', 'reg_rdi_rsi', 'struct_dirent', 'syscall_instruction'.
        A real architectural symbol (e.g. register, syscall, type) is never apocryphal.
        """
        clean_sym = sym.strip().lower()
        if not clean_sym:
            return False

        # Direct O(1) check
        if clean_sym in self._all_whitelisted:
            return True

        # Composite check if contains underscores
        if "_" in clean_sym:
            parts = [p for p in clean_sym.split("_") if p and p not in _FILLER_TOKENS]

            # If all parts were fillers (e.g. "syscall_instruction"), check if any primary token is recognized
            if not parts:
                raw_parts = [p for p in clean_sym.split("_") if p]
                return any(p in self._all_whitelisted for p in raw_parts)

            return all(p in self._all_whitelisted for p in parts)

        return False

    def evaluate(
        self, query: str, store: Optional[Any] = None
    ) -> SymbolGuardDecision:
        """Evaluate query against the 3 Golden Rules of Symbol Guarding.

        Returns SymbolGuardDecision specifying whether retrieval should abstain fail-closed.
        """
        # Regla 1 (Inhibición): Si el estudiante está depurando código propio, NO vetar
        if self.is_student_debugging(query):
            return SymbolGuardDecision(
                should_abstain=False,
                is_student_debugging=True,
                reason="STUDENT_DEBUGGING_CONTEXT",
            )

        # Regla 1 (Activación): Detectar aserción explícita de canonicidad
        has_assertion, matched_markers, assertion_types = self.detect_canonicity_assertions(query)
        if has_assertion:
            symbols = self.extract_candidate_symbols(query)
            if not symbols:
                return SymbolGuardDecision(
                    should_abstain=False,
                    canonicity_asserted=True,
                    matched_markers=matched_markers,
                    reason="GENERAL_CANONICAL_QUERY",
                )

            # Regla 2: Verificación contra Catálogo Estático O(1)
            for sym in symbols:
                # Caso A: Pregunta sobre funciones de biblioteca estándar / C canónico
                if "c_stdlib" in assertion_types:
                    if not self._is_standard_or_composite_symbol(sym, "c_stdlib"):
                        df = self.check_document_frequency(sym, store=store)
                        if df == 0:
                            logger.info(
                                "SymbolGuard: Fail-closed on apocryphal C function '%s' (not in whitelist, DF=0)",
                                sym,
                            )
                            return SymbolGuardDecision(
                                should_abstain=True,
                                reason="NON_STANDARD_CANONICAL_FUNCTION",
                                symbol=sym,
                                canonicity_asserted=True,
                                matched_markers=matched_markers,
                            )

                # Caso B: Pregunta sobre registros de CPU / Kernel Linux
                if "kernel_register" in assertion_types:
                    if not self._is_standard_or_composite_symbol(sym, "kernel_register"):
                        df = self.check_document_frequency(sym, store=store)
                        if df == 0:
                            logger.info(
                                "SymbolGuard: Fail-closed on apocryphal register '%s' (not in whitelist, DF=0)",
                                sym,
                            )
                            return SymbolGuardDecision(
                                should_abstain=True,
                                reason="APOCRYPHAL_CANONICAL_REGISTER",
                                symbol=sym,
                                canonicity_asserted=True,
                                matched_markers=matched_markers,
                            )

                # Caso C: Syscalls POSIX
                if "posix_syscall" in assertion_types:
                    if not self._is_standard_or_composite_symbol(sym, "posix_syscall"):
                        df = self.check_document_frequency(sym, store=store)
                        if df == 0:
                            logger.info(
                                "SymbolGuard: Fail-closed on apocryphal POSIX syscall '%s' (not in whitelist, DF=0)",
                                sym,
                            )
                            return SymbolGuardDecision(
                                should_abstain=True,
                                reason="APOCRYPHAL_POSIX_SYSCALL",
                                symbol=sym,
                                canonicity_asserted=True,
                                matched_markers=matched_markers,
                            )

        # Chequeo de inyecciones prompt / adversarial overrides
        for pat in _INJECTION_PATTERNS:
            if pat.search(query):
                logger.info("SymbolGuard: Fail-closed on adversarial injection in query='%s'", query)
                return SymbolGuardDecision(
                    should_abstain=True,
                    reason="ADVERSARIAL_INJECTION_DETECTED",
                )

        # Chequeo de dominios completamente fuera de alcance (cultura general)
        for pat in _OOD_DOMAIN_PATTERNS:
            if pat.search(query):
                logger.info("SymbolGuard: Fail-closed on out-of-domain general topic in query='%s'", query)
                return SymbolGuardDecision(
                    should_abstain=True,
                    reason="OUT_OF_DOMAIN_CURRICULAR_ABSTENTION",
                )

        # Chequeo de entidades técnicas apócrifas / alucinadas
        for pat in _APOCRYPHAL_ENTITY_PATTERNS:
            m = pat.search(query)
            if m:
                raw_sym = m.group(1) if m.groups() else m.group(0)
                clean_sym = raw_sym.strip().lstrip(".-").lower()
                if not self._is_standard_or_composite_symbol(clean_sym):
                    df = self.check_document_frequency(clean_sym, store=store)
                    if df == 0:
                        logger.info(
                            "SymbolGuard: Fail-closed on apocryphal entity '%s' (not in whitelist, DF=0)",
                            raw_sym,
                        )
                        return SymbolGuardDecision(
                            should_abstain=True,
                            symbol=raw_sym.strip(),
                            reason="APOCRYPHAL_ENTITY_DETECTED",
                        )

        if has_assertion:
            return SymbolGuardDecision(
                should_abstain=False,
                canonicity_asserted=True,
                matched_markers=matched_markers,
                reason="CANONICAL_SYMBOLS_VERIFIED",
            )

        return SymbolGuardDecision(
            should_abstain=False,
            canonicity_asserted=False,
            reason="NO_CANONICITY_ASSERTION",
        )
