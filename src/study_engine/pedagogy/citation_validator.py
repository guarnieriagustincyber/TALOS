"""Post-generation citation validator for pedagogical responses (Fase 2).

Verifica que cada referencia [E#] que el LLM escribe en la respuesta
corresponda a un chunk real del context_pack. Las referencias inventadas
(alucinadas) se reemplazan por '[ref. no verificada]' para no comprometer
la integridad epistémica del tutor.

Invariantes:
- Solo opera sobre texto ya generado (post-generación).
- No llama a ningún LLM ni API externa.
- Idempotente: si no hay citas inválidas, retorna el texto original intacto.
- Falla silenciosamente: si ocurre algún error, retorna el texto original.
"""

from __future__ import annotations

import logging
import re
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# Patrón de bloques de citas (soporta individuales [E1] y múltiples [E# 2292, E# 2293])
_CITATION_BLOCK_RE = re.compile(r"\[[ \t]*[Ee][^\]]*\]")
_ITEM_RE = re.compile(r"[Ee][ \t]*#?[ \t]*(\d*)")
_PREFIX_RE = re.compile(r"^\[(?:[ \t]*[Ee][ \t]*#?[ \t]*\d*[ \t]*[,;]?[ \t]*)*$")

# Texto de reemplazo para citas alucinadas
_INVALID_REPLACEMENT = "[ref. no verificada]"


def is_citation_prefix(buf: str) -> bool:
    """Determina si un buffer parcial puede ser el inicio de una cita válida."""
    if not buf.startswith("[") or "]" in buf or "\n" in buf or len(buf) > 64:
        return False
    return bool(_PREFIX_RE.match(buf))


class StreamCitationBuffer:
    """Lookahead buffer para validación y reescritura de citas en streaming progresivo."""

    def __init__(self, validator: CitationValidator, raw_chunks: List[Dict]) -> None:
        self.validator = validator
        self.raw_chunks = raw_chunks
        self.buf = ""
        self.in_code_fence = False

    def process_token(self, token: str) -> List[str]:
        """Procesa un token entrante del LLM emitiendo fragmentos resueltos."""
        emitted: List[str] = []
        if "```" in token:
            if token.count("```") % 2 == 1:
                self.in_code_fence = not self.in_code_fence
            if self.buf:
                emitted.append(self.buf)
                self.buf = ""
            emitted.append(token)
            return emitted

        if self.in_code_fence:
            if self.buf:
                emitted.append(self.buf)
                self.buf = ""
            emitted.append(token)
            return emitted

        incoming = self.buf + token
        self.buf = ""

        idx = 0
        while idx < len(incoming):
            bracket_pos = incoming.find("[", idx)
            if bracket_pos == -1:
                emitted.append(incoming[idx:])
                break

            if bracket_pos > idx:
                emitted.append(incoming[idx:bracket_pos])
                idx = bracket_pos

            close_pos = incoming.find("]", bracket_pos)
            if close_pos != -1:
                candidate = incoming[bracket_pos : close_pos + 1]
                corrected, _ = self.validator.validate_and_rewrite(candidate, self.raw_chunks)
                emitted.append(corrected)
                idx = close_pos + 1
            else:
                tail = incoming[bracket_pos:]
                if is_citation_prefix(tail):
                    self.buf = tail
                    break
                else:
                    emitted.append(incoming[bracket_pos : bracket_pos + 1])
                    idx = bracket_pos + 1

        return emitted

    def flush(self) -> List[str]:
        """Vacía el buffer retenido al completarse la fase."""
        emitted: List[str] = []
        if self.buf:
            emitted.append(self.buf)
            self.buf = ""
        return emitted


