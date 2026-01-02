import pytest
from fastapi.testclient import TestClient


def _minimal_job_payload():
    return {
        "project_name": "demo",
        "job_type": "attack_surface",
        "target_url": "https://example.com",
        "accept_terms": True,
    }


def test_jobs_endpoint_requires_authentication(client: TestClient):
    """
    Verify that the /jobs endpoint is protected and requires a valid JWT.
    """
    # 1. Create a new user
    user_payload = {
        "email": "test@example.com",
        "password": "a_secure_password"
    }
    resp = client.post("/auth/register", json=user_payload)
    assert resp.status_code == 200

    # 2. Attempt to access /jobs without a token (should fail)
    resp = client.post("/jobs", json=_minimal_job_payload())
    assert resp.status_code == 401

    # 3. Log in to get an access token
    login_payload = {
        "username": user_payload["email"],
        "password": user_payload["password"]
    }
    resp = client.post("/auth/token", data=login_payload)
    assert resp.status_code == 200
    token = resp.json()["access_token"]

    # 4. Access /jobs with an invalid token (should fail)
    headers = {"Authorization": "Bearer invalid-token"}
    resp = client.post("/jobs", json=_minimal_job_payload(), headers=headers)
    assert resp.status_code == 401

    # 5. Access /jobs with the correct token (should succeed)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/jobs", json=_minimal_job_payload(), headers=headers)
    assert resp.status_code == 200
    assert "job_id" in resp.json()
