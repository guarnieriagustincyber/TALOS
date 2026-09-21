"""Isolation and Declarative Purity contract tests for Subsystem S5.4.

Enforces:
- HG-S5.4-O1-01: Strict Contractual Isolation.
- HG-S5.4-06: Declarative Purity.
"""

import ast
import inspect
from pathlib import Path

import study_engine.curriculum as curriculum_pkg


def test_hg_s5_4_o1_01_strict_contractual_isolation() -> None:
    """HG-S5.4-O1-01: No S5.4 module may import S3/S4/S6-S10/State/Ledger."""
    curriculum_dir = Path(curriculum_pkg.__file__).parent
    py_files = list(curriculum_dir.glob("*.py"))
    assert len(py_files) >= 9, (
        f"Expected at least 9 modules, found {len(py_files)}"
    )

    disallowed_import_fragments = [
        "study_engine.session",
        "study_engine.audit",
        "study_engine.generation",
        "study_engine.retrieval",
        "study_engine.llm",
        "study_engine.context",
        "study_engine.state.ledger",
        "study_engine.state.state_engine",
        "study_engine.state.policy_engine",
        "study_engine.lab",
        "study_engine.evaluator",
        "study_engine.execution",
    ]

    for py_file in py_files:
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    for disallowed in disallowed_import_fragments:
                        assert not alias.name.startswith(disallowed), (
                            f"HG-S5.4-O1-01 VIOLATION: {py_file.name} "
                            f"imports forbidden module '{alias.name}'"
                        )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for disallowed in disallowed_import_fragments:
                    assert not module.startswith(disallowed), (
                        f"HG-S5.4-O1-01 VIOLATION: {py_file.name} "
                        f"imports from forbidden module '{module}'"
                    )


def test_hg_s5_4_06_declarative_purity() -> None:
    """HG-S5.4-06: No eval(), exec(), subprocess, sockets, or callables."""
    curriculum_dir = Path(curriculum_pkg.__file__).parent
    py_files = list(curriculum_dir.glob("*.py"))

    forbidden_calls = {"eval", "exec", "compile"}
    forbidden_modules = {
        "subprocess",
        "socket",
        "http",
        "urllib",
        "requests",
        "os.system",
    }

    for py_file in py_files:
        content = py_file.read_text()
        tree = ast.parse(content, filename=str(py_file))

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if (
                    isinstance(node.func, ast.Name)
                    and node.func.id in forbidden_calls
                ):
                    raise AssertionError(
                        f"HG-S5.4-06 VIOLATION: {py_file.name} calls "
                        f"forbidden evaluator '{node.func.id}'"
                    )

            if isinstance(node, ast.Import):
                for alias in node.names:
                    assert alias.name not in forbidden_modules, (
                        f"HG-S5.4-06 VIOLATION: {py_file.name} imports "
                        f"execution module '{alias.name}'"
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                assert module not in forbidden_modules, (
                    f"HG-S5.4-06 VIOLATION: {py_file.name} imports "
                    f"from execution module '{module}'"
                )


def test_exported_contract_classes_possess_no_callables() -> None:
    """HG-S5.4-06: All exported contract classes must be static data."""
    for symbol_name in curriculum_pkg.__all__:
        symbol = getattr(curriculum_pkg, symbol_name)
        if inspect.isclass(symbol) and hasattr(symbol, "model_fields"):
            for field_name, field_info in symbol.model_fields.items():
                annotation = str(field_info.annotation)
                assert "Callable" not in annotation, (
                    f"HG-S5.4-06 VIOLATION: {symbol_name}.{field_name} "
                    f"declares Callable type: {annotation}"
                )
