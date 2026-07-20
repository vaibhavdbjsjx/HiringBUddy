"""Authentication — register (creates an organization + owner), login, me."""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from db_models import Organization, User
from dependencies import get_current_user
from schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from services.security import create_access_token, hash_password, verify_password

logger = logging.getLogger("hiringbuddy.auth")
router = APIRouter()

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _token_response(user: User) -> TokenResponse:
    token = create_access_token(user.id, user.organization_id, user.role or "owner")
    return TokenResponse(access_token=token, user=UserResponse.model_validate(user))


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = (payload.email or "").strip().lower()
    if not _EMAIL_RE.match(email):
        raise HTTPException(status_code=422, detail="Enter a valid email address")
    if len(payload.password or "") < 8:
        raise HTTPException(status_code=422, detail="Password must be at least 8 characters")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    default_name = (payload.full_name or email.split("@")[0]).strip()
    org = Organization(name=(payload.organization_name or "").strip() or f"{default_name}'s workspace")
    db.add(org)
    db.commit()
    db.refresh(org)

    user = User(
        email=email,
        password_hash=hash_password(payload.password),
        full_name=(payload.full_name or "").strip() or None,
        role="owner",
        organization_id=org.id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Registered user %s (org=%s)", user.id, org.id)
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = (payload.email or "").strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password or "", user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    logger.info("Login for user %s", user.id)
    return _token_response(user)


@router.get("/me", response_model=UserResponse)
def me(current: User = Depends(get_current_user)):
    return current
