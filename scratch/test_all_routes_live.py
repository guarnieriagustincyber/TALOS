import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from study_engine.web.app import create_app
from study_engine.web.dependencies import get_container

app = create_app()
client = TestClient(app)

print("=== TESTING ALL REGISTERED GET ENDPOINTS ===")

# Test common GET endpoints
endpoints_to_test = [
    ("/", 200),
    ("/api/health", 200),
    ("/api/curriculum/roadmap", 200),
    ("/api/curriculum/nodes/node_tcp", 200),
    ("/api/curriculum/nodes/non_existent_node", 404),
    ("/api/curriculum/graph", 200),
    ("/api/student/state", 200),
    ("/api/student/ledger", 200),
    ("/api/student/profile", 200),
    ("/api/student/cognitive-state", 200),
    ("/api/student/spaced-repetition/due", 200),
    ("/api/session/practice/task?session_id=sess_default", 200),
    ("/api/llm_pool/health", 200),
    ("/api/sources", 200),
    ("/api/evidence/claims/sess_default", 200),
    ("/api/evidence/coverage/sess_default", 200),
    ("/api/ingestion/catalog", 200),
    ("/api/ingestion/conflicts", 200),
    ("/api/federation/notebooks", 200),
    ("/api/federation/bridges", 200),
    ("/api/threatintel/feed", 200),
    ("/api/telemetry/metrics", 200),
    ("/api/telemetry/gates", 200),
    ("/api/config/read-only", 200),
    ("/api/pedagogy/notebook/fadena-prog/kcs", 200),
    ("/api/notebook/fadena-prog/domain-distribution", 200),
    ("/api/notebook/fadena-prog/sources", 200),
    ("/api/notebook/fadena-prog/curriculum-progress", 200),
    ("/api/evidence/open-local-pdf?hash=123&page=1", 404),  # Checking the frontend mismatch!
]

for url, expected in endpoints_to_test:
    try:
        resp = client.get(url)
        print(f"GET {url:55} -> Status: {resp.status_code} (Expected {expected})")
        if resp.status_code >= 500:
            print(f"  CRASH/500 ERROR on {url}: {resp.text}")
    except Exception as e:
        print(f"  EXCEPTION on GET {url}: {e}")

print("\n=== TESTING POST ENDPOINTS ===")
post_endpoints = [
    ("/api/system/heartbeat", {}),
    ("/api/student/readiness/assess", {"topic_id": "net_tcp", "plan_only": True}),
    ("/api/practice/evaluate", {"task_id": "task_1", "file_path": "solution.py", "command": ":eval"}),
]

for url, payload in post_endpoints:
    try:
        resp = client.post(url, json=payload)
        print(f"POST {url:55} -> Status: {resp.status_code}")
        if resp.status_code >= 500:
            print(f"  CRASH/500 ERROR on {url}: {resp.text}")
    except Exception as e:
        print(f"  EXCEPTION on POST {url}: {e}")

