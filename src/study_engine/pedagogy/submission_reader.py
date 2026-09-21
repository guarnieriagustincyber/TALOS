"""Deterministic Markdown submission reader for local student exercises (VSCode + TALOS).

Parses structured Markdown submission files according to the universal exercise template.
100% deterministic parsing using regex and Markdown AST/section splitting (0 LLM invocations).
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Union


@dataclass
class StudentSubmission:
    """Structured representation of a local student exercise submission parsed from Markdown."""

    exercise_id: str
    title: str
    file_path: str
    sections: Dict[str, str] = field(default_factory=dict)
    code_blocks: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_section(self, name: str, default: str = "") -> str:
        """Retrieve cleaned content of a section by name (case and whitespace-insensitive)."""
        norm = self._normalize_key(name)
        return self.sections.get(norm, default)

    def has_section(self, name: str) -> bool:
        norm = self._normalize_key(name)
        return norm in self.sections and len(self.sections[norm].strip()) > 0

    def get_code_block(self, lang: str = "python", index: int = 0, default: str = "") -> str:
        """Retrieve code block text by language specifier."""
        lang_key = lang.lower().strip()
        blocks = self.code_blocks.get(lang_key, [])
        if 0 <= index < len(blocks):
            return blocks[index]
        return default

    @staticmethod
    def _normalize_key(name: str) -> str:
        # Lowercase, remove accents, replace spaces/hyphens with underscore
        s = name.lower().strip()
        s = s.replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
        s = re.sub(r"[^\w\s]", "", s)
        s = re.sub(r"\s+", "_", s)
        return s


class SubmissionReader:
    """Parses local student markdown submissions into structured StudentSubmission objects."""

    KNOWN_SECTIONS = [
        "Enunciado",
        "Contrato Formal",
        "Diagrama de Flujo",
        "Diagrama de Estados",
        "Pseudocódigo",
        "Código Python",
        "Tests",
        "Fórmulas",
        "Cálculos",
        "Tesis Central",
        "Argumentos",
        "Crítica y Contrapunto",
        "Conclusión",
        "Citas",
        "Análisis Crítico",
        "Análisis",
        "Resultado",
    ]

    def parse(self, file_path: Union[str, Path]) -> StudentSubmission:
        """Read and parse a student markdown file."""
        path = Path(file_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Submission file not found at: {path}")

        raw_content = path.read_text(encoding="utf-8")
        exercise_id = path.stem

        # Extract title from # Header
        title = exercise_id
        title_match = re.search(r"^#\s+(?:Ejercicio:\s*)?(.+)$", raw_content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()

        # Extract sections bounded by ## Section Name
        sections: Dict[str, str] = {}
        section_pattern = re.compile(r"^##\s+([^\n]+)\n(.*?)(?=(?:^##\s+[^\n]+)|\Z)", re.MULTILINE | re.DOTALL)
        for match in section_pattern.finditer(raw_content):
            sec_header = match.group(1).strip()
            sec_body = match.group(2).strip()
            norm_key = StudentSubmission._normalize_key(sec_header)
            sections[norm_key] = sec_body

        # Extract code blocks
        code_blocks: Dict[str, List[str]] = {}
        code_block_pattern = re.compile(r"```([a-zA-Z0-9_-]*)\n(.*?)```", re.DOTALL)
        for match in code_block_pattern.finditer(raw_content):
            lang = match.group(1).strip().lower() or "text"
            block = match.group(2).strip()
            if lang not in code_blocks:
                code_blocks[lang] = []
            code_blocks[lang].append(block)

        # Extract embedded metadata comments <!-- metadata: {...} -->
        meta_match = re.search(r"<!--\s*metadata:\s*(\{.*?\})\s*-->", raw_content, re.DOTALL)
        embedded_meta = {}
        if meta_match:
            try:
                import json
                embedded_meta = json.loads(meta_match.group(1))
            except Exception:
                pass

        nb_id = embedded_meta.get("notebook_id") or self._infer_notebook_id(path)
        metadata = {
            "exercise_id": exercise_id,
            "title": title,
            "filename": path.name,
            "parent_folder": path.parent.name,
            "notebook_id": nb_id,
            "size_bytes": path.stat().st_size,
        }
        metadata.update(embedded_meta)
        if "kc_id" not in metadata:
            metadata["kc_id"] = self._infer_kc_id(path, nb_id)

        return StudentSubmission(
            exercise_id=exercise_id,
            title=title,
            file_path=str(path),
            sections=sections,
            code_blocks=code_blocks,
            metadata=metadata,
        )

    @staticmethod
    def _infer_notebook_id(path: Path) -> str:
        """Infer notebook context from folder hierarchy e.g. data/student_submissions/{notebook_id}/..."""
        parts = path.parts
        if "student_submissions" in parts:
            idx = parts.index("student_submissions")
            if idx + 1 < len(parts):
                return parts[idx + 1]
        return "fase0-soc"

    @staticmethod
    def _infer_kc_id(path: Path, notebook_id: str) -> str:
        """Infer canonical Knowledge Component ID from folder naming."""
        parent = path.parent.name.lower()
        if "fase0" in notebook_id:
            if "tramo1" in parent:
                return "fase0_tramo1_metodologia"
            elif "tramo2" in parent:
                return "fase0_tramo2_logica_control"
            elif "tramo3" in parent:
                return "fase0_tramo3_modularidad_memoria"
            elif "tramo4" in parent:
                return "fase0_tramo4_estructuras_lineales"
            elif "tramo5" in parent:
                return "fase0_tramo5_aritmetica_punteros"
        return path.stem
