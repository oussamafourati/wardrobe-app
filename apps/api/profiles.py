import re
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from auth import current_user
from consents import has_consent
from db import get_db
from models import Profile, User
from taxonomy import keys

router = APIRouter(prefix="/v1")

FIELDS = [
    "height_cm", "top_size", "bottom_size", "shoe_size",
    "undertone", "hair_color", "eye_color", "glasses",
]
SENSITIVE_FIELDS = {"undertone"}  # stored only with the profile_sensitive consent
SIZE_PATTERN = re.compile(r"^(xxs|xs|s|m|l|xl|xxl|xxxl|3[0-9]|4[0-9]|5[0-9]|6[0-4])$")
Source = Literal["entered", "quiz"]  # "inferred" is reserved for the server


class ProfileIn(BaseModel):
    """Fields that are absent are left alone. An explicit null clears the field."""

    model_config = ConfigDict(extra="forbid")

    height_cm: int | None = Field(default=None, ge=100, le=250)
    top_size: str | None = None
    bottom_size: str | None = None
    shoe_size: float | None = Field(default=None, ge=30, le=52)
    undertone: str | None = None
    hair_color: str | None = None
    eye_color: str | None = None
    glasses: bool | None = None
    sources: dict[str, Source] = Field(default_factory=dict)

    @field_validator("top_size", "bottom_size", mode="before")
    @classmethod
    def normalise_size(cls, value):
        if value is None:
            return None
        value = str(value).strip().lower()
        if not SIZE_PATTERN.match(value):
            raise ValueError("unknown size: use a letter (xs..xxxl) or an FR number (30-64)")
        return value

    @field_validator("shoe_size")
    @classmethod
    def half_sizes_only(cls, value):
        if value is not None and (value * 2) % 1 != 0:
            raise ValueError("shoe size must be a whole or half size")
        return value

    @field_validator("undertone", "hair_color", "eye_color")
    @classmethod
    def in_taxonomy(cls, value, info):
        if value is not None and value not in keys(info.field_name):
            raise ValueError(f"not a valid {info.field_name} key")
        return value

    @field_validator("sources")
    @classmethod
    def sources_name_known_fields(cls, value):
        unknown = set(value) - set(FIELDS)
        if unknown:
            raise ValueError(f"unknown fields in sources: {sorted(unknown)}")
        return value


class ProfileOut(BaseModel):
    height_cm: int | None
    top_size: str | None
    bottom_size: str | None
    shoe_size: float | None
    undertone: str | None
    hair_color: str | None
    eye_color: str | None
    glasses: bool | None
    sources: dict[str, str]
    updated_at: datetime | None


def to_out(profile: Profile | None) -> ProfileOut:
    if profile is None:
        return ProfileOut(**{field: None for field in FIELDS}, sources={}, updated_at=None)
    sources = (profile.attrs or {}).get("sources", {})
    return ProfileOut(
        **{field: getattr(profile, field) for field in FIELDS},
        sources=sources,
        updated_at=profile.updated_at,
    )


@router.get("/profile", response_model=ProfileOut)
def get_profile(user: User = Depends(current_user), db: Session = Depends(get_db)):
    return to_out(db.get(Profile, user.id))


@router.put("/profile", response_model=ProfileOut)
def put_profile(
    payload: ProfileIn, user: User = Depends(current_user), db: Session = Depends(get_db)
):
    changes = {field: getattr(payload, field) for field in FIELDS if field in payload.model_fields_set}

    sensitive = sorted(f for f in SENSITIVE_FIELDS if changes.get(f) is not None)
    if sensitive and not has_consent(db, user.id, "profile_sensitive"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "consent_required", "purpose": "profile_sensitive", "fields": sensitive},
        )

    # Create the row if needed (safe if two requests race), then lock it for the update.
    db.execute(insert(Profile).values(user_id=user.id).on_conflict_do_nothing())
    profile = db.scalars(
        select(Profile).where(Profile.user_id == user.id).with_for_update()
    ).one()

    attrs = dict(profile.attrs or {})
    sources = dict(attrs.get("sources", {}))
    for field, value in changes.items():
        setattr(profile, field, value)
        if value is None:
            sources.pop(field, None)
        else:
            sources[field] = payload.sources.get(field, "entered")
    attrs["sources"] = sources
    profile.attrs = attrs
    profile.updated_at = func.now()

    db.commit()
    db.refresh(profile)
    return to_out(profile)
