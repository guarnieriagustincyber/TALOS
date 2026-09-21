import ast
import re
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
ROUTES_DIR = ROOT / "src" / "study_engine" / "web" / "routes"
DEP_FILE = ROOT / "src" / "study_engine" / "web" / "dependencies.py"

# Extract all attributes of self in AppContainer.__init__
dep_content = DEP_FILE.read_text(encoding="utf-8")
tree = ast.parse(dep_content)

container_attrs = set()
for node in ast.walk(tree):
    if isinstance(node, ast.ClassDef) and node.name == "AppContainer":
        for sub in ast.walk(node):
            if isinstance(sub, ast.Attribute) and isinstance(sub.value, ast.Name) and sub.value.id == "self":
                container_attrs.add(sub.attr)

print("Container attributes initialized:", len(container_attrs))
for a in sorted(container_attrs):
    print(" ", a)

# Now check which attributes are accessed on container in routes
route_files = list(ROUTES_DIR.glob("*.py"))
accessed_attrs = {a: [] for a in container_attrs}

for rf in route_files:
    content = rf.read_text(encoding="utf-8")
    for a in container_attrs:
        # check pattern container.<attr>
        matches = re.findall(rf"\bcontainer\.{a}\b", content)
        if matches:
            accessed_attrs[a].append(rf.name)

print("\n=== CONTAINER ATTRIBUTE USAGE IN ROUTES ===")
never_accessed = []
for a, files in sorted(accessed_attrs.items()):
    if not files:
        never_accessed.append(a)
        print(f"  [NEVER USED IN ROUTES] container.{a}")
    else:
        print(f"  container.{a} used in: {', '.join(files)}")

