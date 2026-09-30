"""initial schema: users, consents, profiles

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("locale", sa.Text(), server_default="fr-FR", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "consents",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("granted", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.Text(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "purpose IN ('profile_sensitive', 'selfie_analysis', 'affiliate_tracking', 'analytics')",
            name="ck_consents_purpose",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_consents_user_purpose_created", "consents", ["user_id", "purpose", "created_at"]
    )

    op.create_table(
        "profiles",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("height_cm", sa.SmallInteger(), nullable=True),
        sa.Column("top_size", sa.Text(), nullable=True),
        sa.Column("bottom_size", sa.Text(), nullable=True),
        sa.Column("shoe_size", sa.Numeric(3, 1), nullable=True),
        sa.Column("undertone", sa.Text(), nullable=True),
        sa.Column("hair_color", sa.Text(), nullable=True),
        sa.Column("eye_color", sa.Text(), nullable=True),
        sa.Column("glasses", sa.Boolean(), nullable=True),
        sa.Column(
            "attrs",
            postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("height_cm BETWEEN 100 AND 250", name="ck_profiles_height_cm"),
        sa.CheckConstraint("shoe_size BETWEEN 30 AND 52", name="ck_profiles_shoe_size"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("profiles")
    op.drop_index("ix_consents_user_purpose_created", table_name="consents")
    op.drop_table("consents")
    op.drop_table("users")
    # The vector extension stays: later tables will rely on it.
