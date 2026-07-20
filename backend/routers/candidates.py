import logging
import os
import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, func, String
from typing import List, Optional
from database import get_db, SessionLocal
from db_models import Candidate, SystemSettings, User
from dependencies import get_current_user
from schemas import CandidateResponse, EmailRequest, ScheduleInterviewRequest
from services.resume_parser import extract_text_from_pdf, parse_resume_with_ai
from services.skill_engine import evaluate_truth_score
from services.role_engine import analyze_role
from services.email_service import (
    send_invite_email, send_reject_email, send_shortlist_email,
    send_offer_email, send_reminder_email, send_confirmation_email,
    send_reschedule_email, send_welcome_email, send_followup_email,
)

logger = logging.getLogger("hiringbuddy.candidates")

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_resume_background(candidate_id: int, resume_text: str):
    """Parse + evaluate a resume off the request thread.

    Opens its OWN database session (the request-scoped session from get_db is
    already closed by the time background tasks run). Offline-first parsing +
    evaluation guarantee a result, so a candidate is never left 'processing'.
    """
    db = SessionLocal()
    try:
        logger.info("Processing candidate %s: parsing resume", candidate_id)
        parsed_data = parse_resume_with_ai(resume_text)

        role_match = analyze_role(parsed_data)
        eval_data = evaluate_truth_score(resume_text, parsed_data, role_match)

        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            logger.error("Candidate %s vanished before processing finished", candidate_id)
            return

        candidate.name = parsed_data.get("name") or "Unknown"
        candidate.email = parsed_data.get("email") or None
        if not candidate.email:
            candidate.email_status = "no_email"  # flag: requires manual review (never fake an email)
        candidate.phone = parsed_data.get("phone")
        candidate.skills = parsed_data.get("skills", [])
        candidate.experience_years = parsed_data.get("experience_years", 0.0) or 0.0

        # Rich profile
        candidate.role_applied = role_match["role"]
        candidate.education = parsed_data.get("education", [])
        candidate.languages = parsed_data.get("languages", [])

        candidate.linkedin = next(iter(parsed_data.get("linkedin_links", [])), None)
        candidate.github = next(iter(parsed_data.get("github_links", [])), None)
        candidate.portfolio = next(iter(parsed_data.get("portfolio_links", [])), None)

        candidate.truth_score = eval_data.get("decision_data", {}).get("confidence_score", 0.0)

        candidate.multi_signal_skills = eval_data.get("multi_signal_skills", [])
        candidate.detailed_warnings = eval_data.get("detailed_warnings", [])
        candidate.consistency_data = eval_data.get("consistency_data", {})
        candidate.role_match_data = eval_data.get("role_match_data", {})
        candidate.decision_data = eval_data.get("decision_data", {})

        candidate.github_intelligence = eval_data.get("github_intelligence", {})
        candidate.certification_intelligence = eval_data.get("certification_intelligence", {})
        candidate.interview_risk_analysis = eval_data.get("interview_risk_analysis", {})

        candidate.projects_analysis = eval_data.get("projects_analysis", {})
        candidate.smart_questions = eval_data.get("smart_questions", {})
        candidate.hr_insights = eval_data.get("hr_insights", {})
        candidate.candidate_category = eval_data.get("candidate_category", "Needs Review")
        candidate.hidden_talent_tag = eval_data.get("hidden_talent_tag", False)

        candidate.overall_score = role_match["overall_match"]
        candidate.status = "completed"

        db.commit()
        logger.info(
            "Candidate %s completed: role=%s skills=%d overall=%s%%",
            candidate_id, candidate.role_applied,
            len(candidate.skills or []), candidate.overall_score,
        )
    except Exception as e:
        logger.exception("Failed processing candidate %s: %s", candidate_id, e)
        db.rollback()
        try:
            candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
            if candidate:
                candidate.status = "failed"
                db.commit()
        except Exception:
            logger.exception("Could not mark candidate %s as failed", candidate_id)
    finally:
        db.close()

