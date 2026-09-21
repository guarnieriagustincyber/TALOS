"""CI Test: Verificar que src/study_engine/student/ no importa LLMs.

Regla de oro: El LLM nunca decide mastery.
"""

import ast
from pathlib import Path
from typing import Set


def get_imports(file_path: Path) -> Set[str]:
    """Extrae todos los imports de un archivo Python."""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])

    return imports


def test_no_llm_imports_in_student():
    """Verificar que ningún archivo en student/ importa LLMs."""
    student_dir = Path("src/study_engine/student")
    assert student_dir.exists(), "Directorio src/study_engine/student debe existir"

    forbidden_modules = {
        "openai",
        "anthropic",
        "transformers",
        "llama",
        "ollama",
        "langchain",
        "google",
        "groq",
        "together",
        "cohere",
    }

    violations = []

    for py_file in student_dir.rglob("*.py"):
        imports = get_imports(py_file)
        forbidden_found = imports & forbidden_modules

        if forbidden_found:
            violations.append({
                "file": str(py_file),
                "forbidden": list(forbidden_found),
            })

    assert not violations, (
        f"Regla de oro violada: {len(violations)} archivos importan LLMs:\n"
        + "\n".join(f"  {v['file']}: {v['forbidden']}" for v in violations)
    )


if __name__ == "__main__":
    test_no_llm_imports_in_student()
    print("✅ Regla de oro verificada: student/ no importa LLMs")
