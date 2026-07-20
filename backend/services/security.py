"""Password hashing (bcrypt) and JWT access tokens.

bcrypt is used directly rather than through passlib to avoid the well-known
passlib/bcrypt version incompatibility. Tokens are signed with
``settings.SECRET_KEY`` using HS256.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
import jwt

from config import settings

ALGORITHM = "HS256"
# bcrypt only hashes the first 72 bytes; truncate explicitly to avoid errors.
_MAX_BCRYPT_BYTES = 72


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8")[:_MAX_BCRYPT_BYTES], bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8")[:_MAX_BCRYPT_BYTES], hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(
    user_id: int,
    org_id: Optional[int],
    role: str = "owner",
    expires_minutes: Optional[int] = None,
) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "org": org_id, "role": role, "iat": now, "exp": exp}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode + verify a JWT. Raises jwt exceptions on invalid/expired tokens."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