class CitationValidator:
    """Validador y rewriter de citas [E#] post-generación y streaming.

    Uso::

        validator = CitationValidator()
        corrected_text, invalid = validator.validate_and_rewrite(
            text=llm_output,
            chunks=raw_chunks,  # lista de dicts con key 'id': 'E1', 'E2', ...
        )
    """

    def validate_and_rewrite(
        self,
        text: str,
        chunks: List[Dict],
    ) -> Tuple[str, List[str]]:
        """Verifica y corrige referencias [E#] en el texto generado.

        Args:
            text:   Texto completo generado por el LLM.
            chunks: Lista de dicts de chunks del context_pack.
                    Cada dict tiene al menos la clave 'id' con valor 'E1', 'E2', etc.
                    También acepta clave 'citation_id'.

        Returns:
            Tuple de (texto_corregido, lista_de_citas_invalidas).
            - texto_corregido: texto con [E#] inválidos reemplazados.
            - lista_de_citas_invalidas: lista de strings como '[E5]' que no existían.
        """
        if not text:
            return text, []

        valid_indices = self._build_valid_set(chunks)
        invalid_found: List[str] = []

        def _replace_block(m: re.Match) -> str:
            content = m.group(0)[1:-1]
            parts = re.split(r"[,;]", content)
            new_parts = []
            for part in parts:
                p_strip = part.strip()
                item_m = _ITEM_RE.search(p_strip)
                if not item_m:
                    new_parts.append(_INVALID_REPLACEMENT.strip("[]"))
                    continue
                digits = item_m.group(1)
                token = f"[{p_strip}]"
                if not digits.isdigit() or int(digits) < 1:
                    logger.warning("Cita malformada detectada y rechazada: %r", token)
                    if token not in invalid_found:
                        invalid_found.append(token)
                    new_parts.append(_INVALID_REPLACEMENT.strip("[]"))
                else:
                    idx = int(digits)
                    if idx in valid_indices:
                        new_parts.append(p_strip)
                    else:
                        cit_str = f"[E{idx}]"
                        if cit_str not in invalid_found:
                            invalid_found.append(cit_str)
                        new_parts.append(_INVALID_REPLACEMENT.strip("[]"))

            unique_parts = set(new_parts)
            if unique_parts == {_INVALID_REPLACEMENT.strip("[]")}:
                return _INVALID_REPLACEMENT
            return "[" + ", ".join(new_parts) + "]"

        corrected = _CITATION_BLOCK_RE.sub(_replace_block, text)
        return corrected, invalid_found

    @staticmethod
    def _build_valid_set(chunks: List[Dict]) -> set:
        """Extrae el set de índices enteros válidos desde la lista de chunks."""
        valid: set = set()
        for chunk in chunks:
            raw_id = chunk.get("id") or chunk.get("citation_id") or ""
            m = re.fullmatch(r"E(\d+)", str(raw_id).strip())
            if m:
                valid.add(int(m.group(1)))
        return valid

    def audit_only(
        self,
        text: str,
        chunks: List[Dict],
    ) -> Tuple[List[str], List[str]]:
        """Solo audita sin reescribir. Retorna (citas_validas, citas_invalidas)."""
        if not text:
            return [], []
        valid_indices = self._build_valid_set(chunks)

        found_valid: List[str] = []
        found_invalid: List[str] = []
        for m in _CITATION_BLOCK_RE.finditer(text):
            content = m.group(0)[1:-1]
            parts = re.split(r"[,;]", content)
            for part in parts:
                p_strip = part.strip()
                item_m = _ITEM_RE.search(p_strip)
                if not item_m:
                    continue
                digits = item_m.group(1)
                token = f"[{p_strip}]"
                if not digits.isdigit() or int(digits) < 1:
                    logger.warning("Cita malformada detectada en auditoría: %r", token)
                    if token not in found_invalid:
                        found_invalid.append(token)
                    continue
                idx = int(digits)
                citation_str = f"[E{idx}]"
                if idx in valid_indices:
                    if citation_str not in found_valid:
                        found_valid.append(citation_str)
                else:
                    if citation_str not in found_invalid:
                        found_invalid.append(citation_str)

        return found_valid, found_invalid

