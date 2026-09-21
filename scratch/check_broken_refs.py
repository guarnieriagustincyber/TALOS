import ast
import os
import re
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()

print("=== CHECKING MISSING FILES / PATH REFERENCES IN CODE ===")
# Search for Path("...") or open("...") where the target string looks like a hardcoded file in repo
path_pattern = re.compile(r'Path\(["\']([^"\']+)["\']\)|open\(["\']([^"\']+)["\']')

missing_paths = []
for p in (ROOT / "src").rglob("*.py"):
    if "__pycache__" in str(p):
        continue
    try:
        lines = p.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            for m in path_pattern.finditer(line):
                val = m.group(1) or m.group(2)
                # Ignore url, variables, mode params, or temporary names
                if any(val.startswith(x) for x in ["http", ":", "{", "/", "."]):
                    continue
                # If it looks like a relative file path (contains /)
                if "/" in val and not val.startswith("%"):
                    target_path = ROOT / val
                    if not target_path.exists():
                        missing_paths.append((str(p), i, val, line.strip()))
    except Exception:
        pass

print(f"Missing relative path references in src: {len(missing_paths)}")
for f, l, path, raw in missing_paths:
    print(f"  {f}:L{l} -> {path} | {raw}")

print("\n=== CHECKING UNREGISTERED ROUTERS OR ROUTES ===")
# Check all files in src/study_engine/web/routes
app_file = ROOT / "src" / "study_engine" / "web" / "app.py"
app_content = app_file.read_text(encoding="utf-8")
routes_dir = ROOT / "src" / "study_engine" / "web" / "routes"
for rf in routes_dir.glob("*.py"):
    if rf.name == "__init__.py":
        continue
    mod_name = rf.stem
    # Check if imported in app.py
    if f"from study_engine.web.routes.{mod_name} import router as" not in app_content and f"study_engine.web.routes.{mod_name}" not in app_content:
        print(f"  [UNREGISTERED ROUTE MODULE] {rf.name} is NOT imported in app.py!")

