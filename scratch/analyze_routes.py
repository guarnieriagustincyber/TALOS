import ast
import inspect
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
ROUTES_DIR = ROOT / "src" / "study_engine" / "web" / "routes"

print("=== ANALYZING ALL ROUTE FILES IN SRC/STUDY_ENGINE/WEB/ROUTES ===")
for rf in sorted(ROUTES_DIR.glob("*.py")):
    if rf.name == "__init__.py":
        continue
    content = rf.read_text(encoding="utf-8")
    lines = content.splitlines()
    tree = ast.parse(content, filename=str(rf))
    print(f"\n--- FILE: {rf.name} ({len(lines)} lines) ---")
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Check decorators to see if it's an endpoint
            is_route = False
            route_info = ""
            for dec in node.decorator_list:
                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.value.id == "router":
                    is_route = True
                    method = dec.func.attr
                    path = dec.args[0].value if (dec.args and isinstance(dec.args[0], ast.Constant)) else ""
                    route_info = f"@{method.upper()} {path}"
            if is_route:
                # check body of route function
                print(f"  Line {node.lineno}: {route_info} def {node.name}()")
                # check if returns hardcoded literals
                returns = [n for n in ast.walk(node) if isinstance(n, ast.Return)]
                for r in returns:
                    val = r.value
                    if isinstance(val, (ast.List, ast.Dict, ast.Constant)):
                        print(f"    -> Literal return at line {r.lineno}: {lines[r.lineno-1].strip()[:80]}")

