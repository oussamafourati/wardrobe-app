import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Consent


def has_consent(db: Session, user_id: uuid.UUID, purpose: str) -> bool:
    """The most recent decision wins. Ties (same timestamp) are broken by id."""
    granted = db.scalar(
        select(Consent.granted)
        .where(Consent.user_id == user_id, Consent.purpose == purpose)
        .order_by(Consent.created_at.desc(), Consent.id.desc())
        .limit(1)
    )
    return bool(granted)
