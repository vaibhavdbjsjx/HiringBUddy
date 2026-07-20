"""Skill assessment API — generate role-based MCQ tests, deliver, and score."""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from db_models import Assessment, User
from dependencies import get_current_user
from schemas import (
    AssessmentGenerateRequest, AssessmentQuestion, AssessmentResponse, AssessmentSubmit,
)
from services.assessment_engine import generate_assessment

logger = logging.getLogger("hiringbuddy.assessments")
router = APIRouter()


def _public(a: Assessment) -> AssessmentResponse:
    """Strip answer_index before returning questions to the client."""
    questions = [
        AssessmentQuestion(
            question=q.get("question", ""),
            options=q.get("options", []),
            difficulty=q.get("difficulty"),
            topic=q.get("topic"),
        )
        for q in (a.questions or [])
    ]
    return AssessmentResponse(id=a.id, role=a.role, status=a.status, score=a.score, questions=questions)


@router.post("/generate", response_model=AssessmentResponse)
def generate(payload: AssessmentGenerateRequest, current: User = Depends(get_current_user),
             db: Session = Depends(get_db)):
    questions = generate_assessment(payload.role, payload.skills, payload.num_questions)
    a = Assessment(
        organization_id=current.organization_id,
        candidate_id=payload.candidate_id,
        role=payload.role,
        skills=payload.skills,
        questions=questions,
        status="generated",
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return _public(a)


@router.get("/{assessment_id}", response_model=AssessmentResponse)
def get_assessment(assessment_id: int, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return _public(a)


@router.post("/{assessment_id}/submit")
def submit(assessment_id: int, payload: AssessmentSubmit, db: Session = Depends(get_db)):
    a = db.query(Assessment).filter(Assessment.id == assessment_id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Assessment not found")
    questions = a.questions or []
    total = len(questions)
    answers = payload.answers or []

    results = []
    correct = 0
    for i, q in enumerate(questions):
        chosen = answers[i] if i < len(answers) else None
        is_correct = chosen is not None and chosen == q.get("answer_index")
        correct += 1 if is_correct else 0
        results.append({"correct_index": q.get("answer_index"), "chosen": chosen, "is_correct": is_correct})

    score = round(100 * correct / total, 1) if total else 0.0
    a.answers = answers
    a.score = score
    a.status = "submitted"
    db.commit()
    logger.info("Assessment %s scored: %s%% (%d/%d)", a.id, score, correct, total)
    return {"assessment_id": a.id, "score": score, "correct": correct, "total": total, "results": results}
