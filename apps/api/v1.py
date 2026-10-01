import uuid
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from auth import current_user, hash_token, new_token
from db import get_db
from models import GuestSession, User

router = APIRouter(prefix="/v1")

Locale = Literal["fr-FR", "en-GB", "en-US"]


class SessionCreate(BaseModel):
    locale: Locale = "fr-FR"


class SessionCreated(BaseModel):
    token: str
    user_id: uuid.UUID
    locale: Locale


class Me(BaseModel):
    user_id: uuid.UUID
    locale: str
    created_at: datetime


@router.post("/sessions", response_model=SessionCreated, status_code=status.HTTP_201_CREATED)
def create_session(payload: SessionCreate | None = None, db: Session = Depends(get_db)):
    locale = payload.locale if payload else "fr-FR"
    user = User(locale=locale)
    db.add(user)
    db.flush()  # the database assigns user.id
    token = new_token()
    db.add(GuestSession(token_hash=hash_token(token), user_id=user.id))
    db.commit()
    return SessionCreated(token=token, user_id=user.id, locale=locale)


@router.get("/me", response_model=Me)
def me(user: User = Depends(current_user)):
    return Me(user_id=user.id, locale=user.locale, created_at=user.created_at)
