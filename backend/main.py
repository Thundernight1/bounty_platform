"""
Backend service for the blockchain-based bug bounty platform.

Adds job types (attack_surface, sca, smart_contract), guardrails (accept_terms,
scope checks), and routes scans to the correct agent. Stores results to disk.
"""

from __future__ import annotations

import uuid
import json
import asyncio
from datetime import datetime
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal
from urllib.parse import urlparse

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Support both package and script execution
try:
    from .utils.scanners import (
        run_zap_scan,
        run_mythril_scan,
        run_nuclei_scan,
        run_sca_scan,
    )
except Exception:
    from utils.scanners import (
        run_zap_scan,
        run_mythril_scan,
        run_nuclei_scan,
        run_sca_scan,
    )

app = FastAPI(title="Bug Bounty Platform Backend")

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# CORS for local frontend (8080)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class JobRequest(BaseModel):
    job_type: Literal["attack_surface", "sca", "smart_contract"] = Field(
        "attack_surface", description="Type of scan to run"
    )
    project_name: str = Field(..., description="Project name for reporting")
    target_url: Optional[str] = Field(
        None, description="URL or path (attack_surface URL / sca repo path)"
    )
    contract_source: Optional[str] = Field(
        None, description="Solidity source (for smart_contract jobs)"
    )
    accept_terms: bool = Field(
        ..., description="Must be true to confirm legal/ethical constraints"
    )
    scope: Optional[List[str]] = Field(
        None, description="Allowed domains or repo identifiers"
    )


class JobStatus(BaseModel):
    job_id: str
    project_name: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Dict[str, Any] | None = None


jobs: Dict[str, JobStatus] = {}


def _domain_in_scope(url: str, scope_list: Optional[List[str]]) -> bool:
    if not url or not scope_list:
        return True  # allow if no scope provided (MVP behavior)
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return False
    host = host.lower()
    # exact match or suffix match (e.g., example.com allows a.b.example.com)
    return any(host == s.lower() or host.endswith("." + s.lower()) for s in scope_list)


from fastapi import Depends, Header


def require_api_key(x_api_key: str | None = Header(default=None)):
    required = os.environ.get("API_KEY")
    if not required:
        return  # open by default if API_KEY is not configured
    if x_api_key != required:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/jobs", response_model=JobStatus, summary="Create a new scan job", dependencies=[Depends(require_api_key)])
async def create_job(request: JobRequest, background_tasks: BackgroundTasks) -> JobStatus:
    if not request.accept_terms:
        raise HTTPException(status_code=400, detail="accept_terms must be true")

    if request.job_type == "attack_surface":
        if not request.target_url:
            raise HTTPException(status_code=400, detail="target_url is required")
        if not _domain_in_scope(request.target_url, request.scope):
            raise HTTPException(status_code=400, detail="target_url out of scope")

    if request.job_type == "sca":
        if not request.target_url:
            raise HTTPException(
                status_code=400, detail="target_url must be a local repo path for SCA"
            )

    if request.job_type == "smart_contract":
        if not request.contract_source:
            raise HTTPException(
                status_code=400, detail="contract_source is required for smart_contract"
            )

    job_id = str(uuid.uuid4())
    now = datetime.utcnow()
    job_status = JobStatus(
        job_id=job_id,
        project_name=request.project_name,
        status="pending",
        created_at=now,
    )
    jobs[job_id] = job_status
    background_tasks.add_task(_run_scans, job_id, request)
    return job_status


@app.get("/jobs/{job_id}", response_model=JobStatus, summary="Retrieve job status")
async def get_job(job_id: str) -> JobStatus:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "finished" and job.result is None:
        result_file = RESULTS_DIR / f"{job_id}.json"
        if result_file.exists():
            job.result = json.loads(result_file.read_text())
    return job


async def _run_scans(job_id: str, request: JobRequest) -> None:
    job = jobs[job_id]
    job.status = "running"
    job.started_at = datetime.utcnow()

    result: Dict[str, Any] = {
        "project_name": request.project_name,
        "job_type": request.job_type,
        "target_url": request.target_url,
        "web_scan": None,
        "nuclei": None,
        "sca": None,
        "contract_analysis": None,
    }

    if request.job_type == "attack_surface":
        # Run scans concurrently to reduce total time
        zap_task = run_zap_scan(request.target_url)  # type: ignore[arg-type]
        nuclei_task = run_nuclei_scan(request.target_url)  # type: ignore[arg-type]
        result["web_scan"], result["nuclei"] = await asyncio.gather(zap_task, nuclei_task)

    elif request.job_type == "sca":
        result["sca"] = await run_sca_scan(request.target_url)  # type: ignore[arg-type]

    elif request.job_type == "smart_contract":
        result["contract_analysis"] = await run_mythril_scan(request.contract_source or "")

    job.finished_at = datetime.utcnow()
    job.status = "finished"
    with open(RESULTS_DIR / f"{job_id}.json", "w") as f:
        json.dump(result, f, indent=2)
    await _notify_slack(job_id, request, result)


async def _notify_slack(job_id: str, request: JobRequest, result: Dict[str, Any]) -> None:
    """Post a short summary to Slack if SLACK_WEBHOOK_URL is set."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    try:
        import httpx  # lazy import

        counts = []
        if result.get("web_scan"):
            ws = result["web_scan"]
            v = len(ws.get("vulnerabilities", [])) if isinstance(ws, dict) else 0
            counts.append(f"web:{v}")
        if result.get("nuclei"):
            nu = result["nuclei"]
            v = len(nu.get("findings", [])) if isinstance(nu, dict) else 0
            counts.append(f"nuclei:{v}")
        if result.get("sca"):
            sca = result["sca"]
            if isinstance(sca, dict) and "results" in sca and isinstance(sca["results"], dict):
                v = len(sca["results"].get("vulnerabilities", []))
            else:
                v = len(sca.get("vulnerabilities", [])) if isinstance(sca, dict) else 0
            counts.append(f"sca:{v}")
        if result.get("contract_analysis"):
            ca = result["contract_analysis"]
            v = len(ca.get("issues", [])) if isinstance(ca, dict) else 0
            counts.append(f"contract:{v}")

        text = (
            f"bounty_platform: job {job_id}\n"
            f"type: {request.job_type} | project: {request.project_name}\n"
            f"summary: {' '.join(counts) if counts else 'done'}"
        )
        async with httpx.AsyncClient() as client:
            await client.post(webhook, json={"text": text}, timeout=5)
    except Exception:
        # Silent: notifications should never break the job
        pass
