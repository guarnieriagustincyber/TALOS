import ast
import os
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
SRC = ROOT / "src"
TESTS = ROOT / "tests"
KASIU_LAB = ROOT / "kasiu-lab"

print("=== 1. FUNCTIONS > 100 LINES IN SRC & KASIU-LAB ===")
long_functions = []
for p in list(SRC.rglob("*.py")) + list((KASIU_LAB).glob("*.py")) + list((KASIU_LAB / "contracts").glob("*.py")):
    if "__pycache__" in str(p) or "venv" in str(p):
        continue
    try:
        content = p.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end_lineno = getattr(node, "end_lineno", node.lineno)
                length = end_lineno - node.lineno + 1
                if length > 100:
                    long_functions.append((str(p), node.lineno, node.name, length))
    except Exception:
        pass

long_functions.sort(key=lambda x: -x[3])
print(f"Total functions > 100 lines: {len(long_functions)}")
for f, line, name, length in long_functions[:25]:
    print(f"  {f}:{line} - {name}() -> {length} lines")

print("\n=== 2. NESTING DEPTH > 5 IN SRC ===")
deep_nesting = []
class NestingVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.current_depth = 0
        self.max_depth = 0
        self.deepest_node = None

    def generic_visit(self, node):
        is_nest = isinstance(node, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        if is_nest:
            self.current_depth += 1
            if self.current_depth > 5:
                deep_nesting.append((self.filename, getattr(node, "lineno", 0), self.current_depth, type(node).__name__))
            super().generic_visit(node)
            self.current_depth -= 1
        else:
            super().generic_visit(node)

for p in SRC.rglob("*.py"):
    if "__pycache__" in str(p):
        continue
    try:
        content = p.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(p))
        visitor = NestingVisitor(str(p))
        visitor.visit(tree)
    except Exception:
        pass

print(f"Total nesting > 5 points: {len(deep_nesting)}")
for f, line, depth, ntype in deep_nesting[:20]:
    print(f"  {f}:{line} -> depth {depth} ({ntype})")

print("\n=== 3. HOLLOW TESTS IN TESTS/ (assert True, pass, empty body) ===")
hollow_tests = []
for p in TESTS.rglob("*.py"):
    if "__pycache__" in str(p):
        continue
    try:
        content = p.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
                # check if body has only pass or assert True
                body = node.body
                is_hollow = False
                reason = ""
                if len(body) == 1:
                    stmt = body[0]
                    if isinstance(stmt, ast.Pass):
                        is_hollow = True
                        reason = "only 'pass'"
                    elif isinstance(stmt, ast.Assert):
                        if isinstance(stmt.test, ast.Constant) and stmt.test.value is True:
                            is_hollow = True
                            reason = "only 'assert True'"
                # Also check if any statement in body is assert True
                for stmt in body:
                    if isinstance(stmt, ast.Assert):
                        if isinstance(stmt.test, ast.Constant) and stmt.test.value is True:
                            hollow_tests.append((str(p), stmt.lineno, node.name, "assert True"))
                    elif isinstance(stmt, ast.Pass) and len(body) <= 2:
                        hollow_tests.append((str(p), stmt.lineno, node.name, "pass statement in short test"))
    except Exception:
        pass

print(f"Total hollow test instances: {len(hollow_tests)}")
for f, line, name, reason in hollow_tests[:25]:
    print(f"  {f}:{line} - {name} -> {reason}")

