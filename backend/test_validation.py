from database import SessionLocal
from routers.candidates import get_candidates
from schemas import CandidateResponse
from pydantic import ValidationError

db = SessionLocal()
try:
    candidates = get_candidates(q=None, status=None, min_score=None, max_score=None, min_exp=None, max_exp=None, has_warnings=None, db=db)
    for c in candidates:
        try:
            CandidateResponse.model_validate(c)
        except Exception as e:
            print(f"Error validating candidate {c.id}: {e}")
    print("All validated")
except Exception as e:
    print("Error fetching", e)
