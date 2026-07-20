"""AI HR Copilot — natural-language queries over the recruiter's candidates."""
import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from db_models import Candidate, User
from dependencies import get_current_user
from services.copilot import answer_query

logger = logging.getLogger("hiringbuddy.copilot")
router = APIRouter()


class CopilotQuery(BaseModel):
    message: str


@router.post("/query")
def query(payload: CopilotQuery, current: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    rows = db.query(Candidate).filter(
        or_(Candidate.organization_id == current.organization_id, Candidate.organization_id.is_(None))
    ).all()
    candidates = [{
        "id": c.id, "name": c.name, "skills": c.skills or [], "overall_score": c.overall_score,
        "role_applied": c.role_applied, "experience_years": c.experience_years,
        "status": c.status, "candidate_category": c.candidate_category,
    } for c in rows]
    result = answer_query(payload.message, candidates)
    logger.info("Copilot query answered (%d candidates in scope)", len(candidates))
    return result
