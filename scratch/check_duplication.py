import ast
import re
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()

# Compare endpoints between kasiu-lab/server.py and src/study_engine/web/routes/
server_py = ROOT / "kasiu-lab" / "server.py"
server_lines = server_py.read_text(encoding="utf-8").splitlines()

routes_dir = ROOT / "src" / "study_engine" / "web" / "routes"

print("=== CHECKING DUPLICATION BETWEEN KASIU-LAB/SERVER.PY AND SRC/STUDY_ENGINE/WEB/ROUTES ===")

# Compare blocks of 10 lines
chunk_size = 10
server_chunks = {}
for i in range(len(server_lines) - chunk_size):
    chunk = "\n".join(l.strip() for l in server_lines[i:i+chunk_size] if l.strip() and not l.strip().startswith("#"))
    if len(chunk) > 100:
        server_chunks[chunk] = i + 1

for rf in routes_dir.glob("*.py"):
    rf_lines = rf.read_text(encoding="utf-8").splitlines()
    for j in range(len(rf_lines) - chunk_size):
        rchunk = "\n".join(l.strip() for l in rf_lines[j:j+chunk_size] if l.strip() and not l.strip().startswith("#"))
        if rchunk in server_chunks:
            print(f"Duplicate found between kasiu-lab/server.py:L{server_chunks[rchunk]} and {rf.name}:L{j+1}")

print("\n=== CHECKING DUPLICATE FUNCTIONS IN SRC ===")
# Check identical function bodies in src
from collections import defaultdict
funcs = defaultdict(list)
for pf in (ROOT / "src").rglob("*.py"):
    if "__pycache__" in str(pf):
        continue
    try:
        tree = ast.parse(pf.read_text(encoding="utf-8"), filename=str(pf))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body_dump = ast.dump(node)
                # remove lineno and col_offset
                clean_dump = re.sub(r'lineno=\d+, col_offset=\d+,?|end_lineno=\d+, end_col_offset=\d+,?', '', body_dump)
                funcs[clean_dump].append((str(pf), node.lineno, node.name))
    except Exception:
        pass

dupes = {k: v for k, v in funcs.items() if len(v) >= 3 and "pass" not in k[:50]}
print(f"Functions with identical AST structure replicated >= 3 times: {len(dupes)}")
for k, v in list(dupes.items())[:15]:
    print(f"  Replicated {len(v)} times across:")
    for f, l, n in v[:5]:
        print(f"    - {f}:{l} ({n})")

