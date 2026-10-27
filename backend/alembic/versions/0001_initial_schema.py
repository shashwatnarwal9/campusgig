"""Milestone 1 schema: users, email verifications, sessions, gigs.

Revision ID: 0001
Revises:
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", postgresql.CITEXT(), nullable=False),
        sa.Column(
            "email_hash",
            sa.Text(),
            sa.Computed("encode(sha256(lower(email::text)::bytea), 'hex')", persisted=True),
            nullable=False,
        ),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("roll_no", sa.Text(), nullable=False),
        sa.Column("dept", sa.Text(), nullable=False),
        sa.Column("batch", sa.Integer(), nullable=False),
        sa.Column(
            "role",
            sa.Enum("STUDENT", "ADMIN", name="user_role"),
            server_default="STUDENT",
            nullable=False,
        ),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column(
            "failed_login_attempts", sa.Integer(), server_default=sa.text("0"), nullable=False
        ),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("batch BETWEEN 1900 AND 2100", name="ck_users_batch_range"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("roll_no"),
    )

    op.create_table(
        "email_verifications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("otp_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_verifications_user_id", "email_verifications", ["user_id"])
    op.create_index(
        "ix_email_verifications_user_created", "email_verifications", ["user_id", "created_at"]
    )
    # At most one live code per user, enforced by the database.
    op.create_index(
        "uq_email_verifications_one_active",
        "email_verifications",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL"),
    )

    op.create_table(
        "sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index("ix_sessions_user_id", "sessions", ["user_id"])
    op.create_index("ix_sessions_expires_at", "sessions", ["expires_at"])

    op.create_table(
        "gigs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("poster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "category",
            sa.Enum(
                "ACADEMIC_HELP",
                "DESIGN",
                "DEVELOPMENT",
                "WRITING",
                "TUTORING",
                "EVENTS",
                "PHOTOGRAPHY",
                "OTHER",
                name="gig_category",
            ),
            nullable=False,
        ),
        sa.Column("budget", sa.Numeric(10, 2), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "state",
            sa.Enum("OPEN", "CLOSED", name="gig_state"),
            server_default="OPEN",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("char_length(title) BETWEEN 5 AND 200", name="ck_gigs_title_length"),
        sa.CheckConstraint("budget > 0", name="ck_gigs_budget_positive"),
        sa.ForeignKeyConstraint(["poster_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_gigs_poster_id", "gigs", ["poster_id"])
    op.create_index("ix_gigs_category", "gigs", ["category"])
    op.execute("CREATE INDEX ix_gigs_state_created_at ON gigs (state, created_at DESC)")


def downgrade() -> None:
    op.drop_table("gigs")
    op.drop_table("sessions")
    op.drop_table("email_verifications")
    op.drop_table("users")
    for enum_name in ("gig_state", "gig_category", "user_role"):
        op.execute(f"DROP TYPE IF EXISTS {enum_name}")
