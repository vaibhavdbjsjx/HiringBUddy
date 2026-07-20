import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from db_models import Candidate, Interview
from services.report_service import candidate_report, interview_report

logger = logging.getLogger("hiringbuddy.reports")
router = APIRouter()


def _pdf(data: bytes, filename: str) -> Response:
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


def _candidate(candidate_id: int, db: Session) -> Candidate:
    c = db.query(Candidate).filter(Candidate.id == candidate_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return c


@router.get("/{candidate_id}/candidate")
def download_candidate_report(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _candidate(candidate_id, db)
    try:
        data = candidate_report(candidate)
    except Exception as e:
        logger.exception("Candidate report generation failed for %s: %s", candidate_id, e)
        raise HTTPException(status_code=500, detail="Report generation failed")
    return _pdf(data, f"candidate_{candidate_id}_report.pdf")


@router.get("/{candidate_id}/interview")
def download_interview_report(candidate_id: int, db: Session = Depends(get_db)):
    candidate = _candidate(candidate_id, db)
    interview = (db.query(Interview)
                 .filter(Interview.candidate_id == candidate_id)
                 .order_by(Interview.id.desc()).first())
    try:
        data = interview_report(candidate, interview)
    except Exception as e:
        logger.exception("Interview report generation failed for %s: %s", candidate_id, e)
        raise HTTPException(status_code=500, detail="Report generation failed")
    return _pdf(data, f"interview_{candidate_id}_report.pdf")
