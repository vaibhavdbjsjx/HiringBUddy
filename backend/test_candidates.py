from database import SessionLocal
from routers.candidates import get_candidates

db = SessionLocal()
try:
    res = get_candidates(q=None, status=None, min_score=None, max_score=None, min_exp=None, max_exp=None, has_warnings=None, db=db)
    print("Success")
except Exception as e:
    import traceback
    traceback.print_exc()
