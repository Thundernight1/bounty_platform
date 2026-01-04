"""
Tests for job creation and management endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.models import User, Job, JobType

def test_create_attack_surface_job(client: TestClient, sample_job_payload: dict, auth_headers: dict):
    """Test creating an attack surface scan job"""
    response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "job_id" in data
    assert data["project_name"] == "test_project"
    assert data["status"] == "pending"


def test_create_sca_job(client: TestClient, auth_headers: dict):
    """Test creating an SCA scan job"""
    payload = {
        "project_name": "test_sca",
        "job_type": "sca",
        "target_url": "/path/to/repo",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["project_name"] == "test_sca"


def test_reject_job_without_terms(client: TestClient, sample_job_payload: dict, auth_headers: dict):
    """Test that jobs are rejected if terms are not accepted"""
    sample_job_payload["accept_terms"] = False
    response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    assert response.status_code == 400
    assert "accept_terms" in response.json()["detail"]


def test_reject_out_of_scope_url(client: TestClient, auth_headers: dict):
    """Test that URLs outside defined scope are rejected"""
    payload = {
        "project_name": "test",
        "job_type": "attack_surface",
        "target_url": "https://evil.com",
        "accept_terms": True,
        "scope": ["example.com"]
    }
    response = client.post("/jobs", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "out of scope" in response.json()["detail"]


def test_get_job(client: TestClient, sample_job_payload: dict, auth_headers: dict, db_session: Session, test_user: User):
    """Test retrieving a job by ID"""
    # Create job
    create_response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    job_id = create_response.json()["job_id"]

    # Get job
    get_response = client.get(f"/jobs/{job_id}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["job_id"] == job_id


def test_get_job_unauthorized(client: TestClient, sample_job_payload: dict, auth_headers: dict, db_session: Session):
    """Test that a user cannot retrieve a job they do not own."""
    # Create job with the first user
    create_response = client.post("/jobs", json=sample_job_payload, headers=auth_headers)
    job_id = create_response.json()["job_id"]

    # Create a second user and token
    from backend.main import get_password_hash, create_access_token
    other_user = User(email="other@example.com", hashed_password=get_password_hash("p2"))
    db_session.add(other_user)
    db_session.commit()
    other_token = create_access_token(data={"sub": other_user.email})
    other_headers = {"Authorization": f"Bearer {other_token}"}

    # Attempt to fetch with the second user
    get_response = client.get(f"/jobs/{job_id}", headers=other_headers)
    assert get_response.status_code == 403


def test_get_nonexistent_job(client: TestClient, auth_headers: dict):
    """Test that getting a nonexistent job returns 404"""
    response = client.get("/jobs/nonexistent-id", headers=auth_headers)
    assert response.status_code == 404


def test_list_jobs(client: TestClient, sample_job_payload: dict, auth_headers: dict, test_user: User, db_session: Session):
    """Test listing all jobs for the authenticated user"""
    # Create multiple jobs for the user
    for i in range(3):
        db_job = Job(id=f"test-job-{i}", project_name=f"p{i}", job_type=JobType.ATTACK_SURFACE, user_id=test_user.id, accept_terms=True)
        db_session.add(db_job)
    db_session.commit()

    # List jobs
    response = client.get("/jobs", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert {j["project_name"] for j in data} == {"p0", "p1", "p2"}
