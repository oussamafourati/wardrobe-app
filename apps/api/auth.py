import hashlib
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import get_db
from models import GuestSession, User


def new_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="invalid or missing token",
        headers={"WWW-Authenticate": "Bearer"},
    )


def current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    scheme, _, token = (authorization or "").partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise _unauthorized()
    user = db.scalar(
        select(User)
        .join(GuestSession, GuestSession.user_id == User.id)
        .where(GuestSession.token_hash == hash_token(token))
    )
    if user is None:
        raise _unauthorized()
    return user
