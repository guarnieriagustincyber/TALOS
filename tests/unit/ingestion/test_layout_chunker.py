"""Unit and contract tests for Layout-Aware Extractor and Hierarchical Semantic Chunker.

Validates:
- Preservation of Markdown tables (e.g. process scheduling tables)
- FormulaDetector protection of Big O, summations, and propositional logic
- Hierarchical section boundaries and section_path metadata
- Tesseract tessdata resolution
"""

import pytest
from study_engine.contracts.document import Document
from study_engine.ingestion.chunking import (
    ChunkConfig,
    HierarchicalSemanticChunker,
    chunk_document,
    chunk_document_hierarchical,
)
from study_engine.ingestion.converters.layout_adapter import FormulaDetector, LayoutAwareConverterAdapter
from study_engine.ingestion.converters.tesseract_fallback import (
    TESSDATA_PATHS,
    check_tesseract_availability,
    find_tessdata,
)


def test_formula_detector_patterns():
    detector = FormulaDetector()

    # Big O notation
    assert detector.has_formula("El tiempo de ejecución de MergeSort es O(n log n) en el peor caso.")
    assert "O(n log n)" in detector.extract_formulas("MergeSort es O(n log n)")
    assert detector.has_formula("La complejidad espacial es O(n^2)")

    # Mathematical symbols
    assert detector.has_formula("La suma total ∑ de los elementos verifica que i ≤ n.")
    assert detector.has_formula("Para todo elemento x ∈ S se cumple x ≥ 0.")

    # Propositional logic
    assert detector.has_formula("Dadas las proposiciones p → q y ¬p ∧ q.")

    # Plain text without formulas
    assert not detector.has_formula("Este es un texto explicativo normal sobre computación.")


def test_hierarchical_chunker_preserves_tables_intact():
    table_markdown = (
        "| Proceso | Tiempo de Llegada | Ráfaga CPU | Prioridad |\n"
        "| :--- | :--- | :--- | :--- |\n"
        "| P1 | 0 | 8 | 1 |\n"
        "| P2 | 1 | 4 | 2 |\n"
        "| P3 | 2 | 9 | 1 |\n"
        "| P4 | 3 | 5 | 3 |"
    )

    doc_content = f"# Capítulo 3: Planificación de CPU\n\n## 3.2 Tabla de Procesos\n\nA continuación se detallan los procesos:\n\n{table_markdown}\n\nEl algoritmo asignará turnos según el quantum."

    doc = Document(
        id="doc_sched_01",
        source_id="tanenbaum_so",
        title="Planificación de CPU",
        content=doc_content,
        metadata={"chapter": "Capítulo 3"},
    )

    config = ChunkConfig(chunk_size=1200, chunk_overlap=100)
    chunker = HierarchicalSemanticChunker(config)
    chunks = chunker.chunk(doc)

    assert len(chunks) >= 1
    # Verify table is present in full without row fragmentation
    table_chunk = next((c for c in chunks if c.metadata.get("has_table")), None)
    assert table_chunk is not None
    assert "| P1 | 0 | 8 | 1 |" in table_chunk.content
    assert "| P4 | 3 | 5 | 3 |" in table_chunk.content
    assert table_chunk.metadata["section_path"] is not None
    assert "Capítulo 3" in table_chunk.metadata["section_path"]


def test_hierarchical_chunker_preserves_code_and_formulas():
    code_block = (
        "```c\n"
        "int main() {\n"
        "    pid_t pid = fork();\n"
        "    if (pid == 0) {\n"
        "        printf(\"Hijo\\n\");\n"
        "    }\n"
        "    return 0;\n"
        "}\n"
        "```"
    )
    formula_line = "La recurrencia del algoritmo es T(n) = 2T(n/2) + O(n), lo que demuestra O(n log n)."

    doc_content = f"# Algoritmos de Sistemas\n\n## Syscall Fork\n\nCódigo de ejemplo:\n\n{code_block}\n\n## Análisis de Complejidad\n\n{formula_line}"

    doc = Document(
        id="doc_code_01",
        source_id="stallings_os",
        title="Fork y Complejidad",
        content=doc_content,
    )

    chunks = chunk_document_hierarchical(doc, ChunkConfig(chunk_size=1000))
    assert len(chunks) >= 1

    code_chunk = next((c for c in chunks if c.metadata.get("has_code")), None)
    assert code_chunk is not None
    assert "pid_t pid = fork();" in code_chunk.content

    formula_chunk = next((c for c in chunks if c.metadata.get("has_formula")), None)
    assert formula_chunk is not None
    assert "O(n log n)" in formula_chunk.content


def test_hierarchical_chunker_section_path_metadata():
    doc_content = (
        "# Sistemas Operativos\n\n"
        "Introducción al hardware y software.\n\n"
        "## Gestión de Memoria\n\n"
        "La memoria virtual permite extender la memoria física.\n\n"
        "### Paginación\n\n"
        "El espacio de direcciones se divide en páginas de tamaño fijo."
    )

    doc = Document(
        id="doc_mem_01",
        source_id="silberschatz_so",
        title="Memoria",
        content=doc_content,
    )

    chunks = chunk_document_hierarchical(doc, ChunkConfig(chunk_size=500))
    assert len(chunks) >= 1
    paths = [c.metadata.get("section_path") for c in chunks if c.metadata.get("section_path")]
    assert any("Sistemas Operativos" in p for p in paths)


def test_tesseract_resolution_paths():
    assert len(TESSDATA_PATHS) >= 3
    # Function must execute cleanly without exceptions
    is_avail = check_tesseract_availability()
    assert isinstance(is_avail, bool)
    found_path = find_tessdata()
    if is_avail:
        assert found_path is not None
    else:
        assert found_path is None
