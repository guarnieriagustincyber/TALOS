"""API integration tests for student exercises endpoints (VSCode + TALOS Auditor)."""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from study_engine.web.app import create_app

client = TestClient(create_app())


def test_list_and_verify_student_exercise_flow(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Point BASE_SUBMISSIONS_DIR to tmp_path
    submissions_dir = tmp_path / "student_submissions"
    submissions_dir.mkdir()
    (submissions_dir / "templates").mkdir()
    (submissions_dir / "templates" / "template_programming.md").write_text("# Template", encoding="utf-8")

    from study_engine.web.routes import student_exercises
    monkeypatch.setattr(student_exercises, "BASE_SUBMISSIONS_DIR", submissions_dir)
    monkeypatch.setattr(student_exercises, "REPORTS_DIR", submissions_dir / ".reports")

    # 1. Initially no exercises
    resp = client.get("/api/student/exercises")
    assert resp.status_code == 200
    assert resp.json() == []

    # 2. Student creates file in VSCode
    tramo4_dir = submissions_dir / "fase0-soc" / "tramo4"
    tramo4_dir.mkdir(parents=True)
    doc_content = """# Ejercicio: ej_07_es_octeto_valido

## Enunciado
Validar si un octeto está en el rango [0, 255].

## Contrato Formal
PRE: octeto es un entero
POST: retorna True si 0 <= octeto <= 255, False en caso contrario

## Diagrama de Flujo
```mermaid
flowchart TD
    A[Inicio] --> B{0 <= octeto <= 255?}
    B -->|Sí| C[True]
    B -->|No| D[False]
```

## Pseudocódigo
```
FUNCIÓN es_octeto_valido(octeto)
    SI octeto < 0 O octeto > 255 ENTONCES
        RETORNAR Falso
    FIN SI
    RETORNAR Verdadero
FIN FUNCIÓN
```

## Código Python
```python
def es_octeto_valido(octeto: int) -> bool:
    \"\"\"Valida si un número está en el rango [0, 255].\"\"\"
    return 0 <= octeto <= 255
```

## Tests
```python
assert es_octeto_valido(0) == True
assert es_octeto_valido(255) == True
assert es_octeto_valido(256) == False
assert es_octeto_valido(-1) == False
```
"""
    ex_file = tramo4_dir / "ej_07_es_octeto_valido.md"
    ex_file.write_text(doc_content, encoding="utf-8")

    # 3. GET /exercises lists the discovered file
    resp = client.get("/api/student/exercises")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["exercise_id"] == "ej_07_es_octeto_valido"
    assert items[0]["status"] == "SUBMITTED"
    assert items[0]["file_exists"] is True

    # 4. GET /exercises/{id} returns details
    resp = client.get("/api/student/exercises/ej_07_es_octeto_valido")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["exercise_id"] == "ej_07_es_octeto_valido"
    assert "code " in detail["vscode_command"]
    assert detail["file_exists"] is True

    # 5. POST /exercises/{id}/verify executes audit and updates BKT
    resp = client.post("/api/student/exercises/ej_07_es_octeto_valido/verify")
    assert resp.status_code == 200
    report = resp.json()
    assert report["exercise_id"] == "ej_07_es_octeto_valido"
    assert report["passed"] is True
    assert report["score"] >= 80.0
    assert report["bkt_updated"] is True

    # 6. GET /exercises/{id}/report returns persisted report
    resp = client.get("/api/student/exercises/ej_07_es_octeto_valido/report")
    assert resp.status_code == 200
    cached_report = resp.json()
    assert cached_report["score"] == report["score"]

    # 7. Non-existent exercise verification returns 404
    resp = client.post("/api/student/exercises/ej_inexistente/verify")
    assert resp.status_code == 404
    assert "no encontrado" in resp.json()["detail"].lower()

    # 8. POST /exercises/{id}/init-template generates file on disk
    resp = client.post("/api/student/exercises/ej_nuevo_init/init-template?notebook_id=fase0-soc&unit=tramo1")
    assert resp.status_code == 200
    init_data = resp.json()
    assert init_data["file_exists"] is True
    assert (submissions_dir / "fase0-soc" / "tramo1" / "ej_nuevo_init.md").exists()

