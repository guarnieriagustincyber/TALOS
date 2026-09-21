import sys
import os
from pathlib import Path
import tempfile

ROOT = Path("/media/agustin/Laboratorio/study-engie").resolve()
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

print("1. Creating tmp dir")
tmp_dir = Path(tempfile.mkdtemp())
print("2. Importing dependencies")
from study_engine.web.dependencies import AppContainer, set_container
print("3. Initializing AppContainer(working_dir=tmp_dir, use_mock=True)")
container = AppContainer(working_dir=tmp_dir, use_mock=True)
print("4. set_container")
set_container(container)
print("5. create_app")
from study_engine.web.app import create_app
app = create_app()
print("6. TestClient")
from fastapi.testclient import TestClient
client = TestClient(app)
print("7. client.get('/api/ingestion/catalog')")
response = client.get("/api/ingestion/catalog")
print("8. Got response:", response.status_code)
print(response.json())
