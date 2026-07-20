import logging

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base, ensure_schema
from dependencies import get_current_user
from routers import auth, candidates, interviews, proctoring, settings, reports, jobs, assessments, copilot

# Structured logging so failures are visible instead of silently swallowed.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger("hiringbuddy")

# Create DB tables, then apply additive column migrations.
Base.metadata.create_all(bind=engine)
ensure_schema()

app = FastAPI(title="HiringBuddy API", version="1.0.0")

# CORS middleware
import os
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        FRONTEND_URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Recruiter APIs require authentication. Candidate-facing interview + proctoring
# endpoints stay public (secured by a per-interview token), as does the public
# careers job view.
_auth = [Depends(get_current_user)]

app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
app.include_router(candidates.router, prefix="/api/candidates", tags=["Candidates"], dependencies=_auth)
app.include_router(interviews.router, prefix="/api/interviews", tags=["Interviews"])
app.include_router(proctoring.router, prefix="/api/proctoring", tags=["Proctoring"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"], dependencies=_auth)
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"], dependencies=_auth)
app.include_router(jobs.public_router, prefix="/api/jobs", tags=["Jobs"])
app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"], dependencies=_auth)
app.include_router(assessments.router, prefix="/api/assessments", tags=["Assessments"], dependencies=_auth)
app.include_router(copilot.router, prefix="/api/copilot", tags=["Copilot"], dependencies=_auth)

@app.get("/")
def read_root():
    return {"message": "Welcome to HiringBuddy API"}

# (Removed the unauthenticated /upload-resume/ alias — POST /api/candidates/upload is
#  the authenticated canonical endpoint; an open alias would bypass auth.)
