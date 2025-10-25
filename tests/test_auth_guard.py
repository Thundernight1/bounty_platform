import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture(autouse=True)
def no_background_tasks(monkeypatch):
    # Avoid running real background scans during tests
    async def _noop(job_id, request):
        return None

    monkeypatch.setattr("backend.main._run_scans", _noop)


def _minimal_job_payload():
    return {
        "project_name": "demo",
        "job_type": "attack_surface",
        "target_url": "https://example.com",
        "accept_terms": True,
    }


def test_post_jobs_open_when_no_api_key_set(monkeypatch):
    # Ensure API_KEY is not set
    monkeypatch.delenv("API_KEY", raising=False)

    client = TestClient(app)
    resp = client.post("/jobs", json=_minimal_job_payload())
    assert resp.status_code == 200
    data = resp.json()
    assert "job_id" in data


def test_post_jobs_requires_api_key_when_set(monkeypatch):
    # Set API key requirement
    monkeypatch.setenv("API_KEY", "secret")

    client = TestClient(app)

    # Missing header → 401
    resp = client.post("/jobs", json=_minimal_job_payload())
    assert resp.status_code == 401

    # Wrong header → 401
    resp = client.post(
        "/jobs",
        json=_minimal_job_payload(),
        headers={"X-API-Key": "wrong"},
    )
    assert resp.status_code == 401

    # Correct header → 200
    resp = client.post(
        "/jobs",
        json=_minimal_job_payload(),
        headers={"X-API-Key": "secret"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("project_name") == "demo"
