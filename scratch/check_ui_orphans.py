import re
from pathlib import Path

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
UI_SRC = ROOT / "kasiu-lab" / "ui" / "src"

all_files = [f for f in UI_SRC.rglob("*") if f.suffix in [".ts", ".tsx"]]
imports_found = set()

for f in all_files:
    content = f.read_text(encoding="utf-8")
    for m in re.finditer(r'from\s+["\']([^"\']+)["\']|import\s+["\']([^"\']+)["\']', content):
        target = m.group(1) or m.group(2)
        if target.startswith("."):
            resolved = (f.parent / target).resolve()
            imports_found.add(str(resolved))
            # also without extension
            imports_found.add(str(resolved.with_suffix(".ts")))
            imports_found.add(str(resolved.with_suffix(".tsx")))

print("=== CHECKING UNUSED / ORPHANED FRONTEND FILES ===")
orphans = []
entry_points = ["main.tsx", "App.tsx", "vite-env.d.ts"]
for f in all_files:
    if f.name in entry_points or f.name.endswith(".d.ts"):
        continue
    f_str = str(f)
    f_without_ext = str(f.with_suffix(""))
    if f_str not in imports_found and f_without_ext not in imports_found:
        orphans.append(f)

print(f"Total orphaned UI files: {len(orphans)}")
for o in orphans:
    print(f"  [ORPHAN FILE] {o.relative_to(UI_SRC)}")

