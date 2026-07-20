"""Jobs + Applications API.

CRUD for job postings and the applications attached to them. AI generation of
job content (description, interview plan, questions) lives in the Job Creation
engine (task B1); this router owns persistence and pipeline status.
"""
import logging
import os
import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from db_models import Job, Application, Candidate, User
from dependencies import get_current_user
from schemas import (
    JobCreate, JobUpdate, JobResponse,
    ApplicationCreate, ApplicationResponse, ApplicationStatusUpdate,
)
from services.job_engine import generate_job_content
from services.resume_parser import extract_text_from_pdf

logger = logging.getLogger("hiringbuddy.jobs")
router = APIRouter()
public_router = APIRouter()  # unauthenticated careers endpoints

_APPLICATION_STATUSES = {
    "applied", "screening", "shortlisted", "interview", "offer", "hired", "rejected",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _slug(title: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (title or "job").lower()).strip("-")[:50] or "job"
    return f"{base}-{uuid.uuid4().hex[:6]}"


def _with_count(job: Job) -> Job:
    # Attribute is read by JobResponse (from_attributes).
    job.application_count = len(job.applications or [])
    return job


def _get_job(job_id: int, db: Session, org_id: Optional[int] = None) -> Job:
    q = db.query(Job).filter(Job.id == job_id)
    if org_id is not None:
        q = q.filter(Job.organization_id == org_id)
    job = q.first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


def _skill_match(candidate: Optional[Candidate], job: Job) -> Optional[float]:
    """Cheap job-fit signal: share of a job's required skills the candidate has.

    A deliberately simple baseline — the explainable scoring engine (B3) refines it.
    """
    required = {s.lower() for s in (job.required_skills or []) if s}
    if not required or not candidate or not candidate.skills:
        return None
    have = {s.lower() for s in candidate.skills}
    return round(100 * len(required & have) / len(required), 1)


# ---------------------------------------------------------------------------
# Jobs CRUD
# ---------------------------------------------------------------------------
@router.post("/", response_model=JobResponse)
def create_job(
    payload: JobCreate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    job = Job(**payload.model_dump())
    job.public_slug = _slug(payload.title)
    job.organization_id = current.organization_id
    db.add(job)
    db.commit()
    db.refresh(job)
    logger.info("Job created: id=%s title=%s org=%s", job.id, job.title, job.organization_id)
    return _with_count(job)


@router.get("/", response_model=List[JobResponse])
def list_jobs(
    status: Optional[str] = None,
    q: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Job).filter(Job.organization_id == current.organization_id)
    if status:
        query = query.filter(Job.status == status)
    if q:
        query = query.filter(Job.title.ilike(f"%{q}%"))
    return [_with_count(j) for j in query.order_by(Job.id.desc()).all()]


@public_router.get("/public/{slug}", response_model=JobResponse)
def get_public_job(slug: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.public_slug == slug).first()
    if not job or job.status not in ("open",):
        raise HTTPException(status_code=404, detail="Job posting not available")
    return _with_count(job)


@public_router.post("/public/{slug}/apply")
async def apply_to_job(
    slug: str,
    background_tasks: BackgroundTasks,
    resume: UploadFile = File(...),
    cover_letter: Optional[str] = Form(None),
    expected_salary: Optional[str] = Form(None),
    notice_period: Optional[str] = Form(None),
    db: Session = Depends(get_db),
):
    """Public careers apply: upload a resume, create a candidate + application."""
    job = db.query(Job).filter(Job.public_slug == slug).first()
    if not job or job.status != "open":
        raise HTTPException(status_code=404, detail="Job posting not available")
    if not (resume.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Please upload a PDF resume")

    content = await resume.read()
    try:
        text = extract_text_from_pdf(content)
    except Exception:
        text = ""

    os.makedirs("uploads", exist_ok=True)
    path = os.path.join("uploads", f"{uuid.uuid4()}_{resume.filename}")
    with open(path, "wb") as f:
        f.write(content)

    candidate = Candidate(
        organization_id=job.organization_id,
        name=resume.filename,
        status="processing",
        resume_text=text,
        resume_file_path=path,
    )
    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    application = Application(
        job_id=job.id,
        candidate_id=candidate.id,
        source="careers",
        cover_letter=cover_letter,
        expected_salary=expected_salary,
        notice_period=notice_period,
        status="applied",
        stage_history=[{"stage": "applied", "at": datetime.now(timezone.utc).isoformat()}],
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Parse + score off the request thread (opens its own session).
    from routers.candidates import process_resume_background
    background_tasks.add_task(process_resume_background, candidate.id, text)

    logger.info("Public application: job=%s candidate=%s app=%s", job.id, candidate.id, application.id)
    return {"status": "received", "application_id": application.id, "candidate_id": candidate.id}


@router.get("/{job_id}", response_model=JobResponse)
def get_job(job_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _with_count(_get_job(job_id, db, current.organization_id))


@router.patch("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, payload: JobUpdate, current: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    job = _get_job(job_id, db, current.organization_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    logger.info("Job updated: id=%s status=%s", job.id, job.status)
    return _with_count(job)


@router.delete("/{job_id}")
def delete_job(job_id: int, current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_job(job_id, db, current.organization_id)
    db.delete(job)
    db.commit()
    logger.info("Job deleted: id=%s", job_id)
    return {"status": "deleted", "id": job_id}


@router.post("/{job_id}/generate", response_model=JobResponse)
def generate_content(job_id: int, current: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    """AI-generate (or deterministically build) the full job posting content."""
    job = _get_job(job_id, db, current.organization_id)
    for field, value in generate_job_content(job).items():
        setattr(job, field, value)
    db.commit()
    db.refresh(job)
    logger.info("Job %s content generated", job.id)
    return _with_count(job)


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
@router.post("/{job_id}/applications", response_model=ApplicationResponse)
def create_application(job_id: int, payload: ApplicationCreate,
                       current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = _get_job(job_id, db, current.organization_id)

    candidate = None
    if payload.candidate_id is not None:
        candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

    app_row = Application(
        job_id=job.id,
        candidate_id=payload.candidate_id,
        source=payload.source or "manual",
        cover_letter=payload.cover_letter,
        expected_salary=payload.expected_salary,
        notice_period=payload.notice_period,
        answers=payload.answers,
        match_score=_skill_match(candidate, job),
        stage_history=[{"stage": "applied", "at": datetime.now(timezone.utc).isoformat()}],
    )
    db.add(app_row)
    db.commit()
    db.refresh(app_row)
    logger.info("Application created: id=%s job=%s candidate=%s match=%s",
                app_row.id, job.id, payload.candidate_id, app_row.match_score)
    return app_row


@router.get("/{job_id}/applications", response_model=List[ApplicationResponse])
def list_applications(
    job_id: int,
    status: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _get_job(job_id, db, current.organization_id)
    query = db.query(Application).filter(Application.job_id == job_id)
    if status:
        query = query.filter(Application.status == status)
    return query.order_by(Application.match_score.desc().nullslast(), Application.id.desc()).all()


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdate,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    app_row = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Application.id == application_id, Job.organization_id == current.organization_id)
        .first()
    )
    if not app_row:
        raise HTTPException(status_code=404, detail="Application not found")
    if payload.status not in _APPLICATION_STATUSES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid status. Allowed: {sorted(_APPLICATION_STATUSES)}",
        )
    app_row.status = payload.status
    history = list(app_row.stage_history or [])
    history.append({"stage": payload.status, "at": datetime.now(timezone.utc).isoformat()})
    app_row.stage_history = history
    db.commit()
    db.refresh(app_row)
    return app_row
