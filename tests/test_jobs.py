"""
Tests for job creation and management endpoints.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


def test_create_attack_surface_job(client: TestClient, sample_job_payload: dict):
    """Test creating an attack surface scan job"""
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 200

    data = response.json()
    assert "job_id" in data
    assert data["project_name"] == "test_project"
    assert data["job_type"] == "attack_surface"
    assert data["status"] == "pending"


def test_create_sca_job(client: TestClient):
    """Test creating an SCA scan job"""
    payload = {
        "project_name": "test_sca",
        "job_type": "sca",
        "target_url": "/path/to/repo",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["job_type"] == "sca"


def test_create_smart_contract_job(client: TestClient):
    """Test creating a smart contract scan job"""
    payload = {
        "project_name": "test_contract",
        "job_type": "smart_contract",
        "contract_source": "pragma solidity ^0.8.0; contract Test {}",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["job_type"] == "smart_contract"


def test_reject_job_without_terms(client: TestClient, sample_job_payload: dict):
    """Test that jobs are rejected if terms are not accepted"""
    sample_job_payload["accept_terms"] = False
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 400
    assert "accept_terms" in response.json()["detail"]


def test_reject_attack_surface_without_url(client: TestClient):
    """Test that attack_surface jobs require target_url"""
    payload = {
        "project_name": "test",
        "job_type": "attack_surface",
        "accept_terms": True
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 400
    assert "target_url" in response.json()["detail"]


def test_reject_out_of_scope_url(client: TestClient):
    """Test that URLs outside defined scope are rejected"""
    payload = {
        "project_name": "test",
        "job_type": "attack_surface",
        "target_url": "https://evil.com",
        "accept_terms": True,
        "scope": ["example.com"]
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 400
    assert "out of scope" in response.json()["detail"]


def test_get_job(client: TestClient, sample_job_payload: dict):
    """Test retrieving a job by ID"""
    # Create job
    create_response = client.post("/jobs", json=sample_job_payload)
    job_id = create_response.json()["job_id"]

    # Get job
    get_response = client.get(f"/jobs/{job_id}")
    assert get_response.status_code == 200

    data = get_response.json()
    assert data["job_id"] == job_id
    assert data["project_name"] == "test_project"


def test_get_nonexistent_job(client: TestClient):
    """Test that getting a nonexistent job returns 404"""
    response = client.get("/jobs/nonexistent-id")
    assert response.status_code == 404


def test_list_jobs(client: TestClient, sample_job_payload: dict):
    """Test listing all jobs"""
    # Create multiple jobs
    for i in range(3):
        payload = sample_job_payload.copy()
        payload["project_name"] = f"project_{i}"
        client.post("/jobs", json=payload)

    # List jobs
    response = client.get("/jobs")
    assert response.status_code == 200

    data = response.json()
    assert len(data) >= 3
    assert all("job_id" in job for job in data)


def test_list_jobs_with_filter(client: TestClient, sample_job_payload: dict):
    """Test listing jobs with filters"""
    # Create jobs with different project names
    for project_name in ["project_a", "project_b"]:
        payload = sample_job_payload.copy()
        payload["project_name"] = project_name
        client.post("/jobs", json=payload)

    # Filter by project name
    response = client.get("/jobs?project_name=project_a")
    assert response.status_code == 200

    data = response.json()
    assert all(job["project_name"] == "project_a" for job in data)


def test_list_jobs_pagination(client: TestClient, sample_job_payload: dict):
    """Test job listing pagination"""
    # Create multiple jobs
    for i in range(5):
        payload = sample_job_payload.copy()
        payload["project_name"] = f"project_{i}"
        client.post("/jobs", json=payload)

    # Test pagination
    response = client.get("/jobs?skip=2&limit=2")
    assert response.status_code == 200

    data = response.json()
    assert len(data) <= 2


def test_api_key_protection(client: TestClient, sample_job_payload: dict, api_key_env: str):
    """Test that API key is required when configured"""
    # Without API key should fail
    response = client.post("/jobs", json=sample_job_payload)
    assert response.status_code == 401

    # With correct API key should succeed
    headers = {"X-API-Key": api_key_env}
    response = client.post("/jobs", json=sample_job_payload, headers=headers)
    assert response.status_code == 200

    # With wrong API key should fail
    headers = {"X-API-Key": "wrong-key"}
    response = client.post("/jobs", json=sample_job_payload, headers=headers)
    assert response.status_code == 401


def test_health_check(client: TestClient):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
