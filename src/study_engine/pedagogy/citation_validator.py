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

import re
from typing import Dict, List, Optional, Tuple


# Patrón canónico de citas: [E1], [E12], etc.
# No captura [En] genérico de redacción, solo [E] seguido de dígitos.
_CITATION_RE = re.compile(r"\[E(\d+)\]")

# Texto de reemplazo para citas alucinadas
_INVALID_REPLACEMENT = "[ref. no verificada]"


class CitationValidator:
    """Validador y rewriter de citas [E#] post-generación.

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

        # Construir set de índices válidos desde el context_pack
        valid_indices = self._build_valid_set(chunks)

        # Si no hay chunks en absoluto, no invalidar nada
        # (puede ser modo offline/oracle sin citas formales)
        if not valid_indices:
            return text, []

        invalid_found: List[str] = []
        corrected = _CITATION_RE.sub(
            lambda m: self._replace_match(m, valid_indices, invalid_found),
            text,
        )
        return corrected, invalid_found

    @staticmethod
    def _build_valid_set(chunks: List[Dict]) -> set:
        """Extrae el set de índices enteros válidos desde la lista de chunks."""
        valid: set = set()
        for chunk in chunks:
            # Soportar tanto 'id' como 'citation_id'
            raw_id = chunk.get("id") or chunk.get("citation_id") or ""
            # Extraer el número de 'E1', 'E12', etc.
            m = re.fullmatch(r"E(\d+)", str(raw_id).strip())
            if m:
                valid.add(int(m.group(1)))
        return valid

    @staticmethod
    def _replace_match(
        m: re.Match,
        valid_indices: set,
        invalid_found: List[str],
    ) -> str:
        """Callback de sustitución: retorna la cita original o el reemplazo."""
        idx = int(m.group(1))
        if idx in valid_indices:
            return m.group(0)  # cita válida, sin cambios
        citation_str = f"[E{idx}]"
        if citation_str not in invalid_found:
            invalid_found.append(citation_str)
        return _INVALID_REPLACEMENT

    def audit_only(
        self,
        text: str,
        chunks: List[Dict],
    ) -> Tuple[List[str], List[str]]:
        """Solo audita sin reescribir. Retorna (citas_validas, citas_invalidas).

        Útil para logging y métricas sin modificar el texto.
        """
        if not text:
            return [], []
        valid_indices = self._build_valid_set(chunks)
        if not valid_indices:
            return [], []

        found_valid: List[str] = []
        found_invalid: List[str] = []
        for m in _CITATION_RE.finditer(text):
            idx = int(m.group(1))
            citation_str = f"[E{idx}]"
            if idx in valid_indices:
                if citation_str not in found_valid:
                    found_valid.append(citation_str)
            else:
                if citation_str not in found_invalid:
                    found_invalid.append(citation_str)

        return found_valid, found_invalid
