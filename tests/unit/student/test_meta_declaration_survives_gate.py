"""COMMIT 1 fix(memory): declaraciones meta sobreviven al gate de abstención.

Bug original: una query tipo "Prefiero que me expliques con analogías de X"
no recupera chunks (QUERY_OUT_OF_SCOPE) -> el SSE abstenía y salía sin llamar
a la extracción de memoria en background -> la preferencia jamás persistía.

Contrato: el contenido abstiene (epistemia intacta) PERO la preferencia
queda persistida en student_state.db y es legible por el ensamblador de
directivas (turno/sesión posterior).
"""

import time

from fastapi.testclient import TestClient


def test_meta_declaration_abstains_but_persists_preference(tmp_path):
    from study_engine.contracts.notebook import Notebook
    from study_engine.hierarchy.folder import Folder
    from study_engine.web.app import create_app
    from study_engine.web.dependencies import AppContainer, set_container
    from datetime import datetime, timezone

    app = create_app()
    container = AppContainer(working_dir=tmp_path, use_mock=True)
    set_container(container)
    store = container.knowledge_store

    now = datetime.now(timezone.utc)
    if not store.contains_folder("f_prog"):
        store.create_folder(
            Folder(id="f_prog", name="Carrera Programación",
                   parent_folder_id="folder_root", created_at=now, updated_at=now)
        )
    if not store.contains_notebook("nb_prog_1"):
        store.create_notebook(Notebook(id="nb_prog_1", name="Punteros y Memoria", folder_id="f_prog"))

    client = TestClient(app)
    response = client.post(
        "/api/chat/query",
        json={
            "prompt": "Prefiero que me expliques todo con analogías de comercio exterior",
            "scope_type": "notebook",
            "scope_id": "nb_prog_1",
            "requested_phase": "conceptual",
        },
    )
    assert response.status_code == 200

    import json
    events = [
        json.loads(line[6:])
        for line in response.text.split("\n")
        if line.startswith("data: ")
    ]
    event_types = [e["event_type"] for e in events]

    # 1. El contenido ABSTINE (no hay corpus en el tmp store)
    assert "abstention" in event_types

    # 2. Pero la preferencia persiste en student_state.db (background task)
    deadline = time.time() + 3.0
    prefs = []
    while time.time() < deadline:
        prefs = container.student_storage.get_pedagogical_memories(
            student_id="agustin",
            category="preference",
        )
        if prefs:
            break
        time.sleep(0.1)
    assert prefs, "la preferencia meta debió persistir a pesar de la abstención"
    assert "analog" in prefs[0]["insight"].lower()

    # 3. La directiva de largo plazo la incorpora (turno futuro la vería)
    directive = container.mem0_manager.assemble_long_term_directive(student_id="agustin")
    assert "analog" in directive.lower()