@router.post("/upload", response_model=List[CandidateResponse])
async def upload_resumes(background_tasks: BackgroundTasks, files: List[UploadFile] = File(...),
                         current: User = Depends(get_current_user), db: Session = Depends(get_db)):
    created_candidates = []
    
    logger.info("Upload received: %d file(s)", len(files))
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning("Skipping non-PDF upload: %s", file.filename)
            continue

        content = await file.read()
        try:
            resume_text = extract_text_from_pdf(content)
        except Exception as e:
            logger.exception("PDF extraction crashed for %s: %s", file.filename, e)
            resume_text = ""  # still create the candidate; parser handles empty text

        # Save file to disk
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}_{file.filename}")
        with open(file_path, "wb") as f:
            f.write(content)
            
        # Create pending candidate
        new_candidate = Candidate(
            organization_id=current.organization_id,
            name=file.filename, # Temporary name
            email=None, # DO NOT generate fake emails
            resume_text=resume_text,
            resume_file_path=file_path,
            status="processing"
        )
        db.add(new_candidate)
        db.commit()
        db.refresh(new_candidate)
        
        # Dispatch background task (it opens its own DB session)
        background_tasks.add_task(process_resume_background, new_candidate.id, resume_text)

        created_candidates.append(new_candidate)

    return created_candidates

@router.get("/analytics")
def get_analytics(db: Session = Depends(get_db)):
    total = db.query(Candidate).count()
    shortlisted = db.query(Candidate).filter(Candidate.status == 'shortlisted').count()
    rejected = db.query(Candidate).filter(Candidate.status == 'rejected').count()
    
    avg_score = db.query(func.avg(Candidate.truth_score)).scalar() or 0.0
    
    all_candidates = db.query(Candidate).all()
    skill_counts = {}
    for c in all_candidates:
        if c.skills:
            for s in c.skills:
                skill_counts[s] = skill_counts.get(s, 0) + 1
                
    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_skills_list = [{"skill": k, "count": v} for k, v in top_skills]
    
    return {
        "total_candidates": total,
        "avg_score": round(avg_score, 1),
        "shortlisted_count": shortlisted,
        "rejected_count": rejected,
        "top_skills": top_skills_list
    }

@router.get("/upload-status")
def get_upload_status(db: Session = Depends(get_db)):
    processing = db.query(Candidate).filter(Candidate.status == 'processing').count()
    completed = db.query(Candidate).filter(Candidate.status != 'processing').count()
    return {
        "processing": processing,
        "completed": completed,
        "total": processing + completed
    }

@router.get("/", response_model=List[CandidateResponse])
def get_candidates(
    q: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    min_exp: Optional[float] = None,
    max_exp: Optional[float] = None,
    has_warnings: Optional[bool] = None,
    status: Optional[str] = None,
    sort: Optional[str] = None,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(Candidate).filter(
        or_(
            Candidate.organization_id == current.organization_id,
            Candidate.organization_id.is_(None),
        )
    )
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Candidate.name.ilike(search_term),
                Candidate.email.ilike(search_term),
                Candidate.skills.cast(String).ilike(search_term)
            )
        )
        
    if min_score is not None:
        query = query.filter(Candidate.truth_score >= min_score)
    if max_score is not None:
        query = query.filter(Candidate.truth_score <= max_score)
    if min_exp is not None:
        query = query.filter(Candidate.experience_years >= min_exp)
    if max_exp is not None:
        query = query.filter(Candidate.experience_years <= max_exp)
    if status and status != 'all candidates':
        if status == 'interviews':
            query = query.filter(Candidate.status == 'invited')
        else:
            query = query.filter(Candidate.status == status)
        
    if sort == "score":
        query = query.order_by(desc(Candidate.overall_score), desc(Candidate.id))
    elif sort == "experience":
        query = query.order_by(desc(Candidate.experience_years), desc(Candidate.id))
    else:
        query = query.order_by(desc(Candidate.id))
    candidates = query.all()
    
    if has_warnings is not None:
        if has_warnings:
            candidates = [c for c in candidates if c.red_flags and len(c.red_flags) > 0]
        else:
            candidates = [c for c in candidates if not c.red_flags or len(c.red_flags) == 0]
            
    return candidates

