import ast
import os
import re
import sys
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
SRC = ROOT / "src"
KASIU_LAB = ROOT / "kasiu-lab"
UI_SRC = KASIU_LAB / "ui" / "src"
TESTS = ROOT / "tests"

print("--- STARTING FORENSIC SCAN ---")

# 1. BROKEN IMPORTS CHECK
print("\n=== CHECKING IMPORTS IN SRC & KASIU-LAB ===")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(SRC))
sys.path.insert(0, str(KASIU_LAB))

py_files = list(SRC.rglob("*.py")) + list((KASIU_LAB).glob("*.py")) + list((KASIU_LAB / "contracts").glob("*.py"))
broken_imports = []

for pf in py_files:
    if "venv" in str(pf) or "__pycache__" in str(pf):
        continue
    try:
        content = pf.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(pf))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    # check if top-level module can be imported or resolved
                    top_mod = alias.name.split(".")[0]
                    # ignore standard / installed
            elif isinstance(node, ast.ImportFrom):
                mod = node.module
                # check relative or absolute import
    except Exception as e:
        broken_imports.append((str(pf), 1, f"Syntax/Parse error: {e}"))

# Let's also do a real python import test on all src/ modules
import importlib
failed_module_imports = []
for pf in SRC.rglob("*.py"):
    if pf.name == "__init__.py" or "pycache" in str(pf):
        continue
    rel = pf.relative_to(SRC).with_suffix("")
    mod_name = ".".join(rel.parts)
    try:
        importlib.import_module(mod_name)
    except Exception as e:
        failed_module_imports.append((str(pf), str(e)))

print(f"Failed module imports in src: {len(failed_module_imports)}")
for f, err in failed_module_imports[:10]:
    print(f"  {f}: {err}")

# 2. KEYWORD SEARCH: TODO, FIXME, HACK, MOCK, STUB, PLACEHOLDER
print("\n=== CHECKING KEYWORDS (TODO, FIXME, HACK, MOCK, STUB, PLACEHOLDER) ===")
pattern = re.compile(r"\b(TODO|FIXME|HACK|MOCK|STUB|PLACEHOLDER)\b", re.IGNORECASE)
keyword_findings = []

search_dirs = [SRC, KASIU_LAB / "server.py", KASIU_LAB / "contracts", UI_SRC, ROOT / "start_talos.py"]
for target in search_dirs:
    if target.is_file():
        files = [target]
    else:
        files = [p for p in target.rglob("*") if p.is_file() and not any(x in str(p) for x in ["node_modules", "dist", "venv", "__pycache__", ".git"])]

    for f in files:
        if f.suffix in [".py", ".ts", ".tsx", ".js", ".json", ".html", ".sh"]:
            try:
                lines = f.read_text(encoding="utf-8", errors="ignore").splitlines()
                for idx, line in enumerate(lines, 1):
                    # Check if line matches keyword
                    m = pattern.search(line)
                    if m:
                        # Exclude self-references in this script or documentation markdown
                        keyword_findings.append((str(f), idx, m.group(1).upper(), line.strip()))
            except Exception:
                pass

print(f"Total keyword findings: {len(keyword_findings)}")
for item in keyword_findings[:20]:
    print(f"  {item[0]}:{item[1]} [{item[2]}] {item[3][:80]}")

# 3. MOCK / STUB / HARDCODED RESPONSES IN PRODUCTION CODE (SRC & KASIU-LAB)
print("\n=== CHECKING STUBS / DUMMY RETURNS IN SRC ===")
stub_findings = []
for pf in SRC.rglob("*.py"):
    if "__pycache__" in str(pf):
        continue
    try:
        content = pf.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(pf))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Check if body is just pass or return None, or return [] or return {}
                body = node.body
                if len(body) == 1:
                    stmt = body[0]
                    if isinstance(stmt, ast.Pass):
                        stub_findings.append((str(pf), node.lineno, node.name, "Single statement: 'pass'"))
                    elif isinstance(stmt, ast.Return):
                        if stmt.value is None:
                            stub_findings.append((str(pf), node.lineno, node.name, "Single statement: 'return' (None)"))
                        elif isinstance(stmt.value, ast.Constant) and stmt.value.value is None:
                            stub_findings.append((str(pf), node.lineno, node.name, "Single statement: 'return None'"))
                        elif isinstance(stmt.value, ast.List) and len(stmt.value.elts) == 0:
                            stub_findings.append((str(pf), node.lineno, node.name, "Single statement: 'return []'"))
                        elif isinstance(stmt.value, ast.Dict) and len(stmt.value.keys) == 0:
                            stub_findings.append((str(pf), node.lineno, node.name, "Single statement: 'return {}'"))
                elif len(body) == 2 and isinstance(body[0], ast.Expr) and isinstance(body[0].value, (ast.Str, ast.Constant)):
                    # Docstring + single statement
                    stmt = body[1]
                    if isinstance(stmt, ast.Pass):
                        stub_findings.append((str(pf), node.lineno, node.name, "Docstring + 'pass'"))
                    elif isinstance(stmt, ast.Return):
                        if stmt.value is None or (isinstance(stmt.value, ast.Constant) and stmt.value.value is None):
                            stub_findings.append((str(pf), node.lineno, node.name, "Docstring + 'return None'"))
                        elif isinstance(stmt.value, ast.List) and len(stmt.value.elts) == 0:
                            stub_findings.append((str(pf), node.lineno, node.name, "Docstring + 'return []'"))
                        elif isinstance(stmt.value, ast.Dict) and len(stmt.value.keys) == 0:
                            stub_findings.append((str(pf), node.lineno, node.name, "Docstring + 'return {}'"))
    except Exception as e:
        pass

print(f"Total stub function findings: {len(stub_findings)}")
for item in stub_findings[:20]:
    print(f"  {item[0]}:{item[1]} {item[2]} -> {item[3]}")

