import pytest
from fastapi.testclient import TestClient
from study_engine.web.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_curriculum_progress_fadena(client):
    response = client.get('/api/notebook/fadena-lenguajes/curriculum-progress')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    first_unit = data[0]
    assert 'unit' in first_unit
    assert 'unit_name' in first_unit
    assert 'subtopics' in first_unit
    assert len(first_unit['subtopics']) > 0

    first_sub = first_unit['subtopics'][0]
    assert 'id' in first_sub
    assert 'name' in first_sub
    assert 'status' in first_sub
    assert first_sub['status'] in ['pending', 'in_progress', 'covered', 'mastered']
    assert 'evidence_count' in first_sub


def test_get_curriculum_progress_unknown_notebook(client):
    response = client.get('/api/notebook/unknown-notebook-xyz/curriculum-progress')
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
