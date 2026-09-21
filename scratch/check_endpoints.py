import ast
import re
from pathlib import Path
from fastapi import FastAPI
from fastapi.routing import APIRoute

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
import sys
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from study_engine.web.app import create_app

app = create_app()
backend_routes = {}
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = list(route.methods)
        backend_routes[route.path] = {
            "methods": methods,
            "endpoint": f"{route.endpoint.__module__}.{route.endpoint.__name__}",
            "response_model": str(route.response_model)
        }

print(f"Total backend registered routes: {len(backend_routes)}")
for path, info in sorted(backend_routes.items()):
    print(f"  {info['methods']} {path} -> {info['endpoint']}")

# Now inspect frontend UI calls
UI_SRC = ROOT / "kasiu-lab" / "ui" / "src"
ui_calls = []

# regex to find strings matching /api/... or http://.../api/...
call_pattern = re.compile(r'["\'](/api/[a-zA-Z0-9_\-\/{}$]+|http://[a-zA-Z0-9\.:]+(/api/[a-zA-Z0-9_\-\/{}$]+))["\']|`(/api/[^`]+|http://[^`]+/api/[^`]+)`')

for f in UI_SRC.rglob("*"):
    if f.suffix in [".ts", ".tsx", ".js", ".jsx"]:
        lines = f.read_text(encoding="utf-8").splitlines()
        for i, line in enumerate(lines, 1):
            for m in call_pattern.finditer(line):
                matched = m.group(0).strip('"`\'')
                # normalize if it has http://...
                if "/api/" in matched:
                    api_part = "/api/" + matched.split("/api/")[1]
                    ui_calls.append((str(f), i, api_part, line.strip()))

print(f"\nTotal UI API calls found: {len(ui_calls)}")

# Check matching
print("\n=== ROUTE COMPARISON (UI -> BACKEND) ===")
unmatched_ui_calls = []
for file_path, line_no, api_call, raw_line in ui_calls:
    # remove query params
    base_api = api_call.split("?")[0]
    # template string replacement: e.g. ${encodeURIComponent(activeEntity.id)} -> {notebook_id} or regex
    # replace ${...} with {param}
    normalized_pattern = re.sub(r'\$\{[^}]+\}', '{param}', base_api)
    
    # check if matches any backend route
    matched = False
    for b_path in backend_routes:
        # turn b_path into regex
        # e.g. /api/notebook/{notebook_id}/sources -> /api/notebook/[^/]+/sources
        b_regex = re.sub(r'\{[a-zA-Z0-9_]+\}', r'[^/]+', b_path)
        b_regex = f"^{b_regex}$"
        # compare against base_api or normalized_pattern
        test_api = re.sub(r'\$\{[^}]+\}', 'dummy', base_api)
        if re.match(b_regex, test_api) or test_api == b_path:
            matched = True
            break
    if not matched:
        unmatched_ui_calls.append((file_path, line_no, api_call, raw_line))

print(f"Unmatched UI calls: {len(unmatched_ui_calls)}")
for f, l, call, raw in unmatched_ui_calls:
    print(f"  {f}:{l} -> {call} | line: {raw}")
