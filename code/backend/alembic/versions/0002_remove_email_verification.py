"""Remove OTP email verification.

Signup now creates the account directly and sends the student to the login page.
That leaves `email_verifications` unused and `users.is_verified` permanently true,
so both go. The @thapar.edu domain check remains the access control.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("email_verifications")
    op.drop_column("users", "is_verified")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
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
    op.create_index(
        "uq_email_verifications_one_active",
        "email_verifications",
        ["user_id"],
        unique=True,
        postgresql_where=sa.text("consumed_at IS NULL"),
    )