@router.get("/{candidate_id}", response_model=CandidateResponse)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate

@router.get("/resume/{candidate_id}")
def get_resume(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not candidate or not candidate.resume_file_path or not os.path.exists(candidate.resume_file_path):
        raise HTTPException(status_code=404, detail="Resume not found")
    return FileResponse(candidate.resume_file_path, media_type="application/pdf")

# ---------------------------------------------------------------------------
# Shared helpers for candidate actions
# ---------------------------------------------------------------------------
def _get_settings(db: Session):
    s = db.query(SystemSettings).first()
    if not s:
        s = SystemSettings()
        db.add(s)
        db.commit()
        db.refresh(s)
    return s


def _interview_link(candidate: Candidate) -> str:
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173").rstrip('/')
    return f"{frontend_url}/c-interview/{candidate.id}?token={candidate.interview_token}"


def _resolve(db: Session, candidate_id: Optional[int] = None, email: Optional[str] = None) -> Candidate:
    q = db.query(Candidate)
    candidate = (q.filter(Candidate.id == candidate_id).first() if candidate_id is not None
                 else q.filter(Candidate.email == email).first())
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return candidate


def _role_of(candidate: Candidate) -> str:
    return candidate.role_applied or "Software Engineer"


def _ensure_token(candidate: Candidate):
    if not candidate.interview_token:
        candidate.interview_token = uuid.uuid4().hex
    # Interview links are valid for 7 days from (re)generation.
    candidate.interview_token_expiry = (
        datetime.now(timezone.utc) + timedelta(days=7)
    ).isoformat()
    candidate.interview_type = candidate.interview_type or "ai"


def _do_invite(db: Session, candidate: Candidate, date="", time="") -> dict:
    _ensure_token(candidate)
    candidate.status = "invited"
    candidate.interview_status = "not_started"
    link = _interview_link(candidate)
    settings_obj = _get_settings(db)
    if candidate.email:
        sent = send_invite_email(candidate.email, candidate.name, date, time, link,
                                 settings_obj=settings_obj, role=_role_of(candidate))
        candidate.email_status = "sent" if sent else "failed"
    else:
        candidate.email_status = "no_email"
    candidate.interview_link = link
    db.commit()
    logger.info("Invited candidate %s (email_status=%s)", candidate.id, candidate.email_status)
    return {"success": True, "link": link, "email_status": candidate.email_status,
            "interview_id": candidate.id}


def _do_status(db: Session, candidate: Candidate, status: str, sender) -> dict:
    candidate.status = status
    settings_obj = _get_settings(db)
    if candidate.email:
        sent = sender(candidate.email, candidate.name, settings_obj=settings_obj, role=_role_of(candidate))
        candidate.email_status = "sent" if sent else "failed"
    else:
        candidate.email_status = "no_email"
    db.commit()
    logger.info("Candidate %s -> %s (email_status=%s)", candidate.id, status, candidate.email_status)
    return {"status": "success", "email_status": candidate.email_status}


# ---------------------------------------------------------------------------
# ID-based actions (used by the dashboard cards)
# ---------------------------------------------------------------------------
@router.post("/{candidate_id}/invite")
def invite_by_id(candidate_id: int, db: Session = Depends(get_db)):
    return _do_invite(db, _resolve(db, candidate_id=candidate_id))


@router.post("/{candidate_id}/reject")
def reject_by_id(candidate_id: int, db: Session = Depends(get_db)):
    return _do_status(db, _resolve(db, candidate_id=candidate_id), "rejected", send_reject_email)


@router.post("/{candidate_id}/shortlist")
def shortlist_by_id(candidate_id: int, db: Session = Depends(get_db)):
    return _do_status(db, _resolve(db, candidate_id=candidate_id), "shortlisted", send_shortlist_email)


@router.post("/{candidate_id}/offer")
def offer_by_id(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _resolve(db, candidate_id=candidate_id)
    candidate.status = "offered"
    settings_obj = _get_settings(db)
    if candidate.email:
        sent = send_offer_email(candidate.email, candidate.name, settings_obj=settings_obj, role=_role_of(candidate))
        candidate.email_status = "sent" if sent else "failed"
    else:
        candidate.email_status = "no_email"
    db.commit()
    return {"status": "success", "email_status": candidate.email_status}


@router.post("/{candidate_id}/reminder")
def reminder_by_id(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _resolve(db, candidate_id=candidate_id)
    _ensure_token(candidate)
    db.commit()
    settings_obj = _get_settings(db)
    ok = False
    if candidate.email:
        ok = send_reminder_email(candidate.email, candidate.name, candidate.scheduled_date or "",
                                 candidate.scheduled_time or "", _interview_link(candidate),
                                 settings_obj=settings_obj, role=_role_of(candidate))
    return {"status": "success" if ok else "no_email"}


@router.post("/{candidate_id}/reschedule")
def reschedule_by_id(candidate_id: int, date: str = "", time: str = "", db: Session = Depends(get_db)):
    candidate = _resolve(db, candidate_id=candidate_id)
    _ensure_token(candidate)
    candidate.scheduled_date = date or candidate.scheduled_date
    candidate.scheduled_time = time or candidate.scheduled_time
    db.commit()
    settings_obj = _get_settings(db)
    ok = False
    if candidate.email:
        ok = send_reschedule_email(candidate.email, candidate.name, candidate.scheduled_date or "",
                                   candidate.scheduled_time or "", _interview_link(candidate),
                                   settings_obj=settings_obj, role=_role_of(candidate))
    return {"status": "success" if ok else "no_email"}


@router.post("/{candidate_id}/welcome")
def welcome_by_id(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _resolve(db, candidate_id=candidate_id)
    settings_obj = _get_settings(db)
    candidate.status = "hired"
    ok = False
    if candidate.email:
        ok = send_welcome_email(candidate.email, candidate.name, settings_obj=settings_obj, role=_role_of(candidate))
        candidate.email_status = "sent" if ok else "failed"
    else:
        candidate.email_status = "no_email"
    db.commit()
    return {"status": "success" if ok else candidate.email_status}


@router.post("/{candidate_id}/followup")
def followup_by_id(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _resolve(db, candidate_id=candidate_id)
    settings_obj = _get_settings(db)
    ok = False
    if candidate.email:
        ok = send_followup_email(candidate.email, candidate.name, settings_obj=settings_obj, role=_role_of(candidate))
    return {"status": "success" if ok else "no_email"}


# ---------------------------------------------------------------------------
# Email-based actions (backwards-compatible with existing frontend calls)
# ---------------------------------------------------------------------------
@router.post("/send-reject")
def send_reject(req: EmailRequest, db: Session = Depends(get_db)):
    return _do_status(db, _resolve(db, email=req.candidate_email), "rejected", send_reject_email)


@router.post("/send-shortlist")
def send_shortlist(req: EmailRequest, db: Session = Depends(get_db)):
    return _do_status(db, _resolve(db, email=req.candidate_email), "shortlisted", send_shortlist_email)


@router.post("/send-invite")
def send_invite(req: EmailRequest, db: Session = Depends(get_db)):
    return _do_invite(db, _resolve(db, email=req.candidate_email))


@router.post("/start-ai-interview")
def start_ai_interview(req: EmailRequest, db: Session = Depends(get_db)):
    candidate = _resolve(db, email=req.candidate_email)
    result = _do_invite(db, candidate)
    return {"status": "success", "interview_id": candidate.id, "link": result["link"],
            "email_status": result["email_status"]}
