import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from db_models import Interview, Candidate
from services.interview_engine import (
    generate_questions, evaluate_answer, finalize_report, generate_followup,
)

logger = logging.getLogger("hiringbuddy.interviews")
router = APIRouter()


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------
class ProctoringEvent(BaseModel):
    type: str                 # tab_switch, fullscreen_exit, no_face, multiple_faces, ...
    message: str
    severity: str = "medium"  # low | medium | high


class AnswerSubmission(BaseModel):
    question: str
    answer: str


class FollowupRequest(BaseModel):
    question: str
    answer: str


class FinalizeRequest(BaseModel):
    transcript: List[dict] = []
    integrity_score: float = 100.0


# Penalty (integrity points) per proctoring event severity.
_PENALTY = {"low": 2, "medium": 5, "high": 10}


def _get_candidate(candidate_id: int, db: Session) -> Candidate:
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return c


def _active_interview(candidate_id: int, db: Session) -> Interview:
    iv = (db.query(Interview)
          .filter(Interview.candidate_id == candidate_id)
          .order_by(Interview.id.desc()).first())
    if not iv:
        iv = Interview(candidate_id=candidate_id, integrity_score=100.0, warnings=[],
                       transcript=[], created_at=datetime.now(timezone.utc).isoformat())
        db.add(iv)
        db.commit()
        db.refresh(iv)
    return iv


# ---------------------------------------------------------------------------
# Token verification (secures the interview link)
# ---------------------------------------------------------------------------
@router.get("/{candidate_id}/verify")
def verify_token(candidate_id: int, token: str, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    if not candidate.interview_token or candidate.interview_token != token:
        raise HTTPException(status_code=403, detail="Invalid interview token")
    if candidate.interview_token_expiry:
        try:
            if datetime.fromisoformat(candidate.interview_token_expiry) < datetime.now(timezone.utc):
                raise HTTPException(status_code=403, detail="Interview link has expired")
        except ValueError:
            pass
    return {"valid": True, "candidate_name": candidate.name,
            "role": candidate.role_applied or "Software Engineer"}


# ---------------------------------------------------------------------------
# Questions (adaptive, role-tailored)
# ---------------------------------------------------------------------------
@router.get("/{candidate_id}/questions")
def get_questions(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    questions = generate_questions(candidate)
    iv = _active_interview(candidate_id, db)
    iv.questions = questions
    db.commit()
    return {"questions": questions, "role": candidate.role_applied or "Software Engineer"}


# Legacy path kept for backwards compatibility (returns a plain list).
@router.post("/{candidate_id}/generate-questions")
def generate_questions_legacy(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    return generate_questions(candidate)


# ---------------------------------------------------------------------------
# Interview lifecycle
# ---------------------------------------------------------------------------
@router.post("/{candidate_id}/start")
def start_interview(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    candidate.interview_status = "in_progress"
    iv = _active_interview(candidate_id, db)
    iv.integrity_score = 100.0
    iv.warnings = []
    iv.transcript = []
    db.commit()
    logger.info("Interview started for candidate %s", candidate_id)
    return {"status": "in_progress", "interview_id": iv.id}


@router.post("/{candidate_id}/answer")
def submit_answer(candidate_id: int, submission: AnswerSubmission, db: Session = Depends(get_db)):
    _get_candidate(candidate_id, db)
    result = evaluate_answer(submission.question, submission.answer)
    iv = _active_interview(candidate_id, db)
    transcript = list(iv.transcript or [])
    transcript.append({"question": submission.question, "answer": submission.answer, **result})
    iv.transcript = transcript
    db.commit()
    return result


@router.post("/{candidate_id}/followup")
def followup(candidate_id: int, req: FollowupRequest, db: Session = Depends(get_db)):
    """Return an adaptive follow-up question for the given Q&A."""
    _get_candidate(candidate_id, db)
    return {"question": generate_followup(req.question, req.answer)}


@router.post("/{candidate_id}/proctoring")
def record_proctoring(candidate_id: int, event: ProctoringEvent, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    iv = _active_interview(candidate_id, db)

    warnings = list(iv.warnings or [])
    warnings.append({
        "time": datetime.now(timezone.utc).isoformat(),
        "type": event.type, "message": event.message, "severity": event.severity,
    })
    iv.warnings = warnings
    iv.integrity_score = max(0.0, (iv.integrity_score if iv.integrity_score is not None else 100.0)
                             - _PENALTY.get(event.severity, 5))

    # Mirror onto the candidate for the HR dashboard.
    candidate.integrity_score = iv.integrity_score
    candidate.proctoring_warnings = warnings
    db.commit()
    logger.info("Proctoring event '%s' for candidate %s -> integrity=%s",
                event.type, candidate_id, iv.integrity_score)
    return {"integrity_score": iv.integrity_score, "warnings_count": len(warnings)}


@router.post("/{candidate_id}/finalize")
def finalize_interview(candidate_id: int, req: FinalizeRequest, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    iv = _active_interview(candidate_id, db)

    transcript = req.transcript or iv.transcript or []
    integrity = iv.integrity_score if iv.integrity_score is not None else req.integrity_score
    report = finalize_report(candidate.role_applied or "Software Engineer",
                             transcript, integrity, iv.warnings or [])

    iv.score = report["interview_score"]
    iv.transcript = transcript
    candidate.interview_score = report["interview_score"]
    candidate.integrity_score = report["integrity_score"]
    candidate.interview_status = "completed"
    candidate.interview_report = report
    if candidate.status in ("invited", "processing", "completed"):
        candidate.status = "interviewed"
    db.commit()
    logger.info("Interview finalized for candidate %s: final=%s", candidate_id, report["final_score"])
    return report


@router.get("/{candidate_id}/report")
def get_report(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _get_candidate(candidate_id, db)
    iv = _active_interview(candidate_id, db)
    return {
        "report": candidate.interview_report,
        "transcript": iv.transcript or [],
        "warnings": iv.warnings or [],
        "integrity_score": candidate.integrity_score,
        "interview_score": candidate.interview_score,
    }
