"""
Backend service for the blockchain-based bug bounty platform (v2 with database).

Adds job types (attack_surface, sca, smart_contract), guardrails (accept_terms,
scope checks), and routes scans to the correct agent. Stores results to database.
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

from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from dotenv import load_dotenv
import httpx
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Database imports
try:
    from backend.database import get_db, init_db
    from backend.models import Job as JobModel, JobStatus as JobStatusEnum, JobType as JobTypeEnum, ScanHistory
except ImportError:
    from database import get_db, init_db
    from models import Job as JobModel, JobStatus as JobStatusEnum, JobType as JobTypeEnum, ScanHistory

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

# Initialize database and http client on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and http client on application startup"""
    init_db()
    # Performance optimization: Reuse a single httpx client across requests
    # rather than creating a new one for each notification.
    app.state.http_client = httpx.AsyncClient()
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="Bug Bounty Platform Backend",
    description="Blockchain-based bug bounty platform with multi-agent security scanning",
    version="2.0.0",
    lifespan=lifespan
)

RESULTS_DIR = Path(__file__).resolve().parent / "results"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# CORS configuration from environment
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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


class JobStatusResponse(BaseModel):
    job_id: str
    project_name: str
    status: str
    job_type: str
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    result: Dict[str, Any] | None = None
    error_message: str | None = None


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


def require_api_key(x_api_key: str | None = Header(default=None)):
    required = os.environ.get("API_KEY")
    if not required:
        return  # open by default if API_KEY is not configured
    if x_api_key != required:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


@app.post("/jobs", response_model=JobStatusResponse, summary="Create a new scan job", dependencies=[Depends(require_api_key)])
def create_job(
    request: JobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> JobStatusResponse:
    """
    Create a new security scan job.

    The job will be processed asynchronously in the background.
    Use GET /jobs/{job_id} to check status and retrieve results.
    """
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

    # Create job in database
    job_id = str(uuid.uuid4())
    job = JobModel(
        id=job_id,
        project_name=request.project_name,
        job_type=request.job_type,
        status=JobStatusEnum.PENDING,
        target_url=request.target_url,
        contract_source=request.contract_source,
        scope=request.scope,
        accept_terms=request.accept_terms,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    # Log job creation
    history = ScanHistory(
        job_id=job_id,
        action="job_created",
        details={"project": request.project_name, "type": request.job_type}
    )
    db.add(history)
    db.commit()

    # Start background task
    background_tasks.add_task(_run_scans, job_id, request)

    return JobStatusResponse(**job.to_dict())


@app.get("/jobs/{job_id}", response_model=JobStatusResponse, summary="Retrieve job status")
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobStatusResponse:
    """
    Retrieve the status and results of a scan job.

    Returns job metadata, current status, and results if available.
    """
    job = db.query(JobModel).filter(JobModel.id == job_id).first()

    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    # Also check file-based results for backward compatibility
    if job.status == JobStatusEnum.COMPLETED.value and job.result is None:
        result_file = RESULTS_DIR / f"{job_id}.json"
        if result_file.exists():
            job.result = json.loads(result_file.read_text())
            db.commit()

    return JobStatusResponse(**job.to_dict())


@app.get("/jobs", summary="List all jobs")
def list_jobs(
    skip: int = 0,
    limit: int = 100,
    project_name: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
) -> List[JobStatusResponse]:
    """
    List all scan jobs with optional filtering.

    - **skip**: Number of records to skip (pagination)
    - **limit**: Maximum number of records to return
    - **project_name**: Filter by project name
    - **status**: Filter by job status
    """
    query = db.query(JobModel)

    if project_name:
        query = query.filter(JobModel.project_name == project_name)
    if status:
        query = query.filter(JobModel.status == status)

    jobs = query.order_by(JobModel.created_at.desc()).offset(skip).limit(limit).all()
    return [JobStatusResponse(**job.to_dict()) for job in jobs]


async def _run_scans(job_id: str, request: JobRequest) -> None:
    """
    Background task to run security scans.
    Updates job status in database throughout execution.
    """
    from backend.database import SessionLocal
    db = SessionLocal()

    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if not job:
            return

        # Update to running
        job.status = JobStatusEnum.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()

        # Log scan start
        history = ScanHistory(
            job_id=job_id,
            action="scan_started",
            details={"type": request.job_type}
        )
        db.add(history)
        db.commit()

        result: Dict[str, Any] = {
            "project_name": request.project_name,
            "job_type": request.job_type,
            "target_url": request.target_url,
            "web_scan": None,
            "nuclei": None,
            "sca": None,
            "contract_analysis": None,
        }

        # Run scans based on job type
        if request.job_type == "attack_surface":
            # ⚡ Bolt: Run independent scans in parallel to reduce total job time.
            # Instead of running ZAP then Nuclei (ZapTime + NucleiTime),
            # they run concurrently. Total time is now MAX(ZapTime, NucleiTime).
            zap_task = asyncio.to_thread(run_zap_scan, request.target_url)
            nuclei_task = asyncio.to_thread(run_nuclei_scan, request.target_url)
            zap_result, nuclei_result = await asyncio.gather(zap_task, nuclei_task)
            result["web_scan"] = zap_result
            result["nuclei"] = nuclei_result

        elif request.job_type == "sca":
            result["sca"] = await asyncio.to_thread(run_sca_scan, request.target_url)

        elif request.job_type == "smart_contract":
            result["contract_analysis"] = await asyncio.to_thread(
                run_mythril_scan, request.contract_source or ""
            )

        # Update job with results
        job.status = JobStatusEnum.COMPLETED
        job.finished_at = datetime.utcnow()
        job.result = result
        db.commit()

        # Log completion
        history = ScanHistory(
            job_id=job_id,
            action="scan_completed",
            details={"findings_count": len(result.get("web_scan", {}).get("vulnerabilities", []))}
        )
        db.add(history)
        db.commit()

        # Also save to file for backward compatibility
        with open(RESULTS_DIR / f"{job_id}.json", "w") as f:
            json.dump(result, f, indent=2)

        # Send notification
        await _notify_slack(job_id, request, result)

    except Exception as e:
        # Handle errors
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        if job:
            job.status = JobStatusEnum.FAILED
            job.finished_at = datetime.utcnow()
            job.error_message = str(e)
            db.commit()

            # Log error
            history = ScanHistory(
                job_id=job_id,
                action="scan_failed",
                details={"error": str(e)}
            )
            db.add(history)
            db.commit()
    finally:
        db.close()


async def _notify_slack(job_id: str, request: JobRequest, result: Dict[str, Any]) -> None:
    """Post a short summary to Slack if SLACK_WEBHOOK_URL is set."""
    webhook = os.environ.get("SLACK_WEBHOOK_URL")
    if not webhook:
        return
    try:
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

        # Use the global client if available, otherwise fall back to a new one
        client = getattr(app.state, "http_client", None)
        if client:
            await client.post(webhook, json={"text": text}, timeout=5)
        else:
            async with httpx.AsyncClient() as new_client:
                await new_client.post(webhook, json={"text": text}, timeout=5)

    except Exception:
        # Silent: notifications should never break the job
        pass


@app.get("/health", summary="Health check endpoint")
async def health_check():
    """Simple health check endpoint for monitoring"""
    return {"status": "healthy", "version": "2.0.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000))
    )
