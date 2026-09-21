import ast
import re
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
SRC = ROOT / "src"

print("=== CHECKING FOR N+1 QUERIES (cursor.execute inside for/while loops) ===")
n_plus_one = []

for p in SRC.rglob("*.py"):
    if "__pycache__" in str(p):
        continue
    try:
        content = p.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(p))
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute):
                        if sub.func.attr in ["execute", "executemany"]:
                            # check if it's cursor.execute or conn.execute
                            n_plus_one.append((str(p), sub.lineno, node.lineno, ast.unparse(sub)[:100]))
    except Exception:
        pass

print(f"Total N+1 query patterns found: {len(n_plus_one)}")
for f, exec_line, loop_line, code in n_plus_one:
    print(f"  {f}:L{exec_line} (inside loop at L{loop_line}) -> {code}")

