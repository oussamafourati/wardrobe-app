"""Database tables. Migrations live in migrations/versions and must match this file.
CI runs `alembic check` to catch any drift between the two."""
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    SmallInteger,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    locale: Mapped[str] = mapped_column(Text, nullable=False, server_default="fr-FR")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Consent(Base):
    """Append-only log: one row per grant or withdrawal."""

    __tablename__ = "consents"
    __table_args__ = (
        CheckConstraint(
            "purpose IN ('profile_sensitive', 'selfie_analysis', 'affiliate_tracking', 'analytics')",
            name="ck_consents_purpose",
        ),
        Index("ix_consents_user_purpose_created", "user_id", "purpose", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(Text, nullable=False)
    granted: Mapped[bool] = mapped_column(Boolean, nullable=False)
    policy_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint("height_cm BETWEEN 100 AND 250", name="ck_profiles_height_cm"),
        CheckConstraint("shoe_size BETWEEN 30 AND 52", name="ck_profiles_shoe_size"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    height_cm: Mapped[int | None] = mapped_column(SmallInteger)
    top_size: Mapped[str | None] = mapped_column(Text)
    bottom_size: Mapped[str | None] = mapped_column(Text)
    shoe_size: Mapped[float | None] = mapped_column(Numeric(3, 1))
    undertone: Mapped[str | None] = mapped_column(Text)
    hair_color: Mapped[str | None] = mapped_column(Text)
    eye_color: Mapped[str | None] = mapped_column(Text)
    glasses: Mapped[bool | None] = mapped_column(Boolean)
    attrs: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class GuestSession(Base):
    """One row per device. Only the SHA-256 hash of the token is stored."""

    __tablename__ = "sessions"
    __table_args__ = (Index("ix_sessions_user_id", "user_id"),)

    token_hash: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
